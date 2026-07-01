import hashlib
import os
import json
import litellm
from src.models.resume import ResumeProfile
from src.cache.resume_cache import load_cached_resume, save_resume_cache
from src.utils.llm import configure_llm, get_model_string

def load_resume_text(path: str = "data/resume.pdf") -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Resume not found at: {path}\n"
            "Put your resume PDF/docx/text/markdown at data/resume.pdf or specify RESUME_PATH in .env"
        )

    errors = []

    # 1. Try parsing as PDF
    try:
        return _parse_pdf(path)
    except Exception as e:
        errors.append(f"PDF Parse Error: {e}")

    # 2. Try parsing as DOCX
    try:
        return _parse_docx(path)
    except Exception as e:
        errors.append(f"DOCX Parse Error: {e}")

    # 3. Try reading as plain text/markdown
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        errors.append(f"Text Parse Error: {e}")

    raise ValueError(
        f"Could not parse resume file at '{path}'. Tried PDF, DOCX, and Text.\n"
        "Details:\n" + "\n".join(errors)
    )


def _parse_docx(path: str) -> str:
    import zipfile
    import xml.etree.ElementTree as ET
    try:
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
        root = ET.fromstring(xml_content)
        text = []
        for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                text.append("".join(texts))
        return "\n".join(text).strip()
    except Exception as e:
        raise ValueError(f"Could not parse DOCX file structure: {e}")


def _parse_pdf(path: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages).strip()
        if text:
            return text
    except ImportError:
        pass
    except Exception as e:
        if "Is this really a PDF?" in str(e) or "No /Root object" in str(e) or "not a PDF" in str(e).lower():
            raise ValueError("Not a valid PDF file structure")
        print(f"  [Resume] pdfplumber failed: {e} — trying PyPDF2 …")

    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages  = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if text:
            return text
    except ImportError:
        pass
    except Exception as e:
        raise ValueError(f"PyPDF2 failed: {e}")

    raise ImportError(
        "Could not parse PDF. Install pdfplumber:\n"
        "  pip install pdfplumber"
    )

def parse_resume_profile(path: str = "data/resume.pdf") -> ResumeProfile:
    text = load_resume_text(path)
    resume_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    cached = load_cached_resume()
    if cached and cached.resume_hash == resume_hash:
        print("  [Resume] Loaded profile from cache (hash match)")
        return cached
        
    print("  [Resume] Parsing resume with LLM (cache miss/updated) ...")
    configure_llm()
    
    prompt = f"""\
You are an expert resume parser. Extract the structured details of the candidate's resume below.

RESUME CONTENT:
{text}

Extract and return ONLY a valid compact JSON object (no markdown, no backticks, no extra text):
{{
  "name": "<candidate's name>",
  "skills": [<list of all technical skills as strings>],
  "education": "<latest/highest degree (e.g. BCA, B.Tech, MS)>",
  "experience": "<fresher | X years of experience>",
  "preferred_roles": [<list of roles candidate is interested in (e.g. software engineer, backend, data engineer)>],
  "preferred_locations": [<list of preferred locations/cities/countries (e.g. bangalore, remote, india)>],
  "skill_categories": {{
    "languages": [<programming languages>],
    "frontend": [<frontend technologies>],
    "backend": [<backend technologies>],
    "databases": [<databases>],
    "devops_cloud": [<devops and cloud tools>]
  }},
  "projects": [<list of project names or short descriptions>],
  "github": "<github link or null>",
  "portfolio": "<portfolio link or null>"
}}
"""

    try:
        resp = litellm.completion(
            model=get_model_string(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        
        profile = ResumeProfile(
            name=str(data.get("name", "Candidate")),
            skills=list(data.get("skills", [])),
            education=str(data.get("education", "")),
            experience=str(data.get("experience", "Fresher")),
            preferred_roles=list(data.get("preferred_roles", [])),
            preferred_locations=list(data.get("preferred_locations", [])),
            skill_categories=dict(data.get("skill_categories", {})),
            resume_hash=resume_hash,
            projects=list(data.get("projects", [])),
            github=data.get("github"),
            portfolio=data.get("portfolio")
        )
        
        save_resume_cache(profile)
        print("  [Resume] Profile parsed and cached successfully!")
        return profile
    except Exception as e:
        print(f"  [Resume] LLM parsing failed: {e}. Fallback to basic profile.")
        from src.extractors.skills import extract_skills
        skills = extract_skills(text)
        profile = ResumeProfile(
            name="Candidate",
            skills=skills,
            education="Unknown",
            experience="Fresher",
            resume_hash=resume_hash
        )
        return profile
