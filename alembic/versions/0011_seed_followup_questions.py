"""seed follow-up questions

Revision ID: 0011
Revises: 0010
Create Date: 2025-12-11 10:00:00

Creates follow-up questions for interviews where answers had identified gaps.
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, Integer, DateTime


# revision identifiers, used by Alembic.
revision: str = '0011'
down_revision: Union[str, Sequence[str], None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed follow-up questions for interviews with answer gaps."""

    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schema for bulk insert
    follow_up_questions_table = Table(
        'follow_up_questions', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('parent_question_id', UUID(as_uuid=True)),
        Column('interview_id', UUID(as_uuid=True)),
        Column('text', Text),
        Column('generated_reason', Text),
        Column('order_in_sequence', Integer),
        Column('created_at', DateTime),
    )

    # Insert follow-up questions based on identified gaps in answers
    # Focus on answers with confirmed gaps or significant knowledge gaps
    op.bulk_insert(follow_up_questions_table, [
        # ============================================
        # Interview 1: Alice Chen (Junior) - var/let/const
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440001'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),  # var/let/const
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'text': 'You mentioned the scope differences. Can you explain what hoisting is in JavaScript and how it differs between var, let, and const?',
            'generated_reason': 'Missing key concept: hoisting behavior. The answer covered scope but did not mention how variable declarations are hoisted differently for var vs let/const.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=12, hours=2, minutes=7),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440002'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),  # var/let/const
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'text': 'What is the Temporal Dead Zone (TDZ) and how does it relate to let and const?',
            'generated_reason': 'Missing key concept: Temporal Dead Zone. The answer did not explain why accessing let/const before declaration throws a ReferenceError, which is a critical understanding gap.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=12, hours=2, minutes=8),
        },
        # ============================================
        # Interview 1: Alice Chen (Junior) - React Hooks
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440003'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),  # React Hooks
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'text': 'You mentioned useState and useEffect. Can you explain when you would use useMemo and useCallback, and what problems they solve?',
            'generated_reason': 'Missing optimization hooks: useMemo and useCallback. The answer covered basic hooks but did not demonstrate understanding of performance optimization hooks, which are important for React applications.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=12, hours=2, minutes=17),
        },
        # ============================================
        # Interview 4: David Kim (Frontend) - Event loop
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440004'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),  # Event loop
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'text': 'You mentioned the event loop phases. Can you explain the difference between the microtask queue and the macrotask queue, and how they are processed?',
            'generated_reason': 'Missing key concept: microtask vs macrotask queues. The answer covered event loop phases but did not explain the critical distinction between microtasks (Promise callbacks) and macrotasks (setTimeout), which is essential for understanding async execution order.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=6, hours=2, minutes=47),
        },
        # ============================================
        # Interview 4: David Kim (Frontend) - Async/await
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440005'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),  # Async/await
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'text': 'You explained async/await well. How would you execute multiple async operations in parallel, and what would you use for that?',
            'generated_reason': 'Missing parallel execution pattern: Promise.all. The answer covered sequential async/await usage but did not demonstrate understanding of parallel execution, which is a common optimization pattern.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=6, hours=3, minutes=13),
        },
        # ============================================
        # Interview 5: Emily Thompson (DevOps) - Microservices
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440006'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'text': 'You mentioned Kubernetes for orchestration. Can you explain what a service mesh is and how it helps with microservices communication and observability?',
            'generated_reason': 'Missing key concept: service mesh. The answer showed good understanding of microservices and Kubernetes but did not cover service mesh patterns, which are important for production microservices architectures.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=4, hours=1, minutes=8),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440007'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'text': 'How would you implement distributed tracing across microservices to debug issues that span multiple services?',
            'generated_reason': 'Missing observability pattern: distributed tracing. The answer covered microservices architecture but did not address how to trace requests across service boundaries, which is critical for debugging distributed systems.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=4, hours=1, minutes=9),
        },
        # ============================================
        # Interview 6: James Anderson (Full stack) - Garbage Collection Java
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440008'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),  # Garbage collection Java
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'text': 'You explained the generational GC model. Can you name and compare the different GC algorithms available in the JVM, such as G1, Parallel, and ZGC?',
            'generated_reason': 'Missing key knowledge: GC algorithms. The answer covered generational GC basics but did not demonstrate knowledge of different GC algorithms and their trade-offs, which is important for JVM tuning.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=2, hours=2, minutes=8),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440009'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),  # Garbage collection Java
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'text': 'How would you optimize GC pause times for a low-latency application? What strategies would you use?',
            'generated_reason': 'Missing optimization knowledge: GC pause time reduction. The answer mentioned monitoring GC logs but did not cover strategies for minimizing pause times, which is critical for latency-sensitive applications.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=2, hours=2, minutes=9),
        },
        # ============================================
        # Interview 7: Lisa Martinez (Backend) - CAP theorem
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440010'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),  # CAP theorem
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'text': 'You explained CP and AP systems well. Can you describe different consistency models, such as eventual consistency, strong consistency, and causal consistency?',
            'generated_reason': 'Missing key concept: consistency models. The answer covered CAP theorem basics but did not explain different consistency models, which are important for understanding how distributed systems handle data consistency.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=1, hours=3, minutes=8),
        },
        # ============================================
        # Interview 7: Lisa Martinez (Backend) - Python GC
        # ============================================
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440011'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),  # Python GC
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'text': 'You mentioned three generations. Can you explain in detail how the generational GC works in Python, including the threshold values and collection frequency for each generation?',
            'generated_reason': 'Missing detailed knowledge: GC generation specifics. The answer covered basic GC mechanisms but did not explain the detailed workings of generational GC, including thresholds and collection strategies, which is important for Python performance tuning.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=1, hours=3, minutes=23),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440012'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),  # Python GC
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'text': 'How would you tune Python\'s garbage collector for a high-throughput application? What gc module functions and parameters would you adjust?',
            'generated_reason': 'Missing practical knowledge: GC tuning strategies. The answer mentioned the gc module but did not demonstrate understanding of how to tune GC for performance, which is important for production Python applications.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=1, hours=3, minutes=24),
        },
    ])

    # Update interviews to include follow-up question IDs in adaptive_follow_ups array
    conn = op.get_bind()

    # Interview 1: Alice Chen - 3 follow-ups
    conn.execute(sa.text("""
        UPDATE interviews
        SET adaptive_follow_ups = ARRAY[
            'b60e8400-e29b-41d4-a716-446655440001'::uuid,
            'b60e8400-e29b-41d4-a716-446655440002'::uuid,
            'b60e8400-e29b-41d4-a716-446655440003'::uuid
        ]
        WHERE id = '960e8400-e29b-41d4-a716-446655440001'
    """))

    # Interview 4: David Kim - 2 follow-ups
    conn.execute(sa.text("""
        UPDATE interviews
        SET adaptive_follow_ups = ARRAY[
            'b60e8400-e29b-41d4-a716-446655440004'::uuid,
            'b60e8400-e29b-41d4-a716-446655440005'::uuid
        ]
        WHERE id = '960e8400-e29b-41d4-a716-446655440004'
    """))

    # Interview 5: Emily Thompson - 2 follow-ups
    conn.execute(sa.text("""
        UPDATE interviews
        SET adaptive_follow_ups = ARRAY[
            'b60e8400-e29b-41d4-a716-446655440006'::uuid,
            'b60e8400-e29b-41d4-a716-446655440007'::uuid
        ]
        WHERE id = '960e8400-e29b-41d4-a716-446655440005'
    """))

    # Interview 6: James Anderson - 2 follow-ups
    conn.execute(sa.text("""
        UPDATE interviews
        SET adaptive_follow_ups = ARRAY[
            'b60e8400-e29b-41d4-a716-446655440008'::uuid,
            'b60e8400-e29b-41d4-a716-446655440009'::uuid
        ]
        WHERE id = '960e8400-e29b-41d4-a716-446655440006'
    """))

    # Interview 7: Lisa Martinez - 3 follow-ups
    conn.execute(sa.text("""
        UPDATE interviews
        SET adaptive_follow_ups = ARRAY[
            'b60e8400-e29b-41d4-a716-446655440010'::uuid,
            'b60e8400-e29b-41d4-a716-446655440011'::uuid,
            'b60e8400-e29b-41d4-a716-446655440012'::uuid
        ]
        WHERE id = '960e8400-e29b-41d4-a716-446655440007'
    """))

    print("[OK] Seeded 12 follow-up questions across 5 interviews")
    print("[OK] Updated interview adaptive_follow_ups arrays")


def downgrade() -> None:
    """Remove seeded follow-up questions and clear interview arrays."""
    conn = op.get_bind()

    # Clear adaptive_follow_ups from interviews
    conn.execute(sa.text("""
        UPDATE interviews
        SET adaptive_follow_ups = ARRAY[]::uuid[]
        WHERE id IN (
            '960e8400-e29b-41d4-a716-446655440001',
            '960e8400-e29b-41d4-a716-446655440004',
            '960e8400-e29b-41d4-a716-446655440005',
            '960e8400-e29b-41d4-a716-446655440006',
            '960e8400-e29b-41d4-a716-446655440007'
        )
    """))

    # Delete follow-up questions
    conn.execute(sa.text("""
        DELETE FROM follow_up_questions WHERE id IN (
            'b60e8400-e29b-41d4-a716-446655440001',
            'b60e8400-e29b-41d4-a716-446655440002',
            'b60e8400-e29b-41d4-a716-446655440003',
            'b60e8400-e29b-41d4-a716-446655440004',
            'b60e8400-e29b-41d4-a716-446655440005',
            'b60e8400-e29b-41d4-a716-446655440006',
            'b60e8400-e29b-41d4-a716-446655440007',
            'b60e8400-e29b-41d4-a716-446655440008',
            'b60e8400-e29b-41d4-a716-446655440009',
            'b60e8400-e29b-41d4-a716-446655440010',
            'b60e8400-e29b-41d4-a716-446655440011',
            'b60e8400-e29b-41d4-a716-446655440012'
        )
    """))

    print("[OK] Removed seeded follow-up questions and cleared interview arrays")

