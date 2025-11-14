"""Text-to-Speech port interface."""

from abc import ABC, abstractmethod


class TextToSpeechPort(ABC):
    """Interface for text-to-speech operations.

    This port abstracts TTS services, allowing switching between
    Azure Speech, Edge TTS, Google TTS, etc.
    """

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> bytes:
        """Convert text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., "en-US-AriaNeural", "en-GB-SoniaNeural")
            speed: Speaking rate multiplier (0.5-2.0, default 1.0)

        Returns:
            WAV audio bytes (16kHz mono)
        """
        pass

    @abstractmethod
    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> str:
        """Convert text to speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice: Voice name
            speed: Speaking rate multiplier (0.5-2.0)

        Returns:
            Path to saved audio file
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[str]:
        """Get list of available voice names.

        Returns:
            List of voice name strings (e.g., ["en-US-AriaNeural", "en-GB-SoniaNeural"])
        """
        pass
