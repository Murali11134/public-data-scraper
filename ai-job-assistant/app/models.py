from typing import List
from pydantic import BaseModel, Field


class AnalyzeMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)


class AnalyzeMatchResponse(BaseModel):
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    suggestions: List[str]


class RewriteSummaryRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)


class RewriteSummaryResponse(BaseModel):
    tailored_summary: str


class ImproveBulletsRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)
    bullets: List[str]


class ImproveBulletsResponse(BaseModel):
    improved_bullets: List[str]
