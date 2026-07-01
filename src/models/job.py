from dataclasses import dataclass, field
import hashlib
from typing import List, Dict, Optional

@dataclass
class Job:
    id: str
    company: str
    title: str
    location: str
    url: str
    posted_at: str
    source: str
    requirements: str
    department: str = ""
    
    # Extracted / Evaluated fields
    skills_extracted: List[str] = field(default_factory=list)
    python_score: float = 0.0
    ai_score: Optional[int] = None
    ai_confidence: Optional[str] = None
    ai_strengths: List[str] = field(default_factory=list)
    ai_missing: List[str] = field(default_factory=list)
    ai_summary: Optional[str] = None
    final_score: float = 0.0

    @property
    def content_hash(self) -> str:
        # Normalize and compute SHA-256 of company, title, location, requirements to handle repostings
        norm_requirements = self.requirements.strip()
        data = f"{self.company.strip().lower()}|{self.title.strip().lower()}|{self.location.strip().lower()}|{norm_requirements}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
        
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "url": self.url,
            "posted_at": self.posted_at,
            "source": self.source,
            "requirements": self.requirements,
            "department": self.department,
            "skills_extracted": self.skills_extracted,
            "python_score": self.python_score,
            "ai_score": self.ai_score,
            "ai_confidence": self.ai_confidence,
            "ai_strengths": self.ai_strengths,
            "ai_missing": self.ai_missing,
            "ai_summary": self.ai_summary,
            "final_score": self.final_score,
            "content_hash": self.content_hash
        }
