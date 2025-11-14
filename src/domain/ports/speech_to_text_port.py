"""Speech-to-Text port interface."""

from abc import ABC, abstractmethod
from typing import Any


class SpeechToTextPort(ABC):
    """Interface for speech-to-text operations.

    This port abstracts STT services, allowing switching between
    Azure Speech, Google Speech, etc.
    """

    @abstractmethod
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
    ) -> dict[str, Any]:
        """Transcribe audio bytes to text with voice metrics.

        Args:
            audio_bytes: Audio data as bytes (WAV/PCM format, 16kHz mono)
            language: Language code (e.g., "en-US", "vi-VN")

        Returns:
            Dictionary containing:
            {
                "text": str,  # Transcribed text
                "voice_metrics": {
                    "intonation_score": float,  # 0-1 (pitch variance)
                    "fluency_score": float,     # 0-1 (words/sec normalized)
                    "confidence_score": float,  # 0-1 (recognition confidence)
                    "speaking_rate_wpm": int,   # Words per minute
                },
                "metadata": {
                    "duration_seconds": float,
                    "audio_format": str,
                }
            }
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: bytes,
        language: str = "en-US",
    ) -> dict[str, Any]:
        """Transcribe streaming audio to text with voice metrics.

        Args:
            audio_stream: Audio data stream
            language: Language code

        Returns:
            Same dict structure as transcribe_audio()
        """
        pass

    @abstractmethod
    async def detect_language(
        self,
        audio_bytes: bytes,
    ) -> str | None:
        """Detect language from audio bytes.

        Args:
            audio_bytes: Audio data as bytes

        Returns:
            Detected language code or None
        """
        pass
