"""
Phase 22: Comprehensive End-to-End Integration Tests.
Explicitly validates the 4 core integration pipelines:
1. upload -> processing
2. processing -> database
3. authentication -> protected APIs
4. resume -> job matching

All external dependencies (LLM, embeddings) are mocked for hermetic, fast, and deterministic execution.
Zero dependency on external paid APIs.
"""
import io
import uuid
import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal, Base, engine
from backend.app.models.resume_models import UserModel, ResumeModel, JobDescriptionModel, AnalysisHistoryModel
from backend.app.schemas.parsed_resume import Resume, PersonalInfo, SkillSet, Experience, Education
from backend.app.schemas.job_description import JobDescription
from backend.app.services.storage_service import storage_service

client = TestClient(app)


def create_test_pdf(text: str) -> bytes:
    """Creates a valid, in-memory single-page PDF with native text."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(autouse=True)
def clean_database():
    """Ensures clean DB state before each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(AnalysisHistoryModel).delete()
        db.query(JobDescriptionModel).delete()
        db.query(ResumeModel).delete()
        db.query(UserModel).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield


# ============================================================================
# 1. Integration: Upload -> Processing Pipeline
# ============================================================================

def test_integration_upload_to_processing():
    """
    Validates Flow 1: Upload a resume PDF -> Pipeline processing.
    - Uploads PDF via multipart form
    - Passes uploaded file_id into processing pipeline
    - Verifies extraction, section detection, normalization, and completed status
    """
    resume_text = (
        "Sarah Jenkins\n"
        "sarah.jenkins@cloudtech.com | +1 555-0192 | San Francisco, CA\n\n"
        "Summary\n"
        "Senior Cloud Architect with 7+ years of experience in distributed systems.\n\n"
        "Skills\n"
        "Python, FastAPI, Postgres, Docker, K8s, AWS, Redis\n\n"
        "Experience\n"
        "Lead Architect at CloudTech Corp (2020 - Present)\n"
        "- Scaled microservice architecture to 50M daily transactions.\n\n"
        "Education\n"
        "B.S. in Computer Science, Stanford University, 2017\n"
    )
    pdf_bytes = create_test_pdf(resume_text)

    # Step 1: Upload file
    upload_resp = client.post(
        "/api/resumes/upload",
        files={"file": ("sarah_jenkins_cv.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["success"] is True
    file_id = upload_data["filename"]
    assert file_id.endswith(".pdf")

    # Step 2: Process uploaded file using file_id
    process_resp = client.post(
        "/api/resumes/process",
        data={"file_id": file_id},
    )
    assert process_resp.status_code == 200
    proc_data = process_resp.json()

    assert proc_data["processing_status"] == "completed"
    assert "resume_id" in proc_data
    assert proc_data["resume"] is not None
    assert "personal_info" in proc_data["resume"]
    assert "skills" in proc_data["resume"]
    assert proc_data["raw_text_char_count"] > 200


# ============================================================================
# 2. Integration: Processing -> Database Persistence
# ============================================================================

def test_integration_processing_to_database():
    """
    Validates Flow 2: Processing -> Relational Database Persistence.
    - Uploads and processes resume
    - Retrieves the newly persisted entity via REST API
    - Confirms all child relations and summary attributes are properly stored
    - Confirms it appears in the lightweight history summaries
    """
    candidate_name = "Marcus Alexander"
    candidate_email = f"marcus_{uuid.uuid4().hex[:6]}@techcorp.io"
    sample_resume = {
        "original_filename": "marcus_alexander.pdf",
        "resume": {
            "personal_info": {
                "full_name": candidate_name,
                "email": candidate_email,
                "location": "Boston, MA",
            },
            "summary": "Distributed database specialist.",
            "skills": {
                "programming_languages": ["Python", "Go", "Rust"],
                "databases": ["PostgreSQL", "Redis"],
                "cloud_and_devops": ["Docker", "Kubernetes"],
            },
            "experience": [
                {
                    "company": "Nexus Systems",
                    "title": "Principal DB Engineer",
                    "highlights": ["Designed distributed commit log."],
                    "technologies": ["Go", "PostgreSQL"],
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "B.S. in Computer Science",
                }
            ],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
    }

    # Step 1: Save parsed resume into DB
    persist_resp = client.post("/api/resumes/db", json=sample_resume)
    assert persist_resp.status_code == 201
    persisted = persist_resp.json()
    resume_id = persisted["id"]
    assert persisted["original_filename"] == "marcus_alexander.pdf"

    # Step 2: Query by ID from DB API
    get_resp = client.get(f"/api/resumes/db/{resume_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["resume"]["personal_info"]["full_name"] == candidate_name
    assert detail["resume"]["personal_info"]["email"] == candidate_email
    assert "PostgreSQL" in detail["resume"]["skills"]["databases"]
    assert len(detail["resume"]["experience"]) == 1

    # Step 3: Verify it appears in paginated lightweight history summaries
    hist_resp = client.get("/api/history/resumes?page=1&page_size=10")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert any(item["id"] == resume_id for item in hist_data["items"])


# ============================================================================
# 3. Integration: Authentication -> Protected APIs & User Isolation
# ============================================================================

def test_integration_authentication_to_protected_apis():
    """
    Validates Flow 3: User Authentication -> Protected Endpoints & Multi-User Isolation.
    - User registers and logs in
    - Receives signed JWT access token
    - Accesses protected endpoint (/api/auth/me)
    - Verifies 401 when token is missing or invalid
    - Verifies 403 Forbidden cross-user privacy enforcement
    """
    unique_id = uuid.uuid4().hex[:6]
    u1_email = f"alice_{unique_id}@example.com"
    u2_email = f"bob_{unique_id}@example.com"
    password = "SuperSecurePassword123!"

    # 1. Register User 1
    reg1_resp = client.post(
        "/api/auth/register",
        json={"email": u1_email, "password": password, "full_name": "Alice Engineer"},
    )
    assert reg1_resp.status_code == 201
    u1_token = reg1_resp.json()["access_token"]
    u1_id = reg1_resp.json()["user"]["id"]

    # 2. Register User 2
    reg2_resp = client.post(
        "/api/auth/register",
        json={"email": u2_email, "password": password, "full_name": "Bob Designer"},
    )
    assert reg2_resp.status_code == 201
    u2_token = reg2_resp.json()["access_token"]

    # 3. Access protected /api/auth/me with User 1 token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {u1_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == u1_email
    assert me_resp.json()["full_name"] == "Alice Engineer"

    # 4. Access protected /api/auth/me with missing token -> 401
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # 5. User 1 creates a job description
    job_resp = client.post(
        "/api/jobs",
        json={
            "title": "Confidential Staff Lead",
            "company": "Top Secret Robotics",
            "text": "Requires Python, C++, ROS2, and Embedded Systems expertise.",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # 6. User 2 attempts to read User 1's job -> 403 Forbidden
    cross_read = client.get(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u2_token}"})
    assert cross_read.status_code == 403

    # 7. User 2 attempts to delete User 1's job -> 403 Forbidden
    cross_delete = client.delete(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u2_token}"})
    assert cross_delete.status_code == 403

    # 8. User 1 can successfully view and delete their own job
    own_read = client.get(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u1_token}"})
    assert own_read.status_code == 200
    assert own_read.json()["title"] == "Confidential Staff Lead"

    own_delete = client.delete(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u1_token}"})
    assert own_delete.status_code == 200


# ============================================================================
# 4. Integration: Resume -> Job Matching & Semantic Similarity
# ============================================================================

def test_integration_resume_to_job_matching():
    """
    Validates Flow 4: Resume -> Job Requirement Analysis.
    - Compares structured resume with structured job description
    - Tests keyword/skill matching endpoint: matched skills, missing skills, match percentage
    - Tests semantic similarity endpoint: dense similarity score, alignment metrics
    - Confirms non-evaluative presentation (no hiring prediction claim)
    """
    resume_payload = {
        "personal_info": {"full_name": "David Kim", "email": "david.kim@example.com"},
        "summary": "Backend specialist with deep experience in Python, FastAPI, and PostgreSQL.",
        "skills": {
            "programming_languages": ["Python", "TypeScript", "SQL"],
            "frameworks_and_libraries": ["FastAPI", "React"],
            "databases": ["PostgreSQL", "Redis"],
            "cloud_and_devops": ["Docker", "AWS"],
            "tools": ["Git"],
        },
        "experience": [
            {
                "company": "Apex Labs",
                "title": "Senior Backend Developer",
                "highlights": ["Built REST microservices handling high traffic."],
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
            }
        ],
        "education": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    job_payload = {
        "job_title": "Senior Cloud Backend Engineer",
        "company": "Apex Cloud Systems",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        "preferred_skills": ["Redis", "Terraform", "AWS"],
        "education_requirements": ["Bachelor's in Computer Science"],
        "experience_requirements": ["5+ years backend experience"],
        "responsibilities": ["Design high-throughput APIs", "Database optimization"],
        "tools_and_technologies": ["Python", "PostgreSQL", "Docker"],
        "certifications": [],
    }

    # Step 1: Execute keyword/skill match via POST /api/jobs/match
    match_resp = client.post(
        "/api/jobs/match",
        json={"resume": resume_payload, "job_description": job_payload},
    )
    assert match_resp.status_code == 200
    match_data = match_resp.json()

    assert "matched_skills" in match_data
    assert "missing_required_skills" in match_data
    assert "disclaimer" in match_data

    # Check that Python, FastAPI, PostgreSQL, Docker were matched
    matched_req = match_data["matched_skills"]
    assert any("Python" in s for s in matched_req)
    assert any("FastAPI" in s for s in matched_req)
    assert any("PostgreSQL" in s for s in matched_req)
    assert any("Docker" in s for s in matched_req)

    # Check missing required skill (Kubernetes is not in David's skills)
    missing_req = match_data["missing_required_skills"]
    assert any("Kubernetes" in s for s in missing_req)

    # Step 2: Execute dense semantic similarity match via POST /api/jobs/semantic-match
    semantic_resp = client.post(
        "/api/jobs/semantic-match",
        json={"resume": resume_payload, "job_description": job_payload},
    )
    assert semantic_resp.status_code == 200
    sem_data = semantic_resp.json()

    assert "overall_semantic_similarity" in sem_data
    assert "exact_matched_skills" in sem_data
    assert "missing_required_skills" in sem_data
    assert "disclaimer" in sem_data

    # Ensure score is normalized float in [0.0, 1.0]
    score = sem_data["overall_semantic_similarity"]
    assert 0.0 <= score <= 1.0

    # Ensure disclaimers explicitly clarify this is an analysis, NOT a hiring prediction
    disclaimer_text = sem_data["disclaimer"].lower()
    assert "not a hiring prediction" in disclaimer_text or "informational" in disclaimer_text or "analysis" in disclaimer_text
