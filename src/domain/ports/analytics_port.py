"""Analytics port interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..models.answer import Answer
from ..models.question import Question


class AnalyticsPort(ABC):
    """Interface for analytics and reporting operations.

    This port abstracts analytics storage and report generation.
    """

    @abstractmethod
    async def record_answer_evaluation(
        self,
        interview_id: UUID,
        answer: Answer,
    ) -> None:
        """Record answer evaluation for analytics.

        Args:
            interview_id: Interview identifier
            answer: Answer with evaluation data
        """
        pass

    @abstractmethod
    async def get_interview_statistics(
        self,
        interview_id: UUID,
    ) -> dict[str, Any]:
        """Get statistics for an interview.

        Args:
            interview_id: Interview identifier

        Returns:
            Dictionary with statistics (avg score, completion rate, etc.)
        """
        pass

    @abstractmethod
    async def get_candidate_performance_history(
        self,
        candidate_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get candidate's performance across all interviews.

        Args:
            candidate_id: Candidate identifier

        Returns:
            List of interview performance data
        """
        pass

    @abstractmethod
    async def generate_improvement_recommendations(
        self,
        interview_id: UUID,
        questions: list[Question],
        answers: list[Answer],
    ) -> list[str]:
        """Generate improvement recommendations based on performance.

        Args:
            interview_id: Interview identifier
            questions: Questions asked
            answers: Answers with evaluations

        Returns:
            List of improvement recommendations
        """
        pass

    @abstractmethod
    async def calculate_skill_scores(
        self,
        answers: list[Answer],
        questions: list[Question],
    ) -> dict[str, float]:
        """Calculate scores per skill based on answers.

        Args:
            answers: List of evaluated answers
            questions: Corresponding questions

        Returns:
            Dictionary mapping skill names to scores
        """
        pass
