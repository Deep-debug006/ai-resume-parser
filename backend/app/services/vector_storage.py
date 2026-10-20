"""
Vector Storage Abstraction Layer (Phase 16).
Provides an interface for storing, caching, and querying dense vector embeddings in PostgreSQL with pgvector.

Core Responsibilities:
1. Content-hash based deduplication (SHA-256) to avoid regenerating embeddings unnecessarily.
2. Efficient vector persistence in pgvector tables.
3. Cosine distance similarity search using pgvector's `<=>` operator (or in-memory fallback).
4. Entity-level vector retrieval and lifecycle management.
"""
import hashlib
import logging
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from backend.app.models.embedding_models import (
    VectorEmbeddingModel,
    EMBEDDING_DIMENSIONS,
)

logger = logging.getLogger(__name__)


def compute_content_hash(text: str) -> str:
    """
    Computes deterministic SHA-256 hex digest for input text.
    Normalizes whitespace to ensure consistent hashing.
    """
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    In-memory cosine similarity calculation for validation, offline testing, and mock fallbacks.
    Returns value between -1.0 and 1.0 (typically 0.0 to 1.0 for normalized embeddings).
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    similarity = float(np.dot(a, b) / (norm_a * norm_b))
    return max(0.0, min(1.0, similarity))


class VectorStorage:
    """
    Abstract storage orchestrator for vector embeddings in PostgreSQL + pgvector.
    """

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions

    def get_by_content_hash(
        self,
        db: Session,
        content_hash: str,
    ) -> Optional[VectorEmbeddingModel]:
        """
        Retrieves any existing vector matching this content hash.
        Used to prevent duplicate embedding API generation.
        """
        return (
            db.query(VectorEmbeddingModel)
            .filter(VectorEmbeddingModel.content_hash == content_hash)
            .first()
        )

    def get_embeddings_for_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> List[VectorEmbeddingModel]:
        """
        Returns all vector chunks associated with a specific entity (e.g. resume or job).
        """
        return (
            db.query(VectorEmbeddingModel)
            .filter(
                and_(
                    VectorEmbeddingModel.entity_type == entity_type,
                    VectorEmbeddingModel.entity_id == entity_id,
                )
            )
            .order_by(VectorEmbeddingModel.chunk_index.asc())
            .all()
        )

    def save_embedding(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
        content_text: str,
        embedding: List[float],
        chunk_index: int = 0,
        model_name: str = "text-embedding-004",
    ) -> VectorEmbeddingModel:
        """
        Stores or updates an embedding for an entity chunk.
        Avoids database updates if content hash has not changed.
        """
        content_hash = compute_content_hash(content_text)

        # Check if record for this specific entity chunk already exists
        existing = (
            db.query(VectorEmbeddingModel)
            .filter(
                and_(
                    VectorEmbeddingModel.entity_type == entity_type,
                    VectorEmbeddingModel.entity_id == entity_id,
                    VectorEmbeddingModel.chunk_index == chunk_index,
                )
            )
            .first()
        )

        if existing:
            if existing.content_hash == content_hash:
                logger.debug(
                    "Content hash unchanged for %s:%s chunk %d; skipping update.",
                    entity_type,
                    entity_id,
                    chunk_index,
                )
                return existing
            # Update existing
            existing.content_text = content_text
            existing.content_hash = content_hash
            existing.embedding = embedding
            existing.model_name = model_name
            existing.dimensions = len(embedding)
            db.commit()
            db.refresh(existing)
            return existing

        # Create new record
        record = VectorEmbeddingModel(
            entity_type=entity_type,
            entity_id=entity_id,
            chunk_index=chunk_index,
            content_hash=content_hash,
            content_text=content_text,
            embedding=embedding,
            model_name=model_name,
            dimensions=len(embedding),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def search_similar(
        self,
        db: Session,
        query_vector: List[float],
        entity_type: Optional[str] = None,
        filter_entity_ids: Optional[List[str]] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> List[Tuple[VectorEmbeddingModel, float]]:
        """
        Executes pgvector cosine similarity search.
        Cosine distance in pgvector is calculated using `<=>`.
        Cosine similarity = 1.0 - cosine_distance.
        Includes graceful in-memory vector math fallback.
        """
        try:
            distance_col = VectorEmbeddingModel.embedding.cosine_distance(query_vector).label("distance")
            query = db.query(VectorEmbeddingModel, distance_col)

            if entity_type:
                query = query.filter(VectorEmbeddingModel.entity_type == entity_type)

            if filter_entity_ids:
                query = query.filter(VectorEmbeddingModel.entity_id.in_(filter_entity_ids))

            # Order by closest distance (smallest distance = highest similarity)
            results = query.order_by(distance_col.asc()).limit(limit).all()

            scored_results: List[Tuple[VectorEmbeddingModel, float]] = []
            for record, dist in results:
                # Distance ranges from 0.0 (identical) to 2.0 (opposite)
                sim = max(0.0, min(1.0, 1.0 - float(dist)))
                if sim >= min_similarity:
                    scored_results.append((record, round(sim, 4)))

            return scored_results
        except Exception as e:
            logger.warning(
                "pgvector query failed (%s); falling back to in-memory cosine distance.",
                e,
            )
            query = db.query(VectorEmbeddingModel)
            if entity_type:
                query = query.filter(VectorEmbeddingModel.entity_type == entity_type)
            if filter_entity_ids:
                query = query.filter(VectorEmbeddingModel.entity_id.in_(filter_entity_ids))

            all_records = query.all()
            scored: List[Tuple[VectorEmbeddingModel, float]] = []
            for rec in all_records:
                sim = compute_cosine_similarity(list(rec.embedding), query_vector)
                if sim >= min_similarity:
                    scored.append((rec, round(sim, 4)))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]

    def delete_embeddings_for_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> int:
        """
        Deletes all embeddings for an entity.
        """
        count = (
            db.query(VectorEmbeddingModel)
            .filter(
                and_(
                    VectorEmbeddingModel.entity_type == entity_type,
                    VectorEmbeddingModel.entity_id == entity_id,
                )
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return count


# Global singleton instance
vector_storage = VectorStorage()
