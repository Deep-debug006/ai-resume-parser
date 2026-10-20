"""
Normalized SQLAlchemy ORM Models for PostgreSQL Database Persistence (Phase 11).
Contains models for:
- users
- resumes
- resume_personal_info
- education
- skills
- resume_skills
- experience
- projects
- certifications
- achievements
"""
import uuid
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class UserModel(Base):
    """
    Users table for authentication and resource ownership (Phase 18).
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    resumes = relationship("ResumeModel", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescriptionModel", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("AnalysisHistoryModel", back_populates="user", cascade="all, delete-orphan")


class ResumeModel(Base):
    """
    Resumes parent table storing document metadata, extraction info, and lifecycle status.
    """
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    file_identifier = Column(String(255), nullable=True, index=True)
    processing_status = Column(String(50), nullable=False, default="processed", index=True)
    extraction_method = Column(String(50), nullable=True, default="unified")
    raw_text_char_count = Column(Integer, default=0, nullable=False)
    summary = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    languages = Column(JSON, default=list, nullable=False)
    interests = Column(JSON, default=list, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("UserModel", back_populates="resumes")
    personal_info = relationship(
        "ResumePersonalInfoModel",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    education = relationship(
        "EducationModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="EducationModel.id",
    )
    resume_skills = relationship(
        "ResumeSkillModel",
        back_populates="resume",
        cascade="all, delete-orphan",
    )
    experience = relationship(
        "ExperienceModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ExperienceModel.id",
    )
    projects = relationship(
        "ProjectModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ProjectModel.id",
    )
    certifications = relationship(
        "CertificationModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="CertificationModel.id",
    )
    achievements = relationship(
        "AchievementModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="AchievementModel.id",
    )


class ResumePersonalInfoModel(Base):
    """
    Personal and contact information extracted from the resume.
    """
    __tablename__ = "resume_personal_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume = relationship("ResumeModel", back_populates="personal_info")


class SkillModel(Base):
    """
    Centralized canonical skill dictionary table.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume_skills = relationship("ResumeSkillModel", back_populates="skill", cascade="all, delete-orphan")


class ResumeSkillModel(Base):
    """
    Join table linking resumes to skills with categorization.
    """
    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("resume_id", "skill_id", name="uq_resume_skill"),
    )

    resume = relationship("ResumeModel", back_populates="resume_skills")
    skill = relationship("SkillModel", back_populates="resume_skills")


class EducationModel(Base):
    """
    Education history records.
    """
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution = Column(String(255), nullable=False, index=True)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    gpa = Column(Float, nullable=True)
    gpa_max = Column(Float, nullable=True)
    honors = Column(JSON, default=list, nullable=False)
    courses = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume = relationship("ResumeModel", back_populates="education")


class ExperienceModel(Base):
    """
    Work experience entries.
    """
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    highlights = Column(JSON, default=list, nullable=False)
    technologies = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume = relationship("ResumeModel", back_populates="experience")


class ProjectModel(Base):
    """
    Project showcase records.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    highlights = Column(JSON, default=list, nullable=False)
    technologies = Column(JSON, default=list, nullable=False)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume = relationship("ResumeModel", back_populates="projects")


class CertificationModel(Base):
    """
    Certifications and licenses.
    """
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    issuer = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=True)
    expiration_date = Column(String(50), nullable=True)
    credential_id = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume = relationship("ResumeModel", back_populates="certifications")


class AchievementModel(Base):
    """
    Honors, awards, and achievements.
    """
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False, index=True)
    issuer = Column(String(255), nullable=True)
    date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume = relationship("ResumeModel", back_populates="achievements")
 
 
class JobDescriptionModel(Base):
    """
    Persisted Job Descriptions with user ownership (Phase 18).
    """
    __tablename__ = "job_descriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=True, index=True)
    company = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("UserModel", back_populates="job_descriptions")


class AnalysisHistoryModel(Base):
    """
    Persisted Resume-to-Job Matching and Quality Analysis Records (Phase 20).
    Enforces user ownership, lightweight summary queries, and detailed retrieval.
    """
    __tablename__ = "analysis_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    resume_id = Column(
        String(36),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    candidate_name = Column(String(255), nullable=True)
    resume_filename = Column(String(255), nullable=True)
    job_id = Column(
        String(36),
        ForeignKey("job_descriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_title = Column(String(255), nullable=True, index=True)
    company = Column(String(255), nullable=True)
    analysis_type = Column(String(50), nullable=False, default="job_match", index=True)  # job_match, semantic_match, resume_quality
    score = Column(Float, nullable=True)
    match_rate = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("UserModel", back_populates="analyses")
