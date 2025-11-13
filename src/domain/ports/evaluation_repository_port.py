"""Evaluation repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.evaluation import Evaluation


class EvaluationRepositoryPort(ABC):
    """Interface for evaluation persistence."""

    @abstractmethod
    async def save(self, evaluation: Evaluation) -> Evaluation:
        """Save evaluation with gaps.

        Args:
            evaluation: Evaluation to save

        Returns:
            Saved evaluation with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        """Get evaluation by ID.

        Args:
            evaluation_id: Evaluation UUID

        Returns:
            Evaluation if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_answer_id(self, answer_id: UUID) -> Evaluation | None:
        """Get evaluation for answer (1:1 relationship).

        Args:
            answer_id: Answer UUID

        Returns:
            Evaluation if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_parent_evaluation_id(
        self, parent_id: UUID
    ) -> list[Evaluation]:
        """Get follow-up evaluations for parent.

        Args:
            parent_id: Parent evaluation UUID

        Returns:
            List of follow-up evaluations ordered by attempt_number
        """
        pass

    @abstractmethod
    async def update(self, evaluation: Evaluation) -> Evaluation:
        """Update evaluation.

        Args:
            evaluation: Evaluation to update

        Returns:
            Updated evaluation

        Raises:
            ValueError: If evaluation not found
        """
        pass

    @abstractmethod
    async def delete(self, evaluation_id: UUID) -> None:
        """Delete evaluation.

        Args:
            evaluation_id: Evaluation UUID to delete
        """
        pass
