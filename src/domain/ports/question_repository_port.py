"""Question repository port interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..models.question import Question, QuestionType, DifficultyLevel


class QuestionRepositoryPort(ABC):
    """Interface for question persistence operations.

    This port abstracts database operations for questions,
    allowing easy switching between databases or storage mechanisms.
    """

    @abstractmethod
    async def save(self, question: Question) -> Question:
        """Save a question.

        Args:
            question: Question to save

        Returns:
            Saved question with updated metadata
        """
        pass

    @abstractmethod
    async def get_by_id(self, question_id: UUID) -> Optional[Question]:
        """Retrieve a question by ID.

        Args:
            question_id: Question identifier

        Returns:
            Question if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_ids(self, question_ids: List[UUID]) -> List[Question]:
        """Retrieve multiple questions by IDs.

        Args:
            question_ids: List of question identifiers

        Returns:
            List of questions found
        """
        pass

    @abstractmethod
    async def find_by_skill(
        self,
        skill: str,
        difficulty: Optional[DifficultyLevel] = None,
        limit: int = 10,
    ) -> List[Question]:
        """Find questions by skill.

        Args:
            skill: Skill to filter by
            difficulty: Optional difficulty filter
            limit: Maximum number of results

        Returns:
            List of matching questions
        """
        pass

    @abstractmethod
    async def find_by_type(
        self,
        question_type: QuestionType,
        difficulty: Optional[DifficultyLevel] = None,
        limit: int = 10,
    ) -> List[Question]:
        """Find questions by type.

        Args:
            question_type: Type of questions to find
            difficulty: Optional difficulty filter
            limit: Maximum number of results

        Returns:
            List of matching questions
        """
        pass

    @abstractmethod
    async def find_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 10,
    ) -> List[Question]:
        """Find questions by tags.

        Args:
            tags: Tags to search for
            match_all: If True, match all tags; if False, match any tag
            limit: Maximum number of results

        Returns:
            List of matching questions
        """
        pass

    @abstractmethod
    async def update(self, question: Question) -> Question:
        """Update an existing question.

        Args:
            question: Question with updated data

        Returns:
            Updated question
        """
        pass

    @abstractmethod
    async def delete(self, question_id: UUID) -> bool:
        """Delete a question.

        Args:
            question_id: Question identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Question]:
        """List all questions with pagination.

        Args:
            skip: Number of questions to skip
            limit: Maximum number of results

        Returns:
            List of questions
        """
        pass