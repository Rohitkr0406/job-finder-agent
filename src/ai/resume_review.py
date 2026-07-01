# pyrefly: ignore [missing-import]
import litellm
from src.models.resume import ResumeProfile
from src.ai.prompts import load_resume_review_prompt
from src.utils.llm import configure_llm, get_model_string, acompletion_with_retry
from typing import Dict

async def generate_weekly_resume_insights(resume: ResumeProfile, missing_skills_freq: Dict[str, int]) -> str:
    if not missing_skills_freq:
        return "No missing skills identified this week. Keep maintaining your skillset!"
        
    configure_llm()
    prompt_tpl = load_resume_review_prompt()
    
    freq_lines = []
    for skill, freq in sorted(missing_skills_freq.items(), key=lambda x: x[1], reverse=True)[:15]:
        freq_lines.append(f"- {skill}: {freq} postings")
    missing_skills_str = "\n".join(freq_lines)
    
    prompt = prompt_tpl.format(
        candidate_name=resume.name,
        candidate_skills=", ".join(resume.skills),
        candidate_education=resume.education,
        candidate_experience=resume.experience,
        missing_skills_freq=missing_skills_str
    )
    
    try:
        resp = await acompletion_with_retry(
            model=get_model_string(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [Resume Review] Error generating weekly insights: {e}")
        return "Could not generate weekly recommendation due to an API error."
