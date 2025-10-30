"""Answer domain model."""

from datetime import datetime
from typing import Optional, Dict, Any
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
    sentiment: Optional[str] = None  # e.g., "confident", "uncertain"
    reasoning: Optional[str] = None  # AI explanation of the evaluation
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
    audio_file_path: Optional[str] = None  # If voice answer
    duration_seconds: Optional[float] = None  # Time taken to answer
    evaluation: Optional[AnswerEvaluation] = None
    embedding: Optional[list[float]] = None  # Vector embedding of answer
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_at: Optional[datetime] = None

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

    def get_score(self) -> Optional[float]:
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