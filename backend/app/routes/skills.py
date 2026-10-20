"""
Routes for Phase 10: Skill Normalization and Dictionary Management.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.schemas.skills import (
    NormalizeSkillsRequest,
    NormalizeSkillsResponse,
    SkillDictionaryStatsResponse,
)
from backend.app.services.skill_normalizer import skill_normalizer

logger = logging.getLogger(__name__)

router = APIRouter()


class AddAliasRequest(BaseModel):
    canonical: str = Field(..., min_length=1, description="Target canonical skill name")
    alias: str = Field(..., min_length=1, description="Alias variation to map")


@router.post(
    "/normalize",
    response_model=NormalizeSkillsResponse,
    status_code=status.HTTP_200_OK,
    summary="Normalize Skills List",
    description="Maps skill variations, abbreviations, and informal names to standardized canonical technologies (Phase 10).",
)
async def normalize_skills_endpoint(payload: NormalizeSkillsRequest) -> NormalizeSkillsResponse:
    """
    Normalizes a list of skills:
    1. Detects known aliases (e.g. JS -> JavaScript, ReactJS -> React, Mongo -> MongoDB)
    2. Maps to canonical names
    3. Deduplicates case-insensitively
    4. Preserves unknown skills safely
    5. Avoids cross-technology collisions
    """
    if not payload.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skills list cannot be empty.",
        )

    result = skill_normalizer.normalize_skills(payload.skills)

    logger.info(
        "Normalized %d skills -> %d canonical skills (resolved %d aliases, removed %d duplicates)",
        result.original_count,
        result.normalized_count,
        len(result.aliases_resolved),
        len(result.duplicates_removed),
    )

    return NormalizeSkillsResponse(
        original_count=result.original_count,
        normalized_count=result.normalized_count,
        normalized_skills=result.normalized_skills,
        aliases_resolved=result.aliases_resolved,
        duplicates_removed=result.duplicates_removed,
        unrecognized_skills=result.unrecognized_skills,
    )


@router.get(
    "/dictionary",
    response_model=SkillDictionaryStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Skill Dictionary Stats",
    description="Returns metadata about loaded canonical skills and aliases (Phase 10).",
)
async def get_skill_dictionary_endpoint() -> SkillDictionaryStatsResponse:
    """
    Returns summary stats of the loaded version-controlled skill dictionary.
    """
    canonical_list = sorted(list(skill_normalizer._canonical_skills))
    return SkillDictionaryStatsResponse(
        canonical_count=len(skill_normalizer._canonical_skills),
        aliases_count=len(skill_normalizer._alias_to_canonical),
        canonical_skills=canonical_list,
    )


@router.post(
    "/alias",
    status_code=status.HTTP_200_OK,
    summary="Add Dynamic Skill Alias",
    description="Registers a new alias into the in-memory skill normalizer without restarting the server.",
)
async def add_skill_alias_endpoint(payload: AddAliasRequest) -> Dict[str, Any]:
    """
    Dynamically registers an alias for testing or custom runtime taxonomy extensions.
    """
    skill_normalizer.add_alias(payload.canonical, payload.alias)
    return {
        "status": "success",
        "message": f"Mapped alias '{payload.alias}' -> canonical '{payload.canonical}'",
        "canonical": payload.canonical,
        "alias": payload.alias,
    }
