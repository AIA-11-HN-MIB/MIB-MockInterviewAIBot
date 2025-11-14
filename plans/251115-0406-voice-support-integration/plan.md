# Voice Support Integration - Implementation Plan

**Created**: 2025-11-15
**Plan ID**: `251115-0406-voice-support-integration`
**Status**: Ready for Implementation
**Estimated Effort**: 3-5 days (5 phases, real-time streaming STT)

---

## Executive Summary

Add end-to-end voice interview support using Azure Speech Services (STT/TTS) via WebSocket. Enable voice answers with transcription, voice metrics extraction, and optional TTS question synthesis.

**Key Goal**: Allow candidates to answer interview questions via voice, with real-time transcription, quality analysis, and seamless fallback to text mode.

---

## Current State Analysis

### ✅ Completed Components

**Port Interfaces** (Domain Layer):
- `SpeechToTextPort`: 3 methods (transcribe_audio, transcribe_stream, detect_language)
- `TextToSpeechPort`: 3 methods (synthesize_speech, save_speech_to_file, get_available_voices)
- Both interfaces use bytes-based signatures for audio data

**Azure Adapters** (Real Implementations):
- `AzureSpeechToTextAdapter`: Implements STT with Azure SDK, voice metrics calculation
- `AzureTTSAdapter`: Implements TTS with Azure SDK, SSML support

**Mock Adapters** (Development):
- `MockSTTAdapter`: Returns placeholder transcriptions with generated voice metrics
- `MockTTSAdapter`: Generates silent WAV files for testing

**WebSocket DTOs**:
- `AudioChunkMessage`: Client → Server (base64 audio, chunk_index, is_final)
- `TranscriptionMessage`: Server → Client (text, is_final, confidence)
- `VoiceMetricsMessage`: Server → Client (intonation, fluency, confidence, WPM)
- `QuestionMessage`: Includes optional `audio_data` field for TTS

**Infrastructure**:
- `Settings`: Has Azure Speech config fields (key, region, language, voice, cache_size)
- `Container`: Has placeholder methods `speech_to_text_port()` and `text_to_speech_port()`

### ❌ Critical Issues

**1. Adapter Signature Mismatch**:
- **Port Interface**: `synthesize_speech(text, voice, speed) → bytes`
- **Azure Adapter**: `synthesize_speech(text, language, voice) → bytes` (extra `language` param)
- **Impact**: Violates Liskov Substitution Principle, adapter doesn't implement port contract

**2. TTS Port Missing Method**:
- **Azure Adapter**: Has `list_available_voices(language) → list[dict]`
- **Port Interface**: Has `get_available_voices() → list[str]` (no language param, different return type)
- **Impact**: Signature mismatch prevents polymorphism

**3. DI Container Not Implemented**:
- Methods `speech_to_text_port()` and `text_to_speech_port()` defined but stub implementations
- No mock/real toggle logic based on settings flags
- Missing error handling for missing API keys

**4. WebSocket Handler Stub**:
- `handle_audio_chunk()` function exists but not implemented (line 59)
- No audio assembly logic for chunked streaming
- No STT integration for transcription

**5. Session Orchestrator No Voice Support**:
- Only handles text answers via `handle_answer(answer_text: str)`
- No method for processing voice answers with STT
- No TTS integration for question audio generation

---

## Architecture Overview

### Clean Architecture Constraints

**Dependency Rule** (must follow):
```
Domain (Ports) ← Application (Use Cases) ← Adapters (Implementations) ← Infrastructure (Config/DI)
```

**Key Principles**:
1. **Port interfaces define contract**: Adapters MUST match port signatures exactly
2. **Mock/Real toggle in DI**: Container selects implementation based on `settings.use_mock_stt/tts`
3. **Async throughout**: All I/O operations use async/await
4. **Error handling at adapter layer**: Convert Azure SDK errors to domain exceptions
5. **No Azure SDK in domain**: Ports use only Python stdlib types (bytes, str, dict)

### Voice Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Client (WebSocket)                                         │
│  - Records audio chunks (WebM/WAV)                          │
│  - Sends AudioChunkMessage                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  WebSocket Handler (interview_handler.py)                   │
│  - Receives AudioChunkMessage                               │
│  - Assembles chunks into complete audio                     │
│  - Base64 decode → bytes                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  Session Orchestrator (session_orchestrator.py)             │
│  - handle_voice_answer(audio_bytes, question_id)            │
│  - State: QUESTIONING → EVALUATING                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  SpeechToTextPort (Port Interface)                          │
│  - transcribe_audio(audio_bytes, language) → dict           │
│  - Returns: {text, voice_metrics, metadata}                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─ Mock? → MockSTTAdapter
                  └─ Real  → AzureSpeechToTextAdapter
                              │
                              ↓
                       Azure Speech SDK
                              │
                  ┌───────────┴────────────┐
                  ↓                        ↓
         Transcription Text        Voice Metrics
         (answer_text)             (intonation, fluency, confidence)
                  │                        │
                  └───────────┬────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ProcessAnswerAdaptiveUseCase                               │
│  - Evaluate answer (semantic + voice metrics)               │
│  - Create Answer entity with evaluation                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  WebSocket Response                                         │
│  - TranscriptionMessage (text, is_final, confidence)        │
│  - VoiceMetricsMessage (intonation, fluency, WPM)           │
│  - EvaluationMessage (score, feedback, voice_metrics)       │
└─────────────────────────────────────────────────────────────┘
```

### TTS Integration (Optional)

```
┌─────────────────────────────────────────────────────────────┐
│  Session Orchestrator                                       │
│  - _send_next_main_question()                               │
│  - Generate question audio via TTS (optional)               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│  TextToSpeechPort (Port Interface)                          │
│  - synthesize_speech(text, voice, speed) → bytes            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─ Mock? → MockTTSAdapter (silent WAV)
                  └─ Real  → AzureTTSAdapter
                              │
                              ↓
                       Azure Speech SDK
                              │
                              ↓
                         WAV Audio Bytes
                              │
                              ↓
                       Base64 Encode
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  QuestionMessage                                            │
│  - text: "What is...?"                                      │
│  - audio_data: "UklGRi4YAABUAQABAECAAABACAA..." (base64)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Adapter Signature Alignment
- **Goal**: Fix Azure adapters to match port contracts exactly
- **Effort**: 2-3 hours
- **Files**: 2 adapters + 2 mocks (4 total)
- **Risk**: Low (isolated refactoring)

### Phase 2: DI Container & Settings
- **Goal**: Implement speech service DI with mock/real toggle
- **Effort**: 1-2 hours
- **Files**: Container (1), Settings validation
- **Risk**: Low (straightforward config)

### Phase 3: WebSocket Audio Integration (Real-time Streaming STT)
- **Goal**: Implement real-time streaming STT with audio chunks
- **Effort**: 5-6 hours
- **Files**: Handler (1), Streaming audio queue, Background transcription task
- **Risk**: Medium-High (async streaming, interim results, state management)

### Phase 4: Session Orchestrator Voice Support
- **Goal**: Add voice answer handling with TTS question synthesis
- **Effort**: 3-4 hours
- **Files**: Orchestrator (1), ProcessAnswerAdaptive integration
- **Risk**: Medium (state machine integration)

### Phase 5: Testing & Validation
- **Goal**: Unit tests + integration tests for voice flow
- **Effort**: 4-5 hours
- **Files**: 8-10 test files
- **Risk**: Low (use mocks for fast tests)

---

## Phase Details

### Phase 1: Adapter Signature Alignment

**Objective**: Fix adapter signatures to match port contracts exactly.

**Files Modified**:
1. `src/adapters/speech/azure_tts_adapter.py` (remove `language` param)
2. `src/domain/ports/text_to_speech_port.py` (update `get_available_voices` signature)

**Changes**:
- **TTS Port**: Change `get_available_voices() → list[str]` to `get_available_voices() → list[dict]`
- **Azure TTS Adapter**: Remove `language` param from `synthesize_speech()`, use voice name prefix
- **Mock TTS Adapter**: Update `get_available_voices()` to return `list[dict]` with minimal metadata

**Success Criteria**:
- All adapters pass `isinstance(adapter, Port)` checks
- Mypy type checking passes with no errors
- Mock and real adapters have identical signatures

### Phase 2: DI Container & Settings

**Objective**: Implement speech service DI with configuration validation.

**Files Modified**:
1. `src/infrastructure/dependency_injection/container.py` (implement STT/TTS methods)
2. `src/infrastructure/config/settings.py` (add validation)

**Implementation**:
```python
# Container.speech_to_text_port()
def speech_to_text_port(self) -> SpeechToTextPort:
    if self._stt_port is None:
        if self.settings.use_mock_stt:
            self._stt_port = MockSTTAdapter()
        else:
            if not self.settings.azure_speech_key:
                raise ValueError("AZURE_SPEECH_KEY not configured")
            if not self.settings.azure_speech_region:
                raise ValueError("AZURE_SPEECH_REGION not configured")

            self._stt_port = AzureSpeechToTextAdapter(
                api_key=self.settings.azure_speech_key,
                region=self.settings.azure_speech_region,
                language=self.settings.azure_speech_language,
            )
    return self._stt_port
```

**Success Criteria**:
- `use_mock_stt=True` → Returns MockSTTAdapter
- `use_mock_stt=False` → Returns AzureSpeechToTextAdapter (if API key present)
- Missing API key raises ValueError with clear message
- Both STT and TTS singletons cached in container

### Phase 3: WebSocket Audio Integration

**Objective**: Implement audio chunk assembly and STT transcription.

**Files Modified**:
1. `src/adapters/api/websocket/interview_handler.py` (implement `handle_audio_chunk`)

**Implementation Steps**:
1. Create audio buffer storage (per interview session)
2. Receive AudioChunkMessage, base64 decode, append to buffer
3. When `is_final=True`, assemble complete audio
4. Convert format if needed (WebM → WAV via ffmpeg or accept as-is)
5. Call `stt_port.transcribe_audio(audio_bytes, language)`
6. Extract text + voice_metrics from result
7. Send TranscriptionMessage to client
8. Send VoiceMetricsMessage to client
9. Pass to orchestrator for answer processing

**Audio Assembly Logic**:
```python
# In-memory buffer per session
audio_buffers: dict[UUID, list[bytes]] = {}

async def handle_audio_chunk(interview_id, data, container):
    audio_data_b64 = data.get("audio_data")
    chunk_index = data.get("chunk_index")
    is_final = data.get("is_final")
    question_id = data.get("question_id")

    # Decode
    audio_chunk = base64.b64decode(audio_data_b64)

    # Append to buffer
    if interview_id not in audio_buffers:
        audio_buffers[interview_id] = []
    audio_buffers[interview_id].append(audio_chunk)

    if is_final:
        # Assemble
        complete_audio = b"".join(audio_buffers[interview_id])
        audio_buffers.pop(interview_id)

        # Transcribe
        stt = container.speech_to_text_port()
        result = await stt.transcribe_audio(complete_audio, language="en-US")

        # Send transcription
        await manager.send_message(interview_id, {
            "type": "transcription",
            "text": result["text"],
            "is_final": True,
            "confidence": result["voice_metrics"]["confidence_score"],
        })

        # Send voice metrics
        await manager.send_message(interview_id, {
            "type": "voice_metrics",
            **result["voice_metrics"],
            "real_time": False,
        })

        # Pass to orchestrator
        await orchestrator.handle_voice_answer(
            audio_bytes=complete_audio,
            question_id=UUID(question_id),
            transcription=result["text"],
            voice_metrics=result["voice_metrics"],
        )
```

**Success Criteria**:
- Audio chunks assembled correctly (verified via WAV header)
- STT transcription returns text + metrics
- Client receives TranscriptionMessage + VoiceMetricsMessage
- No memory leaks (buffer cleaned after assembly)

### Phase 4: Session Orchestrator Voice Support

**Objective**: Add voice answer handling to session orchestrator.

**Files Modified**:
1. `src/adapters/api/websocket/session_orchestrator.py` (add `handle_voice_answer`)
2. `src/application/use_cases/process_answer_adaptive.py` (accept voice_metrics param)

**New Method**:
```python
# session_orchestrator.py
async def handle_voice_answer(
    self,
    audio_bytes: bytes,
    question_id: UUID,
    transcription: str,
    voice_metrics: dict[str, float],
) -> None:
    """Process voice answer with STT transcription and voice metrics."""
    # Validate state
    if self.state != SessionState.QUESTIONING:
        raise ValueError(f"Cannot answer in state {self.state}")

    # Transition to evaluating
    self._transition(SessionState.EVALUATING)

    # Process answer (same as text, but with voice_metrics)
    answer = await self.process_answer_use_case.execute(
        interview_id=self.interview_id,
        question_id=question_id,
        answer_text=transcription,
        voice_metrics=voice_metrics,  # NEW
    )

    # Send evaluation
    await self._send_evaluation(answer)

    # Check follow-up decision
    decision = await self.follow_up_decision_use_case.execute(...)

    if decision["needs_followup"]:
        self._transition(SessionState.FOLLOW_UP)
        await self._generate_and_send_followup(...)
    else:
        await self._send_next_main_question_or_complete()
```

**TTS Integration** (optional audio in QuestionMessage):
```python
async def _send_next_main_question(self) -> None:
    """Send next main question with optional TTS audio."""
    question = await self._get_next_question()

    # Generate TTS audio (optional)
    audio_data_b64 = None
    if self.container.settings.enable_tts:  # Feature flag
        tts = self.container.text_to_speech_port()
        audio_bytes = await tts.synthesize_speech(
            text=question.text,
            voice=self.container.settings.azure_speech_voice,
            speed=1.0,
        )
        audio_data_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Send question
    await manager.send_message(self.interview_id, {
        "type": "question",
        "question_id": str(question.id),
        "text": question.text,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "index": self.current_question_index,
        "total": len(self.question_ids),
        "audio_data": audio_data_b64,
        "audio_format": "wav",
    })
```

**Success Criteria**:
- Voice answers processed with same evaluation flow as text
- Voice metrics stored in Answer entity
- TTS audio included in QuestionMessage (if enabled)
- State machine transitions work correctly for voice flow

### Phase 5: Testing & Validation

**Objective**: Comprehensive unit and integration tests for voice flow.

**Test Files**:
1. `tests/unit/adapters/test_azure_stt_adapter.py` (mock Azure SDK)
2. `tests/unit/adapters/test_azure_tts_adapter.py` (mock Azure SDK)
3. `tests/unit/adapters/test_mock_stt_adapter.py`
4. `tests/unit/adapters/test_mock_tts_adapter.py`
5. `tests/integration/test_voice_interview_flow.py` (end-to-end with mocks)
6. `tests/integration/test_audio_chunking.py` (WebSocket chunk assembly)

**Unit Test Coverage**:
- STT adapter: transcribe_audio returns correct dict structure
- TTS adapter: synthesize_speech returns valid WAV bytes
- Mock adapters: deterministic voice metrics based on audio size
- DI container: mock/real toggle logic
- Audio assembly: chunks → complete audio → STT

**Integration Test**:
```python
async def test_voice_interview_end_to_end():
    """Test complete voice interview flow with mock STT/TTS."""
    # Setup
    container = get_test_container(use_mock_stt=True, use_mock_tts=True)

    # Plan interview
    interview = await plan_interview_use_case.execute(...)

    # Connect WebSocket
    async with websocket_client(f"/ws/interviews/{interview.id}") as ws:
        # Receive first question (with TTS audio)
        msg = await ws.receive_json()
        assert msg["type"] == "question"
        assert msg["audio_data"] is not None  # Base64 WAV

        # Send voice answer (chunked)
        audio_chunks = create_test_audio_chunks()
        for i, chunk in enumerate(audio_chunks):
            await ws.send_json({
                "type": "audio_chunk",
                "audio_data": base64_encode(chunk),
                "chunk_index": i,
                "is_final": i == len(audio_chunks) - 1,
                "question_id": msg["question_id"],
            })

        # Receive transcription
        transcription = await ws.receive_json()
        assert transcription["type"] == "transcription"
        assert transcription["is_final"] is True

        # Receive voice metrics
        metrics = await ws.receive_json()
        assert metrics["type"] == "voice_metrics"
        assert 0 <= metrics["fluency_score"] <= 1

        # Receive evaluation
        evaluation = await ws.receive_json()
        assert evaluation["type"] == "evaluation"
        assert evaluation["voice_metrics"] is not None
```

**Success Criteria**:
- All unit tests pass (85%+ coverage on voice code)
- Integration test passes with mock adapters
- Manual test with real Azure Speech Services (optional, documented)
- No regression in existing text-based interview tests

---

## Success Criteria (Overall)

### Functional Requirements
- ✅ Voice answers work via WebSocket (audio chunks → transcription)
- ✅ Voice metrics extracted (intonation, fluency, confidence, WPM)
- ✅ Voice metrics stored in Answer entity and Evaluation
- ✅ TTS audio generation for questions (optional, feature flag)
- ✅ Mock adapters allow development without Azure API keys
- ✅ Error handling gracefully degrades (voice → text fallback)

### Non-Functional Requirements
- ✅ Clean Architecture maintained (no Azure SDK in domain)
- ✅ Port/Adapter pattern followed (adapters match port contracts)
- ✅ Async throughout (no blocking calls)
- ✅ Test coverage 85%+ on new voice code
- ✅ Documentation updated (README, architecture docs)

### Quality Gates
- ✅ All mypy type checks pass
- ✅ All ruff linting passes
- ✅ All pytest tests pass (unit + integration)
- ✅ No security vulnerabilities (API keys in env vars only)

---

## Risk Assessment

### High Risks
1. **Audio Format Compatibility**
   - **Risk**: Client sends WebM, Azure expects WAV
   - **Mitigation**: Accept multiple formats, convert using ffmpeg or accept as-is (Azure SDK handles formats)
   - **Fallback**: Document supported formats, client-side conversion

2. **Network Latency**
   - **Risk**: Large audio files cause timeouts
   - **Mitigation**: Chunked streaming (max 64KB per chunk), WebSocket timeout config
   - **Fallback**: Client-side compression, quality settings

### Medium Risks
3. **Azure Speech API Costs**
   - **Risk**: Frequent STT/TTS calls expensive
   - **Mitigation**: Mock adapters for dev/test, feature flags for TTS
   - **Monitoring**: Track API usage in logs

4. **Voice Metrics Accuracy**
   - **Risk**: Azure metrics may not reflect interview quality
   - **Mitigation**: Normalize scores, document score interpretation
   - **Future**: Train custom voice quality models

### Low Risks
5. **Memory Leaks**
   - **Risk**: Audio buffers not cleaned
   - **Mitigation**: Clear buffer after assembly, session timeout cleanup
   - **Monitoring**: Memory profiling in tests

---

## Security Considerations

### API Key Management
- ✅ Store Azure Speech API key in `.env.local` (gitignored)
- ✅ Validate key presence before initializing adapter
- ✅ Use environment variables in production (no hardcoded keys)

### Audio Data Protection
- ✅ Audio transmitted via WSS (WebSocket Secure) in production
- ✅ Audio not persisted to disk (in-memory only, unless explicitly saved)
- ✅ Audio buffers cleared immediately after processing

### Rate Limiting
- ⏳ Add per-user rate limiting for voice answers (future)
- ⏳ Monitor Azure Speech API quota usage

---

## Next Steps After Implementation

### Phase 6: Production Optimization (Future)
1. **Audio Compression**: Client-side Opus encoding for bandwidth reduction
2. **Streaming STT**: Real-time transcription during speaking (Azure SDK supports)
3. **Voice Quality ML**: Custom model for interview-specific voice analysis
4. **Multilingual Support**: Language detection, multi-language TTS voices

### Phase 7: Analytics & Insights (Future)
1. **Voice Analytics Dashboard**: Aggregate voice metrics across candidates
2. **Correlation Analysis**: Voice quality vs interview success rate
3. **Personalized Feedback**: "You speak 20% faster than average, try slowing down"

---

## ✅ Design Decisions (User Confirmed)

1. **Audio Format Support**: **WebM (primary) + WAV (fallback)**
   - **Decision**: Accept WebM for real-time (lowest latency ~20-50ms), WAV as fallback
   - **Reasoning**: WebM (Opus codec) is browser-native, optimal for WebRTC real-time streaming
   - **Implementation**: Azure SDK handles both formats automatically

2. **TTS Caching**: **Yes, LRU cache (128 entries)**
   - **Decision**: Cache generated TTS audio keyed by (text, voice, speed)
   - **Reasoning**: Reduces Azure API costs, faster response times for repeated questions
   - **Implementation**: `functools.lru_cache` with max size 128

3. **Voice Metrics Weighting**: **70% theoretical + 30% speaking (configurable)**
   - **Decision**: Keep current weighting, make configurable via settings
   - **Config**: `VOICE_METRICS_WEIGHT=0.3` in settings
   - **Reasoning**: Content quality more important than delivery, but voice quality matters

4. **Streaming Mode**: **Real-time STT (streaming transcription)**
   - **Decision**: Implement real-time streaming STT (not batch)
   - **Reasoning**: Better UX with live transcription feedback, lower perceived latency
   - **Implementation**: Azure SDK continuous recognition with interim results

5. **Audio Storage**: **Optional (disabled by default)**
   - **Decision**: Feature flag `SAVE_AUDIO=false` by default
   - **Storage**: Azure Blob if enabled, 30-day retention
   - **Reasoning**: Privacy concerns, GDPR compliance (right to deletion)

---

## References

### Internal Documentation
- [System Architecture](../../docs/system-architecture.md) - Clean Architecture details
- [Codebase Summary](../../docs/codebase-summary.md) - Project structure
- [Code Standards](../../docs/code-standards.md) - Coding conventions

### External Documentation
- [Azure Speech SDK Docs](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/)
- [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Plan Status**: Ready for Implementation
**Estimated Completion**: 2025-11-18 (3-4 days)
**Maintainer**: Elios Development Team
