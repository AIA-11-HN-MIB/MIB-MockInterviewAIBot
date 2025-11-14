# Phase 5: Testing & Validation

**Duration**: 4-5 hours | **Dependencies**: Phase 1-4 | **Risk**: Low

## Objective
Comprehensive unit + integration tests for voice interview flow.

## Test Files

### Unit Tests
1. `tests/unit/adapters/test_azure_stt_adapter.py` - Mock Azure SDK, test transcribe_audio
2. `tests/unit/adapters/test_azure_tts_adapter.py` - Mock Azure SDK, test synthesize_speech
3. `tests/unit/adapters/test_mock_stt_adapter.py` - Test voice metrics generation
4. `tests/unit/adapters/test_mock_tts_adapter.py` - Test WAV generation
5. `tests/unit/infrastructure/test_container_speech.py` - Test DI mock/real toggle

### Integration Tests
6. `tests/integration/test_voice_interview_flow.py` - End-to-end voice interview with mocks
7. `tests/integration/test_audio_chunking.py` - WebSocket chunk assembly

## Key Test Cases

### STT Adapter Tests
```python
async def test_azure_stt_transcribe_returns_dict():
    adapter = AzureSpeechToTextAdapter(api_key="test", region="eastus")
    result = await adapter.transcribe_audio(audio_bytes, language="en-US")

    assert "text" in result
    assert "voice_metrics" in result
    assert "metadata" in result
    assert result["voice_metrics"]["intonation_score"] >= 0

async def test_mock_stt_deterministic_metrics():
    adapter = MockSTTAdapter(seed=42)
    result1 = await adapter.transcribe_audio(audio_bytes, language="en-US")
    result2 = await adapter.transcribe_audio(audio_bytes, language="en-US")

    assert result1["voice_metrics"] == result2["voice_metrics"]
```

### TTS Adapter Tests
```python
async def test_azure_tts_speed_param():
    adapter = AzureTTSAdapter(subscription_key="test", region="eastus")

    # Test speed variation
    audio_normal = await adapter.synthesize_speech("Hello", voice="en-US-AriaNeural", speed=1.0)
    audio_fast = await adapter.synthesize_speech("Hello", voice="en-US-AriaNeural", speed=2.0)

    assert len(audio_fast) < len(audio_normal)  # Faster = shorter

async def test_mock_tts_returns_valid_wav():
    adapter = MockTTSAdapter()
    audio_bytes = await adapter.synthesize_speech("Test", voice="en-US-AriaNeural", speed=1.0)

    # Verify WAV header
    assert audio_bytes[:4] == b"RIFF"
    assert audio_bytes[8:12] == b"WAVE"
```

### DI Container Tests
```python
def test_container_stt_mock_toggle():
    settings = Settings(use_mock_stt=True)
    container = Container(settings)

    stt = container.speech_to_text_port()
    assert isinstance(stt, MockSTTAdapter)

def test_container_stt_missing_key_error():
    settings = Settings(use_mock_stt=False, azure_speech_key=None)
    container = Container(settings)

    with pytest.raises(ValueError, match="AZURE_SPEECH_KEY not configured"):
        container.speech_to_text_port()
```

### End-to-End Test
```python
async def test_voice_interview_complete_flow():
    """Test voice interview from plan to completion."""
    # Plan interview
    interview = await plan_interview_use_case.execute(cv_analysis_id=cv_id)

    # Connect WebSocket
    async with websocket_client(f"/ws/interviews/{interview.id}") as ws:
        # Receive question
        question_msg = await ws.receive_json()
        assert question_msg["type"] == "question"

        # Send voice answer (3 chunks)
        audio_chunks = create_test_audio_chunks(text="My answer")
        for i, chunk in enumerate(audio_chunks):
            await ws.send_json({
                "type": "audio_chunk",
                "audio_data": base64.b64encode(chunk).decode(),
                "chunk_index": i,
                "is_final": i == len(audio_chunks) - 1,
                "question_id": question_msg["question_id"],
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

## Success Criteria
- ✅ All unit tests pass (85%+ coverage)
- ✅ Integration test passes with mock adapters
- ✅ No regression in text-based interview tests
- ✅ Mypy + ruff + black pass

## Manual Testing Checklist
- [ ] Real Azure STT: Record audio, verify transcription accuracy
- [ ] Real Azure TTS: Generate question audio, verify quality
- [ ] WebSocket: Send audio chunks, verify assembly
- [ ] Error handling: Test with invalid audio format
- [ ] Fallback: Verify text mode still works
