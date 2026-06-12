from fastapi import FastAPI
from typing import List
from random import sample
from datetime import date
from uuid import uuid4
from job import Job

app = FastAPI(title="Seek Jobs API")

# Define sample data (dicts instead of Job instances)
JOB_POOL = [
    {
        "title": "Developer",
        "company": "Data Processors Pty Ltd",
        "location": "Melbourne, VIC, Australia",
        "description": "Build and maintain pipelines.",
        "requirements": ["Python", "SQL", "Docker"],
        "responsibilities": ["Validate and transform data", "Deploy pipelines"],
        "employment_type": "Full-time",
        "salary_range": "Negotiable",
        "posted_date": date(2026, 6, 1),
        "skills": ["Python", "SQL", "Docker"]
    },
    {
        "title": "Junior Data Engineer",
        "company": "Tech Innovators Pty Ltd",
        "location": "Sydney, NSW, Australia",
        "description": "Support ETL pipelines and data transformation.",
        "requirements": ["Python", "SQL", "ETL basics"],
        "employment_type": "Full-time",
        "posted_date": date(2026, 5, 20),
        "skills": ["Python", "SQL"]
    },
    {
        "title": "Backend Developer",
        "company": "Cloud Solutions Pty Ltd",
        "location": "Brisbane, QLD, Australia",
        "description": "Develop and maintain backend services and APIs.",
        "requirements": ["Python", "FastAPI/Django", "SQL", "Docker"],
        "employment_type": "Full-time",
        "posted_date": date(2026, 6, 3),
        "skills": ["Python", "FastAPI", "SQL", "Docker"]
    }
]

@app.get("/jobs", response_model=List[Job])
def get_random_jobs(count: int = 2):
    """
    Returns a random list of jobs with fresh UUIDs.
    """
    count = min(count, len(JOB_POOL))
    sampled_data = sample(JOB_POOL, count)

    # Create new Job instances with fresh UUIDs
    jobs = [Job(**data) for data in sampled_data]
    return jobs

@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    Returns 200 OK with a JSON status.
    """
    return {"status": "healthy"}