"""Main script for batch job extraction from Avature sites."""

import json
import time
from pathlib import Path
from datetime import datetime

from src.scraper import AvatureScraper
from src.proxy_manager import ProxyManager


SITES_FILE = "input/retry_sites.txt"
PROXIES_FILE = "input/proxies.txt"
OUTPUT_FILE = "output/jobs.json"
PROGRESS_FILE = "output/progress.json"
SAVE_EVERY = 5
BATCH_SIZE = 20


def log(msg: str):
    """Print with flush for real-time output."""
    print(msg, flush=True)


def load_sites(filepath: str) -> list[str]:
    """Load list of sites to scrape."""
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]


def load_progress() -> dict:
    """Load progress from previous run."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "jobs": [], "failed": []}


def load_existing_jobs() -> list[dict]:
    """Load existing jobs from output file."""
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("jobs", [])
    return []


def save_progress(progress: dict):
    """Save current progress."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def save_jobs(jobs: list[dict], stats: dict):
    """Save final jobs output."""
    output = {
        "total_jobs": len(jobs),
        "stats": stats,
        "jobs": jobs,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def get_subdomain(url: str) -> str:
    """Extract subdomain from URL."""
    return url.split("//")[1].split(".")[0]


def main():
    """Run batch extraction on all valid sites."""
    log("=" * 50)
    log("AVATURE SCRAPER")
    log("=" * 50)
    
    proxy_manager = None
    if Path(PROXIES_FILE).exists():
        proxy_manager = ProxyManager(PROXIES_FILE)
        log(f"Proxies: {proxy_manager.total} loaded")
    else:
        log("Proxies: None (direct connection)")
    
    sites = load_sites(SITES_FILE)
    total_sites = len(sites)
    log(f"Sites: {total_sites}")
    
    progress = load_progress()
    completed = set(progress["completed"])
    all_jobs = load_existing_jobs()
    failed = progress["failed"]
    
    if completed:
        log(f"Resuming: {len(completed)} done")
    if all_jobs:
        log(f"Existing jobs: {len(all_jobs)}")
    
    pending = [s for s in sites if s not in completed]
    batch = pending[:BATCH_SIZE]
    
    log(f"Pending: {len(pending)} | Batch: {len(batch)}")
    log("-" * 50)
    
    start_time = time.time()
    
    for i, site_url in enumerate(batch, 1):
        site_num = len(completed) + i
        subdomain = get_subdomain(site_url)
        
        log(f"[{site_num}/{total_sites}] {subdomain}")
        site_start = time.time()
        
        try:
            with AvatureScraper(site_url, proxy_manager=proxy_manager) as scraper:
                jobs = scraper.get_all_jobs()
            
            site_time = time.time() - site_start
            log(f"  OK: {len(jobs)} jobs ({site_time:.1f}s)")
            
            for job in jobs:
                all_jobs.append(job.to_dict())
            
            completed.add(site_url)
            
        except Exception as e:
            site_time = time.time() - site_start
            error_msg = str(e)[:50]
            log(f"  FAIL: {error_msg} ({site_time:.1f}s)")
            failed.append({"site": site_url, "error": str(e)})
            completed.add(site_url)
        
        if i % SAVE_EVERY == 0:
            log(f"  [Saved: {len(all_jobs)} jobs]")
            save_progress({
                "completed": list(completed),
                "jobs": all_jobs,
                "failed": failed,
            })
    
    total_time = time.time() - start_time
    remaining = len(pending) - len(batch)
    
    log("")
    log("=" * 50)
    log("BATCH DONE")
    log(f"This batch: {len(batch)} sites")
    log(f"Total jobs: {len(all_jobs)}")
    log(f"Remaining: {remaining} sites")
    log(f"Time: {total_time:.0f}s ({total_time/60:.1f} min)")
    
    stats = {
        "total_sites": total_sites,
        "sites_completed": len(completed),
        "sites_remaining": remaining,
        "total_jobs": len(all_jobs),
        "time_seconds": round(total_time, 1),
        "date": datetime.now().isoformat(),
    }
    
    save_progress({
        "completed": list(completed),
        "jobs": [],
        "failed": failed,
    })
    
    save_jobs(all_jobs, stats)
    log(f"\nSaved: {OUTPUT_FILE}")
    
    if remaining > 0:
        log(f"\nRun again to process next {min(remaining, BATCH_SIZE)} sites")


if __name__ == "__main__":
    main()
