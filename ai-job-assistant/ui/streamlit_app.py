import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="AI Job Assistant", layout="wide")
st.title("AI Job Assistant")

resume_text = st.text_area("Paste Resume Text", height=250)
job_description = st.text_area("Paste Job Description", height=250)

if st.button("Analyze Match"):
    response = requests.post(
        f"{API_BASE}/analyze-match",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
        },
        timeout=60,
    )
    if response.ok:
        data = response.json()
        st.subheader("Match Score")
        st.metric("Score", f"{data['match_score']}%")

        st.subheader("Matched Skills")
        st.write(data["matched_skills"])

        st.subheader("Missing Skills")
        st.write(data["missing_skills"])

        st.subheader("Suggestions")
        st.write(data["suggestions"])
    else:
        st.error("Failed to analyze match.")

st.divider()

if st.button("Generate Tailored Summary"):
    response = requests.post(
        f"{API_BASE}/rewrite-summary",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
        },
        timeout=60,
    )
    if response.ok:
        data = response.json()
        st.subheader("Tailored Summary")
        st.write(data["tailored_summary"])
    else:
        st.error("Failed to generate summary.")

st.divider()

bullets_input = st.text_area(
    "Paste Resume Bullets (one per line)",
    height=150,
)

if st.button("Improve Resume Bullets"):
    bullets = [line.strip() for line in bullets_input.splitlines() if line.strip()]
    response = requests.post(
        f"{API_BASE}/improve-bullets",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
            "bullets": bullets,
        },
        timeout=60,
    )
    if response.ok:
        data = response.json()
        st.subheader("Improved Bullets")
        for bullet in data["improved_bullets"]:
            st.write(f"- {bullet}")
    else:
        st.error("Failed to improve bullets.")
