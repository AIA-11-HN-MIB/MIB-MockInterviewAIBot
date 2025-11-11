# Phase 2: WebSocket Message Protocol

**Duration**: 2 days
**Priority**: High
**Dependencies**: Phase 1 (Speech Integration)

## Context

Current WebSocket protocol supports text messages only. Need to add binary frames for audio chunks, voice metrics messages, and error handling for audio failures.

**Context Links**:
- `src/adapters/api/websocket/interview_handler.py` - Current handler (435 lines)
- `src/adapters/api/websocket/connection_manager.py` - Connection pool
- `src/application/dto/websocket_dto.py` - Current message DTOs

## Requirements

### Message Types

**Client → Server**:
- `audio_chunk` - Audio data chunk (binary or base64)
- `text_answer` - Text-only answer (existing)
- `get_next_question` - Request next question (existing)
- `request_retry` - Retry failed operation

**Server → Client**:
- `question` - Question with TTS audio (enhanced)
- `follow_up_question` - Follow-up question with audio (new)
- `evaluation` - Answer evaluation with voice metrics (enhanced)
- `voice_metrics` - Real-time voice analysis (new)
- `transcription` - STT intermediate results (new)
- `interview_complete` - Final summary (existing)
- `error` - Error with recovery options (enhanced)

## Architecture

### Enhanced Message Protocol

```python
# src/application/dto/websocket_dto.py

# CLIENT → SERVER
class AudioChunkMessage(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    audio_data: str  # Base64-encoded audio bytes
    chunk_index: int
    is_final: bool
    format: str = "webm"  # webm, wav, mp3
    question_id: UUID  # Which question this answers

class TextAnswerMessage(BaseModel):
    type: Literal["text_answer"] = "text_answer"
    question_id: UUID
    answer_text: str

# SERVER → CLIENT
class QuestionMessage(BaseModel):
    type: Literal["question"] = "question"
    question_id: UUID
    text: str
    question_type: str
    difficulty: str
    index: int
    total: int
    audio_data: str  # Base64-encoded TTS audio
    audio_format: str = "wav"

class FollowUpQuestionMessage(BaseModel):
    type: Literal["follow_up_question"] = "follow_up_question"
    question_id: UUID
    parent_question_id: UUID
    text: str
    generated_reason: str
    order_in_sequence: int
    audio_data: str
    audio_format: str = "wav"

class EvaluationMessage(BaseModel):
    type: Literal["evaluation"] = "evaluation"
    answer_id: UUID
    score: float
    feedback: str
    strengths: list[str]
    weaknesses: list[str]
    similarity_score: float | None
    gaps: dict[str, Any] | None
    voice_metrics: dict[str, float] | None  # NEW

class VoiceMetricsMessage(BaseModel):
    type: Literal["voice_metrics"] = "voice_metrics"
    intonation_score: float
    fluency_score: float
    confidence_score: float
    speaking_rate_wpm: int
    real_time: bool = True  # Real-time or final

class TranscriptionMessage(BaseModel):
    type: Literal["transcription"] = "transcription"
    text: str
    is_final: bool
    confidence: float

class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: str  # ERROR_CODE enum
    message: str
    recoverable: bool
    retry_available: bool
    fallback_option: str | None  # e.g., "text_mode"
```

### Binary Frame Handling

```python
# Enhanced interview_handler.py
async def handle_interview_websocket(
    websocket: WebSocket,
    interview_id: UUID,
):
    await manager.connect(interview_id, websocket)

    try:
        while True:
            # Support both text and binary frames
            message = await websocket.receive()

            if "text" in message:
                # JSON message
                data = json.loads(message["text"])
                await route_text_message(interview_id, data, container)

            elif "bytes" in message:
                # Binary audio chunk
                await handle_binary_audio(
                    interview_id,
                    message["bytes"],
                    container
                )

    except WebSocketDisconnect:
        manager.disconnect(interview_id)
```

### Error Codes Enum

```python
# src/domain/models/error_codes.py
from enum import Enum

class WebSocketErrorCode(str, Enum):
    # Interview errors
    INTERVIEW_NOT_FOUND = "INTERVIEW_NOT_FOUND"
    INVALID_STATE = "INVALID_STATE"
    NO_MORE_QUESTIONS = "NO_MORE_QUESTIONS"

    # Audio errors (NEW)
    AUDIO_FORMAT_UNSUPPORTED = "AUDIO_FORMAT_UNSUPPORTED"
    AUDIO_TOO_SHORT = "AUDIO_TOO_SHORT"
    AUDIO_TOO_LONG = "AUDIO_TOO_LONG"
    STT_FAILED = "STT_FAILED"
    TTS_FAILED = "TTS_FAILED"
    VOICE_METRICS_UNAVAILABLE = "VOICE_METRICS_UNAVAILABLE"

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
```

## Implementation Steps

### Day 1: Message DTOs & Validation

**Step 1**: Create enhanced message DTOs
- Add AudioChunkMessage, VoiceMetricsMessage, TranscriptionMessage
- Enhance EvaluationMessage with voice_metrics
- Enhance ErrorMessage with recovery options

**Step 2**: Create error codes enum
- Define all error codes
- Add recovery metadata

**Step 3**: Add message validation
- Pydantic validation for all message types
- Custom validators for audio format/size

### Day 2: Binary Frame & Error Handling

**Step 1**: Implement binary frame handling
- Update handle_interview_websocket() to support bytes
- Create handle_binary_audio() handler
- Add base64 decoding/encoding utilities

**Step 2**: Enhance error handling
- Wrap all operations in try-except
- Send structured error messages
- Add retry logic for recoverable errors

**Step 3**: Update connection manager
- Add binary message sending support
- Add broadcast support for multi-client

## Todo List

**Day 1**:
- [ ] Create enhanced DTOs in websocket_dto.py
- [ ] Create error_codes.py with WebSocketErrorCode enum
- [ ] Add Pydantic validators for audio messages
- [ ] Write unit tests for message validation

**Day 2**:
- [ ] Update handle_interview_websocket() for binary frames
- [ ] Implement handle_binary_audio() handler
- [ ] Enhance error handling with structured errors
- [ ] Update connection_manager for binary support
- [ ] Write integration tests for message flow

## Success Criteria

- ✅ All message types defined with Pydantic models
- ✅ Binary frame handling works (audio upload)
- ✅ Error messages include recovery options
- ✅ Validation catches malformed messages
- ✅ Unit test coverage >=80%
