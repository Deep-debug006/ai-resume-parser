"""
Pydantic Schemas for Phase 16: Semantic Similarity Using Embeddings.
Strictly distinguishes exact skill matches from semantic similarity.
Never presents semantic similarity as a definitive hiring probability.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

SEMANTIC_DISCLAIMER = (
    "Semantic similarity is an informational metric reflecting mathematical proximity between text embeddings "
    "(vector cosine similarity). It does NOT represent candidate qualification, interview readiness, "
    "or hiring probability, and must never be interpreted as an automated employment decision."
)


class RequirementSemanticMatch(BaseModel):
    """
    Granular semantic comparison between a single job requirement item
    and the most relevant resume evidence chunk.
    """
    requirement: str = Field(..., description="Stated job requirement, skill, or criterion")
    best_matching_resume_chunk: str = Field(
        ...,
        description="The resume section, experience, or project excerpt that exhibits highest semantic affinity"
    )
    source_type: str = Field(
        ...,
        description="Source of matching chunk: 'experience', 'project', or 'summary'"
    )
    similarity_score: float = Field(
        ...,
        description="Cosine similarity score (0.0 to 1.0) between requirement embedding and resume chunk embedding"
    )
    relevance_tier: str = Field(
        ...,
        description="Informational tier: 'strong_alignment' (>=0.75), 'moderate_alignment' (>=0.55), or 'minimal_alignment' (<0.55)"
    )


class SemanticMatchResult(BaseModel):
    """
    Comprehensive hybrid analysis contrasting exact keyword matches with dense semantic similarity.
    """
    # Dense Semantic Embeddings Metrics
    overall_semantic_similarity: float = Field(
        ...,
        description="Overall cosine similarity between aggregated job overview and candidate profile embeddings (0.0 to 1.0)"
    )
    summary_similarity: Optional[float] = Field(
        None,
        description="Cosine similarity between candidate professional summary and job description overview"
    )
    experience_semantic_alignment: float = Field(
        ...,
        description="Average cosine similarity across key requirements and best-matched experience evidence"
    )
    requirement_matches: List[RequirementSemanticMatch] = Field(
        default_factory=list,
        description="Requirement-by-requirement semantic breakdown"
    )

    # Exact Keyword Matching Metrics (from Phase 15 - explicitly distinguished)
    exact_matched_skills: List[str] = Field(
        default_factory=list,
        description="Skills confirmed via exact/canonical keyword matching (Phase 15)"
    )
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory skills from the job description not explicitly detected in candidate text"
    )
    exact_skills_match_rate: float = Field(
        0.0,
        description="Proportion of required skills with exact keyword verification"
    )

    # Explainability & Ethical AI Non-Evaluative Disclaimers
    semantic_insights: str = Field(
        ...,
        description="Explainable narrative interpreting how semantic vectors align with job context"
    )
    model_name: str = Field(
        "text-embedding-004",
        description="Underlying dense embedding model utilized"
    )
    vector_dimension: int = Field(
        768,
        description="Dimensionality of vectors stored in PostgreSQL pgvector"
    )
    disclaimer: str = Field(
        default=SEMANTIC_DISCLAIMER,
        description="Mandatory ethical disclaimer stating similarity is not a hiring decision or probability"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "overall_semantic_similarity": 0.81,
                "summary_similarity": 0.84,
                "experience_semantic_alignment": 0.79,
                "requirement_matches": [
                    {
                        "requirement": "Required Skill: Python",
                        "best_matching_resume_chunk": "Title: Senior Software Engineer at Nexus\nHighlights: Built microservices using Python and FastAPI",
                        "source_type": "experience",
                        "similarity_score": 0.88,
                        "relevance_tier": "strong_alignment"
                    }
                ],
                "exact_matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                "missing_required_skills": ["Apache Kafka"],
                "exact_skills_match_rate": 0.75,
                "semantic_insights": "Candidate exhibits high semantic affinity in distributed API engineering...",
                "model_name": "text-embedding-004",
                "vector_dimension": 768,
                "disclaimer": SEMANTIC_DISCLAIMER
            }
        }
    }


class SemanticMatchRequest(BaseModel):
    """
    Input request payload for semantic matching endpoint.
    """
    resume_id: Optional[str] = Field(None, description="Optional database resume ID")
    resume_text: Optional[str] = Field(None, description="Raw resume text")
    job_text: Optional[str] = Field(None, description="Raw job description text")
    resume_data: Optional[Dict[str, Any]] = Field(None, description="Parsed structured Resume dictionary")
    job_data: Optional[Dict[str, Any]] = Field(None, description="Parsed structured JobDescription dictionary")
