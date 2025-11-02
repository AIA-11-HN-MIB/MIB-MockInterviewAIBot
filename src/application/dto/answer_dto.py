"""Answer DTOs for REST API request/response."""

from uuid import UUID

from pydantic import BaseModel


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer to a question."""
    question_id: UUID
    answer_text: str
    audio_file_path: str | None = None


class AnswerEvaluationResponse(BaseModel):
    """Response with answer evaluation results."""
    answer_id: UUID
    question_id: UUID
    score: float
    feedback: str
    strengths: list[str]
    weaknesses: list[str]
    improvement_suggestions: list[str]
    next_question_available: bool
