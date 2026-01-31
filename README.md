# Avature ATS Scraper

A scraper to get job posts from Avature websites.

## How to Install

```bash
pip install -r requirements.txt
```

## How to Use

```bash
python main.py
```

## Project Structure

```
avature-scraper/
├── input/              # Input files (URLs, sites)
├── output/             # Jobs and stats
├── scripts/            # Helper scripts
├── src/                # Main code
├── main.py             # Start here
├── requirements.txt    # Dependencies
└── README.md           # This file
```

## Data Preprocessing

The starter pack has 781K URLs, but many are duplicates or old job links.

**The smart approach:**

Instead of scraping 781K URLs one by one, we:

1. Extract unique subdomains (companies) from URLs
2. Add extra subdomains from Certificate Transparency (crt.sh)
3. Validate which sites are still active
4. Scrape each company site with pagination

**Why this is better:**

| Naive way | Smart way |
|-----------|-----------|
| 781K requests | ~120 sites x ~10 pages = ~1,200 requests |
| Old jobs, many 404s | Fresh jobs, all current |
| Lots of duplicates | No duplicates |

**Results:**

- URLs processed: 781,635
- Unique subdomains: 530
- Extra from crt.sh: +16
- Valid sites after check: 121

## Reverse Engineering

I analyzed 3 Avature sites (Ally, Broad Institute, Astellas) using browser dev tools.

**Key finding:** Avature has no public JSON API. Everything is HTML.

**URL patterns discovered:**

| What | Pattern |
|------|---------|
| Job list | `/careers/SearchJobs/?jobRecordsPerPage=50&jobOffset=0` |
| Pagination | Increment `jobOffset` by `jobRecordsPerPage` |
| Job detail | `/careers/JobDetail/{slug}/{id}` |
| Apply link | `/careers/ApplicationMethods?jobId={id}` |

**Logic:** Instead of scraping each job URL from the starter pack, I scrape the job listing pages with pagination. This gets ALL current jobs from each company, not just the ones in the old URL list.

## Why curl_cffi?

We use [curl_cffi](https://github.com/lexiforest/curl_cffi) instead of `requests` or `httpx`.

**The problem:** Websites can detect bots by looking at the "fingerprint" of your HTTP client. Each browser (Chrome, Firefox, Safari) has a unique fingerprint based on TLS settings and HTTP/2 behavior. Python's `requests` library has a fingerprint that screams "I am a bot!"

**The solution:** `curl_cffi` can impersonate real browsers. It copies Chrome's exact fingerprint, so websites think you are a real user.

| Library | Browser fingerprint | Block risk |
|---------|---------------------|------------|
| requests | Python/bot | High |
| httpx | Python/bot | High |
| curl_cffi | Chrome/Safari | Low |

**In code:**

```python
from curl_cffi import requests

response = requests.get(url, impersonate="chrome")
```

This simple change makes our scraper much harder to detect and block.

## Results

- **Total jobs found:** TBD
- **Sites checked:** TBD
- **Time spent:** TBD
