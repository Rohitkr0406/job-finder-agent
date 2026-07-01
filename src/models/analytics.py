from dataclasses import dataclass
from typing import Dict

@dataclass
class AnalyticsEntry:
    date: str
    jobs_scraped: int
    jobs_filtered: int
    duplicates: int
    matched: int
    top_score: int
    average_score: float
