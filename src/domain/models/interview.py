"""Interview domain model."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class InterviewStatus(str, Enum):
    """Interview status enumeration."""

    PLANNING = "PLANNING"  # Interview in planning process
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

    # State transition rules
    VALID_TRANSITIONS: dict[InterviewStatus, list[InterviewStatus]] = {
        InterviewStatus.PLANNING: [InterviewStatus.IDLE, InterviewStatus.CANCELLED],
        InterviewStatus.IDLE: [InterviewStatus.QUESTIONING, InterviewStatus.CANCELLED],
        InterviewStatus.QUESTIONING: [InterviewStatus.EVALUATING, InterviewStatus.CANCELLED],
        InterviewStatus.EVALUATING: [
            InterviewStatus.FOLLOW_UP,
            InterviewStatus.QUESTIONING,
            InterviewStatus.COMPLETE,
            InterviewStatus.CANCELLED,
        ],
        InterviewStatus.FOLLOW_UP: [InterviewStatus.EVALUATING, InterviewStatus.CANCELLED],
        InterviewStatus.COMPLETE: [],  # Terminal state
        InterviewStatus.CANCELLED: [],  # Terminal state
    }

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

    # NEW: Follow-up tracking for current session
    current_parent_question_id: UUID | None = None
    current_followup_count: int = 0

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        frozen = False

    def transition_to(self, new_status: InterviewStatus) -> None:
        """Validate and perform state transition.

        Args:
            new_status: Target status to transition to

        Raises:
            ValueError: If transition is invalid
        """
        if new_status not in self.VALID_TRANSITIONS.get(self.status, []):
            raise ValueError(
                f"Invalid transition: {self.status} → {new_status}. "
                f"Valid transitions from {self.status}: {self.VALID_TRANSITIONS.get(self.status, [])}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def mark_idle(self, cv_analysis_id: UUID) -> None:
        """Mark interview as idle after planning is complete.
        """
        self.transition_to(InterviewStatus.IDLE)
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """Start the interview.

        Raises:
            ValueError: If interview is not ready to start
        """

        self.transition_to(InterviewStatus.QUESTIONING)
        now = datetime.utcnow()
        self.started_at = now
        self.updated_at = now

    def mark_evaluating(self) -> None:
        """Mark interview as evaluating after an answer is added.
        """
        self.transition_to(InterviewStatus.EVALUATING)
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Complete the interview.

        Raises:
            ValueError: If interview is not ready to complete
        """

        self.transition_to(InterviewStatus.COMPLETE)
        now = datetime.utcnow()
        self.completed_at = now
        self.updated_at = now

    def cancel(self) -> None:
        """Cancel the interview."""
        self.transition_to(InterviewStatus.CANCELLED)
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

    def ask_followup(self, followup_id: UUID, parent_question_id: UUID) -> None:
        """Add follow-up question with count tracking.

        Args:
            followup_id: UUID of follow-up question
            parent_question_id: UUID of main question that spawned this follow-up

        Raises:
            ValueError: If max 3 follow-ups per question exceeded
        """
        # Handle parent question change
        if self.current_parent_question_id != parent_question_id:
            self.current_parent_question_id = parent_question_id
            self.current_followup_count = 1
        else:
            # Same parent, increment counter
            if self.current_followup_count >= 3:
                raise ValueError(
                    f"Max 3 follow-ups per question. Current: {self.current_followup_count}"
                )
            self.current_followup_count += 1

        self.adaptive_follow_ups.append(followup_id)
        self.transition_to(InterviewStatus.FOLLOW_UP)
        self.updated_at = datetime.utcnow()

    def answer_followup(self) -> None:
        """Record follow-up answered, return to evaluation.

        Raises:
            ValueError: If not in FOLLOW_UP state
        """
        if self.status != InterviewStatus.FOLLOW_UP:
            raise ValueError(f"Not in FOLLOW_UP state: {self.status}")
        self.transition_to(InterviewStatus.EVALUATING)
        self.updated_at = datetime.utcnow()

    def can_ask_more_followups(self) -> bool:
        """Check if more follow-ups allowed for current parent question.

        Returns:
            True if more follow-ups can be asked (count < 3), False otherwise
        """
        return self.current_followup_count < 3

    def add_adaptive_followup(self, question_id: UUID) -> None:
        """Add adaptive follow-up question to interview.

        DEPRECATED: Use ask_followup() instead for proper count tracking.

        Args:
            question_id: UUID of follow-up question

        Raises:
            ValueError: If follow-up limit exceeded (max 3 per main question)
        """
        self.adaptive_follow_ups.append(question_id)
        self.transition_to(InterviewStatus.FOLLOW_UP)
        self.updated_at = datetime.utcnow()

    def mark_follow_up_answered(self) -> None:
        """Return to evaluation after a follow-up response.

        DEPRECATED: Use answer_followup() instead.
        """
        if self.status != InterviewStatus.FOLLOW_UP:
            raise ValueError(f"Cannot mark follow-up answered in status: {self.status}")
        self.transition_to(InterviewStatus.EVALUATING)
        self.updated_at = datetime.utcnow()

    def proceed_to_next_question(self) -> None:
        """Move to next question or complete interview.

        Resets follow-up tracking when advancing to next main question.

        Raises:
            ValueError: If not in EVALUATING state
        """
        if self.status != InterviewStatus.EVALUATING:
            raise ValueError(f"Cannot proceed from status: {self.status}")

        # Reset follow-up tracking
        self.current_parent_question_id = None
        self.current_question_index += 1
        self.current_followup_count = 0
        now = datetime.utcnow()

        if self.has_more_questions():
            self.transition_to(InterviewStatus.QUESTIONING)
            self.updated_at = now
        else:
            self.transition_to(InterviewStatus.COMPLETE)
            self.completed_at = now
            self.updated_at = now

    def proceed_after_evaluation(self) -> None:
        """Advance interview after evaluation is complete.

        DEPRECATED: Use proceed_to_next_question() instead for proper counter reset.
        """
        if self.status != InterviewStatus.EVALUATING:
            raise ValueError(f"Cannot proceed from status: {self.status}")

        if self.has_more_questions():
            self.transition_to(InterviewStatus.QUESTIONING)
            return

        self.transition_to(InterviewStatus.COMPLETE)
        now = datetime.utcnow()
        self.completed_at = now
        self.updated_at = now

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
