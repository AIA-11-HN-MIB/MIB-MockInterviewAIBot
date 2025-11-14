# Phase 4: Session Orchestrator Voice Support

**Duration**: 3-4 hours | **Dependencies**: Phase 1-3 | **Risk**: Medium

## Objective
Add voice answer handling to session orchestrator. Support both text and voice answers in same evaluation flow.

## Key Implementation

### Add `handle_voice_answer()` Method
```python
# session_orchestrator.py
async def handle_voice_answer(
    self,
    audio_bytes: bytes,
    question_id: UUID,
    transcription: str,
    voice_metrics: dict[str, float],
) -> None:
    """Process voice answer with STT transcription."""
    # Validate state
    if self.state != SessionState.QUESTIONING:
        raise ValueError(f"Cannot answer in state {self.state}")

    # Transition
    self._transition(SessionState.EVALUATING)

    # Process answer (pass voice metrics to use case)
    answer = await self.process_answer_use_case.execute(
        interview_id=self.interview_id,
        question_id=question_id,
        answer_text=transcription,
        answer_mode="VOICE",  # NEW
        voice_metrics=voice_metrics,  # NEW
    )

    # Send evaluation (includes voice_metrics in response)
    await self._send_evaluation(answer)

    # Follow-up decision (same as text flow)
    decision = await self.follow_up_decision_use_case.execute(...)
    if decision["needs_followup"]:
        await self._generate_and_send_followup(...)
    else:
        await self._send_next_main_question_or_complete()
```

### TTS Integration (Optional)
```python
async def _send_next_main_question(self) -> None:
    """Send next question with optional TTS audio."""
    question = await self._get_next_question()

    # Generate TTS audio (feature flag)
    audio_data_b64 = None
    if self.container.settings.enable_tts:
        tts = self.container.text_to_speech_port()
        audio_bytes = await tts.synthesize_speech(
            text=question.text,
            voice=self.container.settings.azure_speech_voice,
            speed=1.0,
        )
        audio_data_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Send QuestionMessage
    await manager.send_message(self.interview_id, {
        "type": "question",
        "question_id": str(question.id),
        "text": question.text,
        "audio_data": audio_data_b64,  # Optional TTS
        "audio_format": "wav",
        # ... other fields
    })
```

### Update ProcessAnswerAdaptiveUseCase
```python
# process_answer_adaptive.py
async def execute(
    interview_id: UUID,
    question_id: UUID,
    answer_text: str,
    answer_mode: str = "TEXT",  # NEW: TEXT or VOICE
    voice_metrics: dict | None = None,  # NEW
) -> Answer:
    # ... existing evaluation logic

    # Create Answer entity with voice metrics
    answer = Answer(
        interview_id=interview_id,
        question_id=question_id,
        answer_text=answer_text,
        answer_mode=answer_mode,
        voice_metrics=voice_metrics,  # Store in Answer
        evaluation=evaluation,
    )

    # Save
    await self.answer_repo.save(answer)
    return answer
```

## Files Modified
- `src/adapters/api/websocket/session_orchestrator.py` (add `handle_voice_answer`)
- `src/application/use_cases/process_answer_adaptive.py` (accept voice_metrics)
- `src/domain/models/answer.py` (add voice_metrics field - if not exists)

## Success Criteria
- ✅ Voice answers processed with same evaluation flow as text
- ✅ Voice metrics stored in Answer entity
- ✅ EvaluationMessage includes voice_metrics
- ✅ TTS audio included in QuestionMessage (if enabled)
- ✅ State machine works for voice flow

## Next: Phase 5 (Testing)
