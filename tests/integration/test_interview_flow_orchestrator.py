"""Integration tests for complete interview flow with InterviewSessionOrchestrator.

These tests verify the end-to-end interview flow using real repositories
and services (with mock LLM/Vector/TTS adapters).
"""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from src.adapters.api.websocket.session_orchestrator import (
    InterviewSessionOrchestrator,
    SessionState,
)
from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.cv_analysis import CVAnalysis, ExtractedSkill
from src.domain.models.follow_up_question import FollowUpQuestion
from src.domain.models.interview import Interview, InterviewStatus
from src.domain.models.question import DifficultyLevel, Question, QuestionType


# ==================== Fixtures ====================


@pytest.fixture
def cv_analysis():
    """Create CV analysis for candidate."""
    return CVAnalysis(
        candidate_id=uuid4(),
        cv_file_path="/path/to/cv.pdf",
        extracted_text="Python developer with FastAPI experience",
        summary="Experienced developer",
        skills=[
            ExtractedSkill(skill="Python", category="technical", proficiency="expert"),
            ExtractedSkill(skill="FastAPI", category="technical", proficiency="intermediate"),
        ],
        work_experience_years=5,
        education_level="Bachelor's",
    )


@pytest.fixture
def questions():
    """Create list of questions for interview."""
    return [
        Question(
            text="Explain recursion in programming",
            question_type=QuestionType.TECHNICAL,
            difficulty=DifficultyLevel.MEDIUM,
            skills=["Python", "Algorithms"],
            ideal_answer="""Recursion is when a function calls itself to solve a problem.
            Key concepts: base case to stop recursion, recursive case to continue calling,
            and call stack management. Examples: factorial, Fibonacci, tree traversal.""",
            rationale="Tests understanding of fundamental programming concepts.",
        ),
        Question(
            text="What is dependency injection?",
            question_type=QuestionType.TECHNICAL,
            difficulty=DifficultyLevel.MEDIUM,
            skills=["Python", "Design Patterns"],
            ideal_answer="""Dependency injection is a design pattern where objects receive
            their dependencies from external sources rather than creating them. Benefits include
            testability, flexibility, and loose coupling.""",
            rationale="Tests understanding of design patterns.",
        ),
        Question(
            text="Describe a challenging project",
            question_type=QuestionType.BEHAVIORAL,
            difficulty=DifficultyLevel.EASY,
            skills=["Communication"],
        ),
    ]


@pytest.fixture
def interview(cv_analysis, questions):
    """Create interview with questions."""
    interview = Interview(
        candidate_id=cv_analysis.candidate_id,
        status=InterviewStatus.IDLE,
        cv_analysis_id=cv_analysis.id,
    )
    interview.plan_metadata = {
        "n": 3,
        "strategy": "adaptive_planning_v1",
        "cv_summary": cv_analysis.summary,
    }
    interview.question_ids = [q.id for q in questions]
    interview.start()  # Move to IN_PROGRESS
    return interview


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    return ws


@pytest.fixture
def mock_container(
    mock_interview_repo,
    mock_question_repo,
    mock_answer_repo,
    mock_follow_up_question_repo,
    mock_llm,
    mock_vector_search,
):
    """Mock DI container with real repository instances."""
    container = MagicMock()

    # Return repository instances
    container.interview_repository_port = MagicMock(return_value=mock_interview_repo)
    container.question_repository_port = MagicMock(return_value=mock_question_repo)
    container.answer_repository_port = MagicMock(return_value=mock_answer_repo)
    container.follow_up_question_repository = MagicMock(return_value=mock_follow_up_question_repo)

    # Return service instances
    container.llm_port = MagicMock(return_value=mock_llm)
    container.vector_search_port = MagicMock(return_value=mock_vector_search)

    # Mock TTS
    mock_tts = AsyncMock()
    mock_tts.synthesize_speech = AsyncMock(return_value=b"fake_audio_data")
    container.text_to_speech_port = MagicMock(return_value=mock_tts)

    return container


# ==================== Integration Tests ====================


class TestCompleteInterviewFlow:
    """Test complete interview flow from start to finish."""

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    @patch("src.adapters.api.websocket.connection_manager.manager")
    async def test_full_interview_flow_no_followups(
        self,
        mock_manager,
        mock_get_session,
        interview,
        questions,
        cv_analysis,
        mock_websocket,
        mock_container,
        mock_interview_repo,
        mock_question_repo,
        mock_answer_repo,
        mock_llm,
    ):
        """Test complete interview flow: 3 questions, all good answers, no follow-ups."""
        # Setup
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_manager.send_message = AsyncMock()

        # Save entities
        await mock_interview_repo.save(interview)
        for q in questions:
            await mock_question_repo.save(q)

        # Mock LLM to return high similarity (no gaps)
        mock_llm.detect_concept_gaps = AsyncMock(return_value={
            "concepts": [],
            "keywords": [],
            "confirmed": False,
            "severity": "minor",
        })

        # Create orchestrator
        orchestrator = InterviewSessionOrchestrator(
            interview_id=interview.id,
            websocket=mock_websocket,
            container=mock_container,
        )

        # Start session - should send Q1
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_next_q:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(side_effect=[
                questions[0],  # First question
                questions[1],  # Second question
                questions[2],  # Third question
                None,          # No more questions
            ])
            mock_next_q.return_value = mock_instance

            await orchestrator.start_session()

            # Verify first question sent
            assert orchestrator.state == SessionState.QUESTIONING
            assert orchestrator.current_question_id == questions[0].id
            question_calls = [c for c in mock_manager.send_message.call_args_list
                            if c[0][1].get("type") == "question"]
            assert len(question_calls) == 1
            assert question_calls[0][0][1]["question_id"] == str(questions[0].id)

            # Answer Q1 with good answer (>80% similarity, no follow-ups)
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    # Mock answer processing
                    answer1 = Answer(
                        interview_id=interview.id,
                        question_id=questions[0].id,
                        candidate_id=interview.candidate_id,
                        text="Complete answer with base case, recursive case, and call stack",
                        is_voice=False,
                        similarity_score=0.85,
                        gaps={"concepts": [], "confirmed": False},
                    )
                    answer1.evaluate(AnswerEvaluation(
                        score=85.0,
                        semantic_similarity=0.85,
                        completeness=0.9,
                        relevance=0.95,
                        sentiment="confident",
                        reasoning="Excellent answer",
                        strengths=["Complete", "Clear"],
                        weaknesses=[],
                        improvement_suggestions=[],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer1, True))
                    mock_process.return_value = mock_process_instance

                    # Mock decision: no follow-up needed
                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": False,
                        "reason": "Similarity 0.85 >= threshold 0.8",
                        "follow_up_count": 0,
                        "cumulative_gaps": [],
                    })
                    mock_decision.return_value = mock_decision_instance

                    await orchestrator.handle_answer("Complete answer with base case, recursive case, and call stack")

                    # Should send evaluation + next question (Q2)
                    assert orchestrator.state == SessionState.QUESTIONING
                    assert orchestrator.current_question_id == questions[1].id
                    assert orchestrator.follow_up_count == 0

                    eval_calls = [c for c in mock_manager.send_message.call_args_list
                                if c[0][1].get("type") == "evaluation"]
                    question_calls = [c for c in mock_manager.send_message.call_args_list
                                    if c[0][1].get("type") == "question"]
                    assert len(eval_calls) == 1
                    assert len(question_calls) == 1
                    assert question_calls[0][0][1]["question_id"] == str(questions[1].id)

            # Answer Q2 with good answer
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    answer2 = Answer(
                        interview_id=interview.id,
                        question_id=questions[1].id,
                        candidate_id=interview.candidate_id,
                        text="Dependency injection provides dependencies externally",
                        is_voice=False,
                        similarity_score=0.82,
                        gaps={"concepts": [], "confirmed": False},
                    )
                    answer2.evaluate(AnswerEvaluation(
                        score=82.0,
                        semantic_similarity=0.82,
                        completeness=0.85,
                        relevance=0.9,
                        sentiment="confident",
                        reasoning="Good answer",
                        strengths=["Clear"],
                        weaknesses=[],
                        improvement_suggestions=[],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer2, True))
                    mock_process.return_value = mock_process_instance

                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": False,
                        "reason": "Similarity 0.82 >= threshold 0.8",
                        "follow_up_count": 0,
                        "cumulative_gaps": [],
                    })
                    mock_decision.return_value = mock_decision_instance

                    await orchestrator.handle_answer("Dependency injection provides dependencies externally")

                    # Should send evaluation + next question (Q3)
                    assert orchestrator.state == SessionState.QUESTIONING
                    assert orchestrator.current_question_id == questions[2].id

            # Answer Q3 (behavioral - no similarity check)
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    with patch("src.adapters.api.websocket.session_orchestrator.CompleteInterviewUseCase") as mock_complete:
                        answer3 = Answer(
                            interview_id=interview.id,
                            question_id=questions[2].id,
                            candidate_id=interview.candidate_id,
                            text="I worked on a challenging microservices project",
                            is_voice=False,
                            similarity_score=None,  # No ideal answer
                            gaps=None,
                        )
                        answer3.evaluate(AnswerEvaluation(
                            score=80.0,
                            semantic_similarity=None,
                            completeness=0.8,
                            relevance=0.9,
                            sentiment="confident",
                            reasoning="Good behavioral answer",
                            strengths=["Specific example"],
                            weaknesses=[],
                            improvement_suggestions=[],
                        ))

                        mock_process_instance = AsyncMock()
                        mock_process_instance.execute = AsyncMock(return_value=(answer3, False))  # No more questions
                        mock_process.return_value = mock_process_instance

                        mock_decision_instance = AsyncMock()
                        mock_decision_instance.execute = AsyncMock(return_value={
                            "needs_followup": False,
                            "reason": "No ideal answer for behavioral question",
                            "follow_up_count": 0,
                            "cumulative_gaps": [],
                        })
                        mock_decision.return_value = mock_decision_instance

                        # Mock complete interview
                        completed_interview = interview
                        completed_interview.status = InterviewStatus.COMPLETE
                        mock_complete_instance = AsyncMock()
                        # CompleteInterviewUseCase now returns tuple (Interview, dict | None)
                        mock_complete_instance.execute = AsyncMock(return_value=(completed_interview, None))
                        mock_complete.return_value = mock_complete_instance

                        await orchestrator.handle_answer("I worked on a challenging microservices project")

                        # Should send evaluation + interview_complete
                        assert orchestrator.state == SessionState.COMPLETE

                        complete_calls = [c for c in mock_manager.send_message.call_args_list
                                        if c[0][1].get("type") == "interview_complete"]
                        assert len(complete_calls) == 1
                        assert complete_calls[0][0][1]["interview_id"] == str(interview.id)

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    @patch("src.adapters.api.websocket.connection_manager.manager")
    async def test_interview_with_multiple_followups(
        self,
        mock_manager,
        mock_get_session,
        interview,
        questions,
        mock_websocket,
        mock_container,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
    ):
        """Test interview flow with multiple follow-ups (0-3 per question)."""
        # Setup
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_manager.send_message = AsyncMock()

        await mock_interview_repo.save(interview)
        await mock_question_repo.save(questions[0])

        orchestrator = InterviewSessionOrchestrator(
            interview_id=interview.id,
            websocket=mock_websocket,
            container=mock_container,
        )

        # Start session
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_next_q:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=questions[0])
            mock_next_q.return_value = mock_instance

            await orchestrator.start_session()
            assert orchestrator.state == SessionState.QUESTIONING

            # Answer with gaps -> trigger first follow-up
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    answer1 = Answer(
                        interview_id=interview.id,
                        question_id=questions[0].id,
                        candidate_id=interview.candidate_id,
                        text="Recursion is calling itself",
                        is_voice=False,
                        similarity_score=0.45,
                        gaps={
                            "concepts": ["base case", "call stack"],
                            "keywords": ["base", "stack"],
                            "confirmed": True,
                            "severity": "major",
                        },
                    )
                    answer1.evaluate(AnswerEvaluation(
                        score=55.0,
                        semantic_similarity=0.45,
                        completeness=0.4,
                        relevance=0.8,
                        sentiment="uncertain",
                        reasoning="Too brief",
                        strengths=["Correct basic definition"],
                        weaknesses=["Missing base case", "No call stack"],
                        improvement_suggestions=["Explain base case"],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer1, True))
                    mock_process.return_value = mock_process_instance

                    # Decision: follow-up needed
                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": True,
                        "reason": "2 missing concepts: base case, call stack",
                        "follow_up_count": 0,
                        "cumulative_gaps": ["base case", "call stack"],
                    })
                    mock_decision.return_value = mock_decision_instance

                    await orchestrator.handle_answer("Recursion is calling itself")

                    # Should be in FOLLOW_UP state with count=1
                    assert orchestrator.state == SessionState.FOLLOW_UP
                    assert orchestrator.follow_up_count == 1

                    # Verify follow-up question sent
                    follow_up_calls = [c for c in mock_manager.send_message.call_args_list
                                      if c[0][1].get("type") == "follow_up_question"]
                    assert len(follow_up_calls) == 1
                    assert follow_up_calls[0][0][1]["order_in_sequence"] == 1

            # Answer follow-up with still some gaps -> trigger second follow-up
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    answer2 = Answer(
                        interview_id=interview.id,
                        question_id=uuid4(),  # Follow-up question ID
                        candidate_id=interview.candidate_id,
                        text="Base case stops recursion",
                        is_voice=False,
                        similarity_score=0.60,
                        gaps={
                            "concepts": ["call stack"],
                            "keywords": ["stack"],
                            "confirmed": True,
                            "severity": "moderate",
                        },
                    )
                    answer2.evaluate(AnswerEvaluation(
                        score=65.0,
                        semantic_similarity=0.60,
                        completeness=0.6,
                        relevance=0.85,
                        sentiment="somewhat confident",
                        reasoning="Better but still incomplete",
                        strengths=["Explained base case"],
                        weaknesses=["Still missing call stack"],
                        improvement_suggestions=["Explain call stack"],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer2, True))
                    mock_process.return_value = mock_process_instance

                    # Decision: another follow-up needed
                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": True,
                        "reason": "1 remaining concept: call stack",
                        "follow_up_count": 1,
                        "cumulative_gaps": ["call stack"],
                    })
                    mock_decision.return_value = mock_decision_instance

                    await orchestrator.handle_answer("Base case stops recursion")

                    # Should still be in FOLLOW_UP with count=2
                    assert orchestrator.state == SessionState.FOLLOW_UP
                    assert orchestrator.follow_up_count == 2

                    # Verify second follow-up sent
                    follow_up_calls = [c for c in mock_manager.send_message.call_args_list
                                      if c[0][1].get("type") == "follow_up_question"]
                    assert len(follow_up_calls) == 1
                    assert follow_up_calls[0][0][1]["order_in_sequence"] == 2

            # Answer second follow-up with complete answer -> move to next question
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    answer3 = Answer(
                        interview_id=interview.id,
                        question_id=uuid4(),
                        candidate_id=interview.candidate_id,
                        text="Call stack tracks each recursive call",
                        is_voice=False,
                        similarity_score=0.85,
                        gaps={"concepts": [], "confirmed": False},
                    )
                    answer3.evaluate(AnswerEvaluation(
                        score=85.0,
                        semantic_similarity=0.85,
                        completeness=0.9,
                        relevance=0.95,
                        sentiment="confident",
                        reasoning="Complete answer",
                        strengths=["Complete explanation"],
                        weaknesses=[],
                        improvement_suggestions=[],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer3, True))
                    mock_process.return_value = mock_process_instance

                    # Decision: no more follow-ups
                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": False,
                        "reason": "Similarity 0.85 >= threshold 0.8",
                        "follow_up_count": 2,
                        "cumulative_gaps": [],
                    })
                    mock_decision.return_value = mock_decision_instance

                    # Mock next question
                    mock_instance.execute = AsyncMock(return_value=questions[1])

                    await orchestrator.handle_answer("Call stack tracks each recursive call")

                    # Should move to next main question
                    assert orchestrator.state == SessionState.QUESTIONING
                    assert orchestrator.follow_up_count == 0  # Reset for next question
                    assert orchestrator.current_question_id == questions[1].id

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    @patch("src.adapters.api.websocket.connection_manager.manager")
    async def test_max_3_followups_enforced_across_sequence(
        self,
        mock_manager,
        mock_get_session,
        interview,
        questions,
        mock_websocket,
        mock_container,
        mock_interview_repo,
        mock_question_repo,
    ):
        """Test that max 3 follow-ups enforced even if gaps persist."""
        # Setup
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_manager.send_message = AsyncMock()

        await mock_interview_repo.save(interview)
        await mock_question_repo.save(questions[0])

        orchestrator = InterviewSessionOrchestrator(
            interview_id=interview.id,
            websocket=mock_websocket,
            container=mock_container,
        )

        # Start session
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_next_q:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=questions[0])
            mock_next_q.return_value = mock_instance

            await orchestrator.start_session()

            # Generate 3 follow-ups with persistent gaps
            for i in range(3):
                mock_manager.reset_mock()
                with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                    with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                        answer = Answer(
                            interview_id=interview.id,
                            question_id=uuid4(),
                            candidate_id=interview.candidate_id,
                            text=f"Incomplete answer {i+1}",
                            is_voice=False,
                            similarity_score=0.50,
                            gaps={
                                "concepts": ["concept1", "concept2"],
                                "confirmed": True,
                                "severity": "major",
                            },
                        )
                        answer.evaluate(AnswerEvaluation(
                            score=55.0,
                            semantic_similarity=0.50,
                            completeness=0.5,
                            relevance=0.8,
                            sentiment="uncertain",
                            reasoning="Still incomplete",
                            strengths=[],
                            weaknesses=["Missing concepts"],
                            improvement_suggestions=["Provide more detail"],
                        ))

                        mock_process_instance = AsyncMock()
                        mock_process_instance.execute = AsyncMock(return_value=(answer, True))
                        mock_process.return_value = mock_process_instance

                        # Decision: follow-up needed for first 3 iterations
                        if i < 3:
                            mock_decision_instance = AsyncMock()
                            mock_decision_instance.execute = AsyncMock(return_value={
                                "needs_followup": True,
                                "reason": f"Gaps persist: iteration {i+1}",
                                "follow_up_count": i,
                                "cumulative_gaps": ["concept1", "concept2"],
                            })
                            mock_decision.return_value = mock_decision_instance

                        await orchestrator.handle_answer(f"Incomplete answer {i+1}")

                        if i < 3:
                            assert orchestrator.state == SessionState.FOLLOW_UP
                            assert orchestrator.follow_up_count == i + 1

            # After 3 follow-ups, the 4th answer should NOT generate another follow-up
            # (even with gaps) and should move to next question
            mock_manager.reset_mock()
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    answer_final = Answer(
                        interview_id=interview.id,
                        question_id=uuid4(),
                        candidate_id=interview.candidate_id,
                        text="Still incomplete answer 4",
                        is_voice=False,
                        similarity_score=0.50,
                        gaps={
                            "concepts": ["concept1"],
                            "confirmed": True,
                            "severity": "moderate",
                        },
                    )
                    answer_final.evaluate(AnswerEvaluation(
                        score=55.0,
                        semantic_similarity=0.50,
                        completeness=0.5,
                        relevance=0.8,
                        sentiment="uncertain",
                        reasoning="Still incomplete after 3 follow-ups",
                        strengths=[],
                        weaknesses=["Missing concepts"],
                        improvement_suggestions=["Provide more detail"],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer_final, True))
                    mock_process.return_value = mock_process_instance

                    # Decision: NO follow-up (max reached)
                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": False,
                        "reason": "Max follow-ups (3) reached",
                        "follow_up_count": 3,
                        "cumulative_gaps": ["concept1"],
                    })
                    mock_decision.return_value = mock_decision_instance

                    # Mock next question
                    mock_instance.execute = AsyncMock(return_value=questions[1])

                    await orchestrator.handle_answer("Still incomplete answer 4")

                    # Should move to next main question despite gaps
                    assert orchestrator.state == SessionState.QUESTIONING
                    assert orchestrator.follow_up_count == 0  # Reset
                    assert orchestrator.current_question_id == questions[1].id

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    @patch("src.adapters.api.websocket.connection_manager.manager")
    async def test_state_persistence_across_messages(
        self,
        mock_manager,
        mock_get_session,
        interview,
        questions,
        mock_websocket,
        mock_container,
        mock_interview_repo,
        mock_question_repo,
    ):
        """Test session state persists correctly across multiple messages."""
        # Setup
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_manager.send_message = AsyncMock()

        await mock_interview_repo.save(interview)
        for q in questions:
            await mock_question_repo.save(q)

        orchestrator = InterviewSessionOrchestrator(
            interview_id=interview.id,
            websocket=mock_websocket,
            container=mock_container,
        )

        # Verify initial state
        state1 = orchestrator.get_state()
        assert state1["state"] == SessionState.IDLE
        assert state1["current_question_id"] is None
        assert state1["follow_up_count"] == 0

        # Start session
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_next_q:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=questions[0])
            mock_next_q.return_value = mock_instance

            await orchestrator.start_session()

            # Verify state after start
            state2 = orchestrator.get_state()
            assert state2["state"] == SessionState.QUESTIONING
            assert state2["current_question_id"] == str(questions[0].id)
            assert state2["parent_question_id"] == str(questions[0].id)
            assert state2["follow_up_count"] == 0

            # Process answer
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    answer = Answer(
                        interview_id=interview.id,
                        question_id=questions[0].id,
                        candidate_id=interview.candidate_id,
                        text="Good answer",
                        is_voice=False,
                        similarity_score=0.85,
                        gaps={"concepts": [], "confirmed": False},
                    )
                    answer.evaluate(AnswerEvaluation(
                        score=85.0,
                        semantic_similarity=0.85,
                        completeness=0.9,
                        relevance=0.95,
                        sentiment="confident",
                        reasoning="Excellent",
                        strengths=["Complete"],
                        weaknesses=[],
                        improvement_suggestions=[],
                    ))

                    mock_process_instance = AsyncMock()
                    mock_process_instance.execute = AsyncMock(return_value=(answer, True))
                    mock_process.return_value = mock_process_instance

                    mock_decision_instance = AsyncMock()
                    mock_decision_instance.execute = AsyncMock(return_value={
                        "needs_followup": False,
                        "reason": "Good answer",
                        "follow_up_count": 0,
                        "cumulative_gaps": [],
                    })
                    mock_decision.return_value = mock_decision_instance

                    mock_instance.execute = AsyncMock(return_value=questions[1])

                    await orchestrator.handle_answer("Good answer")

                    # Verify state after answer
                    state3 = orchestrator.get_state()
                    assert state3["state"] == SessionState.QUESTIONING
                    assert state3["current_question_id"] == str(questions[1].id)
                    assert state3["parent_question_id"] == str(questions[1].id)
                    assert state3["follow_up_count"] == 0

                    # Verify timestamps updated
                    assert state3["last_activity"] > state2["last_activity"]


class TestInterviewCompletion:
    """Test interview completion flow."""

    @pytest.mark.asyncio
    @patch("src.adapters.api.websocket.session_orchestrator.get_async_session")
    @patch("src.adapters.api.websocket.connection_manager.manager")
    async def test_interview_completion_flow(
        self,
        mock_manager,
        mock_get_session,
        interview,
        questions,
        mock_websocket,
        mock_container,
        mock_interview_repo,
        mock_question_repo,
        mock_answer_repo,
    ):
        """Test complete interview completion with overall score calculation."""
        # Setup
        mock_session = AsyncMock()
        async def async_gen():
            yield mock_session
        mock_get_session.return_value = async_gen()

        mock_manager.send_message = AsyncMock()

        await mock_interview_repo.save(interview)
        await mock_question_repo.save(questions[0])

        # Add some answers to calculate average score
        answers = [
            Answer(
                interview_id=interview.id,
                question_id=questions[0].id,
                candidate_id=interview.candidate_id,
                text="Answer 1",
                is_voice=False,
            ),
            Answer(
                interview_id=interview.id,
                question_id=questions[1].id,
                candidate_id=interview.candidate_id,
                text="Answer 2",
                is_voice=False,
            ),
        ]
        answers[0].evaluate(AnswerEvaluation(
            score=85.0,
            semantic_similarity=0.85,
            completeness=0.9,
            relevance=0.95,
            sentiment="confident",
            reasoning="Good",
            strengths=["Clear"],
            weaknesses=[],
            improvement_suggestions=[],
        ))
        answers[1].evaluate(AnswerEvaluation(
            score=75.0,
            semantic_similarity=0.75,
            completeness=0.8,
            relevance=0.9,
            sentiment="confident",
            reasoning="Good",
            strengths=["Relevant"],
            weaknesses=[],
            improvement_suggestions=[],
        ))

        for ans in answers:
            await mock_answer_repo.save(ans)

        orchestrator = InterviewSessionOrchestrator(
            interview_id=interview.id,
            websocket=mock_websocket,
            container=mock_container,
        )

        # Start and answer question
        with patch("src.adapters.api.websocket.session_orchestrator.GetNextQuestionUseCase") as mock_next_q:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(side_effect=[questions[0], None])  # No more questions
            mock_next_q.return_value = mock_instance

            await orchestrator.start_session()

            # Answer last question
            with patch("src.adapters.api.websocket.session_orchestrator.ProcessAnswerAdaptiveUseCase") as mock_process:
                with patch("src.adapters.api.websocket.session_orchestrator.FollowUpDecisionUseCase") as mock_decision:
                    with patch("src.adapters.api.websocket.session_orchestrator.CompleteInterviewUseCase") as mock_complete:
                        answer = Answer(
                            interview_id=interview.id,
                            question_id=questions[0].id,
                            candidate_id=interview.candidate_id,
                            text="Final answer",
                            is_voice=False,
                            similarity_score=0.80,
                            gaps={"concepts": [], "confirmed": False},
                        )
                        answer.evaluate(AnswerEvaluation(
                            score=80.0,
                            semantic_similarity=0.80,
                            completeness=0.85,
                            relevance=0.9,
                            sentiment="confident",
                            reasoning="Good",
                            strengths=["Complete"],
                            weaknesses=[],
                            improvement_suggestions=[],
                        ))

                        mock_process_instance = AsyncMock()
                        mock_process_instance.execute = AsyncMock(return_value=(answer, False))  # No more questions
                        mock_process.return_value = mock_process_instance

                        mock_decision_instance = AsyncMock()
                        mock_decision_instance.execute = AsyncMock(return_value={
                            "needs_followup": False,
                            "reason": "Good answer",
                            "follow_up_count": 0,
                            "cumulative_gaps": [],
                        })
                        mock_decision.return_value = mock_decision_instance

                        # Mock complete interview
                        completed_interview = interview
                        completed_interview.status = InterviewStatus.COMPLETE
                        mock_complete_instance = AsyncMock()
                        # CompleteInterviewUseCase now returns tuple (Interview, dict | None)
                        mock_complete_instance.execute = AsyncMock(return_value=(completed_interview, None))
                        mock_complete.return_value = mock_complete_instance

                        await orchestrator.handle_answer("Final answer")

                        # Verify completion
                        assert orchestrator.state == SessionState.COMPLETE

                        # Verify completion message sent with overall score
                        complete_calls = [c for c in mock_manager.send_message.call_args_list
                                        if c[0][1].get("type") == "interview_complete"]
                        assert len(complete_calls) == 1
                        complete_msg = complete_calls[0][0][1]
                        assert complete_msg["interview_id"] == str(interview.id)
                        assert "overall_score" in complete_msg
                        assert complete_msg["overall_score"] > 0  # Average of answers
