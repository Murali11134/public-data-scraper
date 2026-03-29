from app.llm import call_llm

def match_resume_to_job(resume, job_desc):

    resume = resume[:800]
    job_desc = job_desc[:800]

    prompt = f"""
    You are a strict JSON generator.

    DO NOT write anything except JSON.
    DO NOT explain.
    DO NOT add text.

    Return ONLY this format:

    {{
      "match_score": 0-100,
      "matching_skills": ["skill1", "skill2"],
      "missing_skills": ["skill1"],
      "suggestions": ["suggestion1"]
    }}

    Resume:
    {resume[:800]}

    Job:
    {job_desc[:800]}
    """

    result = call_llm(prompt)
    return result