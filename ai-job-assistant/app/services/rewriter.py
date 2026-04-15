from typing import List


def generate_tailored_summary(resume_text: str, job_description: str) -> str:
    return (
        "Results-driven professional with experience aligned to the target role, "
        "including technical problem-solving, cross-functional collaboration, and "
        "data-informed decision-making. Brings relevant strengths from prior work "
        "and demonstrates readiness to contribute effectively in this position."
    )


def improve_bullets(bullets: List[str], job_description: str) -> List[str]:
    improved = []
    for bullet in bullets:
        improved.append(
            f"Enhanced: {bullet.strip()} with clearer impact, stronger action verbs, "
            f"and closer alignment to the target job requirements."
        )
    return improved
