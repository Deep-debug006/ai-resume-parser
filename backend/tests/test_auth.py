"""
Tests for Phase 18: Authentication & Multi-User Resource Ownership.
Tests:
- registration
- login
- invalid credentials
- protected routes
- unauthorized access
- cross-user resume and job description isolation
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal, Base, engine
from backend.app.models.resume_models import UserModel, ResumeModel, JobDescriptionModel
from backend.app.schemas.parsed_resume import Resume, PersonalInfo

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure database tables are created and cleaned between tests."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(JobDescriptionModel).delete()
        db.query(ResumeModel).delete()
        db.query(UserModel).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield


def test_user_registration_success():
    """Tests successful user registration returning access token and user without password hash."""
    email = "test.user.reg@example.com"
    payload = {
        "email": email,
        "password": "strongPassword123!",
        "full_name": "Test User",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    user = data["user"]
    assert user["email"] == email
    assert user["full_name"] == "Test User"
    assert "password" not in user
    assert "hashed_password" not in user


def test_user_registration_duplicate_email():
    """Tests that registering an already existing email returns 400 Bad Request."""
    email = "duplicate.test@example.com"
    payload = {
        "email": email,
        "password": "password123",
    }
    # First registration
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_user_login_success():
    """Tests login with valid credentials returns a valid JWT access token."""
    email = "login.success@example.com"
    password = "validPassword888"
    client.post("/api/auth/register", json={"email": email, "password": password, "full_name": "Login User"})

    login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


def test_user_login_invalid_credentials():
    """Tests login with incorrect password or nonexistent user returns 401 Unauthorized."""
    email = "invalid.creds@example.com"
    password = "secretPassword123"
    client.post("/api/auth/register", json={"email": email, "password": password})

    # Wrong password
    bad_pw_resp = client.post("/api/auth/login", json={"email": email, "password": "wrongpassword"})
    assert bad_pw_resp.status_code == 401
    assert "Invalid email or password" in bad_pw_resp.json()["detail"]

    # Nonexistent email
    bad_email_resp = client.post("/api/auth/login", json={"email": "nonexistent@example.com", "password": password})
    assert bad_email_resp.status_code == 401


def test_protected_route_get_me():
    """Tests GET /api/auth/me with valid and invalid/missing JWT tokens."""
    email = "auth.me@example.com"
    reg_resp = client.post("/api/auth/register", json={"email": email, "password": "securepassword", "full_name": "Me User"})
    token = reg_resp.json()["access_token"]

    # Authorized request with Bearer token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == email
    assert me_data["full_name"] == "Me User"
    assert "hashed_password" not in me_data

    # Unauthorized request without token
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # Unauthorized request with malformed token
    fake_token_resp = client.get("/api/auth/me", headers={"Authorization": "Bearer totally-invalid-token"})
    assert fake_token_resp.status_code == 401


def test_cross_user_resume_isolation():
    """
    Tests that User 1 cannot access User 2's resume (returns 403 Forbidden).
    Ensures strict multi-user privacy and ownership.
    """
    # 1. Register User 1
    u1_resp = client.post("/api/auth/register", json={"email": "user1@example.com", "password": "password123"})
    u1_token = u1_resp.json()["access_token"]
    u1_id = u1_resp.json()["user"]["id"]

    # 2. Register User 2
    u2_resp = client.post("/api/auth/register", json={"email": "user2@example.com", "password": "password123"})
    u2_token = u2_resp.json()["access_token"]

    # 3. User 1 creates a resume
    resume_payload = {
        "original_filename": "user1_cv.pdf",
        "user_id": u1_id,
        "resume": {
            "personal_info": {"full_name": "User One", "email": "user1@example.com"},
            "skills": {
                "programming_languages": ["Python", "FastAPI"],
                "technical_skills": ["Backend Architecture"],
            },
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
    }
    create_resp = client.post(
        "/api/resumes/db",
        json=resume_payload,
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert create_resp.status_code == 201
    resume_id = create_resp.json()["id"]

    # 4. User 1 can access their own resume
    get_own_resp = client.get(
        f"/api/resumes/db/{resume_id}",
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert get_own_resp.status_code == 200

    # 5. User 2 CANNOT access User 1's resume -> 403 Forbidden
    get_other_resp = client.get(
        f"/api/resumes/db/{resume_id}",
        headers={"Authorization": f"Bearer {u2_token}"},
    )
    assert get_other_resp.status_code == 403
    assert "permission" in get_other_resp.json()["detail"].lower()

    # 6. Unauthenticated user CANNOT access User 1's resume -> 401 Unauthorized
    get_unauth_resp = client.get(f"/api/resumes/db/{resume_id}")
    assert get_unauth_resp.status_code == 401

    # 7. User 2 CANNOT delete User 1's resume -> 403 Forbidden
    delete_other_resp = client.delete(
        f"/api/resumes/db/{resume_id}",
        headers={"Authorization": f"Bearer {u2_token}"},
    )
    assert delete_other_resp.status_code == 403


def test_user_job_description_ownership():
    """
    Tests saving job descriptions linked to authenticated user and cross-user isolation.
    """
    # Register two users
    u1_resp = client.post("/api/auth/register", json={"email": "job_user1@example.com", "password": "password123"})
    u1_token = u1_resp.json()["access_token"]

    u2_resp = client.post("/api/auth/register", json={"email": "job_user2@example.com", "password": "password123"})
    u2_token = u2_resp.json()["access_token"]

    # User 1 saves a job description
    save_resp = client.post(
        "/api/jobs",
        json={
            "title": "Backend Architect",
            "company": "Tech Corp",
            "text": "Seeking a Senior Backend Engineer with Python and PostgreSQL experience.",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert save_resp.status_code == 201
    job_id = save_resp.json()["id"]

    # User 1 can view their job description
    view_u1 = client.get(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u1_token}"})
    assert view_u1.status_code == 200
    assert view_u1.json()["title"] == "Backend Architect"

    # User 2 CANNOT access User 1's job description -> 403 Forbidden
    view_u2 = client.get(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u2_token}"})
    assert view_u2.status_code == 403

    # User 2 CANNOT delete User 1's job description -> 403 Forbidden
    del_u2 = client.delete(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u2_token}"})
    assert del_u2.status_code == 403

    # User 1 CAN delete their own job description -> 200 OK
    del_u1 = client.delete(f"/api/jobs/{job_id}", headers={"Authorization": f"Bearer {u1_token}"})
    assert del_u1.status_code == 200
