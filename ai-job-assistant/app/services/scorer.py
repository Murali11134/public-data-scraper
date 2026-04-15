def calculate_match_score(matched_skills: list[str], missing_skills: list[str]) -> int:
    total = len(matched_skills) + len(missing_skills)
    if total == 0:
        return 50
    score = int((len(matched_skills) / total) * 100)
    return max(0, min(100, score))
