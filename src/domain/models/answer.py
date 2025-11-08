"""Answer domain model."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AnswerEvaluation(BaseModel):
    """Represents the evaluation of an answer.

    This is a value object containing evaluation metrics.
    """

    score: float = Field(ge=0.0, le=100.0)  # Score out of 100
    semantic_similarity: float = Field(ge=0.0, le=1.0)  # Similarity to reference
    completeness: float = Field(ge=0.0, le=1.0)  # How complete the answer is
    relevance: float = Field(ge=0.0, le=1.0)  # How relevant to the question
    sentiment: str | None = None  # e.g., "confident", "uncertain"
    reasoning: str | None = None  # AI explanation of the evaluation
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)

    def is_passing(self, threshold: float = 60.0) -> bool:
        """Check if answer meets passing threshold.

        Args:
            threshold: Minimum score to pass (default: 60.0)

        Returns:
            True if score meets threshold, False otherwise
        """
        return self.score >= threshold


class Answer(BaseModel):
    """Represents a candidate's answer to a question.

    This is an entity in the interview domain.
    """

    id: UUID = Field(default_factory=uuid4)
    interview_id: UUID
    question_id: UUID
    candidate_id: UUID
    text: str  # The actual answer text
    is_voice: bool = False  # Whether answer was given via voice
    audio_file_path: str | None = None  # If voice answer
    duration_seconds: float | None = None  # Time taken to answer
    evaluation: AnswerEvaluation | None = None
    embedding: list[float] | None = None  # Vector embedding of answer
    metadata: dict[str, Any] = Field(default_factory=dict)  # Additional context

    # NEW: Adaptive evaluation fields
    similarity_score: float | None = Field(
        None, ge=0.0, le=1.0
    )  # Cosine similarity vs ideal_answer
    gaps: dict[str, Any] | None = None  # Detected concept gaps {keywords: [], entities: []}

    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_at: datetime | None = None

    class Config:
        """Pydantic configuration."""

        frozen = False

    def evaluate(self, evaluation: AnswerEvaluation) -> None:
        """Evaluate the answer.

        Args:
            evaluation: Evaluation results
        """
        self.evaluation = evaluation
        self.evaluated_at = datetime.utcnow()

    def is_evaluated(self) -> bool:
        """Check if answer has been evaluated.

        Returns:
            True if evaluated, False otherwise
        """
        return self.evaluation is not None

    def get_score(self) -> float | None:
        """Get the evaluation score.

        Returns:
            Score if evaluated, None otherwise
        """
        return self.evaluation.score if self.evaluation else None

    def is_complete(self) -> bool:
        """Check if answer is considered complete.

        Returns:
            True if answer has content and optional evaluation
        """
        return bool(self.text and len(self.text.strip()) > 0)

    def has_similarity_score(self) -> bool:
        """Check if similarity score is available.

        Returns:
            True if similarity_score is set
        """
        return self.similarity_score is not None

    def has_gaps(self) -> bool:
        """Check if concept gaps were detected.

        Returns:
            True if gaps dict is present and non-empty
        """
        return self.gaps is not None and len(self.gaps) > 0

    def meets_threshold(self, similarity_threshold: float = 0.8) -> bool:
        """Check if answer meets similarity threshold.

        Args:
            similarity_threshold: Minimum similarity (default 0.8)

        Returns:
            True if similarity_score >= threshold
        """
        if not self.has_similarity_score():
            return False
        return self.similarity_score >= similarity_threshold  # type: ignore

    def is_adaptive_complete(self) -> bool:
        """Check if answer meets adaptive criteria (no follow-up needed).

        Returns:
            True if similarity >=0.8 OR no gaps detected
        """
        similarity_ok = self.similarity_score and self.similarity_score >= 0.8
        no_gaps = not self.has_gaps()

        return similarity_ok or no_gaps
