"""
Comprehensive unit and integration tests for Phase 16: Semantic Similarity Using Embeddings.
Validates:
- Vector dimensions (768) and unit normalization
- PostgreSQL + pgvector storage and cosine distance search
- Content-hash caching to prevent regenerating unchanged embeddings
- Strict distinction between exact skill matching and dense semantic similarity
- Non-evaluative principles: zero hiring probabilities or automated decision claims
- FastAPI endpoint POST /api/jobs/semantic-match
"""
import uuid
import asyncio
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.schemas.parsed_resume import (
    Resume,
    PersonalInfo,
    Education,
    SkillSet,
    Experience,
    Project,
)
from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.semantic_matching import (
    SemanticMatchResult,
    SEMANTIC_DISCLAIMER,
)
from backend.app.models.embedding_models import VectorEmbeddingModel, EMBEDDING_DIMENSIONS
from backend.app.services.vector_storage import (
    vector_storage,
    compute_content_hash,
    compute_cosine_similarity,
)
from backend.app.services.embedding_service import (
    EmbeddingService,
    MockEmbeddingProvider,
)
from backend.app.services.semantic_matcher import SemanticMatcher, semantic_matcher

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_embedding_env(monkeypatch):
    """Ensures all tests use MockEmbeddingProvider and MockLLMProvider for deterministic fast execution without remote LLM calls."""
    from backend.app.services.llm_service import MockLLMProvider, llm_service
    mock_prov = MockEmbeddingProvider()
    mock_llm = MockLLMProvider()
    semantic_matcher.embedding_service.provider = mock_prov
    monkeypatch.setattr(semantic_matcher.embedding_service, "provider", mock_prov)
    monkeypatch.setattr(llm_service, "provider", mock_llm)
    yield


# ============================================================================
# Test Fixtures & Sample Builders
# ============================================================================

def make_test_resume() -> Resume:
    return Resume(
        personal_info=PersonalInfo(
            full_name="Morgan Vance",
            email="morgan.vance@example.com",
            phone="415-555-0199",
            location="San Francisco, CA",
        ),
        summary="Senior Backend Software Engineer with 6+ years building distributed Python microservices, PostgreSQL architectures, and cloud APIs.",
        education=[
            Education(
                institution="University of Washington",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
            )
        ],
        skills=SkillSet(
            programming_languages=["Python", "Go"],
            frameworks_and_libraries=["FastAPI", "Docker"],
            databases=["PostgreSQL", "Redis"],
            tools=["Git", "Linux"],
        ),
        experience=[
            Experience(
                company="Nexus Infrastructure",
                title="Senior Backend Engineer",
                start_date="2021",
                end_date="Present",
                is_current=True,
                highlights=[
                    "Engineered low-latency REST endpoints handling 10k req/sec with FastAPI and async PostgreSQL",
                    "Maintained Docker container orchestration and Redis cache clusters",
                ],
                technologies=["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
            )
        ],
        projects=[
            Project(
                name="Stream Analytics Engine",
                description="Real-time distributed telemetry pipeline using async Python and PostgreSQL",
                technologies=["Python", "PostgreSQL"],
            )
        ],
    )


def make_test_job() -> JobDescription:
    return JobDescription(
        job_title="Senior Backend Engineer",
        company="Apex Cloud Systems",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Kafka"],
        preferred_skills=["Redis", "Kubernetes"],
        experience_requirements=["5+ years building scalable distributed backend services in Python."],
        education_requirements=["Bachelor's degree in Computer Science or related engineering field."],
        responsibilities=[
            "Design, build, and maintain production RESTful microservices in Python",
            "Optimize relational database schema performance and queries on PostgreSQL",
        ],
        tools_and_technologies=["Python", "FastAPI", "PostgreSQL", "Kafka", "Docker"],
    )


# ============================================================================
# 1. Embedding Dimensions & Unit Normalization Tests
# ============================================================================

def test_mock_embedding_dimensions_and_normalization():
    """Validates that embeddings have exactly 768 dimensions and unit length."""
    async def _test():
        provider = MockEmbeddingProvider(dimensions=768)
        text = "Senior Python engineer building distributed backend APIs"

        vec = await provider.embed_text(text)

        assert len(vec) == 768
        # L2 norm should equal 1.0 (unit vector)
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, 0.001) == 1.0

        # Verify deterministic reproducibility
        vec_repeat = await provider.embed_text(text)
        assert vec == vec_repeat

    asyncio.run(_test())


def test_cosine_similarity_computation():
    """Validates cosine similarity behavior with identical and distinct texts."""
    async def _test():
        provider = MockEmbeddingProvider()

        vec_a = await provider.embed_text("Senior backend engineer with Python and PostgreSQL")
        vec_b = await provider.embed_text("Senior backend engineer with Python and PostgreSQL")
        vec_c = await provider.embed_text("Pastry chef baking French artisanal croissants and bread")

        sim_identical = compute_cosine_similarity(vec_a, vec_b)
        sim_unrelated = compute_cosine_similarity(vec_a, vec_c)

        assert pytest.approx(sim_identical, 0.001) == 1.0
        assert sim_identical > sim_unrelated
        assert sim_unrelated >= 0.0

    asyncio.run(_test())


# ============================================================================
# 2. Vector Storage & Content-Hash Caching Tests
# ============================================================================

def test_vector_storage_content_hash_caching():
    """
    CRITICAL REQUIREMENT:
    Avoid regenerating embeddings unnecessarily when content has not changed.
    Validates SHA-256 deduplication and database retrieval.
    """
    with SessionLocal() as db:
        test_id = f"test_resume_{uuid.uuid4().hex[:8]}"
        sample_text = "Experienced cloud developer specializing in distributed microservices."
        content_hash = compute_content_hash(sample_text)

        rng = np.random.RandomState(42)
        dummy_vec = (rng.normal(0, 1, 768) / np.linalg.norm(rng.normal(0, 1, 768))).tolist()

        # First save
        rec1 = vector_storage.save_embedding(
            db=db,
            entity_type="resume_summary",
            entity_id=test_id,
            content_text=sample_text,
            embedding=dummy_vec,
            chunk_index=0,
        )
        assert rec1.id is not None
        assert rec1.content_hash == content_hash

        # Retrieval by content hash
        cached = vector_storage.get_by_content_hash(db, content_hash)
        assert cached is not None
        assert cached.id == rec1.id

        # Re-saving same content should NOT create duplicate record
        rec2 = vector_storage.save_embedding(
            db=db,
            entity_type="resume_summary",
            entity_id=test_id,
            content_text=sample_text,
            embedding=dummy_vec,
            chunk_index=0,
        )
        assert rec2.id == rec1.id

        # Cleanup
        vector_storage.delete_embeddings_for_entity(db, "resume_summary", test_id)


def test_embedding_service_caching_hit():
    """
    Validates that EmbeddingService skips provider invocation when content hash is cached.
    """
    async def _test():
        with SessionLocal() as db:
            test_id = f"test_cache_{uuid.uuid4().hex[:8]}"
            text = "Staff Architect specializing in Python backend infrastructure."
            service = EmbeddingService(provider=MockEmbeddingProvider())

            # 1st call: newly generated = True
            vec1, is_new1 = await service.get_or_create_embedding(
                db=db,
                text=text,
                entity_type="resume_summary",
                entity_id=test_id,
                chunk_index=0,
            )
            assert is_new1 is True
            assert len(vec1) == 768

            # 2nd call with identical content: newly generated = False (CACHE HIT!)
            vec2, is_new2 = await service.get_or_create_embedding(
                db=db,
                text=text,
                entity_type="resume_summary",
                entity_id=test_id,
                chunk_index=0,
            )
            assert is_new2 is False
            assert vec1 == vec2

            # Cleanup
            vector_storage.delete_embeddings_for_entity(db, "resume_summary", test_id)

    asyncio.run(_test())


# ============================================================================
# 3. pgvector Cosine Distance Search Tests
# ============================================================================

def test_pgvector_cosine_similarity_search():
    """Validates PostgreSQL pgvector cosine distance `<=>` search queries."""
    with SessionLocal() as db:
        group_id = f"search_grp_{uuid.uuid4().hex[:8]}"
        mock_provider = MockEmbeddingProvider()

        vec_py = asyncio.run(mock_provider.embed_text("Python FastAPI backend API developer"))
        vec_fe = asyncio.run(mock_provider.embed_text("Frontend developer with React and CSS styling"))
        vec_unrelated = asyncio.run(mock_provider.embed_text("Sous chef preparing seafood risotto"))

        # Save all 3 to pgvector
        vector_storage.save_embedding(db, "search_test", group_id, "Python FastAPI backend API developer", vec_py, chunk_index=0)
        vector_storage.save_embedding(db, "search_test", group_id, "Frontend developer with React and CSS styling", vec_fe, chunk_index=1)
        vector_storage.save_embedding(db, "search_test", group_id, "Sous chef preparing seafood risotto", vec_unrelated, chunk_index=2)

        # Query with Python-related search vector
        query_vec = asyncio.run(mock_provider.embed_text("Python REST API engineer"))
        similar = vector_storage.search_similar(
            db=db,
            query_vector=query_vec,
            entity_type="search_test",
            filter_entity_ids=[group_id],
            limit=3,
        )

        assert len(similar) == 3
        top_match_record, top_similarity = similar[0]

        # Top result must be the Python backend record
        assert "Python" in top_match_record.content_text
        assert top_similarity > similar[1][1]
        assert top_similarity > similar[2][1]
        assert top_similarity > 0.40
        assert top_similarity <= 1.0

        # Cleanup
        vector_storage.delete_embeddings_for_entity(db, "search_test", group_id)


# ============================================================================
# 4. Clear Distinction: Exact Match vs. Semantic Similarity
# ============================================================================

def test_clear_distinction_exact_match_vs_semantic_similarity():
    """
    CRITICAL REQUIREMENT:
    Clearly distinguish:
    - exact skill match
    - semantic similarity
    """
    async def _test():
        resume = make_test_resume()
        job = make_test_job()

        with SessionLocal() as db:
            matcher = SemanticMatcher(
                embed_service=EmbeddingService(provider=MockEmbeddingProvider())
            )
            result: SemanticMatchResult = await matcher.compute_semantic_match(
                db=db,
                resume=resume,
                job=job,
            )

            # 1. Exact matching metrics (Phase 15)
            assert "Python" in result.exact_matched_skills
            assert "FastAPI" in result.exact_matched_skills
            assert "PostgreSQL" in result.exact_matched_skills
            assert any("Kafka" in s for s in result.missing_required_skills)
            assert result.exact_skills_match_rate == 0.75

            # 2. Semantic similarity metrics (Phase 16)
            assert 0.0 <= result.overall_semantic_similarity <= 1.0
            assert result.experience_semantic_alignment > 0.0
            assert len(result.requirement_matches) > 0

            # 3. Verify granular requirement matches exhibit semantic evidence
            for match in result.requirement_matches:
                assert match.requirement != ""
                assert match.best_matching_resume_chunk != ""
                assert match.similarity_score >= 0.0
                assert match.relevance_tier in ("strong_alignment", "moderate_alignment", "minimal_alignment")

    asyncio.run(_test())


# ============================================================================
# 5. Ethical AI & Non-Evaluative Compliance Tests
# ============================================================================

def test_non_evaluative_no_hiring_probability_claims():
    """
    CRITICAL REQUIREMENT:
    Do not present semantic similarity as a definitive hiring probability.
    """
    async def _test():
        resume = make_test_resume()
        job = make_test_job()

        with SessionLocal() as db:
            matcher = SemanticMatcher(
                embed_service=EmbeddingService(provider=MockEmbeddingProvider())
            )
            result = await matcher.compute_semantic_match(db=db, resume=resume, job=job)

            # Validate mandatory disclaimer
            assert result.disclaimer == SEMANTIC_DISCLAIMER
            assert "not represent candidate qualification" in result.disclaimer.lower()

            # Ensure no hiring probability language in narrative
            forbidden_phrases = [
                "probability of hiring",
                "chance of being hired",
                "will be hired",
                "guaranteed interview",
                "should be hired",
                "hiring probability",
            ]
            insights_lower = result.semantic_insights.lower()
            for phrase in forbidden_phrases:
                assert phrase not in insights_lower

    asyncio.run(_test())


# ============================================================================
# 6. REST API Endpoint Tests: POST /api/jobs/semantic-match
# ============================================================================

def test_api_semantic_match_endpoint_success():
    """Validates POST /api/jobs/semantic-match with structured payload."""
    resume = make_test_resume()
    job = make_test_job()

    payload = {
        "resume": resume.model_dump(),
        "job_description": job.model_dump(),
    }

    response = client.post("/api/jobs/semantic-match", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "overall_semantic_similarity" in data
    assert "experience_semantic_alignment" in data
    assert "requirement_matches" in data
    assert "exact_matched_skills" in data
    assert "missing_required_skills" in data
    assert "exact_skills_match_rate" in data
    assert "semantic_insights" in data
    assert "disclaimer" in data

    # Verify separation
    assert isinstance(data["exact_matched_skills"], list)
    assert isinstance(data["overall_semantic_similarity"], float)
    assert data["model_name"] == "text-embedding-004"
    assert data["vector_dimension"] == 768


def test_api_semantic_match_endpoint_with_raw_text():
    """Validates POST /api/jobs/semantic-match with raw text inputs."""
    payload = {
        "resume_text": "Alex Mercer\nSenior Backend Engineer\nSkills: Python, FastAPI, PostgreSQL\nExperience: Built microservices at Acme",
        "job_text": "Job Title: Backend Developer\nRequirements:\n- Python\n- PostgreSQL\n- Kafka\nExperience: 4+ years",
    }

    response = client.post("/api/jobs/semantic-match", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["overall_semantic_similarity"] > 0.0
    assert len(data["requirement_matches"]) > 0


def test_api_semantic_match_endpoint_empty_payload_returns_400():
    """Validates 400 Bad Request on empty payload."""
    response = client.post("/api/jobs/semantic-match", json={})
    assert response.status_code == 400
