"""Follow-up question domain model."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .question import DifficultyLevel, QuestionType


class FollowUpQuestion(BaseModel):
    """Represents an adaptive follow-up question.

    Follow-up questions are generated dynamically during interviews
    based on candidate answer gaps and similarity scores.
    """

    id: UUID = Field(default_factory=uuid4)
    parent_question_id: UUID  # Original question that triggered follow-up
    interview_id: UUID
    text: str  # The follow-up question text
    generated_reason: str  # Why this follow-up was needed (e.g., "Missing key concept: recursion")
    order_in_sequence: int  # 1st, 2nd, or 3rd follow-up for this parent question
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Required attributes for QuestionRepositoryPort compatibility
    # Follow-up questions inherit these from parent but with adaptive difficulty
    question_type: QuestionType = QuestionType.TECHNICAL  # Follow-ups are always technical deep-dives
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM  # Adaptive difficulty (can be overridden)
    skills: list[str] = Field(default_factory=list)  # Inherited from parent question
    tags: list[str] = Field(default_factory=list)  # Adaptive tagging based on gaps
    evaluation_criteria: str | None = None  # Optional evaluation guidance
    version: int = 1  # Version for tracking question evolution
    embedding: list[float] | None = None  # Vector embedding for semantic search
    ideal_answer: str | None = None  # Reference answer for similarity scoring
    rationale: str | None = None  # Why this follow-up targets specific gaps
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        frozen = False

    def is_first_followup(self) -> bool:
        """Check if this is the first follow-up for the parent question.

        Returns:
            True if order_in_sequence == 1
        """
        return self.order_in_sequence == 1

    def is_last_allowed(self) -> bool:
        """Check if this is the last allowed follow-up (max 3).

        Returns:
            True if order_in_sequence == 3
        """
        return self.order_in_sequence == 3
