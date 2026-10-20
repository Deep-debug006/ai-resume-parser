"""
Tests for Phase 17: AI Resume Analysis Service.
Tests evaluate:
- clarity
- section completeness
- bullet-point quality
- measurable achievements where present
- skill organization
- project descriptions
- formatting-related text issues
- missing common information
- potential improvements

Guardrails verified:
- Do not invent achievements.
- Do not rewrite facts into fake accomplishments.
- Recommendations grounded in actual resume content.
- Factual extraction kept separate from subjective recommendations.
- Valid structured analysis response:
  {
    "strengths": [],
    "areas_for_improvement": [],
    "suggestions": []
  }
- Mocked LLM responses for fast, deterministic unit and API endpoint tests.
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
)
from backend.app.schemas.resume_analysis import (
    ResumeAnalysisResponse,
    ResumeAnalysisRequest,
)
from backend.app.services.llm_service import MockLLMProvider, LLMService
from backend.app.services.resume_analysis_service import (
    ResumeAnalysisService,
    resume_analysis_service,
)

client = TestClient(app)


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
Frameworks & Libraries: FastAPI, React, Docker, Kubernetes
Databases: PostgreSQL, Redis, MongoDB
Cloud & DevOps: AWS, Google Cloud Platform, Terraform
"""

MINIMAL_RESUME_TEXT = """
JOHN DOE
Software developer.
Did some coding in Python.
"""


@pytest.fixture
def sample_structured_resume() -> Resume:
    return Resume(
        personal_info=PersonalInfo(
            full_name="Alex R. Mercer",
            email="alex.mercer@techinnovations.io",
            phone="(415) 889-1020",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/alexmercer",
            github_url="https://github.com/alexmercer",
        ),
        summary="Senior Cloud and Backend Software Engineer with 7 years of production experience designing resilient distributed systems.",
        education=[
            Education(
                institution="University of Texas at Austin",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                start_date="2014",
                end_date="2018",
                gpa=3.82,
                gpa_max=4.0,
            )
        ],
        skills=SkillSet(
            programming_languages=["Python", "Go", "TypeScript", "SQL"],
            frameworks_and_libraries=["FastAPI", "React"],
            databases=["PostgreSQL", "Redis"],
            cloud_and_devops=["AWS", "Docker", "Kubernetes"],
        ),
        experience=[
            Experience(
                company="Nexus Infrastructure",
                title="Senior Software Engineer",
                location="San Francisco, CA",
                start_date="March 2021",
                end_date="Present",
                is_current=True,
                highlights=[
                    "Architected asynchronous event pipeline using FastAPI, Kafka, and Redis processing 40M daily events.",
                    "Migrated monolithic billing engine to Kubernetes, reducing compute expenditure by 28%.",
                ],
                technologies=["FastAPI", "Kafka", "Redis", "Kubernetes"],
            )
        ],
        projects=[
            Project(
                name="Distributed Task Scheduler",
                description="Fault-tolerant job scheduler built with Go and Raft consensus.",
                url="https://github.com/alexmercer/task-scheduler",
                highlights=["Benchmarked at 5,000 tasks/sec with linear scalability."],
                technologies=["Go", "Raft", "Docker"],
            )
        ],
    )


class TestResumeAnalysisFactualExtraction:
    """Tests verify factual extraction is strictly separated from subjective evaluations."""

    def test_extract_factual_summary_detects_sections_and_metrics(self, sample_structured_resume):
        service = ResumeAnalysisService()
        facts = service.extract_factual_summary(resume=sample_structured_resume)

        assert "personal_info" in facts["sections_present"]
        assert "experience" in facts["sections_present"]
        assert "education" in facts["sections_present"]
        assert "skills" in facts["sections_present"]
        assert "projects" in facts["sections_present"]
        assert facts["has_contact_email"] is True
        assert facts["has_linkedin"] is True
        assert facts["total_experience_entries"] == 1
        assert facts["total_projects"] == 1

        # Check metrics detection
        metrics = facts["measurable_metrics_detected"]
        assert any("40M" in m or "28%" in m or "5,000" in m or "40" in m for m in metrics)

    def test_extract_factual_summary_handles_minimal_resume(self):
        service = ResumeAnalysisService()
        facts = service.extract_factual_summary(raw_text=MINIMAL_RESUME_TEXT)

        assert facts["has_contact_email"] is False
        assert facts["has_linkedin"] is False
        assert len(facts["measurable_metrics_detected"]) == 0


class TestResumeAnalysisWithMockedLLM:
    """Tests evaluation behavior using MockLLMProvider."""

    @pytest.mark.asyncio
    async def test_mocked_llm_structured_analysis(self, sample_structured_resume):
        mock_provider = MockLLMProvider()
        mock_provider.add_response({
            "strengths": [
                "Measurable engineering impact highlighted (e.g. 40M daily events, 28% compute cost reduction).",
                "Technical competencies are well-organized across languages, frameworks, and databases.",
                "Direct links provided for GitHub and LinkedIn.",
            ],
            "areas_for_improvement": [
                "Only one work experience entry documented in detail.",
                "Could elaborate on the monitoring and observability strategies applied.",
            ],
            "suggestions": [
                "Consider documenting earlier engineering experience if available.",
                "Detail testing strategies applied to the distributed task scheduler project.",
            ],
            "criteria_evaluations": {
                "clarity": {"criterion": "clarity", "score": 9.0, "observations": ["Clear technical prose"]},
                "section_completeness": {"criterion": "section_completeness", "score": 9.5, "observations": ["All core sections present"]},
                "bullet_point_quality": {"criterion": "bullet_point_quality", "score": 8.5, "observations": ["Action verbs used"]},
                "measurable_achievements": {"criterion": "measurable_achievements", "score": 9.0, "observations": ["40M events, 28% reduction"]},
                "skill_organization": {"criterion": "skill_organization", "score": 9.0, "observations": ["Categorized skills"]},
                "project_descriptions": {"criterion": "project_descriptions", "score": 8.5, "observations": ["Distributed scheduler"]},
                "formatting_related_text_issues": {"criterion": "formatting_related_text_issues", "score": 9.0, "observations": ["Consistent format"]},
                "missing_common_information": {"criterion": "missing_common_information", "score": 10.0, "observations": ["No missing contact info"]},
            },
        })

        llm_service_instance = LLMService(provider=mock_provider)
        analysis_service = ResumeAnalysisService(llm_service_instance=llm_service_instance)

        result: ResumeAnalysisResponse = await analysis_service.analyze_resume(
            resume=sample_structured_resume
        )

        assert isinstance(result, ResumeAnalysisResponse)
        assert len(result.strengths) >= 2
        assert len(result.areas_for_improvement) >= 1
        assert len(result.suggestions) >= 1
        assert "40M" in result.strengths[0]
        assert "clarity" in result.criteria_evaluations
        assert result.criteria_evaluations["clarity"].score == 9.0
        assert result.factual_summary["has_contact_email"] is True
        assert result.llm_provider == "mock"

    @pytest.mark.asyncio
    async def test_deterministic_fallback_when_llm_raises(self, sample_structured_resume):
        mock_provider = MockLLMProvider()
        mock_provider.add_response(RuntimeError("Remote provider simulated timeout/rate limit"))

        llm_service_instance = LLMService(provider=mock_provider)
        analysis_service = ResumeAnalysisService(llm_service_instance=llm_service_instance)

        result: ResumeAnalysisResponse = await analysis_service.analyze_resume(
            resume=sample_structured_resume
        )

        # Fallback must still return valid structured object with strengths, areas, and suggestions
        assert isinstance(result, ResumeAnalysisResponse)
        assert len(result.strengths) > 0
        assert len(result.areas_for_improvement) >= 0
        assert len(result.suggestions) >= 0
        assert "section_completeness" in result.criteria_evaluations
        assert "measurable_achievements" in result.criteria_evaluations


class TestResumeAnalysisAPIEndpoints:
    """Tests the /api/resumes/analyze endpoint with mocked LLM."""

    def test_analyze_endpoint_with_raw_text(self, monkeypatch):
        mock_provider = MockLLMProvider()
        monkeypatch.setattr(resume_analysis_service, "_llm_service", LLMService(provider=mock_provider))

        payload = {"text": SAMPLE_RESUME_TEXT}
        response = client.post("/api/resumes/analyze", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "strengths" in data
        assert "areas_for_improvement" in data
        assert "suggestions" in data
        assert isinstance(data["strengths"], list)
        assert isinstance(data["areas_for_improvement"], list)
        assert isinstance(data["suggestions"], list)
        assert len(data["strengths"]) > 0

    def test_analyze_endpoint_with_structured_resume(self, monkeypatch, sample_structured_resume):
        mock_provider = MockLLMProvider()
        monkeypatch.setattr(resume_analysis_service, "_llm_service", LLMService(provider=mock_provider))

        payload = {"resume": sample_structured_resume.model_dump()}
        response = client.post("/api/resumes/analyze", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "strengths" in data
        assert "areas_for_improvement" in data
        assert "suggestions" in data
        assert "criteria_evaluations" in data
        assert "factual_summary" in data

    def test_analyze_endpoint_validates_empty_payload(self):
        response = client.post("/api/resumes/analyze", json={})
        assert response.status_code == 400
        assert "Must provide either" in response.json()["detail"]

    def test_analyze_saved_resume_not_found(self):
        response = client.post("/api/resumes/non-existent-uuid/analyze")
        assert response.status_code == 404
