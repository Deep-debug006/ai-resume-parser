"""
Unit tests for LLM service and multi-provider abstraction (Phase 9).
All tests use MockLLMProvider or mocking to avoid live API dependencies.
"""
import pytest
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from backend.app.services.llm_service import (
    LLMService,
    MockLLMProvider,
    LLMValidationError,
    LLMProviderError,
    extract_json_from_text,
)


class DummyCandidate(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(...)
    years_experience: int = Field(..., ge=0)
    skills: List[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Email must contain '@'")
        return v.lower()


def test_extract_json_from_various_formats():
    """Verify robust JSON extraction from clean JSON, markdown blocks, and surrounding text."""
    # Clean JSON
    res1 = extract_json_from_text('{"name": "Alice", "role": "Engineer"}')
    assert res1 == {"name": "Alice", "role": "Engineer"}

    # Markdown code fence with ```json
    markdown_json = "```json\n{\n  \"status\": \"success\",\n  \"score\": 98\n}\n```"
    res2 = extract_json_from_text(markdown_json)
    assert res2 == {"status": "success", "score": 98}

    # Text preamble and trailing commentary
    wrapped_json = "Here is your extracted data:\n```\n{\"candidate\": \"Bob\"}\n```\nHope this helps!"
    res3 = extract_json_from_text(wrapped_json)
    assert res3 == {"candidate": "Bob"}

    # Empty text raises ValueError
    with pytest.raises(ValueError, match="empty response"):
        extract_json_from_text("   ")


def test_mock_provider_returns_canned_responses():
    """Verify MockLLMProvider responds with queued responses."""
    provider = MockLLMProvider(responses=[
        {"custom_key": 42},
        '{"text_key": "hello"}',
    ])
    assert provider.provider_name == "mock"

    import asyncio
    r1 = asyncio.run(provider.generate_json("prompt 1"))
    assert r1 == {"custom_key": 42}

    r2 = asyncio.run(provider.generate_json("prompt 2"))
    assert r2 == {"text_key": "hello"}


def test_llm_service_successful_validation_first_attempt():
    """Verify standard extraction succeeds and returns validated Pydantic model with 0 repairs."""
    valid_payload = {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.org",
        "years_experience": 8,
        "skills": ["Python", "FastAPI", "Docker"],
    }
    mock_provider = MockLLMProvider(responses=[valid_payload])
    service = LLMService(provider=mock_provider, max_repair_retries=2)

    import asyncio
    model, repair_count = asyncio.run(
        service.generate_structured(
            prompt="Extract candidate info",
            system_instruction="Strict extraction",
            schema_class=DummyCandidate,
        )
    )

    assert isinstance(model, DummyCandidate)
    assert model.name == "Sarah Connor"
    assert model.email == "sarah@cyberdyne.org"
    assert model.years_experience == 8
    assert repair_count == 0
    assert len(mock_provider.call_history) == 1


def test_llm_service_controlled_repair_loop_succeeds():
    """
    Verify controlled repair:
    1st attempt: invalid email and negative years_experience
    2nd attempt (repair): valid corrected payload
    Result: successfully validated with repair_count == 1.
    """
    invalid_payload = {
        "name": "Sarah Connor",
        "email": "invalid-email-no-at-sign",
        "years_experience": -5,  # Violates ge=0
        "skills": ["Python"],
    }
    corrected_payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "years_experience": 5,
        "skills": ["Python"],
    }

    mock_provider = MockLLMProvider(responses=[invalid_payload, corrected_payload])
    service = LLMService(provider=mock_provider, max_repair_retries=2)

    import asyncio
    model, repair_count = asyncio.run(
        service.generate_structured(
            prompt="Extract candidate",
            system_instruction="Strict extraction",
            schema_class=DummyCandidate,
        )
    )

    assert repair_count == 1
    assert model.email == "sarah.connor@example.com"
    assert model.years_experience == 5
    assert len(mock_provider.call_history) == 2

    # Verify that the second prompt included the repair feedback
    repair_prompt = mock_provider.call_history[1]["prompt"]
    assert "VALIDATION ERROR DETECTED ON PREVIOUS ATTEMPT" in repair_prompt
    assert "REPAIR INSTRUCTIONS" in repair_prompt


def test_llm_service_fails_gracefully_when_max_retries_exceeded():
    """Verify LLMValidationError is raised when all repair attempts fail."""
    always_invalid = {
        "name": "X",  # min_length=2 violation
        "email": "no-at",
        "years_experience": -1,
    }
    mock_provider = MockLLMProvider(responses=[
        always_invalid,
        always_invalid,
        always_invalid,
    ])
    service = LLMService(provider=mock_provider, max_repair_retries=2)

    import asyncio
    with pytest.raises(LLMValidationError) as exc_info:
        asyncio.run(
            service.generate_structured(
                prompt="Extract candidate",
                system_instruction="Strict extraction",
                schema_class=DummyCandidate,
            )
        )

    assert "Failed to validate DummyCandidate after 2 repair retries" in str(exc_info.value)
    assert exc_info.value.validation_errors is not None


def test_provider_factory_creation():
    """Verify LLMService factory correctly resolves supported providers."""
    mock_p = LLMService.create_provider("mock")
    assert mock_p.provider_name == "mock"

    gemini_p = LLMService.create_provider("gemini", api_key="dummy_key", model="gemini-2.5-flash")
    assert gemini_p.provider_name == "gemini"
    assert gemini_p.model_name == "gemini-2.5-flash"

    openai_p = LLMService.create_provider("openai", api_key="dummy_key", model="gpt-4o-mini")
    assert openai_p.provider_name == "openai"
    assert openai_p.model_name == "gpt-4o-mini"

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMService.create_provider("unknown_provider")
