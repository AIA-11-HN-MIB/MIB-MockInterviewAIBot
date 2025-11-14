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
    NOTE: Evaluation moved to separate Evaluation entity (linked via evaluation_id).
    """

    id: UUID = Field(default_factory=uuid4)
    interview_id: UUID
    question_id: UUID
    candidate_id: UUID
    text: str  # The actual answer text
    is_voice: bool = False  # Whether answer was given via voice
    audio_file_path: str | None = None  # If voice answer
    duration_seconds: float | None = None  # Time taken to answer
    embedding: list[float] | None = None  # Vector embedding of answer
    metadata: dict[str, Any] = Field(default_factory=dict)  # Additional context

    # UPDATED: Link to separate Evaluation entity (Phase 1 refactoring)
    evaluation_id: UUID | None = None  # FK to evaluations table

    # REMOVED: evaluation, similarity_score, gaps, speaking_score, overall_score
    # These fields now exist in Evaluation entity

    # KEEP: Voice metrics (will be stored in Evaluation entity in future)
    voice_metrics: dict[str, float] | None = None  # Voice quality metrics from STT

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        frozen = False

    def is_evaluated(self) -> bool:
        """Check if answer has been evaluated.

        Returns:
            True if evaluation_id is set, False otherwise
        """
        return self.evaluation_id is not None

    def is_complete(self) -> bool:
        """Check if answer is considered complete.

        Returns:
            True if answer has content
        """
        return bool(self.text and len(self.text.strip()) > 0)

    def has_voice_metrics(self) -> bool:
        """Check if voice metrics are available.

        Returns:
            True if voice metrics exist
        """
        return self.voice_metrics is not None and len(self.voice_metrics) > 0

    def get_voice_metrics(self) -> dict[str, float] | None:
        """Get voice metrics if available.

        Returns:
            Voice metrics dict or None
        """
        return self.voice_metrics
