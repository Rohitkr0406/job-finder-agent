import asyncio
import aiohttp
import json
import re

# Fetch YC hiring companies
YC_HIRING_URL = "https://yc-oss.github.io/api/companies/hiring.json"

def clean_slug_candidates(name, slug):
    candidates = []
    # 1. YC Slug
    if slug:
        candidates.append(slug.lower().strip())
    # 2. Lowercase name stripped of special characters
    cleaned_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower().strip()
    if cleaned_name and cleaned_name not in candidates:
        candidates.append(cleaned_name)
    # 3. Dashed lowercase name
    dashed_name = re.sub(r'[^a-zA-Z0-9\s-]', '', name).replace(' ', '-').lower().strip()
    # clean multiple dashes
    dashed_name = re.sub(r'-+', '-', dashed_name)
    if dashed_name and dashed_name not in candidates:
        candidates.append(dashed_name)
    return candidates

async def check_greenhouse(session, slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "jobs" in data:
                    return len(data["jobs"])
    except Exception:
        pass
    return None

async def check_lever(session, slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list):
                    return len(data)
    except Exception:
        pass
    return None

async def process_company(session, company, semaphore):
    name = company.get("name", "")
    yc_slug = company.get("slug", "")
    candidates = clean_slug_candidates(name, yc_slug)
    
    gh_match = None
    lev_match = None
    
    for candidate in candidates:
        async with semaphore:
            # Check Greenhouse
            gh_jobs = await check_greenhouse(session, candidate)
            if gh_jobs is not None:
                gh_match = (candidate, gh_jobs)
                break
                
            # Check Lever
            lev_jobs = await check_lever(session, candidate)
            if lev_jobs is not None:
                lev_match = (candidate, lev_jobs)
                break
                
    return name, gh_match, lev_match

async def main():
    print("Fetching hiring YC companies...")
    async with aiohttp.ClientSession() as session:
        async with session.get(YC_HIRING_URL) as r:
            if r.status != 200:
                print("Failed to fetch YC hiring companies list.")
                return
            companies = await r.json()
            
        print(f"Loaded {len(companies)} companies. Scanning...")
        
        semaphore = asyncio.Semaphore(50)  # limit concurrency to be nice
        tasks = [process_company(session, comp, semaphore) for comp in companies]
        
        results = await asyncio.gather(*tasks)
        
        greenhouse_slugs = {}
        lever_slugs = {}
        
        for name, gh, lev in results:
            if gh:
                greenhouse_slugs[gh[0]] = {"company": name, "job_count": gh[1]}
            elif lev:
                lever_slugs[lev[0]] = {"company": name, "job_count": lev[1]}
                
        print(f"\nScan complete!")
        print(f"Found {len(greenhouse_slugs)} Greenhouse slugs.")
        print(f"Found {len(lever_slugs)} Lever slugs.")
        
        # Save results
        with open("data/discovered_greenhouse.json", "w", encoding="utf-8") as f:
            json.dump(greenhouse_slugs, f, indent=2)
        with open("data/discovered_lever.json", "w", encoding="utf-8") as f:
            json.dump(lever_slugs, f, indent=2)
            
        print("Saved discovered boards to data/discovered_greenhouse.json and data/discovered_lever.json")

if __name__ == "__main__":
    asyncio.run(main())
