from src.models.job import Job
from src.models.resume import ResumeProfile
from src.extractors.skills import extract_skills
from src.pipeline.filters import extract_experience
from src.utils.config import load_preferences

def calculate_python_score(job: Job, resume: ResumeProfile) -> float:
    # 1. Skills Extract & Match (50%)
    job.skills_extracted = extract_skills(job.requirements + " " + job.title)
    overlap = set(job.skills_extracted) & set(resume.skills)
    
    if job.skills_extracted:
        skills_score = (len(overlap) / len(job.skills_extracted)) * 50.0
    else:
        skills_score = 30.0
        
    # 2. Experience Match (20%)
    req_exp = extract_experience(job.title, job.requirements)
    if req_exp <= 1:
        exp_score = 20.0
    elif req_exp == 2:
        exp_score = 15.0
    else:
        exp_score = 10.0
        
    # 3. Location Match (10%)
    loc_score = 0.0
    job_loc_lower = job.location.lower()
    pref_locations = [loc.lower() for loc in resume.preferred_locations] if resume.preferred_locations else []
    if not pref_locations:
        preferences = load_preferences()
        pref_locations = [loc.lower() for loc in preferences.get("preferred_locations", [])]
        
    if any(loc in job_loc_lower for loc in pref_locations):
        loc_score = 10.0
        
    # 4. Title Similarity / Role Fit (10%)
    role_score = 0.0
    job_title_lower = job.title.lower()
    pref_roles = [role.lower() for role in resume.preferred_roles] if resume.preferred_roles else []
    if not pref_roles:
        preferences = load_preferences()
        pref_roles = [role.lower() for role in preferences.get("preferred_roles", [])]
        
    if any(role in job_title_lower for role in pref_roles):
        role_score = 10.0
        
    # 5. Remote Preference (5%)
    remote_score = 0.0
    if "remote" in job_loc_lower or "remote" in (job.requirements.lower() + " " + job.title.lower()):
        remote_score = 5.0
        
    # 6. Education Match (5%)
    edu_score = 3.0
    job_desc_lower = job.requirements.lower()
    edu_kw = resume.education.lower() if resume.education else "degree"
    if edu_kw in job_desc_lower or "bachelor" in job_desc_lower or "degree" in job_desc_lower or "graduate" in job_desc_lower:
        edu_score = 5.0
        
    total_score = skills_score + exp_score + loc_score + role_score + remote_score + edu_score
    job.python_score = min(max(total_score, 0.0), 100.0)
    return job.python_score
