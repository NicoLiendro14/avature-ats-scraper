"""HTTP client with retry and rate limiting using curl_cffi."""

import random
import time
from curl_cffi import requests


class HTTPClient:
    """HTTP client that impersonates a browser to avoid blocks."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.session = requests.Session(impersonate="chrome")
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with retry and rate limiting."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self._polite_delay()
                response = self.session.get(url, timeout=15, **kwargs)
                response.raise_for_status()
                return response
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (2 ** attempt)
                    time.sleep(wait_time)
        
        raise last_error
    
    def _polite_delay(self) -> None:
        """Random delay to be nice to servers."""
        time.sleep(random.uniform(0.3, 0.8))
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
