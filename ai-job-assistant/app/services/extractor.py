import re
from typing import List, Set

COMMON_SKILLS = {
    "python", "java", "sql", "excel", "tableau", "power bi", "fastapi",
    "flask", "django", "pandas", "numpy", "machine learning", "deep learning",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "github",
    "rest api", "api", "data analysis", "data visualization", "statistics",
    "etl", "spark", "hadoop", "nlp", "llm", "gen ai", "openai",
    "communication", "leadership", "problem solving", "streamlit"
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\\s+", " ", text)
    return text


def extract_skills(text: str) -> List[str]:
    normalized = normalize_text(text)
    found: Set[str] = set()

    for skill in COMMON_SKILLS:
        if skill in normalized:
            found.add(skill)

    return sorted(found)


def extract_keywords(text: str) -> List[str]:
    normalized = normalize_text(text)
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\\+\\#\\.]{1,}", normalized)
    stopwords = {
        "the", "and", "with", "for", "that", "this", "from", "your", "have",
        "will", "into", "are", "our", "you", "job", "role", "team", "work",
        "using", "years", "year", "experience", "required", "preferred"
    }
    keywords = [t for t in tokens if t not in stopwords and len(t) > 2]
    return sorted(set(keywords))
