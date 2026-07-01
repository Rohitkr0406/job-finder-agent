"""
verify_slugs.py
---------------
Run this ONCE before your first agent run to confirm which company
slugs in companies.txt are valid Greenhouse boards.

Usage:
    python verify_slugs.py

Invalid slugs produce a 404 from Greenhouse — safe to remove them.
"""

import requests
import time


def check_slug(slug: str):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        r = requests.get(url, timeout=8)
        count = len(r.json().get("jobs", [])) if r.status_code == 200 else 0
        return r.status_code, count
    except Exception as e:
        return 0, 0


def load_slugs(filepath: str = "companies.txt"):
    with open(filepath) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


if __name__ == "__main__":
    slugs = load_slugs()
    print(f"Checking {len(slugs)} slugs …\n")

    valid, invalid = [], []

    for slug in slugs:
        code, count = check_slug(slug)
        if code == 200:
            print(f"  ✅  {slug:<30} ({count} open jobs)")
            valid.append(slug)
        else:
            print(f"  ❌  {slug:<30} (HTTP {code})")
            invalid.append(slug)
        time.sleep(0.3)

    print(f"\n{'─'*50}")
    print(f"  ✅  Valid   : {len(valid)}")
    print(f"  ❌  Invalid : {len(invalid)}")

    if invalid:
        print(f"\nRemove these from companies.txt:")
        for s in invalid:
            print(f"    {s}")
