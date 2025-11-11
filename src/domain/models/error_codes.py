"""WebSocket error codes for interview sessions."""

from enum import Enum


class WebSocketErrorCode(str, Enum):
    """Error codes for WebSocket interview communication.

    Each error code indicates a specific failure scenario and includes
    metadata about recoverability and available fallback options.
    """

    # Interview state errors
    INTERVIEW_NOT_FOUND = "INTERVIEW_NOT_FOUND"
    INTERVIEW_NOT_READY = "INTERVIEW_NOT_READY"
    INTERVIEW_ALREADY_COMPLETED = "INTERVIEW_ALREADY_COMPLETED"
    INVALID_STATE = "INVALID_STATE"
    NO_MORE_QUESTIONS = "NO_MORE_QUESTIONS"

    # Question errors
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    QUESTION_ALREADY_ANSWERED = "QUESTION_ALREADY_ANSWERED"

    # Audio processing errors (Phase 1 integration)
    AUDIO_FORMAT_UNSUPPORTED = "AUDIO_FORMAT_UNSUPPORTED"
    AUDIO_TOO_SHORT = "AUDIO_TOO_SHORT"
    AUDIO_TOO_LONG = "AUDIO_TOO_LONG"
    AUDIO_DECODING_FAILED = "AUDIO_DECODING_FAILED"
    STT_FAILED = "STT_FAILED"
    TTS_FAILED = "TTS_FAILED"
    VOICE_METRICS_UNAVAILABLE = "VOICE_METRICS_UNAVAILABLE"

    # Message errors
    UNKNOWN_MESSAGE_TYPE = "UNKNOWN_MESSAGE_TYPE"
    INVALID_MESSAGE_FORMAT = "INVALID_MESSAGE_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    DATABASE_ERROR = "DATABASE_ERROR"

    def is_recoverable(self) -> bool:
        """Check if error is recoverable with retry.

        Returns:
            True if client can retry the operation
        """
        recoverable_errors = {
            self.TIMEOUT,
            self.STT_FAILED,
            self.TTS_FAILED,
            self.DATABASE_ERROR,
            self.INTERNAL_ERROR,
        }
        return self in recoverable_errors

    def get_fallback_option(self) -> str | None:
        """Get fallback option for this error.

        Returns:
            Suggested fallback option (e.g., "text_mode") or None
        """
        fallback_map = {
            self.STT_FAILED: "text_mode",
            self.TTS_FAILED: "text_only",
            self.AUDIO_FORMAT_UNSUPPORTED: "text_mode",
            self.VOICE_METRICS_UNAVAILABLE: "continue_without_metrics",
        }
        return fallback_map.get(self, None)
