"""
Tests for Phase 20: User History & Lightweight Paginated Summaries.
Covers:
- Listing and pagination for resumes, jobs, and analyses
- Search and filtering
- Lightweight summaries (no oversized payloads)
- Detailed record retrieval
- Deletion
- User ownership and cross-user isolation
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal, Base, engine
from backend.app.models.resume_models import UserModel, ResumeModel, JobDescriptionModel, AnalysisHistoryModel

client = TestClient(app)


import uuid

@pytest.fixture(autouse=True)
def init_db():
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


def test_history_summary_counts():
    """Tests GET /api/history/summary returns valid aggregate counts."""
    response = client.get("/api/history/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_resumes" in data
    assert "total_jobs" in data
    assert "total_analyses" in data
    assert isinstance(data["total_resumes"], int)
    assert isinstance(data["total_jobs"], int)
    assert isinstance(data["total_analyses"], int)


def test_resume_history_pagination_and_lightweight_summary():
    """
    Tests GET /api/history/resumes returns paginated lightweight summary records
    without oversized raw text or full nested structures.
    """
    # Create sample resume
    resume_payload = {
        "original_filename": "history_test_candidate.pdf",
        "resume": {
            "personal_info": {"full_name": "History Test Candidate", "email": "history.cand@example.com"},
            "skills": {
                "programming_languages": ["Python", "Docker"],
                "technical_skills": ["CI/CD"],
            },
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
    }
    create_resp = client.post("/api/resumes/db", json=resume_payload)
    assert create_resp.status_code in [200, 201]

    # Query paginated history
    resp = client.get("/api/history/resumes?page=1&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 5
    assert data["meta"]["total"] >= 1

    # Verify lightweight structure: contains summary attributes, not giant blobs
    first_item = data["items"][0]
    assert "id" in first_item
    assert "original_filename" in first_item
    assert "processing_status" in first_item
    assert "created_at" in first_item
    # Ensure raw nested relations are excluded from summary
    assert "experience" not in first_item
    assert "education" not in first_item


def test_job_history_pagination_and_search():
    """
    Tests saving job descriptions and retrieving lightweight paginated history with search.
    """
    # Save job 1
    j1 = client.post(
        "/api/jobs",
        json={
            "title": "Staff Cloud Architect",
            "company": "Apex Global Systems",
            "text": "Seeking a Staff Cloud Architect with Kubernetes, Go, and AWS proficiency.",
        },
    )
    assert j1.status_code == 201

    # Query all jobs
    list_resp = client.get("/api/history/jobs?page=1&page_size=10")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["meta"]["total"] >= 1

    # Search by keyword
    search_resp = client.get("/api/history/jobs?search=Apex")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert any("Apex" in (item.get("company") or "") for item in search_data["items"])


def test_analysis_history_lifecycle_and_details():
    """
    Tests creating an analysis history record, listing via paginated endpoint,
    fetching full details, and deleting.
    """
    record_payload = {
        "candidate_name": "Jane Developer",
        "resume_filename": "jane_developer_resume.pdf",
        "job_title": "Lead Software Engineer",
        "company": "Apex Systems",
        "analysis_type": "job_match",
        "score": 0.85,
        "match_rate": 0.85,
        "summary": "Strong alignment across backend frameworks and cloud architectures.",
        "result_data": {
            "matched_skills": ["Python", "FastAPI", "Docker"],
            "missing_required_skills": ["Kubernetes"],
            "experience_analysis": "Exceeds the 5+ years minimum tenure requirement.",
        },
    }

    create_resp = client.post("/api/history/analyses", json=record_payload)
    assert create_resp.status_code == 201
    analysis_id = create_resp.json()["id"]
    assert create_resp.json()["job_title"] == "Lead Software Engineer"

    # List analyses
    list_resp = client.get("/api/history/analyses?page=1&page_size=10&analysis_type=job_match")
    assert list_resp.status_code == 200
    assert any(a["id"] == analysis_id for a in list_resp.json()["items"])

    # Fetch full detail
    detail_resp = client.get(f"/api/history/analyses/{analysis_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == analysis_id
    assert "result_data" in detail_data
    assert detail_data["result_data"]["matched_skills"] == ["Python", "FastAPI", "Docker"]

    # Delete record
    del_resp = client.delete(f"/api/history/analyses/{analysis_id}")
    assert del_resp.status_code == 200

    # Ensure 404 after deletion
    del_check = client.get(f"/api/history/analyses/{analysis_id}")
    assert del_check.status_code == 404


def test_cross_user_history_isolation():
    """
    Tests that User 1 cannot access or delete User 2's analysis records (403 Forbidden).
    """
    # 1. Register User 1
    u1_email = f"hist_u1_{uuid.uuid4().hex[:6]}@example.com"
    u1_reg = client.post("/api/auth/register", json={"email": u1_email, "password": "password123"})
    u1_token = u1_reg.json()["access_token"]

    # 2. Register User 2
    u2_email = f"hist_u2_{uuid.uuid4().hex[:6]}@example.com"
    u2_reg = client.post("/api/auth/register", json={"email": u2_email, "password": "password123"})
    u2_token = u2_reg.json()["access_token"]

    # 3. User 1 records an analysis
    rec_resp = client.post(
        "/api/history/analyses",
        json={
            "job_title": "Confidential Executive Role",
            "company": "Private Corp",
            "analysis_type": "job_match",
            "match_rate": 0.92,
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert rec_resp.status_code == 201
    record_id = rec_resp.json()["id"]

    # 4. User 1 can view details
    u1_view = client.get(f"/api/history/analyses/{record_id}", headers={"Authorization": f"Bearer {u1_token}"})
    assert u1_view.status_code == 200

    # 5. User 2 CANNOT view User 1's record -> 403 Forbidden
    u2_view = client.get(f"/api/history/analyses/{record_id}", headers={"Authorization": f"Bearer {u2_token}"})
    assert u2_view.status_code == 403

    # 6. User 2 CANNOT delete User 1's record -> 403 Forbidden
    u2_del = client.delete(f"/api/history/analyses/{record_id}", headers={"Authorization": f"Bearer {u2_token}"})
    assert u2_del.status_code == 403
