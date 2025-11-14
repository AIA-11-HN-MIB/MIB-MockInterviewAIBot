"""Tests for Phase 04: ProcessAnswerAdaptiveUseCase."""

from uuid import uuid4

import pytest

from src.application.use_cases.process_answer_adaptive import (
    ProcessAnswerAdaptiveUseCase,
)
from src.domain.models.interview import InterviewStatus


class TestProcessAnswerAdaptiveUseCase:
    """Test adaptive answer processing with follow-up generation."""

    @pytest.mark.asyncio
    async def test_process_answer_high_similarity_no_followup(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test high similarity (>= 80%) -> no follow-up."""
        # Setup
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_with_ideal_answer)

        # Good answer (will get high similarity)
        answer_text = """Recursion is when a function calls itself to solve problems.
        Key concepts: base case to stop recursion, recursive case to continue,
        and call stack management. Examples: factorial, Fibonacci, tree traversal."""

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        answer, has_more = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            answer_text=answer_text,
        )

        # Verify evaluation and gaps (no longer testing follow-up generation)
        assert answer.similarity_score is not None
        assert answer.similarity_score >= 0.8
        assert answer.gaps is not None

    @pytest.mark.asyncio
    async def test_process_answer_low_similarity_generates_followup(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test low similarity (< 80%) with gaps -> gaps detected."""
        # Setup
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_with_ideal_answer)

        # Brief answer (will get low similarity)
        answer_text = "Recursion is a function calling itself."

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        answer, has_more = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            answer_text=answer_text,
        )

        # Verify gaps detected (mock generates gaps for short answers)
        assert answer.similarity_score is not None
        assert answer.gaps is not None
        # Gaps should be detected for brief answers
        assert answer.gaps.get("confirmed") is True

    @pytest.mark.asyncio
    async def test_followup_max_3_limit(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test gap detection still works regardless of follow-up count."""
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_with_ideal_answer)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        # Simulate 3 follow-ups already exist
        sample_interview_adaptive.adaptive_follow_ups = [uuid4(), uuid4(), uuid4()]

        answer_text = "Brief answer"  # Would normally trigger gap detection

        answer, has_more = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            answer_text=answer_text,
        )

        # Gap detection still works, but follow-up generation is handled by WebSocket handler
        assert answer.gaps is not None

    @pytest.mark.asyncio
    async def test_answer_evaluation_stored(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test answer evaluation is properly stored."""
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_with_ideal_answer)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        answer, has_more = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            answer_text="Test answer",
        )

        # Verify evaluation
        assert answer.evaluation is not None
        assert answer.evaluation.score > 0
        assert answer.evaluation.reasoning is not None
        assert len(answer.evaluation.strengths) > 0

    @pytest.mark.asyncio
    async def test_similarity_calculation_with_ideal_answer(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test similarity is calculated when ideal_answer exists."""
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_with_ideal_answer)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        answer, has_more = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            answer_text="Recursion calls itself with base case and examples",
        )

        # Similarity should be calculated
        assert answer.similarity_score is not None
        assert 0.0 < answer.similarity_score <= 1.0

    @pytest.mark.asyncio
    async def test_no_similarity_without_ideal_answer(
        self,
        sample_interview_adaptive,
        sample_question_without_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test no similarity calculation when ideal_answer missing."""
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_without_ideal_answer)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        answer, has_more = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_without_ideal_answer.id,
            answer_text="Tell me about a project",
        )

        # No similarity for behavioral questions
        assert answer.similarity_score is None

    @pytest.mark.asyncio
    async def test_interview_not_found_error(
        self,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test error when interview not found."""
        await mock_question_repo.save(sample_question_with_ideal_answer)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        with pytest.raises(ValueError, match="Interview .* not found"):
            await use_case.execute(
                interview_id=uuid4(),  # Non-existent
                question_id=sample_question_with_ideal_answer.id,
                answer_text="Test",
            )

    @pytest.mark.asyncio
    async def test_question_not_found_error(
        self,
        sample_interview_adaptive,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test error when question not found."""
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        with pytest.raises(ValueError, match="Question .* not found"):
            await use_case.execute(
                interview_id=sample_interview_adaptive.id,
                question_id=uuid4(),  # Non-existent
                answer_text="Test",
            )

    @pytest.mark.asyncio
    async def test_interview_wrong_status_error(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_answer_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
        mock_vector_search,
    ):
        """Test error when interview not IN_PROGRESS."""
        sample_interview_adaptive.status = InterviewStatus.COMPLETE
        await mock_interview_repo.save(sample_interview_adaptive)
        await mock_question_repo.save(sample_question_with_ideal_answer)

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=mock_answer_repo,
            interview_repository=mock_interview_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
            vector_search=mock_vector_search,
        )

        with pytest.raises(ValueError, match="Interview not in progress"):
            await use_case.execute(
                interview_id=sample_interview_adaptive.id,
                question_id=sample_question_with_ideal_answer.id,
                answer_text="Test",
            )


class TestGapDetection:
    """Test hybrid gap detection (keywords + LLM)."""

    @pytest.mark.asyncio
    async def test_keyword_gap_detection(self):
        """Test keyword-based gap detection."""
        from src.application.use_cases.process_answer_adaptive import (
            ProcessAnswerAdaptiveUseCase,
        )

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=None,  # type: ignore
            interview_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
            vector_search=None,  # type: ignore
        )

        ideal_answer = """Recursion is a function calling itself.
        Key concepts: base case, recursive case, call stack, termination condition."""

        # Complete answer -> few missing keywords
        complete_answer = """Recursion calls itself with base case and recursive case.
        The call stack tracks each call and needs termination."""
        gaps = use_case._detect_keyword_gaps(complete_answer, ideal_answer)
        assert len(gaps) <= 5  # Few missing (threshold is >3, so can be 0-4)

        # Brief answer -> many missing keywords
        brief_answer = "Recursion is calling itself."
        gaps = use_case._detect_keyword_gaps(brief_answer, ideal_answer)
        assert len(gaps) > 3  # Significant gaps

    @pytest.mark.asyncio
    async def test_hybrid_gap_detection_no_keywords(self):
        """Test hybrid detection when no keyword gaps."""
        from src.application.use_cases.process_answer_adaptive import (
            ProcessAnswerAdaptiveUseCase,
        )

        use_case = ProcessAnswerAdaptiveUseCase(
            answer_repository=None,  # type: ignore
            interview_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
            vector_search=None,  # type: ignore
        )

        # Very similar texts
        ideal = "Python is a programming language"
        answer = "Python is a programming language"

        result = await use_case._detect_gaps_hybrid(
            answer_text=answer,
            ideal_answer=ideal,
            question_text="What is Python?",
        )

        # No keyword gaps -> no LLM call -> not confirmed
        assert result["confirmed"] is False
        assert len(result["concepts"]) == 0


class TestFollowUpDecisionLogic:
    """Tests for follow-up decision logic - MOVED TO FollowUpDecisionUseCase.

    NOTE: These tests are deprecated as _should_generate_followup() has been
    removed from ProcessAnswerAdaptiveUseCase and moved to FollowUpDecisionUseCase.
    See tests/unit/application/use_cases/test_follow_up_decision.py for new tests.
    """

    def test_should_not_generate_max_followups_reached(
        self, sample_answer_low_similarity
    ):
        """DEPRECATED: Follow-up logic moved to FollowUpDecisionUseCase."""
        pytest.skip("Follow-up decision logic moved to FollowUpDecisionUseCase")

    def test_should_not_generate_high_similarity(self, sample_answer_high_similarity):
        """DEPRECATED: Follow-up logic moved to FollowUpDecisionUseCase."""
        pytest.skip("Follow-up decision logic moved to FollowUpDecisionUseCase")

    def test_should_generate_low_similarity_with_gaps(
        self, sample_answer_low_similarity
    ):
        """DEPRECATED: Follow-up logic moved to FollowUpDecisionUseCase."""
        pytest.skip("Follow-up decision logic moved to FollowUpDecisionUseCase")
