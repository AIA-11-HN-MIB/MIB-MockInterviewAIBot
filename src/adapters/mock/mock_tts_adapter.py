"""Mock Text-to-Speech adapter for development and testing."""


from ...domain.ports.text_to_speech_port import TextToSpeechPort


class MockTTSAdapter(TextToSpeechPort):
    """Mock TTS adapter that returns minimal audio data.

    This adapter simulates text-to-speech behavior for development
    and testing without requiring actual TTS service calls.
    """

    async def synthesize_speech(
        self,
        text: str,
        language: str = "en-US",
        voice: str | None = None,
    ) -> bytes:
        """Mock speech synthesis with minimal WAV structure."""
        # Return mock audio bytes (minimal WAV header + data)
        # Real WAV would have proper RIFF structure
        wav_header = b"RIFF"
        wav_header += (100).to_bytes(4, "little")  # File size
        wav_header += b"WAVE"
        wav_header += b"fmt "
        wav_header += (16).to_bytes(4, "little")  # Format chunk size
        wav_header += b"\x00" * 16  # Format data
        wav_header += b"data"
        wav_header += (64).to_bytes(4, "little")  # Data chunk size
        wav_header += b"\x00" * 64  # Audio data (silence)

        return wav_header

    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        language: str = "en-US",
        voice: str | None = None,
    ) -> str:
        """Mock save to file."""
        # In real implementation, would save actual audio
        audio_bytes = await self.synthesize_speech(text, language, voice)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path

    async def list_available_voices(
        self,
        language: str | None = None,
    ) -> list[dict]:
        """Mock voice list."""
        voices = [
            {
                "name": "mock-en-US-male-1",
                "language": "en-US",
                "gender": "male",
                "quality": "standard",
            },
            {
                "name": "mock-en-US-female-1",
                "language": "en-US",
                "gender": "female",
                "quality": "standard",
            },
            {
                "name": "mock-en-GB-male-1",
                "language": "en-GB",
                "gender": "male",
                "quality": "premium",
            },
        ]

        if language:
            return [v for v in voices if v["language"] == language]
        return voices
