"""Azure Speech-to-Text adapter implementation."""

import os
import azure.cognitiveservices.speech as speechsdk
from typing import Optional

from ...domain.ports.speech_to_text_port import SpeechToTextPort


class AzureSpeechAdapter(SpeechToTextPort):
    """Azure Speech Services implementation of Speech-to-Text port.

    This adapter encapsulates all Azure Speech-specific logic, making it easy
    to swap for another STT provider (Google Speech, AWS Transcribe, etc.)
    without touching domain logic.
    """

    def __init__(
        self,
        subscription_key: str,
        region: str,
        default_language: str = "en-US",
    ):
        """Initialize Azure Speech adapter.

        Args:
            subscription_key: Azure Speech Services subscription key
            region: Azure region (e.g., "eastus", "westus")
            default_language: Default language code (default: "en-US")
        """
        self.subscription_key = subscription_key
        self.region = region
        self.default_language = default_language
        
        # Create speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key,
            region=self.region
        )

    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en-US",
    ) -> str:
        """Transcribe audio file to text using Azure Speech Services.

        Args:
            audio_file_path: Path to audio file (supports wav, mp3, ogg, etc.)
            language: Language code (e.g., "en-US", "vi-VN")

        Returns:
            Transcribed text

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio format is unsupported
            RuntimeError: If transcription fails
        """
        # Validate file exists
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Configure speech recognition
        self.speech_config.speech_recognition_language = language
        
        # Create audio config from file
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        # Perform recognition
        result = speech_recognizer.recognize_once()

        # Process result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise ValueError(
                f"No speech could be recognized from audio: {result.no_match_details}"
            )
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f"\nError details: {cancellation.error_details}"
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unexpected recognition result: {result.reason}")

    async def transcribe_stream(
        self,
        audio_stream: bytes,
        language: str = "en-US",
    ) -> str:
        """Transcribe streaming audio to text using Azure Speech Services.

        This method handles real-time audio streaming for live interviews.

        Args:
            audio_stream: Audio data stream (bytes)
            language: Language code

        Returns:
            Transcribed text

        Raises:
            ValueError: If audio stream is invalid
            RuntimeError: If transcription fails
        """
        # Validate audio stream
        if not audio_stream or len(audio_stream) == 0:
            raise ValueError("Audio stream is empty")

        # Configure speech recognition
        self.speech_config.speech_recognition_language = language

        # Create push stream for audio data
        push_stream = speechsdk.audio.PushAudioInputStream()
        
        # Write audio data to stream
        push_stream.write(audio_stream)
        push_stream.close()

        # Create audio config from stream
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        # Perform recognition
        result = speech_recognizer.recognize_once()

        # Process result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise ValueError(
                f"No speech could be recognized from stream: {result.no_match_details}"
            )
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f"\nError details: {cancellation.error_details}"
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Unexpected recognition result: {result.reason}")

    async def detect_language(
        self,
        audio_file_path: str,
    ) -> Optional[str]:
        """Detect language from audio file using Azure Speech Services.

        This is useful for automatically detecting the interview language
        when working with multilingual candidates.

        Args:
            audio_file_path: Path to audio file

        Returns:
            Detected language code (e.g., "en-US", "vi-VN") or None if detection fails

        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        # Validate file exists
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Create auto-detect source language config
        # Azure supports multiple candidate languages
        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=["en-US", "vi-VN", "zh-CN", "ja-JP", "ko-KR", "fr-FR", "de-DE", "es-ES"]
        )

        # Create audio config from file
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

        # Create speech recognizer with auto-detection
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            auto_detect_source_language_config=auto_detect_source_language_config,
            audio_config=audio_config
        )

        # Perform recognition
        result = speech_recognizer.recognize_once()

        # Extract detected language
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # Get auto-detection result
            auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(result)
            return auto_detect_result.language
        elif result.reason == speechsdk.ResultReason.NoMatch:
            # Could not detect language
            return None
        elif result.reason == speechsdk.ResultReason.Canceled:
            # Recognition was canceled
            return None
        else:
            return None

    async def transcribe_continuous(
        self,
        audio_file_path: str,
        language: str = "en-US",
        callback = None,
    ) -> str:
        """Transcribe audio with continuous recognition (for long audio files).

        This method is more suitable for long interview recordings where
        we need continuous recognition rather than single-shot.

        Args:
            audio_file_path: Path to audio file
            language: Language code
            callback: Optional callback function to receive interim results

        Returns:
            Complete transcribed text

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        # Validate file exists
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Configure speech recognition
        self.speech_config.speech_recognition_language = language

        # Create audio config from file
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        # Accumulate all recognized text
        all_results = []
        done = False

        def stop_cb(evt):
            """Callback when recognition stops."""
            nonlocal done
            done = True

        def recognized_cb(evt):
            """Callback when speech is recognized."""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                all_results.append(evt.result.text)
                if callback:
                    callback(evt.result.text)

        # Connect callbacks
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()

        # Wait until recognition completes
        import time
        while not done:
            time.sleep(0.5)

        # Stop recognition
        speech_recognizer.stop_continuous_recognition()

        # Return concatenated results
        return " ".join(all_results)
