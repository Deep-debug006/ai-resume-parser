"""
Comprehensive test suite for Job Description Parsing (Phase 14).
Validates:
- Pydantic JobDescription schema constraints and validations
- Real-world job description extractions across multiple domains
- Anti-hallucination principles (missing company is None, missing certs is [])
- Separation of required vs preferred qualifications
- Reuse of skill normalization (canonicalization of aliases)
- FastAPI endpoint POST /api/jobs/parse with direct and enveloped payloads
- Deterministic fallback and MockLLMProvider compatibility
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from backend.app.schemas.job_description import (
    JobDescription,
    JobParseRequest,
    JobParseResponse,
)
from backend.app.services.job_parser_service import (
    JobParserService,
    job_parser_service,
    DeterministicJobExtractor,
    JOB_PARSER_SYSTEM_INSTRUCTION,
)
from backend.app.services.llm_service import LLMService, MockLLMProvider, LLMProviderError

client = TestClient(app)

# ============================================================================
# Realistic Job Description Test Datasets
# ============================================================================

JOB_BACKEND_WITH_COMPANY_AND_CERTS = """
Job Title: Senior Backend Engineer
Company: Apex Cloud Systems
Location: San Francisco, CA (Hybrid)
Employment Type: Full-time
Salary: $170,000 - $210,000 per year

About Apex Cloud Systems:
Apex Cloud Systems is an enterprise software platform powering next-generation financial cloud infrastructure.

Role Overview:
We are seeking a seasoned Senior Backend Engineer to architect, build, and maintain our high-throughput distributed microservices.

Key Responsibilities:
- Design, build, and deploy low-latency RESTful and gRPC APIs.
- Optimize complex database queries and schema designs on PostgreSQL.
- Partner with product managers and frontend teams to deliver scalable customer features.
- Mentor junior engineers and participate in code reviews.

Minimum Requirements:
- 5+ years of software engineering experience building production systems.
- Strong proficiency in Python, FastAPI, and PostgreSQL.
- Practical experience with Docker and containerization workflows.
- Bachelor's degree in Computer Science or related technical field.

Preferred Qualifications:
- Experience with Kubernetes and Redis caching.
- Familiarity with Terraform and cloud infrastructure.

Certifications:
- AWS Certified Solutions Architect or equivalent cloud credential is a plus.
"""

JOB_DATA_SCIENTIST_NO_COMPANY = """
Position: Senior Machine Learning Engineer
Location: Remote

What You'll Do:
- Develop state-of-the-art natural language processing models and recommendation systems.
- Deploy real-time machine learning pipelines handling millions of inference requests daily.
- Collaborate with data engineers to build robust feature pipelines.

Basic Qualifications:
- 4+ years of hands-on experience in machine learning and deep learning.
- Strong proficiency in Python, PyTorch, and SQL.
- Master's or Ph.D. degree in Computer Science, Statistics, or related quantitative discipline.

Nice to Have:
- Hands-on experience with MLflow, Ray, and distributed GPU training.
- Experience with Kafka streaming architectures.
"""

JOB_FRONTEND_NO_CERTS = """
Job Title: Lead Frontend Developer
Company: Horizon Media Labs
Job Type: Full-time

About Us:
Horizon Media Labs creates interactive visual experiences for top global media publishers.

Responsibilities:
- Lead the architecture of modern web applications using React and TypeScript.
- Build accessible, high-performance UI components with Tailwind CSS.
- Optimize frontend web vitals and client-side rendering performance.

Requirements:
- 6+ years of professional web development experience.
- Deep expertise in JavaScript, TypeScript, and React.
- Solid understanding of web performance, DOM manipulation, and responsive design.
- Bachelor's degree in Web Development, Software Engineering, or equivalent experience.

Preferred Skills:
- Experience with Next.js and GraphQL.
- Familiarity with Cypress end-to-end testing.
"""

JOB_WITH_UNNORMALIZED_SKILLS = """
Role: Full Stack Cloud Developer
Company: NovaTech Solutions

Requirements:
- Strong experience with React.js, Postgres, and Golang.
- Working knowledge of k8s, AWS, and docker.
- 3+ years of experience in full-stack cloud software engineering.

Bonus Points:
- Familiarity with TF (Terraform) and Mongo.
"""


# ============================================================================
# 1. Pydantic JobDescription Schema Unit Tests
# ============================================================================

def test_job_description_schema_valid():
    """Validates standard JobDescription instantiation."""
    job = JobDescription(
        job_title="Backend Engineer",
        company="Stripe",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        education_requirements=["B.S. in Computer Science"],
        experience_requirements=["3+ years of backend development"],
        responsibilities=["Develop robust APIs"],
        tools_and_technologies=["Git", "PostgreSQL"],
        certifications=["AWS Certified"],
    )

    assert job.job_title == "Backend Engineer"
    assert job.company == "Stripe"
    assert "Python" in job.required_skills
    assert "FastAPI" in job.required_skills
    assert "Docker" in job.preferred_skills
    assert len(job.education_requirements) == 1
    assert len(job.experience_requirements) == 1
    assert len(job.responsibilities) == 1
    assert len(job.tools_and_technologies) == 2
    assert len(job.certifications) == 1


def test_job_description_empty_title_fails():
    """Validates that empty job title raises ValidationError."""
    with pytest.raises(ValidationError):
        JobDescription(job_title="")

    with pytest.raises(ValidationError):
        JobDescription(job_title="   ")


def test_job_description_missing_company_is_none():
    """Validates that missing or whitespace company results in None."""
    job1 = JobDescription(job_title="Software Engineer")
    assert job1.company is None

    job2 = JobDescription(job_title="Software Engineer", company="   ")
    assert job2.company is None


def test_job_description_list_deduplication():
    """Validates that string lists remove duplicates and empty items."""
    job = JobDescription(
        job_title="DevOps Engineer",
        required_skills=["Docker", "Kubernetes", "docker", "   ", "Docker"],
        preferred_skills=["Terraform", "terraform", "Helm"],
    )
    assert job.required_skills == ["Docker", "Kubernetes"]
    assert job.preferred_skills == ["Terraform", "Helm"]


def test_job_description_tools_alias():
    """Validates that 'tools' alias populates tools_and_technologies."""
    data = {
        "job_title": "Site Reliability Engineer",
        "tools": ["Prometheus", "Grafana", "Kubernetes"],
    }
    job = JobDescription.model_validate(data)
    assert job.tools_and_technologies == ["Prometheus", "Grafana", "Kubernetes"]


# ============================================================================
# 2. Deterministic Extractor & Anti-Hallucination Tests
# ============================================================================

def test_deterministic_extraction_backend_complete():
    """Tests deterministic extraction on a comprehensive backend job posting."""
    job = DeterministicJobExtractor.extract_deterministic(JOB_BACKEND_WITH_COMPANY_AND_CERTS)

    assert "Backend Engineer" in job.job_title
    assert job.company == "Apex Cloud Systems"
    assert any("Python" in s for s in job.required_skills)
    assert any("FastAPI" in s for s in job.required_skills)
    assert any("PostgreSQL" in s for s in job.required_skills)
    assert any("Kubernetes" in s or "Redis" in s for s in job.preferred_skills)
    assert any("Bachelor" in e for e in job.education_requirements)
    assert any("5+" in exp for exp in job.experience_requirements)
    assert len(job.responsibilities) > 0
    assert any("AWS Certified" in cert for cert in job.certifications)
    assert job.location is not None
    assert job.employment_type == "Full-time"


def test_anti_hallucination_missing_company_remains_none():
    """
    CRITICAL RULE: When company is not explicitly stated in the job text,
    it MUST remain None and not be fabricated.
    """
    job = DeterministicJobExtractor.extract_deterministic(JOB_DATA_SCIENTIST_NO_COMPANY)

    assert job.company is None
    assert "Machine Learning" in job.job_title
    assert any("Python" in s for s in job.required_skills)
    assert any("PyTorch" in s for s in job.required_skills)
    assert any("Master" in e or "Ph.D." in e for e in job.education_requirements)


def test_anti_hallucination_missing_certifications_remains_empty():
    """
    CRITICAL RULE: When no certifications are mentioned,
    certifications must remain an empty list [] and not be hallucinated.
    """
    job = DeterministicJobExtractor.extract_deterministic(JOB_FRONTEND_NO_CERTS)

    assert job.company == "Horizon Media Labs"
    assert "Frontend" in job.job_title
    assert job.certifications == []
    assert any("React" in s for s in job.required_skills)
    assert any("TypeScript" in s for s in job.required_skills)


def test_separation_required_vs_preferred_skills():
    """Validates that required skills and preferred qualifications are distinctly separated."""
    job = DeterministicJobExtractor.extract_deterministic(JOB_BACKEND_WITH_COMPANY_AND_CERTS)

    # Required should contain Python, FastAPI, Docker
    req_str = " ".join(job.required_skills)
    assert "Python" in req_str
    assert "FastAPI" in req_str

    # Preferred should contain Redis / Kubernetes
    pref_str = " ".join(job.preferred_skills)
    assert "Redis" in pref_str or "Kubernetes" in pref_str


# ============================================================================
# 3. Skill Normalization Reuse Tests
# ============================================================================

def test_job_parser_service_reuses_skill_normalizer():
    """
    Validates that Phase 14 JobParserService reuses Phase 10 SkillNormalizer:
    'React.js' -> 'React'
    'Postgres' -> 'PostgreSQL'
    'k8s' -> 'Kubernetes'
    'Amazon Web Services' -> 'AWS'
    'Golang' -> 'Go'
    """
    async def _run():
        service = JobParserService()
        job, norm_count, provider = await service.parse_job_description(
            JOB_WITH_UNNORMALIZED_SKILLS,
            force_deterministic=True,
        )

        assert job.job_title == "Full Stack Cloud Developer"
        assert job.company == "NovaTech Solutions"

        # Verify canonical skill mapping
        assert "React" in job.required_skills
        assert "React.js" not in job.required_skills

        assert "PostgreSQL" in job.required_skills
        assert "Postgres" not in job.required_skills

        assert "Go" in job.required_skills
        assert "Golang" not in job.required_skills

        assert "Kubernetes" in job.required_skills
        assert "k8s" not in job.required_skills

        assert "Amazon Web Services" in job.required_skills

        assert "Docker" in job.required_skills

        # Preferred skills normalized
        assert "Terraform" in job.preferred_skills
        assert "TF" not in job.preferred_skills
        assert "MongoDB" in job.preferred_skills
        assert "Mongo" not in job.preferred_skills

        assert norm_count > 0

    asyncio.run(_run())


# ============================================================================
# 4. MockLLMProvider Integration Tests
# ============================================================================

def test_job_parser_with_mock_llm_provider():
    """Tests job parsing through LLM abstraction layer using MockLLMProvider."""
    async def _run():
        mock_payload = {
            "job_title": "Principal Distributed Systems Engineer",
            "company": "CloudScale Global",
            "required_skills": ["Go", "Distributed Systems", "Kubernetes", "gRPC"],
            "preferred_skills": ["Rust", "eBPF"],
            "education_requirements": ["B.S. or M.S. in Computer Science"],
            "experience_requirements": ["8+ years in distributed backend infrastructure"],
            "responsibilities": ["Lead architectural strategy for global consensus cluster"],
            "tools_and_technologies": ["Go", "Kubernetes", "Docker", "Prometheus"],
            "certifications": ["CKA"],
            "location": "Remote (US/EU)",
            "employment_type": "Full-time",
            "salary_range": "$220,000 - $280,000",
        }

        mock_provider = MockLLMProvider(responses=[mock_payload])
        custom_llm = LLMService(provider=mock_provider)

        service = JobParserService(llm_service_instance=custom_llm)
        job, norm_count, provider = await service.parse_job_description(
            "Job text for principal engineer...",
            custom_llm_service=custom_llm,
        )

        assert provider == "mock"
        assert job.job_title == "Principal Distributed Systems Engineer"
        assert job.company == "CloudScale Global"
        assert "Go" in job.required_skills
        assert "Kubernetes" in job.required_skills
        assert "CKA" in job.certifications
        assert job.salary_range == "$220,000 - $280,000"

    asyncio.run(_run())


def test_job_parser_llm_failure_falls_back_to_deterministic():
    """Validates graceful degradation to deterministic extractor when LLM provider throws error."""
    async def _run():
        mock_provider = MockLLMProvider(responses=[LLMProviderError("Network connection reset")])
        custom_llm = LLMService(provider=mock_provider)

        service = JobParserService(llm_service_instance=custom_llm)
        job, norm_count, provider = await service.parse_job_description(
            JOB_BACKEND_WITH_COMPANY_AND_CERTS,
            custom_llm_service=custom_llm,
        )

        # Provider falls back to deterministic
        assert provider == "deterministic"
        assert "Backend Engineer" in job.job_title
        assert job.company == "Apex Cloud Systems"

    asyncio.run(_run())


# ============================================================================
# 5. FastAPI Endpoint Tests: POST /api/jobs/parse
# ============================================================================

def test_api_parse_job_success():
    """Tests POST /api/jobs/parse with standard JSON payload."""
    response = client.post(
        "/api/jobs/parse",
        json={"text": JOB_BACKEND_WITH_COMPANY_AND_CERTS},
    )

    assert response.status_code == 200
    data = response.json()

    assert "job_title" in data
    assert "company" in data
    assert "required_skills" in data
    assert "preferred_skills" in data
    assert "education_requirements" in data
    assert "experience_requirements" in data
    assert "responsibilities" in data
    assert "tools_and_technologies" in data
    assert "certifications" in data

    assert data["company"] == "Apex Cloud Systems"
    assert any("Python" in s for s in data["required_skills"])


def test_api_parse_job_alternate_field_name():
    """Tests POST /api/jobs/parse accepting 'job_description' instead of 'text'."""
    response = client.post(
        "/api/jobs/parse",
        json={"job_description": JOB_FRONTEND_NO_CERTS},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Horizon Media Labs"
    assert "Frontend" in data["job_title"]


def test_api_parse_job_enveloped_response():
    """Tests POST /api/jobs/parse with ?envelope=true returning timing metrics."""
    response = client.post(
        "/api/jobs/parse?envelope=true",
        json={"text": JOB_BACKEND_WITH_COMPANY_AND_CERTS},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "job" in data
    assert "normalized_skills_count" in data
    assert "duration_ms" in data
    assert data["duration_ms"] >= 0.0
    assert data["job"]["company"] == "Apex Cloud Systems"


def test_api_parse_job_empty_text_returns_400():
    """Tests POST /api/jobs/parse with empty or blank text returns 400 Bad Request."""
    res1 = client.post("/api/jobs/parse", json={"text": ""})
    assert res1.status_code == 400
    assert "cannot be empty" in res1.json()["detail"].lower()

    res2 = client.post("/api/jobs/parse", json={"text": "   "})
    assert res2.status_code == 400

    res3 = client.post("/api/jobs/parse", json={})
    assert res3.status_code == 400
