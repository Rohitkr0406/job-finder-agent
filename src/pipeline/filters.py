import re
from typing import List, Dict
from src.models.job import Job
from src.utils.config import load_preferences

_EXP_PATTERNS = [
    re.compile(r"\b([0-9]+)\s*\+\s*(?:years?|yrs?)\b", re.IGNORECASE),
    re.compile(r"\b([0-9]+)\s*-\s*([0-9]+)\s*(?:years?|yrs?)\b", re.IGNORECASE),
    re.compile(r"\b([0-9]+)\s*to\s*([0-9]+)\s*(?:years?|yrs?)\b", re.IGNORECASE),
    re.compile(r"\b([0-9]+)\s*(?:years?|yrs?)\b", re.IGNORECASE)
]

def extract_experience(title: str, requirements: str) -> int:
    text = (title + " " + requirements).lower()
    found_years = []
    
    for pattern in _EXP_PATTERNS:
        for match in pattern.finditer(text):
            try:
                # If it's a range match, take the upper bound (group 2)
                if len(match.groups()) >= 2 and match.group(2) is not None:
                    val = int(match.group(2))
                else:
                    val = int(match.group(1))
                found_years.append(val)
            except ValueError:
                continue
                
    if found_years:
        return max(found_years)
    return 0

def apply_hard_filters(jobs: List[Job]) -> List[Job]:
    preferences = load_preferences()
    max_exp = preferences.get("experience", 2)
    allow_internships = preferences.get("internships", True)
    require_salary = preferences.get("require_salary", False)
    
    excluded_depts = [d.lower() for d in preferences.get("excluded_departments", [])]
    preferred_locs = [l.lower() for l in preferences.get("preferred_locations", [])]
    
    filtered = []
    
    for job in jobs:
        title_lower = job.title.lower()
        desc_lower = job.requirements.lower()
        combined_lower = title_lower + " " + desc_lower
        
        # 1. Experience Check
        exp = extract_experience(job.title, job.requirements)
        if exp > max_exp:
            continue
            
        # 2. Internship Check
        is_internship = "intern" in title_lower or "internship" in title_lower or "intern" in desc_lower or "internship" in desc_lower
        if is_internship and not allow_internships:
            continue
            
        # 3. Department Check
        dept_lower = job.department.lower()
        if dept_lower and any(dept in dept_lower for dept in excluded_depts):
            continue
            
        # 4. Location Check
        location_lower = job.location.lower()
        is_remote = "remote" in location_lower or "remote" in combined_lower
        
        location_match = False
        if is_remote and preferences.get("remote", True):
            location_match = True
        else:
            for loc in preferred_locs:
                if loc in location_lower:
                    location_match = True
                    break
                    
        if not location_match:
            continue
            
        # 5. Salary Check
        if require_salary:
            has_salary = any(kw in desc_lower for kw in ["$", "rs.", "inr", "salary", "lpa", "compensation", "equity", "remuneration"])
            if not has_salary:
                continue
                
        filtered.append(job)
        
    print(f"  [Filters] Passed hard filters: {len(filtered)}/{len(jobs)} jobs")
    return filtered
