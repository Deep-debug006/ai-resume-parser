"""
Job Description Parsing API Routes (Phase 14).
Provides endpoints for extracting structured job requirements and details from raw text.
"""
import time
import logging
from typing import Union, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Query, Request, Body, Depends
from sqlalchemy.orm import Session
from pydantic import ValidationError

from backend.app.db.session import get_db
from backend.app.schemas.job_description import (
    JobDescription,
    JobParseRequest,
    JobParseResponse,
)
from backend.app.schemas.parsed_resume import Resume
from backend.app.schemas.job_matcher import JobMatchResult, MatchRequest
from backend.app.schemas.semantic_matching import SemanticMatchResult, SemanticMatchRequest
from backend.app.services.job_parser_service import job_parser_service
from backend.app.services.job_matcher import job_matcher
from backend.app.services.semantic_matcher import semantic_matcher
from backend.app.services.resume_parser_service import resume_parser_service
from backend.app.services.resume_db_service import resume_db_service
from backend.app.models.resume_models import UserModel, JobDescriptionModel
from backend.app.core.auth_dependency import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/parse",
    response_model=Union[JobDescription, JobParseResponse],
    status_code=status.HTTP_200_OK,
    summary="Parse raw job description text into structured JobDescription schema",
    description="Extracts job title, company (if explicit), required/preferred skills, education, experience, responsibilities, tools, and certifications.",
)
async def parse_job_description_endpoint(
    request: Request,
    payload: Optional[Dict[str, Any]] = Body(None),
    envelope: bool = Query(
        False,
        description="If True, wraps result in JobParseResponse envelope with timing metrics"
    ),
):
    """
    Extracts structured information from job description text.
    Accepts JSON body `{"text": "..."}` or `{"job_description": "..."}` or raw text.
    """
    start_time = time.perf_counter()

    raw_text: Optional[str] = None

    # Handle JSON dictionary payload
    if payload and isinstance(payload, dict):
        raw_text = payload.get("text") or payload.get("job_description")

    # If not found in parsed JSON, check raw request body
    if not raw_text:
        body_bytes = await request.body()
        if body_bytes:
            decoded = body_bytes.decode("utf-8").strip()
            # If it's a JSON string or plain text
            if decoded.startswith("{") and decoded.endswith("}"):
                import json
                try:
                    data = json.loads(decoded)
                    if isinstance(data, dict):
                        raw_text = data.get("text") or data.get("job_description")
                except Exception:
                    pass
            elif decoded.startswith('"') and decoded.endswith('"'):
                import json
                try:
                    raw_text = json.loads(decoded)
                except Exception:
                    raw_text = decoded
            else:
                raw_text = decoded

    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty. Please provide 'text' or 'job_description' in request body.",
        )

    try:
        job_obj, norm_count, provider = await job_parser_service.parse_job_description(
            raw_text.strip()
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error("Unhandled error during job description parsing: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse job description: {str(e)}",
        )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if envelope:
        return JobParseResponse(
            success=True,
            job=job_obj,
            normalized_skills_count=norm_count,
            duration_ms=duration_ms,
            provider=provider,
        )

    return job_obj


@router.post(
    "/match",
    response_model=JobMatchResult,
    status_code=status.HTTP_200_OK,
    summary="Compare a structured Resume against a structured Job Description",
    description="Performs deterministic, explainable comparison of required skills, preferred skills, experience, and education without making hiring claims.",
)
async def match_resume_to_job_endpoint(
    request: Request,
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
):
    """
    Compares candidate resume against job description.
    Accepts:
    - structured `resume` and `job_description` objects
    - or `resume_id` and `job_description` / `job_text`
    - or `resume_text` and `job_text`
    """
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body cannot be empty. Please provide resume and job_description details.",
        )

    resume_obj: Optional[Resume] = None
    job_obj: Optional[JobDescription] = None

    # 1. Resolve Resume object
    if "resume" in payload and payload["resume"]:
        try:
            resume_obj = Resume.model_validate(payload["resume"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume schema in payload: {str(e)}",
            )
    elif "resume_id" in payload and payload["resume_id"]:
        try:
            db_res_tuple = resume_db_service.get_resume(db, payload["resume_id"])
            if not db_res_tuple:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume '{payload['resume_id']}' not found in database.",
                )
            _, resume_obj = db_res_tuple
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch database resume: {str(e)}",
            )
    elif "resume_text" in payload and payload["resume_text"]:
        try:
            parse_res = await resume_parser_service.parse_direct_text(payload["resume_text"])
            resume_obj = parse_res.resume
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse resume text: {str(e)}",
            )

    # 2. Resolve JobDescription object
    raw_job = payload.get("job_description") or payload.get("job")
    if raw_job and isinstance(raw_job, dict):
        try:
            job_obj = JobDescription.model_validate(raw_job)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid job_description schema in payload: {str(e)}",
            )
    elif "job_text" in payload and payload["job_text"]:
        try:
            job_obj, _, _ = await job_parser_service.parse_job_description(payload["job_text"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse job description text: {str(e)}",
            )
    elif "text" in payload and payload["text"] and not resume_obj:
        # If user passed text for job
        try:
            job_obj, _, _ = await job_parser_service.parse_job_description(payload["text"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse job description text: {str(e)}",
            )

    if not resume_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing resume data. Provide 'resume' (object), 'resume_id' (string), or 'resume_text' (string).",
        )

    if not job_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing job description data. Provide 'job_description' (object) or 'job_text' (string).",
        )

    try:
        match_result = job_matcher.match(resume=resume_obj, job=job_obj)
        return match_result
    except Exception as e:
        logger.error("Error during resume-job matching: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute resume-job matching: {str(e)}",
        )


@router.post(
    "/semantic-match",
    response_model=SemanticMatchResult,
    status_code=status.HTTP_200_OK,
    summary="Compute dense semantic similarity using PostgreSQL pgvector embeddings",
    description="Generates embeddings for resume summary/experience/projects and job requirements. Strictly distinguishes exact skill matches from semantic similarity. Non-evaluative.",
)
async def semantic_match_endpoint(
    request: Request,
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
):
    """
    Performs Phase 16 semantic similarity analysis using PostgreSQL + pgvector.
    Accepts:
    - structured `resume` and `job_description`
    - or `resume_id` and `job_text` / `job_description`
    - or `resume_text` and `job_text`
    """
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body cannot be empty. Please provide resume and job details.",
        )

    resume_obj: Optional[Resume] = None
    job_obj: Optional[JobDescription] = None
    resume_id: Optional[str] = payload.get("resume_id")
    job_id: Optional[str] = payload.get("job_id")

    # 1. Resolve Resume
    if "resume" in payload and payload["resume"]:
        try:
            resume_obj = Resume.model_validate(payload["resume"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume schema: {str(e)}",
            )
    elif "resume_data" in payload and payload["resume_data"]:
        try:
            resume_obj = Resume.model_validate(payload["resume_data"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume_data schema: {str(e)}",
            )
    elif resume_id:
        try:
            db_res_tuple = resume_db_service.get_resume(db, resume_id)
            if not db_res_tuple:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume '{resume_id}' not found in database.",
                )
            _, resume_obj = db_res_tuple
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch database resume: {str(e)}",
            )
    elif "resume_text" in payload and payload["resume_text"]:
        try:
            parse_res = await resume_parser_service.parse_direct_text(payload["resume_text"])
            resume_obj = parse_res.resume
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse resume text: {str(e)}",
            )

    # 2. Resolve JobDescription
    raw_job = payload.get("job_description") or payload.get("job") or payload.get("job_data")
    if raw_job and isinstance(raw_job, dict):
        try:
            job_obj = JobDescription.model_validate(raw_job)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid job_description schema: {str(e)}",
            )
    elif "job_text" in payload and payload["job_text"]:
        try:
            job_obj, _, _ = await job_parser_service.parse_job_description(payload["job_text"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse job description text: {str(e)}",
            )
    elif "text" in payload and payload["text"] and not resume_obj:
        try:
            job_obj, _, _ = await job_parser_service.parse_job_description(payload["text"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse job description text: {str(e)}",
            )

    if not resume_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing resume data. Provide 'resume' (object), 'resume_id' (string), or 'resume_text' (string).",
        )

    if not job_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing job description data. Provide 'job_description' (object) or 'job_text' (string).",
        )

    try:
        result = await semantic_matcher.compute_semantic_match(
            db=db,
            resume=resume_obj,
            job=job_obj,
            resume_id=resume_id,
            job_id=job_id,
        )
        return result
    except Exception as e:
        logger.error("Error during semantic resume-job matching: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute semantic similarity matching: {str(e)}",
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create & Persist Job Description",
    description="Parses and saves a job description linked to the current user (Phase 18).",
)
async def create_job_description(
    payload: Dict[str, Any] = Body(...),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Saves a job description to the database, enforcing user ownership if authenticated.
    """
    raw_text = payload.get("raw_text") or payload.get("text") or payload.get("job_description")
    if not raw_text or not str(raw_text).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text is required.",
        )

    structured_data = payload.get("structured_data")
    title = payload.get("title")
    company = payload.get("company")
    if not structured_data:
        try:
            job_obj, _, _ = await job_parser_service.parse_job_description(str(raw_text).strip())
            structured_data = job_obj.model_dump() if hasattr(job_obj, "model_dump") else job_obj.dict()
            if not title:
                title = job_obj.title
            if not company:
                company = job_obj.company
        except Exception as e:
            logger.warning("Failed to auto-parse structured job fields: %s", e)

    user_id = current_user.id if current_user else payload.get("user_id")
    orm_job = JobDescriptionModel(
        user_id=user_id,
        title=title,
        company=company,
        raw_text=str(raw_text).strip(),
        structured_data=structured_data,
    )
    db.add(orm_job)
    db.commit()
    db.refresh(orm_job)

    return {
        "id": orm_job.id,
        "user_id": orm_job.user_id,
        "title": orm_job.title,
        "company": orm_job.company,
        "raw_text": orm_job.raw_text,
        "structured_data": orm_job.structured_data,
        "created_at": orm_job.created_at.isoformat() if orm_job.created_at else None,
    }


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List Job Descriptions",
    description="Lists job descriptions. When authenticated, filters to current user's job descriptions.",
)
def list_job_descriptions(
    skip: int = 0,
    limit: int = 50,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Lists job descriptions. Filters by current_user when authenticated.
    """
    query = db.query(JobDescriptionModel)
    if current_user:
        query = query.filter(JobDescriptionModel.user_id == current_user.id)
    jobs = query.order_by(JobDescriptionModel.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": j.id,
            "user_id": j.user_id,
            "title": j.title,
            "company": j.company,
            "raw_text": j.raw_text,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "structured_data": j.structured_data,
        }
        for j in jobs
    ]


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Job Description by ID",
    description="Fetches a job description. Verifies user ownership and authorization.",
)
def get_job_description(
    job_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Retrieves job description by ID. Prevents unauthorized cross-user access.
    """
    orm_job = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == job_id).first()
    if not orm_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )
    if orm_job.user_id:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this job description.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if str(orm_job.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access another user's job description.",
            )
    return {
        "id": orm_job.id,
        "user_id": orm_job.user_id,
        "title": orm_job.title,
        "company": orm_job.company,
        "raw_text": orm_job.raw_text,
        "structured_data": orm_job.structured_data,
        "created_at": orm_job.created_at.isoformat() if orm_job.created_at else None,
    }


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Job Description",
    description="Deletes a job description. Verifies user ownership and authorization.",
)
def delete_job_description(
    job_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Deletes job description. Prevents deleting another user's job.
    """
    orm_job = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == job_id).first()
    if not orm_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )
    if orm_job.user_id:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to delete this job description.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if str(orm_job.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete another user's job description.",
            )
    db.delete(orm_job)
    db.commit()
    return {
        "status": "success",
        "message": f"Job description '{job_id}' deleted successfully.",
        "id": job_id,
    }


