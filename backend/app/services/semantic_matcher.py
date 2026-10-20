"""
Semantic Matching Service Layer (Phase 16).
Combines dense vector embeddings with exact deterministic matching.

Core Design:
1. Generates and caches dense embeddings for resume summary, experience, projects, job overview, and requirements.
2. Performs vector cosine similarity calculations in PostgreSQL + pgvector (or in-memory vector math).
3. Produces granular requirement-to-experience semantic alignments.
4. Strictly distinguishes exact keyword skill matches (Phase 15) from semantic similarity.
5. Adheres to non-evaluative principles: never presents semantic similarity as a hiring probability.
"""
import uuid
import logging
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.schemas.parsed_resume import Resume
from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.semantic_matching import (
    SemanticMatchResult,
    RequirementSemanticMatch,
    SEMANTIC_DISCLAIMER,
)
from backend.app.services.vector_storage import (
    vector_storage,
    compute_cosine_similarity,
)
from backend.app.services.embedding_service import (
    embedding_service,
    DEFAULT_MODEL_NAME,
    EMBEDDING_DIMENSIONS,
)
from backend.app.services.job_matcher import job_matcher

logger = logging.getLogger(__name__)


class SemanticMatcher:
    """
    Coordinates semantic vector comparisons and exact skill distinctions.
    """

    def __init__(
        self,
        embed_service=None,
        storage=None,
        matcher=None,
    ):
        self.embedding_service = embed_service or embedding_service
        self.vector_storage = storage or vector_storage
        self.job_matcher = matcher or job_matcher

    async def compute_semantic_match(
        self,
        db: Session,
        resume: Resume,
        job: JobDescription,
        resume_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> SemanticMatchResult:
        """
        Executes hybrid semantic similarity and deterministic comparison.
        """
        r_id = resume_id or f"transient_res_{uuid.uuid4().hex[:12]}"
        j_id = job_id or f"transient_job_{uuid.uuid4().hex[:12]}"

        # ----------------------------------------------------------------------
        # 1. Exact Keyword Matching from Phase 15
        # ----------------------------------------------------------------------
        exact_match_res = self.job_matcher.match(resume, job)

        # ----------------------------------------------------------------------
        # 2. Generate / Retrieve Resume Embeddings
        # ----------------------------------------------------------------------
        # Summary embedding
        summary_vec = await self.embedding_service.embed_resume_summary(
            db=db,
            resume_id=r_id,
            summary=resume.summary,
        )

        # Experience chunks embeddings
        exp_chunks = await self.embedding_service.embed_resume_experiences(
            db=db,
            resume_id=r_id,
            experiences=resume.experience,
        )

        # Project chunks embeddings
        proj_chunks = await self.embedding_service.embed_resume_projects(
            db=db,
            resume_id=r_id,
            projects=resume.projects,
        )

        # ----------------------------------------------------------------------
        # 3. Generate / Retrieve Job Embeddings
        # ----------------------------------------------------------------------
        job_overview_vec = await self.embedding_service.embed_job_description(
            db=db,
            job_id=j_id,
            job=job,
        )

        job_req_chunks = await self.embedding_service.embed_job_requirements(
            db=db,
            job_id=j_id,
            job=job,
        )

        # ----------------------------------------------------------------------
        # 4. Compute Semantic Similarities
        # ----------------------------------------------------------------------
        # Summary similarity
        summary_sim: Optional[float] = None
        if summary_vec is not None:
            summary_sim = round(compute_cosine_similarity(summary_vec, job_overview_vec), 4)

        # Gather all candidate evidence chunks for requirement matching
        candidate_evidence: List[Tuple[str, str, List[float]]] = []
        if summary_vec is not None and resume.summary:
            candidate_evidence.append(("summary", resume.summary.strip(), summary_vec))
        for _, text, vec in exp_chunks:
            candidate_evidence.append(("experience", text, vec))
        for _, text, vec in proj_chunks:
            candidate_evidence.append(("project", text, vec))

        # Fallback if candidate has no experience/projects/summary: embed full text representation
        if not candidate_evidence:
            fallback_text = f"Candidate: {resume.personal_info.full_name or 'Applicant'}"
            if resume.skills and resume.skills.technical_skills:
                fallback_text += "\nSkills: " + ", ".join(resume.skills.technical_skills)
            fallback_vec, _ = await self.embedding_service.get_or_create_embedding(
                db=db,
                text=fallback_text,
                entity_type="resume_summary",
                entity_id=r_id,
                chunk_index=0,
            )
            candidate_evidence.append(("summary", fallback_text, fallback_vec))

        # Match each requirement against candidate evidence
        requirement_matches: List[RequirementSemanticMatch] = []
        sim_scores: List[float] = []

        for _, req_text, req_vec in job_req_chunks:
            best_chunk_text = ""
            best_source_type = "experience"
            best_sim = -1.0

            for src_type, chunk_text, chunk_vec in candidate_evidence:
                sim = compute_cosine_similarity(req_vec, chunk_vec)
                if sim > best_sim:
                    best_sim = sim
                    best_chunk_text = chunk_text
                    best_source_type = src_type

            best_sim = max(0.0, min(1.0, round(best_sim, 4)))
            sim_scores.append(best_sim)

            tier = (
                "strong_alignment"
                if best_sim >= 0.75
                else "moderate_alignment"
                if best_sim >= 0.55
                else "minimal_alignment"
            )

            requirement_matches.append(
                RequirementSemanticMatch(
                    requirement=req_text,
                    best_matching_resume_chunk=best_chunk_text,
                    source_type=best_source_type,
                    similarity_score=best_sim,
                    relevance_tier=tier,
                )
            )

        # Average semantic alignment across requirements
        exp_alignment = (
            round(sum(sim_scores) / len(sim_scores), 4) if sim_scores else 0.50
        )

        # Overall semantic similarity: combination of summary/profile and experience alignment
        if summary_sim is not None:
            overall_sim = round(0.4 * summary_sim + 0.6 * exp_alignment, 4)
        else:
            overall_sim = exp_alignment

        # ----------------------------------------------------------------------
        # 5. Explainable Insights Narrative (Strictly Informational)
        # ----------------------------------------------------------------------
        insights_parts = []
        strong_count = sum(1 for m in requirement_matches if m.relevance_tier == "strong_alignment")
        total_reqs = len(requirement_matches)

        insights_parts.append(
            f"Dense vector comparison yields an overall semantic similarity of {overall_sim:.2f} "
            f"using {DEFAULT_MODEL_NAME} ({EMBEDDING_DIMENSIONS} dimensions)."
        )
        insights_parts.append(
            f"{strong_count} of {total_reqs} requirement items exhibit strong semantic alignment "
            f"(cosine similarity >= 0.75) against candidate work history and project descriptions."
        )

        if exact_match_res.missing_required_skills:
            insights_parts.append(
                f"Notice: While exact keyword matching flagged {len(exact_match_res.missing_required_skills)} "
                f"missing skill(s) ({', '.join(exact_match_res.missing_required_skills[:3])}), "
                f"semantic analysis measures contextual overlap across adjacent responsibilities and tools."
            )

        insights_narrative = " ".join(insights_parts)

        logger.info(
            "Semantic matching completed for resume '%s': overall=%.2f, exp_align=%.2f, req_count=%d",
            r_id,
            overall_sim,
            exp_alignment,
            len(requirement_matches),
        )

        return SemanticMatchResult(
            overall_semantic_similarity=overall_sim,
            summary_similarity=summary_sim,
            experience_semantic_alignment=exp_alignment,
            requirement_matches=requirement_matches,
            exact_matched_skills=exact_match_res.matched_skills,
            missing_required_skills=exact_match_res.missing_required_skills,
            exact_skills_match_rate=exact_match_res.required_skills_match_rate,
            semantic_insights=insights_narrative,
            model_name=DEFAULT_MODEL_NAME,
            vector_dimension=EMBEDDING_DIMENSIONS,
            disclaimer=SEMANTIC_DISCLAIMER,
        )


# Global singleton instance
semantic_matcher = SemanticMatcher()
