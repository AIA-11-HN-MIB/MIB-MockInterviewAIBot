"""Mock Text-to-Speech adapter for development and testing."""

import struct
from typing import Any

from ...domain.ports.text_to_speech_port import TextToSpeechPort


class MockTTSAdapter(TextToSpeechPort):
    """Mock TTS adapter that generates silent WAV audio data.

    This adapter simulates text-to-speech behavior for development
    and testing without requiring actual TTS service calls.

    Generates properly formatted WAV files with silent audio based on
    text length for predictable testing.
    """

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> bytes:
        """Mock speech synthesis with proper WAV structure.

        Args:
            text: Text to synthesize
            voice: Voice name (ignored in mock)
            speed: Speaking rate (used to adjust audio length)

        Returns:
            WAV audio bytes (16kHz mono, 16-bit PCM)
        """
        # Estimate audio duration based on text length
        # Assume average speaking rate: 150 words/min = 2.5 words/sec
        word_count = len(text.split())
        duration_seconds = (word_count / 150.0) * 60.0 / speed  # Adjust for speed
        duration_seconds = max(duration_seconds, 0.5)  # Minimum 0.5 seconds

        # Generate silent audio data
        sample_rate = 16000  # 16kHz
        num_channels = 1  # Mono
        bits_per_sample = 16
        num_samples = int(sample_rate * duration_seconds)

        # Create WAV file in memory
        wav_bytes = self._create_wav_bytes(
            sample_rate=sample_rate,
            num_channels=num_channels,
            bits_per_sample=bits_per_sample,
            num_samples=num_samples,
        )

        return wav_bytes

    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> str:
        """Mock save to file.

        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice: Voice name
            speed: Speaking rate

        Returns:
            Path to saved audio file
        """
        audio_bytes = await self.synthesize_speech(text, voice, speed)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """Get list of available voices with metadata.

        Returns:
            List of dicts with name, locale, gender, voice_type
        """
        return [
            {
                "name": "en-US-AriaNeural",
                "locale": "en-US",
                "gender": "Female",
                "voice_type": "Neural",
            },
            {
                "name": "en-US-JennyNeural",
                "locale": "en-US",
                "gender": "Female",
                "voice_type": "Neural",
            },
            {
                "name": "en-US-GuyNeural",
                "locale": "en-US",
                "gender": "Male",
                "voice_type": "Neural",
            },
            {
                "name": "en-GB-SoniaNeural",
                "locale": "en-GB",
                "gender": "Female",
                "voice_type": "Neural",
            },
            {
                "name": "en-GB-RyanNeural",
                "locale": "en-GB",
                "gender": "Male",
                "voice_type": "Neural",
            },
        ]

    def _create_wav_bytes(
        self,
        sample_rate: int,
        num_channels: int,
        bits_per_sample: int,
        num_samples: int,
    ) -> bytes:
        """Create properly formatted WAV file bytes with silent audio.

        Args:
            sample_rate: Sample rate in Hz (e.g., 16000)
            num_channels: Number of audio channels (1 for mono)
            bits_per_sample: Bits per sample (16 for 16-bit PCM)
            num_samples: Total number of samples

        Returns:
            Complete WAV file as bytes
        """
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)
        data_size = num_samples * block_align

        # Build WAV header
        wav = b"RIFF"
        wav += struct.pack("<I", 36 + data_size)  # File size - 8
        wav += b"WAVE"

        # fmt chunk
        wav += b"fmt "
        wav += struct.pack("<I", 16)  # fmt chunk size
        wav += struct.pack("<H", 1)  # Audio format (1 = PCM)
        wav += struct.pack("<H", num_channels)
        wav += struct.pack("<I", sample_rate)
        wav += struct.pack("<I", byte_rate)
        wav += struct.pack("<H", block_align)
        wav += struct.pack("<H", bits_per_sample)

        # data chunk
        wav += b"data"
        wav += struct.pack("<I", data_size)

        # Silent audio data (all zeros)
        wav += b"\x00" * data_size

        return wav
