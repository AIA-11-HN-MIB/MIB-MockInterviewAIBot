"""Interview session orchestrator with state machine pattern."""

import base64
import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from ....application.use_cases.complete_interview import CompleteInterviewUseCase
from ....application.use_cases.follow_up_decision import FollowUpDecisionUseCase
from ....application.use_cases.get_next_question import GetNextQuestionUseCase
from ....application.use_cases.process_answer_adaptive import (
    ProcessAnswerAdaptiveUseCase,
)
from ....domain.models.answer import Answer
from ....domain.models.follow_up_question import FollowUpQuestion
from ....domain.ports.answer_repository_port import AnswerRepositoryPort
from ....domain.ports.follow_up_question_repository_port import (
    FollowUpQuestionRepositoryPort,
)
from ....domain.ports.interview_repository_port import InterviewRepositoryPort
from ....domain.ports.question_repository_port import QuestionRepositoryPort
from ....infrastructure.database.session import get_async_session

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Interview session states."""

    IDLE = "idle"
    QUESTIONING = "questioning"
    EVALUATING = "evaluating"
    FOLLOW_UP = "follow_up"
    COMPLETE = "complete"


class InterviewSessionOrchestrator:
    """Orchestrate interview session lifecycle with state machine pattern.

    This orchestrator manages the complete interview flow:
    - State transitions (IDLE → QUESTIONING → EVALUATING → FOLLOW_UP → COMPLETE)
    - Progress tracking (current question, follow-up count)
    - Error recovery and timeout handling
    - Session persistence

    The state machine ensures valid transitions and prevents invalid operations.
    """

    def __init__(
        self,
        interview_id: UUID,
        websocket: WebSocket,
        container: Any,
    ):
        """Initialize session orchestrator.

        Args:
            interview_id: Interview UUID
            websocket: WebSocket connection
            container: Dependency injection container
        """
        self.interview_id = interview_id
        self.websocket = websocket
        self.container = container
        self.state = SessionState.IDLE
        self.current_question_id: UUID | None = None
        self.parent_question_id: UUID | None = None  # For follow-up tracking
        self.follow_up_count = 0
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()

        logger.info(
            f"Session orchestrator created for interview {interview_id}",
            extra={"interview_id": str(interview_id), "state": self.state},
        )

    def _transition(self, new_state: SessionState) -> None:
        """Transition to new state with validation.

        Args:
            new_state: Target state

        Raises:
            ValueError: If transition is invalid

        State transition rules:
        - IDLE → QUESTIONING (start interview)
        - QUESTIONING → EVALUATING (answer received)
        - EVALUATING → FOLLOW_UP (follow-up needed)
        - EVALUATING → QUESTIONING (next main question)
        - EVALUATING → COMPLETE (no more questions)
        - FOLLOW_UP → EVALUATING (follow-up answered)
        """
        valid_transitions = {
            SessionState.IDLE: [SessionState.QUESTIONING],
            SessionState.QUESTIONING: [SessionState.EVALUATING],
            SessionState.EVALUATING: [
                SessionState.FOLLOW_UP,
                SessionState.QUESTIONING,
                SessionState.COMPLETE,
            ],
            SessionState.FOLLOW_UP: [SessionState.EVALUATING],
            SessionState.COMPLETE: [],  # Terminal state
        }

        allowed = valid_transitions.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"Invalid state transition: {self.state} → {new_state}. "
                f"Allowed transitions from {self.state}: {allowed}"
            )

        old_state = self.state
        self.state = new_state
        self.last_activity = datetime.utcnow()

        logger.info(
            f"State transition: {old_state} → {new_state}",
            extra={
                "interview_id": str(self.interview_id),
                "from_state": old_state,
                "to_state": new_state,
            },
        )

    async def start_session(self) -> None:
        """Start interview session by sending first question.

        Raises:
            ValueError: If session already started, interview not found, or no questions
        """
        if self.state != SessionState.IDLE:
            raise ValueError(f"Session already started (current state: {self.state})")

        async for session in get_async_session():
            interview_repo = self.container.interview_repository_port(session)
            question_repo = self.container.question_repository_port(session)
            tts = self.container.text_to_speech_port()

            # Get interview for context (before transitioning state)
            interview = await interview_repo.get_by_id(self.interview_id)
            if not interview:
                logger.error(f"Interview {self.interview_id} not found")
                await self._send_error("INTERVIEW_NOT_FOUND", "Interview not found")
                raise ValueError(f"Interview {self.interview_id} not found")

            # Get first question (before transitioning state)
            use_case = GetNextQuestionUseCase(
                interview_repository=interview_repo,
                question_repository=question_repo,
            )
            question = await use_case.execute(self.interview_id)

            if not question:
                logger.error(f"No questions available for interview {self.interview_id}")
                await self._send_error("NO_QUESTIONS", "No questions available")
                raise ValueError(f"No questions available for interview {self.interview_id}")

            # Now transition to QUESTIONING (after validation)
            self._transition(SessionState.QUESTIONING)

            # Track current question
            self.current_question_id = question.id
            self.parent_question_id = question.id  # First question is its own parent

            # Generate TTS audio
            audio_bytes = await tts.synthesize_speech(question.text)
            audio_data = base64.b64encode(audio_bytes).decode("utf-8")

            # Send question message
            await self._send_message(
                {
                    "type": "question",
                    "question_id": str(question.id),
                    "text": question.text,
                    "question_type": question.question_type,
                    "difficulty": question.difficulty,
                    "index": interview.current_question_index,
                    "total": len(interview.question_ids),
                    "audio_data": audio_data,
                }
            )

            logger.info(
                f"Sent first question: {question.id}",
                extra={
                    "interview_id": str(self.interview_id),
                    "question_id": str(question.id),
                },
            )
            break

    async def handle_answer(self, answer_text: str) -> None:
        """Handle answer based on current state.

        Args:
            answer_text: Candidate's answer text

        Raises:
            ValueError: If called in invalid state
        """
        if self.state == SessionState.QUESTIONING:
            await self._handle_main_question_answer(answer_text)

        elif self.state == SessionState.FOLLOW_UP:
            await self._handle_followup_answer(answer_text)

        else:
            raise ValueError(
                f"Cannot handle answer in state {self.state}. "
                f"Expected QUESTIONING or FOLLOW_UP"
            )

    async def _handle_main_question_answer(self, answer_text: str) -> None:
        """Handle answer to main question.

        Flow:
        1. Transition to EVALUATING
        2. Process answer (evaluation + gap detection)
        3. Make follow-up decision
        4. Either send follow-up OR next main question OR complete

        Args:
            answer_text: Candidate's answer text
        """
        self._transition(SessionState.EVALUATING)

        async for session in get_async_session():
            interview_repo = self.container.interview_repository_port(session)
            question_repo = self.container.question_repository_port(session)
            answer_repo = self.container.answer_repository_port(session)
            follow_up_repo = self.container.follow_up_question_repository()

            # Process answer with adaptive evaluation
            use_case = ProcessAnswerAdaptiveUseCase(
                answer_repository=answer_repo,
                interview_repository=interview_repo,
                question_repository=question_repo,
                follow_up_question_repository=follow_up_repo,
                llm=self.container.llm_port(),
                vector_search=self.container.vector_search_port(),
            )

            answer, has_more = await use_case.execute(
                interview_id=self.interview_id,
                question_id=self.current_question_id,  # type: ignore
                answer_text=answer_text,
            )

            # Send evaluation
            await self._send_evaluation(answer)

            # Make follow-up decision
            decision_use_case = FollowUpDecisionUseCase(
                answer_repository=answer_repo,
                follow_up_question_repository=follow_up_repo,
            )

            decision = await decision_use_case.execute(
                interview_id=self.interview_id,
                parent_question_id=self.parent_question_id,  # type: ignore
                latest_answer=answer,
            )

            logger.info(
                f"Follow-up decision: needs={decision['needs_followup']}, "
                f"reason='{decision['reason']}', count={decision['follow_up_count']}"
            )

            # If follow-up needed, generate and send
            if decision["needs_followup"]:
                await self._generate_and_send_followup(
                    answer, decision, question_repo, follow_up_repo, interview_repo
                )
                break

            # No follow-up needed - send next main question or complete
            if has_more:
                await self._send_next_main_question(interview_repo, question_repo)
            else:
                await self._complete_interview(interview_repo, answer_repo)

            break

    async def _handle_followup_answer(self, answer_text: str) -> None:
        """Handle answer to follow-up question.

        Flow:
        1. Transition to EVALUATING
        2. Process answer (evaluation + gap detection)
        3. Make follow-up decision again (may generate another follow-up)
        4. Either send another follow-up OR next main question OR complete

        Args:
            answer_text: Candidate's answer text
        """
        self._transition(SessionState.EVALUATING)

        async for session in get_async_session():
            interview_repo = self.container.interview_repository_port(session)
            question_repo = self.container.question_repository_port(session)
            answer_repo = self.container.answer_repository_port(session)
            follow_up_repo = self.container.follow_up_question_repository()

            # Process answer (current_question_id is follow-up question ID)
            use_case = ProcessAnswerAdaptiveUseCase(
                answer_repository=answer_repo,
                interview_repository=interview_repo,
                question_repository=question_repo,
                follow_up_question_repository=follow_up_repo,
                llm=self.container.llm_port(),
                vector_search=self.container.vector_search_port(),
            )

            answer, has_more = await use_case.execute(
                interview_id=self.interview_id,
                question_id=self.current_question_id,  # type: ignore
                answer_text=answer_text,
            )

            # Send evaluation
            await self._send_evaluation(answer)

            # Make follow-up decision (using parent question ID)
            decision_use_case = FollowUpDecisionUseCase(
                answer_repository=answer_repo,
                follow_up_question_repository=follow_up_repo,
            )

            decision = await decision_use_case.execute(
                interview_id=self.interview_id,
                parent_question_id=self.parent_question_id,  # type: ignore
                latest_answer=answer,
            )

            logger.info(
                f"Follow-up decision (after follow-up): needs={decision['needs_followup']}, "
                f"reason='{decision['reason']}', count={decision['follow_up_count']}"
            )

            # If another follow-up needed, generate and send
            if decision["needs_followup"]:
                await self._generate_and_send_followup(
                    answer, decision, question_repo, follow_up_repo, interview_repo
                )
                break

            # No more follow-ups - send next main question or complete
            if has_more:
                await self._send_next_main_question(interview_repo, question_repo)
            else:
                await self._complete_interview(interview_repo, answer_repo)

            break

    async def _generate_and_send_followup(
        self,
        answer: Answer,
        decision: dict[str, Any],
        question_repo: QuestionRepositoryPort,
        follow_up_repo: FollowUpQuestionRepositoryPort,
        interview_repo: InterviewRepositoryPort,
    ) -> None:
        """Generate and send follow-up question.

        Args:
            answer: Latest answer entity
            decision: Follow-up decision dict
            question_repo: Question repository
            follow_up_repo: Follow-up question repository
            interview_repo: Interview repository
        """
        # Get current question for context
        current_question = await question_repo.get_by_id(self.parent_question_id)  # type: ignore

        # Generate follow-up question with cumulative context
        follow_up_text = await self.container.llm_port().generate_followup_question(
            parent_question=current_question.text if current_question else "Unknown",
            answer_text=answer.text,
            missing_concepts=decision["cumulative_gaps"],
            severity=answer.gaps.get("severity", "moderate") if answer.gaps else "moderate",
            order=decision["follow_up_count"] + 1,
            cumulative_gaps=decision["cumulative_gaps"],
        )

        # Create and save follow-up question entity
        follow_up = FollowUpQuestion(
            parent_question_id=self.parent_question_id,  # type: ignore
            interview_id=self.interview_id,
            text=follow_up_text,
            generated_reason=decision["reason"],
            order_in_sequence=decision["follow_up_count"] + 1,
        )
        await follow_up_repo.save(follow_up)

        # Track in interview
        interview = await interview_repo.get_by_id(self.interview_id)
        if interview:
            interview.add_adaptive_followup(follow_up.id)
            await interview_repo.update(interview)

        # Update session state
        self.current_question_id = follow_up.id
        self.follow_up_count = decision["follow_up_count"] + 1
        self._transition(SessionState.FOLLOW_UP)

        # Send follow-up question with audio
        tts = self.container.text_to_speech_port()
        audio_bytes = await tts.synthesize_speech(follow_up.text)
        audio_data = base64.b64encode(audio_bytes).decode("utf-8")

        await self._send_message(
            {
                "type": "follow_up_question",
                "question_id": str(follow_up.id),
                "parent_question_id": str(follow_up.parent_question_id),
                "text": follow_up.text,
                "generated_reason": follow_up.generated_reason,
                "order_in_sequence": follow_up.order_in_sequence,
                "audio_data": audio_data,
            }
        )

        logger.info(f"Sent follow-up #{self.follow_up_count}")

    async def _send_next_main_question(
        self,
        interview_repo: InterviewRepositoryPort,
        question_repo: QuestionRepositoryPort,
    ) -> None:
        """Send next main question.

        Args:
            interview_repo: Interview repository
            question_repo: Question repository
        """
        # Reset follow-up tracking
        self.follow_up_count = 0

        # Get next question
        use_case = GetNextQuestionUseCase(
            interview_repository=interview_repo,
            question_repository=question_repo,
        )
        question = await use_case.execute(self.interview_id)

        if not question:
            logger.warning(f"No more questions for interview {self.interview_id}")
            await self._complete_interview(interview_repo, None)
            return

        # Update session state
        self.current_question_id = question.id
        self.parent_question_id = question.id  # New main question
        self._transition(SessionState.QUESTIONING)

        # Get interview for context
        interview = await interview_repo.get_by_id(self.interview_id)

        # Generate TTS audio
        tts = self.container.text_to_speech_port()
        audio_bytes = await tts.synthesize_speech(question.text)
        audio_data = base64.b64encode(audio_bytes).decode("utf-8")

        # Send question message
        await self._send_message(
            {
                "type": "question",
                "question_id": str(question.id),
                "text": question.text,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
                "index": interview.current_question_index if interview else 0,
                "total": len(interview.question_ids) if interview else 0,
                "audio_data": audio_data,
            }
        )

        logger.info(f"Sent next main question: {question.id}")

    async def _complete_interview(
        self,
        interview_repo: InterviewRepositoryPort,
        answer_repo: AnswerRepositoryPort | None,
    ) -> None:
        """Complete interview and send final results.

        Args:
            interview_repo: Interview repository
            answer_repo: Answer repository (optional)
        """
        self._transition(SessionState.COMPLETE)

        # Complete interview
        complete_use_case = CompleteInterviewUseCase(
            interview_repository=interview_repo,
        )
        interview = await complete_use_case.execute(self.interview_id)

        # Calculate overall score
        overall_score = 0.0
        if answer_repo:
            answers = await answer_repo.get_by_interview_id(self.interview_id)
            if answers:
                overall_score = (
                    sum(a.evaluation.score for a in answers if a.evaluation)
                    / len(answers)
                )

        await self._send_message(
            {
                "type": "interview_complete",
                "interview_id": str(interview.id),
                "overall_score": overall_score,
                "total_questions": len(interview.question_ids),
                "feedback_url": f"/api/interviews/{self.interview_id}/feedback",
            }
        )

        logger.info(f"Interview {self.interview_id} completed")

    async def _send_evaluation(self, answer: Answer) -> None:
        """Send evaluation message.

        Args:
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

        await self._send_message(eval_message)

    async def _send_message(self, message: dict) -> None:
        """Send message to client via WebSocket.

        Args:
            message: Message dict to send
        """
        from .connection_manager import manager

        await manager.send_message(self.interview_id, message)

    async def _send_error(self, code: str, message: str) -> None:
        """Send error message to client.

        Args:
            code: Error code
            message: Error message
        """
        await self._send_message(
            {
                "type": "error",
                "code": code,
                "message": message,
            }
        )

    def get_state(self) -> dict[str, Any]:
        """Get current session state for persistence.

        Returns:
            State dict with all session data
        """
        return {
            "interview_id": str(self.interview_id),
            "state": self.state,
            "current_question_id": str(self.current_question_id) if self.current_question_id else None,
            "parent_question_id": str(self.parent_question_id) if self.parent_question_id else None,
            "follow_up_count": self.follow_up_count,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }
