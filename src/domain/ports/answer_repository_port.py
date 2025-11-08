"""Answer repository port interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.answer import Answer


class AnswerRepositoryPort(ABC):
    """Interface for answer persistence operations.

    This port abstracts database operations for answers,
    allowing easy switching between databases or storage mechanisms.
    """

    @abstractmethod
    async def save(self, answer: Answer) -> Answer:
        """Save an answer.

        Args:
            answer: Answer to save

        Returns:
            Saved answer with updated metadata
        """
        pass

    @abstractmethod
    async def get_by_id(self, answer_id: UUID) -> Answer | None:
        """Retrieve an answer by ID.

        Args:
            answer_id: Answer identifier

        Returns:
            Answer if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_ids(self, answer_ids: list[UUID]) -> list[Answer]:
        """Retrieve multiple answers by IDs.

        Args:
            answer_ids: List of answer identifiers

        Returns:
            List of answers found
        """
        pass

    @abstractmethod
    async def get_by_interview_id(self, interview_id: UUID) -> list[Answer]:
        """Retrieve all answers for an interview.

        Args:
            interview_id: Interview identifier

        Returns:
            List of answers
        """
        pass

    @abstractmethod
    async def get_by_question_id(self, question_id: UUID) -> list[Answer]:
        """Retrieve all answers for a question.

        Args:
            question_id: Question identifier

        Returns:
            List of answers
        """
        pass

    @abstractmethod
    async def get_by_candidate_id(self, candidate_id: UUID) -> list[Answer]:
        """Retrieve all answers by a candidate.

        Args:
            candidate_id: Candidate identifier

        Returns:
            List of answers
        """
        pass

    @abstractmethod
    async def update(self, answer: Answer) -> Answer:
        """Update an existing answer.

        Args:
            answer: Answer with updated data

        Returns:
            Updated answer
        """
        pass

    @abstractmethod
    async def delete(self, answer_id: UUID) -> bool:
        """Delete an answer.

        Args:
            answer_id: Answer identifier

        Returns:
            True if deleted, False if not found
        """
        pass
