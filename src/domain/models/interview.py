"""Interview domain model."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class InterviewStatus(str, Enum):
    """Interview status enumeration."""

    IDLE = "IDLE"  # Waiting to start questioning
    QUESTIONING = "QUESTIONING"  # Asking a question
    EVALUATING = "EVALUATING"  # Evaluating received answer(s)
    FOLLOW_UP = "FOLLOW_UP"  # Awaiting follow-up response
    COMPLETE = "COMPLETE"  # Interview finished
    CANCELLED = "CANCELLED"  # Interview cancelled


class Interview(BaseModel):
    """Represents an interview session.

    This is the core aggregate root for the interview domain.
    It encapsulates all interview-related business logic.
    """

    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    status: InterviewStatus = InterviewStatus.IDLE
    cv_analysis_id: UUID | None = None
    question_ids: list[UUID] = Field(default_factory=list)
    answer_ids: list[UUID] = Field(default_factory=list)
    current_question_index: int = 0

    # NEW: Pre-planning metadata for adaptive interviews
    plan_metadata: dict[str, Any] = Field(default_factory=dict)  # {n, generated_at, strategy}
    adaptive_follow_ups: list[UUID] = Field(default_factory=list)  # Follow-up question IDs

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        frozen = False

    def start(self) -> None:
        """Start the interview.

        Raises:
            ValueError: If interview is not ready to start
        """
        if self.status != InterviewStatus.IDLE:
            raise ValueError(f"Cannot start interview with status: {self.status}")

        self.status = InterviewStatus.QUESTIONING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Complete the interview.

        Raises:
            ValueError: If interview is not ready to complete
        """
        if self.status != InterviewStatus.EVALUATING:
            raise ValueError(f"Cannot complete interview with status: {self.status}")
        if self.has_more_questions():
            raise ValueError("Cannot complete interview while questions remain.")

        self.status = InterviewStatus.COMPLETE
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the interview."""
        self.status = InterviewStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def mark_ready(self, cv_analysis_id: UUID) -> None:
        """Mark interview as ready after CV analysis.

        Args:
            cv_analysis_id: ID of the completed CV analysis
        """
        self.cv_analysis_id = cv_analysis_id
        self.status = InterviewStatus.IDLE
        self.updated_at = datetime.utcnow()

    def add_question(self, question_id: UUID) -> None:
        """Add a question to the interview.

        Args:
            question_id: ID of the question to add
        """
        self.question_ids.append(question_id)
        self.updated_at = datetime.utcnow()

    def add_answer(self, answer_id: UUID) -> None:
        """Add an answer to the interview.

        Args:
            answer_id: ID of the answer to add
        """
        self.answer_ids.append(answer_id)
        self.current_question_index += 1
        self.status = InterviewStatus.EVALUATING
        self.updated_at = datetime.utcnow()

    def has_more_questions(self) -> bool:
        """Check if there are more questions to ask.

        Returns:
            True if more questions remain, False otherwise
        """
        return self.current_question_index < len(self.question_ids)

    def get_current_question_id(self) -> UUID | None:
        """Get the current question ID.

        Returns:
            Current question ID or None if no questions remain
        """
        if self.has_more_questions():
            return self.question_ids[self.current_question_index]
        return None

    def get_progress_percentage(self) -> float:
        """Calculate interview progress percentage.

        Returns:
            Progress as a percentage (0-100)
        """
        if not self.question_ids:
            return 0.0
        return (self.current_question_index / len(self.question_ids)) * 100

    def is_active(self) -> bool:
        """Check if interview is currently active.

        Returns:
            True if interview is in progress, False otherwise
        """
        return self.status in {
            InterviewStatus.QUESTIONING,
            InterviewStatus.EVALUATING,
            InterviewStatus.FOLLOW_UP,
        }

    def add_adaptive_followup(self, question_id: UUID) -> None:
        """Add adaptive follow-up question to interview.

        Args:
            question_id: UUID of follow-up question

        Raises:
            ValueError: If follow-up limit exceeded (max 3 per main question)
        """
        self.adaptive_follow_ups.append(question_id)
        self.status = InterviewStatus.FOLLOW_UP
        self.updated_at = datetime.utcnow()

    def mark_follow_up_answered(self) -> None:
        """Return to evaluation after a follow-up response."""
        if self.status != InterviewStatus.FOLLOW_UP:
            raise ValueError(f"Cannot mark follow-up answered in status: {self.status}")
        self.status = InterviewStatus.EVALUATING
        self.updated_at = datetime.utcnow()

    def proceed_after_evaluation(self) -> None:
        """Advance interview after evaluation is complete."""
        if self.status != InterviewStatus.EVALUATING:
            raise ValueError(f"Cannot proceed from status: {self.status}")

        if self.has_more_questions():
            self.status = InterviewStatus.QUESTIONING
            self.updated_at = datetime.utcnow()
            return

        self.status = InterviewStatus.COMPLETE
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_planned(self) -> bool:
        """Check if interview has planning metadata.

        Returns:
            True if plan_metadata contains required keys
        """
        return "n" in self.plan_metadata and "generated_at" in self.plan_metadata

    @property
    def planned_question_count(self) -> int:
        """Get number of planned questions.

        Returns:
            Value of n from plan_metadata, or 0 if not planned
        """
        n = self.plan_metadata.get("n", 0)
        return int(n) if n is not None else 0
