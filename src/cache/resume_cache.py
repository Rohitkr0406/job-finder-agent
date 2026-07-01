import json
import os
from typing import Optional
from src.models.resume import ResumeProfile

CACHE_PATH = "data/resume_profile.json"

def load_cached_resume() -> Optional[ResumeProfile]:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ResumeProfile(
            name=data.get("name", ""),
            skills=data.get("skills", []),
            education=data.get("education", ""),
            experience=data.get("experience", ""),
            preferred_roles=data.get("preferred_roles", []),
            preferred_locations=data.get("preferred_locations", []),
            skill_categories=data.get("skill_categories", {}),
            resume_hash=data.get("resume_hash", ""),
            projects=data.get("projects", []),
            github=data.get("github"),
            portfolio=data.get("portfolio")
        )
    except Exception as e:
        print(f"  [Resume Cache] Error reading cache: {e}")
        return None

def save_resume_cache(profile: ResumeProfile):
    os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)
    except Exception as e:
        print(f"  [Resume Cache] Error saving cache: {e}")
