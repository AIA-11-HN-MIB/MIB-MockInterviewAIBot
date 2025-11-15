"""Azure Text-to-Speech adapter implementation."""

import os
import azure.cognitiveservices.speech as speechsdk  # type: ignore
from typing import Any, Optional

from ...domain.ports.text_to_speech_port import TextToSpeechPort


class AzureTTSAdapter(TextToSpeechPort):
    """Azure Speech Services implementation of Text-to-Speech port.

    This adapter encapsulates all Azure TTS-specific logic, making it easy
    to swap for another TTS provider (Edge TTS, Google TTS, ElevenLabs, etc.)
    without touching domain logic.
    """

    # Default voices for common languages
    DEFAULT_VOICES = {
        "en-US": "en-US-JennyNeural",
        "en-GB": "en-GB-SoniaNeural",
        "vi-VN": "vi-VN-HoaiMyNeural",
        "zh-CN": "zh-CN-XiaoxiaoNeural",
        "ja-JP": "ja-JP-NanamiNeural",
        "ko-KR": "ko-KR-SunHiNeural",
        "fr-FR": "fr-FR-DeniseNeural",
        "de-DE": "de-DE-KatjaNeural",
        "es-ES": "es-ES-ElviraNeural",
    }

    def __init__(
        self,
        subscription_key: str,
        region: str,
        default_language: str = "en-US",
        default_voice: Optional[str] = None,
    ):
        """Initialize Azure TTS adapter.

        Args:
            subscription_key: Azure Speech Services subscription key
            region: Azure region (e.g., "eastus", "westus")
            default_language: Default language code (default: "en-US")
            default_voice: Default voice name (if None, uses language default)
        """
        self.subscription_key = subscription_key
        self.region = region
        self.default_language = default_language
        self.default_voice = default_voice or self.DEFAULT_VOICES.get(
            default_language, "en-US-JennyNeural"
        )

        # Create speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key, region=self.region
        )

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> bytes:
        """Convert text to speech audio using Azure Speech Services.

        Args:
            text: Text to synthesize
            voice: Voice name (locale-specific, e.g., "en-US-JennyNeural")
            speed: Speaking rate multiplier (0.5-2.0, default 1.0)

        Returns:
            Audio data as bytes (WAV format)

        Raises:
            ValueError: If text is empty or invalid
            RuntimeError: If synthesis fails
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Select voice (use parameter or default)
        selected_voice = voice or self.default_voice

        # Configure voice
        self.speech_config.speech_synthesis_voice_name = selected_voice

        # Create synthesizer with null output (we'll get bytes directly)
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=None  # None means output to memory
        )

        # Synthesize speech with speed adjustment if needed
        if speed != 1.0:
            # Use SSML for speed control
            ssml = self._create_ssml_with_speed(text, selected_voice, speed)
            result = speech_synthesizer.speak_ssml_async(ssml).get()  # type: ignore
        else:
            # Use plain text synthesis
            result = speech_synthesizer.speak_text_async(text).get()  # type: ignore

        # Process result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  # type: ignore
            return result.audio_data  # type: ignore
        elif result.reason == speechsdk.ResultReason.Canceled:  # type: ignore
            cancellation = result.cancellation_details  # type: ignore
            error_msg = f"Speech synthesis canceled: {cancellation.reason}"  # type: ignore
            if cancellation.reason == speechsdk.CancellationReason.Error:  # type: ignore
                error_msg += f"\nError details: {cancellation.error_details}"  # type: ignore
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unexpected synthesis result: {result.reason}")  # type: ignore

    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> str:
        """Convert text to speech and save to file using Azure Speech Services.

        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice: Voice name (locale-specific)
            speed: Speaking rate multiplier (0.5-2.0, default 1.0)

        Returns:
            Path to saved audio file

        Raises:
            ValueError: If text is empty or output path is invalid
            RuntimeError: If synthesis fails
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if not output_path:
            raise ValueError("Output path cannot be empty")

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Select voice (use parameter or default)
        selected_voice = voice or self.default_voice

        # Configure voice
        self.speech_config.speech_synthesis_voice_name = selected_voice

        # Create audio config for file output
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

        # Create synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )

        # Synthesize speech with speed adjustment if needed
        if speed != 1.0:
            # Use SSML for speed control
            ssml = self._create_ssml_with_speed(text, selected_voice, speed)
            result = speech_synthesizer.speak_ssml_async(ssml).get()  # type: ignore
        else:
            # Use plain text synthesis
            result = speech_synthesizer.speak_text_async(text).get()  # type: ignore

        # Process result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  # type: ignore
            return output_path
        elif result.reason == speechsdk.ResultReason.Canceled:  # type: ignore
            cancellation = result.cancellation_details  # type: ignore
            error_msg = f"Speech synthesis canceled: {cancellation.reason}"  # type: ignore
            if cancellation.reason == speechsdk.CancellationReason.Error:  # type: ignore
                error_msg += f"\nError details: {cancellation.error_details}"  # type: ignore
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unexpected synthesis result: {result.reason}")  # type: ignore

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """Get list of available voices with metadata.

        Returns:
            List of dicts with keys: name, locale, gender, voice_type
            Example: [
                {
                    "name": "en-US-AriaNeural",
                    "locale": "en-US",
                    "gender": "Female",
                    "voice_type": "Neural"
                },
                ...
            ]

        Raises:
            RuntimeError: If voice list retrieval fails
        """
        # Create synthesizer to access voice list
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=None
        )

        # Get voice list
        result = speech_synthesizer.get_voices_async().get()  # type: ignore

        # Process result
        if result.reason == speechsdk.ResultReason.VoicesListRetrieved:  # type: ignore
            voices = []
            for voice in result.voices:  # type: ignore
                voices.append(
                    {
                        "name": voice.short_name,  # type: ignore
                        "locale": voice.locale,  # type: ignore
                        "gender": voice.gender.name,  # type: ignore
                        "voice_type": voice.voice_type.name,  # type: ignore
                    }
                )
            return voices
        elif result.reason == speechsdk.ResultReason.Canceled:  # type: ignore
            cancellation = result.cancellation_details  # type: ignore
            error_msg = f"Voice list retrieval canceled: {cancellation.reason}"  # type: ignore
            if cancellation.reason == speechsdk.CancellationReason.Error:  # type: ignore
                error_msg += f"\nError details: {cancellation.error_details}"  # type: ignore
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unexpected result: {result.reason}")  # type: ignore

    async def synthesize_ssml(
        self,
        ssml: str,
        output_path: Optional[str] = None,
    ) -> bytes:
        """Convert SSML to speech audio (advanced feature).

        SSML (Speech Synthesis Markup Language) allows fine-grained control
        over pronunciation, pitch, rate, volume, etc.

        Args:
            ssml: SSML markup text
            output_path: Optional path to save audio file

        Returns:
            Audio data as bytes

        Raises:
            ValueError: If SSML is invalid
            RuntimeError: If synthesis fails
        """
        # Validate input
        if not ssml or not ssml.strip():
            raise ValueError("SSML cannot be empty")

        # Create audio config
        audio_config = None
        if output_path:
            # Create output directory if needed
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

        # Create synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )

        # Synthesize from SSML
        result = speech_synthesizer.speak_ssml_async(ssml).get()  # type: ignore

        # Process result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  # type: ignore
            return result.audio_data  # type: ignore
        elif result.reason == speechsdk.ResultReason.Canceled:  # type: ignore
            cancellation = result.cancellation_details  # type: ignore
            error_msg = f"SSML synthesis canceled: {cancellation.reason}"  # type: ignore
            if cancellation.reason == speechsdk.CancellationReason.Error:  # type: ignore
                error_msg += f"\nError details: {cancellation.error_details}"  # type: ignore
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unexpected synthesis result: {result.reason}")  # type: ignore

    def create_ssml(
        self,
        text: str,
        voice: str,
        rate: str = "medium",
        pitch: str = "medium",
        volume: str = "medium",
    ) -> str:
        """Helper method to create SSML markup.

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., "en-US-JennyNeural")
            rate: Speaking rate ("x-slow", "slow", "medium", "fast", "x-fast")
            pitch: Pitch ("x-low", "low", "medium", "high", "x-high")
            volume: Volume ("silent", "x-soft", "soft", "medium", "loud", "x-loud")

        Returns:
            SSML markup string
        """
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()

    def _create_ssml_with_speed(
        self,
        text: str,
        voice: str,
        speed: float,
    ) -> str:
        """Create SSML with speaking rate adjustment.

        Args:
            text: Text to synthesize
            voice: Voice name
            speed: Speed multiplier (0.5 = 50% slower, 2.0 = 100% faster)

        Returns:
            SSML markup string
        """
        # Convert speed multiplier to percentage
        # 1.0 = 0%, 1.5 = +50%, 0.5 = -50%
        rate_percent = f"{int((speed - 1.0) * 100):+d}%"

        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <prosody rate="{rate_percent}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()
