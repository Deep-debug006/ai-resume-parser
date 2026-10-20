"""
Pydantic models for Resume-Job Matching (Phase 15).
Purely informational, explainable comparison between structured Resumes and Job Descriptions.
Strictly adheres to non-evaluative principles: no hiring decisions, no outcome claims.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from backend.app.schemas.parsed_resume import Resume
from backend.app.schemas.job_description import JobDescription


INFORMATIONAL_DISCLAIMER = (
    "This analysis is purely an informational comparison between extracted resume details "
    "and stated job requirements. It does not evaluate candidate competency, predict interview success, "
    "or make hiring or employment recommendations."
)


class MatchRequest(BaseModel):
    """
    Input payload for resume-job matching.
    Accepts either full structured Resume + JobDescription models,
    or raw texts / database IDs.
    """
    resume: Optional[Resume] = Field(None, description="Structured parsed resume object")
    job_description: Optional[JobDescription] = Field(None, description="Structured parsed job description object")
    resume_text: Optional[str] = Field(None, description="Raw resume text if parsing on-the-fly")
    job_text: Optional[str] = Field(None, description="Raw job description text if parsing on-the-fly")
    resume_id: Optional[str] = Field(None, description="Optional database resume ID to load from PostgreSQL")


class JobMatchResult(BaseModel):
    """
    Canonical deterministic match result comparing Resume and JobDescription.
    Transparent, explainable, and informational.
    """
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Required skills from the job description that were identified in the candidate's background"
    )
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Required skills from the job description that were not explicitly detected in the candidate's profile"
    )
    matched_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred/bonus skills from the job description present in the candidate's profile"
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred/bonus skills from the job description not detected in the candidate's profile"
    )
    experience_analysis: str = Field(
        ...,
        description="Explainable breakdown of candidate work history compared against stated experience criteria"
    )
    education_analysis: str = Field(
        ...,
        description="Explainable breakdown of candidate degrees and coursework compared against stated educational criteria"
    )
    experience_alignment: str = Field(
        "unknown",
        description="Informational alignment rating: 'meets_requirements', 'exceeds_requirements', 'below_requirements', or 'not_specified'"
    )
    education_alignment: str = Field(
        "unknown",
        description="Informational alignment rating: 'meets_requirements', 'exceeds_requirements', 'below_requirements', or 'not_specified'"
    )
    candidate_years_experience: Optional[float] = Field(
        None,
        description="Estimated total professional experience in years extracted from work history"
    )
    required_years_experience: Optional[float] = Field(
        None,
        description="Minimum years of experience requested in job description, if explicitly stated"
    )
    matched_certifications: List[str] = Field(
        default_factory=list,
        description="Certifications mentioned in job description held by candidate"
    )
    missing_certifications: List[str] = Field(
        default_factory=list,
        description="Certifications mentioned in job description not found on resume"
    )
    required_skills_match_rate: float = Field(
        0.0,
        description="Proportion of required skills matched (between 0.0 and 1.0)"
    )
    preferred_skills_match_rate: float = Field(
        0.0,
        description="Proportion of preferred skills matched (between 0.0 and 1.0)"
    )
    disclaimer: str = Field(
        default=INFORMATIONAL_DISCLAIMER,
        description="Mandatory ethical disclaimer stating this is informational and not a hiring decision"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "missing_required_skills": ["Kafka"],
                "matched_preferred_skills": ["Kubernetes", "Redis"],
                "missing_preferred_skills": ["Terraform"],
                "experience_analysis": "Candidate presents approximately 5.5 years of experience across 2 software engineering roles, meeting the required 5+ years.",
                "education_analysis": "Candidate holds a Bachelor of Science in Computer Science, satisfying the requirement for a Bachelor's degree in CS or related field.",
                "experience_alignment": "meets_requirements",
                "education_alignment": "meets_requirements",
                "candidate_years_experience": 5.5,
                "required_years_experience": 5.0,
                "matched_certifications": ["AWS Certified Solutions Architect"],
                "missing_certifications": [],
                "required_skills_match_rate": 0.8,
                "preferred_skills_match_rate": 0.67,
                "disclaimer": INFORMATIONAL_DISCLAIMER
            }
        }
    }
