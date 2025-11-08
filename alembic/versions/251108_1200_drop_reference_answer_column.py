"""drop reference_answer column from questions table

Revision ID: 251108_1200
Revises: 251106_2300
Create Date: 2025-11-08 12:00:00

Changes:
- questions: Remove redundant reference_answer column (replaced by ideal_answer)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "251108_1200"
down_revision = "251106_2300"
branch_labels = None
depends_on = None


def upgrade():
    """Drop reference_answer column from questions table."""
    op.drop_column("questions", "reference_answer")


def downgrade():
    """Re-add reference_answer column to questions table."""
    op.add_column(
        "questions",
        sa.Column("reference_answer", sa.Text(), nullable=True),
    )
