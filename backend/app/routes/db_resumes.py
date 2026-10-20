"""
Routes for Phase 11: PostgreSQL Database Persistence & Phase 18: User Ownership & Authorization.
Provides CRUD operations, listing, and seed data endpoints for resumes with proper authorization.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import get_db
from backend.app.models.resume_models import ResumeModel, SkillModel, UserModel
from backend.app.schemas.db_resume import (
    DBResumeCreateRequest,
    DBResumeUpdateRequest,
    DBResumeSummaryResponse,
    DBResumeDetailResponse,
    DBStatsResponse,
)
from backend.app.services.resume_db_service import resume_db_service
from backend.app.db.seed import seed_database
from backend.app.core.auth_dependency import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[DBResumeSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Persisted Resumes",
    description="Retrieves a list of resumes stored in the database. When authenticated, filters to only resumes owned by the current user.",
)
def list_db_resumes(
    skip: int = 0,
    limit: int = 50,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> List[DBResumeSummaryResponse]:
    """
    Lists resumes stored in PostgreSQL.
    If authenticated, returns only resumes belonging to current_user.
    """
    user_id = current_user.id if current_user else None
    summaries = resume_db_service.list_resumes(db, skip=skip, limit=limit, user_id=user_id)
    return [DBResumeSummaryResponse(**s) for s in summaries]


@router.post(
    "",
    response_model=DBResumeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Persist Structured Resume",
    description="Saves a structured Resume Pydantic model into normalized tables, associating with authenticated user if present.",
)
def create_db_resume(
    payload: DBResumeCreateRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> DBResumeDetailResponse:
    """
    Persists a parsed resume.
    """
    target_user_id = current_user.id if current_user else payload.user_id

    orm_resume, pydantic_resume = resume_db_service.save_parsed_resume(
        db=db,
        resume=payload.resume,
        original_filename=payload.original_filename,
        user_id=target_user_id,
        file_identifier=payload.file_identifier,
        extraction_method=payload.extraction_method or "unified",
        raw_text_char_count=payload.raw_text_char_count or 0,
    )

    return DBResumeDetailResponse(
        id=orm_resume.id,
        user_id=orm_resume.user_id,
        original_filename=orm_resume.original_filename,
        file_identifier=orm_resume.file_identifier,
        processing_status=orm_resume.processing_status,
        extraction_method=orm_resume.extraction_method,
        raw_text_char_count=orm_resume.raw_text_char_count,
        created_at=orm_resume.created_at.isoformat() if orm_resume.created_at else None,
        updated_at=orm_resume.updated_at.isoformat() if orm_resume.updated_at else None,
        resume=pydantic_resume,
    )


@router.get(
    "/stats",
    response_model=DBStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Database Persistence Metrics",
    description="Returns PostgreSQL connection health and entity metrics.",
)
def get_db_stats(db: Session = Depends(get_db)) -> DBStatsResponse:
    """
    Returns table metrics for PostgreSQL.
    """
    total_resumes = db.query(func.count(ResumeModel.id)).scalar() or 0
    total_skills = db.query(func.count(SkillModel.id)).scalar() or 0
    total_users = db.query(func.count(UserModel.id)).scalar() or 0

    return DBStatsResponse(
        status="healthy",
        database_name="ai_resume_parser (PostgreSQL)",
        total_resumes=total_resumes,
        total_skills=total_skills,
        total_users=total_users,
    )


@router.post(
    "/seed",
    response_model=DBResumeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Seed Database Data",
    description="Seeds default user, canonical skill records, and a sample full resume into PostgreSQL (Phase 11).",
)
def seed_db_endpoint(db: Session = Depends(get_db)) -> DBResumeDetailResponse:
    """
    Seeds database with test/demo data.
    """
    orm_resume = seed_database(db)
    res_pair = resume_db_service.get_resume(db, orm_resume.id)
    if not res_pair:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve seeded resume.",
        )
    orm_res, pyd_res = res_pair
    return DBResumeDetailResponse(
        id=orm_res.id,
        user_id=orm_res.user_id,
        original_filename=orm_res.original_filename,
        file_identifier=orm_res.file_identifier,
        processing_status=orm_res.processing_status,
        extraction_method=orm_res.extraction_method,
        raw_text_char_count=orm_res.raw_text_char_count,
        created_at=orm_res.created_at.isoformat() if orm_res.created_at else None,
        updated_at=orm_res.updated_at.isoformat() if orm_res.updated_at else None,
        resume=pyd_res,
    )


def _check_resume_authorization(
    orm_resume: ResumeModel,
    current_user: Optional[UserModel],
    action_description: str = "access",
) -> None:
    """
    Enforces user ownership and cross-user isolation.
    If the resume is associated with a registered user account:
    - If caller is not authenticated -> 401 Unauthorized
    - If caller is authenticated as another user -> 403 Forbidden
    """
    owner = orm_resume.user
    is_registered_account = owner and bool(owner.hashed_password)

    if is_registered_account:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication required to {action_description} this resume.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if str(orm_resume.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to {action_description} another user's resume.",
            )
    elif current_user and orm_resume.user_id:
        if owner and owner.email != "demo@example.com":
            if str(orm_resume.user_id) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to {action_description} another user's resume.",
                )


@router.get(
    "/{resume_id}",
    response_model=DBResumeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Persisted Resume by ID",
    description="Fetches a complete persisted resume and all child relations by ID. Enforces user authorization.",
)
def get_db_resume(
    resume_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> DBResumeDetailResponse:
    """
    Retrieves full resume with all relations.
    Prevents cross-user access if owned by another user.
    """
    result = resume_db_service.get_resume(db, resume_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' was not found in the database.",
        )
    orm_resume, pydantic_resume = result

    # Authorization Check
    _check_resume_authorization(orm_resume, current_user, action_description="access")

    return DBResumeDetailResponse(
        id=orm_resume.id,
        user_id=orm_resume.user_id,
        original_filename=orm_resume.original_filename,
        file_identifier=orm_resume.file_identifier,
        processing_status=orm_resume.processing_status,
        extraction_method=orm_resume.extraction_method,
        raw_text_char_count=orm_resume.raw_text_char_count,
        created_at=orm_resume.created_at.isoformat() if orm_resume.created_at else None,
        updated_at=orm_resume.updated_at.isoformat() if orm_resume.updated_at else None,
        resume=pydantic_resume,
    )


@router.put(
    "/{resume_id}",
    response_model=DBResumeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Persisted Resume",
    description="Updates existing resume fields and child collections. Enforces user authorization.",
)
def update_db_resume(
    resume_id: str,
    payload: DBResumeUpdateRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> DBResumeDetailResponse:
    """
    Updates a persisted resume.
    """
    existing = resume_db_service.get_resume(db, resume_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' was not found to update.",
        )
    orm_existing, _ = existing
    _check_resume_authorization(orm_existing, current_user, action_description="modify")

    result = resume_db_service.update_resume(db, resume_id, payload.resume)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' was not found to update.",
        )
    orm_resume, pydantic_resume = result
    return DBResumeDetailResponse(
        id=orm_resume.id,
        user_id=orm_resume.user_id,
        original_filename=orm_resume.original_filename,
        file_identifier=orm_resume.file_identifier,
        processing_status=orm_resume.processing_status,
        extraction_method=orm_resume.extraction_method,
        raw_text_char_count=orm_resume.raw_text_char_count,
        created_at=orm_resume.created_at.isoformat() if orm_resume.created_at else None,
        updated_at=orm_resume.updated_at.isoformat() if orm_resume.updated_at else None,
        resume=pydantic_resume,
    )


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Persisted Resume",
    description="Deletes a resume and cascades deletion to all child relations. Enforces user authorization.",
)
def delete_db_resume(
    resume_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Deletes a resume.
    """
    existing = resume_db_service.get_resume(db, resume_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' was not found to delete.",
        )
    orm_existing, _ = existing
    _check_resume_authorization(orm_existing, current_user, action_description="delete")

    success = resume_db_service.delete_resume(db, resume_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' was not found to delete.",
        )
    return {
        "status": "success",
        "message": f"Resume '{resume_id}' and all associated records deleted.",
        "id": resume_id,
    }
