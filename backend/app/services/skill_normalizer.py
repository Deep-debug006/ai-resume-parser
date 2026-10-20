"""
Deterministic Skill Normalization Service (Phase 10).
Normalizes variations, abbreviations, and informal names into standardized canonical forms.
Uses a version-controlled dictionary (data/skill_aliases.json) for high performance and extensibility.

Key Rules:
1. Detect known aliases and map to canonical names.
2. Remove duplicates while preserving original order.
3. Preserve unknown skills rather than deleting or omitting them.
4. Avoid incorrectly merging unrelated technologies (e.g., Java != JavaScript, C != C++ != C#, SQL != NoSQL).
"""
import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any

from backend.app.schemas.parsed_resume import SkillSet, Resume

logger = logging.getLogger(__name__)

# Search paths for the skill aliases configuration
DEFAULT_CONFIG_PATHS = [
    Path("/data/skill_aliases.json"),
    Path("/app/applet/data/skill_aliases.json"),
    Path("/app/applet/backend/app/data/skill_aliases.json"),
    Path(__file__).resolve().parent.parent / "data" / "skill_aliases.json",
    Path("data/skill_aliases.json"),
]


@dataclass
class SkillNormalizationResult:
    """
    Detailed audit outcome of normalizing a collection of skills.
    """
    original_skills: List[str]
    normalized_skills: List[str]
    aliases_resolved: Dict[str, str] = field(default_factory=dict)
    duplicates_removed: List[str] = field(default_factory=list)
    unrecognized_skills: List[str] = field(default_factory=list)

    @property
    def original_count(self) -> int:
        return len(self.original_skills)

    @property
    def normalized_count(self) -> int:
        return len(self.normalized_skills)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_count": self.original_count,
            "normalized_count": self.normalized_count,
            "normalized_skills": self.normalized_skills,
            "aliases_resolved": self.aliases_resolved,
            "duplicates_removed": self.duplicates_removed,
            "unrecognized_skills": self.unrecognized_skills,
        }


class SkillNormalizer:
    """
    Normalizes skill names using an extensible alias lookup table with strict collision guards.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self._alias_to_canonical: Dict[str, str] = {}
        self._canonical_skills: Set[str] = set()
        self._loaded_path: Optional[Path] = None
        self.load_dictionary(config_path)

    def load_dictionary(self, config_path: Optional[Path] = None) -> None:
        """
        Loads the alias dictionary from the specified or discovered path.
        """
        target_path: Optional[Path] = None

        if config_path and Path(config_path).exists():
            target_path = Path(config_path)
        else:
            for p in DEFAULT_CONFIG_PATHS:
                if p.exists() and p.is_file():
                    target_path = p
                    break

        if not target_path:
            logger.warning(
                "Skill aliases file not found in search paths. Initializing empty normalizer."
            )
            return

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            skills_dict = data.get("skills", {})
            self._alias_to_canonical.clear()
            self._canonical_skills.clear()

            for canonical, aliases in skills_dict.items():
                canonical_clean = canonical.strip()
                self._canonical_skills.add(canonical_clean)

                # Canonical name always maps to itself (case-insensitively)
                self._alias_to_canonical[canonical_clean.lower()] = canonical_clean

                # Register each alias
                for alias in aliases:
                    alias_clean = alias.strip().lower()
                    if alias_clean:
                        self._alias_to_canonical[alias_clean] = canonical_clean

            self._loaded_path = target_path
            logger.info(
                "Loaded %d canonical skills with %d alias mappings from %s",
                len(self._canonical_skills),
                len(self._alias_to_canonical),
                target_path,
            )
        except Exception as e:
            logger.error("Failed to load skill aliases dictionary from %s: %s", target_path, e)

    def add_alias(self, canonical_name: str, alias: str) -> None:
        """
        Programmatically extends the dictionary with a new alias.
        """
        canonical_clean = canonical_name.strip()
        alias_clean = alias.strip().lower()

        self._canonical_skills.add(canonical_clean)
        self._alias_to_canonical[canonical_clean.lower()] = canonical_clean
        self._alias_to_canonical[alias_clean] = canonical_clean

    def clean_skill_string(self, raw_skill: str) -> str:
        """
        Cleans extraneous punctuation, leading bullets, and whitespace from a skill string.
        """
        if not raw_skill:
            return ""

        s = raw_skill.strip()
        # Remove leading bullet symbols: •, -, *, ·
        while s and s[0] in ("•", "-", "*", "·", ">", "/", "—", "–", " "):
            s = s[1:].strip()

        # Remove trailing punctuation: , ; . :
        while s and s[-1] in (",", ";", ":", "/", " "):
            s = s[:-1].strip()

        return s

    def normalize_single_skill(self, skill: str) -> Tuple[str, bool]:
        """
        Normalizes a single skill string.

        Returns:
            Tuple of (normalized_skill_name, is_known_alias)
        """
        cleaned = self.clean_skill_string(skill)
        if not cleaned:
            return "", False

        lookup_key = cleaned.lower()

        # 1. Direct dictionary match
        if lookup_key in self._alias_to_canonical:
            canonical = self._alias_to_canonical[lookup_key]
            is_resolved = (cleaned != canonical)
            return canonical, is_resolved

        # 2. Specific punctuation variations (e.g. "React.js" -> "react js", "C++" preserved)
        if "." in lookup_key and lookup_key.endswith(".js"):
            alt_key = lookup_key.replace(".js", " js")
            if alt_key in self._alias_to_canonical:
                return self._alias_to_canonical[alt_key], True

        # 3. Unknown skill: Preserve original case if it has uppercase, else Title-case words
        if cleaned.islower():
            # e.g., "solidity" -> "Solidity"
            preserved = " ".join(word.capitalize() for word in cleaned.split())
        else:
            preserved = cleaned

        return preserved, False

    def normalize_skills(self, skills: List[str]) -> SkillNormalizationResult:
        """
        Normalizes a list of skills:
        - Resolves known aliases
        - Preserves unknown skills
        - Deduplicates without altering first-appearance order
        - Collects full resolution telemetry
        """
        normalized_list: List[str] = []
        seen_canonical_lower: Set[str] = set()
        aliases_resolved: Dict[str, str] = {}
        duplicates_removed: List[str] = []
        unrecognized_skills: List[str] = []

        for raw_item in skills:
            if not raw_item or not raw_item.strip():
                continue

            # Split comma-delimited strings inside a single skill element if present
            # E.g. "Python, Docker, FastAPI" in a single entry
            sub_items = [p.strip() for p in raw_item.split(",") if p.strip()] if "," in raw_item else [raw_item]

            for raw_skill in sub_items:
                normalized, was_resolved = self.normalize_single_skill(raw_skill)
                if not normalized:
                    continue

                norm_key = normalized.lower()

                if was_resolved:
                    aliases_resolved[raw_skill.strip()] = normalized
                else:
                    if normalized not in self._canonical_skills:
                        if normalized not in unrecognized_skills:
                            unrecognized_skills.append(normalized)

                if norm_key in seen_canonical_lower:
                    duplicates_removed.append(raw_skill.strip())
                else:
                    seen_canonical_lower.add(norm_key)
                    normalized_list.append(normalized)

        return SkillNormalizationResult(
            original_skills=list(skills),
            normalized_skills=normalized_list,
            aliases_resolved=aliases_resolved,
            duplicates_removed=duplicates_removed,
            unrecognized_skills=unrecognized_skills,
        )

    def normalize_skill_set(self, skill_set: SkillSet) -> SkillSet:
        """
        Normalizes all skill categories inside a structured Pydantic SkillSet model.
        """
        return SkillSet(
            technical_skills=self.normalize_skills(skill_set.technical_skills).normalized_skills,
            programming_languages=self.normalize_skills(skill_set.programming_languages).normalized_skills,
            frameworks_and_libraries=self.normalize_skills(skill_set.frameworks_and_libraries).normalized_skills,
            databases=self.normalize_skills(skill_set.databases).normalized_skills,
            cloud_and_devops=self.normalize_skills(skill_set.cloud_and_devops).normalized_skills,
            soft_skills=self.normalize_skills(skill_set.soft_skills).normalized_skills,
            tools=self.normalize_skills(skill_set.tools).normalized_skills,
        )

    def normalize_resume(self, resume: Resume) -> Resume:
        """
        Deep-normalizes all skills and technology tags across the entire Resume model:
        - resume.skills (all 7 categories)
        - resume.experience[*].technologies
        - resume.projects[*].technologies
        """
        # Normalize skill set
        normalized_skills = self.normalize_skill_set(resume.skills)

        # Normalize experience technology tags
        normalized_exp = []
        for exp in resume.experience:
            norm_techs = self.normalize_skills(exp.technologies).normalized_skills if exp.technologies else []
            updated_exp = exp.model_copy(update={"technologies": norm_techs})
            normalized_exp.append(updated_exp)

        # Normalize project technology tags
        normalized_proj = []
        for proj in resume.projects:
            norm_techs = self.normalize_skills(proj.technologies).normalized_skills if proj.technologies else []
            updated_proj = proj.model_copy(update={"technologies": norm_techs})
            normalized_proj.append(updated_proj)

        return resume.model_copy(update={
            "skills": normalized_skills,
            "experience": normalized_exp,
            "projects": normalized_proj,
        })


# Global default normalizer instance
skill_normalizer = SkillNormalizer()
