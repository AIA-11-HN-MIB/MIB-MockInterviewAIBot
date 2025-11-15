"""Azure Speech-to-Text adapter implementation."""

import asyncio
import json
import logging
from typing import Any

import azure.cognitiveservices.speech as speechsdk

from ...domain.ports.speech_to_text_port import SpeechToTextPort

logger = logging.getLogger(__name__)


class AzureSpeechToTextAdapter(SpeechToTextPort):
    """Azure Speech SDK implementation for speech-to-text with voice metrics.

    This adapter uses Azure Cognitive Services Speech SDK to transcribe
    audio and extract voice quality metrics (intonation, fluency, confidence).
    """

    def __init__(
        self,
        api_key: str,
        region: str,
        language: str = "en-US",
    ):
        """Initialize Azure STT adapter.

        Args:
            api_key: Azure Speech Services API key
            region: Azure region (e.g., "eastus", "westus")
            language: Default language code (e.g., "en-US")
        """
        self.api_key = api_key
        self.region = region
        self.default_language = language

        # Create speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=api_key,
            region=region,
        )
        self.speech_config.speech_recognition_language = language

        # Enable detailed result
        self.speech_config.output_format = speechsdk.OutputFormat.Detailed

        logger.info(f"Initialized Azure STT adapter (region={region}, language={language})")

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
    ) -> dict[str, Any]:
        """Transcribe audio bytes to text with voice metrics.

        Args:
            audio_bytes: Audio data as bytes (WAV/PCM format, 16kHz mono)
            language: Language code

        Returns:
            Dict with text, voice_metrics, and metadata

        Raises:
            ValueError: If speech recognition fails
        """
        # Run sync Azure SDK in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_bytes,
            language,
        )

        return result

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
        # For now, treat stream as complete audio
        return await self.transcribe_audio(audio_stream, language)

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
        # Azure SDK has language detection, but for simplicity return default
        # In production, implement proper language detection
        return self.default_language

    def _transcribe_sync(
        self,
        audio_bytes: bytes,
        language: str,
    ) -> dict[str, Any]:
        """Synchronous transcription using Azure SDK.

        Args:
            audio_bytes: Audio data as bytes
            language: Language code

        Returns:
            Dict with text, voice_metrics, and metadata
        """
        try:
            # Create push stream
            stream = speechsdk.audio.PushAudioInputStream()

            # Write audio data to stream
            stream.write(audio_bytes)
            stream.close()

            # Create audio config from stream
            audio_config = speechsdk.audio.AudioConfig(stream=stream)

            # Update language if different from default
            if language != self.default_language:
                self.speech_config.speech_recognition_language = language

            # Create recognizer
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config,
            )

            # Perform recognition
            result = recognizer.recognize_once()

            # Check result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Extract text and metrics
                text = result.text
                voice_metrics = self._calculate_voice_metrics(result, audio_bytes)
                # Handle duration: Azure SDK returns int (100-nanosecond ticks) or timedelta
                if isinstance(result.duration, int):
                    # Convert from 100-nanosecond ticks to seconds
                    duration_seconds = result.duration / 10_000_000.0
                else:
                    duration_seconds = result.duration.total_seconds()

                logger.info(f"Transcribed {len(text)} chars, duration={duration_seconds:.2f}s")

                return {
                    "text": text,
                    "voice_metrics": voice_metrics,
                    "metadata": {
                        "duration_seconds": duration_seconds,
                        "audio_format": "wav",
                    }
                }

            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech detected in audio")
                raise ValueError("No speech detected in audio")

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                raise ValueError(f"Speech recognition failed: {cancellation.error_details}")

            else:
                raise ValueError(f"Unexpected result reason: {result.reason}")

        except Exception as e:
            logger.error(f"Error during speech recognition: {str(e)}")
            raise

    def _calculate_voice_metrics(
        self,
        result: speechsdk.SpeechRecognitionResult,
        audio_bytes: bytes,
    ) -> dict[str, float]:
        """Calculate voice quality metrics from Azure recognition result.

        Args:
            result: Azure speech recognition result
            audio_bytes: Original audio bytes

        Returns:
            Dict with intonation, fluency, confidence scores and speaking rate
        """
        try:
            # Get detailed JSON result with prosody data
            json_result = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult
            )

            if json_result:
                data = json.loads(json_result)
                # Extract confidence from detailed result
                confidence = data.get("NBest", [{}])[0].get("Confidence", 0.8)
            else:
                # Fallback to basic confidence
                confidence = 0.8  # Default if not available

            # Calculate metrics
            text = result.text
            # Handle duration: Azure SDK returns int (100-nanosecond ticks) or timedelta
            if isinstance(result.duration, int):
                # Convert from 100-nanosecond ticks to seconds
                duration_seconds = result.duration / 10_000_000.0
            else:
                duration_seconds = result.duration.total_seconds()

            # Intonation score (pitch variance) - estimated from confidence and length
            # Higher confidence + longer speech = better intonation
            intonation_score = min(confidence + (duration_seconds / 30.0) * 0.1, 1.0)

            # Fluency score based on speaking rate
            word_count = len(text.split())
            speaking_rate_wpm = int((word_count / duration_seconds) * 60) if duration_seconds > 0 else 0

            # Optimal speaking rate: 120-180 WPM
            # Calculate fluency based on how close to optimal range
            if 120 <= speaking_rate_wpm <= 180:
                fluency_score = 0.9 + (confidence * 0.1)  # High fluency in optimal range
            elif 90 <= speaking_rate_wpm < 120:
                fluency_score = 0.7 + ((speaking_rate_wpm - 90) / 30.0) * 0.2
            elif 180 < speaking_rate_wpm <= 220:
                fluency_score = 0.7 + ((220 - speaking_rate_wpm) / 40.0) * 0.2
            else:
                fluency_score = 0.5  # Too slow or too fast

            # Clamp scores to [0, 1]
            intonation_score = max(0.0, min(intonation_score, 1.0))
            fluency_score = max(0.0, min(fluency_score, 1.0))
            confidence_score = max(0.0, min(confidence, 1.0))

            return {
                "intonation_score": round(intonation_score, 3),
                "fluency_score": round(fluency_score, 3),
                "confidence_score": round(confidence_score, 3),
                "speaking_rate_wpm": speaking_rate_wpm,
            }

        except Exception as e:
            logger.warning(f"Error calculating voice metrics, using defaults: {e}")
            # Return default metrics if calculation fails
            return {
                "intonation_score": 0.7,
                "fluency_score": 0.7,
                "confidence_score": 0.7,
                "speaking_rate_wpm": 150,
            }
