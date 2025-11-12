"""Complete interview use case."""

from typing import Any
from uuid import UUID

from ...domain.models.interview import Interview, InterviewStatus
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.follow_up_question_repository_port import (
    FollowUpQuestionRepositoryPort,
)
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort
from .generate_summary import GenerateSummaryUseCase


class CompleteInterviewUseCase:
    """Complete interview and generate comprehensive summary."""

    def __init__(
        self,
        interview_repository: InterviewRepositoryPort,
        answer_repository: AnswerRepositoryPort | None = None,
        question_repository: QuestionRepositoryPort | None = None,
        follow_up_question_repository: FollowUpQuestionRepositoryPort | None = None,
        llm: LLMPort | None = None,
    ):
        self.interview_repo = interview_repository
        self.answer_repo = answer_repository
        self.question_repo = question_repository
        self.follow_up_repo = follow_up_question_repository
        self.llm = llm

    async def execute(
        self, interview_id: UUID, generate_summary: bool = True
    ) -> tuple[Interview, dict[str, Any] | None]:
        """Mark interview as completed and optionally generate summary.

        Args:
            interview_id: The interview UUID
            generate_summary: Whether to generate comprehensive summary (default: True)

        Returns:
            Tuple of (completed interview, summary dict or None)

        Raises:
            ValueError: If interview not found or invalid state
        """
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete interview with status: {interview.status}")

        # Generate summary if requested and dependencies available
        summary = None
        if (
            generate_summary
            and self.answer_repo
            and self.question_repo
            and self.follow_up_repo
            and self.llm
        ):
            summary_use_case = GenerateSummaryUseCase(
                interview_repository=self.interview_repo,
                answer_repository=self.answer_repo,
                question_repository=self.question_repo,
                follow_up_question_repository=self.follow_up_repo,
                llm=self.llm,
            )
            summary = await summary_use_case.execute(interview_id)

            # Store summary in interview metadata
            if interview.plan_metadata is None:
                interview.plan_metadata = {}
            interview.plan_metadata["completion_summary"] = summary

        # Mark interview as complete
        interview.complete()
        updated_interview = await self.interview_repo.update(interview)

        return updated_interview, summary
