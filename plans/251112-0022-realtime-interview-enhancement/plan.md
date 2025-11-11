# Real-time Interview Enhancement Plan

**Plan ID**: 251112-0022
**Created**: 2025-11-12 00:22
**Status**: Draft
**Complexity**: High (7 phases, ~3-4 weeks)

## Executive Summary

Enhance real-time interview system with TTS/STT integration and adaptive follow-up question loop. Current implementation has basic WebSocket handler and adaptive evaluation logic, but lacks voice integration, parallel processing, and iterative follow-up cycles. Target architecture implements audio streaming, voice metrics analysis, gap-based follow-up generation (max 3 per question), and comprehensive final summary.

## Current State

**Implemented ✅**:
- WebSocket handler (`interview_handler.py` - 435 lines) with text answer support
- Adaptive answer evaluation (`process_answer_adaptive.py` - 418 lines) with gap detection
- Follow-up question model and repository
- Answer model with similarity_score and gaps fields
- TTS/STT port interfaces (no production implementation)
- Mock adapters for development (6 total)

**Gaps ❌**:
- No audio streaming protocol (binary frames)
- No voice metrics analysis (intonation, fluency, confidence)
- No parallel evaluation (LLM + Speech concurrent)
- No iterative follow-up loop (currently 1:1 mapping)
- No final summary generation use case
- No session state tracking (follow-up counters, evaluation history)

## Target Architecture

### Enhanced Interview Flow

```
1. Session Init: WebSocket → Fetch questions → Send Q1 (TTS audio + text)
2. FOR each main question (i=1..n):
   ├─ Receive answer (audio)
   ├─ STT conversion
   ├─ Parallel evaluation:
   │  ├─ LLM semantic analysis
   │  └─ Voice metrics (intonation, fluency, confidence)
   ├─ Combine evaluations → overall_evaluation
   ├─ Store evaluation
   ├─ WHILE (need_follow_up AND count < 3):
   │  ├─ LLM decides gaps
   │  ├─ Generate follow-up question
   │  ├─ TTS conversion
   │  ├─ Send to frontend
   │  ├─ Receive answer (audio)
   │  ├─ STT + evaluate (same as main)
   │  ├─ Store evaluation
   │  ├─ Check gaps again
   │  └─ Increment counter
   └─ Move to next main question
3. Finalization:
   ├─ Fetch all evaluations (main + follow-ups)
   ├─ Generate final summary (LLM)
   ├─ Update status = COMPLETED
   └─ Send summary to frontend
```

### Key Enhancements

**Speech Integration**:
- Binary WebSocket frames for audio chunks
- Real-time STT streaming (Azure Speech SDK)
- TTS with voice selection (Edge TTS or Azure)
- Voice metrics analysis (pitch, pace, pauses)

**Adaptive Follow-up Loop**:
- Iterative gap-based questioning (max 3 per main question)
- Session state tracking (follow-up counters per question)
- Break conditions: gaps filled OR max reached OR similarity >80%
- Each follow-up fully evaluated same as main questions

**Enhanced Evaluation**:
- Parallel async processing (LLM + Speech)
- Combined scoring (semantic 70% + voice 30%)
- Granular gap tracking (concepts, keywords, severity)
- Evaluation history for summary generation

**Session Orchestration**:
- State machine pattern (IDLE → QUESTIONING → EVALUATING → FOLLOW_UP → COMPLETE)
- Progress tracking (current question index, follow-up count)
- Error recovery (retry logic, fallback to text)
- Performance monitoring (<3s latency target)

## Implementation Phases

### Phase 1: Speech Integration Foundation (3 days)
- Enhance STT/STT port interfaces with voice metrics
- Implement Azure Speech SDK adapters
- Create audio streaming DTOs
- Update mock adapters with voice metrics simulation
- **Deliverable**: Production-ready speech adapters

### Phase 2: WebSocket Message Protocol (2 days)
- Define audio message types (audio_chunk, voice_metrics, etc.)
- Implement binary frame handling
- Add error handling for audio failures
- Create message validation layer
- **Deliverable**: Complete WebSocket protocol spec

### Phase 3: Enhanced Answer Evaluation (3 days)
- Add voice metrics to ProcessAnswerAdaptiveUseCase
- Implement parallel evaluation (LLM + Speech async)
- Create CombineEvaluationUseCase for weighted scores
- Update Answer model with voice_metrics field
- **Deliverable**: Multi-dimensional evaluation system

### Phase 4: Adaptive Follow-up Engine (4 days)
- Create FollowUpDecisionUseCase (gap-based logic)
- Implement iterative follow-up loop in WebSocket handler
- Add session state tracking (follow-up counters)
- Create break condition logic (max 3, similarity >80%, no gaps)
- **Deliverable**: Working follow-up loop with max 3 iterations

### Phase 5: Session Orchestration (3 days)
- Refactor WebSocket handler as state machine
- Implement main question loop with follow-up nesting
- Add progress tracking and session state persistence
- Create error recovery mechanisms
- **Deliverable**: Robust session orchestrator

### Phase 6: Final Summary Generation (2 days)
- Create GenerateSummaryUseCase (aggregate all evaluations)
- Implement comprehensive feedback generation (LLM)
- Add performance metrics calculation
- Update Interview status to COMPLETED
- **Deliverable**: Final summary endpoint

### Phase 7: Testing & Integration (4 days)
- Unit tests for all new use cases (80%+ coverage)
- Integration tests for WebSocket flow (real adapters)
- E2E test for complete interview session
- Performance testing (latency, concurrency)
- **Deliverable**: Test suite with CI/CD integration

## Technical Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| Real-time audio streaming latency | High (>5s breaks flow) | Use streaming STT, chunk audio (1-2s), optimize network |
| Parallel evaluation coordination | Medium | Use asyncio.gather(), timeout safety nets |
| Follow-up loop state management | High | State machine pattern, persist session state |
| Voice metrics accuracy | Medium | Use Azure Speech SDK confidence scores, fallback to mock |
| Error recovery without breaking session | High | Try-except wrappers, graceful degradation to text |

## Success Criteria

**Functional**:
- ✅ Audio streaming works (upload + playback)
- ✅ Voice metrics extracted (3 metrics: intonation, fluency, confidence)
- ✅ Adaptive follow-up loop generates 0-3 questions per main question
- ✅ Final summary aggregates all evaluations (main + follow-ups)
- ✅ Interview status updates to COMPLETED after final question

**Non-Functional**:
- ✅ Average latency <3s (question → answer → evaluation)
- ✅ Audio quality acceptable (>=16kHz, no drops)
- ✅ Handle 10+ concurrent interviews
- ✅ Error rate <5% (speech recognition, TTS)
- ✅ Test coverage >=80%

## Dependencies

**Existing Ports**:
- SpeechToTextPort (needs enhancement)
- TextToSpeechPort (needs enhancement)
- LLMPort (already complete)
- VectorSearchPort (already complete)

**New Use Cases**:
- CombineEvaluationUseCase
- FollowUpDecisionUseCase
- GenerateSummaryUseCase
- VoiceMetricsAnalysisUseCase (or extend STT port)

**External Libraries**:
- Azure Speech SDK (STT/TTS production)
- Edge TTS (TTS alternative)
- asyncio (parallel processing)
- websockets (binary frame support)

## Risks & Mitigation

**Risk: Azure Speech SDK complexity**
- Impact: High (blocks speech integration)
- Mitigation: Use mock adapters for development, gradual rollout

**Risk: Follow-up loop infinite loop**
- Impact: Critical (hangs session)
- Mitigation: Hard limit max 3, timeout per iteration (30s)

**Risk: Performance degradation with parallel eval**
- Impact: Medium (latency >5s)
- Mitigation: Optimize LLM prompts, use streaming STT, timeout safety

**Risk: State management complexity**
- Impact: Medium (bugs in follow-up logic)
- Mitigation: State machine pattern, extensive unit tests

## Timeline

**Week 1**: Phases 1-2 (Speech foundation + WebSocket protocol)
**Week 2**: Phases 3-4 (Enhanced evaluation + Follow-up engine)
**Week 3**: Phase 5 (Session orchestration)
**Week 4**: Phases 6-7 (Summary generation + Testing)

**Total**: ~21 working days (4 weeks)

## Related Documentation

- [System Architecture](../../docs/system-architecture.md) - Architecture patterns
- [Codebase Summary](../../docs/codebase-summary.md) - Project structure
- [WebSocket Handler](../../src/adapters/api/websocket/interview_handler.py) - Current implementation
- [Adaptive Answer Evaluation](../../src/application/use_cases/process_answer_adaptive.py) - Evaluation logic

## Phase Files

1. [Phase 1: Speech Integration Foundation](phase1-speech-integration.md)
2. [Phase 2: WebSocket Message Protocol](phase2-websocket-protocol.md)
3. [Phase 3: Enhanced Answer Evaluation](phase3-enhanced-evaluation.md)
4. [Phase 4: Adaptive Follow-up Engine](phase4-followup-engine.md)
5. [Phase 5: Session Orchestration](phase5-session-orchestration.md)
6. [Phase 6: Final Summary Generation](phase6-summary-generation.md)
7. [Phase 7: Testing & Integration](phase7-testing.md)

## Unresolved Questions

1. **Voice metrics**: Should we use Azure Speech SDK's built-in prosody detection or custom analysis?
2. **Audio format**: WebM Opus vs WAV vs MP3 for browser compatibility?
3. **State persistence**: Store session state in Redis or PostgreSQL?
4. **Follow-up limit**: Should max 3 be configurable per interview difficulty?
5. **Performance target**: Is <3s realistic for LLM + STT + TTS pipeline?
6. **Error handling**: Should speech errors fall back to text mode or retry?
7. **Concurrency**: How many concurrent interviews can Neon PostgreSQL handle?
8. **Monitoring**: Which metrics to track (latency, error rate, audio quality)?
