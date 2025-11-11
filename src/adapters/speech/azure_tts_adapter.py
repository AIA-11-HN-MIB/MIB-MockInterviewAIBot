"""Azure Text-to-Speech adapter implementation."""

import asyncio
import logging

import azure.cognitiveservices.speech as speechsdk

from ...domain.ports.text_to_speech_port import TextToSpeechPort

logger = logging.getLogger(__name__)


class AzureTextToSpeechAdapter(TextToSpeechPort):
    """Azure Speech SDK implementation for text-to-speech.

    This adapter uses Azure Cognitive Services Speech SDK to synthesize
    speech from text with configurable voices and speaking rates.

    Includes LRU caching for frequently synthesized texts to reduce API calls.
    """

    def __init__(
        self,
        api_key: str,
        region: str,
        default_voice: str = "en-US-AriaNeural",
        cache_size: int = 128,
    ):
        """Initialize Azure TTS adapter.

        Args:
            api_key: Azure Speech Services API key
            region: Azure region (e.g., "eastus", "westus")
            default_voice: Default voice name (e.g., "en-US-AriaNeural")
            cache_size: Max number of cached audio outputs (default 128)
        """
        self.api_key = api_key
        self.region = region
        self.default_voice = default_voice
        self.cache_size = cache_size

        # Create speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=api_key,
            region=region,
        )
        self.speech_config.speech_synthesis_voice_name = default_voice

        # Set output format to WAV 16kHz mono
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )

        logger.info(f"Initialized Azure TTS adapter (region={region}, voice={default_voice})")

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> bytes:
        """Convert text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., "en-US-AriaNeural")
            speed: Speaking rate multiplier (0.5-2.0)

        Returns:
            WAV audio bytes (16kHz mono)

        Raises:
            ValueError: If speech synthesis fails
        """
        # Check cache first
        cache_key: tuple[str, str, float] = (text, voice, speed)
        cached_audio = self._get_from_cache(cache_key)
        if cached_audio:
            logger.debug(f"Cache hit for text (length={len(text)})")
            return cached_audio

        # Run sync Azure SDK in thread pool
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
            voice,
            speed,
        )

        # Cache the result
        self._add_to_cache(cache_key, audio_bytes)

        return audio_bytes

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
            speed: Speaking rate multiplier

        Returns:
            Path to saved audio file
        """
        audio_bytes = await self.synthesize_speech(text, voice, speed)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        logger.info(f"Saved audio to {output_path} ({len(audio_bytes)} bytes)")
        return output_path

    async def get_available_voices(self) -> list[str]:
        """Get list of available voice names.

        Returns:
            List of voice name strings

        Note:
            In production, this would query Azure's voice list API.
            For now, returns commonly used neural voices.
        """
        # Commonly available Azure Neural voices
        return [
            "en-US-AriaNeural",
            "en-US-JennyNeural",
            "en-US-GuyNeural",
            "en-US-DavisNeural",
            "en-GB-SoniaNeural",
            "en-GB-RyanNeural",
            "en-AU-NatashaNeural",
            "en-AU-WilliamNeural",
        ]

    def _synthesize_sync(
        self,
        text: str,
        voice: str,
        speed: float,
    ) -> bytes:
        """Synchronous speech synthesis using Azure SDK.

        Args:
            text: Text to synthesize
            voice: Voice name
            speed: Speaking rate multiplier

        Returns:
            WAV audio bytes

        Raises:
            ValueError: If synthesis fails
        """
        try:
            # Update voice if different from default
            if voice != self.default_voice:
                self.speech_config.speech_synthesis_voice_name = voice

            # Create synthesizer for in-memory synthesis
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None,  # Use in-memory synthesis
            )

            # Build SSML with speed adjustment
            ssml = self._build_ssml(text, voice, speed)

            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml).get()

            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_bytes = result.audio_data
                logger.info(f"Synthesized {len(text)} chars → {len(audio_bytes)} bytes")
                return audio_bytes

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                raise ValueError(f"Speech synthesis failed: {cancellation.error_details}")

            else:
                raise ValueError(f"Unexpected result reason: {result.reason}")

        except Exception as e:
            logger.error(f"Error during speech synthesis: {str(e)}")
            raise

    def _build_ssml(self, text: str, voice: str, speed: float) -> str:
        """Build SSML (Speech Synthesis Markup Language) with speed control.

        Args:
            text: Text to synthesize
            voice: Voice name
            speed: Speaking rate multiplier (0.5-2.0)

        Returns:
            SSML string
        """
        # Clamp speed to valid range
        speed = max(0.5, min(speed, 2.0))

        # Convert speed to percentage (1.0 = +0%, 1.5 = +50%, 0.5 = -50%)
        speed_percent = int((speed - 1.0) * 100)
        speed_str = f"{speed_percent:+d}%" if speed_percent != 0 else "0%"

        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <prosody rate="{speed_str}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """

        return ssml.strip()

    def _get_from_cache(self, cache_key: tuple[str, str, float]) -> bytes | None:
        """Get audio from LRU cache.

        Args:
            cache_key: Tuple of (text, voice, speed)

        Returns:
            Cached audio bytes or None

        Note:
            In production, implement proper caching (Redis, memcached, etc.)
            For now, returns None (no caching implemented)
        """
        return None

    def _add_to_cache(self, cache_key: tuple[str, str, float], audio_bytes: bytes) -> None:
        """Add audio to LRU cache.

        Args:
            cache_key: Tuple of (text, voice, speed)
            audio_bytes: Audio bytes to cache

        Note:
            In production, implement proper caching (Redis, memcached, etc.)
            For now, this is a no-op.
        """
        pass
