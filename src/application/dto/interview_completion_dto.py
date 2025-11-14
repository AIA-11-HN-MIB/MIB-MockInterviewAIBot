"""Interview completion result DTO."""

from dataclasses import dataclass
from typing import Any

from ...domain.models.interview import Interview


@dataclass
class InterviewCompletionResult:
    """Result of interview completion with comprehensive summary.

    This DTO encapsulates both the completed interview entity and its
    generated summary. Both fields are always present (never None).

    Attributes:
        interview: Completed interview entity with status=COMPLETE
        summary: Comprehensive interview summary dict containing:
            - interview_id: str
            - overall_score: float
            - theoretical_score_avg: float
            - speaking_score_avg: float
            - total_questions: int
            - total_follow_ups: int
            - question_summaries: list[dict]
            - gap_progression: dict
            - strengths: list[str]
            - weaknesses: list[str]
            - study_recommendations: list[str]
            - technique_tips: list[str]
            - completion_time: str (ISO format)
    """

    interview: Interview
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization.

        Returns:
            Dictionary with interview_id, status, and full summary
        """
        return {
            "interview_id": str(self.interview.id),
            "status": self.interview.status.value,
            "summary": self.summary,
        }
