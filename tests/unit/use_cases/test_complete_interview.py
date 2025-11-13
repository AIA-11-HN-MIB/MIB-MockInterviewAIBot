"""Tests for Phase 06: CompleteInterviewUseCase."""

from uuid import uuid4

import pytest

from src.application.use_cases.complete_interview import CompleteInterviewUseCase
from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.interview import InterviewStatus


class TestCompleteInterviewUseCase:
    """Test interview completion with summary generation."""

    @pytest.mark.asyncio
    async def test_complete_interview_with_summary_generation(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test complete interview with summary generation enabled."""
        # Setup interview
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create question and answer
        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Good answer",
            is_voice=False,
            similarity_score=0.85,
            gaps={"concepts": [], "keywords": [], "confirmed": False},
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=85.0,
                semantic_similarity=0.85,
                completeness=0.9,
                relevance=0.95,
                sentiment="confident",
                reasoning="Strong",
                strengths=["Good"],
                weaknesses=[],
                improvement_suggestions=[],
            )
        )
        await mock_answer_repo.save(answer1)

        # Execute use case with all dependencies
        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        interview, summary = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=True,
        )

        # Verify interview completed
        assert interview.status == InterviewStatus.COMPLETE

        # Verify summary generated
        assert summary is not None
        assert summary["interview_id"] == str(sample_interview_adaptive.id)
        assert "overall_score" in summary
        assert "strengths" in summary

        # Verify summary stored in metadata
        assert interview.plan_metadata is not None
        assert "completion_summary" in interview.plan_metadata
        assert interview.plan_metadata["completion_summary"] == summary

    @pytest.mark.asyncio
    async def test_complete_interview_without_summary_generation(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
    ):
        """Test complete interview with summary generation disabled."""
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
        )

        interview, summary = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=False,
        )

        # Verify interview completed
        assert interview.status == InterviewStatus.COMPLETE

        # Verify no summary generated
        assert summary is None

    @pytest.mark.asyncio
    async def test_complete_interview_missing_dependencies(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
        mock_answer_repo,
    ):
        """Test complete interview with missing dependencies -> no summary."""
        await mock_interview_repo.save(sample_interview_adaptive)

        # Missing question_repo, follow_up_repo, llm
        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=None,
            follow_up_question_repository=None,
            llm=None,
        )

        interview, summary = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=True,  # Requested but will be skipped
        )

        # Verify interview completed
        assert interview.status == InterviewStatus.COMPLETE

        # Verify no summary generated (missing dependencies)
        assert summary is None

    @pytest.mark.asyncio
    async def test_complete_interview_not_found(
        self,
        mock_interview_repo,
    ):
        """Test error when interview not found."""
        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
        )

        with pytest.raises(ValueError, match="Interview .* not found"):
            await use_case.execute(interview_id=uuid4())

    @pytest.mark.asyncio
    async def test_complete_interview_invalid_status(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
    ):
        """Test error when interview not IN_PROGRESS."""
        # Set status to COMPLETED
        sample_interview_adaptive.status = InterviewStatus.COMPLETE
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
        )

        with pytest.raises(ValueError, match="Cannot complete interview with status"):
            await use_case.execute(interview_id=sample_interview_adaptive.id)

    @pytest.mark.asyncio
    async def test_complete_interview_ready_status_invalid(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
    ):
        """Test error when interview status is READY (not started)."""
        # Set status to READY
        sample_interview_adaptive.status = InterviewStatus.IDLE
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
        )

        with pytest.raises(ValueError, match="Cannot complete interview with status"):
            await use_case.execute(interview_id=sample_interview_adaptive.id)

    @pytest.mark.asyncio
    async def test_complete_interview_initializes_metadata(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test plan_metadata initialized if None before storing summary."""
        # Setup interview with None metadata
        sample_interview_adaptive.plan_metadata = None
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create minimal data for summary
        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer",
            is_voice=False,
            similarity_score=0.8,
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=80.0,
                semantic_similarity=0.8,
                completeness=0.85,
                relevance=0.9,
                sentiment="confident",
                reasoning="Good",
                strengths=["Clear"],
                weaknesses=[],
                improvement_suggestions=[],
            )
        )
        await mock_answer_repo.save(answer1)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        interview, summary = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=True,
        )

        # Verify metadata initialized
        assert interview.plan_metadata is not None
        assert "completion_summary" in interview.plan_metadata

    @pytest.mark.asyncio
    async def test_complete_interview_preserves_existing_metadata(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test existing plan_metadata preserved when adding summary."""
        # Setup interview with existing metadata
        sample_interview_adaptive.plan_metadata = {
            "n": 3,
            "strategy": "adaptive_planning_v1",
            "custom_field": "preserved",
        }
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create minimal data
        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer",
            is_voice=False,
            similarity_score=0.8,
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=80.0,
                semantic_similarity=0.8,
                completeness=0.85,
                relevance=0.9,
                sentiment="confident",
                reasoning="Good",
                strengths=["Clear"],
                weaknesses=[],
                improvement_suggestions=[],
            )
        )
        await mock_answer_repo.save(answer1)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        interview, summary = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=True,
        )

        # Verify existing metadata preserved
        assert interview.plan_metadata["n"] == 3
        assert interview.plan_metadata["strategy"] == "adaptive_planning_v1"
        assert interview.plan_metadata["custom_field"] == "preserved"
        assert "completion_summary" in interview.plan_metadata

    @pytest.mark.asyncio
    async def test_complete_interview_returns_tuple(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
    ):
        """Test return value is tuple (Interview, dict | None)."""
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
        )

        result = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=False,
        )

        # Verify tuple structure
        assert isinstance(result, tuple)
        assert len(result) == 2
        interview, summary = result
        assert interview is not None
        assert summary is None


class TestCompleteInterviewIntegration:
    """Integration tests for complete interview with summary."""

    @pytest.mark.asyncio
    async def test_complete_flow_with_multiple_answers(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test complete flow with multiple evaluated answers."""
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create 3 questions
        q1_id = sample_interview_adaptive.question_ids[0]
        q2_id = sample_interview_adaptive.question_ids[1]
        q3_id = sample_interview_adaptive.question_ids[2]

        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        q2 = sample_question_with_ideal_answer
        q2.id = q2_id
        await mock_question_repo.save(q2)

        q3 = sample_question_with_ideal_answer
        q3.id = q3_id
        await mock_question_repo.save(q3)

        # Create 3 evaluated answers
        for q_id in [q1_id, q2_id, q3_id]:
            answer = Answer(
                interview_id=sample_interview_adaptive.id,
                question_id=q_id,
                candidate_id=sample_interview_adaptive.candidate_id,
                text="Good answer",
                is_voice=False,
                similarity_score=0.85,
            )
            answer.evaluate(
                AnswerEvaluation(
                    score=85.0,
                    semantic_similarity=0.85,
                    completeness=0.9,
                    relevance=0.95,
                    sentiment="confident",
                    reasoning="Strong",
                    strengths=["Good"],
                    weaknesses=[],
                    improvement_suggestions=[],
                )
            )
            await mock_answer_repo.save(answer)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        interview, summary = await use_case.execute(
            interview_id=sample_interview_adaptive.id,
            generate_summary=True,
        )

        # Verify complete flow
        assert interview.status == InterviewStatus.COMPLETE
        assert summary is not None
        assert summary["total_questions"] == 3
        assert summary["overall_score"] > 0.0
        assert len(summary["question_summaries"]) == 3
