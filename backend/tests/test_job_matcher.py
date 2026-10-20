"""
Comprehensive unit and integration tests for Resume-Job Matching (Phase 15).
Validates:
- Deterministic skill matching and canonical alias resolution
- Identification of matched skills, missing required skills, matched preferred skills, missing preferred skills
- Experience alignment and explainable narrative analysis
- Education alignment and degree rank comparisons
- Certifications comparison
- Strict compliance with non-evaluative principles (no hiring decisions or claims)
- Top-level import compatibility (from services.job_matcher import ...)
- FastAPI endpoint POST /api/jobs/match
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.parsed_resume import (
    Resume,
    PersonalInfo,
    Education,
    SkillSet,
    Experience,
    Project,
    Certification,
)
from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.job_matcher import JobMatchResult, INFORMATIONAL_DISCLAIMER
from backend.app.services.job_matcher import JobMatcher, job_matcher

# Test top-level re-export import
from services.job_matcher import JobMatcher as TopLevelJobMatcher, job_matcher as top_level_job_matcher

client = TestClient(app)

# ============================================================================
# Test Fixtures & Sample Objects
# ============================================================================

def create_sample_resume(
    skills_list: list = None,
    experience_years_duration: int = 5,
    degree_name: str = "B.S.",
    field_of_study: str = "Computer Science",
    certifications_list: list = None,
) -> Resume:
    """Helper to construct a realistic structured Resume object."""
    skills = skills_list or ["Python", "FastAPI", "Postgres", "Docker", "Git"]
    certs = [
        Certification(name=c, issuer="Cloud Provider")
        for c in (certifications_list or ["AWS Certified Solutions Architect"])
    ]

    exp_list = []
    if experience_years_duration >= 4:
        exp_list = [
            Experience(
                company="Nexus Infrastructure",
                title="Senior Backend Engineer",
                start_date="March 2021",
                end_date="Present",
                is_current=True,
                highlights=["Designed microservices using Python and FastAPI"],
                technologies=["Python", "FastAPI", "Redis", "Docker"],
            ),
            Experience(
                company="Acrobyte Technologies",
                title="Software Engineer",
                start_date="June 2018",
                end_date="February 2021",
                is_current=False,
                highlights=["Maintained PostgreSQL database cluster"],
                technologies=["Python", "PostgreSQL", "Linux"],
            ),
        ]
    else:
        exp_list = [
            Experience(
                company="Startup Labs",
                title="Junior Developer",
                start_date="2024",
                end_date="Present",
                is_current=True,
                highlights=["Built web pages"],
                technologies=["JavaScript", "React"],
            )
        ]

    return Resume(
        personal_info=PersonalInfo(
            full_name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+1 (555) 019-2834",
            location="San Francisco, CA",
        ),
        education=[
            Education(
                institution="University of Texas at Austin",
                degree=degree_name,
                field_of_study=field_of_study,
                start_date="2014",
                end_date="2018",
                gpa=3.85,
            )
        ],
        skills=SkillSet(
            programming_languages=["Python", "Go"],
            frameworks_and_libraries=["FastAPI", "React"],
            databases=["PostgreSQL", "Redis"],
            cloud_and_devops=["Docker", "Kubernetes"],
            tools=["Git", "Linux"],
        ),
        experience=exp_list,
        projects=[
            Project(
                name="Cloud Metrics Engine",
                technologies=["Python", "FastAPI", "PostgreSQL"],
            )
        ],
        certifications=certs,
    )


def create_sample_job(
    required_skills: list = None,
    preferred_skills: list = None,
    exp_reqs: list = None,
    edu_reqs: list = None,
    certs_reqs: list = None,
) -> JobDescription:
    """Helper to construct a realistic structured JobDescription object."""
    return JobDescription(
        job_title="Senior Backend Engineer",
        company="Apex Cloud Systems",
        required_skills=required_skills if required_skills is not None else ["Python", "FastAPI", "PostgreSQL", "Kafka"],
        preferred_skills=preferred_skills if preferred_skills is not None else ["Kubernetes", "Redis", "Terraform"],
        experience_requirements=exp_reqs if exp_reqs is not None else ["5+ years of software engineering experience building production systems."],
        education_requirements=edu_reqs if edu_reqs is not None else ["Bachelor's degree in Computer Science or related technical field."],
        responsibilities=["Design and build low-latency APIs", "Optimize database schema designs"],
        tools_and_technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        certifications=certs_reqs if certs_reqs is not None else ["AWS Certified Solutions Architect"],
        location="San Francisco, CA",
        employment_type="Full-time",
    )


# ============================================================================
# 1. Top-Level Import & Compatibility Tests
# ============================================================================

def test_top_level_services_import():
    """Validates that 'from services.job_matcher import JobMatcher, job_matcher' works."""
    assert TopLevelJobMatcher is not None
    assert top_level_job_matcher is not None
    assert isinstance(top_level_job_matcher, JobMatcher)


# ============================================================================
# 2. Deterministic Skill Matching Tests
# ============================================================================

def test_deterministic_skill_matching_exact_and_canonical():
    """
    Validates required skills matching and gap detection:
    - Candidate has: Python, FastAPI, PostgreSQL, Docker, Kubernetes, Redis, Go
    - Job requires: Python, FastAPI, PostgreSQL, Kafka
    Expect:
    - matched_skills: Python, FastAPI, PostgreSQL
    - missing_required_skills: Kafka
    """
    resume = create_sample_resume()
    job = create_sample_job(
        required_skills=["Python", "FastAPI", "Postgres", "Kafka"],
    )

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert "Python" in result.matched_skills
    assert "FastAPI" in result.matched_skills
    assert "PostgreSQL" in result.matched_skills
    assert any("Kafka" in s for s in result.missing_required_skills)
    assert not any("Kafka" in s for s in result.matched_skills)


def test_deterministic_preferred_skills_matching():
    """
    Validates preferred skills matching and gap detection:
    - Job prefers: Kubernetes, Redis, Terraform
    - Candidate has: Kubernetes, Redis
    Expect:
    - matched_preferred_skills: Kubernetes, Redis
    - missing_preferred_skills: Terraform
    """
    resume = create_sample_resume()
    job = create_sample_job(
        preferred_skills=["k8s", "Redis", "Terraform"],
    )

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert "Kubernetes" in result.matched_preferred_skills
    assert "Redis" in result.matched_preferred_skills
    assert "Terraform" in result.missing_preferred_skills


def test_skill_match_rates():
    """Validates that match rates are correctly computed numeric proportions."""
    resume = create_sample_resume()
    job = create_sample_job(
        required_skills=["Python", "FastAPI", "PostgreSQL", "Kafka"],  # 3 of 4 match = 0.75
        preferred_skills=["Kubernetes", "Terraform"],                   # 1 of 2 match = 0.50
    )

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.required_skills_match_rate == 0.75
    assert result.preferred_skills_match_rate == 0.50


# ============================================================================
# 3. Experience Alignment & Explainability Tests
# ============================================================================

def test_experience_alignment_meets_requirements():
    """Candidate with ~5+ years meets a 5+ years requirement."""
    resume = create_sample_resume(experience_years_duration=5)
    job = create_sample_job(exp_reqs=["5+ years of experience"])

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.experience_alignment in ("meets_requirements", "exceeds_requirements")
    assert "5" in result.experience_analysis
    assert "years" in result.experience_analysis.lower()
    assert result.candidate_years_experience >= 4.0


def test_experience_alignment_below_requirements():
    """Candidate with <2 years does not meet a 5+ years requirement."""
    resume = create_sample_resume(experience_years_duration=1)
    job = create_sample_job(exp_reqs=["5+ years of experience in distributed systems"])

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.experience_alignment == "below_requirements"
    assert "variance" in result.experience_analysis.lower() or "below" in result.experience_analysis.lower()
    assert result.candidate_years_experience < 5.0


def test_experience_alignment_unspecified():
    """Job with no stated experience duration reports not_specified."""
    resume = create_sample_resume(experience_years_duration=5)
    job = create_sample_job(exp_reqs=[])

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.experience_alignment == "not_specified"
    assert "does not explicitly specify" in result.experience_analysis


# ============================================================================
# 4. Education Alignment Tests
# ============================================================================

def test_education_alignment_meets_requirements():
    """Candidate with B.S. in Computer Science meets Bachelor's requirement."""
    resume = create_sample_resume(degree_name="Bachelor of Science", field_of_study="Computer Science")
    job = create_sample_job(edu_reqs=["Bachelor's degree in Computer Science or related field"])

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.education_alignment == "meets_requirements"
    assert "Computer Science" in result.education_analysis
    assert "Bachelor" in result.education_analysis


def test_education_alignment_exceeds_requirements():
    """Candidate with M.S. in Computer Science exceeds Bachelor's requirement."""
    resume = create_sample_resume(degree_name="Master of Science", field_of_study="Computer Science")
    job = create_sample_job(edu_reqs=["Bachelor's degree in Computer Science"])

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.education_alignment == "exceeds_requirements"
    assert "exceeding" in result.education_analysis.lower() or "advanced degree" in result.education_analysis.lower()


def test_education_alignment_unspecified():
    """Job with no educational criteria reports not_specified."""
    resume = create_sample_resume()
    job = create_sample_job(edu_reqs=[])

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert result.education_alignment == "not_specified"


# ============================================================================
# 5. Certifications Alignment Tests
# ============================================================================

def test_certifications_matching():
    """Validates matched and missing certifications."""
    resume = create_sample_resume(
        certifications_list=["AWS Certified Solutions Architect"]
    )
    job = create_sample_job(
        certs_reqs=["AWS Certified Solutions Architect", "Certified Kubernetes Administrator (CKA)"]
    )

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    assert any("AWS" in c for c in result.matched_certifications)
    assert any("Kubernetes" in c or "CKA" in c for c in result.missing_certifications)


# ============================================================================
# 6. Ethical AI, Anti-Bias & Disclaimer Tests
# ============================================================================

def test_non_evaluative_disclaimer_present():
    """
    CRITICAL MANDATE:
    Must NOT make hiring decisions.
    Must NOT claim candidate will be hired.
    Must contain informational disclaimer.
    """
    resume = create_sample_resume()
    job = create_sample_job()

    matcher = JobMatcher()
    result = matcher.match(resume, job)

    # Validate disclaimer
    assert result.disclaimer == INFORMATIONAL_DISCLAIMER
    assert "hiring" in result.disclaimer.lower()
    assert "not evaluate" in result.disclaimer.lower()

    # Ensure no hiring decision language in analysis fields
    forbidden_terms = ["will get hired", "hire this candidate", "reject this candidate", "guaranteed interview"]
    for term in forbidden_terms:
        assert term not in result.experience_analysis.lower()
        assert term not in result.education_analysis.lower()


# ============================================================================
# 7. FastAPI Endpoint Tests: POST /api/jobs/match
# ============================================================================

def test_api_match_endpoint_success():
    """Tests POST /api/jobs/match with structured resume and job objects."""
    resume = create_sample_resume()
    job = create_sample_job()

    payload = {
        "resume": resume.model_dump(),
        "job_description": job.model_dump(),
    }

    response = client.post("/api/jobs/match", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "matched_skills" in data
    assert "missing_required_skills" in data
    assert "matched_preferred_skills" in data
    assert "missing_preferred_skills" in data
    assert "experience_analysis" in data
    assert "education_analysis" in data
    assert "disclaimer" in data

    assert "Python" in data["matched_skills"]
    assert any("Kafka" in s for s in data["missing_required_skills"])


def test_api_match_endpoint_with_job_text():
    """Tests POST /api/jobs/match with structured resume and raw job text."""
    resume = create_sample_resume()
    raw_job_text = """
    Job Title: Backend Developer
    Requirements:
    - Strong skills in Python, FastAPI, and Postgres.
    - Experience with Apache Kafka.
    Preferred:
    - Docker and Redis.
    """

    payload = {
        "resume": resume.model_dump(),
        "job_text": raw_job_text,
    }

    response = client.post("/api/jobs/match", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "matched_skills" in data
    assert "missing_required_skills" in data
    assert any("Python" in s for s in data["matched_skills"])


def test_api_match_endpoint_missing_resume_returns_400():
    """Tests POST /api/jobs/match with missing resume returns 400 Bad Request."""
    payload = {
        "job_description": create_sample_job().model_dump()
    }
    response = client.post("/api/jobs/match", json=payload)
    assert response.status_code == 400
    assert "missing resume" in response.json()["detail"].lower()


def test_api_match_endpoint_empty_payload_returns_400():
    """Tests POST /api/jobs/match with empty body returns 400 Bad Request."""
    response = client.post("/api/jobs/match", json={})
    assert response.status_code == 400
