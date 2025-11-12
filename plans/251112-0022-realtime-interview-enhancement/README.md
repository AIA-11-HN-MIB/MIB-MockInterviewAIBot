# Real-time Interview Enhancement - Implementation Plan

**Plan ID**: 251112-0022
**Created**: 2025-11-12 00:22
**Status**: Ready for Implementation
**Estimated Duration**: 4 weeks (21 working days)

## 📋 Overview

Comprehensive plan to enhance Elios AI Interview Service with real-time TTS/STT integration and adaptive follow-up question loops. Transforms basic WebSocket handler into production-ready interview orchestrator with voice analysis, iterative gap-based questioning, and comprehensive feedback generation.

## 🎯 Goals

1. **Speech Integration**: Production Azure Speech SDK adapters with voice metrics (intonation, fluency, confidence)
2. **Adaptive Follow-up Loop**: Iterative gap-based questioning (max 3 per main question)
3. **Multi-Dimensional Evaluation**: Combined theoretical (70%) + speaking (30%) scoring
4. **Session Orchestration**: State machine pattern for robust session management
5. **Comprehensive Summary**: Final report aggregating all evaluations with LLM-powered recommendations

## 📂 Plan Structure

### Core Plan Document
- **[plan.md](plan.md)** - Executive summary, architecture, timeline, risks

### Phase Documents (7 phases)

1. **[phase1-speech-integration.md](phase1-speech-integration.md)** (3 days)
   - Enhance STT/TTS port interfaces with voice metrics
   - Implement Azure Speech SDK adapters
   - Update mock adapters with realistic simulations
   - Create audio streaming DTOs

2. **[phase2-websocket-protocol.md](phase2-websocket-protocol.md)** (2 days)
   - Define enhanced message types (audio_chunk, voice_metrics, etc.)
   - Implement binary frame handling for audio
   - Add structured error handling with recovery options
   - Update connection manager for binary support

3. **[phase3-enhanced-evaluation.md](phase3-enhanced-evaluation.md)** (3 days)
   - Add voice metrics to Answer model
   - Implement parallel evaluation (LLM + Speech async)
   - Create CombineEvaluationUseCase for weighted scoring
   - Update evaluation message format

4. **[phase4-followup-engine.md](phase4-followup-engine.md)** (4 days)
   - Create FollowUpDecisionUseCase with break conditions
   - Implement iterative follow-up loop in WebSocket handler
   - Add session state tracking (follow-up counters)
   - Implement gap accumulation across iterations

5. **[phase5-session-orchestration.md](phase5-session-orchestration.md)** (3 days)
   - Create InterviewSessionOrchestrator with state machine
   - Refactor WebSocket handler to use orchestrator
   - Implement progress tracking and state persistence
   - Add error recovery mechanisms

6. **[phase6-summary-generation.md](phase6-summary-generation.md)** (2 days)
   - Create GenerateSummaryUseCase
   - Implement gap progression analysis
   - Add LLM-powered recommendation generation
   - Update CompleteInterviewUseCase

7. **[phase7-testing.md](phase7-testing.md)** (4 days)
   - Unit tests for all new use cases (80%+ coverage)
   - Integration tests with real Azure Speech SDK
   - E2E test for complete interview session
   - Performance testing (latency, concurrency)

## 🚀 Quick Start

### For Implementers

1. **Read [plan.md](plan.md)** for executive summary and architecture
2. **Review current state** in referenced source files
3. **Start with Phase 1** and work sequentially through phases
4. **Use Todo lists** in each phase document to track progress
5. **Run tests** after each phase to validate implementation

### For Reviewers

1. **Check [plan.md](plan.md)** for overall approach and risks
2. **Review phase documents** for technical details
3. **Validate success criteria** in each phase
4. **Verify test coverage** meets 80% target

## 📊 Current State

**Implemented ✅**:
- Basic WebSocket handler with text answer support
- Adaptive evaluation with gap detection (single follow-up)
- Follow-up question model and repository
- Answer model with similarity_score and gaps fields
- Mock adapters for development (6 total)

**Missing ❌**:
- Audio streaming protocol (binary frames)
- Voice metrics analysis (intonation, fluency, confidence)
- Parallel evaluation (LLM + Speech concurrent)
- Iterative follow-up loop (max 3 iterations)
- Final summary generation use case
- Session state machine

## 🎯 Target Architecture

```
Session Flow:
1. WebSocket connects → Send Q1 (TTS audio + text)
2. FOR each main question (i=1..n):
   ├─ Receive answer (audio)
   ├─ STT conversion → text + voice metrics
   ├─ Parallel evaluation: LLM semantic + Voice analysis
   ├─ Combine evaluations → overall_evaluation
   ├─ Store evaluation
   ├─ WHILE (need_follow_up AND count < 3):
   │  ├─ LLM decides gaps
   │  ├─ Generate follow-up question
   │  ├─ TTS → audio
   │  ├─ Send to frontend
   │  ├─ Receive answer
   │  ├─ STT + evaluate (parallel)
   │  ├─ Store evaluation
   │  ├─ Check gaps again
   │  └─ Increment counter
   └─ Move to next main question
3. Finalization:
   ├─ Aggregate all evaluations (main + follow-ups)
   ├─ Generate comprehensive summary (LLM)
   ├─ Update status = COMPLETED
   └─ Send summary to frontend
```

## 🔧 Key Technical Decisions

### Speech Services
- **STT**: Azure Speech SDK (production), Mock adapter (dev/test)
- **TTS**: Azure Neural Voices (production), Edge TTS (fallback)
- **Audio Format**: 16kHz mono WAV for processing, WebM Opus from browser

### Voice Metrics
- **Intonation**: Pitch variance analysis (custom)
- **Fluency**: Words per minute normalized (120-160 WPM baseline)
- **Confidence**: Azure Speech SDK confidence scores

### Evaluation Weighting
- **Theoretical**: 70% (semantic similarity, completeness, relevance)
- **Speaking**: 30% (intonation, fluency, confidence)

### Follow-up Break Conditions
1. Similarity >= 0.8 (answer quality meets threshold)
2. No confirmed gaps (gaps.confirmed == False)
3. Max 3 iterations reached (hard limit)

### Session State Management
- **Pattern**: State machine (IDLE → QUESTIONING → EVALUATING → FOLLOW_UP → COMPLETE)
- **Storage**: In-memory (Phase 5), Redis (future enhancement)
- **Tracking**: Follow-up count per main question, evaluation history

## 📈 Success Metrics

**Functional**:
- ✅ Audio streaming works (upload + playback)
- ✅ Voice metrics extracted (3 metrics per answer)
- ✅ Adaptive follow-up loop generates 0-3 questions per main question
- ✅ Final summary aggregates all evaluations
- ✅ Interview status updates to COMPLETED

**Non-Functional**:
- ✅ Average latency <3s (question → answer → evaluation)
- ✅ Handle 10+ concurrent interviews
- ✅ Test coverage >=80%
- ✅ Error rate <5% (speech recognition, TTS)
- ✅ Audio quality acceptable (>=16kHz, no drops)

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Azure Speech SDK complexity | High | Use mock adapters for dev, gradual rollout |
| Follow-up loop infinite loop | Critical | Hard limit max 3, timeout 30s per iteration |
| Performance degradation | Medium | Optimize LLM prompts, streaming STT, timeout safety |
| State management complexity | Medium | State machine pattern, extensive unit tests |
| Audio format compatibility | High | Test multiple browsers, add format conversion |

## 🔗 Related Documentation

- [System Architecture](../../docs/system-architecture.md) - Architecture patterns
- [Codebase Summary](../../docs/codebase-summary.md) - Project structure
- [Code Standards](../../docs/code-standards.md) - Coding conventions
- [WebSocket Handler](../../src/adapters/api/websocket/interview_handler.py) - Current implementation
- [Adaptive Evaluation](../../src/application/use_cases/process_answer_adaptive.py) - Current evaluation logic

## 📝 Implementation Checklist

**Phase 1: Speech Integration** (3 days)
- [ ] Enhance STT/TTS port interfaces
- [ ] Implement Azure Speech SDK adapters
- [ ] Update mock adapters with voice metrics
- [ ] Create audio streaming DTOs

**Phase 2: WebSocket Protocol** (2 days)
- [ ] Define enhanced message types
- [ ] Implement binary frame handling
- [ ] Add structured error handling
- [ ] Update connection manager

**Phase 3: Enhanced Evaluation** (3 days)
- [ ] Add voice metrics to Answer model
- [ ] Implement parallel evaluation
- [ ] Create CombineEvaluationUseCase
- [ ] Update evaluation messages

**Phase 4: Follow-up Engine** (4 days)
- [ ] Create FollowUpDecisionUseCase
- [ ] Implement iterative follow-up loop
- [ ] Add session state tracking
- [ ] Implement gap accumulation

**Phase 5: Session Orchestration** (3 days)
- [ ] Create InterviewSessionOrchestrator
- [ ] Refactor WebSocket handler
- [ ] Implement progress tracking
- [ ] Add error recovery

**Phase 6: Summary Generation** (2 days)
- [ ] Create GenerateSummaryUseCase
- [ ] Implement gap progression analysis
- [ ] Add LLM recommendation generation
- [ ] Update CompleteInterviewUseCase

**Phase 7: Testing** (4 days)
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests with real adapters
- [ ] E2E test for full interview
- [ ] Performance testing

## ❓ Unresolved Questions

1. **Voice metrics**: Azure Speech SDK prosody detection vs custom analysis?
2. **Audio format**: WebM Opus vs WAV vs MP3 for browser compatibility?
3. **State persistence**: Redis vs PostgreSQL for session state?
4. **Follow-up limit**: Should max 3 be configurable per interview?
5. **Performance target**: Is <3s realistic for LLM + STT + TTS pipeline?
6. **Error handling**: Speech errors fall back to text mode or retry?
7. **Concurrency**: PostgreSQL connection limits for concurrent interviews?
8. **Monitoring**: Which metrics to track (latency, error rate, audio quality)?

## 👥 Team & Communication

**Roles**:
- **Implementer**: Execute phases sequentially, run tests, update docs
- **Reviewer**: Code review after each phase, validate architecture
- **Tester**: Write tests, validate coverage, performance testing
- **Product Owner**: Prioritize features, validate UX, approve changes

**Communication**:
- Daily standup: Progress updates, blockers, questions
- Phase reviews: After each phase completion
- Code reviews: PR per phase or major component
- Demo: After Phase 4 (working follow-up loop) and Phase 7 (complete system)

---

**Status**: Ready for implementation
**Next Action**: Begin Phase 1 - Speech Integration Foundation
**Estimated Completion**: Week of 2025-12-09
