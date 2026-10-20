"""
LLM abstraction layer and multi-provider service (Phase 9).
Decouples LLM provider implementations (Gemini, OpenAI, Mock) from business logic.
Provides structured JSON generation, automated schema validation, and controlled repair loops.
"""
import os
import re
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, TypeVar, Tuple

from pydantic import BaseModel, ValidationError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for all LLM service failures."""
    pass


class LLMProviderError(LLMError):
    """Raised when an LLM provider returns an API or connectivity error."""
    pass


class LLMValidationError(LLMError):
    """Raised when the LLM output cannot be validated or repaired into the target schema."""
    def __init__(self, message: str, validation_errors: Optional[str] = None, raw_output: Optional[str] = None):
        super().__init__(message)
        self.validation_errors = validation_errors
        self.raw_output = raw_output


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Robust JSON parser that extracts valid JSON objects from raw LLM text,
    stripping markdown backticks and extraneous preamble if present.
    """
    if not text or not text.strip():
        raise ValueError("Received empty response from LLM; cannot extract JSON.")

    cleaned = text.strip()

    # Match ```json ... ``` or ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if code_block_match:
        cleaned = code_block_match.group(1).strip()

    # If surrounded by text, find the outermost curly braces
    if not (cleaned.startswith("{") and cleaned.endswith("}")):
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace : last_brace + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON string from LLM response: {e}") from e


class LLMProvider(ABC):
    """
    Abstract interface for LLM backends.
    Allows seamlessly swapping providers (Gemini, OpenAI, Claude, Mock) without app changes.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider service."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific model in use."""
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a prompt against the model and returns a decoded JSON dictionary.
        """
        pass


class GeminiLLMProvider(LLMProvider):
    """
    Google Gemini provider using official google-genai SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
    ):
        self._api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self._model = model or settings.GEMINI_MODEL
        self._temperature = temperature

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._api_key:
            raise LLMProviderError(
                "Gemini API key is not configured. Set the GEMINI_API_KEY environment variable."
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=self._temperature,
                response_mime_type="application/json",
            )

            # Synchronous client call wrapped for async execution
            import asyncio
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self._model,
                contents=prompt,
                config=config,
            )

            if not response or not response.text:
                raise LLMProviderError("Empty response received from Gemini API.")

            return extract_json_from_text(response.text)

        except Exception as e:
            if isinstance(e, (LLMProviderError, ValueError)):
                raise
            err_str = str(e)
            logger.error("Gemini API call failed: %s", err_str)
            raise LLMProviderError(f"Gemini API error: {err_str}") from e


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI-compatible LLM provider using asynchronous HTTP.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        base_url: str = "https://api.openai.com/v1",
    ):
        self._api_key = api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        self._model = model or settings.OPENAI_MODEL
        self._temperature = temperature
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._api_key:
            raise LLMProviderError(
                "OpenAI API key is not configured. Set the OPENAI_API_KEY environment variable."
            )

        import httpx

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                res = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                res.raise_for_status()
                data = res.json()
                raw_text = data["choices"][0]["message"]["content"]
                return extract_json_from_text(raw_text)
        except Exception as e:
            logger.error("OpenAI API call failed: %s", str(e))
            raise LLMProviderError(f"OpenAI API error: {str(e)}") from e


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for fast unit/integration testing without network dependencies or billing.
    Can return predefined responses or an automatic schema-compliant mock resume.
    """

    def __init__(
        self,
        responses: Optional[list] = None,
        model: str = "mock-model-v1",
    ):
        self._responses = list(responses) if responses else []
        self._model = model
        self.call_history: list = []

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model

    def add_response(self, response: Any) -> None:
        """Enqueue a response for the next call."""
        self._responses.append(response)

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.call_history.append({
            "prompt": prompt,
            "system_instruction": system_instruction,
            "time": time.time(),
        })

        if self._responses:
            next_resp = self._responses.pop(0)
            if isinstance(next_resp, Exception):
                raise next_resp
            if isinstance(next_resp, str):
                return extract_json_from_text(next_resp)
            if isinstance(next_resp, dict):
                return next_resp
            raise ValueError(f"Invalid mock response type: {type(next_resp)}")

        # Check if the requested schema is for ResumeAnalysisResponse
        is_analysis_request = False
        if json_schema and ("areas_for_improvement" in json_schema.get("properties", {}) or "suggestions" in json_schema.get("properties", {})):
            is_analysis_request = True
        elif system_instruction and ("Resume Analyst" in system_instruction or "resume quality criteria" in system_instruction.lower()):
            is_analysis_request = True
        elif prompt and ("areas_for_improvement" in prompt or "EVALUATE THIS RESUME" in prompt):
            is_analysis_request = True

        if is_analysis_request:
            return {
                "strengths": [
                    "Strong quantitative metrics present in work experience highlighting measurable impact.",
                    "Comprehensive technical skill organization with categorized competencies.",
                    "Direct links to relevant professional profiles provided.",
                ],
                "areas_for_improvement": [
                    "Some experience bullet points lack context on the specific business problem solved.",
                    "Professional summary could be more concise to immediately establish career focus.",
                ],
                "suggestions": [
                    "Add measurable scale indicators to earlier roles where true without inventing new metrics.",
                    "Highlight production database optimization results in the projects section.",
                ],
                "criteria_evaluations": {
                    "clarity": {
                        "criterion": "clarity",
                        "score": 8.5,
                        "observations": ["Clear, concise sentence structure throughout experience entries."],
                    },
                    "section_completeness": {
                        "criterion": "section_completeness",
                        "score": 9.0,
                        "observations": ["All essential sections (contact, summary, experience, education, skills, projects) are populated."],
                    },
                    "bullet_point_quality": {
                        "criterion": "bullet_point_quality",
                        "score": 8.0,
                        "observations": ["Bullets begin with strong action verbs like 'Architected' and 'Migrated'."],
                    },
                    "measurable_achievements": {
                        "criterion": "measurable_achievements",
                        "score": 8.0,
                        "observations": ["Includes specific metrics (e.g. 40M daily events, 28% reduction) in experience."],
                    },
                    "skill_organization": {
                        "criterion": "skill_organization",
                        "score": 8.5,
                        "observations": ["Skills are grouped logically by languages, frameworks, and databases."],
                    },
                    "project_descriptions": {
                        "criterion": "project_descriptions",
                        "score": 8.0,
                        "observations": ["Project scopes and technologies are documented clearly."],
                    },
                    "formatting_related_text_issues": {
                        "criterion": "formatting_related_text_issues",
                        "score": 9.0,
                        "observations": ["No noticeable typos or inconsistent date formats."],
                    },
                    "missing_common_information": {
                        "criterion": "missing_common_information",
                        "score": 9.5,
                        "observations": ["Full contact details, education timeframe, and locations are present."],
                    },
                },
            }

        # Check if the requested schema is for a JobDescription
        is_job_request = False
        if json_schema and ("job_title" in json_schema.get("properties", {}) or "job_title" in json_schema.get("required", [])):
            is_job_request = True
        elif system_instruction and ("JobDescription" in system_instruction or "Job Description" in system_instruction or "job description" in system_instruction):
            is_job_request = True
        elif prompt and ("JobDescription" in prompt or "job_title" in prompt):
            is_job_request = True

        if is_job_request:
            # Extract company and job_title from prompt if present
            company = "Apex Cloud Systems"
            job_title = "Senior Cloud Backend Engineer"
            if prompt:
                comp_match = re.search(r"Company:\s*([^\n\r,]+)", prompt)
                if comp_match:
                    company = comp_match.group(1).strip()
                title_match = re.search(r"Job Title:\s*([^\n\r,]+)", prompt)
                if title_match:
                    job_title = title_match.group(1).strip()

            return {
                "job_title": job_title,
                "company": company,
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "preferred_skills": ["Kubernetes", "Redis", "Terraform"],
                "education_requirements": ["Bachelor's degree in Computer Science or equivalent practical experience"],
                "experience_requirements": ["5+ years of production software engineering experience"],
                "responsibilities": [
                    "Design, implement, and maintain high-throughput RESTful microservices",
                    "Optimize PostgreSQL database queries and indexing strategies",
                ],
                "tools_and_technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"],
                "certifications": ["AWS Certified Solutions Architect"],
                "location": "San Francisco, CA (Hybrid)",
                "employment_type": "Full-time",
                "salary_range": "$160,000 - $210,000",
            }

        # Default fallback: realistic schema-compliant resume object
        return {
            "personal_info": {
                "full_name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "+1 (555) 234-5678",
                "location": "San Francisco, CA",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "github_url": "https://github.com/janedoe",
                "portfolio_url": None,
            },
            "summary": "Experienced Full-Stack Software Engineer with expertise in distributed cloud architectures.",
            "objective": None,
            "education": [
                {
                    "institution": "University of California, Berkeley",
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "start_date": "2016",
                    "end_date": "2020",
                    "gpa": 3.85,
                    "gpa_max": 4.0,
                    "honors": ["Dean's Honors List"],
                    "courses": ["Data Structures", "Algorithms", "Operating Systems"],
                }
            ],
            "skills": {
                "technical_skills": ["Microservices", "RESTful APIs", "CI/CD"],
                "programming_languages": ["Python", "TypeScript", "Go"],
                "frameworks_and_libraries": ["FastAPI", "React", "Docker"],
                "databases": ["PostgreSQL", "Redis"],
                "cloud_and_devops": ["Google Cloud Platform", "Kubernetes", "Terraform"],
                "soft_skills": ["Team Leadership", "Agile Project Management"],
                "tools": ["Git", "VS Code", "Postman"],
            },
            "experience": [
                {
                    "company": "Apex Cloud Systems",
                    "title": "Senior Software Engineer",
                    "location": "San Francisco, CA",
                    "start_date": "Jan 2021",
                    "end_date": "Present",
                    "is_current": True,
                    "highlights": [
                        "Designed and deployed high-throughput event processing pipelines handling 50k events/sec.",
                        "Reduced API p99 latency by 35% through query optimization and caching.",
                    ],
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "Redis", "GCP"],
                }
            ],
            "projects": [
                {
                    "name": "Cloud Ledger",
                    "description": "High-throughput distributed ledger tracking financial microtransactions.",
                    "url": "https://github.com/janedoe/cloud-ledger",
                    "highlights": ["Implemented zero-knowledge consensus protocol"],
                    "technologies": ["Go", "Docker", "gRPC"],
                    "start_date": "2022",
                    "end_date": "2023",
                }
            ],
            "certifications": [
                {
                    "name": "Google Cloud Professional Cloud Architect",
                    "issuer": "Google Cloud",
                    "issue_date": "2022",
                    "expiration_date": "2025",
                    "credential_id": "GCP-PCA-987654",
                    "url": None,
                }
            ],
            "achievements": [
                {
                    "title": "First Place Hackathon Winner",
                    "issuer": "Cal Hacks",
                    "date": "2019",
                    "description": "Created real-time disaster relief routing algorithm.",
                }
            ],
            "languages": ["English", "Spanish"],
            "interests": ["Open Source", "Distributed Systems"],
        }


class LLMService:
    """
    High-level LLM orchestration service.
    Handles provider selection, invocation, Pydantic validation,
    and structured repair/retry loop.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        max_repair_retries: Optional[int] = None,
    ):
        self.provider = provider or self._resolve_default_provider()
        self.max_repair_retries = (
            max_repair_retries
            if max_repair_retries is not None
            else settings.LLM_MAX_REPAIR_RETRIES
        )

    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> LLMProvider:
        """Factory method to instantiate a provider."""
        ptype = provider_type.lower().strip()
        if ptype == "gemini":
            return GeminiLLMProvider(**kwargs)
        elif ptype == "openai":
            return OpenAILLMProvider(**kwargs)
        elif ptype == "mock":
            return MockLLMProvider(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: '{provider_type}'. Allowed: 'gemini', 'openai', 'mock'")

    def _resolve_default_provider(self) -> LLMProvider:
        ptype = settings.LLM_PROVIDER.lower().strip()
        return self.create_provider(ptype)

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        schema_class: Type[T],
    ) -> Tuple[T, int]:
        """
        Executes an extraction request with Pydantic validation and controlled repair.

        Returns:
            Tuple of (validated_model_instance, repair_attempts_count)

        Raises:
            LLMValidationError: if validation fails after all repair attempts
            LLMProviderError: if provider network/quota fails
        """
        start_time = time.perf_counter()
        repair_attempts = 0
        current_prompt = prompt

        logger.info(
            "Executing structured extraction: provider=%s, model=%s, target_schema=%s, prompt_len=%d",
            self.provider.provider_name,
            self.provider.model_name,
            schema_class.__name__,
            len(prompt),
        )

        last_error_msg = ""
        last_raw_json = {}

        for attempt in range(self.max_repair_retries + 1):
            if attempt > 0:
                repair_attempts += 1
                logger.warning(
                    "Attempting structured repair %d/%d for %s",
                    repair_attempts,
                    self.max_repair_retries,
                    schema_class.__name__,
                )

            # Execute provider call
            raw_dict = await self.provider.generate_json(
                prompt=current_prompt,
                system_instruction=system_instruction,
                json_schema=schema_class.model_json_schema(),
            )
            last_raw_json = raw_dict

            # Attempt Pydantic validation
            try:
                validated_model = schema_class.model_validate(raw_dict)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    "Structured extraction successful on attempt %d: schema=%s, duration=%.2fms",
                    attempt + 1,
                    schema_class.__name__,
                    duration_ms,
                )
                return validated_model, repair_attempts

            except ValidationError as val_err:
                err_details = val_err.errors()
                err_summary_lines = []
                for e in err_details:
                    loc = " -> ".join(str(item) for item in e.get("loc", []))
                    msg = e.get("msg", "")
                    err_summary_lines.append(f"- Field '{loc}': {msg}")
                error_description = "\n".join(err_summary_lines)
                last_error_msg = error_description

                logger.warning(
                    "Pydantic validation failed on attempt %d:\n%s",
                    attempt + 1,
                    error_description,
                )

                if attempt < self.max_repair_retries:
                    # Construct controlled repair prompt
                    current_prompt = (
                        f"{prompt}\n\n"
                        f"--- VALIDATION ERROR DETECTED ON PREVIOUS ATTEMPT ---\n"
                        f"The previous output failed validation on these specific fields:\n"
                        f"{error_description}\n\n"
                        f"REPAIR INSTRUCTIONS:\n"
                        f"1. Fix only the invalid fields identified above.\n"
                        f"2. Maintain strict fidelity to original resume text—NEVER invent facts to satisfy fields.\n"
                        f"3. If information is missing, set field to null or empty list [] as allowed by schema.\n"
                        f"4. Return the complete corrected JSON object."
                    )

        # Exceeded max repair attempts
        logger.error(
            "Failed structured validation for %s after %d repair attempts.",
            schema_class.__name__,
            self.max_repair_retries,
        )
        raise LLMValidationError(
            message=f"Failed to validate {schema_class.__name__} after {self.max_repair_retries} repair retries.",
            validation_errors=last_error_msg,
            raw_output=json.dumps(last_raw_json, indent=2),
        )


# Global default service instance
llm_service = LLMService()
