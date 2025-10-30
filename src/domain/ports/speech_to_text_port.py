"""Speech-to-Text port interface."""

from abc import ABC, abstractmethod
from typing import Optional


class SpeechToTextPort(ABC):
    """Interface for speech-to-text operations.

    This port abstracts STT services, allowing switching between
    Azure Speech, Google Speech, etc.
    """

    @abstractmethod
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en-US",
    ) -> str:
        """Transcribe audio file to text.

        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., "en-US", "vi-VN")

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: bytes,
        language: str = "en-US",
    ) -> str:
        """Transcribe streaming audio to text.

        Args:
            audio_stream: Audio data stream
            language: Language code

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    async def detect_language(
        self,
        audio_file_path: str,
    ) -> Optional[str]:
        """Detect language from audio file.

        Args:
            audio_file_path: Path to audio file

        Returns:
            Detected language code or None
        """
        pass
