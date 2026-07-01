import os

PROMPTS_DIR = "prompts"

DEFAULT_EXPLANATION = """\
You are a precise job-fit evaluator for a junior/fresher candidate.

CANDIDATE RESUME PROFILE:
Name: {candidate_name}
Skills: {candidate_skills}
Education: {candidate_education}
Experience: {candidate_experience}

JOB POSTING:
Company: {company}
Title: {title}
Location: {location}
Department: {department}
Source: {source}
Description: {description}

TASK:
Analyze the match between the candidate and the job.
Evaluate the score (0-100) based on how well the candidate's skills, experience, and education fit the job.

Return ONLY a valid compact JSON object (no markdown, no backticks, no extra text):
{{"score": <int>, "confidence": "<high|medium|low>", "strengths": [<list of matched skills as strings>], "missing": [<list of missing skills required by the job>], "summary": "<concise reason of max 40 words>"}}
"""

DEFAULT_RESUME_REVIEW = """\
You are an expert career coach and technical resume reviewer.

CANDIDATE RESUME PROFILE:
Name: {candidate_name}
Skills: {candidate_skills}
Education: {candidate_education}
Experience: {candidate_experience}

MISSING SKILLS DATA:
Below is a frequency count of missing skills extracted from job postings that the candidate matched/applied to recently:
{missing_skills_freq}

TASK:
Provide a concise, action-oriented recommendation (maximum 80 words) advising the candidate on:
1. Which skills they should prioritize learning first (based on frequency and candidate's current background).
2. How to update their resume or portfolio to stand out.

Return your response as plain text without any markdown bold or headers, keeping it short and conversational.
"""

def load_explanation_prompt() -> str:
    path = os.path.join(PROMPTS_DIR, "explanation.txt")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return DEFAULT_EXPLANATION

def load_resume_review_prompt() -> str:
    path = os.path.join(PROMPTS_DIR, "resume_review.txt")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return DEFAULT_RESUME_REVIEW
