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

## Pagination Limitation

I tested if we could get more jobs per page to reduce the number of requests.

**What I tried:**
- Request `jobRecordsPerPage=20` or `jobRecordsPerPage=50`
- Avature ignores this and always returns 6 jobs per page

**Browser analysis showed:**

| Site | Parameter used | Jobs per page |
|------|----------------|---------------|
| ally.avature.net | `jobRecordsPerPage` | 6 (fixed) |
| healthfirst.avature.net | `pipelineRecordsPerPage` | 6 (fixed) |

**Key findings:**
1. The page size (6) is configured on Avature's backend, not controllable by URL parameters
2. Different sites use different parameter names (`job*` vs `pipeline*`)
3. There is no way to get more than 6 jobs per page from the client side

**Impact:** For a site like healthfirst with 9,000+ jobs, the scraper needs ~1,500 requests (9000 ÷ 6). This is a server limitation we cannot change.

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

## Rate Limiting and Proxies

### The Problem

When we tried to speed up the scraper using parallel requests (4 workers), Avature detected the unusual traffic pattern and blocked our IP with HTTP 406 errors.

```
[44/121] harmanglobal: 20 jobs (18.0s)
Error fetching page: HTTP Error 406:
[45/121] healthfirst: 0 jobs (8.7s)
Error fetching page: HTTP Error 406:
[46/121] infor: 0 jobs (6.5s)
...
```

**What happened:**
- First 40 sites worked fine
- Then Avature detected too many requests from one IP
- Server started returning 406 "Not Acceptable" (anti-bot response)

### The Solution: Proxy Rotation

To avoid IP-based rate limiting, we implemented a proxy rotation system:

```python
from src.proxy_manager import ProxyManager

proxy_manager = ProxyManager("input/proxies.txt")
proxy = proxy_manager.get_next()  # Returns next proxy in rotation
```

**How it works:**
1. Load a list of proxy servers from a file
2. Rotate through proxies for each request
3. If a proxy fails, mark it as bad and skip it
4. This distributes requests across multiple IPs

**Proxy file format** (`input/proxies.txt`):
```
http://user:pass@proxy1.example.com:8080
http://user:pass@proxy2.example.com:8080
socks5://proxy3.example.com:1080
```

## Results

### Final Numbers

- **Total jobs scraped:** 15,424 (after deduplication)
- **Sites processed:** 121
- **Duplicates removed:** 780
- **Total time:** ~3 hours

### Top 10 Companies by Jobs

| Company | Jobs |
|---------|------|
| Manpowergroupco | 2,004 |
| Sandboxtesco | 2,000 |
| Nva | 1,950 |
| Loa | 1,562 |
| Tesco | 1,129 |
| Uclahealth | 608 |
| Rohdeschwarz | 550 |
| Justicejobs | 547 |
| Mantech | 546 |
| Radpartners | 523 |

### Output Files

**`output/jobs.json`** - All jobs with metadata:

```json
{
  "total_jobs": 15424,
  "stats": { ... },
  "jobs": [
    {
      "job_id": "12345",
      "title": "Software Engineer",
      "company": "Acme",
      "location": "New York, USA",
      "description": "Job description...",
      "application_url": "https://acme.avature.net/careers/...",
      "source_url": "https://acme.avature.net/careers/...",
      "scraped_at": "2026-02-02T22:00:00"
    }
  ]
}
```

**`output/stats.json`** - Statistics summary:

```json
{
  "total_jobs": 15424,
  "total_companies": 43,
  "duplicates_removed": 780,
  "top_companies": [...],
  "top_locations": [...]
}
```

## Time Invested

| Phase | Task | Time |
|-------|------|------|
| 1 | Project setup | 15 min |
| 2 | Data preprocessing | 30 min |
| 3 | Reverse engineering | 45 min |
| 4 | Scraper components | 1 hour |
| 5 | Batch extraction | 3 hours |
| 6 | Output and docs | 30 min |
| **Total** | | **~6 hours** |
