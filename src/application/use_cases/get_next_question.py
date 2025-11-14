"""Get next question use case."""

from uuid import UUID

from ...domain.models.question import Question
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort


class GetNextQuestionUseCase:
    """Get next question in interview sequence."""

    def __init__(
        self,
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
    ):
        self.interview_repo = interview_repository
        self.question_repo = question_repository

    async def execute(self, interview_id: UUID) -> Question | None:
        """Get next unanswered question.

        Args:
            interview_id: The interview UUID

        Returns:
            Next question or None if interview complete

        Raises:
            ValueError: If interview not found
        """
        # Get interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        # Check if more questions available
        if not interview.has_more_questions():
            return None

        # Get current question
        question_id = interview.get_current_question_id()
        if not question_id:
            return None

        question = await self.question_repo.get_by_id(question_id)
        return question
