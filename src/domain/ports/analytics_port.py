"""Analytics port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
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
    ) -> Dict[str, Any]:
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
    ) -> List[Dict[str, Any]]:
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
        questions: List[Question],
        answers: List[Answer],
    ) -> List[str]:
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
        answers: List[Answer],
        questions: List[Question],
    ) -> Dict[str, float]:
        """Calculate scores per skill based on answers.

        Args:
            answers: List of evaluated answers
            questions: Corresponding questions

        Returns:
            Dictionary mapping skill names to scores
        """
        pass
