import os
import asyncio
from datetime import datetime
from typing import List

from src.models.job import Job
from src.extractors.resume import parse_resume_profile
from src.scraper import scrape_all_jobs
from src.database.jobs import init_db, filter_new_jobs, mark_jobs_seen, get_db_stats
from src.database.analytics import init_analytics_db, save_daily_analytics, get_weekly_aggregated_data
from src.pipeline.filters import apply_hard_filters
from src.pipeline.scoring import calculate_python_score
from src.pipeline.ranking import rank_jobs
from src.notifications.telegram import send_daily_report, send_weekly_report
from src.ai.resume_review import generate_weekly_resume_insights

RESUME_PATH = os.getenv("RESUME_PATH", "data/resume.pdf")
TOP_N = int(os.getenv("TOP_N", "25"))

async def run_pipeline():
    print("=" * 52)
    print("🤖  Job Finder Agent v2  —  Running Pipeline")
    print("=" * 52)

    init_db()
    init_analytics_db()

    resume = parse_resume_profile(RESUME_PATH)
    print(f"✅ Resume profile loaded for: {resume.name}")
    print(f"   Skills extracted from resume: {len(resume.skills)}")

    raw_jobs = scrape_all_jobs()
    print(f"📡 Scraped {len(raw_jobs)} jobs after initial title pre-filter.")

    jobs = [
        Job(
            id=j["id"],
            company=j["company"],
            title=j["title"],
            location=j["location"],
            url=j["url"],
            posted_at=j["posted_at"],
            source=j["source"],
            requirements=j["requirements"],
            department=j.get("department", "")
        )
        for j in raw_jobs
    ]

    new_jobs = filter_new_jobs(jobs)
    duplicates_count = len(jobs) - len(new_jobs)

    today_str = datetime.now().strftime("%Y-%m-%d")

    if not new_jobs:
        print("\nℹ️  No new jobs today — nothing to evaluate.")
        save_daily_analytics(
            date_str=today_str,
            jobs_scraped=len(raw_jobs),
            jobs_filtered=0,
            duplicates=duplicates_count,
            matched=0,
            top_score=0,
            average_score=0.0,
            missing_skills={},
            companies={}
        )
        stats_db = get_db_stats()
        print(f"   DB total seen: {stats_db['total_seen']}")
        return

    filtered_jobs = apply_hard_filters(new_jobs)
    filtered_count = len(new_jobs) - len(filtered_jobs)

    for job in filtered_jobs:
        calculate_python_score(job, resume)

    ranked_jobs = await rank_jobs(filtered_jobs, resume)
    print(f"🏆 Ranked {len(ranked_jobs)} candidate jobs.")

    mark_jobs_seen(jobs)

    top_score = 0
    avg_score = 0.0
    missing_skills = {}
    companies = {}

    if ranked_jobs:
        top_score = int(max(j.final_score for j in ranked_jobs))
        avg_score = sum(j.final_score for j in ranked_jobs) / len(ranked_jobs)
        
        for job in ranked_jobs:
            for skill in job.ai_missing:
                missing_skills[skill] = missing_skills.get(skill, 0) + 1
                
        for job in ranked_jobs:
            companies[job.company] = companies.get(job.company, 0) + 1

    save_daily_analytics(
        date_str=today_str,
        jobs_scraped=len(raw_jobs),
        jobs_filtered=filtered_count,
        duplicates=duplicates_count,
        matched=len(ranked_jobs),
        top_score=top_score,
        average_score=avg_score,
        missing_skills=missing_skills,
        companies=companies
    )

    top_n_jobs = ranked_jobs[:TOP_N]
    if top_n_jobs:
        print(f"📱 Sending report of top {len(top_n_jobs)} jobs to Telegram...")
        await send_daily_report(top_n_jobs)
    else:
        print("ℹ️  No jobs matched the report criteria today.")

    is_sunday = datetime.now().strftime("%A") == "Sunday"
    if is_sunday:
        print("\n📅 Sunday detected — generating weekly career insights...")
        weekly_skills, weekly_companies = get_weekly_aggregated_data(today_str, days=7)
        
        insights = await generate_weekly_resume_insights(resume, weekly_skills)
        
        top_weekly_companies = sorted(weekly_companies, key=lambda x: x[1], reverse=True)[:5]
        top_weekly_skills = sorted(weekly_skills.items(), key=lambda x: x[1], reverse=True)[:10]
        
        await send_weekly_report(
            resume=resume,
            insights=insights,
            top_companies=top_weekly_companies,
            top_skills=top_weekly_skills
        )

    stats_db = get_db_stats()
    print(f"\n✅ Pipeline complete! DB total seen: {stats_db['total_seen']}")
