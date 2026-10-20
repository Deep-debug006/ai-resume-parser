"""add error_message to resumes

Revision ID: e7381f9a2024
Revises: dcce1e7d0014
Create Date: 2026-10-03 09:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7381f9a2024'
down_revision: Union[str, None] = 'dcce1e7d0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add error_message column if not present
    op.add_column('resumes', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('resumes', 'error_message')
