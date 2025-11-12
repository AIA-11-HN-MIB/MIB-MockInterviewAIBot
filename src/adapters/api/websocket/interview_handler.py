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
            tts = container.text_to_speech_port()

            await _send_initial_question(
                interview_id, interview_repo, question_repo, tts
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


async def _validate_interview_exists(interview_id: UUID, interview_repo):
    """Validate that interview exists and send error if not.

    Args:
        interview_id: Interview UUID
        interview_repo: Interview repository

    Returns:
        Interview entity if exists, None otherwise
    """
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
        return None

    return interview


async def _send_initial_question(
    interview_id: UUID, interview_repo, question_repo, tts
):
    """Get and send the first question to start the interview.

    Args:
        interview_id: Interview UUID
        interview_repo: Interview repository
        question_repo: Question repository
        tts: Text-to-speech port

    Returns:
        True if question was sent, False otherwise
    """
    use_case = GetNextQuestionUseCase(
        interview_repository=interview_repo,
        question_repository=question_repo,
    )

    question = await use_case.execute(interview_id)
    if not question:
        return False

    # Get interview for context
    interview = await _validate_interview_exists(interview_id, interview_repo)
    if not interview:
        return False

    # Generate TTS audio
    audio_bytes = await tts.synthesize_speech(question.text)
    audio_data = base64.b64encode(audio_bytes).decode("utf-8")

    # Send question message
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
    return True


async def _process_answer(
    interview_id: UUID,
    question_id: UUID,
    answer_text: str,
    answer_repo,
    interview_repo,
    question_repo,
    container,
):
    """Process answer with adaptive evaluation.

    Args:
        interview_id: Interview UUID
        question_id: Question UUID
        answer_text: Candidate's answer text
        answer_repo: Answer repository
        interview_repo: Interview repository
        question_repo: Question repository
        container: DI container

    Returns:
        Tuple of (answer, has_more)
    """
    use_case = ProcessAnswerAdaptiveUseCase(
        answer_repository=answer_repo,
        interview_repository=interview_repo,
        question_repository=question_repo,
        follow_up_question_repository=container.follow_up_question_repository(),
        llm=container.llm_port(),
        vector_search=container.vector_search_port(),
    )

    return await use_case.execute(
        interview_id=interview_id,
        question_id=question_id,
        answer_text=answer_text,
    )


async def _send_evaluation(interview_id: UUID, answer):
    """Send evaluation message with adaptive metrics.

    Args:
        interview_id: Interview UUID
        answer: Answer entity with evaluation
    """
    eval_message = {
        "type": "evaluation",
        "answer_id": str(answer.id),
        "score": answer.evaluation.score,
        "feedback": answer.evaluation.reasoning,
        "strengths": answer.evaluation.strengths,
        "weaknesses": answer.evaluation.weaknesses,
        "similarity_score": answer.similarity_score,
        "gaps": answer.gaps,
    }

    await manager.send_message(interview_id, eval_message)


async def _send_follow_up_question(interview_id: UUID, follow_up_question, tts):
    """Send follow-up question with audio.

    Args:
        interview_id: Interview UUID
        follow_up_question: Follow-up question entity
        tts: Text-to-speech port
    """
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


async def _send_next_question(
    interview_id: UUID, interview, interview_repo, question_repo, tts
):
    """Send next main question with audio.

    Args:
        interview_id: Interview UUID
        interview: Interview entity
        interview_repo: Interview repository
        question_repo: Question repository
        tts: Text-to-speech port
    """
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


async def _complete_interview(interview_id: UUID, interview_repo, answer_repo):
    """Complete interview and send final results.

    Args:
        interview_id: Interview UUID
        interview_repo: Interview repository
        answer_repo: Answer repository
    """
    complete_use_case = CompleteInterviewUseCase(
        interview_repository=interview_repo,
    )
    interview = await complete_use_case.execute(interview_id)

    # Calculate overall score (average of all answer scores)
    answers = await answer_repo.get_by_interview_id(interview_id)
    overall_score = (
        sum(a.evaluation.score for a in answers if a.evaluation) / len(answers)
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


async def handle_text_answer(interview_id: UUID, data: dict, container):
    """Handle text answer from client with iterative follow-up loop.

    Implements Phase 4 adaptive follow-up logic:
    - Evaluate answer
    - Check decision (FollowUpDecisionUseCase)
    - Generate 0-3 follow-ups based on gaps
    - Exit loop when similarity >=0.8 OR no gaps OR max 3 reached

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
        follow_up_repo = container.follow_up_question_repository()

        # Validate interview exists
        interview = await _validate_interview_exists(interview_id, interview_repo)
        if not interview:
            break

        # Get question to determine if it's main or follow-up
        question_id = UUID(data["question_id"])
        current_question = await question_repo.get_by_id(question_id)

        # Determine parent question ID (for tracking follow-up count)
        parent_question_id = question_id  # Default: current is parent

        # Check if current question is a follow-up
        follow_up_question = await follow_up_repo.get_by_id(question_id)
        if follow_up_question:
            parent_question_id = follow_up_question.parent_question_id

        # Process answer with adaptive evaluation
        answer, has_more = await _process_answer(
            interview_id=interview_id,
            question_id=question_id,
            answer_text=data["answer_text"],
            answer_repo=answer_repo,
            interview_repo=interview_repo,
            question_repo=question_repo,
            container=container,
        )

        # Send evaluation
        await _send_evaluation(interview_id, answer)

        # Get TTS once
        tts = container.text_to_speech_port()

        # ITERATIVE FOLLOW-UP LOOP (Phase 4)
        # Loop will not actually wait for answers within this function
        # Instead, it breaks after sending first follow-up and waits for next message
        # This is a limitation of current architecture - noted in plan
        from ...application.use_cases.follow_up_decision import FollowUpDecisionUseCase

        decision_use_case = FollowUpDecisionUseCase(
            answer_repository=answer_repo,
            follow_up_question_repository=follow_up_repo,
        )

        # Make decision: should we generate follow-up?
        decision = await decision_use_case.execute(
            interview_id=interview_id,
            parent_question_id=parent_question_id,
            latest_answer=answer,
        )

        logger.info(
            f"Follow-up decision: needs={decision['needs_followup']}, "
            f"reason='{decision['reason']}', count={decision['follow_up_count']}"
        )

        # If follow-up needed, generate and send
        if decision["needs_followup"]:
            # Generate follow-up question with cumulative context
            follow_up_text = await container.llm_port().generate_followup_question(
                parent_question=current_question.text if current_question else "Unknown",
                answer_text=answer.text,
                missing_concepts=decision["cumulative_gaps"],
                severity=answer.gaps.get("severity", "moderate") if answer.gaps else "moderate",
                order=decision["follow_up_count"] + 1,
                cumulative_gaps=decision["cumulative_gaps"],
            )

            # Create and save follow-up question entity
            from ...domain.models.follow_up_question import FollowUpQuestion

            follow_up = FollowUpQuestion(
                parent_question_id=parent_question_id,
                interview_id=interview_id,
                text=follow_up_text,
                generated_reason=decision["reason"],
                order_in_sequence=decision["follow_up_count"] + 1,
            )
            await follow_up_repo.save(follow_up)

            # Track in interview
            interview.add_adaptive_followup(follow_up.id)
            await interview_repo.update(interview)

            # Send follow-up question with audio
            await _send_follow_up_question(interview_id, follow_up, tts)

            logger.info(f"Sent follow-up #{decision['follow_up_count'] + 1}")

            # Exit and wait for next answer
            # NOTE: This breaks the "iterative loop within single handler" pattern
            # Follow-ups are handled by receiving the next message
            break

        # No follow-up needed - send next main question or complete
        if has_more:
            await _send_next_question(
                interview_id, interview, interview_repo, question_repo, tts
            )
        else:
            await _complete_interview(interview_id, interview_repo, answer_repo)

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
        tts = container.text_to_speech_port()

        # Get next question
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

        # Validate interview exists
        interview = await _validate_interview_exists(interview_id, interview_repo)
        if not interview:
            break

        # Send question with audio
        await _send_next_question(
            interview_id, interview, interview_repo, question_repo, tts
        )
        break
