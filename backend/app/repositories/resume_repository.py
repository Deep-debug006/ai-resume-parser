"""
Repository pattern for Resume persistence in PostgreSQL (Phase 11).
Decouples API schemas from SQLAlchemy ORM entities.
"""
import uuid
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload

from backend.app.schemas.parsed_resume import (
    Resume,
    PersonalInfo,
    Education,
    SkillSet,
    Experience,
    Project,
    Certification,
    Achievement,
)
from backend.app.models.resume_models import (
    ResumeModel,
    ResumePersonalInfoModel,
    SkillModel,
    ResumeSkillModel,
    EducationModel,
    ExperienceModel,
    ProjectModel,
    CertificationModel,
    AchievementModel,
    UserModel,
)

logger = logging.getLogger(__name__)


class ResumeRepository:
    """
    CRUD repository for normalized Resume domain models.
    """

    @staticmethod
    def _get_or_create_skill(db: Session, skill_name: str, category: Optional[str] = None) -> SkillModel:
        """Helper to get existing canonical skill or insert a new record."""
        clean_name = skill_name.strip()
        skill = db.query(SkillModel).filter(SkillModel.name == clean_name).first()
        if not skill:
            skill = SkillModel(name=clean_name, category=category)
            db.add(skill)
            db.flush()
        return skill

    def create(
        self,
        db: Session,
        resume_data: Resume,
        original_filename: str,
        user_id: Optional[str] = None,
        file_identifier: Optional[str] = None,
        processing_status: str = "processed",
        extraction_method: str = "unified",
        raw_text_char_count: int = 0,
    ) -> ResumeModel:
        """
        Persists a complete parsed Resume domain object into normalized PostgreSQL tables.
        """
        resume_id = str(uuid.uuid4())

        orm_resume = ResumeModel(
            id=resume_id,
            user_id=user_id,
            original_filename=original_filename,
            file_identifier=file_identifier,
            processing_status=processing_status,
            extraction_method=extraction_method,
            raw_text_char_count=raw_text_char_count,
            summary=resume_data.summary,
            objective=resume_data.objective,
            languages=resume_data.languages or [],
            interests=resume_data.interests or [],
        )
        db.add(orm_resume)
        db.flush()

        # 1. Personal Info
        pi = resume_data.personal_info
        if pi:
            orm_pi = ResumePersonalInfoModel(
                resume_id=resume_id,
                full_name=pi.full_name,
                email=pi.email,
                phone=pi.phone,
                location=pi.location,
                linkedin_url=pi.linkedin_url,
                github_url=pi.github_url,
                portfolio_url=pi.portfolio_url,
            )
            db.add(orm_pi)

        # 2. Education
        for edu in resume_data.education or []:
            orm_edu = EducationModel(
                resume_id=resume_id,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                start_date=edu.start_date,
                end_date=edu.end_date,
                gpa=edu.gpa,
                gpa_max=edu.gpa_max,
                honors=edu.honors or [],
                courses=edu.courses or [],
            )
            db.add(orm_edu)

        # 3. Skills (Normalized relational join)
        if resume_data.skills:
            skill_categories = {
                "technical_skills": resume_data.skills.technical_skills,
                "programming_languages": resume_data.skills.programming_languages,
                "frameworks_and_libraries": resume_data.skills.frameworks_and_libraries,
                "databases": resume_data.skills.databases,
                "cloud_and_devops": resume_data.skills.cloud_and_devops,
                "soft_skills": resume_data.skills.soft_skills,
                "tools": resume_data.skills.tools,
            }

            for cat_name, skill_list in skill_categories.items():
                for sk_name in skill_list or []:
                    clean_sk = sk_name.strip()
                    if not clean_sk:
                        continue
                    skill_entity = self._get_or_create_skill(db, clean_sk, cat_name)
                    link = ResumeSkillModel(
                        resume_id=resume_id,
                        skill_id=skill_entity.id,
                        category=cat_name,
                    )
                    db.add(link)

        # 4. Experience
        for exp in resume_data.experience or []:
            orm_exp = ExperienceModel(
                resume_id=resume_id,
                company=exp.company,
                title=exp.title,
                location=exp.location,
                start_date=exp.start_date,
                end_date=exp.end_date,
                is_current=exp.is_current,
                highlights=exp.highlights or [],
                technologies=exp.technologies or [],
            )
            db.add(orm_exp)

        # 5. Projects
        for proj in resume_data.projects or []:
            orm_proj = ProjectModel(
                resume_id=resume_id,
                name=proj.name,
                description=proj.description,
                url=proj.url,
                highlights=proj.highlights or [],
                technologies=proj.technologies or [],
                start_date=proj.start_date,
                end_date=proj.end_date,
            )
            db.add(orm_proj)

        # 6. Certifications
        for cert in resume_data.certifications or []:
            orm_cert = CertificationModel(
                resume_id=resume_id,
                name=cert.name,
                issuer=cert.issuer,
                issue_date=cert.issue_date,
                expiration_date=cert.expiration_date,
                credential_id=cert.credential_id,
                url=cert.url,
            )
            db.add(orm_cert)

        # 7. Achievements
        for ach in resume_data.achievements or []:
            orm_ach = AchievementModel(
                resume_id=resume_id,
                title=ach.title,
                issuer=ach.issuer,
                date=ach.date,
                description=ach.description,
            )
            db.add(orm_ach)

        db.commit()
        db.refresh(orm_resume)
        return orm_resume

    def get_by_id(self, db: Session, resume_id: str) -> Optional[ResumeModel]:
        """
        Retrieves a full resume record by primary key with all associated child relations.
        """
        return (
            db.query(ResumeModel)
            .options(
                joinedload(ResumeModel.personal_info),
                joinedload(ResumeModel.education),
                joinedload(ResumeModel.experience),
                joinedload(ResumeModel.projects),
                joinedload(ResumeModel.certifications),
                joinedload(ResumeModel.achievements),
                joinedload(ResumeModel.resume_skills).joinedload(ResumeSkillModel.skill),
            )
            .filter(ResumeModel.id == resume_id)
            .first()
        )

    def list_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> List[ResumeModel]:
        """
        Lists stored resumes with optional user filtering and pagination.
        """
        query = db.query(ResumeModel).options(
            joinedload(ResumeModel.personal_info),
        )
        if user_id:
            query = query.filter(ResumeModel.user_id == user_id)
        return query.order_by(ResumeModel.created_at.desc()).offset(skip).limit(limit).all()

    def update(
        self,
        db: Session,
        resume_id: str,
        updated_resume: Resume,
    ) -> Optional[ResumeModel]:
        """
        Updates an existing resume and replaces child entities with updated records.
        """
        orm_resume = self.get_by_id(db, resume_id)
        if not orm_resume:
            return None

        # Update parent fields
        orm_resume.summary = updated_resume.summary
        orm_resume.objective = updated_resume.objective
        orm_resume.languages = updated_resume.languages or []
        orm_resume.interests = updated_resume.interests or []

        # Update Personal Info
        if updated_resume.personal_info:
            if orm_resume.personal_info:
                orm_resume.personal_info.full_name = updated_resume.personal_info.full_name
                orm_resume.personal_info.email = updated_resume.personal_info.email
                orm_resume.personal_info.phone = updated_resume.personal_info.phone
                orm_resume.personal_info.location = updated_resume.personal_info.location
                orm_resume.personal_info.linkedin_url = updated_resume.personal_info.linkedin_url
                orm_resume.personal_info.github_url = updated_resume.personal_info.github_url
                orm_resume.personal_info.portfolio_url = updated_resume.personal_info.portfolio_url
            else:
                db.add(
                    ResumePersonalInfoModel(
                        resume_id=resume_id,
                        full_name=updated_resume.personal_info.full_name,
                        email=updated_resume.personal_info.email,
                        phone=updated_resume.personal_info.phone,
                        location=updated_resume.personal_info.location,
                        linkedin_url=updated_resume.personal_info.linkedin_url,
                        github_url=updated_resume.personal_info.github_url,
                        portfolio_url=updated_resume.personal_info.portfolio_url,
                    )
                )

        # Clear and recreate child collections
        db.query(EducationModel).filter(EducationModel.resume_id == resume_id).delete()
        for edu in updated_resume.education or []:
            db.add(
                EducationModel(
                    resume_id=resume_id,
                    institution=edu.institution,
                    degree=edu.degree,
                    field_of_study=edu.field_of_study,
                    start_date=edu.start_date,
                    end_date=edu.end_date,
                    gpa=edu.gpa,
                    gpa_max=edu.gpa_max,
                    honors=edu.honors or [],
                    courses=edu.courses or [],
                )
            )

        db.query(ExperienceModel).filter(ExperienceModel.resume_id == resume_id).delete()
        for exp in updated_resume.experience or []:
            db.add(
                ExperienceModel(
                    resume_id=resume_id,
                    company=exp.company,
                    title=exp.title,
                    location=exp.location,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    is_current=exp.is_current,
                    highlights=exp.highlights or [],
                    technologies=exp.technologies or [],
                )
            )

        db.query(ProjectModel).filter(ProjectModel.resume_id == resume_id).delete()
        for proj in updated_resume.projects or []:
            db.add(
                ProjectModel(
                    resume_id=resume_id,
                    name=proj.name,
                    description=proj.description,
                    url=proj.url,
                    highlights=proj.highlights or [],
                    technologies=proj.technologies or [],
                    start_date=proj.start_date,
                    end_date=proj.end_date,
                )
            )

        db.query(CertificationModel).filter(CertificationModel.resume_id == resume_id).delete()
        for cert in updated_resume.certifications or []:
            db.add(
                CertificationModel(
                    resume_id=resume_id,
                    name=cert.name,
                    issuer=cert.issuer,
                    issue_date=cert.issue_date,
                    expiration_date=cert.expiration_date,
                    credential_id=cert.credential_id,
                    url=cert.url,
                )
            )

        db.query(AchievementModel).filter(AchievementModel.resume_id == resume_id).delete()
        for ach in updated_resume.achievements or []:
            db.add(
                AchievementModel(
                    resume_id=resume_id,
                    title=ach.title,
                    issuer=ach.issuer,
                    date=ach.date,
                    description=ach.description,
                )
            )

        # Update skills
        db.query(ResumeSkillModel).filter(ResumeSkillModel.resume_id == resume_id).delete()
        if updated_resume.skills:
            skill_categories = {
                "technical_skills": updated_resume.skills.technical_skills,
                "programming_languages": updated_resume.skills.programming_languages,
                "frameworks_and_libraries": updated_resume.skills.frameworks_and_libraries,
                "databases": updated_resume.skills.databases,
                "cloud_and_devops": updated_resume.skills.cloud_and_devops,
                "soft_skills": updated_resume.skills.soft_skills,
                "tools": updated_resume.skills.tools,
            }
            for cat_name, skill_list in skill_categories.items():
                for sk_name in skill_list or []:
                    clean_sk = sk_name.strip()
                    if clean_sk:
                        skill_entity = self._get_or_create_skill(db, clean_sk, cat_name)
                        db.add(ResumeSkillModel(
                            resume_id=resume_id,
                            skill_id=skill_entity.id,
                            category=cat_name,
                        ))

        db.commit()
        db.refresh(orm_resume)
        return orm_resume

    def delete(self, db: Session, resume_id: str) -> bool:
        """
        Deletes a resume and cascades to all child relations.
        """
        orm_resume = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if not orm_resume:
            return False

        db.delete(orm_resume)
        db.commit()
        return True

    def to_pydantic(self, orm_resume: ResumeModel) -> Resume:
        """
        Transforms a database ORM ResumeModel instance into a pure Pydantic Resume domain model.
        Decouples storage representation from API contract.
        """
        # Personal Info
        pi_data = orm_resume.personal_info
        personal_info = (
            PersonalInfo(
                full_name=pi_data.full_name,
                email=pi_data.email,
                phone=pi_data.phone,
                location=pi_data.location,
                linkedin_url=pi_data.linkedin_url,
                github_url=pi_data.github_url,
                portfolio_url=pi_data.portfolio_url,
            )
            if pi_data
            else PersonalInfo(full_name="Unknown")
        )

        # Education
        education = [
            Education(
                institution=e.institution,
                degree=e.degree,
                field_of_study=e.field_of_study,
                start_date=e.start_date,
                end_date=e.end_date,
                gpa=e.gpa,
                gpa_max=e.gpa_max,
                honors=e.honors or [],
                courses=e.courses or [],
            )
            for e in orm_resume.education
        ]

        # Skills
        categorized_skills: Dict[str, List[str]] = {
            "technical_skills": [],
            "programming_languages": [],
            "frameworks_and_libraries": [],
            "databases": [],
            "cloud_and_devops": [],
            "soft_skills": [],
            "tools": [],
        }

        for rs in orm_resume.resume_skills:
            if rs.skill:
                cat = rs.category or "technical_skills"
                if cat in categorized_skills:
                    categorized_skills[cat].append(rs.skill.name)
                else:
                    categorized_skills["technical_skills"].append(rs.skill.name)

        skills = SkillSet(
            technical_skills=categorized_skills["technical_skills"],
            programming_languages=categorized_skills["programming_languages"],
            frameworks_and_libraries=categorized_skills["frameworks_and_libraries"],
            databases=categorized_skills["databases"],
            cloud_and_devops=categorized_skills["cloud_and_devops"],
            soft_skills=categorized_skills["soft_skills"],
            tools=categorized_skills["tools"],
        )

        # Experience
        experience = [
            Experience(
                company=exp.company,
                title=exp.title,
                location=exp.location,
                start_date=exp.start_date,
                end_date=exp.end_date,
                is_current=exp.is_current,
                highlights=exp.highlights or [],
                technologies=exp.technologies or [],
            )
            for exp in orm_resume.experience
        ]

        # Projects
        projects = [
            Project(
                name=proj.name,
                description=proj.description,
                url=proj.url,
                highlights=proj.highlights or [],
                technologies=proj.technologies or [],
                start_date=proj.start_date,
                end_date=proj.end_date,
            )
            for proj in orm_resume.projects
        ]

        # Certifications
        certifications = [
            Certification(
                name=cert.name,
                issuer=cert.issuer,
                issue_date=cert.issue_date,
                expiration_date=cert.expiration_date,
                credential_id=cert.credential_id,
                url=cert.url,
            )
            for cert in orm_resume.certifications
        ]

        # Achievements
        achievements = [
            Achievement(
                title=ach.title,
                issuer=ach.issuer,
                date=ach.date,
                description=ach.description,
            )
            for ach in orm_resume.achievements
        ]

        return Resume(
            personal_info=personal_info,
            summary=orm_resume.summary,
            objective=orm_resume.objective,
            education=education,
            skills=skills,
            experience=experience,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
            languages=orm_resume.languages or [],
            interests=orm_resume.interests or [],
        )

    def create_initial(
        self,
        db: Session,
        original_filename: str,
        file_identifier: Optional[str] = None,
        user_id: Optional[str] = None,
        processing_status: str = "uploaded",
    ) -> ResumeModel:
        """
        Creates an initial resume record with tracked status (e.g. uploaded).
        """
        resume_id = str(uuid.uuid4())
        orm_resume = ResumeModel(
            id=resume_id,
            user_id=user_id,
            original_filename=original_filename,
            file_identifier=file_identifier,
            processing_status=processing_status,
            extraction_method=None,
            raw_text_char_count=0,
            summary=None,
            objective=None,
            languages=[],
            interests=[],
        )
        db.add(orm_resume)
        db.commit()
        db.refresh(orm_resume)
        return orm_resume

    def update_status(
        self,
        db: Session,
        resume_id: str,
        processing_status: str,
        error_message: Optional[str] = None,
    ) -> Optional[ResumeModel]:
        """
        Updates the processing status of a resume (uploaded, processing, completed, failed).
        """
        orm_resume = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
        if not orm_resume:
            return None
        orm_resume.processing_status = processing_status
        if error_message is not None:
            orm_resume.error_message = error_message
        db.commit()
        db.refresh(orm_resume)
        return orm_resume

    def save_pipeline_results(
        self,
        db: Session,
        resume_id: str,
        resume_data: Resume,
        extraction_method: str = "unified",
        raw_text_char_count: int = 0,
        processing_status: str = "completed",
    ) -> ResumeModel:
        """
        Populates structured resume data and updates status to completed.
        """
        orm_resume = self.update(db, resume_id, resume_data)
        if not orm_resume:
            return self.create(
                db=db,
                resume_data=resume_data,
                original_filename="resume.pdf",
                processing_status=processing_status,
                extraction_method=extraction_method,
                raw_text_char_count=raw_text_char_count,
            )
        orm_resume.extraction_method = extraction_method
        orm_resume.raw_text_char_count = raw_text_char_count
        orm_resume.processing_status = processing_status
        orm_resume.error_message = None
        db.commit()
        db.refresh(orm_resume)
        return orm_resume


resume_repository = ResumeRepository()
