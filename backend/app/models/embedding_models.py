"""
SQLAlchemy ORM Model for pgvector Vector Embeddings (Phase 16).
Stores dense vector embeddings for:
- resume summary
- resume experience/project descriptions
- job description
- job requirements
With content hashing (SHA256) to eliminate redundant embedding API calls.
"""
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Index,
    func,
)
from pgvector.sqlalchemy import Vector

from backend.app.db.session import Base

# Canonical embedding dimensionality for text-embedding-004
EMBEDDING_DIMENSIONS = 768


class VectorEmbeddingModel(Base):
    """
    Dedicated pgvector table storing dense embeddings and content hashes.
    Enables cosine distance queries using pgvector's `<=>` operator.
    """
    __tablename__ = "vector_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False, index=True)  # resume_summary, resume_experience, resume_project, job_description, job_requirement
    entity_id = Column(String(64), nullable=False, index=True)    # resume_id, job_id, or parent document ID
    chunk_index = Column(Integer, default=0, nullable=False)     # sub-index for multi-part records (e.g. experience bullet 0, 1...)
    content_hash = Column(String(64), nullable=False, index=True) # SHA-256 hex digest of the normalized content text
    content_text = Column(Text, nullable=False)                  # raw text representation that was embedded
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    model_name = Column(String(100), default="text-embedding-004", nullable=False)
    dimensions = Column(Integer, default=EMBEDDING_DIMENSIONS, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_vec_entity_lookup", "entity_type", "entity_id", "chunk_index"),
        Index("idx_vec_content_hash", "content_hash"),
    )
