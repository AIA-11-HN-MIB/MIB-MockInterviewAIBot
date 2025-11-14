"""Speech adapters (STT and TTS)."""

from .azure_speech_adapter import AzureSpeechAdapter
from .azure_tts_adapter import AzureTTSAdapter

__all__ = ["AzureSpeechAdapter", "AzureTTSAdapter"]
