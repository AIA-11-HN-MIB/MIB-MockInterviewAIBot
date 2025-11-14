"""Mock Speech-to-Text adapter for development and testing."""

import random
from typing import Any

from ...domain.ports.speech_to_text_port import SpeechToTextPort


class MockSTTAdapter(SpeechToTextPort):
    """Mock STT adapter that returns placeholder transcriptions with voice metrics.

    This adapter simulates speech-to-text behavior for development
    and testing without requiring actual STT service calls.

    Voice metrics are generated using deterministic random values based on
    audio size to provide consistent test results.
    """

    def __init__(self, seed: int | None = None):
        """Initialize mock adapter.

        Args:
            seed: Random seed for deterministic metrics (default: None for random)
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
    ) -> dict[str, Any]:
        """Mock transcription from audio bytes with voice metrics.

        Args:
            audio_bytes: Audio data as bytes
            language: Language code

        Returns:
            Dict with text, voice_metrics, and metadata
        """
        # Generate mock transcript based on audio size
        audio_size = len(audio_bytes)
        word_count = max(10, audio_size // 1000)  # Estimate words from size
        mock_text = f"Mock transcription with approximately {word_count} words from {audio_size} bytes"

        # Generate realistic voice metrics
        voice_metrics = self._generate_voice_metrics(audio_size, word_count)

        # Calculate duration (assume 16kHz mono WAV)
        duration_seconds = audio_size / (16000 * 2)  # 2 bytes per sample

        return {
            "text": mock_text,
            "voice_metrics": voice_metrics,
            "metadata": {
                "duration_seconds": duration_seconds,
                "audio_format": "wav",
            }
        }

    async def transcribe_stream(
        self,
        audio_stream: bytes,
        language: str = "en-US",
    ) -> dict[str, Any]:
        """Mock stream transcription with voice metrics.

        Args:
            audio_stream: Audio data stream
            language: Language code

        Returns:
            Same dict structure as transcribe_audio()
        """
        # Reuse transcribe_audio logic
        return await self.transcribe_audio(audio_stream, language)

    async def detect_language(
        self,
        audio_bytes: bytes,
    ) -> str | None:
        """Mock language detection."""
        return "en-US"

    def _generate_voice_metrics(self, audio_size: int, word_count: int) -> dict[str, float]:
        """Generate realistic voice metrics for testing.

        Args:
            audio_size: Size of audio in bytes
            word_count: Estimated word count

        Returns:
            Dict with intonation, fluency, confidence scores and speaking rate
        """
        # Use audio size as seed for consistent metrics per audio
        if self.seed is None:
            random.seed(audio_size)

        # Generate scores with realistic distributions
        # Higher audio size -> slightly better metrics (simulates longer, clearer speech)
        size_factor = min(audio_size / 100000, 1.0)  # Cap at 100KB

        intonation_score = 0.5 + (random.random() * 0.3) + (size_factor * 0.2)
        fluency_score = 0.6 + (random.random() * 0.25) + (size_factor * 0.15)
        confidence_score = 0.7 + (random.random() * 0.2) + (size_factor * 0.1)

        # Clamp to [0, 1]
        intonation_score = min(max(intonation_score, 0.0), 1.0)
        fluency_score = min(max(fluency_score, 0.0), 1.0)
        confidence_score = min(max(confidence_score, 0.0), 1.0)

        # Calculate speaking rate (typical range: 120-180 WPM)
        duration_seconds = audio_size / (16000 * 2)
        speaking_rate_wpm = int((word_count / duration_seconds) * 60) if duration_seconds > 0 else 150
        speaking_rate_wpm = min(max(speaking_rate_wpm, 80), 200)  # Clamp to realistic range

        return {
            "intonation_score": round(intonation_score, 3),
            "fluency_score": round(fluency_score, 3),
            "confidence_score": round(confidence_score, 3),
            "speaking_rate_wpm": speaking_rate_wpm,
        }
