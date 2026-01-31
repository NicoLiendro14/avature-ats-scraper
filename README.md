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

## Results

- **Total jobs found:** TBD
- **Sites checked:** TBD
- **Time spent:** TBD
