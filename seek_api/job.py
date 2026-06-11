from pydantic import BaseModel, Field, HttpUrl, PositiveInt
from datetime import date
from typing import Optional, List
from uuid import uuid4, UUID

class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique job identifier")
    title: str = Field(..., description="The job title")
    company: str = Field(..., description="Name of the company")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Detailed job description")
    requirements: List[str] = Field(..., description="List of key skills and requirements")
    responsibilities: Optional[List[str]] = Field(None, description="Core responsibilities")
    employment_type: str = Field(..., description="Full-time, Part-time, Contract etc.")
    salary_range: Optional[str] = Field(None, description="Expected salary range")
    posted_date: Optional[date] = Field(None, description="Date the job was posted")
    apply_url: Optional[HttpUrl] = Field(None, description="URL for online application")
    benefits: Optional[List[str]] = Field(None, description="Optional list of employee benefits")
    experience_years: Optional[PositiveInt] = Field(None, description="Required years of experience")
    skills: Optional[List[str]] = Field(None, description="Specific skills needed for the role")