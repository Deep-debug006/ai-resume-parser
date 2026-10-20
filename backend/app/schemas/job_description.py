"""
Pydantic models for structured Job Description parsing (Phase 14).
Strict schema validation, anti-hallucination guarantees, and clean field boundaries.
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class JobDescription(BaseModel):
    """
    Canonical structured representation of an extracted Job Description.
    Strictly grounded in provided text with zero invented details.
    """
    job_title: str = Field(
        ...,
        description="Position or job title explicitly stated in the job posting (e.g., 'Senior Backend Engineer')"
    )
    company: Optional[str] = Field(
        None,
        description="Hiring organization or company name if explicitly present; None if not explicitly stated"
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory, must-have, or baseline required skills"
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred, bonus, nice-to-have, or secondary skills"
    )
    education_requirements: List[str] = Field(
        default_factory=list,
        description="Degrees, academic qualifications, or fields of study explicitly required or mentioned"
    )
    experience_requirements: List[str] = Field(
        default_factory=list,
        description="Years of experience, seniority criteria, or specific background criteria explicitly stated"
    )
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Core duties, day-to-day tasks, and architectural responsibilities"
    )
    tools_and_technologies: List[str] = Field(
        default_factory=list,
        description="Platforms, software tools, frameworks, and developer utilities explicitly mentioned"
    )
    certifications: List[str] = Field(
        default_factory=list,
        description="Professional certifications, licenses, or credentials if explicitly mentioned"
    )
    location: Optional[str] = Field(
        None,
        description="Geographic location or work arrangement (e.g., 'San Francisco, CA', 'Remote', 'Hybrid')"
    )
    employment_type: Optional[str] = Field(
        None,
        description="Employment arrangement (e.g., 'Full-time', 'Contract', 'Part-time', 'Internship')"
    )
    salary_range: Optional[str] = Field(
        None,
        description="Salary, compensation bracket, or hourly rate if explicitly stated"
    )
    raw_text_char_count: Optional[int] = Field(
        None,
        description="Total character length of the raw input job description"
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "job_title": "Senior Cloud Backend Engineer",
                "company": "Apex Cloud Systems",
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "preferred_skills": ["Kubernetes", "Redis", "Terraform"],
                "education_requirements": ["Bachelor's degree in Computer Science or equivalent practical experience"],
                "experience_requirements": ["5+ years of production software engineering experience"],
                "responsibilities": [
                    "Design, implement, and maintain high-throughput RESTful microservices",
                    "Optimize PostgreSQL database queries and indexing strategies"
                ],
                "tools_and_technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"],
                "certifications": ["AWS Certified Solutions Architect"],
                "location": "San Francisco, CA (Hybrid)",
                "employment_type": "Full-time",
                "salary_range": "$160,000 - $210,000"
            }
        }
    }

    @field_validator("job_title")
    @classmethod
    def validate_job_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Job title cannot be empty or blank.")
        return v.strip()

    @field_validator("company", "location", "employment_type", "salary_range", mode="before")
    @classmethod
    def clean_optional_strings(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator(
        "required_skills",
        "preferred_skills",
        "education_requirements",
        "experience_requirements",
        "responsibilities",
        "tools_and_technologies",
        "certifications",
        mode="before"
    )
    @classmethod
    def clean_string_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            # Split comma or newline delimited strings if passed as a single string
            items = [item.strip() for item in v.split("\n") if item.strip()]
        elif isinstance(v, (list, tuple, set)):
            items = [str(item).strip() for item in v if item is not None and str(item).strip()]
        else:
            return []

        # Deduplicate while preserving original order
        cleaned: List[str] = []
        seen = set()
        for item in items:
            normalized_key = item.lower()
            if normalized_key not in seen:
                seen.add(normalized_key)
                cleaned.append(item)
        return cleaned

    @model_validator(mode="before")
    @classmethod
    def handle_tools_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "tools" in data and "tools_and_technologies" not in data:
                data["tools_and_technologies"] = data["tools"]
        return data

    @property
    def tools(self) -> List[str]:
        """Convenience property for tools_and_technologies."""
        return self.tools_and_technologies


class JobParseRequest(BaseModel):
    """
    Request payload for parsing a job description text.
    Accepts text via `text` or `job_description`.
    """
    text: Optional[str] = Field(
        None,
        description="Raw text of the job description to parse"
    )
    job_description: Optional[str] = Field(
        None,
        description="Alternative field name for raw job description text"
    )

    @model_validator(mode="after")
    def validate_has_content(self) -> "JobParseRequest":
        raw = self.text or self.job_description
        if not raw or not raw.strip():
            raise ValueError("Job description text cannot be empty. Provide non-empty 'text' or 'job_description'.")
        self.text = raw.strip()
        return self


class JobParseResponse(BaseModel):
    """
    Detailed envelope for job description parsing response with metadata and metrics.
    """
    success: bool = Field(True, description="Whether parsing completed successfully")
    job: JobDescription = Field(..., description="Structured job description object")
    normalized_skills_count: int = Field(0, description="Count of skills normalized via canonical aliases")
    duration_ms: float = Field(..., description="Time taken to extract and process job in milliseconds")
    provider: Optional[str] = Field(None, description="Extraction provider (e.g., 'gemini', 'mock', 'deterministic')")
