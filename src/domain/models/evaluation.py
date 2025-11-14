"""Evaluation domain model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class GapSeverity(str, Enum):
    """Concept gap severity levels."""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class ConceptGap(BaseModel):
    """Represents a missing concept in an answer.

    Value object - identified by evaluation_id + concept.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID
    concept: str  # Missing concept (e.g., "event loop", "closure")
    severity: GapSeverity
    resolved: bool = False  # True if filled in follow-up
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        frozen = False  # Allow mutation for resolved field


class Evaluation(BaseModel):
    """Represents evaluation of an answer.

    Entity - tracks scoring, gaps, and penalties across follow-up attempts.
    """

    id: UUID = Field(default_factory=uuid4)
    answer_id: UUID
    question_id: UUID  # Main question OR follow-up question
    interview_id: UUID

    # Scores
    raw_score: float = Field(ge=0.0, le=100.0)  # LLM score before penalty
    penalty: float = Field(ge=-15.0, le=0.0, default=0.0)  # Attempt penalty
    final_score: float = Field(ge=0.0, le=100.0)  # raw_score + penalty
    similarity_score: float | None = Field(None, ge=0.0, le=1.0)  # Cosine similarity

    # LLM evaluation details
    completeness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    sentiment: str | None = None  # confident/uncertain/nervous
    reasoning: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)

    # Follow-up context
    attempt_number: int = Field(ge=1, le=3, default=1)  # 1 (main), 2-3 (follow-ups)
    parent_evaluation_id: UUID | None = None  # NULL if main question

    # Gaps (relationship)
    gaps: list[ConceptGap] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_at: datetime | None = None

    class Config:
        """Pydantic configuration."""

        frozen = False

    def apply_penalty(self, attempt_number: int) -> None:
        """Apply penalty based on attempt number.

        Penalty progression: 0 (1st) / -5 (2nd) / -15 (3rd)

        Args:
            attempt_number: 1, 2, or 3

        Raises:
            ValueError: If attempt_number not in [1, 2, 3]
        """
        if attempt_number == 1:
            self.penalty = 0.0
        elif attempt_number == 2:
            self.penalty = -5.0
        elif attempt_number == 3:
            self.penalty = -15.0
        else:
            raise ValueError(f"Invalid attempt_number: {attempt_number} (must be 1-3)")

        self.attempt_number = attempt_number
        self.final_score = max(0.0, min(100.0, self.raw_score + self.penalty))

    def has_gaps(self) -> bool:
        """Check if unresolved gaps exist.

        Returns:
            True if any gap is not resolved, False otherwise
        """
        return any(not gap.resolved for gap in self.gaps)

    def resolve_gaps(self) -> None:
        """Mark all gaps as resolved."""
        for gap in self.gaps:
            gap.resolved = True

    def is_passing(self, threshold: float = 60.0) -> bool:
        """Check if final score meets threshold.

        Args:
            threshold: Minimum score to pass (default: 60.0)

        Returns:
            True if final_score >= threshold, False otherwise
        """
        return self.final_score >= threshold

    def is_gap_resolved_by_criteria(self) -> bool:
        """Check if gaps should be considered resolved based on criteria.

        Gap resolution criteria:
        - completeness >= 0.8 OR
        - final_score >= 80 OR
        - attempt_number == 3 (max attempts reached)

        Returns:
            True if criteria met, False otherwise
        """
        return (
            self.completeness >= 0.8
            or self.final_score >= 80
            or self.attempt_number == 3
        )

    def is_adaptive_complete(self) -> bool:
        """Check if answer meets adaptive completion criteria.

        Completion criteria:
        - similarity_score >= 0.8 OR
        - no unresolved gaps (has_gaps() returns False)

        Returns:
            True if answer meets completion criteria, False otherwise
        """
        if self.similarity_score is not None and self.similarity_score >= 0.8:
            return True
        return not self.has_gaps()


@dataclass(frozen=True)
class FollowUpEvaluationContext:
    """Context for evaluating follow-up answers.

    Immutable value object passed to LLM adapters to provide context
    about previous attempts, gaps, and scores.
    """

    parent_question_id: UUID
    follow_up_question_id: UUID
    attempt_number: int  # 2 or 3
    previous_evaluations: list[Evaluation]  # All previous attempts (main + follow-ups)
    cumulative_gaps: list[ConceptGap]  # All unresolved gaps from previous attempts
    previous_scores: list[float]  # Scores from previous attempts
    parent_ideal_answer: str  # For reference

    @property
    def has_persistent_gaps(self) -> bool:
        """Check if any gaps persist across attempts.

        Returns:
            True if unresolved gaps exist, False otherwise
        """
        return len(self.cumulative_gaps) > 0

    @property
    def average_previous_score(self) -> float:
        """Calculate average score from previous attempts.

        Returns:
            Average score, or 0.0 if no previous attempts
        """
        if not self.previous_scores:
            return 0.0
        return sum(self.previous_scores) / len(self.previous_scores)

    def get_persistent_gap_concepts(self) -> list[str]:
        """Get list of persistent gap concepts.

        Returns:
            List of concept names that remain unresolved
        """
        return [gap.concept for gap in self.cumulative_gaps if not gap.resolved]
