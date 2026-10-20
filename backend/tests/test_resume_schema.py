"""
Unit tests for Phase 7: Structured Resume Schema (app/schemas/parsed_resume.py).
Tests cover:
- Valid full resume schema instantiation and serialization
- Partially filled resume (optional fields omitted or empty)
- Missing required fields validation
- Invalid types (type mismatches)
- Invalid values (empty names, invalid emails, out-of-range GPAs, GPA exceeding max)
"""
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.app.main import app

from backend.app.schemas.parsed_resume import (
    PersonalInfo,
    Education,
    SkillSet,
    Experience,
    Project,
    Certification,
    Achievement,
    Resume,
)


def test_valid_full_resume():
    """Verify that a fully populated resume parses cleanly and serializes properly."""
    data = {
        "personal_info": {
            "full_name": "Maya Lin",
            "email": "maya.lin@domain.org",
            "phone": "+1 (555) 432-8765",
            "location": "Seattle, WA",
            "linkedin_url": "https://linkedin.com/in/mayalin",
            "github_url": "https://github.com/mayalin",
            "portfolio_url": "https://mayalin.dev",
        },
        "summary": "Senior Distributed Systems Engineer with 8 years of experience building resilient cloud infrastructure.",
        "objective": "To lead high-impact infrastructure teams scaling planetary-scale platforms.",
        "education": [
            {
                "institution": "University of Washington",
                "degree": "B.S.",
                "field_of_study": "Computer Science",
                "start_date": "2014",
                "end_date": "2018",
                "gpa": 3.92,
                "gpa_max": 4.0,
                "honors": ["Summa Cum Laude", "Dean's List"],
                "courses": ["Operating Systems", "Distributed Systems", "Algorithms"],
            }
        ],
        "skills": {
            "technical_skills": ["Microservices", "System Design", "Observability"],
            "programming_languages": ["Go", "Rust", "Python", "SQL"],
            "frameworks_and_libraries": ["FastAPI", "Tokio", "gRPC"],
            "databases": ["PostgreSQL", "Redis", "CockroachDB"],
            "cloud_and_devops": ["AWS", "Kubernetes", "Terraform", "Docker"],
            "soft_skills": ["Mentorship", "Technical Writing"],
            "tools": ["Git", "Prometheus", "Grafana"],
        },
        "experience": [
            {
                "company": "CloudNative Systems",
                "title": "Principal Infrastructure Engineer",
                "location": "Seattle, WA (Hybrid)",
                "start_date": "2021-03",
                "end_date": "Present",
                "is_current": True,
                "highlights": [
                    "Led zero-downtime migration of 140+ microservices to Kubernetes.",
                    "Reduced 99th percentile API latency from 450ms to 42ms.",
                ],
                "technologies": ["Go", "Kubernetes", "Envoy", "Terraform"],
            },
            {
                "company": "TechStart Inc.",
                "title": "Software Engineer II",
                "location": "San Francisco, CA",
                "start_date": "2018-06",
                "end_date": "2021-02",
                "is_current": False,
                "highlights": ["Built distributed caching layer handling 50k QPS."],
                "technologies": ["Python", "Redis", "FastAPI"],
            },
        ],
        "projects": [
            {
                "name": "HyperSync Raft",
                "description": "Fault-tolerant consensus module implemented in Rust.",
                "url": "https://github.com/mayalin/hypersync-raft",
                "highlights": ["Achieved 120,000 replicated ops/sec across 5-node cluster."],
                "technologies": ["Rust", "Tokio"],
                "start_date": "2023-01",
                "end_date": "2023-06",
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Solutions Architect - Professional",
                "issuer": "Amazon Web Services",
                "issue_date": "2022-09",
                "expiration_date": "2025-09",
                "credential_id": "AWS-PSA-894719",
                "url": "https://aws.amazon.com/verification",
            }
        ],
        "achievements": [
            {
                "title": "Best Innovation Award 2023",
                "issuer": "CloudNative Systems Annual Summit",
                "date": "2023-11",
                "description": "Awarded for autonomous cluster auto-scaler reducing cloud costs by 35%.",
            }
        ],
        "languages": ["English (Native)", "Mandarin (Professional)"],
        "interests": ["Mountaineering", "Open Source Contributing"],
    }

    resume = Resume(**data)

    assert resume.personal_info.full_name == "Maya Lin"
    assert resume.personal_info.email == "maya.lin@domain.org"
    assert len(resume.education) == 1
    assert resume.education[0].gpa == 3.92
    assert resume.education[0].gpa_max == 4.0
    assert len(resume.skills.programming_languages) == 4
    assert len(resume.experience) == 2
    assert resume.experience[0].is_current is True
    assert len(resume.projects) == 1
    assert len(resume.certifications) == 1
    assert len(resume.achievements) == 1

    # Verify JSON serialization round-trip
    dumped = resume.model_dump()
    assert dumped["personal_info"]["full_name"] == "Maya Lin"


def test_partially_filled_resume():
    """Verify that resumes omitting optional sections parse without errors."""
    minimal_data = {
        "personal_info": {
            "full_name": "Jordan Bell",
        }
    }

    resume = Resume(**minimal_data)

    assert resume.personal_info.full_name == "Jordan Bell"
    assert resume.personal_info.email is None
    assert resume.personal_info.phone is None
    assert resume.summary is None
    assert resume.objective is None
    assert resume.education == []
    assert resume.skills.programming_languages == []
    assert resume.experience == []
    assert resume.projects == []
    assert resume.certifications == []
    assert resume.achievements == []


def test_missing_required_fields():
    """Verify that omitting required fields raises ValidationError with informative messages."""
    # 1. Missing entire personal_info
    with pytest.raises(ValidationError) as exc_info:
        Resume()
    errors = exc_info.value.errors()
    assert any("personal_info" in err["loc"] for err in errors)

    # 2. Missing required full_name in PersonalInfo
    with pytest.raises(ValidationError) as exc_info:
        PersonalInfo()
    errors = exc_info.value.errors()
    assert any("full_name" in err["loc"] for err in errors)

    # 3. Missing required institution in Education
    with pytest.raises(ValidationError) as exc_info:
        Education()
    errors = exc_info.value.errors()
    assert any("institution" in err["loc"] for err in errors)

    # 4. Missing required company or title in Experience
    with pytest.raises(ValidationError) as exc_info:
        Experience(company="Acme Corp")
    errors = exc_info.value.errors()
    assert any("title" in err["loc"] for err in errors)

    # 5. Missing required name in Project
    with pytest.raises(ValidationError) as exc_info:
        Project()
    errors = exc_info.value.errors()
    assert any("name" in err["loc"] for err in errors)

    # 6. Missing required name in Certification
    with pytest.raises(ValidationError) as exc_info:
        Certification()
    errors = exc_info.value.errors()
    assert any("name" in err["loc"] for err in errors)

    # 7. Missing required title in Achievement
    with pytest.raises(ValidationError) as exc_info:
        Achievement()
    errors = exc_info.value.errors()
    assert any("title" in err["loc"] for err in errors)


def test_invalid_types():
    """Verify that providing incompatible types triggers ValidationError."""
    # 1. Non-string for full_name
    with pytest.raises(ValidationError):
        PersonalInfo(full_name=12345)

    # 2. Non-numeric string for gpa
    with pytest.raises(ValidationError):
        Education(institution="Stanford", gpa="not-a-number")

    # 3. Object instead of list for experience
    with pytest.raises(ValidationError):
        Resume(
            personal_info=PersonalInfo(full_name="Sam"),
            experience={"not": "a list"},
        )

    # 4. Non-boolean for is_current
    with pytest.raises(ValidationError):
        Experience(
            company="Tech Corp",
            title="Dev",
            is_current="not-a-boolean-value",
        )


def test_invalid_values():
    """Verify custom business logic validations (email format, empty strings, GPA boundaries)."""
    # 1. Blank full_name
    with pytest.raises(ValidationError) as exc_info:
        PersonalInfo(full_name="   ")
    assert "Candidate full name cannot be empty" in str(exc_info.value)

    # 2. Malformed email address
    with pytest.raises(ValidationError) as exc_info:
        PersonalInfo(full_name="Valid Name", email="invalid-email-no-at-sign")
    assert "Invalid email address format" in str(exc_info.value)

    # 3. Negative GPA
    with pytest.raises(ValidationError) as exc_info:
        Education(institution="MIT", gpa=-1.5)
    assert "GPA must be between 0.0 and 10.0" in str(exc_info.value)

    # 4. GPA greater than 10.0
    with pytest.raises(ValidationError) as exc_info:
        Education(institution="MIT", gpa=15.0)
    assert "GPA must be between 0.0 and 10.0" in str(exc_info.value)

    # 5. GPA exceeding its own stated maximum scale
    with pytest.raises(ValidationError) as exc_info:
        Education(institution="MIT", gpa=4.5, gpa_max=4.0)
    assert "cannot exceed maximum scale value" in str(exc_info.value)

    # 6. GPA max scale <= 0
    with pytest.raises(ValidationError) as exc_info:
        Education(institution="MIT", gpa=3.5, gpa_max=0.0)
    assert "GPA maximum scale value must be greater than 0" in str(exc_info.value)

    # 7. Blank company in Experience
    with pytest.raises(ValidationError) as exc_info:
        Experience(company="   ", title="Software Engineer")
    assert "Company and title fields cannot be empty" in str(exc_info.value)

    # 8. Blank title in Experience
    with pytest.raises(ValidationError) as exc_info:
        Experience(company="Acme", title="   ")
    assert "Company and title fields cannot be empty" in str(exc_info.value)


def test_api_get_resume_schema():
    """Verify GET /api/resumes/schema returns valid OpenAPI JSON schema."""
    client = TestClient(app)
    response = client.get("/api/resumes/schema")
    assert response.status_code == 200
    data = response.json()
    assert "properties" in data
    assert "personal_info" in data["properties"]
    assert "education" in data["properties"]
    assert "skills" in data["properties"]
    assert "experience" in data["properties"]
    assert "projects" in data["properties"]
    assert "certifications" in data["properties"]
    assert "achievements" in data["properties"]

