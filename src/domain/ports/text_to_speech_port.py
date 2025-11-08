"""Text-to-Speech port interface."""

from abc import ABC, abstractmethod


class TextToSpeechPort(ABC):
    """Interface for text-to-speech operations.

    This port abstracts TTS services, allowing switching between
    Edge TTS, Google TTS, etc.
    """

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        language: str = "en-US",
        voice: str | None = None,
    ) -> bytes:
        """Convert text to speech audio.

        Args:
            text: Text to synthesize
            language: Language code (e.g., "en-US", "vi-VN")
            voice: Optional specific voice name

        Returns:
            Audio data as bytes
        """
        pass

    @abstractmethod
    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        language: str = "en-US",
        voice: str | None = None,
    ) -> str:
        """Convert text to speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            language: Language code
            voice: Optional specific voice name

        Returns:
            Path to saved audio file
        """
        pass

    @abstractmethod
    async def list_available_voices(
        self,
        language: str | None = None,
    ) -> list[dict]:
        """List available voices.

        Args:
            language: Optional language filter

        Returns:
            List of available voices with metadata
        """
        pass
