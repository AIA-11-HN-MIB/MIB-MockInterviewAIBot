"""Mock Speech-to-Text adapter for development and testing."""


from ...domain.ports.speech_to_text_port import SpeechToTextPort


class MockSTTAdapter(SpeechToTextPort):
    """Mock STT adapter that returns placeholder transcriptions.

    This adapter simulates speech-to-text behavior for development
    and testing without requiring actual STT service calls.
    """

    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en-US",
    ) -> str:
        """Mock transcription from file."""
        return f"[Mock transcription from {audio_file_path}]"

    async def transcribe_stream(
        self,
        audio_stream: bytes,
        language: str = "en-US",
    ) -> str:
        """Mock stream transcription."""
        stream_size = len(audio_stream)
        return f"[Mock transcription from audio stream ({stream_size} bytes)]"

    async def detect_language(
        self,
        audio_file_path: str,
    ) -> str | None:
        """Mock language detection."""
        return "en-US"
