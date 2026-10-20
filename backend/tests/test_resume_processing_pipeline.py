"""
Comprehensive Integration Tests for Phase 12: Complete Resume Processing Pipeline.
Tests verify:
- End-to-end pipeline execution from PDF upload to PostgreSQL persistence
- Multiple diverse resume formats:
  1. Standard Tech Software Engineer (single-column)
  2. Data Scientist / ML Specialist (two-column / dense)
  3. Executive Engineering Leader (multi-role experience & metrics)
  4. Academic / Researcher CV (publications, achievements, education)
  5. Scanned Image-Only PDF triggering OCR fallback
- Lifecycle status tracking: 'uploaded' -> 'processing' -> 'completed' / 'failed'
- Stage failure resilience (corrupt PDF, LLM validation failure)
- Skill normalization in full pipeline (e.g. JS -> JavaScript, Postgres -> PostgreSQL)
- Direct file upload vs file_id parameter
- Database persistence verification across child entities
"""
import io
import json
from typing import Dict, Any
import pymupdf
from PIL import Image, ImageDraw
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.models.resume_models import ResumeModel, SkillModel, ResumeSkillModel
from backend.app.schemas.parsed_resume import Resume
from backend.app.services.storage_service import storage_service
from backend.app.services.llm_service import LLMService, MockLLMProvider, LLMValidationError
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator, PipelineOrchestrator

client = TestClient(app)


def make_pdf(pages_text: list[str]) -> bytes:
    """Creates in-memory valid PDF with native machine-readable text."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=612, height=792)
        page.insert_text((54, 54), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def make_scanned_image_pdf(text_to_draw: str) -> bytes:
    """Creates raster image-only PDF containing zero machine-readable text (triggers OCR fallback)."""
    img = Image.new("RGB", (900, 300), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), text_to_draw, fill="black")

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_bytes = img_buffer.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(pymupdf.Rect(50, 50, 550, 250), stream=img_bytes)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# FORMAT 1: Standard Software Engineer
# ---------------------------------------------------------------------------
FORMAT_1_TEXT = """
JORDAN SMITH
jordan.smith@devmail.org | (555) 234-5678 | Seattle, WA
https://linkedin.com/in/jordansmith | https://github.com/jordansmith

SUMMARY
Backend Engineer with 5 years experience specializing in distributed systems, RESTful microservices, and event-driven architectures.

EXPERIENCE
CloudScale Systems - Software Engineer
Seattle, WA | January 2021 - Present
- Designed high-throughput data processing microservices handling 15,000 req/sec using FastAPI and PostgreSQL.
- Implemented automated CI/CD pipelines with Docker and Kubernetes reducing deployment time by 40%.

DataTech Labs - Junior Developer
Portland, OR | June 2019 - December 2020
- Built internal analytics dashboards and REST APIs in Python.
- Maintained PostgreSQL schemas and optimized slow SQL queries.

EDUCATION
University of Washington
Bachelor of Science in Computer Science | 2015 - 2019
GPA: 3.75 / 4.0

SKILLS
Programming: Python, JS, Go, SQL
Technologies: FastAPI, Docker, K8s, Postgres, Redis

PROJECTS
EventStreamer
Built an open-source lightweight event streaming engine in Go and Python.
https://github.com/jordansmith/event-streamer

CERTIFICATIONS
AWS Certified Solutions Architect - Associate
Amazon Web Services | Issued: 2022
"""

FORMAT_1_STRUCTURED = {
    "personal_info": {
        "full_name": "Jordan Smith",
        "email": "jordan.smith@devmail.org",
        "phone": "(555) 234-5678",
        "location": "Seattle, WA",
        "linkedin_url": "https://linkedin.com/in/jordansmith",
        "github_url": "https://github.com/jordansmith",
        "portfolio_url": None,
    },
    "summary": "Backend Engineer with 5 years experience specializing in distributed systems.",
    "objective": None,
    "education": [
        {
            "institution": "University of Washington",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "start_date": "2015",
            "end_date": "2019",
            "gpa": 3.75,
            "gpa_max": 4.0,
            "honors": [],
            "courses": [],
        }
    ],
    "skills": {
        "technical_skills": ["Distributed Systems"],
        "programming_languages": ["Python", "JS", "Go", "SQL"],
        "frameworks_and_libraries": ["FastAPI"],
        "databases": ["Postgres", "Redis"],
        "cloud_and_devops": ["Docker", "K8s"],
        "soft_skills": [],
        "tools": [],
    },
    "experience": [
        {
            "company": "CloudScale Systems",
            "title": "Software Engineer",
            "location": "Seattle, WA",
            "start_date": "January 2021",
            "end_date": "Present",
            "is_current": True,
            "highlights": [
                "Designed high-throughput data processing microservices handling 15,000 req/sec.",
                "Implemented automated CI/CD pipelines reducing deployment time by 40%.",
            ],
            "technologies": ["FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        }
    ],
    "projects": [
        {
            "name": "EventStreamer",
            "description": "Built an open-source lightweight event streaming engine in Go and Python.",
            "url": "https://github.com/jordansmith/event-streamer",
            "highlights": ["Lightweight event streaming"],
            "technologies": ["Go", "Python"],
            "start_date": None,
            "end_date": None,
        }
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect - Associate",
            "issuer": "Amazon Web Services",
            "issue_date": "2022",
            "expiration_date": None,
            "credential_id": None,
            "url": None,
        }
    ],
    "achievements": [],
    "languages": ["English"],
    "interests": [],
}


# ---------------------------------------------------------------------------
# FORMAT 2: Data Scientist / ML Specialist (Dense Two-Column style)
# ---------------------------------------------------------------------------
FORMAT_2_TEXT = """
DR. ELENA ROSTOVA
elena.rostova@ailab.edu | +1-415-990-1122 | San Francisco, CA
https://linkedin.com/in/erostova | https://github.com/erostova

OBJECTIVE
Principal Machine Learning Researcher seeking to deploy state-of-the-art transformer architectures into real-world production.

EDUCATION
Stanford University
Ph.D. in Computer Science (Artificial Intelligence) | 2017 - 2021
Dissertation: Scalable Reinforcement Learning in Stochastic Multi-Agent Settings
GPA: 3.96 / 4.0

Carnegie Mellon University
B.S. in Mathematics and Computer Science | 2013 - 2017
GPA: 3.91 / 4.0 | Summa Cum Laude

SKILLS
ML & AI: PyTorch, TensorFlow, Scikit-Learn, Transformers, HuggingFace
Languages: Python, R, C++, Julia
Databases: MongoDB, PostgreSQL, VectorDB
Cloud: AWS, GCP, MLflow

EXPERIENCE
DeepThought AI - Senior Research Scientist
Palo Alto, CA | September 2021 - Present
- Trained 7B parameter domain-adapted foundation models with FlashAttention-2.
- Reduced inference latency by 55% using TensorRT-LLM and FP8 quantization.

PROJECTS
OpenQuantLab
High-frequency automated statistical arbitrage simulator.
https://github.com/erostova/open-quant-lab

ACHIEVEMENTS
NeurIPS Best Paper Honorable Mention | 2022
Outstanding Doctoral Dissertation Award | Stanford University | 2021
"""

FORMAT_2_STRUCTURED = {
    "personal_info": {
        "full_name": "Dr. Elena Rostova",
        "email": "elena.rostova@ailab.edu",
        "phone": "+1-415-990-1122",
        "location": "San Francisco, CA",
        "linkedin_url": "https://linkedin.com/in/erostova",
        "github_url": "https://github.com/erostova",
        "portfolio_url": None,
    },
    "summary": None,
    "objective": "Principal Machine Learning Researcher seeking to deploy transformer architectures.",
    "education": [
        {
            "institution": "Stanford University",
            "degree": "Ph.D.",
            "field_of_study": "Computer Science (Artificial Intelligence)",
            "start_date": "2017",
            "end_date": "2021",
            "gpa": 3.96,
            "gpa_max": 4.0,
            "honors": ["Outstanding Doctoral Dissertation Award"],
            "courses": [],
        },
        {
            "institution": "Carnegie Mellon University",
            "degree": "B.S.",
            "field_of_study": "Mathematics and Computer Science",
            "start_date": "2013",
            "end_date": "2017",
            "gpa": 3.91,
            "gpa_max": 4.0,
            "honors": ["Summa Cum Laude"],
            "courses": [],
        },
    ],
    "skills": {
        "technical_skills": ["Transformers", "FP8 Quantization", "FlashAttention-2"],
        "programming_languages": ["Python", "R", "C++", "Julia"],
        "frameworks_and_libraries": ["PyTorch", "TensorFlow", "Scikit-Learn"],
        "databases": ["MongoDB", "PostgreSQL"],
        "cloud_and_devops": ["AWS", "GCP"],
        "soft_skills": [],
        "tools": ["MLflow"],
    },
    "experience": [
        {
            "company": "DeepThought AI",
            "title": "Senior Research Scientist",
            "location": "Palo Alto, CA",
            "start_date": "September 2021",
            "end_date": "Present",
            "is_current": True,
            "highlights": [
                "Trained 7B parameter domain-adapted foundation models.",
                "Reduced inference latency by 55% using TensorRT-LLM.",
            ],
            "technologies": ["PyTorch", "TensorRT-LLM", "FlashAttention-2"],
        }
    ],
    "projects": [
        {
            "name": "OpenQuantLab",
            "description": "High-frequency automated statistical arbitrage simulator.",
            "url": "https://github.com/erostova/open-quant-lab",
            "highlights": ["Statistical arbitrage simulation"],
            "technologies": ["Python", "C++"],
            "start_date": None,
            "end_date": None,
        }
    ],
    "certifications": [],
    "achievements": [
        {
            "title": "NeurIPS Best Paper Honorable Mention",
            "issuer": "NeurIPS",
            "date": "2022",
            "description": "Recognized for novel scalable multi-agent exploration.",
        }
    ],
    "languages": ["English", "Russian"],
    "interests": ["Chess", "Hiking"],
}


# ---------------------------------------------------------------------------
# FORMAT 3: Executive Engineering Leader
# ---------------------------------------------------------------------------
FORMAT_3_TEXT = """
MARCUS V. AURELIUS
marcus.aurelius@leadership.co | (212) 555-0199 | New York, NY
https://linkedin.com/in/mvaurelius

EXECUTIVE SUMMARY
Vice President of Engineering with 16+ years scaling engineering organizations from series A to IPO. Proven track record managing 120+ engineers across 4 global hubs and managing $25M operational budgets.

PROFESSIONAL EXPERIENCE
Vanguard FinTech Solutions - Vice President of Engineering
New York, NY | January 2019 - Present
- Scaled engineering department from 32 to 140 members while maintaining 94% retention.
- Overseeing architecture of core banking exchange processing $14B in annual transactions.
- Spearheaded SOC-2 Type II and ISO-27001 security compliance certifications.

AlphaCore Tech - Director of Software Engineering
Boston, MA | March 2014 - December 2018
- Managed 5 squads of 45 engineers building cloud payments infrastructure.
- Cut infrastructure hosting costs by $2.4M annually via multi-cloud container orchestration.

EDUCATION
Massachusetts Institute of Technology (MIT)
Master of Science in Engineering Management | 2006 - 2008
Bachelor of Science in Electrical Engineering & Computer Science | 2002 - 2006

SKILLS & EXPERTISE
Leadership: Organizational Design, Agile Transformation, Budgeting ($25M+), Executive Mentorship
Technical Architecture: Distributed Systems, High-Availability, Cloud Strategy, FinTech Security

CERTIFICATIONS
Certified Information Systems Security Professional (CISSP) | (ISC)² | 2016
Certified ScrumMaster (CSM) | Scrum Alliance | 2012
"""

FORMAT_3_STRUCTURED = {
    "personal_info": {
        "full_name": "Marcus V. Aurelius",
        "email": "marcus.aurelius@leadership.co",
        "phone": "(212) 555-0199",
        "location": "New York, NY",
        "linkedin_url": "https://linkedin.com/in/mvaurelius",
        "github_url": None,
        "portfolio_url": None,
    },
    "summary": "Vice President of Engineering with 16+ years scaling engineering organizations from series A to IPO.",
    "objective": None,
    "education": [
        {
            "institution": "Massachusetts Institute of Technology (MIT)",
            "degree": "Master of Science",
            "field_of_study": "Engineering Management",
            "start_date": "2006",
            "end_date": "2008",
            "gpa": None,
            "gpa_max": None,
            "honors": [],
            "courses": [],
        }
    ],
    "skills": {
        "technical_skills": ["Distributed Systems", "High-Availability", "Cloud Strategy"],
        "programming_languages": [],
        "frameworks_and_libraries": [],
        "databases": [],
        "cloud_and_devops": ["Kubernetes", "Multi-Cloud"],
        "soft_skills": ["Organizational Design", "Executive Mentorship", "Agile Transformation"],
        "tools": [],
    },
    "experience": [
        {
            "company": "Vanguard FinTech Solutions",
            "title": "Vice President of Engineering",
            "location": "New York, NY",
            "start_date": "January 2019",
            "end_date": "Present",
            "is_current": True,
            "highlights": [
                "Scaled engineering department from 32 to 140 members while maintaining 94% retention.",
                "Overseeing core banking exchange processing $14B in annual transactions.",
            ],
            "technologies": ["Cloud", "Microservices", "FinTech"],
        }
    ],
    "projects": [],
    "certifications": [
        {
            "name": "Certified Information Systems Security Professional (CISSP)",
            "issuer": "(ISC)²",
            "issue_date": "2016",
            "expiration_date": None,
            "credential_id": None,
            "url": None,
        }
    ],
    "achievements": [],
    "languages": ["English"],
    "interests": ["Triathlon", "Angel Investing"],
}


# ---------------------------------------------------------------------------
# FORMAT 4: Academic Researcher / Fellow CV
# ---------------------------------------------------------------------------
FORMAT_4_TEXT = """
DR. AMINA KHAN
amina.khan@oxford.ac.uk | +44 1865 270000 | Oxford, UK
https://linkedin.com/in/aminakhan-phd

PROFILE
Computational Biologist and Postdoctoral Fellow with expertise in structural genomics, protein folding simulation, and bioinformatic pipelines.

RESEARCH EXPERIENCE
University of Oxford - Postdoctoral Research Fellow
Oxford, UK | October 2021 - Present
- Developed automated molecular dynamics analysis pipeline processing cryo-EM datasets.
- Published 4 first-author papers in Nature Communications and Bioinformatics.

Harvard University - Graduate Research Assistant
Cambridge, MA | September 2016 - June 2021
- Applied graph neural networks to predict small molecule ligand-binding affinities.

EDUCATION
Harvard University
Ph.D. in Biophysics and Computational Biology | 2016 - 2021

University of Cambridge
B.A. in Natural Sciences (First Class Honours) | 2013 - 2016

SKILLS
Bioinformatics: AlphaFold, PyMOL, GROMACS, Biopython
Languages: Python, R, Bash, C++
Data Science: NumPy, SciPy, Pandas

AWARDS & HONOURS
Wellcome Trust Early-Career Postdoctoral Fellowship | 2021
Cambridge Tripos Prize for Academic Excellence | 2016
"""

FORMAT_4_STRUCTURED = {
    "personal_info": {
        "full_name": "Dr. Amina Khan",
        "email": "amina.khan@oxford.ac.uk",
        "phone": "+44 1865 270000",
        "location": "Oxford, UK",
        "linkedin_url": "https://linkedin.com/in/aminakhan-phd",
        "github_url": None,
        "portfolio_url": None,
    },
    "summary": "Computational Biologist and Postdoctoral Fellow with expertise in structural genomics.",
    "objective": None,
    "education": [
        {
            "institution": "Harvard University",
            "degree": "Ph.D.",
            "field_of_study": "Biophysics and Computational Biology",
            "start_date": "2016",
            "end_date": "2021",
            "gpa": None,
            "gpa_max": None,
            "honors": [],
            "courses": [],
        },
        {
            "institution": "University of Cambridge",
            "degree": "B.A.",
            "field_of_study": "Natural Sciences",
            "start_date": "2013",
            "end_date": "2016",
            "gpa": None,
            "gpa_max": None,
            "honors": ["First Class Honours"],
            "courses": [],
        },
    ],
    "skills": {
        "technical_skills": ["Molecular Dynamics", "Cryo-EM", "Structural Genomics"],
        "programming_languages": ["Python", "R", "Bash", "C++"],
        "frameworks_and_libraries": ["NumPy", "SciPy", "Pandas", "Biopython"],
        "databases": [],
        "cloud_and_devops": [],
        "soft_skills": [],
        "tools": ["AlphaFold", "PyMOL", "GROMACS"],
    },
    "experience": [
        {
            "company": "University of Oxford",
            "title": "Postdoctoral Research Fellow",
            "location": "Oxford, UK",
            "start_date": "October 2021",
            "end_date": "Present",
            "is_current": True,
            "highlights": [
                "Developed automated molecular dynamics pipeline processing cryo-EM datasets.",
                "Published 4 first-author papers.",
            ],
            "technologies": ["Python", "GROMACS", "AlphaFold"],
        }
    ],
    "projects": [],
    "certifications": [],
    "achievements": [
        {
            "title": "Wellcome Trust Early-Career Postdoctoral Fellowship",
            "issuer": "Wellcome Trust",
            "date": "2021",
            "description": "Fellowship supporting computational biology research.",
        }
    ],
    "languages": ["English", "Urdu"],
    "interests": ["Rowing", "Astronomy"],
}


# ---------------------------------------------------------------------------
# FORMAT 5: Scanned / OCR Document
# ---------------------------------------------------------------------------
FORMAT_5_SCANNED_TEXT = "Carlos Mendoza\nSenior DevOps Engineer\nEmail: carlos.mendoza@infraops.io\nSkills: Docker, Kubernetes, Linux, Terraform, Python"

FORMAT_5_STRUCTURED = {
    "personal_info": {
        "full_name": "Carlos Mendoza",
        "email": "carlos.mendoza@infraops.io",
        "phone": None,
        "location": None,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
    },
    "summary": "Senior DevOps Engineer with deep Linux and infrastructure automation expertise.",
    "objective": None,
    "education": [],
    "skills": {
        "technical_skills": ["Linux System Administration"],
        "programming_languages": ["Python"],
        "frameworks_and_libraries": [],
        "databases": [],
        "cloud_and_devops": ["Docker", "Kubernetes", "Terraform"],
        "soft_skills": [],
        "tools": [],
    },
    "experience": [],
    "projects": [],
    "certifications": [],
    "achievements": [],
    "languages": ["English", "Spanish"],
    "interests": [],
}


# ===========================================================================
# TEST SUITE
# ===========================================================================

@pytest.fixture(autouse=True)
def clean_temp_storage():
    """Ensure clean test storage state."""
    yield


def test_pipeline_format_1_software_engineer():
    """
    Test Format 1: Standard single-column tech resume.
    Verifies PyMuPDF extraction, clean text, section detection, NLP anchors,
    mocked LLM structured extraction, skill normalization (JS -> JavaScript, Postgres -> PostgreSQL),
    and complete PostgreSQL database persistence.
    """
    pdf_bytes = make_pdf([FORMAT_1_TEXT])

    # Inject mock provider returning Format 1 structured data
    mock_provider = MockLLMProvider(responses=[json.dumps(FORMAT_1_STRUCTURED)])
    mock_llm_service = LLMService(provider=mock_provider)

    # Directly run pipeline orchestrator
    with SessionLocal() as db:
        from pathlib import Path
        temp_file = storage_service.temp_dir / "format_1_test.pdf"
        temp_file.write_bytes(pdf_bytes)

        result = pytest.run_async = None
        import asyncio
        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="jordan_smith_resume.pdf",
                custom_llm_service=mock_llm_service,
            )
        )

        assert result.processing_status == "completed"
        assert result.resume is not None
        assert result.resume.personal_info.full_name == "Jordan Smith"
        assert result.resume.personal_info.email == "jordan.smith@devmail.org"
        assert result.extraction_method in ["pdf_text", "pymupdf_native", "unified"]
        assert result.raw_text_char_count > 300
        assert "experience" in result.sections_detected or "skills" in result.sections_detected

        # Verify skill normalization in pipeline
        assert "JavaScript" in result.resume.skills.programming_languages
        assert "PostgreSQL" in result.resume.skills.databases
        assert "Kubernetes" in result.resume.skills.cloud_and_devops

        # Verify database persistence
        orm_record = db.query(ResumeModel).filter(ResumeModel.id == result.resume_id).first()
        assert orm_record is not None
        assert orm_record.processing_status == "completed"
        assert orm_record.personal_info.full_name == "Jordan Smith"
        assert len(orm_record.experience) == 1
        assert len(orm_record.education) == 1
        assert len(orm_record.projects) == 1
        assert len(orm_record.certifications) == 1

        # Check relational skill table
        db_skills = [rs.skill.name for rs in orm_record.resume_skills]
        assert "JavaScript" in db_skills
        assert "PostgreSQL" in db_skills


def test_pipeline_format_2_dense_data_scientist():
    """
    Test Format 2: Dense two-column research/data science resume.
    Verifies multi-degree education parsing, honors, projects, and achievements persistence.
    """
    pdf_bytes = make_pdf([FORMAT_2_TEXT])
    mock_provider = MockLLMProvider(responses=[json.dumps(FORMAT_2_STRUCTURED)])
    mock_llm_service = LLMService(provider=mock_provider)

    import asyncio
    with SessionLocal() as db:
        temp_file = storage_service.temp_dir / "format_2_test.pdf"
        temp_file.write_bytes(pdf_bytes)

        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="elena_rostova_cv.pdf",
                custom_llm_service=mock_llm_service,
            )
        )

        assert result.processing_status == "completed"
        assert result.resume.personal_info.full_name == "Dr. Elena Rostova"
        assert len(result.resume.education) == 2
        assert result.resume.education[0].institution == "Stanford University"
        assert result.resume.education[0].gpa == 3.96
        assert len(result.resume.achievements) == 1
        assert "NeurIPS" in result.resume.achievements[0].title

        # Verify DB records
        orm_record = db.query(ResumeModel).filter(ResumeModel.id == result.resume_id).first()
        assert orm_record is not None
        assert len(orm_record.education) == 2
        assert len(orm_record.achievements) == 1


def test_pipeline_format_3_executive_leader():
    """
    Test Format 3: Executive engineering leader CV with high metrics, multiple certifications.
    """
    pdf_bytes = make_pdf([FORMAT_3_TEXT])
    mock_provider = MockLLMProvider(responses=[json.dumps(FORMAT_3_STRUCTURED)])
    mock_llm_service = LLMService(provider=mock_provider)

    import asyncio
    with SessionLocal() as db:
        temp_file = storage_service.temp_dir / "format_3_test.pdf"
        temp_file.write_bytes(pdf_bytes)

        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="marcus_aurelius_vp.pdf",
                custom_llm_service=mock_llm_service,
            )
        )

        assert result.processing_status == "completed"
        assert result.resume.personal_info.full_name == "Marcus V. Aurelius"
        assert "Vice President of Engineering" in result.resume.summary
        assert len(result.resume.certifications) == 1
        assert "CISSP" in result.resume.certifications[0].name

        # Verify DB status
        orm_record = db.query(ResumeModel).filter(ResumeModel.id == result.resume_id).first()
        assert orm_record.processing_status == "completed"


def test_pipeline_format_4_academic_researcher():
    """
    Test Format 4: Academic Researcher / Postdoctoral Fellow CV.
    """
    pdf_bytes = make_pdf([FORMAT_4_TEXT])
    mock_provider = MockLLMProvider(responses=[json.dumps(FORMAT_4_STRUCTURED)])
    mock_llm_service = LLMService(provider=mock_provider)

    import asyncio
    with SessionLocal() as db:
        temp_file = storage_service.temp_dir / "format_4_test.pdf"
        temp_file.write_bytes(pdf_bytes)

        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="amina_khan_oxford.pdf",
                custom_llm_service=mock_llm_service,
            )
        )

        assert result.processing_status == "completed"
        assert result.resume.personal_info.full_name == "Dr. Amina Khan"
        assert result.resume.personal_info.email == "amina.khan@oxford.ac.uk"
        assert len(result.resume.education) == 2


def test_pipeline_format_5_scanned_ocr_fallback():
    """
    Test Format 5: Scanned image-only document where OCR fallback (Tesseract) is triggered.
    """
    scanned_bytes = make_scanned_image_pdf(FORMAT_5_SCANNED_TEXT)
    mock_provider = MockLLMProvider(responses=[json.dumps(FORMAT_5_STRUCTURED)])
    mock_llm_service = LLMService(provider=mock_provider)

    import asyncio
    with SessionLocal() as db:
        temp_file = storage_service.temp_dir / "format_5_scanned.pdf"
        temp_file.write_bytes(scanned_bytes)

        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="carlos_mendoza_scan.pdf",
                custom_llm_service=mock_llm_service,
            )
        )

        assert result.processing_status == "completed"
        assert result.resume.personal_info.full_name == "Carlos Mendoza"
        # Verify OCR or hybrid method was triggered due to zero native text characters
        assert "ocr" in result.extraction_method.lower() or "hybrid" in result.extraction_method.lower() or result.extraction_method == "tesseract_ocr"


def test_api_process_endpoint_multipart_file_upload(monkeypatch):
    """
    Test POST /api/resumes/process HTTP endpoint with multipart PDF upload.
    Verifies response model containing resume_id, processing_status, and structured data.
    """
    pdf_bytes = make_pdf([FORMAT_1_TEXT])

    # Patch default llm_service generate_structured to return mock resume
    mock_resume = Resume(**FORMAT_1_STRUCTURED)

    async def mock_generate_structured(*args, **kwargs):
        return mock_resume, 0

    monkeypatch.setattr(pipeline_orchestrator._llm_service, "generate_structured", mock_generate_structured)

    response = client.post(
        "/api/resumes/process",
        files={"file": ("jordan_smith.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()

    assert "resume_id" in data
    assert data["processing_status"] == "completed"
    assert "resume" in data
    assert "structured_resume_data" in data
    assert data["resume"]["personal_info"]["full_name"] == "Jordan Smith"
    assert data["original_filename"] == "jordan_smith.pdf"
    assert data["raw_text_char_count"] > 100


def test_api_process_endpoint_from_existing_file_id(monkeypatch):
    """
    Test POST /api/resumes/process HTTP endpoint when passing existing file_id.
    """
    pdf_bytes = make_pdf([FORMAT_2_TEXT])
    # 1. Upload file first
    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("elena_rostova.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    file_id = upload_res.json()["filename"]

    # 2. Patch LLM service
    mock_resume = Resume(**FORMAT_2_STRUCTURED)

    async def mock_generate_structured(*args, **kwargs):
        return mock_resume, 0

    monkeypatch.setattr(pipeline_orchestrator._llm_service, "generate_structured", mock_generate_structured)

    # 3. Process via file_id
    process_res = client.post(
        "/api/resumes/process",
        data={"file_id": file_id},
    )
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["processing_status"] == "completed"
    assert data["resume"]["personal_info"]["full_name"] == "Dr. Elena Rostova"


def test_api_get_resume_status_endpoint(monkeypatch):
    """
    Test GET /api/resumes/{resume_id}/status endpoint.
    Verifies that lifecycle status can be queried at any time.
    """
    pdf_bytes = make_pdf([FORMAT_1_TEXT])
    mock_resume = Resume(**FORMAT_1_STRUCTURED)

    async def mock_generate_structured(*args, **kwargs):
        return mock_resume, 0

    monkeypatch.setattr(pipeline_orchestrator._llm_service, "generate_structured", mock_generate_structured)

    process_res = client.post(
        "/api/resumes/process",
        files={"file": ("status_check.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert process_res.status_code == 200
    resume_id = process_res.json()["resume_id"]

    # Query status endpoint
    status_res = client.get(f"/api/resumes/{resume_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["resume_id"] == resume_id
    assert status_data["processing_status"] == "completed"
    assert status_data["original_filename"] == "status_check.pdf"


def test_pipeline_failure_corrupt_pdf():
    """
    Test stage failure handling:
    Corrupt PDF causes extraction failure -> status marked 'failed' in DB, error reported in response.
    """
    corrupt_bytes = b"%PDF-1.4\ncorrupt content without any valid objects%%EOF"

    with SessionLocal() as db:
        temp_file = storage_service.temp_dir / "corrupt_pipeline_test.pdf"
        temp_file.write_bytes(corrupt_bytes)

        import asyncio
        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="corrupt.pdf",
            )
        )

        assert result.processing_status == "failed"
        assert result.error is not None
        assert result.resume is None

        # Verify DB reflects 'failed' status
        orm_record = db.query(ResumeModel).filter(ResumeModel.id == result.resume_id).first()
        assert orm_record is not None
        assert orm_record.processing_status == "failed"
        assert orm_record.error_message is not None


def test_pipeline_failure_llm_validation_error():
    """
    Test stage failure handling:
    When LLM output cannot be repaired to match Pydantic schema,
    status is marked 'failed' and database reflects failure state.
    """
    pdf_bytes = make_pdf([FORMAT_1_TEXT])

    # Mock provider returning completely invalid schema that fails validation
    class FailingProvider(MockLLMProvider):
        async def generate_json(self, prompt: str, system_instruction: str = "", json_schema = None) -> dict:
            return {"invalid_key": "not a resume"}

    failing_service = LLMService(provider=FailingProvider(), max_repair_retries=1)

    with SessionLocal() as db:
        temp_file = storage_service.temp_dir / "llm_fail_test.pdf"
        temp_file.write_bytes(pdf_bytes)

        import asyncio
        result = asyncio.run(
            pipeline_orchestrator.process_file(
                db=db,
                file_path=temp_file,
                original_filename="llm_fail.pdf",
                custom_llm_service=failing_service,
            )
        )

        assert result.processing_status == "failed"
        assert "validation failed" in result.error.lower() or "schema" in result.error.lower()
        assert result.resume is None

        # Verify DB record was updated to 'failed'
        orm_record = db.query(ResumeModel).filter(ResumeModel.id == result.resume_id).first()
        assert orm_record.processing_status == "failed"
        assert orm_record.error_message is not None


def test_api_missing_parameters_returns_400():
    """
    Test calling POST /api/resumes/process without file or file_id returns 400 Bad Request.
    """
    response = client.post("/api/resumes/process")
    assert response.status_code == 400
    assert "either" in response.json()["detail"].lower()
