import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # ✅ NO spaces
FILE_PATH = os.path.join(BASE_DIR, "jobs.json")

def save_job(url, result):
    data = {
        "url": url,
        "match_score": result.get("match_score"),
        "matching_skills": result.get("matching_skills"),
        "missing_skills": result.get("missing_skills"),
        "suggestions": result.get("suggestions")
    }

    with open(FILE_PATH, "a") as f:
        f.write(json.dumps(data) + "\n")