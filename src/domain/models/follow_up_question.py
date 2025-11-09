"""Follow-up question domain model."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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
