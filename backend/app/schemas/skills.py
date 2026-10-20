"""
Pydantic schemas for Phase 10: Skill Normalization and Taxonomy.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NormalizeSkillsRequest(BaseModel):
    """
    Request payload containing list of raw, unnormalized skill strings.
    """
    skills: List[str] = Field(
        ...,
        min_length=1,
        description="List of raw skill strings, acronyms, or comma-separated items to normalize.",
        examples=[["JS", "ReactJS", "Node", "Mongo", "Python 3", "react.js", "CustomInternalTool"]],
    )


class NormalizeSkillsResponse(BaseModel):
    """
    Detailed audit response showing canonical mappings, deduplication, and unrecognized skills.
    """
    original_count: int = Field(..., description="Count of input skill tokens")
    normalized_count: int = Field(..., description="Count of unique normalized skills")
    normalized_skills: List[str] = Field(..., description="Ordered list of deduplicated canonical skills")
    aliases_resolved: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from raw alias variants to their canonical normalized names",
    )
    duplicates_removed: List[str] = Field(
        default_factory=list,
        description="List of skill variations that were merged into already-present canonical forms",
    )
    unrecognized_skills: List[str] = Field(
        default_factory=list,
        description="Preserved skills that were not found in the alias dictionary",
    )


class SkillDictionaryStatsResponse(BaseModel):
    """
    Metadata about the loaded skill alias configuration.
    """
    canonical_count: int = Field(..., description="Total canonical technologies configured")
    aliases_count: int = Field(..., description="Total alias lookups indexed")
    canonical_skills: List[str] = Field(default_factory=list, description="Sorted list of canonical skill names")
