"""
Pydantic schemas for resume upload and processing.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    """
    Schema for successful resume upload response.
    """
    success: bool = Field(True, description="Indicates whether the upload succeeded")
    filename: str = Field(..., description="Unique secure temporary filename generated on server")
    original_filename: str = Field(..., description="Sanitized original filename")
    size_bytes: int = Field(..., description="Size of uploaded file in bytes")
    message: str = Field("Resume uploaded successfully", description="Status message")
    uploaded_at: str = Field(..., description="ISO 8601 timestamp of upload")


class UploadErrorResponse(BaseModel):
    """
    Standard schema for upload failure responses.
    """
    success: bool = Field(False, description="Failure indicator")
    error: str = Field(..., description="Summary error category")
    detail: Optional[str] = Field(None, description="Detailed explanatory message")


class ResumeExtractTextResponse(BaseModel):
    """
    Schema for PDF text extraction response (Phase 3, 4 & 5).
    """
    resume_id: str = Field(..., description="Identifier of the processed resume document")
    text: str = Field(..., description="Extracted clean plain text with preserved line breaks")
    page_count: int = Field(..., description="Total number of pages in the PDF")
    extraction_method: str = Field(
        "pdf_text",
        description="Method used for extraction: 'pdf_text', 'ocr', or 'mixed'"
    )
    original_char_count: Optional[int] = Field(None, description="Character count before preprocessing")
    cleaned_char_count: Optional[int] = Field(None, description="Character count after preprocessing")
    transformations_applied: Optional[List[str]] = Field(None, description="List of text normalization steps applied")


class ResumeSectionsResponse(BaseModel):
    """
    Schema for resume section segmentation response (Phase 6).
    """
    resume_id: str = Field(..., description="Identifier of the processed resume document")
    sections: Dict[str, str] = Field(..., description="Logical canonical sections: summary, education, skills, experience, projects, etc.")
    detected_sections_list: List[str] = Field(default_factory=list, description="Ordered list of detected sections")
    raw_headings: Dict[str, str] = Field(default_factory=dict, description="Original heading text found in the document")
    unclassified: str = Field("", description="Unclassified text stored separately")


class ResumeNLPEntitiesResponse(BaseModel):
    """
    Schema for deterministic spaCy NLP entity extraction response (Phase 8).
    """
    resume_id: str = Field(..., description="Identifier of the processed resume document")
    persons: List[str] = Field(default_factory=list, description="Extracted candidate and personal names")
    organizations: List[str] = Field(default_factory=list, description="Detected companies, universities, and institutions")
    locations: List[str] = Field(default_factory=list, description="Detected cities, states, and countries (GPE/LOC)")
    dates: List[str] = Field(default_factory=list, description="Detected dates, employment durations, and years")
    emails: List[str] = Field(default_factory=list, description="Extracted email addresses")
    urls: List[str] = Field(default_factory=list, description="Extracted portfolio, LinkedIn, and GitHub links")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Raw entity spans with character offsets")


class ResumeParseResponse(BaseModel):
    """
    Schema for completed AI structured resume parsing response (Phase 9).
    """
    resume_id: str = Field(..., description="Identifier of the processed resume document")
    resume: Any = Field(..., description="Canonical structured Resume model")
    raw_text_char_count: int = Field(..., description="Total characters in cleaned resume text")
    sections_detected: List[str] = Field(default_factory=list, description="Logical sections identified in the document")
    nlp_entities_count: Dict[str, int] = Field(default_factory=dict, description="Counts of detected entities by category")
    llm_provider: str = Field(..., description="LLM provider used: 'gemini', 'openai', or 'mock'")
    llm_model: str = Field(..., description="Underlying model name")
    repair_attempts: int = Field(0, description="Number of schema repair retries triggered")
    parsing_duration_ms: float = Field(..., description="Pipeline execution duration in milliseconds")


class DirectParseRequest(BaseModel):
    """
    Payload schema for directly parsing raw resume text (Phase 9).
    """
    text: str = Field(..., min_length=10, description="Cleaned or raw resume text content")
    sections: Optional[Dict[str, str]] = Field(None, description="Optional pre-segmented sections mapping")
    provider: Optional[str] = Field(None, description="Optional override for LLM provider")




