"""Tests for CompleteInterviewUseCase (refactored - atomic operation)."""

from uuid import uuid4

import pytest

from src.application.dto.interview_completion_dto import InterviewCompletionResult
from src.application.use_cases.complete_interview import CompleteInterviewUseCase
from src.domain.models.answer import Answer
from src.domain.models.evaluation import Evaluation
from src.domain.models.interview import InterviewStatus


class TestCompleteInterviewUseCase:
    """Test interview completion with summary generation (atomic operation)."""

    @pytest.mark.asyncio
    async def test_complete_interview_generates_summary(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test complete interview always generates summary (atomic operation)."""
        # Setup interview in EVALUATING status
        sample_interview_adaptive.status = InterviewStatus.EVALUATING
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create question
        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        # Create answer
        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Good answer about recursion",
            is_voice=False,
        )
        await mock_answer_repo.save(answer1)

        # Create evaluation (NEW: separate entity)
        evaluation1 = Evaluation(
            answer_id=answer1.id,
            question_id=q1_id,
            interview_id=sample_interview_adaptive.id,
            raw_score=85.0,
            final_score=85.0,
            completeness=0.9,
            relevance=0.95,
            sentiment="confident",
            reasoning="Strong answer",
            strengths=["Clear explanation"],
            weaknesses=[],
        )
        await mock_evaluation_repo.save(evaluation1)

        # Link evaluation to answer
        answer1.evaluation_id = evaluation1.id
        await mock_answer_repo.save(answer1)

        # Execute use case (NEW: all dependencies required)
        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        # NEW: Returns InterviewCompletionResult DTO
        result = await use_case.execute(interview_id=sample_interview_adaptive.id)

        # Verify return type
        assert isinstance(result, InterviewCompletionResult)
        assert result.interview.status == InterviewStatus.COMPLETE
        assert result.summary is not None  # Always present

        # Verify summary structure
        assert result.summary["interview_id"] == str(sample_interview_adaptive.id)
        assert "overall_score" in result.summary
        assert "strengths" in result.summary
        assert "weaknesses" in result.summary
        assert "total_questions" in result.summary

        # Verify summary stored in metadata
        assert result.interview.plan_metadata is not None
        assert "completion_summary" in result.interview.plan_metadata
        assert result.interview.plan_metadata["completion_summary"] == result.summary

    @pytest.mark.asyncio
    async def test_complete_interview_not_found(
        self,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test error when interview not found."""
        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        with pytest.raises(ValueError, match="Interview .* not found"):
            await use_case.execute(interview_id=uuid4())

    @pytest.mark.asyncio
    async def test_complete_interview_invalid_status(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test error when interview not in EVALUATING status."""
        # Set status to QUESTIONING (invalid for completion)
        sample_interview_adaptive.status = InterviewStatus.QUESTIONING
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        with pytest.raises(ValueError, match="Cannot complete interview with status"):
            await use_case.execute(interview_id=sample_interview_adaptive.id)

    @pytest.mark.asyncio
    async def test_complete_interview_with_multiple_evaluations(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test complete with multiple evaluated answers."""
        sample_interview_adaptive.status = InterviewStatus.EVALUATING
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create 3 questions and answers
        for idx, q_id in enumerate(sample_interview_adaptive.question_ids):
            question = sample_question_with_ideal_answer
            question.id = q_id
            await mock_question_repo.save(question)

            answer = Answer(
                interview_id=sample_interview_adaptive.id,
                question_id=q_id,
                candidate_id=sample_interview_adaptive.candidate_id,
                text=f"Answer {idx + 1}",
                is_voice=False,
            )
            await mock_answer_repo.save(answer)

            evaluation = Evaluation(
                answer_id=answer.id,
                question_id=q_id,
                interview_id=sample_interview_adaptive.id,
                raw_score=80.0 + (idx * 5),
                final_score=80.0 + (idx * 5),
                completeness=0.8,
                relevance=0.9,
                sentiment="confident",
                reasoning=f"Good answer {idx + 1}",
                strengths=[f"Strength {idx + 1}"],
                weaknesses=[],
            )
            await mock_evaluation_repo.save(evaluation)

            answer.evaluation_id = evaluation.id
            await mock_answer_repo.save(answer)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        result = await use_case.execute(interview_id=sample_interview_adaptive.id)

        assert result.interview.status == InterviewStatus.COMPLETE
        assert result.summary["total_questions"] == 3
        assert result.summary["overall_score"] > 0.0
        assert len(result.summary["question_summaries"]) == 3

    @pytest.mark.asyncio
    async def test_complete_interview_initializes_metadata_if_none(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test plan_metadata initialized if None before storing summary."""
        sample_interview_adaptive.status = InterviewStatus.EVALUATING
        sample_interview_adaptive.plan_metadata = None  # Force None
        await mock_interview_repo.save(sample_interview_adaptive)

        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer",
            is_voice=False,
        )
        await mock_answer_repo.save(answer)

        evaluation = Evaluation(
            answer_id=answer.id,
            question_id=q1_id,
            interview_id=sample_interview_adaptive.id,
            raw_score=75.0,
            final_score=75.0,
            completeness=0.8,
            relevance=0.85,
        )
        await mock_evaluation_repo.save(evaluation)

        answer.evaluation_id = evaluation.id
        await mock_answer_repo.save(answer)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        result = await use_case.execute(interview_id=sample_interview_adaptive.id)

        # Verify metadata initialized
        assert result.interview.plan_metadata is not None
        assert "completion_summary" in result.interview.plan_metadata

    @pytest.mark.asyncio
    async def test_complete_interview_preserves_existing_metadata(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test existing plan_metadata preserved when adding summary."""
        sample_interview_adaptive.status = InterviewStatus.EVALUATING
        sample_interview_adaptive.plan_metadata = {
            "n": 3,
            "strategy": "adaptive_planning_v1",
            "custom_field": "preserved",
        }
        await mock_interview_repo.save(sample_interview_adaptive)

        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer",
            is_voice=False,
        )
        await mock_answer_repo.save(answer)

        evaluation = Evaluation(
            answer_id=answer.id,
            question_id=q1_id,
            interview_id=sample_interview_adaptive.id,
            raw_score=75.0,
            final_score=75.0,
            completeness=0.8,
            relevance=0.85,
        )
        await mock_evaluation_repo.save(evaluation)

        answer.evaluation_id = evaluation.id
        await mock_answer_repo.save(answer)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        result = await use_case.execute(interview_id=sample_interview_adaptive.id)

        # Verify existing metadata preserved
        assert result.interview.plan_metadata["n"] == 3
        assert result.interview.plan_metadata["strategy"] == "adaptive_planning_v1"
        assert result.interview.plan_metadata["custom_field"] == "preserved"
        assert "completion_summary" in result.interview.plan_metadata

    @pytest.mark.asyncio
    async def test_complete_interview_returns_dto_not_tuple(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_evaluation_repo,
        mock_llm,
    ):
        """Test return value is InterviewCompletionResult DTO, not tuple."""
        sample_interview_adaptive.status = InterviewStatus.EVALUATING
        await mock_interview_repo.save(sample_interview_adaptive)

        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer",
            is_voice=False,
        )
        await mock_answer_repo.save(answer)

        evaluation = Evaluation(
            answer_id=answer.id,
            question_id=q1_id,
            interview_id=sample_interview_adaptive.id,
            raw_score=75.0,
            final_score=75.0,
            completeness=0.8,
            relevance=0.85,
        )
        await mock_evaluation_repo.save(evaluation)

        answer.evaluation_id = evaluation.id
        await mock_answer_repo.save(answer)

        use_case = CompleteInterviewUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            evaluation_repository=mock_evaluation_repo,
            llm=mock_llm,
        )

        result = await use_case.execute(interview_id=sample_interview_adaptive.id)

        # Verify DTO structure (NOT tuple)
        assert isinstance(result, InterviewCompletionResult)
        assert hasattr(result, "interview")
        assert hasattr(result, "summary")
        assert result.interview is not None
        assert result.summary is not None  # Always present
