"""
Pydantic models for structured resume representation (Phase 7).
Designed for strict validation, sensible optionality, and future LLM output generation.
"""
import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PersonalInfo(BaseModel):
    """
    Contact and personal identification details of the candidate.
    """
    full_name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone contact number")
    location: Optional[str] = Field(None, description="City, state, or country of residence")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio_url: Optional[str] = Field(None, description="Personal website or portfolio link")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Candidate full name cannot be empty.")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            return None
        if not EMAIL_REGEX.match(stripped):
            raise ValueError(f"Invalid email address format: '{v}'")
        return stripped.lower()

    @field_validator("phone", "location", "linkedin_url", "github_url", "portfolio_url")
    @classmethod
    def clean_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class Education(BaseModel):
    """
    Educational credential or degree details.
    """
    institution: str = Field(..., description="Name of the university, college, or educational institution")
    degree: Optional[str] = Field(None, description="Degree or diploma earned, e.g. 'B.S.', 'M.S.', 'Ph.D.'")
    field_of_study: Optional[str] = Field(None, description="Major, concentration, or specialization")
    start_date: Optional[str] = Field(None, description="Start date or year, e.g. '2018' or 'Aug 2018'")
    end_date: Optional[str] = Field(None, description="Graduation date, year, or 'Present'")
    gpa: Optional[float] = Field(None, description="Numeric grade point average (e.g. 3.85)")
    gpa_max: Optional[float] = Field(None, description="Maximum possible scale value for GPA (e.g. 4.0 or 10.0)")
    honors: List[str] = Field(default_factory=list, description="Academic honors or distinctions")
    courses: List[str] = Field(default_factory=list, description="Relevant coursework completed")

    @field_validator("institution")
    @classmethod
    def validate_institution(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Educational institution cannot be empty.")
        return stripped

    @field_validator("gpa")
    @classmethod
    def validate_gpa(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0.0 or v > 10.0:
                raise ValueError(f"GPA must be between 0.0 and 10.0, received: {v}")
        return v

    @model_validator(mode="after")
    def validate_gpa_range(self) -> "Education":
        if self.gpa is not None and self.gpa_max is not None:
            if self.gpa_max <= 0.0:
                raise ValueError("GPA maximum scale value must be greater than 0.")
            if self.gpa > self.gpa_max:
                raise ValueError(f"GPA ({self.gpa}) cannot exceed maximum scale value ({self.gpa_max}).")
        return self


class SkillSet(BaseModel):
    """
    Categorized collection of skills and competencies.
    """
    technical_skills: List[str] = Field(default_factory=list, description="General technical capabilities")
    programming_languages: List[str] = Field(default_factory=list, description="Programming languages (e.g. Python, Go)")
    frameworks_and_libraries: List[str] = Field(default_factory=list, description="Frameworks & libraries (e.g. React, FastAPI)")
    databases: List[str] = Field(default_factory=list, description="Databases and datastores (e.g. PostgreSQL, Redis)")
    cloud_and_devops: List[str] = Field(default_factory=list, description="Cloud infrastructure and DevOps tools")
    soft_skills: List[str] = Field(default_factory=list, description="Leadership and interpersonal skills")
    tools: List[str] = Field(default_factory=list, description="Software tools, IDEs, and utilities")


class Experience(BaseModel):
    """
    Professional work history or internship record.
    """
    company: str = Field(..., description="Organization or employer name")
    title: str = Field(..., description="Job role or position title")
    location: Optional[str] = Field(None, description="Work location or 'Remote'")
    start_date: Optional[str] = Field(None, description="Start date or year of employment")
    end_date: Optional[str] = Field(None, description="End date of employment, or 'Present'")
    is_current: bool = Field(False, description="True if the candidate currently holds this position")
    highlights: List[str] = Field(default_factory=list, description="Key responsibilities and quantitative achievements")
    technologies: List[str] = Field(default_factory=list, description="Technologies and tools applied in this position")

    @field_validator("company", "title")
    @classmethod
    def validate_required_strings(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Company and title fields cannot be empty.")
        return stripped


class Project(BaseModel):
    """
    Notable personal, academic, or professional project.
    """
    name: str = Field(..., description="Project name or title")
    description: Optional[str] = Field(None, description="Brief description of the project scope")
    url: Optional[str] = Field(None, description="Project code repository or live link")
    highlights: List[str] = Field(default_factory=list, description="Key features and accomplishments")
    technologies: List[str] = Field(default_factory=list, description="Technologies and frameworks utilized")
    start_date: Optional[str] = Field(None, description="Project inception date")
    end_date: Optional[str] = Field(None, description="Project completion date")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty.")
        return stripped


class Certification(BaseModel):
    """
    Professional certification, license, or credential.
    """
    name: str = Field(..., description="Title of the certification")
    issuer: Optional[str] = Field(None, description="Issuing organization or authority")
    issue_date: Optional[str] = Field(None, description="Date or year credential was issued")
    expiration_date: Optional[str] = Field(None, description="Expiration date if credential expires")
    credential_id: Optional[str] = Field(None, description="License or verification ID")
    url: Optional[str] = Field(None, description="Credential verification URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Certification name cannot be empty.")
        return stripped


class Achievement(BaseModel):
    """
    Award, competitive honor, or notable distinction.
    """
    title: str = Field(..., description="Title of the achievement or award")
    issuer: Optional[str] = Field(None, description="Organization or competition that granted the award")
    date: Optional[str] = Field(None, description="Date or year awarded")
    description: Optional[str] = Field(None, description="Description or significance of the distinction")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Achievement title cannot be empty.")
        return stripped


class Resume(BaseModel):
    """
    Canonical structured representation of a fully parsed resume.
    """
    personal_info: PersonalInfo = Field(..., description="Contact and personal information")
    summary: Optional[str] = Field(None, description="Professional summary or profile")
    objective: Optional[str] = Field(None, description="Career objective")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    skills: SkillSet = Field(default_factory=SkillSet, description="Categorized skill set")
    experience: List[Experience] = Field(default_factory=list, description="Work and internship experience")
    projects: List[Project] = Field(default_factory=list, description="Technical and portfolio projects")
    certifications: List[Certification] = Field(default_factory=list, description="Professional certifications")
    achievements: List[Achievement] = Field(default_factory=list, description="Awards and honors")
    languages: List[str] = Field(default_factory=list, description="Spoken languages")
    interests: List[str] = Field(default_factory=list, description="Hobbies and personal interests")
