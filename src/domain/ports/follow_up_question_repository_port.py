"""Follow-up question repository port interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.follow_up_question import FollowUpQuestion


class FollowUpQuestionRepositoryPort(ABC):
    """Interface for follow-up question persistence operations.

    This port abstracts database operations for follow-up questions,
    allowing easy switching between databases or storage mechanisms.
    """

    @abstractmethod
    async def save(self, follow_up_question: FollowUpQuestion) -> FollowUpQuestion:
        """Save a follow-up question.

        Args:
            follow_up_question: FollowUpQuestion to save

        Returns:
            Saved follow-up question with updated metadata
        """
        pass

    @abstractmethod
    async def get_by_id(self, question_id: UUID) -> FollowUpQuestion | None:
        """Retrieve a follow-up question by ID.

        Args:
            question_id: Follow-up question identifier

        Returns:
            FollowUpQuestion if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_parent_question_id(
        self, parent_question_id: UUID
    ) -> list[FollowUpQuestion]:
        """Retrieve all follow-up questions for a parent question.

        Args:
            parent_question_id: Parent question identifier

        Returns:
            List of follow-up questions ordered by order_in_sequence
        """
        pass

    @abstractmethod
    async def get_by_interview_id(self, interview_id: UUID) -> list[FollowUpQuestion]:
        """Retrieve all follow-up questions for an interview.

        Args:
            interview_id: Interview identifier

        Returns:
            List of follow-up questions ordered by created_at
        """
        pass

    @abstractmethod
    async def count_by_parent_question_id(self, parent_question_id: UUID) -> int:
        """Count follow-up questions for a parent question.

        Args:
            parent_question_id: Parent question identifier

        Returns:
            Count of follow-up questions
        """
        pass

    @abstractmethod
    async def delete(self, question_id: UUID) -> bool:
        """Delete a follow-up question.

        Args:
            question_id: Follow-up question identifier

        Returns:
            True if deleted, False if not found
        """
        pass
