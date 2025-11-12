"""Create all database tables

Revision ID: 0001
Revises:
Create Date: 2025-11-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create all tables with all columns."""

    # Create candidates table
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('cv_file_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_candidates_email', 'candidates', ['email'])
    op.create_index('idx_candidates_created_at', 'candidates', ['created_at'])

    # Create questions table
    # Note: reference_answer column is excluded (was dropped in migration 0005)
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=False),
        sa.Column('skills', postgresql.ARRAY(sa.String(100)), nullable=False, server_default='{}'),
        sa.Column('tags', postgresql.ARRAY(sa.String(100)), nullable=False, server_default='{}'),
        sa.Column('evaluation_criteria', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        # Added in 0003
        sa.Column('ideal_answer', sa.Text(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_questions_type', 'questions', ['question_type'])
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty'])
    op.create_index('idx_questions_skills', 'questions', ['skills'], postgresql_using='gin')
    op.create_index('idx_questions_tags', 'questions', ['tags'], postgresql_using='gin')

    # Create cv_analyses table
    op.create_table(
        'cv_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cv_file_path', sa.String(500), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('skills', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('work_experience_years', sa.Float(), nullable=True),
        sa.Column('education_level', sa.String(100), nullable=True),
        sa.Column('suggested_topics', postgresql.ARRAY(sa.String(200)), nullable=False, server_default='{}'),
        sa.Column('suggested_difficulty', sa.String(50), nullable=False, server_default="'medium'"),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_cv_analyses_candidate_id', 'cv_analyses', ['candidate_id'])
    op.create_index('idx_cv_analyses_created_at', 'cv_analyses', ['created_at'])

    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('cv_analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('question_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('answer_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'),
        # Added in 0003
        sa.Column('plan_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('adaptive_follow_ups', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cv_analysis_id'], ['cv_analyses.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_interviews_candidate_id', 'interviews', ['candidate_id'])
    op.create_index('idx_interviews_status', 'interviews', ['status'])
    op.create_index('idx_interviews_created_at', 'interviews', ['created_at'])

    # Create answers table
    op.create_table(
        'answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('is_voice', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('audio_file_path', sa.String(500), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('evaluation', postgresql.JSONB(), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        # Added in 0003
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_answers_interview_id', 'answers', ['interview_id'])
    op.create_index('idx_answers_question_id', 'answers', ['question_id'])
    op.create_index('idx_answers_candidate_id', 'answers', ['candidate_id'])
    op.create_index('idx_answers_created_at', 'answers', ['created_at'])
    # Indexes added in 0003
    op.create_index(
        'idx_answers_similarity_score',
        'answers',
        ['similarity_score'],
        postgresql_where=sa.text('similarity_score IS NOT NULL'),
    )
    op.create_index(
        'idx_answers_gaps',
        'answers',
        ['gaps'],
        postgresql_using='gin',
        postgresql_where=sa.text('gaps IS NOT NULL'),
    )
    # Constraint added in 0003
    op.create_check_constraint(
        'check_similarity_score_bounds',
        'answers',
        'similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)',
    )

    # Create follow_up_questions table (added in 0003)
    op.create_table(
        'follow_up_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'parent_question_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('questions.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'interview_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('interviews.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('generated_reason', sa.Text(), nullable=False),
        sa.Column('order_in_sequence', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index(
        'idx_follow_up_questions_parent_question_id',
        'follow_up_questions',
        ['parent_question_id'],
    )
    op.create_index(
        'idx_follow_up_questions_interview_id',
        'follow_up_questions',
        ['interview_id'],
    )
    op.create_index(
        'idx_follow_up_questions_created_at',
        'follow_up_questions',
        ['created_at'],
    )


def downgrade() -> None:
    """Downgrade schema - drop all tables."""
    op.drop_table('follow_up_questions')
    op.drop_table('answers')
    op.drop_table('interviews')
    op.drop_table('cv_analyses')
    op.drop_table('questions')
    op.drop_table('candidates')

