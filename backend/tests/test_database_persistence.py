"""
Unit and integration tests for Phase 11: PostgreSQL Database Persistence.
Tests complete lifecycle:
- Create resume
- Retrieve resume with all relations
- Update resume and child collections
- Delete resume with cascading integrity
- Relational mappings (User -> Resumes -> PersonalInfo, Education, Skills, Experience, Projects, Certs, Achievements)
- REST API persistence endpoints
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.db.session import SessionLocal, get_db, Base, engine
from backend.app.models.resume_models import (
    UserModel,
    ResumeModel,
    ResumePersonalInfoModel,
    SkillModel,
    ResumeSkillModel,
    EducationModel,
    ExperienceModel,
    ProjectModel,
    CertificationModel,
    AchievementModel,
)
from backend.app.schemas.parsed_resume import (
    Resume,
    PersonalInfo,
    Education,
    SkillSet,
    Experience,
    Project,
    Certification,
    Achievement,
)
from backend.app.repositories.resume_repository import resume_repository
from backend.app.services.resume_db_service import resume_db_service

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provides a transactional database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_pydantic_resume():
    """Fixture providing a complete canonical Resume model."""
    return Resume(
        personal_info=PersonalInfo(
            full_name="Jordan Vance",
            email="jordan.vance@innovatech.io",
            phone="+1 (555) 432-8765",
            location="Seattle, WA",
            linkedin_url="https://linkedin.com/in/jordanvance",
            github_url="https://github.com/jordanvance",
            portfolio_url="https://jordanvance.io",
        ),
        summary="Principal Platform Architect with 10 years of experience designing scalable data architectures.",
        objective=None,
        education=[
            Education(
                institution="University of Washington",
                degree="M.S.",
                field_of_study="Computer Engineering",
                start_date="2012",
                end_date="2014",
                gpa=3.92,
                gpa_max=4.0,
                honors=["Graduate Fellowship"],
                courses=["Advanced Distributed Systems", "Database Internals"],
            )
        ],
        skills=SkillSet(
            technical_skills=["Distributed Systems", "Database Optimization"],
            programming_languages=["Python", "Go", "TypeScript"],
            frameworks_and_libraries=["FastAPI", "React"],
            databases=["PostgreSQL", "Redis", "MongoDB"],
            cloud_and_devops=["Amazon Web Services", "Kubernetes", "Terraform"],
            soft_skills=["Architecture Review", "Team Leadership"],
            tools=["Git", "Docker"],
        ),
        experience=[
            Experience(
                company="HyperScale Cloud",
                title="Staff Infrastructure Engineer",
                location="Seattle, WA",
                start_date="2020",
                end_date="Present",
                is_current=True,
                highlights=[
                    "Spearheaded multi-tenant database migration reducing compute costs by $1.2M annually.",
                    "Designed zero-downtime failover protocol for PostgreSQL clusters.",
                ],
                technologies=["PostgreSQL", "Go", "Kubernetes"],
            )
        ],
        projects=[
            Project(
                name="RaftDB",
                description="Distributed consensus key-value database built in Go.",
                url="https://github.com/jordanvance/raftdb",
                highlights=["Implemented Raft protocol from paper specifications."],
                technologies=["Go", "gRPC"],
                start_date="2021",
                end_date="2022",
            )
        ],
        certifications=[
            Certification(
                name="AWS Certified Solutions Architect - Professional",
                issuer="Amazon Web Services",
                issue_date="2021",
                expiration_date="2024",
                credential_id="AWS-SAP-102938",
                url=None,
            )
        ],
        achievements=[
            Achievement(
                title="Keynote Speaker at CloudNativeConf",
                issuer="Cloud Native Foundation",
                date="2023",
                description="Delivered keynote on distributed state management.",
            )
        ],
        languages=["English", "French"],
        interests=["Distributed Consensus", "Sailing"],
    )


def test_create_and_retrieve_resume(db_session: Session, sample_pydantic_resume: Resume):
    """
    Test 1: CREATE and RETRIEVE resume with all normalized relational tables.
    Verifies that foreign keys and child records are persisted correctly.
    """
    # 1. Create a user
    user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    user = UserModel(email=user_email, full_name="Jordan Vance")
    db_session.add(user)
    db_session.commit()

    # 2. Persist resume via repository
    orm_resume = resume_repository.create(
        db=db_session,
        resume_data=sample_pydantic_resume,
        original_filename="jordan_vance_resume.pdf",
        user_id=user.id,
        processing_status="processed",
        extraction_method="unified",
        raw_text_char_count=1650,
    )

    resume_id = orm_resume.id
    assert resume_id is not None
    assert orm_resume.user_id == user.id

    # 3. Retrieve and verify relational integrity
    fetched = resume_repository.get_by_id(db_session, resume_id)
    assert fetched is not None
    assert fetched.original_filename == "jordan_vance_resume.pdf"
    assert fetched.personal_info is not None
    assert fetched.personal_info.full_name == "Jordan Vance"
    assert fetched.personal_info.email == "jordan.vance@innovatech.io"
    assert len(fetched.education) == 1
    assert fetched.education[0].institution == "University of Washington"
    assert len(fetched.experience) == 1
    assert fetched.experience[0].company == "HyperScale Cloud"
    assert len(fetched.projects) == 1
    assert fetched.projects[0].name == "RaftDB"
    assert len(fetched.certifications) == 1
    assert len(fetched.achievements) == 1
    assert len(fetched.resume_skills) > 0

    # 4. Verify decoupling / conversion to pure Pydantic Resume
    pyd_resume = resume_repository.to_pydantic(fetched)
    assert isinstance(pyd_resume, Resume)
    assert pyd_resume.personal_info.full_name == "Jordan Vance"
    assert "PostgreSQL" in pyd_resume.skills.databases
    assert "Python" in pyd_resume.skills.programming_languages


def test_update_resume(db_session: Session, sample_pydantic_resume: Resume):
    """
    Test 2: UPDATE resume and child collections.
    Verifies changes to personal info, summary, experience, and skills are applied.
    """
    # 1. Create initial resume
    orm_resume = resume_repository.create(
        db=db_session,
        resume_data=sample_pydantic_resume,
        original_filename="initial_resume.pdf",
    )
    resume_id = orm_resume.id

    # 2. Modify Pydantic model
    updated_model = sample_pydantic_resume.model_copy(deep=True)
    updated_model.personal_info.location = "San Francisco, CA"
    updated_model.summary = "Updated Senior Platform Architect Summary"
    updated_model.skills.programming_languages.append("Rust")

    # 3. Apply update
    updated_orm = resume_repository.update(db_session, resume_id, updated_model)
    assert updated_orm is not None

    # 4. Verify changes
    refetched = resume_repository.get_by_id(db_session, resume_id)
    assert refetched.personal_info.location == "San Francisco, CA"
    assert refetched.summary == "Updated Senior Platform Architect Summary"

    refetched_pyd = resume_repository.to_pydantic(refetched)
    assert "Rust" in refetched_pyd.skills.programming_languages


def test_delete_resume_cascades_cleanly(db_session: Session, sample_pydantic_resume: Resume):
    """
    Test 3: DELETE resume cascades to all child tables without leaving orphan records.
    Verifies parent user and global skills dictionary remain intact.
    """
    # 1. Create user and resume
    user = UserModel(email=f"cascade_{uuid.uuid4().hex[:8]}@example.com", full_name="Cascade User")
    db_session.add(user)
    db_session.commit()

    orm_resume = resume_repository.create(
        db=db_session,
        resume_data=sample_pydantic_resume,
        original_filename="delete_test.pdf",
        user_id=user.id,
    )
    resume_id = orm_resume.id
    user_id = user.id

    # Verify child records exist
    assert db_session.query(ResumePersonalInfoModel).filter_by(resume_id=resume_id).count() == 1
    assert db_session.query(EducationModel).filter_by(resume_id=resume_id).count() == 1
    assert db_session.query(ExperienceModel).filter_by(resume_id=resume_id).count() == 1
    assert db_session.query(ProjectModel).filter_by(resume_id=resume_id).count() == 1
    assert db_session.query(ResumeSkillModel).filter_by(resume_id=resume_id).count() > 0

    # 2. Delete resume
    deleted = resume_repository.delete(db_session, resume_id)
    assert deleted is True

    # 3. Verify cascading deletion of all child records
    assert db_session.query(ResumeModel).filter_by(id=resume_id).first() is None
    assert db_session.query(ResumePersonalInfoModel).filter_by(resume_id=resume_id).count() == 0
    assert db_session.query(EducationModel).filter_by(resume_id=resume_id).count() == 0
    assert db_session.query(ExperienceModel).filter_by(resume_id=resume_id).count() == 0
    assert db_session.query(ProjectModel).filter_by(resume_id=resume_id).count() == 0
    assert db_session.query(ResumeSkillModel).filter_by(resume_id=resume_id).count() == 0

    # 4. Verify parent user and global skills dictionary were NOT deleted
    assert db_session.query(UserModel).filter_by(id=user_id).first() is not None
    assert db_session.query(SkillModel).count() > 0


def test_user_resume_one_to_many_relationship(db_session: Session, sample_pydantic_resume: Resume):
    """
    Test 4: User to Resumes 1:N relationship.
    Verifies user.resumes collection contains all resumes owned by the user.
    """
    user = UserModel(email=f"multi_{uuid.uuid4().hex[:8]}@example.com", full_name="Multi User")
    db_session.add(user)
    db_session.commit()

    r1 = resume_repository.create(db_session, sample_pydantic_resume, "v1.pdf", user_id=user.id)
    r2 = resume_repository.create(db_session, sample_pydantic_resume, "v2.pdf", user_id=user.id)

    db_session.refresh(user)
    assert len(user.resumes) == 2
    resume_ids = [r.id for r in user.resumes]
    assert r1.id in resume_ids
    assert r2.id in resume_ids


def test_api_crud_endpoints_cycle(sample_pydantic_resume: Resume):
    """
    Test 5: Full REST API CRUD cycle via FastAPI TestClient.
    - POST /api/resumes/db (Create)
    - GET /api/resumes/db (List)
    - GET /api/resumes/db/{id} (Retrieve)
    - PUT /api/resumes/db/{id} (Update)
    - DELETE /api/resumes/db/{id} (Delete)
    - GET /api/resumes/db/stats (Metrics)
    """
    # 1. CREATE
    create_payload = {
        "resume": sample_pydantic_resume.model_dump(),
        "original_filename": "api_test_resume.pdf",
        "extraction_method": "pdf_text",
        "raw_text_char_count": 1420,
    }
    create_res = client.post("/api/resumes/db", json=create_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    resume_id = created_data["id"]
    assert created_data["original_filename"] == "api_test_resume.pdf"
    assert created_data["resume"]["personal_info"]["full_name"] == "Jordan Vance"

    # 2. LIST
    list_res = client.get("/api/resumes/db")
    assert list_res.status_code == 200
    resumes_list = list_res.json()
    assert any(r["id"] == resume_id for r in resumes_list)

    # 3. GET BY ID
    get_res = client.get(f"/api/resumes/db/{resume_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == resume_id
    assert detail["resume"]["personal_info"]["email"] == "jordan.vance@innovatech.io"

    # 4. UPDATE
    updated_resume_data = sample_pydantic_resume.model_dump()
    updated_resume_data["summary"] = "New API Summary for Testing"
    update_res = client.put(
        f"/api/resumes/db/{resume_id}",
        json={"resume": updated_resume_data},
    )
    assert update_res.status_code == 200
    assert update_res.json()["resume"]["summary"] == "New API Summary for Testing"

    # 5. STATS
    stats_res = client.get("/api/resumes/db/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_resumes"] >= 1
    assert stats["total_skills"] >= 1

    # 6. DELETE
    del_res = client.delete(f"/api/resumes/db/{resume_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 7. CONFIRM 404 AFTER DELETION
    not_found_res = client.get(f"/api/resumes/db/{resume_id}")
    assert not_found_res.status_code == 404
