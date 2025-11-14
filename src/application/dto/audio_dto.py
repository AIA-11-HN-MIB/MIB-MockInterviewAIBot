"""Audio-related Data Transfer Objects."""

from pydantic import BaseModel, Field


class AudioChunkDTO(BaseModel):
    """Audio chunk for WebSocket transmission."""

    audio_data: str = Field(..., description="Base64-encoded audio bytes")
    chunk_index: int = Field(..., description="Sequential chunk number")
    is_final: bool = Field(..., description="Whether this is the last chunk")
    format: str = Field(default="webm", description="Audio format (webm, wav, mp3)")


class VoiceMetricsDTO(BaseModel):
    """Voice analysis results from speech-to-text."""

    intonation_score: float = Field(
        ..., ge=0.0, le=1.0, description="Pitch variance score (0-1)"
    )
    fluency_score: float = Field(
        ..., ge=0.0, le=1.0, description="Speaking fluency score (0-1)"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Speech recognition confidence (0-1)"
    )
    speaking_rate_wpm: int = Field(..., ge=0, description="Words per minute")
    duration_seconds: float = Field(..., ge=0.0, description="Audio duration in seconds")


class TranscriptionResultDTO(BaseModel):
    """Complete transcription result with text and metrics."""

    text: str = Field(..., description="Transcribed text")
    voice_metrics: VoiceMetricsDTO = Field(..., description="Voice analysis metrics")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
