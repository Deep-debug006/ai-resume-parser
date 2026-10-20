"""
Pipeline Orchestrator Service (Phase 12: Complete Resume Processing Pipeline).
Orchestrates the entire end-to-end workflow:
Upload PDF
  ↓
Extract text (PyMuPDF)
  ↓
OCR fallback if necessary (Tesseract)
  ↓
Clean text (TextCleaner)
  ↓
Detect sections (SectionDetector)
  ↓
NLP entity extraction (spaCy)
  ↓
LLM structured extraction (LLMService)
  ↓
Pydantic validation & controlled repair loop
  ↓
Skill normalization (SkillNormalizer)
  ↓
PostgreSQL persistence (ResumeDBService / ResumeRepository)

Tracks processing status lifecycle:
- uploaded
- processing
- completed
- failed
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.schemas.parsed_resume import Resume
from backend.app.schemas.resume_process import ResumeProcessResponse
from backend.app.services.storage_service import storage_service, FileValidationError
from backend.app.services.resume_text_extractor import extract_resume_text as unified_extract_resume_text
from backend.app.services.text_cleaner import clean_resume_text
from backend.app.services.section_detector import detect_resume_sections, CANONICAL_SECTIONS
from backend.app.services.nlp_service import extract_resume_nlp_entities
from backend.app.services.resume_parser_service import (
    resume_parser_service,
    RESUME_PARSER_SYSTEM_INSTRUCTION,
)
from backend.app.services.llm_service import (
    LLMService,
    llm_service as default_llm_service,
    LLMError,
    LLMValidationError,
    LLMProviderError,
)
from backend.app.services.skill_normalizer import skill_normalizer
from backend.app.services.resume_db_service import resume_db_service

logger = logging.getLogger(__name__)


@dataclass
class ResumeProcessResult:
    """
    Internal container for completed or failed pipeline execution.
    """
    resume_id: str
    processing_status: str  # uploaded, processing, completed, failed
    resume: Optional[Resume] = None
    original_filename: str = "unknown.pdf"
    extraction_method: Optional[str] = None
    raw_text_char_count: int = 0
    sections_detected: Optional[List[str]] = None
    nlp_entities_count: Optional[Dict[str, int]] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    repair_attempts: int = 0
    processing_duration_ms: float = 0.0
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_response(self) -> ResumeProcessResponse:
        """Converts to API response schema."""
        return ResumeProcessResponse(
            resume_id=self.resume_id,
            processing_status=self.processing_status,
            resume=self.resume,
            structured_resume_data=self.resume,
            original_filename=self.original_filename,
            extraction_method=self.extraction_method,
            raw_text_char_count=self.raw_text_char_count,
            sections_detected=self.sections_detected or [],
            nlp_entities_count=self.nlp_entities_count or {},
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            repair_attempts=self.repair_attempts,
            processing_duration_ms=round(self.processing_duration_ms, 2),
            error=self.error,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class PipelineOrchestrator:
    """
    Service coordinating all modular components into a resilient, tracked pipeline.
    """

    def __init__(self, llm_service_instance: Optional[LLMService] = None):
        self._llm_service = llm_service_instance or default_llm_service

    async def process_file(
        self,
        db: Session,
        file: Optional[UploadFile] = None,
        file_path: Optional[Path] = None,
        original_filename: Optional[str] = None,
        user_id: Optional[str] = None,
        custom_llm_service: Optional[LLMService] = None,
    ) -> ResumeProcessResult:
        """
        Executes complete pipeline:
        1. Intake / Upload & Validation (status: 'uploaded')
        2. Set status: 'processing'
        3. Text extraction & OCR fallback
        4. Text cleaning
        5. Section detection
        6. NLP entity extraction
        7. LLM structured extraction & Pydantic validation loop
        8. Skill normalization & taxonomy deduplication
        9. PostgreSQL persistence (status: 'completed')
        Failure at any stage marks DB record as 'failed' and returns failure details.
        """
        start_time = time.perf_counter()
        resume_record = None
        target_path: Optional[Path] = None
        target_original_filename = original_filename or (file.filename if file else "unknown.pdf")

        # =========================================================================
        # STAGE 1: Upload / File Intake & Validation
        # =========================================================================
        try:
            if file is not None:
                # 1a. Validate filename and MIME
                clean_name = storage_service.validate_filename_and_mime(
                    filename=file.filename or "resume.pdf",
                    content_type=file.content_type,
                )
                target_original_filename = clean_name

                # 1b. Read bytes
                content = await file.read()

                # 1c. Deep byte validation (%PDF header, %%EOF trailer, size limit)
                storage_service.validate_file_content(content)

                # 1d. Save temporarily to disk
                safe_filename, target_path = storage_service.save_temporarily(content, clean_name)

                # 1e. Initialize DB record with status: 'uploaded'
                resume_record = resume_db_service.create_initial_record(
                    db=db,
                    original_filename=clean_name,
                    file_identifier=safe_filename,
                    user_id=user_id,
                    processing_status="uploaded",
                )
            elif file_path is not None:
                target_path = Path(file_path)
                if not target_path.exists() or not target_path.is_file():
                    raise FileNotFoundError(f"File not found at path: {file_path}")

                target_original_filename = original_filename or target_path.name
                resume_record = resume_db_service.create_initial_record(
                    db=db,
                    original_filename=target_original_filename,
                    file_identifier=target_path.name,
                    user_id=user_id,
                    processing_status="uploaded",
                )
            else:
                raise ValueError("Neither file stream nor file_path was provided for processing.")

        except FileValidationError as fve:
            logger.warning("Upload validation failed for '%s': %s", target_original_filename, fve.message)
            # Create a tracked failure record if possible
            if resume_record is None:
                try:
                    resume_record = resume_db_service.create_initial_record(
                        db=db,
                        original_filename=target_original_filename,
                        processing_status="failed",
                    )
                    resume_db_service.update_status(db, resume_record.id, "failed", error_message=fve.message)
                except Exception:
                    pass

            duration_ms = (time.perf_counter() - start_time) * 1000
            return ResumeProcessResult(
                resume_id=resume_record.id if resume_record else "upload-failed",
                processing_status="failed",
                original_filename=target_original_filename,
                error=fve.message,
                processing_duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error("Intake stage failure for '%s': %s", target_original_filename, str(e))
            duration_ms = (time.perf_counter() - start_time) * 1000
            if resume_record is None:
                try:
                    resume_record = resume_db_service.create_initial_record(
                        db=db,
                        original_filename=target_original_filename,
                        processing_status="failed",
                    )
                    resume_db_service.update_status(db, resume_record.id, "failed", error_message=str(e))
                except Exception:
                    pass

            return ResumeProcessResult(
                resume_id=resume_record.id if resume_record else "intake-failed",
                processing_status="failed",
                original_filename=target_original_filename,
                error=str(e),
                processing_duration_ms=duration_ms,
            )

        resume_id = resume_record.id

        # =========================================================================
        # STAGE 2: Transition Status to 'processing'
        # =========================================================================
        try:
            resume_db_service.update_status(db, resume_id, processing_status="processing")
        except Exception as e:
            logger.error("Failed to update status to 'processing' for resume '%s': %s", resume_id, str(e))

        # =========================================================================
        # STAGES 3 TO 9: Extraction -> Clean -> Sections -> NLP -> LLM -> Skills -> DB
        # =========================================================================
        try:
            # Step 3: Text extraction & OCR fallback
            try:
                extraction_res = unified_extract_resume_text(target_path)
            except Exception as e:
                err_msg = f"Text extraction failed: {str(e)}"
                logger.error("Stage 3 failure for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    original_filename=target_original_filename,
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )

            # Step 4: Text cleaning
            try:
                cleaning_res = clean_resume_text(extraction_res.text)
                cleaned_text = cleaning_res.cleaned_text
            except Exception as e:
                err_msg = f"Text cleaning failed: {str(e)}"
                logger.error("Stage 4 failure for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    original_filename=target_original_filename,
                    extraction_method=extraction_res.extraction_method,
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )

            # Step 5: Detect sections
            try:
                section_res = detect_resume_sections(cleaned_text)
                sections_dict = {
                    s: getattr(section_res, s)
                    for s in CANONICAL_SECTIONS
                    if s != "unclassified" and getattr(section_res, s)
                }
            except Exception as e:
                err_msg = f"Section detection failed: {str(e)}"
                logger.error("Stage 5 failure for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    original_filename=target_original_filename,
                    extraction_method=extraction_res.extraction_method,
                    raw_text_char_count=len(cleaned_text),
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )

            # Step 6: Deterministic NLP entity extraction
            try:
                nlp_res = extract_resume_nlp_entities(cleaned_text)
            except Exception as e:
                logger.warning("Stage 6 NLP extraction warning for resume '%s': %s (proceeding)", resume_id, str(e))
                nlp_res = None

            # Step 7: Build grounded prompt
            prompt = resume_parser_service.build_prompt(
                cleaned_text=cleaned_text,
                sections=sections_dict,
                nlp_result=nlp_res,
            )

            # Step 8: LLM structured extraction & Pydantic validation with repair loop
            service = custom_llm_service or self._llm_service
            try:
                resume_obj, repair_attempts = await service.generate_structured(
                    prompt=prompt,
                    system_instruction=RESUME_PARSER_SYSTEM_INSTRUCTION,
                    schema_class=Resume,
                )
            except LLMValidationError as lve:
                err_msg = f"LLM schema validation failed after retries: {str(lve)}"
                logger.error("Stage 8 validation error for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    original_filename=target_original_filename,
                    extraction_method=extraction_res.extraction_method,
                    raw_text_char_count=len(cleaned_text),
                    sections_detected=section_res.detected_sections_list,
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )
            except LLMProviderError as lpe:
                err_msg = f"LLM Provider error: {str(lpe)}"
                logger.error("Stage 8 provider error for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    original_filename=target_original_filename,
                    extraction_method=extraction_res.extraction_method,
                    raw_text_char_count=len(cleaned_text),
                    sections_detected=section_res.detected_sections_list,
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )
            except Exception as e:
                err_msg = f"LLM structured extraction failed: {str(e)}"
                logger.error("Stage 8 unexpected error for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    original_filename=target_original_filename,
                    extraction_method=extraction_res.extraction_method,
                    raw_text_char_count=len(cleaned_text),
                    sections_detected=section_res.detected_sections_list,
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )

            # Step 9: Skill Normalization & Taxonomy Deduplication
            try:
                resume_obj = skill_normalizer.normalize_resume(resume_obj)
            except Exception as e:
                logger.warning("Stage 9 skill normalization warning for '%s': %s", resume_id, str(e))

            # Step 10: PostgreSQL persistence (status: 'completed')
            try:
                orm_saved, pyd_saved = resume_db_service.save_completed_pipeline(
                    db=db,
                    resume_id=resume_id,
                    resume=resume_obj,
                    extraction_method=extraction_res.extraction_method,
                    raw_text_char_count=len(cleaned_text),
                )
            except Exception as e:
                err_msg = f"Database persistence failed: {str(e)}"
                logger.error("Stage 10 persistence failure for resume '%s': %s", resume_id, err_msg)
                resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ResumeProcessResult(
                    resume_id=resume_id,
                    processing_status="failed",
                    resume=resume_obj,
                    original_filename=target_original_filename,
                    extraction_method=extraction_res.extraction_method,
                    raw_text_char_count=len(cleaned_text),
                    sections_detected=section_res.detected_sections_list,
                    error=err_msg,
                    processing_duration_ms=duration_ms,
                )

            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Resume pipeline completed successfully: id='%s', file='%s', chars=%d, duration=%.2fms",
                resume_id,
                target_original_filename,
                len(cleaned_text),
                duration_ms,
            )

            nlp_counts = {
                "persons": len(nlp_res.persons) if nlp_res else 0,
                "organizations": len(nlp_res.organizations) if nlp_res else 0,
                "locations": len(nlp_res.locations) if nlp_res else 0,
                "dates": len(nlp_res.dates) if nlp_res else 0,
                "emails": len(nlp_res.emails) if nlp_res else 0,
                "urls": len(nlp_res.urls) if nlp_res else 0,
            }

            return ResumeProcessResult(
                resume_id=resume_id,
                processing_status="completed",
                resume=pyd_saved,
                original_filename=target_original_filename,
                extraction_method=extraction_res.extraction_method,
                raw_text_char_count=len(cleaned_text),
                sections_detected=section_res.detected_sections_list,
                nlp_entities_count=nlp_counts,
                llm_provider=service.provider.provider_name,
                llm_model=service.provider.model_name,
                repair_attempts=repair_attempts,
                processing_duration_ms=duration_ms,
                created_at=orm_saved.created_at.isoformat() if orm_saved.created_at else None,
                updated_at=orm_saved.updated_at.isoformat() if orm_saved.updated_at else None,
            )

        except Exception as e:
            err_msg = f"Unhandled pipeline failure: {str(e)}"
            logger.error("Unhandled exception processing resume '%s': %s", resume_id, err_msg)
            resume_db_service.update_status(db, resume_id, "failed", error_message=err_msg)
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ResumeProcessResult(
                resume_id=resume_id,
                processing_status="failed",
                original_filename=target_original_filename,
                error=err_msg,
                processing_duration_ms=duration_ms,
            )


pipeline_orchestrator = PipelineOrchestrator()
