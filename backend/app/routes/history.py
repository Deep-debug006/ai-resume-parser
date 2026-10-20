"""
History API Routes for Phase 20: User History.
Provides paginated, lightweight summary listings, filtering, sorting, detail retrieval,
and deletion for:
- Previously uploaded resumes and processing status
- Previous job descriptions
- Previous resume-job and resume-quality analyses
- Timestamps
Enforces user ownership and proper authorization checks.
"""
import math
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc, asc

from backend.app.db.session import get_db
from backend.app.models.resume_models import (
    UserModel,
    ResumeModel,
    JobDescriptionModel,
    AnalysisHistoryModel,
    ResumeSkillModel,
)
from backend.app.schemas.history import (
    PaginatedMeta,
    ResumeHistorySummary,
    JobHistorySummary,
    AnalysisHistorySummary,
    AnalysisHistoryDetail,
    AnalysisCreateRequest,
    PaginatedResumesResponse,
    PaginatedJobsResponse,
    PaginatedAnalysesResponse,
    HistoryOverviewResponse,
)
from backend.app.core.auth_dependency import get_current_user_optional
from backend.app.services.resume_db_service import resume_db_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# 1. Overview Summary Stats
# ============================================================================

@router.get(
    "/summary",
    response_model=HistoryOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="User History Overview Metrics",
    description="Returns aggregate counts of stored resumes, jobs, and analyses for the active user.",
)
def get_history_summary(
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> HistoryOverviewResponse:
    """
    Returns user history counts.
    """
    resume_q = db.query(func.count(ResumeModel.id))
    job_q = db.query(func.count(JobDescriptionModel.id))
    analysis_q = db.query(func.count(AnalysisHistoryModel.id))

    if current_user:
        resume_q = resume_q.filter(ResumeModel.user_id == current_user.id)
        job_q = job_q.filter(JobDescriptionModel.user_id == current_user.id)
        analysis_q = analysis_q.filter(AnalysisHistoryModel.user_id == current_user.id)

    return HistoryOverviewResponse(
        total_resumes=resume_q.scalar() or 0,
        total_jobs=job_q.scalar() or 0,
        total_analyses=analysis_q.scalar() or 0,
    )


# ============================================================================
# 2. Resumes History
# ============================================================================

@router.get(
    "/resumes",
    response_model=PaginatedResumesResponse,
    status_code=status.HTTP_200_OK,
    summary="List Resume Upload History",
    description="Paginated, lightweight summary list of previously uploaded resumes with search, filter, and sorting.",
)
def list_resume_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by filename or candidate name"),
    status_filter: Optional[str] = Query(None, description="Filter by processing status"),
    sort_by: str = Query("newest", description="Sort order: newest, oldest, name_asc, name_desc"),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> PaginatedResumesResponse:
    """
    Returns lightweight summary of resumes for the user. Never returns large text/JSON blobs.
    """
    query = db.query(ResumeModel).options(
        joinedload(ResumeModel.personal_info),
        joinedload(ResumeModel.resume_skills),
    )

    if current_user:
        query = query.filter(ResumeModel.user_id == current_user.id)

    if status_filter and status_filter.strip():
        query = query.filter(ResumeModel.processing_status == status_filter.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.outerjoin(ResumeModel.personal_info).filter(
            or_(
                ResumeModel.original_filename.ilike(term),
                ResumeModel.personal_info.has(full_name=term),
            )
        )

    # Sorting
    if sort_by == "oldest":
        query = query.order_by(asc(ResumeModel.created_at))
    elif sort_by == "name_asc":
        query = query.order_by(asc(ResumeModel.original_filename))
    elif sort_by == "name_desc":
        query = query.order_by(desc(ResumeModel.original_filename))
    else:  # newest
        query = query.order_by(desc(ResumeModel.created_at))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = []
    for r in records:
        cand_name = r.personal_info.full_name if r.personal_info else None
        cand_email = r.personal_info.email if r.personal_info else None
        skills_cnt = len(r.resume_skills) if r.resume_skills else 0

        items.append(
            ResumeHistorySummary(
                id=r.id,
                user_id=r.user_id,
                original_filename=r.original_filename,
                candidate_name=cand_name,
                candidate_email=cand_email,
                processing_status=r.processing_status,
                extraction_method=r.extraction_method or "unified",
                raw_text_char_count=r.raw_text_char_count or 0,
                skills_count=skills_cnt,
                created_at=r.created_at.isoformat() if r.created_at else None,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
        )

    return PaginatedResumesResponse(
        items=items,
        meta=PaginatedMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


# ============================================================================
# 3. Job Descriptions History
# ============================================================================

@router.get(
    "/jobs",
    response_model=PaginatedJobsResponse,
    status_code=status.HTTP_200_OK,
    summary="List Job Descriptions History",
    description="Paginated, lightweight summary list of previously entered job descriptions with search and sorting.",
)
def list_job_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title, company, or keywords"),
    sort_by: str = Query("newest", description="Sort order: newest, oldest, title_asc, title_desc"),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> PaginatedJobsResponse:
    """
    Returns lightweight summaries of job descriptions.
    """
    query = db.query(JobDescriptionModel)

    if current_user:
        query = query.filter(JobDescriptionModel.user_id == current_user.id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JobDescriptionModel.title.ilike(term),
                JobDescriptionModel.company.ilike(term),
                JobDescriptionModel.raw_text.ilike(term),
            )
        )

    if sort_by == "oldest":
        query = query.order_by(asc(JobDescriptionModel.created_at))
    elif sort_by == "title_asc":
        query = query.order_by(asc(JobDescriptionModel.title))
    elif sort_by == "title_desc":
        query = query.order_by(desc(JobDescriptionModel.title))
    else:  # newest
        query = query.order_by(desc(JobDescriptionModel.created_at))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = []
    for j in records:
        req_cnt = 0
        if j.structured_data and isinstance(j.structured_data, dict):
            req_cnt = len(j.structured_data.get("required_skills", []))

        items.append(
            JobHistorySummary(
                id=j.id,
                user_id=j.user_id,
                title=j.title or "Untitled Role",
                company=j.company,
                char_count=len(j.raw_text) if j.raw_text else 0,
                required_skills_count=req_cnt,
                created_at=j.created_at.isoformat() if j.created_at else None,
                updated_at=j.updated_at.isoformat() if j.updated_at else None,
            )
        )

    return PaginatedJobsResponse(
        items=items,
        meta=PaginatedMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


# ============================================================================
# 4. Analysis History
# ============================================================================

@router.get(
    "/analyses",
    response_model=PaginatedAnalysesResponse,
    status_code=status.HTTP_200_OK,
    summary="List Analysis Records History",
    description="Paginated, lightweight summary list of previously executed resume-job matches and quality analyses.",
)
def list_analysis_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by job title, candidate name, or company"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis_type: job_match, semantic_match, resume_quality"),
    sort_by: str = Query("newest", description="Sort order: newest, oldest, score_desc, score_asc"),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> PaginatedAnalysesResponse:
    """
    Returns lightweight analysis history records.
    """
    query = db.query(AnalysisHistoryModel)

    if current_user:
        query = query.filter(AnalysisHistoryModel.user_id == current_user.id)

    if analysis_type and analysis_type.strip():
        query = query.filter(AnalysisHistoryModel.analysis_type == analysis_type.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AnalysisHistoryModel.job_title.ilike(term),
                AnalysisHistoryModel.candidate_name.ilike(term),
                AnalysisHistoryModel.company.ilike(term),
                AnalysisHistoryModel.resume_filename.ilike(term),
            )
        )

    if sort_by == "oldest":
        query = query.order_by(asc(AnalysisHistoryModel.created_at))
    elif sort_by == "score_desc":
        query = query.order_by(desc(AnalysisHistoryModel.match_rate), desc(AnalysisHistoryModel.score))
    elif sort_by == "score_asc":
        query = query.order_by(asc(AnalysisHistoryModel.match_rate), asc(AnalysisHistoryModel.score))
    else:  # newest
        query = query.order_by(desc(AnalysisHistoryModel.created_at))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = [
        AnalysisHistorySummary(
            id=a.id,
            user_id=a.user_id,
            resume_id=a.resume_id,
            candidate_name=a.candidate_name,
            resume_filename=a.resume_filename,
            job_id=a.job_id,
            job_title=a.job_title,
            company=a.company,
            analysis_type=a.analysis_type,
            score=a.score,
            match_rate=a.match_rate,
            summary=a.summary,
            created_at=a.created_at.isoformat() if a.created_at else None,
            updated_at=a.updated_at.isoformat() if a.updated_at else None,
        )
        for a in records
    ]

    return PaginatedAnalysesResponse(
        items=items,
        meta=PaginatedMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.post(
    "/analyses",
    response_model=AnalysisHistorySummary,
    status_code=status.HTTP_201_CREATED,
    summary="Record Analysis to History",
    description="Saves a completed resume-job comparison or resume quality analysis into history.",
)
def record_analysis_history(
    payload: AnalysisCreateRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> AnalysisHistorySummary:
    """
    Saves an analysis record associated with user.
    """
    user_id = current_user.id if current_user else None

    orm_analysis = AnalysisHistoryModel(
        user_id=user_id,
        resume_id=payload.resume_id,
        candidate_name=payload.candidate_name,
        resume_filename=payload.resume_filename,
        job_id=payload.job_id,
        job_title=payload.job_title,
        company=payload.company,
        analysis_type=payload.analysis_type,
        score=payload.score,
        match_rate=payload.match_rate,
        summary=payload.summary,
        result_data=payload.result_data,
    )
    db.add(orm_analysis)
    db.commit()
    db.refresh(orm_analysis)

    return AnalysisHistorySummary(
        id=orm_analysis.id,
        user_id=orm_analysis.user_id,
        resume_id=orm_analysis.resume_id,
        candidate_name=orm_analysis.candidate_name,
        resume_filename=orm_analysis.resume_filename,
        job_id=orm_analysis.job_id,
        job_title=orm_analysis.job_title,
        company=orm_analysis.company,
        analysis_type=orm_analysis.analysis_type,
        score=orm_analysis.score,
        match_rate=orm_analysis.match_rate,
        summary=orm_analysis.summary,
        created_at=orm_analysis.created_at.isoformat() if orm_analysis.created_at else None,
        updated_at=orm_analysis.updated_at.isoformat() if orm_analysis.updated_at else None,
    )


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisHistoryDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Analysis Record",
    description="Retrieves full analysis payload and comparisons. Enforces user authorization.",
)
def get_analysis_detail(
    analysis_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> AnalysisHistoryDetail:
    """
    Fetches full analysis payload. Prevents unauthorized cross-user access.
    """
    record = db.query(AnalysisHistoryModel).filter(AnalysisHistoryModel.id == analysis_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis record with ID '{analysis_id}' was not found.",
        )

    if record.user_id:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this analysis record.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if str(record.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view another user's analysis record.",
            )

    return AnalysisHistoryDetail(
        id=record.id,
        user_id=record.user_id,
        resume_id=record.resume_id,
        candidate_name=record.candidate_name,
        resume_filename=record.resume_filename,
        job_id=record.job_id,
        job_title=record.job_title,
        company=record.company,
        analysis_type=record.analysis_type,
        score=record.score,
        match_rate=record.match_rate,
        summary=record.summary,
        result_data=record.result_data,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


@router.delete(
    "/analyses/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Analysis Record",
    description="Deletes an analysis record. Enforces user ownership.",
)
def delete_analysis_record(
    analysis_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Deletes analysis record with authorization checks.
    """
    record = db.query(AnalysisHistoryModel).filter(AnalysisHistoryModel.id == analysis_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis record with ID '{analysis_id}' was not found to delete.",
        )

    if record.user_id:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to delete this analysis record.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if str(record.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete another user's analysis record.",
            )

    db.delete(record)
    db.commit()
    return {
        "status": "success",
        "message": f"Analysis record '{analysis_id}' deleted successfully.",
        "id": analysis_id,
    }
