"""Complete interview use case."""

from uuid import UUID

from ...domain.models.interview import Interview, InterviewStatus
from ...domain.ports.interview_repository_port import InterviewRepositoryPort


class CompleteInterviewUseCase:
    """Complete interview and mark as finished."""

    def __init__(self, interview_repository: InterviewRepositoryPort):
        self.interview_repo = interview_repository

    async def execute(self, interview_id: UUID) -> Interview:
        """Mark interview as completed.

        Args:
            interview_id: The interview UUID

        Returns:
            Completed interview

        Raises:
            ValueError: If interview not found or invalid state
        """
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot complete interview with status: {interview.status}"
            )

        interview.complete()
        return await self.interview_repo.update(interview)
