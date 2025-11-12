"""seed additional candidates

Revision ID: 0006
Revises: 0005
Create Date: 2025-12-11 10:00:00

Adds 7 new diverse candidates for realistic interview simulation.
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed additional candidates with diverse profiles."""

    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schema for bulk insert
    candidates_table = Table(
        'candidates', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('name', String),
        Column('email', String),
        Column('cv_file_path', String),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    # Insert 7 diverse candidates
    op.bulk_insert(candidates_table, [
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'name': 'Alice Chen',
            'email': 'alice.chen@example.com',
            'cv_file_path': '/uploads/cvs/alice_chen_cv.pdf',
            'created_at': now - timedelta(days=14),
            'updated_at': now - timedelta(days=14),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'name': 'Michael Rodriguez',
            'email': 'michael.rodriguez@example.com',
            'cv_file_path': '/uploads/cvs/michael_rodriguez_cv.pdf',
            'created_at': now - timedelta(days=12),
            'updated_at': now - timedelta(days=12),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'name': 'Sarah Williams',
            'email': 'sarah.williams@example.com',
            'cv_file_path': '/uploads/cvs/sarah_williams_cv.pdf',
            'created_at': now - timedelta(days=10),
            'updated_at': now - timedelta(days=10),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'name': 'David Kim',
            'email': 'david.kim@example.com',
            'cv_file_path': '/uploads/cvs/david_kim_cv.pdf',
            'created_at': now - timedelta(days=8),
            'updated_at': now - timedelta(days=8),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),
            'name': 'Emily Thompson',
            'email': 'emily.thompson@example.com',
            'cv_file_path': '/uploads/cvs/emily_thompson_cv.pdf',
            'created_at': now - timedelta(days=6),
            'updated_at': now - timedelta(days=6),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),
            'name': 'James Anderson',
            'email': 'james.anderson@example.com',
            'cv_file_path': '/uploads/cvs/james_anderson_cv.pdf',
            'created_at': now - timedelta(days=4),
            'updated_at': now - timedelta(days=4),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
            'name': 'Lisa Martinez',
            'email': 'lisa.martinez@example.com',
            'cv_file_path': '/uploads/cvs/lisa_martinez_cv.pdf',
            'created_at': now - timedelta(days=2),
            'updated_at': now - timedelta(days=2),
        },
    ])

    print("[OK] Seeded 7 additional candidates")


def downgrade() -> None:
    """Remove seeded candidates."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM candidates WHERE id IN (
            '660e8400-e29b-41d4-a716-446655440001',
            '660e8400-e29b-41d4-a716-446655440002',
            '660e8400-e29b-41d4-a716-446655440003',
            '660e8400-e29b-41d4-a716-446655440004',
            '660e8400-e29b-41d4-a716-446655440005',
            '660e8400-e29b-41d4-a716-446655440006',
            '660e8400-e29b-41d4-a716-446655440007'
        )
    """))

    print("[OK] Removed seeded candidates")

