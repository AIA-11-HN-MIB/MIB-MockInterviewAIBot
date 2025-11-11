"""WebSocket message DTOs for real-time interview communication."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Base message
class WebSocketMessage(BaseModel):
    """Base WebSocket message format."""

    type: str
    payload: dict[str, Any]


# ============================================================================
# CLIENT → SERVER MESSAGES
# ============================================================================


class TextAnswerMessage(BaseModel):
    """Client sends text answer for a question."""

    type: Literal["text_answer"] = "text_answer"
    question_id: UUID = Field(..., description="ID of question being answered")
    answer_text: str = Field(..., min_length=1, description="Answer text content")


class AudioChunkMessage(BaseModel):
    """Client sends audio chunk for voice answer.

    Audio is sent in chunks to support streaming and large files.
    """

    type: Literal["audio_chunk"] = "audio_chunk"
    audio_data: str = Field(..., description="Base64-encoded audio bytes")
    chunk_index: int = Field(..., ge=0, description="Sequential chunk number")
    is_final: bool = Field(..., description="Whether this is the last chunk")
    format: str = Field(default="webm", description="Audio format (webm, wav, mp3)")
    question_id: UUID = Field(..., description="ID of question being answered")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate audio format is supported."""
        supported_formats = {"webm", "wav", "mp3", "ogg"}
        if v.lower() not in supported_formats:
            raise ValueError(f"Unsupported audio format: {v}. Must be one of {supported_formats}")
        return v.lower()


class GetNextQuestionMessage(BaseModel):
    """Client requests next question in interview."""

    type: Literal["get_next_question"] = "get_next_question"


class RequestRetryMessage(BaseModel):
    """Client requests retry of failed operation."""

    type: Literal["request_retry"] = "request_retry"
    failed_message_type: str = Field(..., description="Type of message that failed")
    error_code: str = Field(..., description="Error code from failure")


# ============================================================================
# SERVER → CLIENT MESSAGES
# ============================================================================


class QuestionMessage(BaseModel):
    """Server sends question to client with optional TTS audio."""

    type: Literal["question"] = "question"
    question_id: UUID = Field(..., description="Unique question ID")
    text: str = Field(..., description="Question text")
    question_type: str = Field(..., description="Type (TECHNICAL, BEHAVIORAL, SITUATIONAL)")
    difficulty: str = Field(..., description="Difficulty (EASY, MEDIUM, HARD)")
    index: int = Field(..., ge=1, description="Current question number (1-based)")
    total: int = Field(..., ge=1, description="Total questions in interview")
    audio_data: str | None = Field(None, description="Base64-encoded TTS audio (WAV)")
    audio_format: str = Field(default="wav", description="Audio format")


class FollowUpQuestionMessage(BaseModel):
    """Server sends follow-up question for deeper probing."""

    type: Literal["follow_up_question"] = "follow_up_question"
    question_id: UUID = Field(..., description="Unique follow-up question ID")
    parent_question_id: UUID = Field(..., description="ID of original question")
    text: str = Field(..., description="Follow-up question text")
    generated_reason: str = Field(..., description="Why this follow-up was generated")
    order_in_sequence: int = Field(..., ge=1, description="Order in follow-up chain")
    audio_data: str | None = Field(None, description="Base64-encoded TTS audio")
    audio_format: str = Field(default="wav", description="Audio format")


class EvaluationMessage(BaseModel):
    """Server sends answer evaluation with optional voice metrics."""

    type: Literal["evaluation"] = "evaluation"
    answer_id: UUID = Field(..., description="Unique answer ID")
    score: float = Field(..., ge=0.0, le=100.0, description="Answer score (0-100)")
    feedback: str = Field(..., description="Overall feedback")
    strengths: list[str] = Field(default_factory=list, description="Answer strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Areas for improvement")
    similarity_score: float | None = Field(None, description="Similarity to ideal answer")
    gaps: dict[str, Any] | None = Field(None, description="Knowledge gaps detected")
    voice_metrics: dict[str, float] | None = Field(
        None, description="Voice quality metrics (if audio answer)"
    )


class VoiceMetricsMessage(BaseModel):
    """Server sends real-time voice analysis during answer."""

    type: Literal["voice_metrics"] = "voice_metrics"
    intonation_score: float = Field(..., ge=0.0, le=1.0, description="Pitch variance (0-1)")
    fluency_score: float = Field(..., ge=0.0, le=1.0, description="Speaking fluency (0-1)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Recognition confidence (0-1)")
    speaking_rate_wpm: int = Field(..., ge=0, description="Words per minute")
    real_time: bool = Field(default=True, description="Real-time or final metrics")


class TranscriptionMessage(BaseModel):
    """Server sends transcription of audio (intermediate or final)."""

    type: Literal["transcription"] = "transcription"
    text: str = Field(..., description="Transcribed text")
    is_final: bool = Field(..., description="Whether transcription is final")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")


class InterviewCompleteMessage(BaseModel):
    """Server notifies interview completion with final results."""

    type: Literal["interview_complete"] = "interview_complete"
    interview_id: UUID = Field(..., description="Completed interview ID")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall score (0-100)")
    total_questions: int = Field(..., ge=1, description="Total questions answered")
    feedback_url: str = Field(..., description="URL to detailed feedback report")


class ErrorMessage(BaseModel):
    """Server sends structured error with recovery options."""

    type: Literal["error"] = "error"
    code: str = Field(..., description="Error code (see WebSocketErrorCode enum)")
    message: str = Field(..., description="Human-readable error message")
    recoverable: bool = Field(default=False, description="Whether error is recoverable")
    retry_available: bool = Field(default=False, description="Whether retry is possible")
    fallback_option: str | None = Field(
        None, description="Suggested fallback (e.g., 'text_mode')"
    )
