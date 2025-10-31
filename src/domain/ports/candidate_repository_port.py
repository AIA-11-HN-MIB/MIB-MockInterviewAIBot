"""Candidate repository port interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..models.candidate import Candidate


class CandidateRepositoryPort(ABC):
    """Interface for candidate persistence operations.

    This port abstracts database operations for candidates,
    allowing easy switching between databases or storage mechanisms.
    """

    @abstractmethod
    async def save(self, candidate: Candidate) -> Candidate:
        """Save a candidate.

        Args:
            candidate: Candidate to save

        Returns:
            Saved candidate with updated metadata
        """
        pass

    @abstractmethod
    async def get_by_id(self, candidate_id: UUID) -> Optional[Candidate]:
        """Retrieve a candidate by ID.

        Args:
            candidate_id: Candidate identifier

        Returns:
            Candidate if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Candidate]:
        """Retrieve a candidate by email.

        Args:
            email: Candidate email address

        Returns:
            Candidate if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, candidate: Candidate) -> Candidate:
        """Update an existing candidate.

        Args:
            candidate: Candidate with updated data

        Returns:
            Updated candidate
        """
        pass

    @abstractmethod
    async def delete(self, candidate_id: UUID) -> bool:
        """Delete a candidate.

        Args:
            candidate_id: Candidate identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Candidate]:
        """List all candidates with pagination.

        Args:
            skip: Number of candidates to skip
            limit: Maximum number of results

        Returns:
            List of candidates
        """
        pass
