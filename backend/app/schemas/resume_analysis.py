"""
Pydantic Schemas for Phase 17: AI Resume Analysis.
Evaluates resume against general resume-quality criteria:
- clarity
- section completeness
- bullet-point quality
- measurable achievements where present
- skill organization
- project descriptions
- formatting-related text issues
- missing common information
- potential improvements

Strict Anti-Hallucination Guardrails:
- Do NOT invent achievements.
- Do NOT rewrite facts into fake accomplishments.
- Every recommendation must be based on actual resume content.
- Keep factual extraction separate from subjective recommendations.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResumeQualityCriterionEvaluation(BaseModel):
    """
    Detailed evaluation of a specific resume-quality criterion.
    """
    criterion: str = Field(
        ...,
        description="Name of the criterion (e.g. 'clarity', 'section_completeness', 'bullet_point_quality', 'measurable_achievements', 'skill_organization', 'project_descriptions', 'formatting_related_text_issues', 'missing_common_information')"
    )
    score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Optional rating on a 0-10 scale for this dimension"
    )
    observations: List[str] = Field(
        default_factory=list,
        description="Factual observations anchored directly in actual resume content"
    )


class ResumeAnalysisResponse(BaseModel):
    """
    Structured AI Resume Analysis response schema.
    Conforms directly to the user specification:
    {
      "strengths": [],
      "areas_for_improvement": [],
      "suggestions": []
    }
    Includes detailed criterion assessments, factual findings, and audit metadata.
    """
    strengths: List[str] = Field(
        default_factory=list,
        description="Strong aspects grounded strictly in factual resume evidence"
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="Specific shortcomings, gaps, or quality issues identified in actual resume text"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations for improvement, without inventing fake facts or metrics"
    )

    # Detailed criteria breakdown
    criteria_evaluations: Optional[Dict[str, ResumeQualityCriterionEvaluation]] = Field(
        default_factory=dict,
        description="Granular evaluations for each of the 8 required quality criteria"
    )

    # Factual extraction summary kept separate from subjective recommendations
    factual_summary: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Factual summary extracted from resume (sections present, bullet count, metrics detected, etc.)"
    )

    # Execution metadata
    llm_provider: Optional[str] = Field(
        None,
        description="LLM provider used ('gemini', 'openai', 'mock')"
    )
    llm_model: Optional[str] = Field(
        None,
        description="Model identifier used for analysis"
    )
    analysis_duration_ms: Optional[float] = Field(
        None,
        description="Execution duration in milliseconds"
    )


class ResumeAnalysisRequest(BaseModel):
    """
    Request payload for analyzing a resume.
    Can analyze via:
    - raw text
    - parsed Resume object
    - resume_id (persisted database resume)
    """
    resume_id: Optional[str] = Field(None, description="UUID of persisted database resume")
    text: Optional[str] = Field(None, description="Raw or cleaned resume text")
    resume: Optional[Dict[str, Any]] = Field(None, description="Parsed structured resume object dictionary")
