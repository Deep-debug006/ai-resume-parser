"""
Pydantic schemas for Phase 11: PostgreSQL Database Persistence API.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.parsed_resume import Resume


class DBResumeCreateRequest(BaseModel):
    """
    Request to persist a structured resume model into PostgreSQL.
    """
    resume: Resume = Field(..., description="Canonical structured Resume model")
    original_filename: str = Field(..., min_length=1, description="Original uploaded filename")
    user_id: Optional[str] = Field(None, description="Optional associated user ID")
    file_identifier: Optional[str] = Field(None, description="Temporary isolation ID")
    extraction_method: Optional[str] = Field("unified", description="Text extraction method used")
    raw_text_char_count: Optional[int] = Field(0, description="Length of cleaned resume text")


class DBResumeUpdateRequest(BaseModel):
    """
    Request to update an existing persisted resume.
    """
    resume: Resume = Field(..., description="Updated canonical Resume model")


class DBResumeSummaryResponse(BaseModel):
    """
    Summary view of a persisted resume for listing.
    """
    id: str
    original_filename: str
    candidate_name: str
    candidate_email: Optional[str] = None
    processing_status: str
    extraction_method: Optional[str] = None
    raw_text_char_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DBResumeDetailResponse(BaseModel):
    """
    Full detail view including complete Pydantic Resume domain object and storage metadata.
    """
    id: str
    user_id: Optional[str] = None
    original_filename: str
    file_identifier: Optional[str] = None
    processing_status: str
    extraction_method: Optional[str] = None
    raw_text_char_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    resume: Resume


class DBStatsResponse(BaseModel):
    """
    Database health and table metrics.
    """
    status: str
    database_name: str
    total_resumes: int
    total_skills: int
    total_users: int
