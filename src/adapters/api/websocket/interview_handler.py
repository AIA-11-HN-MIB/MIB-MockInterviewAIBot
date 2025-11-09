"""WebSocket handler for interview sessions."""

import base64
import logging
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from ....application.use_cases.complete_interview import CompleteInterviewUseCase
from ....application.use_cases.get_next_question import GetNextQuestionUseCase
from ....application.use_cases.process_answer_adaptive import (
    ProcessAnswerAdaptiveUseCase,
)
from ....infrastructure.database.session import get_async_session
from ....infrastructure.dependency_injection.container import get_container
from .connection_manager import manager

logger = logging.getLogger(__name__)


async def handle_interview_websocket(
    websocket: WebSocket,
    interview_id: UUID,
):
    """WebSocket handler for interview session.

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

        # Send first question
        async for session in get_async_session():
            interview_repo = container.interview_repository_port(session)
            question_repo = container.question_repository_port(session)

            use_case = GetNextQuestionUseCase(
                interview_repository=interview_repo,
                question_repository=question_repo,
            )

            question = await use_case.execute(interview_id)
            if question:
                # Get interview for context
                interview = await interview_repo.get_by_id(interview_id)

                if not interview:
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "error",
                            "code": "INTERVIEW_NOT_FOUND",
                            "message": f"Interview {interview_id} not found",
                        },
                    )
                    break

                # Get TTS audio
                tts = container.text_to_speech_port()
                audio_bytes = await tts.synthesize_speech(question.text)
                audio_data = base64.b64encode(audio_bytes).decode("utf-8")

                await manager.send_message(
                    interview_id,
                    {
                        "type": "question",
                        "question_id": str(question.id),
                        "text": question.text,
                        "question_type": question.question_type,
                        "difficulty": question.difficulty,
                        "index": interview.current_question_index,
                        "total": len(interview.question_ids),
                        "audio_data": audio_data,
                    },
                )
            break

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "text_answer":
                await handle_text_answer(interview_id, data, container)

            elif message_type == "audio_chunk":
                await handle_audio_chunk(interview_id, data, container)

            elif message_type == "get_next_question":
                await handle_get_next_question(interview_id, container)

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

    except Exception as e:
        logger.error(
            f"WebSocket error for interview {interview_id}: {e}", exc_info=True
        )
        await manager.send_message(
            interview_id,
            {"type": "error", "code": "INTERNAL_ERROR", "message": str(e)},
        )
        manager.disconnect(interview_id)


async def handle_text_answer(interview_id: UUID, data: dict, container):
    """Handle text answer from client with adaptive evaluation.

    Args:
        interview_id: Interview UUID
        data: Message data with question_id and answer_text
        container: DI container
    """
    async for session in get_async_session():
        # Fetch repositories once
        interview_repo = container.interview_repository_port(session)
        question_repo = container.question_repository_port(session)
        answer_repo = container.answer_repository_port(session)

        interview = await interview_repo.get_by_id(interview_id)

        if not interview:
            await manager.send_message(
                interview_id,
                {
                    "type": "error",
                    "code": "INTERVIEW_NOT_FOUND",
                    "message": f"Interview {interview_id} not found",
                },
            )
            break

        # Process answer with adaptive evaluation
        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=answer_repo,
            interview_repository=interview_repo,
            question_repository=question_repo,
            llm=container.llm_port(),
            vector_search=container.vector_search_port(),
        )

        answer, follow_up_question, has_more = await use_case.execute(
            interview_id=interview_id,
            question_id=UUID(data["question_id"]),
            answer_text=data["answer_text"],
        )

        # Send evaluation with adaptive metrics
        if answer.evaluation:
            eval_message = {
                "type": "evaluation",
                "answer_id": str(answer.id),
                "score": answer.evaluation.score,
                "feedback": answer.evaluation.reasoning,
                "strengths": answer.evaluation.strengths,
                "weaknesses": answer.evaluation.weaknesses,
            }
        else:
            eval_message = {
                "type": "evaluation",
                "answer_id": str(answer.id),
                "score": 0.0,
                "feedback": "No evaluation available",
                "strengths": [],
                "weaknesses": [],
            }

        # Add adaptive metrics if available
        if answer.similarity_score is not None:
            eval_message["similarity_score"] = answer.similarity_score
        if answer.gaps:
            eval_message["gaps"] = answer.gaps

        await manager.send_message(interview_id, eval_message)

        # Get TTS once (will be used for either follow-up or next question)
        tts = container.text_to_speech_port()

        # If follow-up generated, send it immediately
        if follow_up_question:
            audio_bytes = await tts.synthesize_speech(follow_up_question.text)
            audio_data = base64.b64encode(audio_bytes).decode("utf-8")

            await manager.send_message(
                interview_id,
                {
                    "type": "follow_up_question",
                    "question_id": str(follow_up_question.id),
                    "parent_question_id": str(follow_up_question.parent_question_id),
                    "text": follow_up_question.text,
                    "generated_reason": follow_up_question.generated_reason,
                    "order_in_sequence": follow_up_question.order_in_sequence,
                    "audio_data": audio_data,
                },
            )
            # Don't proceed to next main question yet
            break

        # Send next question or complete
        if has_more:
            question_use_case = GetNextQuestionUseCase(
                interview_repository=interview_repo,
                question_repository=question_repo,
            )
            question = await question_use_case.execute(interview_id)

            if question:
                audio_bytes = await tts.synthesize_speech(question.text)
                audio_data = base64.b64encode(audio_bytes).decode("utf-8")

                await manager.send_message(
                    interview_id,
                    {
                        "type": "question",
                        "question_id": str(question.id),
                        "text": question.text,
                        "question_type": question.question_type,
                        "difficulty": question.difficulty,
                        "index": interview.current_question_index,
                        "total": len(interview.question_ids),
                        "audio_data": audio_data,
                    },
                )
        else:
            # Complete interview
            complete_use_case = CompleteInterviewUseCase(
                interview_repository=interview_repo,
            )
            interview = await complete_use_case.execute(interview_id)

            # Calculate overall score (average of all answer scores)
            answers = await answer_repo.get_by_interview_id(interview_id)
            overall_score = (
                sum(a.evaluation.score for a in answers if a.evaluation)
                / len(answers)
                if answers
                else 0.0
            )

            await manager.send_message(
                interview_id,
                {
                    "type": "interview_complete",
                    "interview_id": str(interview.id),
                    "overall_score": overall_score,
                    "total_questions": len(interview.question_ids),
                    "feedback_url": f"/api/interviews/{interview_id}/feedback",
                },
            )
        break


async def handle_audio_chunk(interview_id: UUID, data: dict, container):
    """Handle audio chunk from client (for voice answers).

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
            "text": "[Mock transcription of audio]",
            "is_final": data.get("is_final", False),
        },
    )


async def handle_get_next_question(interview_id: UUID, container):
    """Handle request for next question.

    Args:
        interview_id: Interview UUID
        container: DI container
    """
    async for session in get_async_session():
        interview_repo = container.interview_repository_port(session)
        question_repo = container.question_repository_port(session)

        use_case = GetNextQuestionUseCase(
            interview_repository=interview_repo,
            question_repository=question_repo,
        )

        question = await use_case.execute(interview_id)
        if not question:
            await manager.send_message(
                interview_id,
                {
                    "type": "error",
                    "code": "NO_MORE_QUESTIONS",
                    "message": "No more questions available",
                },
            )
            break

        interview = await interview_repo.get_by_id(interview_id)

        if not interview:
            await manager.send_message(
                interview_id,
                {
                    "type": "error",
                    "code": "INTERVIEW_NOT_FOUND",
                    "message": f"Interview {interview_id} not found",
                },
            )
            break

        # Get TTS
        tts = container.text_to_speech_port()
        audio_bytes = await tts.synthesize_speech(question.text)
        audio_data = base64.b64encode(audio_bytes).decode("utf-8")

        await manager.send_message(
            interview_id,
            {
                "type": "question",
                "question_id": str(question.id),
                "text": question.text,
                "question_type": question.question_type.value,
                "difficulty": question.difficulty.value,
                "index": interview.current_question_index,
                "total": len(interview.question_ids),
                "audio_data": audio_data,
            },
        )
        break