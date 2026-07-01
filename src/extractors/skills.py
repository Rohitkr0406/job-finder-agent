import json
import os
import re
from typing import List

_patterns = {}
_initialized = False

def init_extractor(skills_json_path: str = "data/skills.json", force: bool = False):
    global _patterns, _initialized
    if _initialized and not force:
        return
    if not os.path.exists(skills_json_path):
        print(f"  [Skills Extractor] Warning: {skills_json_path} not found.")
        return
    if force:
        _patterns = {}
        
    try:
        with open(skills_json_path, "r", encoding="utf-8") as f:
            skills_data = json.load(f)
    except Exception as e:
        print(f"  [Skills Extractor] Error loading {skills_json_path}: {e}")
        skills_data = {}
        
    for category, skills in skills_data.items():
        for skill in skills:
            escaped = re.escape(skill)
            # Custom edge cases for C, C++, C#
            if skill.lower() == "c":
                pattern_str = r"\bC\b(?![+#])"
            elif skill.lower() in ("c++", "cplusplus"):
                pattern_str = r"\bC\+\+"
            elif skill.lower() in ("c#", "csharp"):
                pattern_str = r"\bC\#"
            else:
                start_boundary = r"\b" if skill[0].isalnum() else ""
                end_boundary = r"\b" if skill[-1].isalnum() else r"(?!\w)"
                pattern_str = f"{start_boundary}{escaped}{end_boundary}"
                
            _patterns[skill] = re.compile(pattern_str, re.IGNORECASE)
            
    _initialized = True

def extract_skills(text: str) -> List[str]:
    init_extractor()
    if not text:
        return []
    
    matched = []
    for skill, pattern in _patterns.items():
        if pattern.search(text):
            matched.append(skill)
    return sorted(list(set(matched)))
