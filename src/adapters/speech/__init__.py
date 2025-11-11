"""Speech adapters package."""

from .azure_stt_adapter import AzureSpeechToTextAdapter
from .azure_tts_adapter import AzureTextToSpeechAdapter

__all__ = [
    "AzureSpeechToTextAdapter",
    "AzureTextToSpeechAdapter",
]
