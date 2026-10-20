"""
Schemas for Phase 12: Complete Resume Processing Pipeline.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.parsed_resume import Resume


class ResumeProcessResponse(BaseModel):
    """
    Response schema returned by POST /api/resumes/process orchestrator.
    Guarantees returning:
    - resume_id
    - processing_status ('uploaded', 'processing', 'completed', 'failed')
    - structured resume data
    """
    resume_id: str = Field(..., description="PostgreSQL unique resume identifier")
    processing_status: str = Field(
        ...,
        description="Current processing status: uploaded, processing, completed, or failed",
    )
    resume: Optional[Resume] = Field(
        None,
        description="Structured, validated, normalized Resume domain model",
    )
    structured_resume_data: Optional[Resume] = Field(
        None,
        description="Alias for structured resume data matching specification",
    )
    original_filename: str = Field(..., description="Original name of the uploaded document")
    extraction_method: Optional[str] = Field(
        None,
        description="Text extraction technique utilized (pymupdf_native, tesseract_ocr, or hybrid)",
    )
    raw_text_char_count: Optional[int] = Field(0, description="Cleaned character count of extracted text")
    sections_detected: Optional[List[str]] = Field(default_factory=list, description="List of recognized sections")
    nlp_entities_count: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        description="Counts of deterministic NLP entities extracted",
    )
    llm_provider: Optional[str] = Field(None, description="Active LLM provider used")
    llm_model: Optional[str] = Field(None, description="Active LLM model used")
    repair_attempts: Optional[int] = Field(0, description="Number of schema repair attempts required")
    processing_duration_ms: Optional[float] = Field(0.0, description="End-to-end pipeline latency in ms")
    error: Optional[str] = Field(None, description="Detailed error description if processing status is failed")
    created_at: Optional[str] = Field(None, description="ISO timestamp of record creation")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of record update")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ResumeStatusResponse(BaseModel):
    """
    Status checking response schema.
    """
    resume_id: str
    original_filename: str
    processing_status: str
    extraction_method: Optional[str] = None
    raw_text_char_count: Optional[int] = 0
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
