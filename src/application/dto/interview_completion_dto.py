"""Interview completion result DTO."""

from dataclasses import dataclass
from typing import Any

from ...domain.models.interview import Interview
from .detailed_feedback_dto import DetailedInterviewFeedback


@dataclass
class InterviewCompletionResult:
    """Result of interview completion with detailed feedback.

    This DTO encapsulates both the completed interview entity and its
    detailed evaluation feedback. Both fields are always present (never None).

    Attributes:
        interview: Completed interview entity with status=COMPLETE
        summary: Detailed interview feedback with comprehensive evaluation data
            (DetailedInterviewFeedback DTO containing per-question evaluations,
            aggregate metrics, gap progression, and LLM recommendations)
    """

    interview: Interview
    summary: DetailedInterviewFeedback

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization.

        Returns:
            Dictionary with interview_id, status, and detailed feedback
        """
        return {
            "interview_id": str(self.interview.id),
            "status": self.interview.status.value,
            "summary": self.summary.model_dump(mode="json"),
        }
