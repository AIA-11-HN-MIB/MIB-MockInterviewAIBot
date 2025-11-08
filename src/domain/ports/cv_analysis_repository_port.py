"""CV Analysis repository port interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.cv_analysis import CVAnalysis


class CVAnalysisRepositoryPort(ABC):
    """Interface for CV analysis persistence operations.

    This port abstracts database operations for CV analyses,
    allowing easy switching between databases or storage mechanisms.
    """

    @abstractmethod
    async def save(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Save a CV analysis.

        Args:
            cv_analysis: CV analysis to save

        Returns:
            Saved CV analysis with updated metadata
        """
        pass

    @abstractmethod
    async def get_by_id(self, cv_analysis_id: UUID) -> CVAnalysis | None:
        """Retrieve a CV analysis by ID.

        Args:
            cv_analysis_id: CV analysis identifier

        Returns:
            CV analysis if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_candidate_id(self, candidate_id: UUID) -> list[CVAnalysis]:
        """Retrieve all CV analyses for a candidate.

        Args:
            candidate_id: Candidate identifier

        Returns:
            List of CV analyses
        """
        pass

    @abstractmethod
    async def get_latest_by_candidate_id(
        self,
        candidate_id: UUID,
    ) -> CVAnalysis | None:
        """Retrieve the most recent CV analysis for a candidate.

        Args:
            candidate_id: Candidate identifier

        Returns:
            Latest CV analysis if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Update an existing CV analysis.

        Args:
            cv_analysis: CV analysis with updated data

        Returns:
            Updated CV analysis
        """
        pass

    @abstractmethod
    async def delete(self, cv_analysis_id: UUID) -> bool:
        """Delete a CV analysis.

        Args:
            cv_analysis_id: CV analysis identifier

        Returns:
            True if deleted, False if not found
        """
        pass
