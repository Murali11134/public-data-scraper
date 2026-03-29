from fastapi import FastAPI
from app.resume_parser import load_resume
from app.scraper import scrape_job_description
from app.matcher import match_resume_to_job
from app.storage import save_job
from app.resume_parser import load_resume
from app.scraper import scrape_job_description
from app.matcher import match_resume_to_job
from app.storage import save_job

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Job Assistant is running 🚀"}

@app.get("/resume")
def get_resume():
    resume = load_resume()
    return {"resume": resume[:500]}



@app.get("/match")
def match(url: str):
    # ✅ Load resume
    resume = load_resume()

    # ✅ Get job description
    job_desc = scrape_job_description(url)

    # ✅ Run matching
    result = match_resume_to_job(resume, job_desc)

    # ✅ Save result
    save_job(url, result)

    return result