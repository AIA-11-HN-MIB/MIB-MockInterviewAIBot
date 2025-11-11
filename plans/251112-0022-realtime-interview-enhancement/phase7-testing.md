# Phase 7: Testing & Integration

**Duration**: 4 days
**Priority**: High
**Dependencies**: All previous phases

## Context

Comprehensive testing of entire real-time interview system with TTS/STT integration and adaptive follow-up loops.

## Requirements

### Test Coverage Targets

**Unit Tests**: >=80% coverage
- All use cases
- All adapters
- Voice metrics calculation
- State machine transitions
- Gap detection logic

**Integration Tests**:
- WebSocket message flow
- Speech SDK integration (Azure)
- Database operations
- Follow-up loop iterations

**E2E Tests**:
- Complete interview session (text + voice)
- Adaptive follow-up cycles (0-3)
- Error recovery scenarios
- Concurrent interviews

**Performance Tests**:
- Latency benchmarks (<3s target)
- Concurrency limits (10+ concurrent)
- Audio streaming performance
- Memory usage

## Test Plan

### Unit Tests

```python
# tests/unit/test_combine_evaluation.py
class TestCombineEvaluationUseCase:
    def test_weighted_scoring(self):
        """Test theoretical (70%) + speaking (30%) weights."""
        use_case = CombineEvaluationUseCase()
        theoretical_eval = AnswerEvaluation(score=80, ...)
        voice_metrics = {"intonation_score": 0.9, ...}

        result = use_case.execute(theoretical_eval, voice_metrics)

        expected_score = 80 * 0.7 + 85 * 0.3  # ~81.5
        assert abs(result["overall_score"] - expected_score) < 1.0

# tests/unit/test_followup_decision.py
class TestFollowUpDecisionUseCase:
    def test_max_followups_reached(self):
        """Test loop exits when 3 follow-ups exist."""
        # Mock 3 existing follow-ups
        decision = await use_case.execute(...)
        assert decision["needs_followup"] is False
        assert "Max follow-ups" in decision["reason"]

    def test_similarity_threshold_met(self):
        """Test loop exits when similarity >= 0.8."""
        answer = Answer(similarity_score=0.85, ...)
        decision = await use_case.execute(...)
        assert decision["needs_followup"] is False
```

### Integration Tests

```python
# tests/integration/test_websocket_flow.py
class TestWebSocketInterviewFlow:
    async def test_complete_interview_with_followups(self):
        """Test full interview: 3 main Q + 2 follow-ups."""
        async with websocket_client(interview_id) as ws:
            # Receive first question
            msg = await ws.receive_json()
            assert msg["type"] == "question"

            # Submit answer with low similarity
            await ws.send_json({
                "type": "text_answer",
                "question_id": msg["question_id"],
                "answer_text": "Incomplete answer..."
            })

            # Expect evaluation + follow-up
            eval_msg = await ws.receive_json()
            assert eval_msg["type"] == "evaluation"

            followup_msg = await ws.receive_json()
            assert followup_msg["type"] == "follow_up_question"

            # Answer follow-up
            await ws.send_json({
                "type": "text_answer",
                "question_id": followup_msg["question_id"],
                "answer_text": "Better answer with missing concepts..."
            })

            # Expect evaluation + next main question (or another follow-up)
            eval_msg2 = await ws.receive_json()
            next_msg = await ws.receive_json()

            # Continue until interview complete
            # ...

# tests/integration/test_speech_adapters.py
class TestAzureSpeechIntegration:
    async def test_stt_with_voice_metrics(self):
        """Test real Azure STT with voice metrics extraction."""
        adapter = AzureSpeechToTextAdapter(...)
        audio_bytes = load_test_audio("sample_answer.wav")

        result = await adapter.transcribe_audio(audio_bytes)

        assert result["text"]
        assert "voice_metrics" in result
        assert 0 <= result["voice_metrics"]["intonation_score"] <= 1
        assert result["voice_metrics"]["speaking_rate_wpm"] > 0
```

### E2E Tests

```python
# tests/e2e/test_full_interview_session.py
class TestFullInterviewSession:
    async def test_interview_with_adaptive_followups(self):
        """Test complete interview flow end-to-end."""
        # 1. Create candidate
        candidate = await create_candidate(...)

        # 2. Upload and analyze CV
        cv_analysis = await upload_cv(candidate.id, "sample_cv.pdf")

        # 3. Plan interview (generates questions)
        interview = await plan_interview(candidate.id, cv_analysis.id)

        # 4. Connect WebSocket and conduct interview
        async with websocket_client(interview.id) as ws:
            questions_answered = 0
            followups_received = 0

            while questions_answered < len(interview.question_ids):
                # Receive question
                msg = await ws.receive_json()

                if msg["type"] == "question":
                    questions_answered += 1
                    # Submit answer with varying quality
                    await submit_answer(ws, msg["question_id"])

                elif msg["type"] == "follow_up_question":
                    followups_received += 1
                    # Answer follow-up
                    await submit_answer(ws, msg["question_id"])

                elif msg["type"] == "interview_complete":
                    break

            # Verify interview completed
            assert followups_received > 0  # At least some follow-ups
            assert followups_received <= len(interview.question_ids) * 3  # Max 3 per Q

        # 5. Fetch final summary
        summary = await get_interview_summary(interview.id)

        assert summary["overall_score"] > 0
        assert summary["total_follow_ups"] == followups_received
        assert len(summary["strengths"]) > 0
        assert len(summary["recommendations"]) > 0
```

### Performance Tests

```python
# tests/performance/test_latency.py
class TestInterviewPerformance:
    async def test_average_latency(self):
        """Test average latency <3s per question."""
        latencies = []

        for _ in range(10):
            start = time.time()
            # Submit answer → receive evaluation
            await submit_and_wait_for_eval(...)
            latency = time.time() - start
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 3.0, f"Avg latency {avg_latency:.2f}s exceeds 3s"

    async def test_concurrent_interviews(self):
        """Test handling 10 concurrent interviews."""
        interviews = [create_interview() for _ in range(10)]

        # Conduct all interviews concurrently
        results = await asyncio.gather(
            *[conduct_interview(i) for i in interviews]
        )

        # All should complete successfully
        assert all(r["status"] == "completed" for r in results)
```

## Implementation Steps

### Day 1: Unit Tests

**Step 1**: Write unit tests for all use cases
- CombineEvaluationUseCase
- FollowUpDecisionUseCase
- GenerateSummaryUseCase

**Step 2**: Write unit tests for adapters
- Voice metrics calculation
- Mock adapters

**Step 3**: Run coverage report
- Measure coverage
- Fill gaps to reach 80%

### Day 2: Integration Tests

**Step 1**: Write WebSocket flow tests
- Text answer flow
- Audio answer flow
- Follow-up loop

**Step 2**: Write adapter integration tests
- Azure Speech SDK (with test account)
- PostgreSQL operations

### Day 3: E2E Tests

**Step 1**: Write full interview E2E test
- Complete flow from CV upload to summary
- Verify adaptive follow-ups
- Check final summary quality

**Step 2**: Write error scenario tests
- Network failures
- Audio errors
- Timeout handling

### Day 4: Performance & Cleanup

**Step 1**: Write performance tests
- Latency benchmarks
- Concurrency tests
- Memory profiling

**Step 2**: Code review and refactoring
- Optimize slow paths
- Refactor complex code
- Update documentation

## Todo List

**Day 1**:
- [ ] Write unit tests for CombineEvaluationUseCase
- [ ] Write unit tests for FollowUpDecisionUseCase
- [ ] Write unit tests for GenerateSummaryUseCase
- [ ] Write unit tests for voice metrics calculation
- [ ] Run coverage report, target 80%

**Day 2**:
- [ ] Write WebSocket flow integration tests
- [ ] Write Azure Speech SDK integration tests
- [ ] Write database operation integration tests
- [ ] Test follow-up loop with mocks

**Day 3**:
- [ ] Write E2E test for full interview session
- [ ] Write E2E test for error scenarios
- [ ] Write E2E test for concurrent interviews
- [ ] Validate against real Azure Speech SDK

**Day 4**:
- [ ] Write latency benchmarks
- [ ] Write concurrency tests
- [ ] Profile memory usage
- [ ] Code review and refactoring
- [ ] Update all documentation

## Success Criteria

- ✅ Unit test coverage >=80%
- ✅ All integration tests pass with real adapters
- ✅ E2E test covers full interview flow
- ✅ Average latency <3s per question
- ✅ Handles 10+ concurrent interviews
- ✅ No memory leaks detected
- ✅ All error scenarios handled gracefully

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Azure Speech SDK test account limits | Medium | Use mock adapters for most tests |
| Performance tests fail (<3s target) | High | Profile and optimize hot paths |
| E2E tests flaky | Medium | Add retries, improve test isolation |
| Concurrency issues | High | Stress test with 50+ concurrent sessions |
