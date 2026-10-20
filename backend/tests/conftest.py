"""
Global Pytest Configuration and Fixtures for Phase 22: Comprehensive Testing.
Ensures:
- All external dependencies (LLM, embeddings) are mocked.
- Zero dependency on remote or paid APIs (Gemini, OpenAI).
- Deterministic, fast, and repeatable test runs.
"""
import pytest
from unittest.mock import patch
from backend.app.core.config import settings
from backend.app.services.llm_service import MockLLMProvider, llm_service
from backend.app.services.embedding_service import MockEmbeddingProvider, embedding_service
from backend.app.services.job_parser_service import job_parser_service
from backend.app.services.resume_parser_service import resume_parser_service
from backend.app.services.resume_analysis_service import resume_analysis_service
from backend.app.services.semantic_matcher import semantic_matcher
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator


@pytest.fixture(autouse=True, scope="session")
def configure_test_environment():
    """Configures global settings to mock external providers for the entire test session."""
    settings.LLM_PROVIDER = "mock"
    settings.EMBEDDING_PROVIDER = "mock"
    settings.OCR_ENABLED = True


@pytest.fixture(autouse=True)
def mock_external_providers(monkeypatch):
    """
    Autouse fixture that ensures all service singletons use MockLLMProvider
    and MockEmbeddingProvider across all test modules.
    """
    mock_llm = MockLLMProvider()
    mock_emb = MockEmbeddingProvider()

    # Configure llm_service
    llm_service.provider = mock_llm
    monkeypatch.setattr(llm_service, "provider", mock_llm)

    # Configure job_parser_service
    if hasattr(job_parser_service, "llm_service") and job_parser_service.llm_service:
        job_parser_service.llm_service.provider = mock_llm
        monkeypatch.setattr(job_parser_service.llm_service, "provider", mock_llm)

    # Configure resume_parser_service
    if hasattr(resume_parser_service, "llm_service") and resume_parser_service.llm_service:
        resume_parser_service.llm_service.provider = mock_llm
        monkeypatch.setattr(resume_parser_service.llm_service, "provider", mock_llm)

    # Configure resume_analysis_service
    if hasattr(resume_analysis_service, "llm_service") and resume_analysis_service.llm_service:
        resume_analysis_service.llm_service.provider = mock_llm
        monkeypatch.setattr(resume_analysis_service.llm_service, "provider", mock_llm)

    # Configure pipeline orchestrator
    if hasattr(pipeline_orchestrator, "_llm_service") and pipeline_orchestrator._llm_service:
        pipeline_orchestrator._llm_service.provider = mock_llm
        monkeypatch.setattr(pipeline_orchestrator._llm_service, "provider", mock_llm)

    # Configure embedding services
    embedding_service.provider = mock_emb
    monkeypatch.setattr(embedding_service, "provider", mock_emb)

    if hasattr(semantic_matcher, "embedding_service") and semantic_matcher.embedding_service:
        semantic_matcher.embedding_service.provider = mock_emb
        monkeypatch.setattr(semantic_matcher.embedding_service, "provider", mock_emb)

    yield
