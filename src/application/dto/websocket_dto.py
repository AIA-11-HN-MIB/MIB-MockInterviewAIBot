"""WebSocket message DTOs for real-time interview communication."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


# Base message
class WebSocketMessage(BaseModel):
    """Base WebSocket message format."""
    type: str
    payload: dict[str, Any]


# Client → Server messages
class TextAnswerMessage(BaseModel):
    """Client sends text answer."""
    type: Literal["text_answer"]
    question_id: UUID
    answer_text: str


class AudioChunkMessage(BaseModel):
    """Client sends audio chunk for voice answer."""
    type: Literal["audio_chunk"]
    chunk_data: str  # base64 encoded
    is_final: bool


class GetNextQuestionMessage(BaseModel):
    """Client requests next question."""
    type: Literal["get_next_question"]


# Server → Client messages
class QuestionMessage(BaseModel):
    """Server sends question to client."""
    type: Literal["question"]
    question_id: UUID
    text: str
    question_type: str
    difficulty: str
    index: int
    total: int
    audio_data: str | None = None  # base64 encoded TTS


class TranscriptionMessage(BaseModel):
    """Server sends transcription of audio."""
    type: Literal["transcription"]
    text: str
    is_final: bool


class EvaluationMessage(BaseModel):
    """Server sends answer evaluation."""
    type: Literal["evaluation"]
    answer_id: UUID
    score: float
    feedback: str
    strengths: list[str]
    weaknesses: list[str]


class InterviewCompleteMessage(BaseModel):
    """Server notifies interview completion."""
    type: Literal["interview_complete"]
    interview_id: UUID
    overall_score: float
    total_questions: int
    feedback_url: str


class ErrorMessage(BaseModel):
    """Server sends error message."""
    type: Literal["error"]
    code: str
    message: str
