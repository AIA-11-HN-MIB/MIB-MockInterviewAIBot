"""Clear all data and seed candidates in Vietnamese

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-15 00:00:00
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Clear all database data and seed candidates in Vietnamese."""

    conn = op.get_bind()
    metadata = MetaData()
    now = datetime.utcnow()

    # Clear all data in reverse dependency order
    print("[INFO] Clearing all database data...")

    # Delete in reverse order of dependencies
    conn.execute(sa.text("DELETE FROM follow_up_questions"))
    conn.execute(sa.text("DELETE FROM evaluation_gaps"))
    conn.execute(sa.text("DELETE FROM evaluations"))
    conn.execute(sa.text("DELETE FROM answers"))
    conn.execute(sa.text("DELETE FROM interviews"))
    conn.execute(sa.text("DELETE FROM cv_analyses"))
    conn.execute(sa.text("DELETE FROM questions"))
    conn.execute(sa.text("DELETE FROM candidates"))

    print("[OK] All data cleared")

    # Define table schema for candidates
    candidates_table = Table(
        'candidates', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('name', String),
        Column('email', String),
        Column('cv_file_path', String),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    # =============================================
    # SEED DATA - CANDIDATES (Vietnamese)
    # =============================================
    op.bulk_insert(candidates_table, [
        {
            'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'name': 'Nguyễn Văn A',
            'email': 'nguyen.van.a@example.com',
            'cv_file_path': '/uploads/cvs/nguyen_van_a_cv.pdf',
            'created_at': now - timedelta(days=30),
            'updated_at': now - timedelta(days=30),
        },
        {
            'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'name': 'Trần Thị B',
            'email': 'tran.thi.b@example.com',
            'cv_file_path': '/uploads/cvs/tran_thi_b_cv.pdf',
            'created_at': now - timedelta(days=25),
            'updated_at': now - timedelta(days=25),
        },
        {
            'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'name': 'Lê Văn C',
            'email': 'le.van.c@example.com',
            'cv_file_path': '/uploads/cvs/le_van_c_cv.pdf',
            'created_at': now - timedelta(days=20),
            'updated_at': now - timedelta(days=20),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'name': 'Phạm Thị D',
            'email': 'pham.thi.d@example.com',
            'cv_file_path': '/uploads/cvs/pham_thi_d_cv.pdf',
            'created_at': now - timedelta(days=14),
            'updated_at': now - timedelta(days=14),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'name': 'Hoàng Văn E',
            'email': 'hoang.van.e@example.com',
            'cv_file_path': '/uploads/cvs/hoang_van_e_cv.pdf',
            'created_at': now - timedelta(days=12),
            'updated_at': now - timedelta(days=12),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'name': 'Vũ Thị F',
            'email': 'vu.thi.f@example.com',
            'cv_file_path': '/uploads/cvs/vu_thi_f_cv.pdf',
            'created_at': now - timedelta(days=10),
            'updated_at': now - timedelta(days=10),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'name': 'Đỗ Văn G',
            'email': 'do.van.g@example.com',
            'cv_file_path': '/uploads/cvs/do_van_g_cv.pdf',
            'created_at': now - timedelta(days=8),
            'updated_at': now - timedelta(days=8),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),
            'name': 'Bùi Thị H',
            'email': 'bui.thi.h@example.com',
            'cv_file_path': '/uploads/cvs/bui_thi_h_cv.pdf',
            'created_at': now - timedelta(days=6),
            'updated_at': now - timedelta(days=6),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),
            'name': 'Ngô Văn I',
            'email': 'ngo.van.i@example.com',
            'cv_file_path': '/uploads/cvs/ngo_van_i_cv.pdf',
            'created_at': now - timedelta(days=4),
            'updated_at': now - timedelta(days=4),
        },
        {
            'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
            'name': 'Đặng Thị K',
            'email': 'dang.thi.k@example.com',
            'cv_file_path': '/uploads/cvs/dang_thi_k_cv.pdf',
            'created_at': now - timedelta(days=2),
            'updated_at': now - timedelta(days=2),
        },
    ])

    print("[OK] Seeded 10 candidates (Vietnamese)")


def downgrade() -> None:
    """Downgrade - delete seeded candidates."""
    conn = op.get_bind()

    print("[INFO] Removing seeded candidates...")
    conn.execute(sa.text("DELETE FROM candidates"))

    print("[OK] Candidates removed")

