"""Avature job scraper with pagination support."""

from .http_client import HTTPClient
from .parser import parse_job_listing, parse_total_jobs
from .endpoints import build_search_url
from .models import Job


class AvatureScraper:
    """Scraper for a single Avature career site."""
    
    def __init__(self, base_url: str, per_page: int = 50):
        self.base_url = base_url.rstrip("/")
        self.per_page = per_page
        self.company = self._extract_company()
        self.client = HTTPClient()
    
    def _extract_company(self) -> str:
        """Extract company name from subdomain."""
        host = self.base_url.split("//")[1].split("/")[0]
        subdomain = host.split(".")[0]
        return subdomain.title()
    
    def get_all_jobs(self) -> list[Job]:
        """Fetch all jobs from the site using pagination."""
        all_jobs = []
        offset = 0
        total_jobs = None
        page_size = None
        page_num = 1
        
        while True:
            url = build_search_url(self.base_url, offset=offset, per_page=self.per_page)
            
            try:
                response = self.client.get(url)
                html = response.text
            except Exception as e:
                print(f"  Error fetching page: {e}")
                break
            
            if total_jobs is None:
                total_jobs = parse_total_jobs(html)
                if total_jobs > 0:
                    print(f"  Total jobs on site: {total_jobs}")
            
            jobs = parse_job_listing(html, self.company, self.base_url)
            
            if not jobs:
                break
            
            if page_size is None:
                page_size = len(jobs)
            
            all_jobs.extend(jobs)
            print(f"  Page {page_num}: {len(jobs)} jobs (total: {len(all_jobs)})")
            
            offset += page_size
            page_num += 1
            
            if total_jobs and len(all_jobs) >= total_jobs:
                break
        
        return all_jobs
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
