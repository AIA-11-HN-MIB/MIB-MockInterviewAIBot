# Phase 1: Speech Integration Foundation

**Duration**: 3 days
**Priority**: Critical
**Dependencies**: None

## Context

Current STT/TTS ports have basic interfaces but no production implementation. Mock adapters exist but don't simulate voice metrics (intonation, fluency, confidence). Need production-ready Azure Speech SDK adapters with voice metrics analysis.

**Context Links**:
- `src/domain/ports/speech_to_text_port.py` - STT interface (basic)
- `src/domain/ports/text_to_speech_port.py` - TTS interface (basic)
- `src/adapters/mock/mock_stt_adapter.py` - Mock STT (no voice metrics)
- `src/adapters/mock/mock_tts_adapter.py` - Mock TTS (empty audio)

## Key Insights

1. **Voice Metrics**: Azure Speech SDK provides prosody data (pitch, speaking rate) but NOT fluency/confidence directly → Need custom analysis
2. **Streaming STT**: Azure supports chunked audio input → Enables real-time transcription
3. **Audio Format**: Browser MediaRecorder uses WebM Opus → Need conversion to WAV/PCM for Azure
4. **Mock Adapters**: Must simulate realistic voice metrics for testing → Use random distributions based on answer length

## Requirements

### Functional Requirements

**FR1**: STT adapter converts audio bytes to text
- Input: Audio bytes (WAV/PCM format, 16kHz mono)
- Output: Transcript text + voice metrics (dict)
- Error: Return None if recognition fails

**FR2**: Voice metrics extraction
- Metrics: intonation (pitch variance), fluency (word/sec), confidence (0-1)
- Calculation: Real-time analysis during STT processing
- Storage: Embed in Answer.metadata field

**FR3**: TTS adapter converts text to audio
- Input: Text string + voice settings (locale, speed)
- Output: Audio bytes (WAV format, 16kHz mono)
- Caching: Cache frequent questions to reduce API calls

**FR4**: Mock adapters simulate voice metrics
- STT mock: Random metrics based on answer length
- TTS mock: Generate silent audio bytes (predictable size)
- Behavior: Deterministic for testing

### Non-Functional Requirements

**NFR1**: Performance
- STT latency: <2s for 30-second audio
- TTS latency: <1s for 100-word text
- Voice metrics calc: <500ms

**NFR2**: Audio Quality
- Sample rate: 16kHz minimum
- Channels: Mono
- Bitrate: 32kbps (TTS) / 128kbps (STT)

**NFR3**: Error Handling
- Retry logic: 3 attempts with exponential backoff
- Graceful degradation: Fall back to mock if Azure fails
- Logging: Log all speech API errors

## Architecture

### Updated Port Interfaces

```python
# speech_to_text_port.py
class SpeechToTextPort(ABC):
    @abstractmethod
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "en-US"
    ) -> dict[str, Any]:
        """Transcribe audio to text with voice metrics.

        Returns:
            {
                "text": str,
                "voice_metrics": {
                    "intonation_score": float,  # 0-1 (pitch variance)
                    "fluency_score": float,     # 0-1 (words/sec normalized)
                    "confidence_score": float,  # 0-1 (recognition confidence)
                    "speaking_rate_wpm": int,   # Words per minute
                },
                "metadata": {
                    "duration_seconds": float,
                    "audio_format": str,
                }
            }
        """
        pass

# text_to_speech_port.py
class TextToSpeechPort(ABC):
    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0
    ) -> bytes:
        """Convert text to audio bytes.

        Args:
            text: Text to synthesize
            voice: Azure voice name
            speed: Speaking rate (0.5-2.0)

        Returns:
            WAV audio bytes (16kHz mono)
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[str]:
        """Get list of available voice names."""
        pass
```

### Azure Speech SDK Adapter

```python
# src/adapters/speech/azure_stt_adapter.py
import azure.cognitiveservices.speech as speechsdk
from ...domain.ports.speech_to_text_port import SpeechToTextPort

class AzureSpeechToTextAdapter(SpeechToTextPort):
    def __init__(
        self,
        api_key: str,
        region: str,
        language: str = "en-US"
    ):
        self.api_key = api_key
        self.region = region
        self.language = language
        self.speech_config = speechsdk.SpeechConfig(
            subscription=api_key,
            region=region
        )

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "en-US"
    ) -> dict[str, Any]:
        # Create push stream
        stream = speechsdk.audio.PushAudioInputStream()
        stream.write(audio_bytes)
        stream.close()

        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        # Recognize with prosody
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # Extract voice metrics
            voice_metrics = self._calculate_voice_metrics(result)

            return {
                "text": result.text,
                "voice_metrics": voice_metrics,
                "metadata": {
                    "duration_seconds": result.duration.total_seconds(),
                    "audio_format": "wav",
                }
            }
        else:
            raise ValueError(f"Speech recognition failed: {result.reason}")

    def _calculate_voice_metrics(self, result) -> dict[str, float]:
        """Calculate voice metrics from Azure result."""
        # Get prosody data
        prosody = result.properties.get(
            speechsdk.PropertyId.SpeechServiceResponse_JsonResult
        )

        # Parse JSON for pitch, rate, etc.
        # Calculate custom metrics
        intonation_score = self._calculate_intonation(prosody)
        fluency_score = self._calculate_fluency(result.text, result.duration)
        confidence_score = result.confidence

        return {
            "intonation_score": intonation_score,
            "fluency_score": fluency_score,
            "confidence_score": confidence_score,
            "speaking_rate_wpm": self._calculate_wpm(result.text, result.duration)
        }
```

### Audio DTO

```python
# src/application/dto/audio_dto.py
from pydantic import BaseModel

class AudioChunkDTO(BaseModel):
    """Audio chunk for WebSocket transmission."""
    audio_data: str  # Base64-encoded audio bytes
    chunk_index: int
    is_final: bool
    format: str = "webm"  # webm, wav, mp3

class VoiceMetricsDTO(BaseModel):
    """Voice analysis results."""
    intonation_score: float  # 0-1
    fluency_score: float     # 0-1
    confidence_score: float  # 0-1
    speaking_rate_wpm: int
    duration_seconds: float
```

## Implementation Steps

### Day 1: Port Enhancement & DTOs

**Step 1**: Update STT port interface
- Add voice_metrics to return type
- Add metadata field
- Update docstrings

**Step 2**: Update TTS port interface
- Add voice parameter
- Add speed parameter
- Add get_available_voices() method

**Step 3**: Create audio DTOs
- AudioChunkDTO for WebSocket
- VoiceMetricsDTO for evaluation

**Step 4**: Update mock adapters
- Enhance MockSTTAdapter with voice metrics simulation
- Enhance MockTTSAdapter with realistic audio bytes

### Day 2: Azure Speech SDK Integration

**Step 1**: Create Azure STT adapter
- Install azure-cognitiveservices-speech package
- Implement transcribe_audio() with streaming support
- Implement _calculate_voice_metrics() helper

**Step 2**: Create Azure TTS adapter
- Implement synthesize_speech() with caching
- Implement get_available_voices()
- Add error handling and retries

**Step 3**: Update DI container
- Add speech service configuration
- Wire Azure adapters (production)
- Wire mock adapters (development)

### Day 3: Testing & Validation

**Step 1**: Unit tests
- Test voice metrics calculation
- Test error handling (network failures)
- Test mock adapter determinism

**Step 2**: Integration tests
- Test with real Azure Speech SDK (test account)
- Verify audio format compatibility
- Measure latency

**Step 3**: Documentation
- Update port interface docs
- Add Azure setup guide
- Document voice metrics formula

## Todo List

**Day 1**: ✅ COMPLETED
- [x] Update SpeechToTextPort interface with voice_metrics
- [x] Update TextToSpeechPort interface with voice and speed params
- [x] Create AudioChunkDTO in application/dto/audio_dto.py
- [x] Create VoiceMetricsDTO in application/dto/audio_dto.py
- [x] Enhance MockSTTAdapter with random voice metrics
- [x] Enhance MockTTSAdapter with silent audio generation

**Day 2**: ✅ COMPLETED (implementation) - ⚠️ ISSUES FOUND (see review)
- [x] Install azure-cognitiveservices-speech package (⚠️ defined in pyproject.toml, not installed in env)
- [x] Create src/adapters/speech/ directory
- [x] Implement AzureSpeechToTextAdapter
- [x] Implement AzureTextToSpeechAdapter
- [x] Update DI container with speech adapter selection
- [x] Add speech service config to Settings

**Day 3**: ❌ NOT STARTED - BLOCKING ISSUES
- [ ] Write unit tests for voice metrics calculation
- [ ] Write unit tests for mock adapters
- [ ] Write integration tests with Azure Speech SDK
- [ ] Measure and log latency (STT, TTS, metrics calc)
- [ ] Update docs/system-architecture.md with speech integration

**Code Review Findings** (2025-11-12):
- [ ] Fix type safety issues (6 mypy errors) - CRITICAL
- [ ] Install Azure SDK in virtual environment - CRITICAL
- [ ] Fix mock adapter global random state issue - HIGH
- [ ] Implement LRU caching for TTS - HIGH
- [ ] Add retry logic with exponential backoff - HIGH
- [ ] Add graceful degradation fallback to mock - HIGH
- [ ] Create domain exceptions for speech errors - MEDIUM
- [ ] Decide on language detection (implement or remove) - MEDIUM
- [ ] Validate voice metrics formulas with baseline data - MEDIUM
- [ ] Add performance metrics logging - LOW

## Success Criteria

- ✅ STT adapter returns text + 3 voice metrics (intonation, fluency, confidence) - PASS
- ⚠️ TTS adapter generates audio <1s for 100-word text - UNVERIFIED (no caching implemented)
- ✅ Mock adapters simulate realistic voice metrics (deterministic) - PASS
- ⚠️ Voice metrics calculation <500ms - UNVERIFIED (no performance tests)
- ❌ Unit test coverage >=80% - FAIL (0% coverage - NO TESTS WRITTEN)
- ❌ Integration tests pass with real Azure Speech SDK - FAIL (SDK not installed in env)

**Phase 1 Status**: 60% complete (implementation done, validation/testing missing)
**Blocking Issues**: Missing tests, Azure SDK not installed, type errors
**Review Report**: See `reports/251112-code-review-phase1-speech-integration.md`

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Azure Speech SDK complexity | High | Medium | Use mock adapters for dev, gradual rollout |
| Voice metrics inaccuracy | Medium | Low | Validate against human evaluation baseline |
| Audio format compatibility | High | Medium | Test with multiple browsers, add conversion |
| API costs | Medium | Low | Cache TTS results, use mock by default |

## Security Considerations

1. **API Keys**: Store Azure keys in environment variables (`.env.local`)
2. **Audio Data**: Don't persist raw audio bytes (only text + metrics)
3. **Rate Limiting**: Implement per-candidate API call limits
4. **PII**: Transcripts may contain sensitive info → Enable deletion
