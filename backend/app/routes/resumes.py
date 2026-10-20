"""
Routes for resume document handling and uploads.
"""
import os
from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Form
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.resume import (
    ResumeUploadResponse,
    UploadErrorResponse,
    ResumeExtractTextResponse,
    ResumeSectionsResponse,
    ResumeNLPEntitiesResponse,
    ResumeParseResponse,
    DirectParseRequest,
)
from backend.app.schemas.resume_process import (
    ResumeProcessResponse,
    ResumeStatusResponse,
)
from backend.app.schemas.resume_analysis import (
    ResumeAnalysisResponse,
    ResumeAnalysisRequest,
)
from backend.app.services.resume_analysis_service import resume_analysis_service
from backend.app.schemas.parsed_resume import Resume
from backend.app.services.storage_service import storage_service, FileValidationError
from backend.app.services.resume_text_extractor import extract_resume_text as unified_extract_resume_text
from backend.app.services.section_detector import detect_resume_sections, CANONICAL_SECTIONS
from backend.app.services.nlp_service import extract_resume_nlp_entities
from backend.app.services.resume_parser_service import resume_parser_service
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator
from backend.app.services.resume_db_service import resume_db_service
from backend.app.models.resume_models import ResumeModel, UserModel
from backend.app.core.auth_dependency import get_current_user_optional
from backend.app.services.llm_service import (
    LLMService,
    LLMError,
    LLMProviderError,
    LLMValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Resume Document",
    description="Uploads and securely validates a PDF resume document without permanent DB persistence.",
    responses={
        400: {"model": UploadErrorResponse, "description": "Invalid file, unsupported type, empty, or corrupt PDF"},
        413: {"model": UploadErrorResponse, "description": "File exceeds maximum permitted size"},
        500: {"model": UploadErrorResponse, "description": "Unexpected internal server error during upload processing"},
    },
)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    """
    Handle secure resume PDF upload:
    - Verifies file presence
    - Checks file extension (.pdf)
    - Validates MIME type
    - Reads content and inspects binary size
    - Validates PDF structure (%PDF- header and %%EOF trailer)
    - Writes to safe temporary storage under an unpredictable unique identifier
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided or filename is missing.",
        )

    # 1. Validate filename extension and declared MIME
    try:
        clean_filename = storage_service.validate_filename_and_mime(
            filename=file.filename,
            content_type=file.content_type,
        )
    except FileValidationError as e:
        logger.warning("File validation failed for filename '%s': %s", file.filename, e.message)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )

    # 2. Read file contents into memory for deep byte inspection
    try:
        content = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file stream: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read the uploaded file stream. Please try again.",
        )

    # 3. Validate content bytes (empty, size limit, %PDF- header, %%EOF trailer)
    try:
        storage_service.validate_file_content(content)
    except FileValidationError as e:
        logger.warning("Content inspection failed for '%s': %s", clean_filename, e.message)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except Exception as e:
        logger.error("Unexpected error validating file content: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error validating file contents.",
        )

    # 4. Save to temporary storage with generated unique safe filename
    try:
        safe_filename, _ = storage_service.save_temporarily(content, clean_filename)
    except Exception as e:
        logger.error("Failed to store uploaded file temporarily: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file to temporary storage.",
        )

    uploaded_timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Successfully uploaded resume: original='%s', saved_as='%s', size=%d bytes",
        clean_filename,
        safe_filename,
        len(content),
    )

    return ResumeUploadResponse(
        success=True,
        filename=safe_filename,
        original_filename=clean_filename,
        size_bytes=len(content),
        message="Resume uploaded successfully",
        uploaded_at=uploaded_timestamp,
    )


@router.get(
    "/schema",
    summary="Get Structured Resume Schema",
    description="Returns the canonical JSON schema for the Resume Pydantic model (Phase 7).",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def get_resume_schema() -> Dict[str, Any]:
    """
    Returns the complete OpenAPI/JSON Schema specification for the canonical Resume schema.
    """
    return Resume.model_json_schema()


@router.post(
    "/{resume_id}/extract-text",
    response_model=ResumeExtractTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Text from Resume PDF",
    description="Safely extracts clean plain text from a previously uploaded PDF using PyMuPDF.",
    responses={
        400: {"model": UploadErrorResponse, "description": "Malformed or unreadable PDF document"},
        404: {"model": UploadErrorResponse, "description": "Resume identifier not found in temporary storage"},
        500: {"model": UploadErrorResponse, "description": "Unexpected server error during text extraction"},
    },
)
async def extract_resume_text(resume_id: str) -> ResumeExtractTextResponse:
    """
    Extracts text from an uploaded resume using PyMuPDF:
    - Resolves resume file from secure temporary storage
    - Iterates pages safely and extracts clean readable text
    - Preserves logical line breaks and lists
    - Handles malformed and empty PDFs gracefully
    """
    if not resume_id or not resume_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume ID parameter cannot be empty.",
        )

    # Sanitize identifier to prevent directory traversal
    try:
        target_path = storage_service.get_safe_path(resume_id)
        filename = target_path.name
        clean_id = filename[:-4] if filename.endswith(".pdf") else filename
    except FileValidationError as fve:
        raise HTTPException(status_code=fve.status_code, detail=fve.message)

    if not target_path.exists() or not target_path.is_file():
        logger.warning("Resume file not found for extraction: '%s'", filename)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume '{resume_id}' was not found in temporary storage. Please upload the file first.",
        )

    try:
        extraction_result = unified_extract_resume_text(target_path)
    except Exception as e:
        err_msg = str(e)
        if "not exist" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        elif "malformed" in err_msg.lower() or "corrupt" in err_msg.lower() or "format" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
        logger.error("Unexpected error during text extraction on '%s': %s", filename, err_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while parsing the PDF: {err_msg}",
        )

    logger.info(
        "Extracted text from '%s' (%d pages, %d chars, method=%s)",
        filename,
        extraction_result.page_count,
        len(extraction_result.text),
        extraction_result.extraction_method,
    )

    return ResumeExtractTextResponse(
        resume_id=clean_id,
        text=extraction_result.text,
        page_count=extraction_result.page_count,
        extraction_method=extraction_result.extraction_method,
        original_char_count=extraction_result.original_char_count,
        cleaned_char_count=extraction_result.cleaned_char_count,
        transformations_applied=extraction_result.transformations_applied,
    )


@router.post(
    "/{resume_id}/sections",
    response_model=ResumeSectionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect and Segment Resume Sections",
    description="Deterministic segmentation of cleaned resume text into canonical logical sections.",
    responses={
        200: {"model": ResumeSectionsResponse, "description": "Structured sections dictionary"},
        400: {"model": UploadErrorResponse, "description": "Invalid resume ID or corrupt document"},
        404: {"model": UploadErrorResponse, "description": "Resume file not found"},
        500: {"model": UploadErrorResponse, "description": "Internal processing failure"},
    },
)
async def detect_sections_endpoint(resume_id: str) -> ResumeSectionsResponse:
    """
    Extracts, preprocesses, and segments resume text into canonical sections.
    """
    if not resume_id or not resume_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume ID parameter cannot be empty.",
        )

    try:
        target_path = storage_service.get_safe_path(resume_id)
        filename = target_path.name
        clean_id = filename[:-4] if filename.endswith(".pdf") else filename
    except FileValidationError as fve:
        raise HTTPException(status_code=fve.status_code, detail=fve.message)

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume '{resume_id}' was not found in temporary storage.",
        )

    try:
        extraction_result = unified_extract_resume_text(target_path)
    except Exception as e:
        err_msg = str(e)
        if "not exist" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        elif "malformed" in err_msg.lower() or "corrupt" in err_msg.lower() or "format" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract resume text: {err_msg}",
        )

    detection_result = detect_resume_sections(extraction_result.text)

    # Convert canonical sections into structured dictionary, excluding unclassified
    sections_dict = {
        s: getattr(detection_result, s)
        for s in CANONICAL_SECTIONS
        if s != "unclassified" and getattr(detection_result, s)
    }

    logger.info(
        "Detected %d sections in '%s': %s",
        len(sections_dict),
        filename,
        list(sections_dict.keys()),
    )

    return ResumeSectionsResponse(
        resume_id=clean_id,
        sections=sections_dict,
        detected_sections_list=detection_result.detected_sections_list,
        raw_headings=detection_result.raw_headings,
        unclassified=detection_result.unclassified,
    )


@router.post(
    "/{resume_id}/entities",
    response_model=ResumeNLPEntitiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract NLP Entities with spaCy",
    description="Deterministic NLP entity extraction using spaCy (Phase 8): PERSON, ORG, GPE, DATE, EMAIL, URL.",
    responses={
        200: {"model": ResumeNLPEntitiesResponse, "description": "Structured NLP entities extraction result"},
        400: {"model": UploadErrorResponse, "description": "Invalid resume ID or corrupt document"},
        404: {"model": UploadErrorResponse, "description": "Resume file not found"},
        500: {"model": UploadErrorResponse, "description": "Internal NLP processing error"},
    },
)
async def extract_nlp_entities_endpoint(resume_id: str) -> ResumeNLPEntitiesResponse:
    """
    Runs deterministic spaCy NLP entity extraction on the cleaned resume text.
    """
    if not resume_id or not resume_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume ID parameter cannot be empty.",
        )

    try:
        target_path = storage_service.get_safe_path(resume_id)
        filename = target_path.name
        clean_id = filename[:-4] if filename.endswith(".pdf") else filename
    except FileValidationError as fve:
        raise HTTPException(status_code=fve.status_code, detail=fve.message)

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume '{resume_id}' was not found in temporary storage.",
        )

    try:
        extraction_result = unified_extract_resume_text(target_path)
    except Exception as e:
        err_msg = str(e)
        if "not exist" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        elif "malformed" in err_msg.lower() or "corrupt" in err_msg.lower() or "format" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text for NLP: {err_msg}",
        )

    nlp_result = extract_resume_nlp_entities(extraction_result.text)

    logger.info(
        "NLP extracted entities for '%s': persons=%d, orgs=%d, locs=%d, dates=%d, emails=%d, urls=%d",
        filename,
        len(nlp_result.persons),
        len(nlp_result.organizations),
        len(nlp_result.locations),
        len(nlp_result.dates),
        len(nlp_result.emails),
        len(nlp_result.urls),
    )

    return ResumeNLPEntitiesResponse(
        resume_id=clean_id,
        persons=nlp_result.persons,
        organizations=nlp_result.organizations,
        locations=nlp_result.locations,
        dates=nlp_result.dates,
        emails=nlp_result.emails,
        urls=nlp_result.urls,
        entities=nlp_result.entities,
    )


@router.post(
    "/{resume_id}/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Structured Resume Parsing",
    description="Executes end-to-end AI structured resume parsing pipeline with Pydantic validation and anti-hallucination guarantees (Phase 9).",
    responses={
        200: {"model": ResumeParseResponse, "description": "Structured Resume domain model successfully generated"},
        400: {"model": UploadErrorResponse, "description": "Invalid input or document text"},
        404: {"model": UploadErrorResponse, "description": "Resume ID not found"},
        422: {"model": UploadErrorResponse, "description": "Schema validation failure after repair retries"},
        502: {"model": UploadErrorResponse, "description": "Upstream LLM API error or quota exhaustion"},
        500: {"model": UploadErrorResponse, "description": "Internal parsing failure"},
    },
)
async def parse_resume_endpoint(resume_id: str) -> ResumeParseResponse:
    """
    Executes Phase 9 full pipeline for an uploaded resume:
    PDF -> Text -> Clean -> Sections -> NLP -> LLM -> Pydantic Validation -> Structured Resume.
    """
    if not resume_id or not resume_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume ID parameter cannot be empty.",
        )

    try:
        result = await resume_parser_service.parse_resume_document(resume_id)
    except FileNotFoundError as fnf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(fnf),
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except LLMValidationError as lve:
        logger.error("Resume validation failed for '%s': %s", resume_id, str(lve))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Schema validation failed: {str(lve)}. Specific errors: {lve.validation_errors}",
        )
    except LLMProviderError as lpe:
        logger.error("LLM provider failure for '%s': %s", resume_id, str(lpe))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Provider error: {str(lpe)}",
        )
    except Exception as e:
        logger.error("Unexpected error during structured parsing for '%s': %s", resume_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during resume parsing: {str(e)}",
        )

    return ResumeParseResponse(
        resume_id=result.resume_id,
        resume=result.resume,
        raw_text_char_count=result.raw_text_char_count,
        sections_detected=result.sections_detected,
        nlp_entities_count=result.nlp_entities_count,
        llm_provider=result.llm_provider,
        llm_model=result.llm_model,
        repair_attempts=result.repair_attempts,
        parsing_duration_ms=result.parsing_duration_ms,
    )


@router.post(
    "/parse-direct",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct Text Structured Parsing",
    description="Parses arbitrary resume text into a structured Resume object without prior file upload (Phase 9).",
    responses={
        200: {"model": ResumeParseResponse, "description": "Successfully parsed resume"},
        400: {"model": UploadErrorResponse, "description": "Empty or invalid resume text"},
        422: {"model": UploadErrorResponse, "description": "Schema validation failed"},
        502: {"model": UploadErrorResponse, "description": "LLM provider failure"},
        500: {"model": UploadErrorResponse, "description": "Unexpected error"},
    },
)
async def parse_direct_endpoint(payload: DirectParseRequest) -> ResumeParseResponse:
    """
    Parses resume text directly using the configured LLM provider and validation pipeline.
    """
    custom_service = None
    if payload.provider:
        try:
            custom_provider = LLMService.create_provider(payload.provider)
            custom_service = LLMService(provider=custom_provider)
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve),
            )

    try:
        result = await resume_parser_service.parse_direct_text(
            text=payload.text,
            sections=payload.sections,
            custom_llm_service=custom_service,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except LLMValidationError as lve:
        logger.error("Direct resume validation failed: %s", str(lve))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Schema validation failed: {str(lve)}. Specific errors: {lve.validation_errors}",
        )
    except LLMProviderError as lpe:
        logger.error("LLM provider failure during direct parsing: %s", str(lpe))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Provider error: {str(lpe)}",
        )
    except Exception as e:
        logger.error("Unexpected error during direct parsing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during direct parsing: {str(e)}",
        )

    return ResumeParseResponse(
        resume_id=result.resume_id,
        resume=result.resume,
        raw_text_char_count=result.raw_text_char_count,
        sections_detected=result.sections_detected,
        nlp_entities_count=result.nlp_entities_count,
        llm_provider=result.llm_provider,
        llm_model=result.llm_model,
        repair_attempts=result.repair_attempts,
        parsing_duration_ms=result.parsing_duration_ms,
    )


@router.post(
    "/process",
    response_model=ResumeProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete Resume Processing Pipeline",
    description="End-to-end resume pipeline: Upload -> Extract Text -> OCR Fallback -> Clean -> Sections -> NLP -> LLM -> Pydantic Validation -> Skill Normalization -> PostgreSQL Persistence (Phase 12).",
)
async def process_resume_endpoint(
    file: Optional[UploadFile] = File(None),
    file_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> ResumeProcessResponse:
    """
    Orchestrates the entire Phase 12 resume pipeline.
    Tracks status through: 'uploaded' -> 'processing' -> 'completed' or 'failed'.
    Returns resume_id, processing_status, and structured resume data.
    """
    if file is None and (not file_id or not file_id.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a PDF 'file' upload or an existing 'file_id' must be provided.",
        )

    if file is not None:
        result = await pipeline_orchestrator.process_file(
            db=db,
            file=file,
            user_id=user_id,
        )
        return result.to_response()

    # Process from previously uploaded file_id
    try:
        target_path = storage_service.get_safe_path(file_id)
        filename = target_path.name
    except FileValidationError as fve:
        raise HTTPException(status_code=fve.status_code, detail=fve.message)

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume file '{file_id}' was not found in storage.",
        )

    result = await pipeline_orchestrator.process_file(
        db=db,
        file_path=target_path,
        original_filename=filename,
        user_id=user_id,
    )
    return result.to_response()


@router.get(
    "/{resume_id}/status",
    response_model=ResumeStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resume Processing Status",
    description="Fetches current processing status (uploaded, processing, completed, failed) of a resume.",
)
def get_resume_processing_status(
    resume_id: str,
    db: Session = Depends(get_db),
) -> ResumeStatusResponse:
    """
    Retrieves the lifecycle processing status of a resume from the database.
    """
    record = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' was not found.",
        )

    return ResumeStatusResponse(
        resume_id=record.id,
        original_filename=record.original_filename,
        processing_status=record.processing_status,
        extraction_method=record.extraction_method,
        raw_text_char_count=record.raw_text_char_count,
        error=record.error_message,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Resume Analysis (Phase 17)",
    description="Evaluates resume quality across clarity, completeness, bullet-point quality, measurable achievements, skill organization, project descriptions, formatting, and missing common information.",
)
async def analyze_resume_endpoint(
    request: ResumeAnalysisRequest,
    db: Session = Depends(get_db),
) -> ResumeAnalysisResponse:
    """
    Analyzes resume quality against standard professional criteria:
    - Accepts 'text', 'resume' dict, or 'resume_id' (from PostgreSQL DB)
    - Returns structured evaluation with strengths, areas_for_improvement, and suggestions
    - Strictly avoids fake accomplishments or invented facts
    - Keeps factual extraction separate from subjective recommendations
    """
    target_resume: Optional[Resume] = None
    target_text: Optional[str] = request.text

    # 1. If resume_id provided, retrieve from database
    if request.resume_id:
        try:
            persisted = resume_db_service.get_resume(db, request.resume_id)
            if not persisted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume with ID '{request.resume_id}' not found in database.",
                )
            target_resume = persisted.structured_resume
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to retrieve resume '%s' from DB: %s", request.resume_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving resume: {str(e)}",
            )

    # 2. If structured resume dict provided
    elif request.resume:
        try:
            target_resume = Resume.model_validate(request.resume)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume structure: {str(e)}",
            )

    # 3. If only raw text is provided
    elif target_text and target_text.strip():
        # Valid text payload
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either 'resume_id', structured 'resume', or raw 'text' for analysis.",
        )

    try:
        result = await resume_analysis_service.analyze_resume(
            resume=target_resume,
            raw_text=target_text,
        )
        return result
    except Exception as e:
        logger.error("Error executing resume quality analysis: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume analysis failed: {str(e)}",
        )


@router.post(
    "/{resume_id}/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Saved Resume by ID (Phase 17)",
    description="Evaluates quality criteria for a persisted resume document stored in PostgreSQL.",
)
async def analyze_saved_resume_endpoint(
    resume_id: str,
    db: Session = Depends(get_db),
) -> ResumeAnalysisResponse:
    """
    Convenience path endpoint to analyze a database resume by its UUID.
    """
    req = ResumeAnalysisRequest(resume_id=resume_id)
    return await analyze_resume_endpoint(request=req, db=db)





