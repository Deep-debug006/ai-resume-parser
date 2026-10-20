"""
Database seed script for Phase 11 PostgreSQL persistence.
Seeds:
- Default user
- Canonical skills from skill_aliases.json
- Complete sample resume with education, skills, experience, projects, certifications, and achievements.
"""
import logging
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal, engine, Base
from backend.app.models.resume_models import (
    UserModel,
    SkillModel,
    ResumeModel,
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
from backend.app.services.resume_db_service import resume_db_service
from backend.app.services.skill_normalizer import skill_normalizer

logger = logging.getLogger(__name__)


def seed_database(db: Session = None) -> ResumeModel:
    """
    Seeds initial users, canonical skills, and a sample full resume into PostgreSQL.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # 1. Create default demo user
        from backend.app.services.auth_service import auth_service
        user = db.query(UserModel).filter(UserModel.email == "developer.demo@example.com").first()
        if not user:
            user = UserModel(
                email="developer.demo@example.com",
                full_name="Alex Mercer",
                hashed_password=auth_service.hash_password("demo123"),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created seed user: %s", user.email)
        elif not user.hashed_password:
            user.hashed_password = auth_service.hash_password("demo123")
            db.commit()

        # 2. Seed canonical skills from dictionary
        canonical_count = 0
        for skill_name in skill_normalizer._canonical_skills:
            existing = db.query(SkillModel).filter(SkillModel.name == skill_name).first()
            if not existing:
                db.add(SkillModel(name=skill_name))
                canonical_count += 1
        db.commit()
        if canonical_count > 0:
            logger.info("Seeded %d canonical skills into database.", canonical_count)

        # 3. Check if sample resume already exists
        existing_sample = (
            db.query(ResumeModel)
            .filter(ResumeModel.original_filename == "alex_mercer_sample.pdf")
            .first()
        )
        if existing_sample:
            logger.info("Sample resume already seeded: %s", existing_sample.id)
            return existing_sample

        # 4. Construct rich Pydantic Resume
        sample_resume = Resume(
            personal_info=PersonalInfo(
                full_name="Alex Mercer",
                email="alex.mercer@techinnovations.io",
                phone="+1 (415) 889-1020",
                location="San Francisco, CA",
                linkedin_url="https://linkedin.com/in/alexmercer",
                github_url="https://github.com/alexmercer",
                portfolio_url="https://alexmercer.dev",
            ),
            summary="Senior Cloud and Backend Software Engineer with 7+ years of expertise designing resilient microservice architectures and distributed event processing systems.",
            objective=None,
            education=[
                Education(
                    institution="University of Texas at Austin",
                    degree="Bachelor of Science",
                    field_of_study="Computer Science",
                    start_date="2014",
                    end_date="2018",
                    gpa=3.85,
                    gpa_max=4.0,
                    honors=["Dean's Exemplary Scholar", "Summa Cum Laude"],
                    courses=["Distributed Operating Systems", "Algorithms", "Database Systems"],
                )
            ],
            skills=SkillSet(
                technical_skills=["Microservices", "RESTful APIs", "System Architecture"],
                programming_languages=["Python", "Go", "TypeScript", "SQL"],
                frameworks_and_libraries=["FastAPI", "React", "Docker"],
                databases=["PostgreSQL", "Redis", "MongoDB"],
                cloud_and_devops=["Amazon Web Services", "Kubernetes", "Terraform", "CI/CD"],
                soft_skills=["Technical Leadership", "Agile", "Mentorship"],
                tools=["Git", "GitHub Actions", "Docker Compose"],
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
                        "Architected asynchronous event streaming pipelines handling 50M daily events with sub-50ms latency.",
                        "Optimized PostgreSQL connection pooling and multi-region read replicas, reducing p99 latency by 40%.",
                        "Led team of 6 engineers across sprint cycles and code quality reviews.",
                    ],
                    technologies=["Python", "FastAPI", "PostgreSQL", "Kafka", "Kubernetes"],
                ),
                Experience(
                    company="Acrobyte Technologies",
                    title="Backend Developer",
                    location="Austin, TX",
                    start_date="June 2018",
                    end_date="February 2021",
                    is_current=False,
                    highlights=[
                        "Implemented secure RESTful endpoints and role-based access control.",
                        "Authored comprehensive integration and unit test suites reaching 94% coverage.",
                    ],
                    technologies=["Python", "Docker", "PostgreSQL", "Redis"],
                ),
            ],
            projects=[
                Project(
                    name="OpenMesh Gateway",
                    description="Open-source dynamic reverse proxy with automated TLS certificate management.",
                    url="https://github.com/alexmercer/openmesh",
                    highlights=["1,200+ GitHub stars and 50+ community contributors"],
                    technologies=["Go", "Docker", "gRPC"],
                    start_date="2022",
                    end_date="Present",
                )
            ],
            certifications=[
                Certification(
                    name="AWS Certified Solutions Architect - Associate",
                    issuer="Amazon Web Services",
                    issue_date="2022",
                    expiration_date="2025",
                    credential_id="AWS-SAA-839210",
                    url="https://aws.amazon.com/verification",
                )
            ],
            achievements=[
                Achievement(
                    title="1st Place Winner - Distributed Systems Hackathon",
                    issuer="TechCrunch Disrupt",
                    date="2021",
                    description="Built fault-tolerant edge data synchronizer in 48 hours.",
                )
            ],
            languages=["English (Native)", "Spanish (Conversational)"],
            interests=["Open Source Systems", "Rust Programming", "Rock Climbing"],
        )

        orm_resume, _ = resume_db_service.save_parsed_resume(
            db=db,
            resume=sample_resume,
            original_filename="alex_mercer_sample.pdf",
            user_id=user.id,
            extraction_method="unified",
            raw_text_char_count=1850,
        )

        logger.info("Successfully seeded resume ID: %s", orm_resume.id)
        return orm_resume

    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
