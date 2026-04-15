from typing import Dict, List
from app.services.extractor import extract_skills


def compare_resume_to_jd(resume_text: str, job_description: str) -> Dict[str, List[str]]:
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description))

    matched = sorted(resume_skills.intersection(jd_skills))
    missing = sorted(jd_skills.difference(resume_skills))

    return {
        "matched_skills": matched,
        "missing_skills": missing,
    }
