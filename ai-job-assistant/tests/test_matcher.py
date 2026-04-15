from app.services.matcher import compare_resume_to_jd
from app.services.scorer import calculate_match_score


def test_compare_resume_to_jd():
    resume = "Python SQL FastAPI Git"
    jd = "Looking for Python SQL Docker AWS FastAPI"

    result = compare_resume_to_jd(resume, jd)

    assert "python" in result["matched_skills"]
    assert "sql" in result["matched_skills"]
    assert "fastapi" in result["matched_skills"]
    assert "docker" in result["missing_skills"]
    assert "aws" in result["missing_skills"]


def test_calculate_match_score():
    score = calculate_match_score(["python", "sql"], ["aws", "docker"])
    assert score == 50
