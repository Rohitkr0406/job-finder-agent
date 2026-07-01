import os
import asyncio
from datetime import date
from typing import List, Dict, Tuple
import telegram.error
from telegram import Bot
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from src.models.job import Job
from src.models.resume import ResumeProfile

async def _send_message_with_retry(
    bot: Bot,
    chat_id: str,
    text: str,
    parse_mode: ParseMode,
    disable_web_page_preview: bool = None,
    retries: int = 3,
    delay: float = 3.0
):
    for attempt in range(retries):
        try:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
            )
        except (telegram.error.TimedOut, telegram.error.NetworkError) as e:
            if isinstance(e, telegram.error.BadRequest):
                raise e
            if attempt == retries - 1:
                raise e
            print(f"  [Telegram] WARNING: Timeout/Network error (attempt {attempt + 1}/{retries}): {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)



DEFAULT_HEADER_TEMPLATE = """\
🤖 <b>Job Finder Agent v2</b>  ·  {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total openings today : <b>{total_jobs}</b>
🔥 High match (85+)    : <b>{high_count}</b>
✅ Good match (70–84)  : <b>{good_count}</b>
📋 Decent match (55–69) : <b>{decent_count}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<i>Sorted by match score · fresher-friendly only</i>
"""

DEFAULT_JOB_TEMPLATE = """\
🏢 <b>{company}</b>
💼 <b>{title}</b>
📍 <b>{location}</b>
{score_emoji} <b>Match:</b> {score}% ({confidence} confidence)
────────────────
✅ <b>Skills Matched</b>
{skills_matched}
────────────────
📚 <b>Missing</b>
{skills_missing}
────────────────
🤖 <b>AI Summary</b>
<i>{summary}</i>
────────────────
🔗 <a href="{url}">Apply Here ↗</a>
"""

DEFAULT_WEEKLY_TEMPLATE = """\
📊 <b>Weekly Career Insights & Resume Review</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 <b>Top Hiring Companies:</b>
{top_companies}

🛠 <b>Top Requested Tech:</b>
{top_skills}

────────────────
💡 <b>Weekly Learning & Resume Recommendations:</b>
{insights}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 <i>Keep building and learning!</i>
"""

def load_template(filename: str, default_content: str) -> str:
    path = os.path.join("templates", filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return default_content

def _score_emoji(score: float) -> str:
    if score >= 80:
        return "🟢"
    if score >= 60:
        return "🟡"
    return "🔴"

async def send_daily_report(jobs: List[Job]):
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID",   "").strip()

    if not token or not chat_id:
        print("  [Telegram] WARNING: Missing BOT_TOKEN or CHAT_ID - skipping daily notification")
        return

    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=15.0,
        connection_pool_size=8
    )
    bot = Bot(token=token, request=request)
    
    header_tpl = load_template("telegram_report_header.html", DEFAULT_HEADER_TEMPLATE)
    today_str = date.today().strftime("%B %d, %Y")
    
    high = sum(1 for j in jobs if j.final_score >= 80)
    good = sum(1 for j in jobs if 60 <= j.final_score < 80)
    decent = sum(1 for j in jobs if 40 <= j.final_score < 60)
    
    header_text = header_tpl.format(
        date=today_str,
        total_jobs=len(jobs),
        high_count=high,
        good_count=good,
        decent_count=decent
    )
    
    await _send_message_with_retry(
        bot=bot,
        chat_id=chat_id,
        text=header_text,
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(0.8)

    job_tpl = load_template("telegram_job.html", DEFAULT_JOB_TEMPLATE)
    divider = f"\n{'─' * 28}\n"
    
    current_cards = []
    current_len = 0
    chunk_start_idx = 1
    
    for idx, job in enumerate(jobs):
        matched = ", ".join(job.ai_strengths) if job.ai_strengths else "None"
        missing = ", ".join(job.ai_missing) if job.ai_missing else "None"
        
        card = job_tpl.format(
            company=job.company,
            title=job.title,
            location=job.location,
            score_emoji=_score_emoji(job.final_score),
            score=int(job.final_score),
            confidence=job.ai_confidence or "medium",
            skills_matched=matched,
            skills_missing=missing,
            summary=job.ai_summary or "No summary.",
            url=job.url
        )
        
        card_len = len(card)
        if not current_cards:
            projected_len = card_len
        else:
            projected_len = current_len + len(divider) + card_len
            
        if projected_len > 4000:
            body = divider.join(current_cards)
            try:
                await _send_message_with_retry(
                    bot=bot,
                    chat_id=chat_id,
                    text=body,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except Exception as e:
                print(f"  [Telegram] WARNING: Failed to send chunk starting at #{chunk_start_idx}: {e}")
            await asyncio.sleep(0.8)
            
            current_cards = [card]
            current_len = card_len
            chunk_start_idx = idx + 1
        else:
            current_cards.append(card)
            current_len = projected_len
            
    if current_cards:
        body = divider.join(current_cards)
        try:
            await _send_message_with_retry(
                bot=bot,
                chat_id=chat_id,
                text=body,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"  [Telegram] WARNING: Failed to send chunk starting at #{chunk_start_idx}: {e}")
        await asyncio.sleep(0.8)

    footer = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ <b>End of today's report.</b>\nGood luck, boss! 🚀"
    await _send_message_with_retry(
        bot=bot,
        chat_id=chat_id,
        text=footer,
        parse_mode=ParseMode.HTML,
    )
    print(f"  [Telegram] ✅ Daily report sent — {len(jobs)} jobs")

async def send_weekly_report(
    resume: ResumeProfile,
    insights: str,
    top_companies: List[Tuple[str, int]],
    top_skills: List[Tuple[str, int]]
):
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID",   "").strip()

    if not token or not chat_id:
        print("  [Telegram] WARNING: Missing BOT_TOKEN or CHAT_ID - skipping weekly insights notification")
        return

    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=15.0,
        connection_pool_size=8
    )
    bot = Bot(token=token, request=request)
    
    comp_lines = [f"- {comp}: {freq} openings" for comp, freq in top_companies]
    comp_str = "\n".join(comp_lines) if comp_lines else "None recorded."
    
    skills_lines = [f"- {skill}: {freq} requested" for skill, freq in top_skills]
    skills_str = "\n".join(skills_lines) if skills_lines else "None recorded."
    
    weekly_tpl = load_template("telegram_weekly_report.html", DEFAULT_WEEKLY_TEMPLATE)
    weekly_text = weekly_tpl.format(
        top_companies=comp_str,
        top_skills=skills_str,
        insights=insights
    )
    
    await _send_message_with_retry(
        bot=bot,
        chat_id=chat_id,
        text=weekly_text,
        parse_mode=ParseMode.HTML,
    )
    print("  [Telegram] ✅ Weekly career insights report sent")
