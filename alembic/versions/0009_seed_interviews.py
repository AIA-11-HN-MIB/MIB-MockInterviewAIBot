"""seed interviews

Revision ID: 0009
Revises: 0008
Create Date: 2025-12-11 10:00:00

Creates 10 interview sessions with various states for realistic simulation.
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import String, Integer, DateTime


# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, Sequence[str], None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed interviews with various states."""

    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schema for bulk insert
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
        Column('started_at', DateTime),
        Column('completed_at', DateTime),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    # Mix of existing questions (from 0002) and new questions (from 0007)
    # Existing question IDs from 0002: 650e8400-e29b-41d4-a716-446655440001 to 023
    # New question IDs from 0007: 760e8400-e29b-41d4-a716-446655440001 to 018

    # Insert 10 interviews with various states
    op.bulk_insert(interviews_table, [
        # 1. Completed interview - Alice Chen (Junior, easy questions)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),  # Alice Chen
            'status': 'completed',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440001'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),  # var/let/const (existing)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),  # React Hooks (existing)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),  # Unit/Integration/E2E testing (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440017'),  # Learning new tech (existing)
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
            'adaptive_follow_ups': [],
            'started_at': now - timedelta(days=12, hours=2),
            'completed_at': now - timedelta(days=12, hours=2, minutes=35),
            'created_at': now - timedelta(days=12),
            'updated_at': now - timedelta(days=12, hours=2, minutes=35),
        },
        # 2. Completed interview - Michael Rodriguez (Mid-level, medium questions)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),  # Michael Rodriguez
            'status': 'completed',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440001'),  # Dependency injection (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440003'),  # Hash tables (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440004'),  # Auth/Authz (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),  # SOLID principles (existing)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440014'),  # Prioritization (new)
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
            'started_at': now - timedelta(days=10, hours=3),
            'completed_at': now - timedelta(days=10, hours=3, minutes=48),
            'created_at': now - timedelta(days=10),
            'updated_at': now - timedelta(days=10, hours=3, minutes=48),
        },
        # 3. Completed interview - Sarah Williams (Senior, hard questions)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),  # Sarah Williams
            'status': 'completed',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440003'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices vs Monolith (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),  # CAP theorem (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),  # Event loop (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),  # Caching strategy (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),  # System design 1M req/s (existing)
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
            'started_at': now - timedelta(days=8, hours=1),
            'completed_at': now - timedelta(days=8, hours=1, minutes=52),
            'created_at': now - timedelta(days=8),
            'updated_at': now - timedelta(days=8, hours=1, minutes=52),
        },
        # 4. Completed interview - David Kim (Frontend specialist)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),  # David Kim
            'status': 'completed',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440004'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),  # React Hooks (existing)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),  # Event loop (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),  # Testing types (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),  # Async/await (existing)
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
            'adaptive_follow_ups': [],
            'started_at': now - timedelta(days=6, hours=2, minutes=30),
            'completed_at': now - timedelta(days=6, hours=3, minutes=15),
            'created_at': now - timedelta(days=6),
            'updated_at': now - timedelta(days=6, hours=3, minutes=15),
        },
        # 5. In-progress interview - Emily Thompson (DevOps)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),  # Emily Thompson
            'status': 'in_progress',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440005'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440018'),  # Horizontal vs Vertical scaling (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440011'),  # Docker (existing)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),  # Caching strategy (new)
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
            'adaptive_follow_ups': [],
            'started_at': now - timedelta(days=4, hours=1),
            'completed_at': None,
            'created_at': now - timedelta(days=4),
            'updated_at': now - timedelta(days=4, hours=1, minutes=25),
        },
        # 6. In-progress interview - James Anderson (Full stack)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),  # James Anderson
            'status': 'in_progress',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440006'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),  # Garbage collection Java (existing)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440006'),  # SQL vs NoSQL (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440010'),  # Database indexing (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),  # SOLID (existing)
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
            'adaptive_follow_ups': [],
            'started_at': now - timedelta(days=2, hours=2),
            'completed_at': None,
            'created_at': now - timedelta(days=2),
            'updated_at': now - timedelta(days=2, hours=2, minutes=12),
        },
        # 7. In-progress interview - Lisa Martinez (Backend)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),  # Lisa Martinez
            'status': 'in_progress',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440007'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),  # CAP theorem (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),  # Python GC (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),  # Caching strategy (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440004'),  # Python closures (existing)
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
            'adaptive_follow_ups': [],
            'started_at': now - timedelta(days=1, hours=3),
            'completed_at': None,
            'created_at': now - timedelta(days=1),
            'updated_at': now - timedelta(days=1, hours=3, minutes=38),
        },
        # 8. Ready interview - Alice Chen (second interview)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440008'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),  # Alice Chen
            'status': 'ready',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440001'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440002'),  # REST API (existing)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),  # Testing types (new)
                uuid.UUID('650e8400-e29b-41d4-a716-446655440005'),  # List comprehension (existing)
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
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(hours=2),
            'updated_at': now - timedelta(hours=2),
        },
        # 9. Ready interview - Michael Rodriguez (second interview)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440009'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),  # Michael Rodriguez
            'status': 'ready',
            'cv_analysis_id': uuid.UUID('860e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('760e8400-e29b-41d4-a716-446655440006'),  # SQL vs NoSQL (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440010'),  # Database indexing (new)
                uuid.UUID('760e8400-e29b-41d4-a716-446655440012'),  # Difficult team member (new)
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
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(hours=1),
            'updated_at': now - timedelta(hours=1),
        },
        # 10. Preparing interview - David Kim (second interview)
        {
            'id': uuid.UUID('960e8400-e29b-41d4-a716-446655440010'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),  # David Kim
            'status': 'preparing',
            'cv_analysis_id': None,  # CV analysis in progress
            'question_ids': [],
            'answer_ids': [],
            'current_question_index': 0,
            'plan_metadata': {},
            'adaptive_follow_ups': [],
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(minutes=30),
            'updated_at': now - timedelta(minutes=30),
        },
    ])

    print("[OK] Seeded 10 interviews (4 completed, 3 in-progress, 2 ready, 1 preparing)")


def downgrade() -> None:
    """Remove seeded interviews."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM interviews WHERE id IN (
            '960e8400-e29b-41d4-a716-446655440001',
            '960e8400-e29b-41d4-a716-446655440002',
            '960e8400-e29b-41d4-a716-446655440003',
            '960e8400-e29b-41d4-a716-446655440004',
            '960e8400-e29b-41d4-a716-446655440005',
            '960e8400-e29b-41d4-a716-446655440006',
            '960e8400-e29b-41d4-a716-446655440007',
            '960e8400-e29b-41d4-a716-446655440008',
            '960e8400-e29b-41d4-a716-446655440009',
            '960e8400-e29b-41d4-a716-446655440010'
        )
    """))

    print("[OK] Removed seeded interviews")

