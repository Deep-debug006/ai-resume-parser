"""add pgvector extension and vector_embeddings table

Revision ID: f3a81b9c2025
Revises: e7381f9a2024
Create Date: 2026-10-06 02:22:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'f3a81b9c2025'
down_revision: Union[str, None] = 'e7381f9a2024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create vector_embeddings table
    op.create_table(
        'vector_embeddings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(64), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False, server_default='text-embedding-004'),
        sa.Column('dimensions', sa.Integer(), nullable=False, server_default='768'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 3. Create indices for fast lookup & filtering
    op.create_index('idx_vec_entity_lookup', 'vector_embeddings', ['entity_type', 'entity_id', 'chunk_index'])
    op.create_index('idx_vec_content_hash', 'vector_embeddings', ['content_hash'])
    op.create_index('idx_vec_entity_type', 'vector_embeddings', ['entity_type'])
    op.create_index('idx_vec_entity_id', 'vector_embeddings', ['entity_id'])

    # 4. Create HNSW vector cosine similarity index
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vec_embedding_cosine "
        "ON vector_embeddings USING hnsw (embedding vector_cosine_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_vec_embedding_cosine;")
    op.drop_index('idx_vec_entity_id', table_name='vector_embeddings')
    op.drop_index('idx_vec_entity_type', table_name='vector_embeddings')
    op.drop_index('idx_vec_content_hash', table_name='vector_embeddings')
    op.drop_index('idx_vec_entity_lookup', table_name='vector_embeddings')
    op.drop_table('vector_embeddings')
