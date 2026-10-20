"""
Resume Database Service Layer (Phase 11).
Coordinates transactional persistence, conversion between Pydantic and ORM models,
and data lifecycle operations for resumes stored in PostgreSQL.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.schemas.parsed_resume import Resume
from backend.app.models.resume_models import ResumeModel, UserModel
from backend.app.repositories.resume_repository import resume_repository, ResumeRepository

logger = logging.getLogger(__name__)


class ResumeDBService:
    """
    Service layer orchestrating database persistence for resumes.
    """

    def __init__(self, repository: Optional[ResumeRepository] = None):
        self.repo = repository or resume_repository

    def get_or_create_default_user(self, db: Session, email: str = "demo@example.com", full_name: str = "Demo User") -> UserModel:
        """
        Retrieves or provisions a default user for unauthenticated resumes.
        """
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            user = UserModel(email=email, full_name=full_name)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def save_parsed_resume(
        self,
        db: Session,
        resume: Resume,
        original_filename: str,
        user_id: Optional[str] = None,
        file_identifier: Optional[str] = None,
        extraction_method: str = "unified",
        raw_text_char_count: int = 0,
    ) -> Tuple[ResumeModel, Resume]:
        """
        Persists a parsed Resume model into the PostgreSQL database.
        Returns tuple of (orm_model, pydantic_resume).
        """
        # If user_id is not specified, assign to default user
        if not user_id:
            default_user = self.get_or_create_default_user(db)
            user_id = default_user.id

        orm_resume = self.repo.create(
            db=db,
            resume_data=resume,
            original_filename=original_filename,
            user_id=user_id,
            file_identifier=file_identifier,
            processing_status="processed",
            extraction_method=extraction_method,
            raw_text_char_count=raw_text_char_count,
        )

        pydantic_res = self.repo.to_pydantic(orm_resume)
        logger.info(
            "Persisted resume into PostgreSQL: id='%s', candidate='%s', filename='%s'",
            orm_resume.id,
            pydantic_res.personal_info.full_name,
            original_filename,
        )
        return orm_resume, pydantic_res

    def get_resume(self, db: Session, resume_id: str) -> Optional[Tuple[ResumeModel, Resume]]:
        """
        Retrieves an ORM model and its corresponding Pydantic Resume instance.
        """
        orm_resume = self.repo.get_by_id(db, resume_id)
        if not orm_resume:
            return None
        return orm_resume, self.repo.to_pydantic(orm_resume)

    def list_resumes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists stored resumes with high-level summary metadata.
        """
        records = self.repo.list_all(db, skip=skip, limit=limit, user_id=user_id)
        summaries = []
        for r in records:
            candidate_name = r.personal_info.full_name if r.personal_info else "Unknown"
            candidate_email = r.personal_info.email if r.personal_info else None
            summaries.append({
                "id": r.id,
                "original_filename": r.original_filename,
                "candidate_name": candidate_name,
                "candidate_email": candidate_email,
                "processing_status": r.processing_status,
                "extraction_method": r.extraction_method,
                "raw_text_char_count": r.raw_text_char_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            })
        return summaries

    def update_resume(
        self,
        db: Session,
        resume_id: str,
        updated_resume: Resume,
    ) -> Optional[Tuple[ResumeModel, Resume]]:
        """
        Updates an existing persisted resume.
        """
        orm_resume = self.repo.update(db, resume_id, updated_resume)
        if not orm_resume:
            return None
        return orm_resume, self.repo.to_pydantic(orm_resume)

    def delete_resume(self, db: Session, resume_id: str) -> bool:
        """
        Deletes a resume and cascades to all child relations.
        """
        return self.repo.delete(db, resume_id)

    def create_initial_record(
        self,
        db: Session,
        original_filename: str,
        file_identifier: Optional[str] = None,
        user_id: Optional[str] = None,
        processing_status: str = "uploaded",
    ) -> ResumeModel:
        """
        Creates an initial resume record with tracked status (e.g. uploaded or processing).
        """
        if not user_id:
            default_user = self.get_or_create_default_user(db)
            user_id = default_user.id

        return self.repo.create_initial(
            db=db,
            original_filename=original_filename,
            file_identifier=file_identifier,
            user_id=user_id,
            processing_status=processing_status,
        )

    def update_status(
        self,
        db: Session,
        resume_id: str,
        processing_status: str,
        error_message: Optional[str] = None,
    ) -> Optional[ResumeModel]:
        """
        Updates the processing status of a resume.
        """
        return self.repo.update_status(
            db=db,
            resume_id=resume_id,
            processing_status=processing_status,
            error_message=error_message,
        )

    def save_completed_pipeline(
        self,
        db: Session,
        resume_id: str,
        resume: Resume,
        extraction_method: str = "unified",
        raw_text_char_count: int = 0,
    ) -> Tuple[ResumeModel, Resume]:
        """
        Persists all structured tables for the completed pipeline and marks status as 'completed'.
        """
        orm_resume = self.repo.save_pipeline_results(
            db=db,
            resume_id=resume_id,
            resume_data=resume,
            extraction_method=extraction_method,
            raw_text_char_count=raw_text_char_count,
            processing_status="completed",
        )
        pydantic_res = self.repo.to_pydantic(orm_resume)
        return orm_resume, pydantic_res


resume_db_service = ResumeDBService()
