"""Process answer use case."""

from datetime import datetime
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.interview import InterviewStatus
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort


class ProcessAnswerUseCase:
    """Process and evaluate candidate answer."""

    def __init__(
        self,
        answer_repository: AnswerRepositoryPort,
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
        llm: LLMPort,
    ):
        self.answer_repo = answer_repository
        self.interview_repo = interview_repository
        self.question_repo = question_repository
        self.llm = llm

    async def execute(
        self,
        interview_id: UUID,
        question_id: UUID,
        answer_text: str,
        audio_file_path: str | None = None,
    ) -> tuple[Answer, bool]:
        """Process answer and return evaluation + has_more_questions.

        Args:
            interview_id: The interview UUID
            question_id: The question UUID
            answer_text: The answer text
            audio_file_path: Optional audio file path for voice answers

        Returns:
            Tuple of (Answer with evaluation, has_more_questions)

        Raises:
            ValueError: If interview or question not found, or invalid state
        """
        # Validate interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.IN_PROGRESS:
            raise ValueError(f"Interview not in progress: {interview.status}")

        # Validate question
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Create answer
        answer = Answer(
            interview_id=interview_id,
            question_id=question_id,
            candidate_id=interview.candidate_id,
            text=answer_text,
            is_voice=bool(audio_file_path),
            audio_file_path=audio_file_path,
            created_at=datetime.utcnow(),
        )

        # Evaluate answer using LLM
        evaluation = await self.llm.evaluate_answer(
            question=question,
            answer_text=answer_text,
            context={
                "interview_id": str(interview_id),
                "candidate_id": str(interview.candidate_id),
            },
        )

        # Set evaluation
        answer.evaluate(evaluation)

        # Save answer
        saved_answer = await self.answer_repo.save(answer)

        # Update interview
        interview.add_answer(saved_answer.id)
        await self.interview_repo.update(interview)

        # Check if more questions
        has_more = interview.has_more_questions()

        return saved_answer, has_more
