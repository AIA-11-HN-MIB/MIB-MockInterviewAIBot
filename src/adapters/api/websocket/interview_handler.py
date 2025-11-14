"""WebSocket handler for interview sessions (orchestrator-based)."""

import logging
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from ....infrastructure.dependency_injection.container import get_container
from .connection_manager import manager
from .session_orchestrator import InterviewSessionOrchestrator

logger = logging.getLogger(__name__)


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
                logger.warning(
                    "get_next_question deprecated - use orchestrator state machine"
                )
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
        logger.info(f"Client disconnected from interview {interview_id}")

    except ValueError as e:
        # State machine validation error
        logger.error(f"State machine error for interview {interview_id}: {e}")
        await manager.send_message(
            interview_id,
            {"type": "error", "code": "INVALID_STATE", "message": str(e)},
        )
        manager.disconnect(interview_id)

    except Exception as e:
        logger.error(
            f"WebSocket error for interview {interview_id}: {e}", exc_info=True
        )
        await manager.send_message(
            interview_id,
            {"type": "error", "code": "INTERNAL_ERROR", "message": str(e)},
        )
        manager.disconnect(interview_id)


# Deprecated functions - now handled by InterviewSessionOrchestrator
# Kept for reference during migration period


async def handle_audio_chunk(interview_id: UUID, data: dict, container):
    """Handle audio chunk from client (for voice answers).

    TODO: Integrate with InterviewSessionOrchestrator in Phase 6 (Voice Integration)

    Args:
        interview_id: Interview UUID
        data: Message data with audio chunk
        container: DI container
    """
    # Mock implementation for now
    await manager.send_message(
        interview_id,
        {
            "type": "transcription",
            "text": "[Mock transcription of audio - Phase 6]",
            "is_final": data.get("is_final", False),
        },
    )
