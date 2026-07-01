import os
import sqlite3
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

ANALYTICS_DB_PATH = os.getenv("ANALYTICS_DB_PATH", "data/analytics.db")

def init_analytics_db():
    os.makedirs(os.path.dirname(ANALYTICS_DB_PATH) or ".", exist_ok=True)
    with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_stats (
                date          TEXT PRIMARY KEY,
                jobs_scraped  INTEGER,
                jobs_filtered INTEGER,
                duplicates    INTEGER,
                matched       INTEGER,
                top_score     INTEGER,
                average_score REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS missing_skills_history (
                date      TEXT,
                skill     TEXT,
                frequency INTEGER,
                PRIMARY KEY (date, skill)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS companies_history (
                date      TEXT,
                company   TEXT,
                frequency INTEGER,
                PRIMARY KEY (date, company)
            )
            """
        )
        conn.commit()
    print(f"  [DB] Analytics database initialized at {ANALYTICS_DB_PATH}")

def save_daily_analytics(
    date_str: str,
    jobs_scraped: int,
    jobs_filtered: int,
    duplicates: int,
    matched: int,
    top_score: int,
    average_score: float,
    missing_skills: Dict[str, int],
    companies: Dict[str, int]
):
    init_analytics_db()
    with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_stats (date, jobs_scraped, jobs_filtered, duplicates, matched, top_score, average_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (date_str, jobs_scraped, jobs_filtered, duplicates, matched, top_score, average_score)
        )
        
        for skill, freq in missing_skills.items():
            conn.execute(
                """
                INSERT OR REPLACE INTO missing_skills_history (date, skill, frequency)
                VALUES (?, ?, ?)
                """,
                (date_str, skill, freq)
            )
            
        for company, freq in companies.items():
            conn.execute(
                """
                INSERT OR REPLACE INTO companies_history (date, company, frequency)
                VALUES (?, ?, ?)
                """,
                (date_str, company, freq)
            )
        conn.commit()
    print(f"  [Analytics] Logged stats for {date_str}")

def get_weekly_aggregated_data(end_date_str: str, days: int = 7) -> Tuple[Dict[str, int], List[Tuple[str, int]]]:
    init_analytics_db()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=days-1)
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT skill, SUM(frequency) as total_freq 
            FROM missing_skills_history 
            WHERE date >= ? AND date <= ?
            GROUP BY skill
            ORDER BY total_freq DESC
            """,
            (start_date_str, end_date_str)
        )
        skills = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute(
            """
            SELECT company, SUM(frequency) as total_freq
            FROM companies_history
            WHERE date >= ? AND date <= ?
            GROUP BY company
            ORDER BY total_freq DESC
            LIMIT 10
            """,
            (start_date_str, end_date_str)
        )
        companies = [(row[0], row[1]) for row in cursor.fetchall()]
        
    return skills, companies
