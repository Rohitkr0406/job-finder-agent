"""
scraper.py
----------
Pulls jobs from three completely free, API-based sources:
  1. Greenhouse boards API  (structured JSON, no auth)
  2. Lever postings API      (structured JSON, no auth)
  3. HN/YC Jobs via Firebase API (no auth, no scraping)

Then applies a keyword pre-filter to weed out senior roles before
sending anything to the LLM, saving API tokens.
"""

import os
import re
import time
import json
import requests
from typing import List, Dict


# ── Helpers ────────────────────────────────────────────────────────────────────

def _strip_html(html: str) -> str:
    text = re.sub(r"<[^<]+?>", " ", html or "")
    return " ".join(text.split())


def _load_manual_slugs(filepath: str) -> List[str]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def _load_discovered_slugs(filepath: str) -> Dict[str, str]:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
            return {slug: info.get("company", slug) for slug, info in data.items()}
    except Exception as e:
        print(f"  [Scraper] ⚠ Error loading {filepath}: {e}")
        return {}


# ── 1. Greenhouse ──────────────────────────────────────────────────────────────

def _fetch_greenhouse(slug: str, pretty_name: str = None) -> List[Dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    comp_name = pretty_name or slug.replace("-", " ").title()
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []

        jobs = r.json().get("jobs", [])
        results = []
        for job in jobs:
            depts = job.get("departments") or []
            dept = depts[0].get("name", "") if depts else ""
            results.append({
                "id":           f"gh_{job['id']}",
                "company":      comp_name,
                "title":        job.get("title", ""),
                "location":     job.get("location", {}).get("name", "Unknown"),
                "url":          job.get("absolute_url", ""),
                "posted_at":    job.get("updated_at", ""),
                "source":       "Greenhouse",
                "requirements": _strip_html(job.get("content", ""))[:2000],
                "department":   dept,
            })
        return results
    except Exception as e:
        print(f"  [Greenhouse] ⚠ {slug}: {e}")
        return []


def _scrape_greenhouse(slugs_with_names: List[tuple], manual_slugs: set) -> List[Dict]:
    all_jobs: List[Dict] = []
    for slug, pretty_name in slugs_with_names:
        jobs = _fetch_greenhouse(slug, pretty_name)
        if jobs:
            print(f"  [Greenhouse] ✅ {slug}: {len(jobs)} jobs")
        elif slug in manual_slugs:
            print(f"  [Greenhouse] — {slug}: 0 jobs (invalid slug or no openings)")
        all_jobs.extend(jobs)
        time.sleep(0.4)   # be polite to the API
    return all_jobs


# ── 2. Lever ───────────────────────────────────────────────────────────────────

def _fetch_lever(slug: str, pretty_name: str = None) -> List[Dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    comp_name = pretty_name or slug.replace("-", " ").title()
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        
        postings = r.json()
        if not isinstance(postings, list):
            return []
            
        results = []
        for job in postings:
            categories = job.get("categories") or {}
            dept = categories.get("department", "") or categories.get("team", "")
            loc = categories.get("location", "Unknown")
            
            # Extract plain text description and lists
            desc = job.get("descriptionBodyPlain") or job.get("descriptionPlain") or ""
            list_parts = []
            for lst in job.get("lists", []):
                title = lst.get("text", "")
                content = _strip_html(lst.get("content", ""))
                list_parts.append(f"{title}: {content}")
            reqs = desc + "\n" + "\n".join(list_parts)
            
            results.append({
                "id":           f"lev_{job['id']}",
                "company":      comp_name,
                "title":        job.get("text", ""),
                "location":     loc,
                "url":          job.get("hostedUrl", ""),
                "posted_at":    str(job.get("createdAt", "")),
                "source":       "Lever",
                "requirements": reqs[:2000],
                "department":   dept,
            })
        return results
    except Exception as e:
        print(f"  [Lever] ⚠ {slug}: {e}")
        return []


def _scrape_lever(slugs_with_names: List[tuple], manual_slugs: set) -> List[Dict]:
    all_jobs: List[Dict] = []
    for slug, pretty_name in slugs_with_names:
        jobs = _fetch_lever(slug, pretty_name)
        if jobs:
            print(f"  [Lever] ✅ {slug}: {len(jobs)} jobs")
        elif slug in manual_slugs:
            print(f"  [Lever] — {slug}: 0 jobs (invalid slug or no openings)")
        all_jobs.extend(jobs)
        time.sleep(0.4)   # be polite to the API
    return all_jobs


# ── 3. HN / YC Jobs (Firebase API) ────────────────────────────────────────────

HN_API = "https://hacker-news.firebaseio.com/v0"


def _extract_company_hn(title: str) -> str:
    """'Acme Inc (YC W24) is hiring ...' → 'Acme Inc'"""
    m = re.match(r"^([^(|–\-:]+)", title)
    return m.group(1).strip() if m else title.split()[0]


def _extract_location_hn(text: str) -> str:
    if not text:
        return "Check posting"
    if re.search(r"\bremote\b", text, re.IGNORECASE):
        return "Remote"
    m = re.search(
        r"(?:location|based in|office in|located in)[:\s]+([^\n<.]{3,60})",
        text, re.IGNORECASE,
    )
    return m.group(1).strip() if m else "Check posting"


def _scrape_hn_jobs(limit: int = 60) -> List[Dict]:
    try:
        r = requests.get(f"{HN_API}/jobstories.json", timeout=10)
        job_ids = r.json()[:limit]
    except Exception as e:
        print(f"  [HN] ⚠ Could not fetch job IDs: {e}")
        return []

    jobs: List[Dict] = []
    for jid in job_ids:
        try:
            item = requests.get(f"{HN_API}/item/{jid}.json", timeout=5).json()
            if not item or item.get("type") != "job":
                continue
            text_clean = _strip_html(item.get("text", ""))
            url = item.get("url") or f"https://news.ycombinator.com/item?id={jid}"
            jobs.append({
                "id":           f"hn_{jid}",
                "company":      _extract_company_hn(item.get("title", "")),
                "title":        item.get("title", ""),
                "location":     _extract_location_hn(text_clean),
                "url":          url,
                "posted_at":    str(item.get("time", "")),
                "source":       "YC / HN Jobs",
                "requirements": text_clean[:2000],
                "department":   "",
            })
            time.sleep(0.1)
        except Exception:
            continue

    print(f"  [HN] ✅ {len(jobs)} YC/HN jobs fetched")
    return jobs


# ── 4. Pre-filter (before LLM scoring) ────────────────────────────────────────

_SENIOR = re.compile(
    r"\b(senior|sr\b|lead\b|principal|staff engineer|director|vp\b|"
    r"vice president|head of|hiring manager|cto|ceo|chief|founder|"
    r"[5-9]\+\s*years?|[1-9][0-9]+\s*years?)\b",
    re.IGNORECASE,
)
_FRESHER = re.compile(
    r"\b(intern|internship|fresher|entry[\s\-]?level|junior|graduate|"
    r"new\s*grad|recent\s*grad|associate|trainee|apprentice|"
    r"0[\s\-]?[–\-]?\s*1\s*year|no experience)\b",
    re.IGNORECASE,
)


def _pre_filter(jobs: List[Dict]) -> List[Dict]:
    """
    Pass a job if:
      - Title/requirements mention a fresher keyword, OR
      - Title/requirements have no senior keyword at all.
    This cuts LLM calls by ~60-70%.
    """
    kept = []
    for job in jobs:
        combined = (job["title"] + " " + job["requirements"]).lower()
        is_senior  = bool(_SENIOR.search(combined))
        is_fresher = bool(_FRESHER.search(combined))
        if is_fresher or not is_senior:
            kept.append(job)

    print(f"  [Pre-filter] {len(kept)}/{len(jobs)} jobs passed fresher filter")
    return kept


# ── Public entry ───────────────────────────────────────────────────────────────

def scrape_all_jobs() -> List[Dict]:
    # --- Greenhouse ---
    gh_manual = _load_manual_slugs("companies.txt")
    gh_discovered = _load_discovered_slugs("data/discovered_greenhouse.json")
    
    gh_slugs_to_scrape = {}
    for slug in gh_manual:
        gh_slugs_to_scrape[slug] = slug.replace("-", " ").title()
    for slug, name in gh_discovered.items():
        gh_slugs_to_scrape[slug] = name
        
    print(f"\n📡 Scraping Greenhouse ({len(gh_slugs_to_scrape)} companies) ...")
    gh_tuples = list(gh_slugs_to_scrape.items())
    gh_jobs = _scrape_greenhouse(gh_tuples, set(gh_manual))

    # --- Lever ---
    lev_manual = _load_manual_slugs("companies_lever.txt")
    lev_discovered = _load_discovered_slugs("data/discovered_lever.json")
    
    lev_slugs_to_scrape = {}
    for slug in lev_manual:
        lev_slugs_to_scrape[slug] = slug.replace("-", " ").title()
    for slug, name in lev_discovered.items():
        lev_slugs_to_scrape[slug] = name
        
    print(f"\n📡 Scraping Lever ({len(lev_slugs_to_scrape)} companies) ...")
    lev_tuples = list(lev_slugs_to_scrape.items())
    lev_jobs = _scrape_lever(lev_tuples, set(lev_manual))

    # --- HN / YC Jobs ---
    print("\n📡 Scraping HN / YC Jobs ...")
    hn_jobs = _scrape_hn_jobs()

    all_jobs = gh_jobs + lev_jobs + hn_jobs
    print(f"\n  Total before filter : {len(all_jobs)}")
    return _pre_filter(all_jobs)
