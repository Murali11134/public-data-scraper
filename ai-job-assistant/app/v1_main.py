from fastapi import FastAPI
from app.models import (
    AnalyzeMatchRequest,
    AnalyzeMatchResponse,
    RewriteSummaryRequest,
    RewriteSummaryResponse,
    ImproveBulletsRequest,
    ImproveBulletsResponse,
)
from app.services.matcher import compare_resume_to_jd
from app.services.scorer import calculate_match_score
from app.services.rewriter import generate_tailored_summary, improve_bullets

app = FastAPI(title="AI Job Assistant", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze-match", response_model=AnalyzeMatchResponse)
def analyze_match(payload: AnalyzeMatchRequest):
    result = compare_resume_to_jd(payload.resume_text, payload.job_description)
    score = calculate_match_score(
        result["matched_skills"],
        result["missing_skills"],
    )

    suggestions = []
    if result["missing_skills"]:
        suggestions.append(
            "Add relevant missing skills only if you genuinely have them."
        )
    if result["matched_skills"]:
        suggestions.append(
            "Highlight matched skills more clearly in your summary and experience bullets."
        )
    if not suggestions:
        suggestions.append(
            "Add more role-specific keywords and measurable achievements."
        )

    return AnalyzeMatchResponse(
        match_score=score,
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        suggestions=suggestions,
    )


@app.post("/rewrite-summary", response_model=RewriteSummaryResponse)
def rewrite_summary(payload: RewriteSummaryRequest):
    summary = generate_tailored_summary(
        payload.resume_text,
        payload.job_description,
    )
    return RewriteSummaryResponse(tailored_summary=summary)


@app.post("/improve-bullets", response_model=ImproveBulletsResponse)
def improve_resume_bullets(payload: ImproveBulletsRequest):
    result = improve_bullets(payload.bullets, payload.job_description)
    return ImproveBulletsResponse(improved_bullets=result)
