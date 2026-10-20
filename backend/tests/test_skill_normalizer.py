"""
Unit and integration tests for Phase 10: Skill Normalization and Taxonomy.
Verifies alias resolution, deduplication, unknown skill preservation,
and collision prevention between distinct technologies (e.g. Java vs JavaScript).
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.skill_normalizer import (
    SkillNormalizer,
    skill_normalizer,
    SkillNormalizationResult,
)
from backend.app.schemas.parsed_resume import SkillSet, Resume, PersonalInfo

client = TestClient(app)


def test_user_requested_examples_normalize_correctly():
    """
    Verify all examples explicitly specified in the user prompt:
    JS -> JavaScript
    Javascript -> JavaScript
    ReactJS -> React
    React.js -> React
    Node -> Node.js
    Mongo -> MongoDB
    """
    normalizer = skill_normalizer

    # 1. JS -> JavaScript
    skill, is_alias = normalizer.normalize_single_skill("JS")
    assert skill == "JavaScript"
    assert is_alias is True

    # 2. Javascript -> JavaScript
    skill, _ = normalizer.normalize_single_skill("Javascript")
    assert skill == "JavaScript"

    # 3. ReactJS -> React
    skill, is_alias = normalizer.normalize_single_skill("ReactJS")
    assert skill == "React"
    assert is_alias is True

    # 4. React.js -> React
    skill, is_alias = normalizer.normalize_single_skill("React.js")
    assert skill == "React"
    assert is_alias is True

    # 5. Node -> Node.js
    skill, is_alias = normalizer.normalize_single_skill("Node")
    assert skill == "Node.js"
    assert is_alias is True

    # 6. Mongo -> MongoDB
    skill, is_alias = normalizer.normalize_single_skill("Mongo")
    assert skill == "MongoDB"
    assert is_alias is True


def test_common_devops_and_backend_aliases():
    """Verify common industry abbreviations resolve to canonical names."""
    normalizer = skill_normalizer

    assert normalizer.normalize_single_skill("postgres")[0] == "PostgreSQL"
    assert normalizer.normalize_single_skill("psql")[0] == "PostgreSQL"
    assert normalizer.normalize_single_skill("k8s")[0] == "Kubernetes"
    assert normalizer.normalize_single_skill("aws")[0] == "Amazon Web Services"
    assert normalizer.normalize_single_skill("gcp")[0] == "Google Cloud Platform"
    assert normalizer.normalize_single_skill("azure")[0] == "Microsoft Azure"
    assert normalizer.normalize_single_skill("fastapi")[0] == "FastAPI"
    assert normalizer.normalize_single_skill("cicd")[0] == "CI/CD"
    assert normalizer.normalize_single_skill("ml")[0] == "Machine Learning"
    assert normalizer.normalize_single_skill("golang")[0] == "Go"


def test_obvious_duplicates_removed_preserving_order():
    """
    Verify multiple variants of the same technology are collapsed to a single canonical entry,
    and first-appearance order is preserved.
    """
    raw_skills = [
        "ReactJS",
        "Python",
        "react.js",
        "React",
        "JS",
        "JavaScript",
        "Node",
        "Node.js",
        "nodejs",
    ]

    result = skill_normalizer.normalize_skills(raw_skills)

    assert result.original_count == 9
    assert result.normalized_skills == ["React", "Python", "JavaScript", "Node.js"]
    assert result.normalized_count == 4
    assert "react.js" in result.duplicates_removed
    assert "React" in result.duplicates_removed
    assert "JavaScript" in result.duplicates_removed
    assert "Node.js" in result.duplicates_removed
    assert "nodejs" in result.duplicates_removed
    assert result.aliases_resolved["ReactJS"] == "React"
    assert result.aliases_resolved["JS"] == "JavaScript"
    assert result.aliases_resolved["Node"] == "Node.js"


def test_preserve_unknown_skills_rather_than_deleting():
    """Verify unknown, internal, or emerging technologies are preserved."""
    raw_skills = [
        "FastAPI",
        "SuperNicheFramework99",
        "CustomInternalTool",
        "solidity",
    ]

    result = skill_normalizer.normalize_skills(raw_skills)

    assert "FastAPI" in result.normalized_skills
    assert "SuperNicheFramework99" in result.normalized_skills
    assert "CustomInternalTool" in result.normalized_skills
    assert "Solidity" in result.normalized_skills  # Title-cased from lower
    assert "SuperNicheFramework99" in result.unrecognized_skills
    assert "CustomInternalTool" in result.unrecognized_skills
    assert len(result.normalized_skills) == 4


def test_avoid_incorrectly_merging_unrelated_technologies():
    """
    CRITICAL: Verify unrelated technologies with similar names are NEVER merged.
    - Java vs JavaScript
    - C vs C++ vs C#
    - SQL vs NoSQL vs PostgreSQL vs MySQL
    - Git vs GitHub
    """
    raw_skills = [
        "Java",
        "JavaScript",
        "C++",
        "C#",
        "SQL",
        "NoSQL",
        "PostgreSQL",
        "MySQL",
        "Git",
        "GitHub",
    ]

    result = skill_normalizer.normalize_skills(raw_skills)

    # All 10 must remain distinct!
    assert len(result.normalized_skills) == 10
    assert "Java" in result.normalized_skills
    assert "JavaScript" in result.normalized_skills
    assert "C++" in result.normalized_skills
    assert "C#" in result.normalized_skills
    assert "SQL" in result.normalized_skills
    assert "NoSQL" in result.normalized_skills
    assert "PostgreSQL" in result.normalized_skills
    assert "MySQL" in result.normalized_skills
    assert "Git" in result.normalized_skills
    assert "GitHub" in result.normalized_skills


def test_clean_skill_string_handles_bullets_and_punctuation():
    """Verify bullets, commas, whitespace, and formatting artifacts are stripped."""
    assert skill_normalizer.clean_skill_string("• Python, ") == "Python"
    assert skill_normalizer.clean_skill_string("- Docker;") == "Docker"
    assert skill_normalizer.clean_skill_string(" * Kubernetes / ") == "Kubernetes"
    assert skill_normalizer.clean_skill_string("   ") == ""


def test_comma_delimited_skills_expanded():
    """Verify comma-delimited strings in a single element are split and normalized."""
    raw = ["Python, Docker, FastAPI", "ReactJS, Node"]
    result = skill_normalizer.normalize_skills(raw)

    assert result.normalized_skills == ["Python", "Docker", "FastAPI", "React", "Node.js"]
    assert result.normalized_count == 5


def test_normalize_pydantic_skill_set():
    """Verify SkillSet domain model normalization across all categories."""
    raw_set = SkillSet(
        technical_skills=["Microservices", "RESTful APIs", "rest"],
        programming_languages=["JS", "Javascript", "Python 3", "ts"],
        frameworks_and_libraries=["ReactJS", "react.js", "fastapi"],
        databases=["mongo", "MongoDB", "postgres"],
        cloud_and_devops=["aws", "k8s", "docker"],
        soft_skills=["Leadership", "Scrum", "agile"],
        tools=["git", "github"],
    )

    normalized_set = skill_normalizer.normalize_skill_set(raw_set)

    assert normalized_set.programming_languages == ["JavaScript", "Python", "TypeScript"]
    assert normalized_set.frameworks_and_libraries == ["React", "FastAPI"]
    assert normalized_set.databases == ["MongoDB", "PostgreSQL"]
    assert normalized_set.cloud_and_devops == ["Amazon Web Services", "Kubernetes", "Docker"]
    assert normalized_set.soft_skills == ["Leadership", "Agile"]
    assert normalized_set.technical_skills == ["Microservices", "RESTful APIs"]
    assert normalized_set.tools == ["Git", "GitHub"]


def test_extending_dictionary_dynamically():
    """Verify dictionary can be extended programmatically with new aliases."""
    test_normalizer = SkillNormalizer()
    test_normalizer.add_alias("Vue.js", "vue-special")

    norm, is_alias = test_normalizer.normalize_single_skill("vue-special")
    assert norm == "Vue.js"
    assert is_alias is True


def test_api_normalize_skills_endpoint():
    """Verify POST /api/skills/normalize endpoint."""
    response = client.post(
        "/api/skills/normalize",
        json={"skills": ["JS", "ReactJS", "Node", "Mongo", "Python 3", "react.js", "ProprietaryCustom"]},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["original_count"] == 7
    assert data["normalized_count"] == 6
    assert data["normalized_skills"] == [
        "JavaScript",
        "React",
        "Node.js",
        "MongoDB",
        "Python",
        "ProprietaryCustom",
    ]
    assert data["aliases_resolved"]["JS"] == "JavaScript"
    assert data["aliases_resolved"]["ReactJS"] == "React"
    assert data["aliases_resolved"]["Node"] == "Node.js"
    assert data["aliases_resolved"]["Mongo"] == "MongoDB"
    assert "react.js" in data["duplicates_removed"]
    assert "ProprietaryCustom" in data["unrecognized_skills"]


def test_api_get_skill_dictionary_stats():
    """Verify GET /api/skills/dictionary endpoint."""
    response = client.get("/api/skills/dictionary")
    assert response.status_code == 200
    data = response.json()

    assert data["canonical_count"] > 30
    assert data["aliases_count"] > 100
    assert "JavaScript" in data["canonical_skills"]
    assert "Python" in data["canonical_skills"]
    assert "React" in data["canonical_skills"]


def test_api_add_alias_endpoint():
    """Verify POST /api/skills/alias endpoint."""
    response = client.post(
        "/api/skills/alias",
        json={"canonical": "PyTorch", "alias": "pytorch-v2"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Now verify it normalizes
    norm_res = client.post(
        "/api/skills/normalize",
        json={"skills": ["pytorch-v2"]},
    )
    assert norm_res.status_code == 200
    assert norm_res.json()["normalized_skills"] == ["PyTorch"]
