# Phase 3: WebSocket Audio Integration (Real-time Streaming STT)

**Duration**: 5-6 hours | **Dependencies**: Phase 1-2 | **Risk**: Medium-High

## Objective
Implement **real-time streaming STT** with WebSocket audio chunks: receive audio, send interim transcriptions, final transcription with voice metrics.

## Key Implementation

### Real-time Streaming Audio Handler
```python
# interview_handler.py - Streaming STT implementation
from asyncio import Queue

# Per-session state
audio_streams: dict[UUID, Queue[bytes]] = {}
transcription_tasks: dict[UUID, asyncio.Task] = {}

async def handle_audio_chunk(interview_id: UUID, data: dict, container: Container):
    """Process audio chunk with real-time streaming STT."""
    audio_data_b64 = data["audio_data"]
    chunk_index = data["chunk_index"]
    is_final = data["is_final"]
    question_id = UUID(data["question_id"])

    # Decode chunk
    audio_chunk = base64.b64decode(audio_data_b64)

    # Initialize streaming on first chunk
    if interview_id not in audio_streams:
        audio_streams[interview_id] = Queue()
        # Start background transcription task
        task = asyncio.create_task(
            stream_transcription(interview_id, question_id, container)
        )
        transcription_tasks[interview_id] = task

    # Feed chunk to stream
    await audio_streams[interview_id].put(audio_chunk)

    if is_final:
        # Signal end of stream
        await audio_streams[interview_id].put(None)  # sentinel
        # Wait for transcription to complete
        await transcription_tasks[interview_id]
        # Cleanup
        audio_streams.pop(interview_id, None)
        transcription_tasks.pop(interview_id, None)


async def stream_transcription(
    interview_id: UUID,
    question_id: UUID,
    container: Container
):
    """Background task: consume audio stream, send interim transcriptions."""
    stt = container.speech_to_text_port()
    audio_queue = audio_streams[interview_id]

    # Collect chunks
    chunks = []
    while True:
        chunk = await audio_queue.get()
        if chunk is None:  # End signal
            break
        chunks.append(chunk)

    # Assemble complete audio
    complete_audio = b"".join(chunks)

    # Use streaming STT (Azure SDK continuous recognition)
    result = await stt.transcribe_stream(complete_audio, language="en-US")

    # Send final transcription
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

    # Pass to orchestrator (Phase 4)
    orchestrator = session_orchestrators.get(interview_id)
    if orchestrator:
        await orchestrator.handle_voice_answer(
            audio_bytes=complete_audio,
            question_id=question_id,
            transcription=result["text"],
            voice_metrics=result["voice_metrics"],
        )
```

### Integration with WebSocket Handler
```python
# interview_handler.py (line 59)
elif message_type == "audio_chunk":
    await handle_audio_chunk(interview_id, data, container)
```

## Files Modified
- `src/adapters/api/websocket/interview_handler.py` (implement `handle_audio_chunk`)

## Success Criteria
- ✅ Audio chunks assembled correctly (validate WAV header)
- ✅ STT returns transcription + voice metrics
- ✅ Client receives TranscriptionMessage and VoiceMetricsMessage
- ✅ Buffer cleaned after assembly (no memory leaks)

## Risks
- **Format Conversion**: Client sends WebM, Azure expects WAV → Accept both, Azure SDK handles
- **Memory Leaks**: Large buffers not cleaned → Clear on disconnect + timeout
- **Network Errors**: Partial chunks lost → Send error message, request retry

## Next: Phase 4 (Session Orchestrator Voice Support)
