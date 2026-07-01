import json
# pyrefly: ignore [missing-import]
import litellm
from src.models.job import Job
from src.models.resume import ResumeProfile
from src.cache.ai_cache import get_ai_explanation, cache_ai_explanation
from src.ai.prompts import load_explanation_prompt
from src.utils.llm import configure_llm, get_model_string, acompletion_with_retry

async def explain_job(job: Job, resume: ResumeProfile) -> Job:
    # 1. Check Cache
    cached = get_ai_explanation(job.content_hash)
    if cached:
        job.ai_score = cached["score"]
        job.ai_confidence = cached["confidence"]
        job.ai_strengths = cached["strengths"]
        job.ai_missing = cached["missing"]
        job.ai_summary = cached["summary"]
        return job

    # 2. Cache Miss: Run LLM
    configure_llm()
    prompt_tpl = load_explanation_prompt()
    prompt = prompt_tpl.format(
        candidate_name=resume.name,
        candidate_skills=", ".join(resume.skills),
        candidate_education=resume.education,
        candidate_experience=resume.experience,
        company=job.company,
        title=job.title,
        location=job.location,
        department=job.department,
        source=job.source,
        description=job.requirements[:1500]
    )

    try:
        resp = await acompletion_with_retry(
            model=get_model_string(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        score = int(data.get("score", 0))
        confidence = str(data.get("confidence", "medium"))
        strengths = list(data.get("strengths", []))
        missing = list(data.get("missing", []))
        summary = str(data.get("summary", "No summary provided."))

        job.ai_score = score
        job.ai_confidence = confidence
        job.ai_strengths = strengths
        job.ai_missing = missing
        job.ai_summary = summary

        cache_ai_explanation(job.content_hash, score, confidence, strengths, missing, summary)
    except Exception as e:
        print(f"  [Explainer] Error explaining '{job.title}': {e}")
        job.ai_score = 0
        job.ai_confidence = "low"
        job.ai_strengths = []
        job.ai_missing = []
        job.ai_summary = f"Scoring failed: {str(e)}"

    return job
