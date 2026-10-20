"""
Embedding Service & Provider Layer (Phase 16).
Generates dense vector embeddings for:
- resume summary
- resume experience / project descriptions
- job description overview
- job requirements
Integrates content-hash caching via VectorStorage to avoid regenerating unchanged embeddings.
"""
import os
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.schemas.parsed_resume import Resume, Experience, Project
from backend.app.schemas.job_description import JobDescription
from backend.app.services.vector_storage import vector_storage, compute_content_hash

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 768
DEFAULT_MODEL_NAME = "text-embedding-004"


class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for text embedding models.
    """

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generates a 768-dimensional normalized embedding vector for a single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for multiple texts."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    High-fidelity deterministic embedding provider for unit tests, offline environments,
    and fallback when remote LLM quotas are reached.
    Produces unit-normalized 768-dimensional vectors that maintain semantic keyword affinity.
    """

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions

    def _generate_vector(self, text: str) -> List[float]:
        if not text or not text.strip():
            # Return zero-like normalized vector
            vec = np.ones(self.dimensions, dtype=np.float32) / np.sqrt(self.dimensions)
            return vec.tolist()

        cleaned = text.lower().strip()
        words = [w for w in cleaned.split() if len(w) > 1]

        # Base seed from content SHA-256 for deterministic reproducibility
        content_int = int(hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.RandomState(content_int % (2**31 - 1))
        base_vector = rng.normal(0.0, 1.0, self.dimensions).astype(np.float32)

        # Word-level semantic bias: identical tokens across different sentences boost dot product
        word_vector = np.zeros(self.dimensions, dtype=np.float32)
        if words:
            for w in words:
                w_seed = int(hashlib.md5(w.encode("utf-8")).hexdigest()[:8], 16)
                w_rng = np.random.RandomState(w_seed % (2**31 - 1))
                word_vector += w_rng.normal(0.0, 1.0, self.dimensions).astype(np.float32)
            word_vector /= np.sqrt(len(words))
            combined = 0.15 * base_vector + 0.85 * word_vector
        else:
            combined = base_vector

        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        else:
            combined = np.ones(self.dimensions, dtype=np.float32) / np.sqrt(self.dimensions)

        return combined.tolist()

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Production embedding provider using Google Gemini's text-embedding-004.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL_NAME,
        dimensions: int = EMBEDDING_DIMENSIONS,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.dimensions = dimensions
        self._fallback_provider = MockEmbeddingProvider(dimensions=dimensions)
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI client for embeddings: %s", e)

    async def embed_text(self, text: str) -> List[float]:
        if not self._client:
            return await self._fallback_provider.embed_text(text)

        try:
            # Synchronous client call wrapped in thread or direct call
            response = self._client.models.embed_content(
                model=self.model_name,
                contents=text,
            )
            if response and response.embedding and response.embedding.values:
                vals = response.embedding.values[:self.dimensions]
                # Normalize vector to unit length
                arr = np.array(vals, dtype=np.float32)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm
                return arr.tolist()
        except Exception as e:
            logger.warning(
                "Gemini embedding API call failed (%s). Falling back to deterministic provider.",
                e,
            )

        return await self._fallback_provider.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results = []
        for t in texts:
            results.append(await self.embed_text(t))
        return results


class EmbeddingService:
    """
    Orchestrates embedding generation, caching, and structured entity vectorization.
    Prevents regenerating embeddings unnecessarily when text content has not changed.
    """

    def __init__(
        self,
        provider: Optional[BaseEmbeddingProvider] = None,
    ):
        if provider:
            self.provider = provider
        elif settings.EMBEDDING_PROVIDER == "mock":
            self.provider = MockEmbeddingProvider()
        else:
            self.provider = GeminiEmbeddingProvider()

        self.storage = vector_storage

    async def get_or_create_embedding(
        self,
        db: Session,
        text: str,
        entity_type: str,
        entity_id: str,
        chunk_index: int = 0,
    ) -> Tuple[List[float], bool]:
        """
        Retrieves embedding from database cache if content hash matches,
        otherwise invokes provider and persists vector.
        Returns:
            Tuple of (embedding_vector, was_newly_generated_bool)
        """
        content_hash = compute_content_hash(text)

        # 1. Check existing record for this entity chunk
        existing_entity_vec = (
            db.query(vector_storage.storage_model if hasattr(vector_storage, 'storage_model') else None)
            if False else None
        )
        cached_record = self.storage.get_by_content_hash(db, content_hash)

        if cached_record:
            logger.debug(
                "Embedding cache hit for %s:%s chunk %d (hash=%s)",
                entity_type,
                entity_id,
                chunk_index,
                content_hash[:8],
            )
            # Ensure entity mapping is saved if found by hash under another entity
            if cached_record.entity_id != entity_id or cached_record.entity_type != entity_type:
                self.storage.save_embedding(
                    db=db,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    content_text=text,
                    embedding=list(cached_record.embedding),
                    chunk_index=chunk_index,
                    model_name=cached_record.model_name,
                )
            return list(cached_record.embedding), False

        # 2. Generate new embedding via provider
        logger.info(
            "Generating new embedding for %s:%s chunk %d (hash=%s)",
            entity_type,
            entity_id,
            chunk_index,
            content_hash[:8],
        )
        vec = await self.provider.embed_text(text)

        # 3. Store in PostgreSQL + pgvector
        self.storage.save_embedding(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            content_text=text,
            embedding=vec,
            chunk_index=chunk_index,
            model_name=DEFAULT_MODEL_NAME,
        )

        return vec, True

    # --------------------------------------------------------------------------
    # Entity-specific embedding helpers
    # --------------------------------------------------------------------------

    async def embed_resume_summary(
        self,
        db: Session,
        resume_id: str,
        summary: Optional[str],
    ) -> Optional[List[float]]:
        """Embeds resume summary if present."""
        if not summary or not summary.strip():
            return None
        vec, _ = await self.get_or_create_embedding(
            db=db,
            text=summary.strip(),
            entity_type="resume_summary",
            entity_id=resume_id,
            chunk_index=0,
        )
        return vec

    async def embed_resume_experiences(
        self,
        db: Session,
        resume_id: str,
        experiences: List[Experience],
    ) -> List[Tuple[int, str, List[float]]]:
        """
        Embeds each experience entry (role title, company, highlights, tech).
        Returns list of (index, text_chunk, vector).
        """
        results: List[Tuple[int, str, List[float]]] = []
        for idx, exp in enumerate(experiences):
            chunk_parts = [f"Title: {exp.title} at {exp.company}"]
            if exp.highlights:
                chunk_parts.append("Highlights: " + "; ".join(exp.highlights))
            if exp.technologies:
                chunk_parts.append("Technologies: " + ", ".join(exp.technologies))

            chunk_text = "\n".join(chunk_parts)
            vec, _ = await self.get_or_create_embedding(
                db=db,
                text=chunk_text,
                entity_type="resume_experience",
                entity_id=resume_id,
                chunk_index=idx,
            )
            results.append((idx, chunk_text, vec))
        return results

    async def embed_resume_projects(
        self,
        db: Session,
        resume_id: str,
        projects: List[Project],
    ) -> List[Tuple[int, str, List[float]]]:
        """
        Embeds each project entry (name, description, technologies).
        Returns list of (index, text_chunk, vector).
        """
        results: List[Tuple[int, str, List[float]]] = []
        for idx, proj in enumerate(projects):
            chunk_parts = [f"Project: {proj.name}"]
            if proj.description:
                chunk_parts.append(f"Description: {proj.description}")
            if proj.technologies:
                chunk_parts.append("Technologies: " + ", ".join(proj.technologies))

            chunk_text = "\n".join(chunk_parts)
            vec, _ = await self.get_or_create_embedding(
                db=db,
                text=chunk_text,
                entity_type="resume_project",
                entity_id=resume_id,
                chunk_index=idx,
            )
            results.append((idx, chunk_text, vec))
        return results

    async def embed_job_description(
        self,
        db: Session,
        job_id: str,
        job: JobDescription,
    ) -> List[float]:
        """
        Embeds overall job description overview.
        """
        overview_parts = [f"Job Title: {job.job_title}"]
        if job.company:
            overview_parts.append(f"Company: {job.company}")
        if job.responsibilities:
            overview_parts.append("Responsibilities: " + "; ".join(job.responsibilities))
        if job.tools_and_technologies:
            overview_parts.append("Tools: " + ", ".join(job.tools_and_technologies))

        overview_text = "\n".join(overview_parts)
        vec, _ = await self.get_or_create_embedding(
            db=db,
            text=overview_text,
            entity_type="job_description",
            entity_id=job_id,
            chunk_index=0,
        )
        return vec

    async def embed_job_requirements(
        self,
        db: Session,
        job_id: str,
        job: JobDescription,
    ) -> List[Tuple[int, str, List[float]]]:
        """
        Embeds individual job requirement items (required skills, qualifications, experience criteria).
        Returns list of (index, requirement_text, vector).
        """
        req_items = []
        for s in job.required_skills:
            req_items.append(f"Required Skill: {s}")
        for exp in job.experience_requirements:
            req_items.append(f"Experience Criterion: {exp}")
        for edu in job.education_requirements:
            req_items.append(f"Education Criterion: {edu}")

        if not req_items and job.tools_and_technologies:
            for t in job.tools_and_technologies:
                req_items.append(f"Technology: {t}")

        if not req_items and job.responsibilities:
            for resp in job.responsibilities[:5]:
                req_items.append(f"Core Responsibility: {resp}")

        if not req_items and job.job_title:
            req_items.append(f"Position: {job.job_title}")

        results: List[Tuple[int, str, List[float]]] = []
        for idx, req_text in enumerate(req_items):
            vec, _ = await self.get_or_create_embedding(
                db=db,
                text=req_text,
                entity_type="job_requirement",
                entity_id=job_id,
                chunk_index=idx,
            )
            results.append((idx, req_text, vec))
        return results


# Global singleton instance
embedding_service = EmbeddingService()
