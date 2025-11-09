"""seed data for planning and adaptive fields

Revision ID: 0004
Revises: 0003
Create Date: 2025-11-08 23:01:57.944002

Seed sample data for new columns:
- questions: ideal_answer, rationale
- interviews: plan_metadata (already has default {})
- answers: similarity_score, gaps
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed data for new planning and adaptive fields."""

    conn = op.get_bind()

    # === Seed Questions table ===
    # Update existing questions with ideal_answer and rationale
    conn.execute(text("""
        UPDATE questions
        SET
            ideal_answer = CASE
                WHEN question_type = 'technical' THEN
                    'A comprehensive answer should cover: ' ||
                    CASE
                        WHEN text ILIKE '%OOP%' OR text ILIKE '%object%oriented%' THEN 'classes, objects, inheritance, polymorphism, encapsulation, abstraction'
                        WHEN text ILIKE '%database%' OR text ILIKE '%sql%' THEN 'data modeling, ACID properties, indexing, query optimization'
                        WHEN text ILIKE '%algorithm%' THEN 'time complexity, space complexity, trade-offs, real-world applications'
                        ELSE 'technical concepts, best practices, and practical implementation'
                    END
                WHEN question_type = 'behavioral' THEN
                    'Use STAR method: Situation, Task, Action, Result. Provide specific examples with measurable outcomes.'
                WHEN question_type = 'situational' THEN
                    'Demonstrate problem-solving approach: understand problem, consider options, make decision, explain rationale.'
                ELSE 'Provide detailed, structured response with examples.'
            END,
            rationale = CASE
                WHEN question_type = 'technical' THEN
                    'Assesses technical knowledge and ability to explain complex concepts clearly.'
                WHEN question_type = 'behavioral' THEN
                    'Evaluates past behavior as predictor of future performance and cultural fit.'
                WHEN question_type = 'situational' THEN
                    'Tests problem-solving skills and decision-making process under hypothetical scenarios.'
                ELSE 'Evaluates candidate competency in relevant domain.'
            END
        WHERE ideal_answer IS NULL OR rationale IS NULL
    """))

    # === Seed Answers table ===
    # Calculate similarity scores for existing answers (mock values for demo)
    conn.execute(text("""
        UPDATE answers
        SET
            similarity_score = CASE
                WHEN LENGTH(text) > 200 THEN 0.85 + (RANDOM() * 0.15)
                WHEN LENGTH(text) > 100 THEN 0.70 + (RANDOM() * 0.15)
                WHEN LENGTH(text) > 50 THEN 0.60 + (RANDOM() * 0.10)
                ELSE 0.40 + (RANDOM() * 0.20)
            END,
            gaps = CASE
                WHEN LENGTH(text) < 100 THEN
                    '{"missing_concepts": ["detail", "examples"], "improvement_areas": ["depth", "clarity"]}'::jsonb
                WHEN LENGTH(text) < 200 THEN
                    '{"missing_concepts": ["advanced_details"], "improvement_areas": ["specificity"]}'::jsonb
                ELSE
                    '{"missing_concepts": [], "improvement_areas": []}'::jsonb
            END
        WHERE similarity_score IS NULL OR gaps IS NULL
    """))

    print("[OK] Seeded ideal answers and rationale for questions")
    print("[OK] Seeded similarity scores and gaps for answers")


def downgrade() -> None:
    """Clear seeded data."""

    conn = op.get_bind()

    # Clear seeded data (set to NULL)
    conn.execute(text("""
        UPDATE questions
        SET ideal_answer = NULL, rationale = NULL
    """))

    conn.execute(text("""
        UPDATE answers
        SET similarity_score = NULL, gaps = NULL
    """))

    print("[OK] Cleared seeded data for new columns")
