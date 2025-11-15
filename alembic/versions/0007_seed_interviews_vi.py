"""Seed interviews in Vietnamese

Revision ID: 0007
Revises: 0006
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
revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed interviews in Vietnamese."""

    metadata = MetaData()
    now = datetime.utcnow()

    interviews_table = Table(
        'interviews', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('candidate_id', UUID(as_uuid=True)),
        Column('status', String),
        Column('cv_analysis_id', UUID(as_uuid=True)),
        Column('question_ids', ARRAY(UUID(as_uuid=True))),
        Column('answer_ids', ARRAY(UUID(as_uuid=True))),
        Column('current_question_index', Integer),
        Column('plan_metadata', JSONB),
        Column('adaptive_follow_ups', ARRAY(UUID(as_uuid=True))),
        Column('current_parent_question_id', UUID(as_uuid=True)),
        Column('current_followup_count', Integer),
        Column('started_at', DateTime),
        Column('completed_at', DateTime),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    # =============================================
    # SEED DATA - INTERVIEWS (Vietnamese)
    # =============================================
    interviews_data = [
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'status': 'COMPLETE',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440001'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),
            ],
            'answer_ids': [
                uuid.UUID('950e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440002'),
            ],
            'current_question_index': 2,
            'plan_metadata': {},
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=28),
            'completed_at': now - timedelta(days=28) + timedelta(minutes=30),
            'created_at': now - timedelta(days=28),
            'updated_at': now - timedelta(days=28) + timedelta(minutes=30),
        },
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'status': 'COMPLETE',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440004'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440006'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440016'),
            ],
            'answer_ids': [
                uuid.UUID('950e8400-e29b-41d4-a716-446655440003'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440004'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440006'),
            ],
            'current_question_index': 4,
            'plan_metadata': {},
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=23),
            'completed_at': now - timedelta(days=23) + timedelta(minutes=45),
            'created_at': now - timedelta(days=23),
            'updated_at': now - timedelta(days=23) + timedelta(minutes=45),
        },
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'status': 'QUESTIONING',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440003'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440014'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440018'),
            ],
            'answer_ids': [
                uuid.UUID('950e8400-e29b-41d4-a716-446655440007'),
            ],
            'current_question_index': 1,
            'plan_metadata': {},
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=18),
            'completed_at': None,
            'created_at': now - timedelta(days=18),
            'updated_at': now - timedelta(days=18) + timedelta(minutes=20),
        },
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'status': 'IDLE',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440009'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440013'),
            ],
            'answer_ids': [],
            'current_question_index': 0,
            'plan_metadata': {},
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(days=15),
            'updated_at': now - timedelta(days=15),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'status': 'COMPLETE',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440001'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440017'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440002'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440003'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440004'),
            ],
            'current_question_index': 4,
            'plan_metadata': {
                'n': 4,
                'generated_at': (now - timedelta(days=12)).isoformat(),
                'strategy': 'beginner_focused',
                'difficulty': 'easy',
            },
            'adaptive_follow_ups': [
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440002'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440003'),
            ],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=12, hours=2),
            'completed_at': now - timedelta(days=12, hours=2, minutes=35),
            'created_at': now - timedelta(days=12),
            'updated_at': now - timedelta(days=12, hours=2, minutes=35),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'status': 'COMPLETE',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440003'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440004'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440014'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440006'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440007'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440008'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440009'),
            ],
            'current_question_index': 5,
            'plan_metadata': {
                'n': 5,
                'generated_at': (now - timedelta(days=10)).isoformat(),
                'strategy': 'balanced_technical',
                'difficulty': 'medium',
            },
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=10, hours=3),
            'completed_at': now - timedelta(days=10, hours=3, minutes=48),
            'created_at': now - timedelta(days=10),
            'updated_at': now - timedelta(days=10, hours=3, minutes=48),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'status': 'COMPLETE',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440003'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440011'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440012'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440013'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440014'),
            ],
            'current_question_index': 5,
            'plan_metadata': {
                'n': 5,
                'generated_at': (now - timedelta(days=8)).isoformat(),
                'strategy': 'senior_design_focused',
                'difficulty': 'hard',
            },
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=8, hours=1),
            'completed_at': now - timedelta(days=8, hours=1, minutes=52),
            'created_at': now - timedelta(days=8),
            'updated_at': now - timedelta(days=8, hours=1, minutes=52),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'status': 'COMPLETE',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440004'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440015'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440016'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440017'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440018'),
            ],
            'current_question_index': 4,
            'plan_metadata': {
                'n': 4,
                'generated_at': (now - timedelta(days=6)).isoformat(),
                'strategy': 'frontend_focused',
                'difficulty': 'medium',
            },
            'adaptive_follow_ups': [
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440004'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440005'),
            ],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=6, hours=2, minutes=30),
            'completed_at': now - timedelta(days=6, hours=3, minutes=15),
            'created_at': now - timedelta(days=6),
            'updated_at': now - timedelta(days=6, hours=3, minutes=15),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),
            'status': 'FOLLOW_UP',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440005'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440018'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440011'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440019'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440020'),
            ],
            'current_question_index': 2,
            'plan_metadata': {
                'n': 4,
                'generated_at': (now - timedelta(days=4)).isoformat(),
                'strategy': 'devops_infrastructure',
                'difficulty': 'hard',
            },
            'adaptive_follow_ups': [
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440006'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440007'),
            ],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=4, hours=1),
            'completed_at': None,
            'created_at': now - timedelta(days=4),
            'updated_at': now - timedelta(days=4, hours=1, minutes=25),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),
            'status': 'FOLLOW_UP',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440006'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440006'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440021'),
            ],
            'current_question_index': 1,
            'plan_metadata': {
                'n': 4,
                'generated_at': (now - timedelta(days=2)).isoformat(),
                'strategy': 'java_backend_focused',
                'difficulty': 'easy',
            },
            'adaptive_follow_ups': [
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440008'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440009'),
            ],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=2, hours=2),
            'completed_at': None,
            'created_at': now - timedelta(days=2),
            'updated_at': now - timedelta(days=2, hours=2, minutes=12),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
            'status': 'FOLLOW_UP',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440007'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440004'),
            ],
            'answer_ids': [
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440022'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440023'),
                uuid.UUID('a60e8400-e29b-41d4-a716-446655440024'),
            ],
            'current_question_index': 3,
            'plan_metadata': {
                'n': 5,
                'generated_at': (now - timedelta(days=1)).isoformat(),
                'strategy': 'senior_backend_design',
                'difficulty': 'hard',
            },
            'adaptive_follow_ups': [
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440011'),
                uuid.UUID('b60e8400-e29b-41d4-a716-446655440012'),
            ],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': now - timedelta(days=1, hours=3),
            'completed_at': None,
            'created_at': now - timedelta(days=1),
            'updated_at': now - timedelta(days=1, hours=3, minutes=38),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440008'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'status': 'IDLE',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440001'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440002'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440005'),
            ],
            'answer_ids': [],
            'current_question_index': 0,
            'plan_metadata': {
                'n': 3,
                'generated_at': (now - timedelta(hours=2)).isoformat(),
                'strategy': 'follow_up_basics',
                'difficulty': 'easy',
            },
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(hours=2),
            'updated_at': now - timedelta(hours=2),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440009'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'status': 'IDLE',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440006'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('760e8400-e29b-41d4-a716-446655440012'),
            ],
            'answer_ids': [],
            'current_question_index': 0,
            'plan_metadata': {
                'n': 3,
                'generated_at': (now - timedelta(hours=1)).isoformat(),
                'strategy': 'database_deep_dive',
                'difficulty': 'medium',
            },
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(hours=1),
            'updated_at': now - timedelta(hours=1),
        },
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440010'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'status': 'IDLE',
            'cv_analysis_id': None,
            'question_ids': [],
            'answer_ids': [],
            'current_question_index': 0,
            'plan_metadata': {},
            'adaptive_follow_ups': [],
            'current_parent_question_id': None,
            'current_followup_count': 0,
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(minutes=30),
            'updated_at': now - timedelta(minutes=30),
        },
    ]

    op.bulk_insert(interviews_table, interviews_data)
    print("[OK] Seeded 14 interviews (Vietnamese)")


def downgrade() -> None:
    """Downgrade - delete seeded interviews."""
    conn = op.get_bind()

    print("[INFO] Removing seeded interviews...")
    conn.execute(sa.text("DELETE FROM interviews"))

    print("[OK] Interviews removed")

