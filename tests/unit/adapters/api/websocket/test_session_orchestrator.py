"""Unit tests for InterviewSessionOrchestrator (Phase 5)."""

import base64
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from src.adapters.api.websocket.session_orchestrator import (
    InterviewSessionOrchestrator,
    SessionState,
)
from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.follow_up_question import FollowUpQuestion
from src.domain.models.interview import Interview, InterviewStatus
from src.domain.models.question import DifficultyLevel, Question, QuestionType


# ==================== Fixtures ====================


@pytest.fixture
def interview_id():
    """Sample interview ID."""
    return uuid4()


@pytest.fixture
def question_id():
    """Sample question ID."""
    return uuid4()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    return ws


@pytest.fixture
def mock_container():
    """Mock dependency injection container."""
    container = MagicMock()

    # Mock repositories
    container.interview_repository_port = MagicMock()
    container.question_repository_port = MagicMock()
    container.answer_repository_port = MagicMock()
    container.follow_up_question_repository = MagicMock()

    # Mock services
    container.llm_port = MagicMock()
    container.vector_search_port = MagicMock()
    container.text_to_speech_port = MagicMock()

    return container


@pytest.fixture
def sample_question():
    """Sample question entity."""
    return Question(
        text="Explain recursion in programming",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.MEDIUM,
        skills=["Python", "Algorithms"],
        ideal_answer="Recursion is when a function calls itself...",
    )


@pytest.fixture
def sample_interview(interview_id, question_id):
    """Sample interview entity."""
    interview = Interview(
        candidate_id=uuid4(),
        status=InterviewStatus.IN_PROGRESS,
        cv_analysis_id=uuid4(),
    )
    interview.id = interview_id
    interview.question_ids = [question_id, uuid4(), uuid4()]
    interview.current_question_index = 0
    return interview


@pytest.fixture
def sample_answer(interview_id, question_id):
    """Sample answer with evaluation."""
    answer = Answer(
        interview_id=interview_id,
        question_id=question_id,
        candidate_id=uuid4(),
        text="Recursion is when a function calls itself to solve problems.",
        is_voice=False,
        similarity_score=0.75,
        gaps={
            "concepts": ["base case", "call stack"],
            "keywords": ["base", "stack"],
            "confirmed": True,
            "severity": "moderate",
        },
    )
    answer.evaluate(
        AnswerEvaluation(
            score=75.0,
            semantic_similarity=0.75,
            completeness=0.7,
            relevance=0.9,
            sentiment="uncertain",
            reasoning="Answer needs more detail on base case and call stack",
            strengths=["Correct definition"],
            weaknesses=["Missing base case", "No call stack explanation"],
            improvement_suggestions=["Explain base case", "Describe call stack"],
        )
    )
    return answer


@pytest.fixture
def orchestrator(interview_id, mock_websocket, mock_container):
    """Create orchestrator instance."""
    return InterviewSessionOrchestrator(
        interview_id=interview_id,
        websocket=mock_websocket,
        container=mock_container,
    )


# ==================== State Transition Tests ====================


class TestStateTransitions:
    """Test state machine transition logic."""

    def test_initial_state_is_idle(self, orchestrator):
        """Test orchestrator starts in IDLE state."""
        assert orchestrator.state == SessionState.IDLE

    def test_valid_transition_idle_to_questioning(self, orchestrator):
        """Test valid transition from IDLE to QUESTIONING."""
        orchestrator._transition(SessionState.QUESTIONING)
        assert orchestrator.state == SessionState.QUESTIONING

    def test_invalid_transition_idle_to_evaluating(self, orchestrator):
        """Test invalid transition from IDLE to EVALUATING raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.EVALUATING)

    def test_invalid_transition_idle_to_follow_up(self, orchestrator):
        """Test invalid transition from IDLE to FOLLOW_UP raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.FOLLOW_UP)

    def test_invalid_transition_idle_to_complete(self, orchestrator):
        """Test invalid transition from IDLE to COMPLETE raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.COMPLETE)

    def test_valid_transition_questioning_to_evaluating(self, orchestrator):
        """Test valid transition from QUESTIONING to EVALUATING."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        assert orchestrator.state == SessionState.EVALUATING

    def test_invalid_transition_questioning_to_follow_up(self, orchestrator):
        """Test invalid direct transition from QUESTIONING to FOLLOW_UP."""
        orchestrator._transition(SessionState.QUESTIONING)
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.FOLLOW_UP)

    def test_valid_transition_evaluating_to_follow_up(self, orchestrator):
        """Test valid transition from EVALUATING to FOLLOW_UP."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.FOLLOW_UP)
        assert orchestrator.state == SessionState.FOLLOW_UP

    def test_valid_transition_evaluating_to_questioning(self, orchestrator):
        """Test valid transition from EVALUATING to QUESTIONING (next question)."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.QUESTIONING)
        assert orchestrator.state == SessionState.QUESTIONING

    def test_valid_transition_evaluating_to_complete(self, orchestrator):
        """Test valid transition from EVALUATING to COMPLETE."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.COMPLETE)
        assert orchestrator.state == SessionState.COMPLETE

    def test_valid_transition_follow_up_to_evaluating(self, orchestrator):
        """Test valid transition from FOLLOW_UP to EVALUATING."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.FOLLOW_UP)
        orchestrator._transition(SessionState.EVALUATING)
        assert orchestrator.state == SessionState.EVALUATING

    def test_invalid_transition_follow_up_to_questioning(self, orchestrator):
        """Test invalid direct transition from FOLLOW_UP to QUESTIONING."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.FOLLOW_UP)
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.QUESTIONING)

    def test_terminal_state_complete_rejects_all_transitions(self, orchestrator):
        """Test COMPLETE state rejects all transitions (terminal state)."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.COMPLETE)

        # Try all possible transitions from COMPLETE
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.IDLE)

        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.QUESTIONING)

        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.EVALUATING)

        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.FOLLOW_UP)

    def test_transition_updates_last_activity(self, orchestrator):
        """Test transition updates last_activity timestamp."""
        old_time = orchestrator.last_activity
        import time
        time.sleep(0.01)  # Small delay
        orchestrator._transition(SessionState.QUESTIONING)
        assert orchestrator.last_activity > old_time

    def test_error_message_shows_allowed_transitions(self, orchestrator):
        """Test error message includes allowed transitions for clarity."""
        with pytest.raises(ValueError) as exc_info:
            orchestrator._transition(SessionState.EVALUATING)

        error_msg = str(exc_info.value)
        assert "IDLE" in error_msg
        assert "EVALUATING" in error_msg
        assert "Allowed transitions" in error_msg


# ==================== Session Lifecycle Tests ====================


class TestSessionLifecycle:
    """Test session lifecycle methods."""

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_start_session_sends_first_question(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        sample_interview,
        mock_container,
    ):
        """Test start_session transitions to QUESTIONING and sends first question."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_get_session.return_value.__aexit__ = AsyncMock()

        # Mock async generators to return properly
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_question_repo.get_by_id = AsyncMock(return_value=sample_question)
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_tts = AsyncMock()
        mock_tts.synthesize_speech = AsyncMock(return_value=b"fake_audio")
        mock_container.text_to_speech_port.return_value = mock_tts

        # Mock GetNextQuestionUseCase
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_question)
            mock_use_case.return_value = mock_instance

            # Mock connection manager
            with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                mock_manager.send_message = AsyncMock()

                # Execute
                await orchestrator.start_session()

                # Verify state transition
                assert orchestrator.state == SessionState.QUESTIONING

                # Verify current_question_id set
                assert orchestrator.current_question_id == sample_question.id
                assert orchestrator.parent_question_id == sample_question.id

                # Verify message sent
                mock_manager.send_message.assert_called_once()
                call_args = mock_manager.send_message.call_args[0]
                message = call_args[1]
                assert message["type"] == "question"
                assert message["question_id"] == str(sample_question.id)
                assert message["text"] == sample_question.text
                assert "audio_data" in message

    @pytest.mark.asyncio
    async def test_start_session_already_started_raises_error(self, orchestrator):
        """Test start_session raises ValueError if session already started."""
        orchestrator._transition(SessionState.QUESTIONING)

        with pytest.raises(ValueError, match="Session already started"):
            await orchestrator.start_session()

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_start_session_no_questions_available(
        self,
        mock_get_session,
        orchestrator,
        sample_interview,
        mock_container,
    ):
        """Test start_session handles no questions available (raises ValueError).

        FIXED: Now validates questions exist BEFORE transitioning to QUESTIONING state.
        This prevents invalid state transitions and keeps state machine clean.
        """
        # Setup mocks
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_tts = AsyncMock()
        mock_container.text_to_speech_port.return_value = mock_tts

        # Mock GetNextQuestionUseCase to return None
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=None)
            mock_use_case.return_value = mock_instance

            # Mock connection manager
            with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                mock_manager.send_message = AsyncMock()

                # Execute - should raise ValueError with clear message
                with pytest.raises(ValueError, match="No questions available"):
                    await orchestrator.start_session()

                # State should remain IDLE (never transitioned)
                assert orchestrator.state == SessionState.IDLE

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_start_session_interview_not_found(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        mock_container,
    ):
        """Test start_session handles interview not found (raises ValueError).

        FIXED: Now validates interview exists BEFORE transitioning to QUESTIONING state.
        """
        # Setup mocks
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=None)  # Not found
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_tts = AsyncMock()
        mock_container.text_to_speech_port.return_value = mock_tts

        # Mock GetNextQuestionUseCase
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_question)
            mock_use_case.return_value = mock_instance

            # Mock connection manager
            with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                mock_manager.send_message = AsyncMock()

                # Execute - should raise ValueError with clear message
                with pytest.raises(ValueError, match="Interview.*not found"):
                    await orchestrator.start_session()

                # State should remain IDLE (never transitioned)
                assert orchestrator.state == SessionState.IDLE

    @pytest.mark.asyncio
    async def test_handle_answer_in_questioning_state(self, orchestrator):
        """Test handle_answer calls _handle_main_question_answer in QUESTIONING state."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator.current_question_id = uuid4()

        with patch.object(orchestrator, "_handle_main_question_answer", new=AsyncMock()) as mock_handler:
            await orchestrator.handle_answer("Test answer")
            mock_handler.assert_called_once_with("Test answer")

    @pytest.mark.asyncio
    async def test_handle_answer_in_follow_up_state(self, orchestrator):
        """Test handle_answer calls _handle_followup_answer in FOLLOW_UP state."""
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.FOLLOW_UP)
        orchestrator.current_question_id = uuid4()

        with patch.object(orchestrator, "_handle_followup_answer", new=AsyncMock()) as mock_handler:
            await orchestrator.handle_answer("Test answer")
            mock_handler.assert_called_once_with("Test answer")

    @pytest.mark.asyncio
    async def test_handle_answer_in_invalid_state_raises_error(self, orchestrator):
        """Test handle_answer raises ValueError in invalid states."""
        # IDLE state
        with pytest.raises(ValueError, match="Cannot handle answer"):
            await orchestrator.handle_answer("Test answer")

        # EVALUATING state
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator._transition(SessionState.EVALUATING)
        with pytest.raises(ValueError, match="Cannot handle answer"):
            await orchestrator.handle_answer("Test answer")

        # COMPLETE state
        orchestrator._transition(SessionState.COMPLETE)
        with pytest.raises(ValueError, match="Cannot handle answer"):
            await orchestrator.handle_answer("Test answer")


# ==================== Follow-up Logic Tests ====================


class TestFollowUpLogic:
    """Test follow-up question generation and tracking."""

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_follow_up_generated_when_gaps_detected(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        sample_interview,
        sample_answer,
        mock_container,
    ):
        """Test follow-up question generated when gaps detected."""
        # Setup
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator.current_question_id = sample_question.id
        orchestrator.parent_question_id = sample_question.id

        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        # Mock repositories
        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_interview_repo.update = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_question_repo.get_by_id = AsyncMock(return_value=sample_question)
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_answer_repo = AsyncMock()
        mock_container.answer_repository_port.return_value = mock_answer_repo

        mock_follow_up_repo = AsyncMock()
        mock_follow_up_repo.save = AsyncMock(side_effect=lambda x: x)
        mock_container.follow_up_question_repository.return_value = mock_follow_up_repo

        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.generate_followup_question = AsyncMock(
            return_value="Can you explain what a base case is?"
        )
        mock_container.llm_port.return_value = mock_llm

        # Mock vector search
        mock_vector_search = AsyncMock()
        mock_container.vector_search_port.return_value = mock_vector_search

        # Mock TTS
        mock_tts = AsyncMock()
        mock_tts.synthesize_speech = AsyncMock(return_value=b"fake_audio")
        mock_container.text_to_speech_port.return_value = mock_tts

        # Mock ProcessAnswerAdaptiveUseCase to return answer with gaps
        with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=(sample_answer, True))
            mock_use_case.return_value = mock_instance

            # Mock FollowUpDecisionUseCase to say follow-up needed
            with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision_use_case:
                mock_decision_instance = AsyncMock()
                mock_decision_instance.execute = AsyncMock(return_value={
                    "needs_followup": True,
                    "reason": "2 missing concepts: base case, call stack",
                    "follow_up_count": 0,
                    "cumulative_gaps": ["base case", "call stack"],
                })
                mock_decision_use_case.return_value = mock_decision_instance

                # Mock connection manager
                with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                    mock_manager.send_message = AsyncMock()

                    # Execute
                    await orchestrator.handle_answer("Brief answer")

                    # Verify state transitioned to FOLLOW_UP
                    assert orchestrator.state == SessionState.FOLLOW_UP

                    # Verify follow-up count incremented
                    assert orchestrator.follow_up_count == 1

                    # Verify follow-up question saved
                    mock_follow_up_repo.save.assert_called_once()

                    # Verify follow-up message sent
                    follow_up_calls = [c for c in mock_manager.send_message.call_args_list
                                      if c[0][1].get("type") == "follow_up_question"]
                    assert len(follow_up_calls) == 1
                    follow_up_msg = follow_up_calls[0][0][1]
                    assert follow_up_msg["parent_question_id"] == str(sample_question.id)
                    assert follow_up_msg["order_in_sequence"] == 1

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_max_3_follow_ups_enforced_by_decision_use_case(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        sample_interview,
        sample_answer,
        mock_container,
    ):
        """Test that FollowUpDecisionUseCase enforces max 3 follow-ups."""
        # Setup - already at 3 follow-ups
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator.current_question_id = sample_question.id
        orchestrator.parent_question_id = sample_question.id
        orchestrator.follow_up_count = 3  # Already at max

        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        # Mock repositories
        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_question_repo.get_by_id = AsyncMock(return_value=sample_question)
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_answer_repo = AsyncMock()
        mock_container.answer_repository_port.return_value = mock_answer_repo

        mock_follow_up_repo = AsyncMock()
        mock_container.follow_up_question_repository.return_value = mock_follow_up_repo

        mock_llm = AsyncMock()
        mock_container.llm_port.return_value = mock_llm

        mock_vector_search = AsyncMock()
        mock_container.vector_search_port.return_value = mock_vector_search

        # Mock ProcessAnswerAdaptiveUseCase
        with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=(sample_answer, True))
            mock_use_case.return_value = mock_instance

            # Mock FollowUpDecisionUseCase to say NO follow-up (max reached)
            with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision_use_case:
                mock_decision_instance = AsyncMock()
                mock_decision_instance.execute = AsyncMock(return_value={
                    "needs_followup": False,
                    "reason": "Max follow-ups (3) reached",
                    "follow_up_count": 3,
                    "cumulative_gaps": ["base case", "call stack"],
                })
                mock_decision_use_case.return_value = mock_decision_instance

                # Mock GetNextQuestionUseCase for next main question
                with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_next_q:
                    next_question = Question(
                        text="Next question",
                        question_type=QuestionType.TECHNICAL,
                        difficulty=DifficultyLevel.MEDIUM,
                        skills=["Python"],
                    )
                    mock_next_instance = AsyncMock()
                    mock_next_instance.execute = AsyncMock(return_value=next_question)
                    mock_next_q.return_value = mock_next_instance

                    # Mock TTS
                    mock_tts = AsyncMock()
                    mock_tts.synthesize_speech = AsyncMock(return_value=b"fake_audio")
                    mock_container.text_to_speech_port.return_value = mock_tts

                    # Mock connection manager
                    with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                        mock_manager.send_message = AsyncMock()

                        # Execute
                        await orchestrator.handle_answer("Another brief answer")

                        # Verify no follow-up generated (should move to next main question)
                        assert orchestrator.state == SessionState.QUESTIONING

                        # Verify follow_up_count reset to 0 for next question
                        assert orchestrator.follow_up_count == 0

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_follow_up_count_tracking(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        sample_interview,
        sample_answer,
        mock_container,
    ):
        """Test follow-up count increments correctly."""
        # Setup
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator.current_question_id = sample_question.id
        orchestrator.parent_question_id = sample_question.id

        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        # Need to return new generator each time
        mock_get_session.return_value = async_gen()

        # Mock all dependencies
        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_interview_repo.update = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_question_repo.get_by_id = AsyncMock(return_value=sample_question)
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_answer_repo = AsyncMock()
        mock_container.answer_repository_port.return_value = mock_answer_repo

        mock_follow_up_repo = AsyncMock()
        mock_follow_up_repo.save = AsyncMock(side_effect=lambda x: x)
        mock_container.follow_up_question_repository.return_value = mock_follow_up_repo

        mock_llm = AsyncMock()
        mock_llm.generate_followup_question = AsyncMock(return_value="Follow-up question")
        mock_container.llm_port.return_value = mock_llm

        mock_vector_search = AsyncMock()
        mock_container.vector_search_port.return_value = mock_vector_search

        mock_tts = AsyncMock()
        mock_tts.synthesize_speech = AsyncMock(return_value=b"fake_audio")
        mock_container.text_to_speech_port.return_value = mock_tts

        # Mock use cases
        with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=(sample_answer, True))
            mock_use_case.return_value = mock_instance

            with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                # First follow-up
                mock_decision_instance = AsyncMock()
                mock_decision_instance.execute = AsyncMock(return_value={
                    "needs_followup": True,
                    "reason": "Gaps detected",
                    "follow_up_count": 0,
                    "cumulative_gaps": ["concept1"],
                })
                mock_decision.return_value = mock_decision_instance

                with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                    mock_manager.send_message = AsyncMock()

                    # Reset mock_get_session for first call
                    mock_get_session.side_effect = [async_gen(), async_gen()]

                    # Generate first follow-up
                    await orchestrator.handle_answer("Answer 1")
                    assert orchestrator.follow_up_count == 1
                    assert orchestrator.state == SessionState.FOLLOW_UP

                    # Update decision for second follow-up
                    mock_decision_instance.execute.return_value = {
                        "needs_followup": True,
                        "reason": "More gaps",
                        "follow_up_count": 1,
                        "cumulative_gaps": ["concept1", "concept2"],
                    }

                    # Answer the follow-up question, which should generate another follow-up
                    await orchestrator.handle_answer("Answer 2")
                    assert orchestrator.follow_up_count == 2

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_parent_question_id_tracking(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        sample_interview,
        sample_answer,
        mock_container,
    ):
        """Test parent_question_id remains consistent across follow-ups."""
        # Setup
        orchestrator._transition(SessionState.QUESTIONING)
        orchestrator.current_question_id = sample_question.id
        orchestrator.parent_question_id = sample_question.id
        original_parent_id = sample_question.id

        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        # Mock dependencies
        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_interview_repo.update = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_question_repo.get_by_id = AsyncMock(return_value=sample_question)
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_answer_repo = AsyncMock()
        mock_container.answer_repository_port.return_value = mock_answer_repo

        mock_follow_up_repo = AsyncMock()
        mock_follow_up_repo.save = AsyncMock(side_effect=lambda x: x)
        mock_container.follow_up_question_repository.return_value = mock_follow_up_repo

        mock_llm = AsyncMock()
        mock_llm.generate_followup_question = AsyncMock(return_value="Follow-up question")
        mock_container.llm_port.return_value = mock_llm

        mock_vector_search = AsyncMock()
        mock_container.vector_search_port.return_value = mock_vector_search

        mock_tts = AsyncMock()
        mock_tts.synthesize_speech = AsyncMock(return_value=b"fake_audio")
        mock_container.text_to_speech_port.return_value = mock_tts

        with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=(sample_answer, True))
            mock_use_case.return_value = mock_instance

            with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                mock_decision_instance = AsyncMock()
                mock_decision_instance.execute = AsyncMock(return_value={
                    "needs_followup": True,
                    "reason": "Gaps",
                    "follow_up_count": 0,
                    "cumulative_gaps": ["concept1"],
                })
                mock_decision.return_value = mock_decision_instance

                with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                    mock_manager.send_message = AsyncMock()

                    # Generate follow-up
                    await orchestrator.handle_answer("Answer")

                    # Verify parent_question_id unchanged
                    assert orchestrator.parent_question_id == original_parent_id

                    # Verify current_question_id changed to follow-up ID
                    assert orchestrator.current_question_id != original_parent_id


# ==================== Progress Tracking Tests ====================


class TestProgressTracking:
    """Test progress tracking functionality."""

    def test_current_question_id_updates_correctly(self, orchestrator):
        """Test current_question_id tracks current question."""
        assert orchestrator.current_question_id is None

        q_id = uuid4()
        orchestrator.current_question_id = q_id
        assert orchestrator.current_question_id == q_id

    def test_follow_up_count_increments(self, orchestrator):
        """Test follow_up_count increments."""
        assert orchestrator.follow_up_count == 0

        orchestrator.follow_up_count += 1
        assert orchestrator.follow_up_count == 1

        orchestrator.follow_up_count += 1
        assert orchestrator.follow_up_count == 2

    def test_follow_up_count_resets_on_next_main_question(self, orchestrator):
        """Test follow_up_count resets when moving to next main question."""
        orchestrator.follow_up_count = 3
        orchestrator.follow_up_count = 0  # Reset
        assert orchestrator.follow_up_count == 0

    def test_get_state_returns_complete_session_data(self, orchestrator, interview_id):
        """Test get_state returns all session data."""
        # Setup state
        orchestrator._transition(SessionState.QUESTIONING)
        q_id = uuid4()
        orchestrator.current_question_id = q_id
        orchestrator.parent_question_id = q_id
        orchestrator.follow_up_count = 2

        # Get state
        state = orchestrator.get_state()

        # Verify all fields present
        assert state["interview_id"] == str(interview_id)
        assert state["state"] == SessionState.QUESTIONING
        assert state["current_question_id"] == str(q_id)
        assert state["parent_question_id"] == str(q_id)
        assert state["follow_up_count"] == 2
        assert "created_at" in state
        assert "last_activity" in state

    def test_get_state_handles_none_values(self, orchestrator, interview_id):
        """Test get_state handles None for question IDs."""
        state = orchestrator.get_state()

        assert state["interview_id"] == str(interview_id)
        assert state["state"] == SessionState.IDLE
        assert state["current_question_id"] is None
        assert state["parent_question_id"] is None
        assert state["follow_up_count"] == 0

    def test_created_at_set_on_init(self, orchestrator):
        """Test created_at timestamp set on initialization."""
        assert isinstance(orchestrator.created_at, datetime)
        assert orchestrator.created_at <= datetime.utcnow()

    def test_last_activity_updates_on_transition(self, orchestrator):
        """Test last_activity updates on state transitions."""
        old_activity = orchestrator.last_activity
        import time
        time.sleep(0.01)

        orchestrator._transition(SessionState.QUESTIONING)
        assert orchestrator.last_activity > old_activity


# ==================== Error Handling Tests ====================


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_interview_not_found_during_start(
        self,
        mock_get_session,
        orchestrator,
        sample_question,
        mock_container,
    ):
        """Test handling when interview not found during start_session (raises ValueError).

        FIXED: Validates interview exists BEFORE transitioning to QUESTIONING.
        """
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=None)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_tts = AsyncMock()
        mock_container.text_to_speech_port.return_value = mock_tts

        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_question)
            mock_use_case.return_value = mock_instance

            with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                mock_manager.send_message = AsyncMock()

                # Should raise ValueError with clear message
                with pytest.raises(ValueError, match="Interview.*not found"):
                    await orchestrator.start_session()

                # State should remain IDLE (never transitioned)
                assert orchestrator.state == SessionState.IDLE

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    async def test_no_questions_available_during_start(
        self,
        mock_get_session,
        orchestrator,
        sample_interview,
        mock_container,
    ):
        """Test handling when no questions available (raises ValueError).

        FIXED: Validates questions exist BEFORE transitioning to QUESTIONING.
        """
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_interview_repo = AsyncMock()
        mock_interview_repo.get_by_id = AsyncMock(return_value=sample_interview)
        mock_container.interview_repository_port.return_value = mock_interview_repo

        mock_question_repo = AsyncMock()
        mock_container.question_repository_port.return_value = mock_question_repo

        mock_tts = AsyncMock()
        mock_container.text_to_speech_port.return_value = mock_tts

        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_use_case:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=None)  # No questions
            mock_use_case.return_value = mock_instance

            with patch("src.adapters.api.websocket.connection_manager.manager") as mock_manager:
                mock_manager.send_message = AsyncMock()

                # Should raise ValueError with clear message
                with pytest.raises(ValueError, match="No questions available"):
                    await orchestrator.start_session()

                # State should remain IDLE (never transitioned)
                assert orchestrator.state == SessionState.IDLE

    def test_state_transition_validation_errors(self, orchestrator):
        """Test state transition validation raises clear errors."""
        # Invalid from IDLE
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.EVALUATING)

        # Invalid from QUESTIONING
        orchestrator._transition(SessionState.QUESTIONING)
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.FOLLOW_UP)

        # Terminal state COMPLETE
        orchestrator._transition(SessionState.EVALUATING)
        orchestrator._transition(SessionState.COMPLETE)
        with pytest.raises(ValueError, match="Invalid state transition"):
            orchestrator._transition(SessionState.IDLE)
