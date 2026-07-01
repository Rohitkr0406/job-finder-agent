from typing import Optional, Dict
from src.database.jobs import get_cached_ai, set_cached_ai

def get_ai_explanation(job_hash: str) -> Optional[Dict]:
    return get_cached_ai(job_hash)

def cache_ai_explanation(job_hash: str, score: int, confidence: str, strengths: list, missing: list, summary: str):
    set_cached_ai(job_hash, score, confidence, strengths, missing, summary)
