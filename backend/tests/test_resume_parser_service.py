"""
Integration tests for Resume Parser Service (Phase 9: AI Structured Information Extraction).
Uses MockLLMProvider to test the end-to-end pipeline, Pydantic validation, and endpoints
without external network or API key dependencies.
"""
import io
import pytest
from fastapi.testclient import TestClient
import pymupdf

from backend.app.main import app
from backend.app.schemas.parsed_resume import Resume
from backend.app.services.storage_service import storage_service
from backend.app.services.llm_service import LLMService, MockLLMProvider, LLMValidationError, LLMProviderError
from backend.app.services.resume_parser_service import (
    ResumeParserService,
    resume_parser_service,
    RESUME_PARSER_SYSTEM_INSTRUCTION,
)
from backend.app.services.nlp_service import NLPExtractionResult

client = TestClient(app)


def create_minimal_pdf_bytes(text: str) -> bytes:
    """Creates a valid PDF document containing the given text."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


SAMPLE_RESUME_TEXT = """
ALEX R. MERCER
alex.mercer@techinnovations.io | (415) 889-1020 | San Francisco, CA
https://linkedin.com/in/alexmercer | https://github.com/alexmercer

PROFESSIONAL SUMMARY
Senior Cloud and Backend Software Engineer with 7 years of production experience designing resilient distributed systems.

WORK EXPERIENCE
Nexus Infrastructure - Senior Software Engineer
San Francisco, CA | March 2021 - Present
- Architected asynchronous event pipeline using FastAPI, Kafka, and Redis processing 40M daily events.
- Migrated monolithic billing engine to Kubernetes, reducing compute expenditure by 28%.

Acrobyte Technologies - Backend Developer
Austin, TX | June 2018 - February 2021
- Developed REST microservices using Python and PostgreSQL.
- Authored integration test suite achieving 92% code coverage.

EDUCATION
University of Texas at Austin
Bachelor of Science in Computer Science | 2014 - 2018
GPA: 3.82 / 4.0

TECHNICAL SKILLS
Languages: Python, Go, TypeScript, SQL
Frameworks: FastAPI, React, Docker, Kubernetes
Databases: PostgreSQL, Redis, DynamoDB
Cloud & Tools: GCP, AWS, Terraform, Git, CI/CD

PROJECTS
OpenMesh Gateway
- Open source reverse proxy built in Go with dynamic TLS termination.
- https://github.com/alexmercer/openmesh

CERTIFICATIONS
AWS Certified Solutions Architect - Associate
Issuer: Amazon Web Services | 2021
"""


@pytest.fixture
def mock_resume_payload():
    return {
        "personal_info": {
            "full_name": "Alex R. Mercer",
            "email": "alex.mercer@techinnovations.io",
            "phone": "(415) 889-1020",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/alexmercer",
            "github_url": "https://github.com/alexmercer",
            "portfolio_url": None,
        },
        "summary": "Senior Cloud and Backend Software Engineer with 7 years of production experience.",
        "objective": None,
        "education": [
            {
                "institution": "University of Texas at Austin",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "2014",
                "end_date": "2018",
                "gpa": 3.82,
                "gpa_max": 4.0,
                "honors": [],
                "courses": [],
            }
        ],
        "skills": {
            "technical_skills": ["Distributed Systems", "CI/CD"],
            "programming_languages": ["Python", "Go", "TypeScript", "SQL"],
            "frameworks_and_libraries": ["FastAPI", "React", "Docker"],
            "databases": ["PostgreSQL", "Redis", "DynamoDB"],
            "cloud_and_devops": ["GCP", "AWS", "Terraform", "Kubernetes"],
            "soft_skills": [],
            "tools": ["Git"],
        },
        "experience": [
            {
                "company": "Nexus Infrastructure",
                "title": "Senior Software Engineer",
                "location": "San Francisco, CA",
                "start_date": "March 2021",
                "end_date": "Present",
                "is_current": True,
                "highlights": [
                    "Architected asynchronous event pipeline using FastAPI, Kafka, and Redis processing 40M daily events.",
                    "Migrated monolithic billing engine to Kubernetes, reducing compute expenditure by 28%.",
                ],
                "technologies": ["Python", "FastAPI", "Kafka", "Redis", "Kubernetes"],
            },
            {
                "company": "Acrobyte Technologies",
                "title": "Backend Developer",
                "location": "Austin, TX",
                "start_date": "June 2018",
                "end_date": "February 2021",
                "is_current": False,
                "highlights": [
                    "Developed REST microservices using Python and PostgreSQL.",
                    "Authored integration test suite achieving 92% code coverage.",
                ],
                "technologies": ["Python", "PostgreSQL"],
            },
        ],
        "projects": [
            {
                "name": "OpenMesh Gateway",
                "description": "Open source reverse proxy built in Go with dynamic TLS termination.",
                "url": "https://github.com/alexmercer/openmesh",
                "highlights": ["Open source reverse proxy built in Go"],
                "technologies": ["Go"],
                "start_date": None,
                "end_date": None,
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Solutions Architect - Associate",
                "issuer": "Amazon Web Services",
                "issue_date": "2021",
                "expiration_date": None,
                "credential_id": None,
                "url": None,
            }
        ],
        "achievements": [],
        "languages": ["English"],
        "interests": [],
    }


def test_build_prompt_contains_structural_elements():
    """Verify build_prompt incorporates sections, NLP entity anchors, and strict guidelines."""
    sections = {
        "summary": "Experienced engineer.",
        "skills": "Python, Docker, SQL",
    }
    nlp_res = NLPExtractionResult(
        persons=["Alex Mercer"],
        organizations=["Nexus Infrastructure"],
        locations=["San Francisco"],
        dates=["2021 - Present"],
        emails=["alex@example.com"],
        urls=["https://github.com/alexmercer"],
    )

    prompt = resume_parser_service.build_prompt(
        cleaned_text="Raw clean resume text",
        sections=sections,
        nlp_result=nlp_res,
    )

    assert "=== STRUCTURAL RESUME SECTIONS DETECTED ===" in prompt
    assert "--- SECTION: SUMMARY ---" in prompt
    assert "=== DETERMINISTIC NLP ANCHORS (VERIFIED EVIDENCE FOR REFERENCE) ===" in prompt
    assert "Alex Mercer" in prompt
    assert "Nexus Infrastructure" in prompt
    assert "=== FULL CLEAN RESUME TEXT ===" in prompt
    assert "=== REMINDER OF MANDATORY RULES ===" in prompt
    assert "NEVER invent dates, skills, or metrics" in prompt


@pytest.mark.anyio
async def test_parse_direct_text_pipeline(mock_resume_payload):
    """Verify parse_direct_text end-to-end execution with MockLLMProvider."""
    mock_provider = MockLLMProvider(responses=[mock_resume_payload])
    custom_service = LLMService(provider=mock_provider)

    result = await resume_parser_service.parse_direct_text(
        text=SAMPLE_RESUME_TEXT,
        custom_llm_service=custom_service,
    )

    assert result.resume_id == "direct_text"
    assert isinstance(result.resume, Resume)
    assert result.resume.personal_info.full_name == "Alex R. Mercer"
    assert result.resume.personal_info.email == "alex.mercer@techinnovations.io"
    assert len(result.resume.experience) == 2
    assert result.resume.experience[0].company == "Nexus Infrastructure"
    assert result.resume.experience[0].is_current is True
    assert result.resume.education[0].gpa == 3.82
    assert result.repair_attempts == 0
    assert result.llm_provider == "mock"


@pytest.mark.anyio
async def test_parse_resume_document_pipeline(mock_resume_payload):
    """Verify parse_resume_document extracts from an uploaded PDF and parses via mock LLM."""
    pdf_bytes = create_minimal_pdf_bytes(SAMPLE_RESUME_TEXT)
    saved_filename, _ = storage_service.save_temporarily(pdf_bytes, "alex_mercer.pdf")

    mock_provider = MockLLMProvider(responses=[mock_resume_payload])
    custom_service = LLMService(provider=mock_provider)

    result = await resume_parser_service.parse_resume_document(
        resume_id=saved_filename,
        custom_llm_service=custom_service,
    )

    assert result.resume_id == saved_filename
    assert result.resume.personal_info.full_name == "Alex R. Mercer"
    assert result.raw_text_char_count > 100
    assert len(result.sections_detected) > 0
    assert result.repair_attempts == 0


def test_api_parse_resume_endpoint_not_found():
    """Verify 404 is returned when resume ID does not exist in storage."""
    response = client.post("/api/resumes/non_existent_resume_id/parse")
    assert response.status_code == 404
    assert "was not found in temporary storage" in response.json()["detail"]


def test_api_parse_direct_endpoint_success(monkeypatch, mock_resume_payload):
    """Verify POST /api/resumes/parse-direct endpoint succeeds with mock provider."""
    # Monkeypatch the default resume_parser_service._llm_service with MockLLMProvider
    mock_provider = MockLLMProvider(responses=[mock_resume_payload])
    mock_service = LLMService(provider=mock_provider)
    monkeypatch.setattr(resume_parser_service, "_llm_service", mock_service)

    response = client.post(
        "/api/resumes/parse-direct",
        json={"text": SAMPLE_RESUME_TEXT},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resume_id"] == "direct_text"
    assert data["resume"]["personal_info"]["full_name"] == "Alex R. Mercer"
    assert data["resume"]["personal_info"]["email"] == "alex.mercer@techinnovations.io"
    assert data["llm_provider"] == "mock"
    assert data["repair_attempts"] == 0


def test_api_parse_resume_endpoint_success(monkeypatch, mock_resume_payload):
    """Verify POST /api/resumes/{resume_id}/parse endpoint succeeds end-to-end."""
    # 1. Upload sample PDF
    pdf_bytes = create_minimal_pdf_bytes(SAMPLE_RESUME_TEXT)
    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("alex_mercer.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    resume_id = upload_res.json()["filename"]

    # 2. Patch LLM service to use mock responses
    mock_provider = MockLLMProvider(responses=[mock_resume_payload])
    mock_service = LLMService(provider=mock_provider)
    monkeypatch.setattr(resume_parser_service, "_llm_service", mock_service)

    # 3. Call parse endpoint
    parse_res = client.post(f"/api/resumes/{resume_id}/parse")
    assert parse_res.status_code == 200
    parsed_data = parse_res.json()

    assert parsed_data["resume_id"] == resume_id
    assert parsed_data["resume"]["personal_info"]["full_name"] == "Alex R. Mercer"
    assert len(parsed_data["resume"]["experience"]) == 2
    assert parsed_data["resume"]["education"][0]["institution"] == "University of Texas at Austin"
    assert parsed_data["repair_attempts"] == 0


def test_api_parse_direct_short_text_rejected():
    """Verify validation rejects empty or too short text (min_length=10)."""
    response = client.post(
        "/api/resumes/parse-direct",
        json={"text": "Short"},
    )
    assert response.status_code == 422  # Pydantic validation error for min_length
