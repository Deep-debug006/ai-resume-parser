"""
Pydantic Schemas for Phase 20: User History.
Ensures lightweight summary models for list queries and comprehensive schemas for detail views.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class PaginatedMeta(BaseModel):
    """Metadata envelope for paginated collections."""
    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="Total count of matching records")
    page: int = Field(..., description="Current 1-indexed page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages calculated")


class ResumeHistorySummary(BaseModel):
    """Lightweight summary of a resume document for history listings."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    original_filename: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    processing_status: str
    extraction_method: Optional[str] = "unified"
    raw_text_char_count: int = 0
    skills_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobHistorySummary(BaseModel):
    """Lightweight summary of a job description for history listings."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    char_count: int = 0
    required_skills_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AnalysisHistorySummary(BaseModel):
    """Lightweight summary of an analysis record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    resume_id: Optional[str] = None
    candidate_name: Optional[str] = None
    resume_filename: Optional[str] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    analysis_type: str
    score: Optional[float] = None
    match_rate: Optional[float] = None
    summary: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AnalysisHistoryDetail(BaseModel):
    """Comprehensive detail payload for an analysis history record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    resume_id: Optional[str] = None
    candidate_name: Optional[str] = None
    resume_filename: Optional[str] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    analysis_type: str
    score: Optional[float] = None
    match_rate: Optional[float] = None
    summary: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AnalysisCreateRequest(BaseModel):
    """Payload to record an analysis into history."""
    resume_id: Optional[str] = None
    candidate_name: Optional[str] = None
    resume_filename: Optional[str] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    analysis_type: str = "job_match"
    score: Optional[float] = None
    match_rate: Optional[float] = None
    summary: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class PaginatedResumesResponse(BaseModel):
    """Paginated resumes response."""
    items: List[ResumeHistorySummary]
    meta: PaginatedMeta


class PaginatedJobsResponse(BaseModel):
    """Paginated job descriptions response."""
    items: List[JobHistorySummary]
    meta: PaginatedMeta


class PaginatedAnalysesResponse(BaseModel):
    """Paginated analyses response."""
    items: List[AnalysisHistorySummary]
    meta: PaginatedMeta


class HistoryOverviewResponse(BaseModel):
    """Lightweight aggregate counts for dashboard cards."""
    total_resumes: int
    total_jobs: int
    total_analyses: int
