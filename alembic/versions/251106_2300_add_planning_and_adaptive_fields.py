"""add planning and adaptive evaluation fields

Revision ID: 251106_2300
Revises: 525593eca676
Create Date: 2025-11-06 23:00:00

Changes:
- questions: ideal_answer, rationale
- interviews: plan_metadata, adaptive_follow_ups
- answers: similarity_score, gaps
- Add new follow_up_questions table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "251106_2300"
down_revision = "525593eca676"
branch_labels = None
depends_on = None


def upgrade():
    # === Questions table ===
    op.add_column(
        "questions",
        sa.Column("ideal_answer", sa.Text(), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("rationale", sa.Text(), nullable=True),
    )

    # === Interviews table ===
    op.add_column(
        "interviews",
        sa.Column(
            "plan_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "interviews",
        sa.Column(
            "adaptive_follow_ups",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            server_default="{}",
            nullable=False,
        ),
    )

    # === Answers table ===
    op.add_column(
        "answers",
        sa.Column("similarity_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "answers",
        sa.Column(
            "gaps", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # === Create follow_up_questions table ===
    op.create_table(
        "follow_up_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "parent_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interview_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("generated_reason", sa.Text(), nullable=False),
        sa.Column("order_in_sequence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # === Indexes for follow_up_questions ===
    op.create_index(
        "idx_follow_up_questions_parent_question_id",
        "follow_up_questions",
        ["parent_question_id"],
    )
    op.create_index(
        "idx_follow_up_questions_interview_id",
        "follow_up_questions",
        ["interview_id"],
    )
    op.create_index(
        "idx_follow_up_questions_created_at",
        "follow_up_questions",
        ["created_at"],
    )

    # === Constraints for answers ===
    op.create_check_constraint(
        "check_similarity_score_bounds",
        "answers",
        "similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)",
    )

    # === Indexes for answers ===
    op.create_index(
        "idx_answers_similarity_score",
        "answers",
        ["similarity_score"],
        postgresql_where=sa.text("similarity_score IS NOT NULL"),
    )
    op.create_index(
        "idx_answers_gaps",
        "answers",
        ["gaps"],
        postgresql_using="gin",
        postgresql_where=sa.text("gaps IS NOT NULL"),
    )


def downgrade():
    # Drop indexes
    op.drop_index("idx_answers_gaps", table_name="answers")
    op.drop_index("idx_answers_similarity_score", table_name="answers")
    op.drop_constraint("check_similarity_score_bounds", "answers", type_="check")

    # Drop follow_up_questions table and its indexes
    op.drop_index("idx_follow_up_questions_created_at", table_name="follow_up_questions")
    op.drop_index("idx_follow_up_questions_interview_id", table_name="follow_up_questions")
    op.drop_index("idx_follow_up_questions_parent_question_id", table_name="follow_up_questions")
    op.drop_table("follow_up_questions")

    # Drop columns (answers)
    op.drop_column("answers", "gaps")
    op.drop_column("answers", "similarity_score")

    # Drop columns (interviews)
    op.drop_column("interviews", "adaptive_follow_ups")
    op.drop_column("interviews", "plan_metadata")

    # Drop columns (questions)
    op.drop_column("questions", "rationale")
    op.drop_column("questions", "ideal_answer")
