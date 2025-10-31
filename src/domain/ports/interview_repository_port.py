"""Interview repository port interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..models.interview import Interview, InterviewStatus


class InterviewRepositoryPort(ABC):
    """Interface for interview persistence operations.

    This port abstracts database operations for interviews,
    allowing easy switching between databases or storage mechanisms.
    """

    @abstractmethod
    async def save(self, interview: Interview) -> Interview:
        """Save an interview.

        Args:
            interview: Interview to save

        Returns:
            Saved interview with updated metadata
        """
        pass

    @abstractmethod
    async def get_by_id(self, interview_id: UUID) -> Optional[Interview]:
        """Retrieve an interview by ID.

        Args:
            interview_id: Interview identifier

        Returns:
            Interview if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_candidate_id(
        self,
        candidate_id: UUID,
        status: Optional[InterviewStatus] = None,
    ) -> List[Interview]:
        """Retrieve interviews for a candidate.

        Args:
            candidate_id: Candidate identifier
            status: Optional status filter

        Returns:
            List of interviews
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: InterviewStatus,
        limit: int = 100,
    ) -> List[Interview]:
        """Retrieve interviews by status.

        Args:
            status: Interview status
            limit: Maximum number of results

        Returns:
            List of interviews
        """
        pass

    @abstractmethod
    async def update(self, interview: Interview) -> Interview:
        """Update an existing interview.

        Args:
            interview: Interview with updated data

        Returns:
            Updated interview
        """
        pass

    @abstractmethod
    async def delete(self, interview_id: UUID) -> bool:
        """Delete an interview.

        Args:
            interview_id: Interview identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Interview]:
        """List all interviews with pagination.

        Args:
            skip: Number of interviews to skip
            limit: Maximum number of results

        Returns:
            List of interviews
        """
        pass
