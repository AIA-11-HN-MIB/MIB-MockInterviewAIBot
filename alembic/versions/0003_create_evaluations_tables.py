"""Create evaluations and evaluation_gaps tables

Revision ID: 0003
Revises: 0002
Create Date: 2025-11-14 02:23:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create evaluations and evaluation_gaps tables, migrate data from answers."""

    # Step 1: Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Scores
        sa.Column('raw_score', sa.Float(), nullable=False),
        sa.Column('penalty', sa.Float(), nullable=False, server_default='0'),
        sa.Column('final_score', sa.Float(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),

        # LLM evaluation details
        sa.Column('completeness', sa.Float(), nullable=False),
        sa.Column('relevance', sa.Float(), nullable=False),
        sa.Column('sentiment', sa.String(50), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('strengths', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('weaknesses', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('improvement_suggestions', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),

        # Follow-up context
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_evaluation_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_evaluation_id'], ['evaluations.id'], ondelete='SET NULL'),
    )

    # Indexes for evaluations
    op.create_index('idx_evaluations_answer_id', 'evaluations', ['answer_id'])
    op.create_index('idx_evaluations_question_id', 'evaluations', ['question_id'])
    op.create_index('idx_evaluations_interview_id', 'evaluations', ['interview_id'])
    op.create_index('idx_evaluations_parent_id', 'evaluations', ['parent_evaluation_id'])
    op.create_index('idx_evaluations_attempt_number', 'evaluations', ['attempt_number'])

    # Constraints for evaluations
    op.create_check_constraint(
        'check_raw_score_bounds',
        'evaluations',
        'raw_score >= 0 AND raw_score <= 100'
    )
    op.create_check_constraint(
        'check_penalty_bounds',
        'evaluations',
        'penalty >= -15 AND penalty <= 0'
    )
    op.create_check_constraint(
        'check_final_score_bounds',
        'evaluations',
        'final_score >= 0 AND final_score <= 100'
    )
    op.create_check_constraint(
        'check_similarity_score_bounds',
        'evaluations',
        'similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)'
    )
    op.create_check_constraint(
        'check_completeness_bounds',
        'evaluations',
        'completeness >= 0 AND completeness <= 1'
    )
    op.create_check_constraint(
        'check_relevance_bounds',
        'evaluations',
        'relevance >= 0 AND relevance <= 1'
    )
    op.create_check_constraint(
        'check_attempt_number_bounds',
        'evaluations',
        'attempt_number >= 1 AND attempt_number <= 3'
    )

    # Step 2: Create evaluation_gaps table
    op.create_table(
        'evaluation_gaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('concept', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default="'moderate'"),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),

        # Foreign key
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
    )

    # Indexes for evaluation_gaps
    op.create_index('idx_evaluation_gaps_evaluation_id', 'evaluation_gaps', ['evaluation_id'])
    op.create_index('idx_evaluation_gaps_resolved', 'evaluation_gaps', ['resolved'])

    # Constraint for evaluation_gaps
    op.create_check_constraint(
        'check_severity_values',
        'evaluation_gaps',
        "severity IN ('minor', 'moderate', 'major')"
    )

    # Step 3: Add evaluation_id column to answers table
    op.add_column('answers', sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_answers_evaluation_id',
        'answers', 'evaluations',
        ['evaluation_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_answers_evaluation_id', 'answers', ['evaluation_id'])

    # Step 4: Migrate existing data from answers.evaluation JSONB to evaluations table
    # This uses raw SQL because SQLAlchemy ORM doesn't handle JSONB migration well
    connection = op.get_bind()

    # Migration SQL (using PostgreSQL JSONB functions)
    migration_sql = """
    -- Insert evaluations from answers.evaluation JSONB
    INSERT INTO evaluations (
        id, answer_id, question_id, interview_id,
        raw_score, penalty, final_score, similarity_score,
        completeness, relevance, sentiment, reasoning,
        strengths, weaknesses, improvement_suggestions,
        attempt_number, parent_evaluation_id,
        created_at, evaluated_at
    )
    SELECT
        gen_random_uuid() as id,
        a.id as answer_id,
        a.question_id,
        a.interview_id,

        -- Extract score from JSONB (raw_score = final_score for old data)
        COALESCE((a.evaluation->>'score')::FLOAT, 0.0) as raw_score,
        0.0 as penalty,  -- No penalty for old data
        COALESCE((a.evaluation->>'score')::FLOAT, 0.0) as final_score,
        a.similarity_score,

        -- Extract evaluation details from JSONB
        COALESCE((a.evaluation->>'completeness')::FLOAT, 0.5) as completeness,
        COALESCE((a.evaluation->>'relevance')::FLOAT, 0.5) as relevance,
        a.evaluation->>'sentiment' as sentiment,
        a.evaluation->>'reasoning' as reasoning,

        -- Convert JSONB arrays to PostgreSQL arrays
        COALESCE(
            ARRAY(SELECT jsonb_array_elements_text(a.evaluation->'strengths')),
            ARRAY[]::TEXT[]
        ) as strengths,
        COALESCE(
            ARRAY(SELECT jsonb_array_elements_text(a.evaluation->'weaknesses')),
            ARRAY[]::TEXT[]
        ) as weaknesses,
        COALESCE(
            ARRAY(SELECT jsonb_array_elements_text(a.evaluation->'improvement_suggestions')),
            ARRAY[]::TEXT[]
        ) as improvement_suggestions,

        1 as attempt_number,  -- Assume main question for old data
        NULL as parent_evaluation_id,

        a.created_at,
        a.evaluated_at
    FROM answers a
    WHERE a.evaluation IS NOT NULL;
    """

    connection.execute(sa.text(migration_sql))

    # Step 5: Migrate gaps from answers.gaps JSONB to evaluation_gaps table
    gaps_migration_sql = """
    -- Insert gaps from answers.gaps JSONB
    INSERT INTO evaluation_gaps (id, evaluation_id, concept, severity, resolved, created_at)
    SELECT
        gen_random_uuid() as id,
        e.id as evaluation_id,
        gap_concept.value as concept,
        COALESCE(a.gaps->>'severity', 'moderate') as severity,
        FALSE as resolved,  -- Old gaps not resolved
        a.created_at
    FROM answers a
    JOIN evaluations e ON e.answer_id = a.id
    CROSS JOIN LATERAL jsonb_array_elements_text(a.gaps->'concepts') as gap_concept(value)
    WHERE a.gaps IS NOT NULL
      AND a.gaps->'concepts' IS NOT NULL
      AND jsonb_array_length(a.gaps->'concepts') > 0;
    """

    connection.execute(sa.text(gaps_migration_sql))

    # Step 6: Update answers.evaluation_id to link to new evaluations
    update_fk_sql = """
    UPDATE answers a
    SET evaluation_id = e.id
    FROM evaluations e
    WHERE e.answer_id = a.id;
    """

    connection.execute(sa.text(update_fk_sql))

    # Step 7: Drop old columns from answers table (after verification)
    # Keep them for now to allow rollback
    # op.drop_column('answers', 'evaluation')
    # op.drop_column('answers', 'similarity_score')
    # op.drop_column('answers', 'gaps')
    # op.drop_column('answers', 'evaluated_at')


def downgrade() -> None:
    """Revert migration - restore old JSONB structure."""

    connection = op.get_bind()

    # Step 1: Recreate old columns if they were dropped
    # (Skip if columns still exist)

    # Step 2: Migrate data back from evaluations to answers.evaluation JSONB
    rollback_sql = """
    -- Restore evaluation JSONB
    UPDATE answers a
    SET
        evaluation = (
            SELECT jsonb_build_object(
                'score', e.raw_score,
                'completeness', e.completeness,
                'relevance', e.relevance,
                'sentiment', e.sentiment,
                'reasoning', e.reasoning,
                'strengths', to_jsonb(e.strengths),
                'weaknesses', to_jsonb(e.weaknesses),
                'improvement_suggestions', to_jsonb(e.improvement_suggestions)
            )
            FROM evaluations e
            WHERE e.answer_id = a.id
        ),
        similarity_score = (
            SELECT e.similarity_score
            FROM evaluations e
            WHERE e.answer_id = a.id
        ),
        gaps = (
            SELECT jsonb_build_object(
                'concepts', COALESCE(jsonb_agg(g.concept), '[]'::jsonb),
                'severity', COALESCE(MIN(g.severity), 'moderate'),
                'confirmed', COALESCE(BOOL_OR(NOT g.resolved), false)
            )
            FROM evaluation_gaps g
            WHERE g.evaluation_id = (
                SELECT e.id FROM evaluations e WHERE e.answer_id = a.id
            )
        ),
        evaluated_at = (
            SELECT e.evaluated_at
            FROM evaluations e
            WHERE e.answer_id = a.id
        )
    WHERE EXISTS (
        SELECT 1 FROM evaluations e WHERE e.answer_id = a.id
    );
    """

    connection.execute(sa.text(rollback_sql))

    # Step 3: Drop new tables
    op.drop_index('idx_answers_evaluation_id', 'answers')
    op.drop_constraint('fk_answers_evaluation_id', 'answers', type_='foreignkey')
    op.drop_column('answers', 'evaluation_id')

    op.drop_table('evaluation_gaps')
    op.drop_table('evaluations')
