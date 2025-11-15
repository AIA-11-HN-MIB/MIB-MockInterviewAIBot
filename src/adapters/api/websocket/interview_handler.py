"""WebSocket handler for interview sessions (orchestrator-based)."""

import asyncio
import base64
import logging
from asyncio import Queue
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from ....infrastructure.dependency_injection.container import Container, get_container
from .connection_manager import manager
from .session_orchestrator import InterviewSessionOrchestrator

logger = logging.getLogger(__name__)

# Per-session state for streaming audio
audio_streams: dict[UUID, Queue[bytes]] = {}
transcription_tasks: dict[UUID, asyncio.Task] = {}
session_orchestrators: dict[UUID, InterviewSessionOrchestrator] = {}


async def handle_interview_websocket(
    websocket: WebSocket,
    interview_id: UUID,
):
    """WebSocket handler for interview session (orchestrator-based).

    Uses InterviewSessionOrchestrator to manage state machine lifecycle.

    Protocol:
        Client → Server: { type: "text_answer", question_id: UUID, answer_text: str }
        Server → Client: { type: "evaluation", ... }
        Server → Client: { type: "question", ... }
        Server → Client: { type: "interview_complete", ... }

    Args:
        websocket: WebSocket connection
        interview_id: Interview UUID
    """
    # Connect
    await manager.connect(interview_id, websocket)

    try:
        container = get_container()

        # Create session orchestrator
        orchestrator = InterviewSessionOrchestrator(
            interview_id=interview_id,
            websocket=websocket,
            container=container,
        )

        # Store orchestrator for audio chunk handler access
        session_orchestrators[interview_id] = orchestrator

        # Start session (send first question)
        await orchestrator.start_session()

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "text_answer":
                answer_text = data.get("answer_text", "")
                await orchestrator.handle_answer(answer_text)

            elif message_type == "audio_chunk":
                await handle_audio_chunk(interview_id, data, container)

            elif message_type == "get_next_question":
                logger.warning("get_next_question deprecated - use orchestrator state machine")
                await manager.send_message(
                    interview_id,
                    {
                        "type": "error",
                        "code": "DEPRECATED_MESSAGE_TYPE",
                        "message": "get_next_question deprecated - orchestrator manages flow",
                    },
                )

            else:
                await manager.send_message(
                    interview_id,
                    {
                        "type": "error",
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {message_type}",
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(interview_id)
        # Cleanup audio streaming resources
        _cleanup_audio_resources(interview_id)
        logger.info(f"Client disconnected from interview {interview_id}")

    except ValueError as e:
        # State machine validation error
        logger.error(f"State machine error for interview {interview_id}: {e}")
        await manager.send_message(
            interview_id,
            {"type": "error", "code": "INVALID_STATE", "message": str(e)},
        )
        _cleanup_audio_resources(interview_id)
        manager.disconnect(interview_id)

    except Exception as e:
        logger.error(f"WebSocket error for interview {interview_id}: {e}", exc_info=True)
        await manager.send_message(
            interview_id,
            {"type": "error", "code": "INTERNAL_ERROR", "message": str(e)},
        )
        _cleanup_audio_resources(interview_id)
        manager.disconnect(interview_id)


def _cleanup_audio_resources(interview_id: UUID):
    """Clean up audio streaming resources for a session.

    Args:
        interview_id: Interview UUID
    """
    # Cancel any pending transcription tasks
    if interview_id in transcription_tasks:
        task = transcription_tasks.pop(interview_id)
        if not task.done():
            task.cancel()

    # Clear audio streams
    audio_streams.pop(interview_id, None)

    # Remove orchestrator reference
    session_orchestrators.pop(interview_id, None)

    logger.debug(f"Cleaned up audio resources for interview {interview_id}")


async def _stream_transcription(
    interview_id: UUID,
    question_id: UUID,
    container: Container,
):
    """Background task: consume audio stream and send transcriptions.

    Args:
        interview_id: Interview UUID
        question_id: Question UUID
        container: DI container
    """
    try:
        stt = container.speech_to_text_port()
        audio_queue = audio_streams[interview_id]

        # Collect chunks from queue
        chunks = []
        while True:
            chunk = await audio_queue.get()
            if chunk is None:  # End signal (sentinel value)
                break
            chunks.append(chunk)

        # Assemble complete audio
        complete_audio = b"".join(chunks)
        logger.info(
            f"Assembled {len(chunks)} chunks ({len(complete_audio)} bytes) "
            f"for interview {interview_id}"
        )

        # Transcribe using STT service (supports streaming via transcribe_stream)
        result = await stt.transcribe_stream(complete_audio, language="en-US")

        # Send final transcription to client
        await manager.send_message(
            interview_id,
            {
                "type": "transcription",
                "text": result["text"],
                "is_final": True,
                "confidence": result.get("voice_metrics", {}).get("confidence_score", 0.0),
            },
        )

        # Send voice metrics to client
        voice_metrics = result.get("voice_metrics", {})
        await manager.send_message(
            interview_id,
            {
                "type": "voice_metrics",
                **voice_metrics,
                "real_time": False,
            },
        )

        logger.info(f"Sent transcription and voice metrics for interview {interview_id}")

        # Pass to orchestrator for answer processing
        orchestrator = session_orchestrators.get(interview_id)
        if orchestrator:
            logger.info(
                f"Processing voice answer via orchestrator: '{result['text']}' "
                f"(interview {interview_id}, question {question_id})"
            )
            await orchestrator.handle_voice_answer(
                audio_bytes=complete_audio,
                question_id=question_id,
                transcription=result["text"],
                voice_metrics=result.get("voice_metrics", {}),
            )
        else:
            logger.warning(
                f"No orchestrator found for interview {interview_id} - "
                f"cannot process voice answer"
            )

    except Exception as e:
        logger.error(
            f"Error in transcription stream for interview {interview_id}: {e}",
            exc_info=True,
        )
        await manager.send_message(
            interview_id,
            {
                "type": "error",
                "code": "TRANSCRIPTION_ERROR",
                "message": f"Failed to transcribe audio: {str(e)}",
            },
        )


# Deprecated functions - now handled by InterviewSessionOrchestrator
# Kept for reference during migration period


async def handle_audio_chunk(interview_id: UUID, data: dict, container: Container):
    """Handle audio chunk from client with real-time streaming STT.

    Implements real-time audio streaming:
    1. First chunk: Initialize audio queue and background transcription task
    2. Intermediate chunks: Add to queue for streaming processing
    3. Final chunk: Signal end of stream, wait for transcription completion

    Args:
        interview_id: Interview UUID
        data: Message data with audio chunk (audio_data, chunk_index, is_final, question_id)
        container: DI container
    """
    try:
        # Extract message fields
        audio_data_b64 = data.get("audio_data")
        chunk_index = data.get("chunk_index", 0)
        is_final = data.get("is_final", False)
        question_id_str = data.get("question_id")

        if not audio_data_b64:
            logger.error(f"Audio chunk missing audio_data for interview {interview_id}")
            await manager.send_message(
                interview_id,
                {
                    "type": "error",
                    "code": "INVALID_AUDIO_CHUNK",
                    "message": "Missing audio_data field",
                },
            )
            return

        if not question_id_str:
            logger.error(f"Audio chunk missing question_id for interview {interview_id}")
            await manager.send_message(
                interview_id,
                {
                    "type": "error",
                    "code": "INVALID_AUDIO_CHUNK",
                    "message": "Missing question_id field",
                },
            )
            return

        question_id = UUID(question_id_str)

        # Decode audio chunk from base64
        try:
            audio_chunk = base64.b64decode(audio_data_b64)
        except Exception as e:
            logger.error(f"Failed to decode audio chunk: {e}")
            await manager.send_message(
                interview_id,
                {
                    "type": "error",
                    "code": "INVALID_AUDIO_DATA",
                    "message": "Failed to decode base64 audio data",
                },
            )
            return

        # Initialize streaming on first chunk
        if interview_id not in audio_streams:
            logger.info(
                f"Initializing audio stream for interview {interview_id}, "
                f"question {question_id}"
            )
            audio_streams[interview_id] = Queue()

            # Start background transcription task
            task = asyncio.create_task(_stream_transcription(interview_id, question_id, container))
            transcription_tasks[interview_id] = task

        # Feed chunk to stream
        await audio_streams[interview_id].put(audio_chunk)
        logger.debug(f"Added audio chunk {chunk_index} to stream for interview {interview_id}")

        if is_final:
            logger.info(
                f"Received final audio chunk for interview {interview_id}, "
                f"signaling end of stream"
            )
            # Signal end of stream
            await audio_streams[interview_id].put(None)  # sentinel value

            # Wait for transcription to complete
            await transcription_tasks[interview_id]

            # Cleanup
            audio_streams.pop(interview_id, None)
            transcription_tasks.pop(interview_id, None)
            logger.info(f"Audio stream completed for interview {interview_id}")

    except Exception as e:
        logger.error(
            f"Error handling audio chunk for interview {interview_id}: {e}",
            exc_info=True,
        )
        await manager.send_message(
            interview_id,
            {
                "type": "error",
                "code": "AUDIO_PROCESSING_ERROR",
                "message": f"Failed to process audio chunk: {str(e)}",
            },
        )
