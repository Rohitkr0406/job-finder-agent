from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ResumeProfile:
    name: str
    skills: List[str]
    education: str
    experience: str
    preferred_roles: List[str] = field(default_factory=list)
    preferred_locations: List[str] = field(default_factory=list)
    skill_categories: Dict[str, List[str]] = field(default_factory=dict)
    resume_hash: str = ""
    projects: List[str] = field(default_factory=list)
    github: Optional[str] = None
    portfolio: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "skills": self.skills,
            "education": self.education,
            "experience": self.experience,
            "preferred_roles": self.preferred_roles,
            "preferred_locations": self.preferred_locations,
            "skill_categories": self.skill_categories,
            "resume_hash": self.resume_hash,
            "projects": self.projects,
            "github": self.github,
            "portfolio": self.portfolio
        }
