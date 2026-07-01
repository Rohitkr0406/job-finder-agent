import json
import os
from typing import Dict

PREFERENCES_PATH = "config/preferences.json"

DEFAULT_PREFERENCES = {
  "experience": 2,
  "remote": True,
  "india": True,
  "internships": True,
  "require_salary": False,
  "excluded_departments": ["sales", "marketing", "hr", "recruiting", "legal", "finance", "design", "operations", "support", "admin"],
  "preferred_locations": ["bangalore", "bengaluru", "hyderabad", "pune", "noida", "gurgaon", "mumbai", "chennai", "remote", "india"],
  "preferred_roles": ["backend", "software engineer", "fullstack", "python", "developer", "data engineer"],
  "weights": {
    "skills": 0.5,
    "experience": 0.2,
    "location": 0.1,
    "title_similarity": 0.1,
    "remote_preference": 0.05,
    "education": 0.05
  }
}

def load_preferences() -> Dict:
    if not os.path.exists(PREFERENCES_PATH):
        return DEFAULT_PREFERENCES
    try:
        with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [Config] Error reading {PREFERENCES_PATH}: {e}. Using defaults.")
        return DEFAULT_PREFERENCES
