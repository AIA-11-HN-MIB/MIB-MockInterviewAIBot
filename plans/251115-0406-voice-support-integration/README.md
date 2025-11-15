# Voice Support Integration - Plan Summary

**Plan ID**: `251115-0406-voice-support-integration`
**Created**: 2025-11-15
**Status**: Ready for Implementation
**Total Effort**: 14-18 hours (3-4 days)

---

## Quick Start

Read phases in order:
1. **[plan.md](./plan.md)** - Executive summary, architecture, success criteria
2. **[phase-1-adapter-alignment.md](./phase-1-adapter-alignment.md)** - Fix adapter signatures (2-3h)
3. **[phase-2-di-container-settings.md](./phase-2-di-container-settings.md)** - DI implementation (1-2h)
4. **[phase-3-websocket-audio.md](./phase-3-websocket-audio.md)** - Audio chunking + STT (4-5h)
5. **[phase-4-orchestrator-voice.md](./phase-4-orchestrator-voice.md)** - Voice answer handling (3-4h)
6. **[phase-5-testing.md](./phase-5-testing.md)** - Tests + validation (4-5h)

---

## Phase Overview

| Phase | Goal | Duration | Risk | Dependencies |
|-------|------|----------|------|--------------|
| 1 | Fix Azure adapter signatures to match ports | 2-3h | Low | None |
| 2 | Implement DI container with mock/real toggle | 1-2h | Low | Phase 1 |
| 3 | WebSocket audio chunk handling + STT | 4-5h | Medium | Phase 1-2 |
| 4 | Session orchestrator voice support | 3-4h | Medium | Phase 1-3 |
| 5 | Comprehensive testing | 4-5h | Low | Phase 1-4 |

---

## Critical Issues Fixed

1. **Adapter Signature Mismatch**: Azure TTS adapter has extra `language` param not in port interface
   - **Solution**: Remove `language` param, derive from voice name

2. **DI Container Stubs**: Methods defined but not implemented
   - **Solution**: Implement with mock/real toggle based on settings flags

3. **No WebSocket Audio Handling**: `handle_audio_chunk()` stub exists but empty
   - **Solution**: Implement audio assembly + STT transcription

4. **No Voice Answer Support**: Orchestrator only handles text answers
   - **Solution**: Add `handle_voice_answer()` method with voice metrics

---

## Key Deliverables

### Code Changes
- 2 port interfaces updated (TTS)
- 4 adapters fixed (Azure STT/TTS, Mock STT/TTS)
- 1 DI container completed
- 1 WebSocket handler implemented
- 1 session orchestrator enhanced
- 1 use case updated (ProcessAnswerAdaptive)

### Tests
- 5 unit test files
- 2 integration test files
- 85%+ coverage on voice code

### Documentation
- Architecture docs updated
- README.md updated (Phase 2 status: Voice Support ✅)
- `.env.example` updated with Azure Speech config

---

## Success Criteria

✅ Voice interviews work end-to-end via WebSocket
✅ Audio chunks → STT transcription → answer evaluation
✅ Voice metrics (intonation, fluency, confidence, WPM) extracted
✅ TTS audio generation for questions (optional)
✅ Mock adapters allow development without Azure API keys
✅ Error handling gracefully degrades (voice → text fallback)
✅ All tests pass (unit + integration)
✅ Clean Architecture maintained (no Azure SDK in domain)

---

## Risks & Mitigations

### High Risks
1. **Audio Format Compatibility** (Client sends WebM, Azure expects WAV)
   - **Mitigation**: Accept multiple formats, Azure SDK handles conversion

2. **Network Latency** (Large audio files cause timeouts)
   - **Mitigation**: Chunked streaming (max 64KB/chunk), WebSocket timeout config

### Medium Risks
3. **Azure Speech API Costs** (Frequent STT/TTS calls expensive)
   - **Mitigation**: Mock adapters for dev/test, feature flags for TTS

4. **Voice Metrics Accuracy** (Azure metrics may not reflect interview quality)
   - **Mitigation**: Normalize scores, document interpretation

---

## Environment Setup

### Required for Development (Mock Mode)
```bash
# .env.local
USE_MOCK_STT=true
USE_MOCK_TTS=true
```

### Required for Production (Real Azure)
```bash
# .env.local
USE_MOCK_STT=false
USE_MOCK_TTS=false
AZURE_SPEECH_KEY=your-api-key-here
AZURE_SPEECH_REGION=eastus
AZURE_SPEECH_LANGUAGE=en-US
AZURE_SPEECH_VOICE=en-US-AriaNeural
```

---

## Unresolved Questions

1. **Audio Format Support**: Accept WebM/WAV/MP3 or require specific format?
   - **Recommendation**: Accept all, rely on Azure SDK format detection

2. **TTS Caching**: Cache generated TTS audio for repeated questions?
   - **Recommendation**: Yes, LRU cache (128 entries) keyed by (text, voice, speed)

3. **Voice Metrics Weighting**: 70% theoretical + 30% speaking?
   - **Recommendation**: Keep current, make configurable

4. **Streaming vs Batch**: Streaming STT or wait for complete audio?
   - **Recommendation**: Start with batch, add streaming in Phase 6 (future)

5. **Audio Storage**: Save audio files for review/training?
   - **Recommendation**: Optional feature flag (`save_audio=false` by default)

---

## Next Steps After Implementation

1. **Update README.md**: Mark Phase 2 (Voice Support) as ✅
2. **Manual Testing**: Test with real Azure Speech Services
3. **Performance Benchmarks**: Measure latency, API costs
4. **Phase 6 Planning**: Streaming STT, voice quality ML, multilingual support

---

## References

- [System Architecture](../../docs/system-architecture.md)
- [Codebase Summary](../../docs/codebase-summary.md)
- [Azure Speech SDK Docs](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/)
- [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)
