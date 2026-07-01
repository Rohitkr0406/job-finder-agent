import os
import sqlite3
import json
from typing import List, Dict, Optional
from src.models.job import Job

DB_PATH = os.getenv("DB_PATH", "data/jobs.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                job_hash   TEXT PRIMARY KEY,
                first_seen TEXT DEFAULT (date('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_cache (
                job_hash   TEXT PRIMARY KEY,
                score      INTEGER,
                confidence TEXT,
                strengths  TEXT,
                missing    TEXT,
                summary    TEXT,
                timestamp  TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    print(f"  [DB] Jobs database initialized at {DB_PATH}")

def filter_new_jobs(jobs: List[Job]) -> List[Job]:
    """Return only jobs whose content hash hasn't been seen before."""
    with sqlite3.connect(DB_PATH) as conn:
        seen = {row[0] for row in conn.execute("SELECT job_hash FROM seen_jobs")}
    new = [j for j in jobs if j.content_hash not in seen]
    print(f"  [DB] {len(new)} new jobs (of {len(jobs)} total after pre-filter)")
    return new

def mark_jobs_seen(jobs: List[Job]):
    """Persist all scraped job hashes so they are skipped next run."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO seen_jobs (job_hash) VALUES (?)",
            [(j.content_hash,) for j in jobs],
        )
        conn.commit()
    print(f"  [DB] Marked {len(jobs)} jobs as seen")

def get_cached_ai(job_hash: str) -> Optional[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT score, confidence, strengths, missing, summary FROM ai_cache WHERE job_hash = ?",
            (job_hash,)
        )
        row = cursor.fetchone()
        if row:
            try:
                strengths = json.loads(row[2])
            except Exception:
                strengths = []
            try:
                missing = json.loads(row[3])
            except Exception:
                missing = []
            return {
                "score": row[0],
                "confidence": row[1],
                "strengths": strengths,
                "missing": missing,
                "summary": row[4]
            }
    return None

def set_cached_ai(job_hash: str, score: int, confidence: str, strengths: List[str], missing: List[str], summary: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO ai_cache (job_hash, score, confidence, strengths, missing, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_hash, score, confidence, json.dumps(strengths), json.dumps(missing), summary)
        )
        conn.commit()

def get_db_stats() -> Dict:
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(*) FROM seen_jobs WHERE first_seen = date('now')"
        ).fetchone()[0]
    return {"total_seen": total, "added_today": today}
