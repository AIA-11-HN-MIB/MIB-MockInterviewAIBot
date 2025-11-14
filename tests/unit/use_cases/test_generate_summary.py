"""Tests for Phase 06: GenerateSummaryUseCase."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.application.use_cases.generate_summary import GenerateSummaryUseCase
from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.follow_up_question import FollowUpQuestion


class TestGenerateSummaryUseCase:
    """Test comprehensive interview summary generation."""

    @pytest.mark.asyncio
    async def test_generate_summary_happy_path(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test happy path with 3 main questions, 2 evaluated answers, 1 with follow-up."""
        # Setup interview
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create 3 main questions
        q1_id = sample_interview_adaptive.question_ids[0]
        q2_id = sample_interview_adaptive.question_ids[1]
        q3_id = sample_interview_adaptive.question_ids[2]

        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        q2 = sample_question_with_ideal_answer
        q2.id = q2_id
        q2.text = "Explain async/await in Python"
        await mock_question_repo.save(q2)

        q3 = sample_question_with_ideal_answer
        q3.id = q3_id
        q3.text = "What are Python decorators?"
        await mock_question_repo.save(q3)

        # Create 2 evaluated main answers
        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Recursion is when a function calls itself.",
            is_voice=True,
            similarity_score=0.65,
            gaps={"concepts": ["base case", "call stack"], "keywords": ["base"], "confirmed": True},
            voice_metrics={
                "overall_score": 70.0,
                "clarity_score": 75.0,
                "pace_score": 65.0,
            },
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=65.0,
                semantic_similarity=0.65,
                completeness=0.6,
                relevance=0.8,
                sentiment="uncertain",
                reasoning="Missing key concepts",
                strengths=["Correct basic definition"],
                weaknesses=["Missing base case", "No examples"],
                improvement_suggestions=["Explain base case"],
            )
        )
        await mock_answer_repo.save(answer1)

        answer2 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q2_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Async/await allows non-blocking I/O operations.",
            is_voice=True,
            similarity_score=0.85,
            gaps={"concepts": [], "keywords": [], "confirmed": False},
            voice_metrics={
                "overall_score": 80.0,
                "clarity_score": 85.0,
                "pace_score": 75.0,
            },
        )
        answer2.evaluate(
            AnswerEvaluation(
                score=85.0,
                semantic_similarity=0.85,
                completeness=0.9,
                relevance=0.95,
                sentiment="confident",
                reasoning="Strong answer",
                strengths=["Clear explanation", "Good examples"],
                weaknesses=["Could add more detail"],
                improvement_suggestions=["Discuss event loop"],
            )
        )
        await mock_answer_repo.save(answer2)

        # Create 1 follow-up question for q1
        follow_up = FollowUpQuestion(
            parent_question_id=q1_id,
            interview_id=sample_interview_adaptive.id,
            text="Can you explain what a base case is?",
            generated_reason="Missing concept: base case",
            order_in_sequence=1,
        )
        await mock_follow_up_question_repo.save(follow_up)

        # Follow-up answer (improved)
        follow_up_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=follow_up.id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Base case is the condition that stops recursion.",
            is_voice=True,
            similarity_score=0.75,
            gaps={"concepts": ["call stack"], "keywords": [], "confirmed": True},
            voice_metrics={
                "overall_score": 75.0,
                "clarity_score": 80.0,
                "pace_score": 70.0,
            },
        )
        follow_up_answer.evaluate(
            AnswerEvaluation(
                score=75.0,
                semantic_similarity=0.75,
                completeness=0.7,
                relevance=0.85,
                sentiment="confident",
                reasoning="Better understanding",
                strengths=["Correct explanation"],
                weaknesses=["Could elaborate more"],
                improvement_suggestions=["Add examples"],
            )
        )
        await mock_answer_repo.save(follow_up_answer)

        # Update interview with follow-up
        sample_interview_adaptive.adaptive_follow_ups = [follow_up.id]
        await mock_interview_repo.update(sample_interview_adaptive)

        # Execute use case
        use_case = GenerateSummaryUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        summary = await use_case.execute(sample_interview_adaptive.id)

        # Verify structure
        assert summary["interview_id"] == str(sample_interview_adaptive.id)
        assert summary["total_questions"] == 3
        assert summary["total_follow_ups"] == 1

        # Verify aggregate metrics
        # Expected: (65 + 85 + 75) / 3 = 75.0 theoretical
        #           (70 + 80 + 75) / 3 = 75.0 speaking
        #           75 * 0.7 + 75 * 0.3 = 75.0 overall
        assert summary["theoretical_score_avg"] == 75.0
        assert summary["speaking_score_avg"] == 75.0
        assert summary["overall_score"] == 75.0

        # Verify gap progression
        assert summary["gap_progression"]["questions_with_followups"] == 1
        assert summary["gap_progression"]["gaps_filled"] == 1  # "base case" was filled
        assert summary["gap_progression"]["gaps_remaining"] == 1  # "call stack" remains
        assert summary["gap_progression"]["avg_followups_per_question"] == 1.0

        # Verify question summaries
        assert len(summary["question_summaries"]) == 3
        q1_summary = next(s for s in summary["question_summaries"] if s["question_id"] == str(q1_id))
        assert q1_summary["main_answer_score"] == 65.0
        assert q1_summary["follow_up_count"] == 1
        assert "base case" in q1_summary["initial_gaps"]
        assert "base case" not in q1_summary["final_gaps"]
        assert q1_summary["improvement"] is True

        # Verify LLM recommendations
        assert "strengths" in summary
        assert "weaknesses" in summary
        assert "study_recommendations" in summary
        assert "technique_tips" in summary
        assert isinstance(summary["strengths"], list)

        # Verify completion time
        assert "completion_time" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_interview_not_found(
        self,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test error when interview not found."""
        use_case = GenerateSummaryUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        with pytest.raises(ValueError, match="Interview .* not found"):
            await use_case.execute(uuid4())

    @pytest.mark.asyncio
    async def test_generate_summary_no_answers(
        self,
        sample_interview_adaptive,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test summary with no answers -> 0.0 scores, empty recommendations."""
        await mock_interview_repo.save(sample_interview_adaptive)

        use_case = GenerateSummaryUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        summary = await use_case.execute(sample_interview_adaptive.id)

        # Verify zero scores
        assert summary["overall_score"] == 0.0
        assert summary["theoretical_score_avg"] == 0.0
        assert summary["speaking_score_avg"] == 0.0

        # Verify empty structures
        assert summary["total_questions"] == 3
        assert summary["total_follow_ups"] == 0
        assert summary["gap_progression"]["questions_with_followups"] == 0

    @pytest.mark.asyncio
    async def test_generate_summary_no_followups(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test summary with no follow-ups -> gap progression shows 0."""
        await mock_interview_repo.save(sample_interview_adaptive)

        # Create main question and answer
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

        use_case = GenerateSummaryUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        summary = await use_case.execute(sample_interview_adaptive.id)

        # Verify no follow-ups
        assert summary["total_follow_ups"] == 0
        assert summary["gap_progression"]["questions_with_followups"] == 0
        assert summary["gap_progression"]["gaps_filled"] == 0
        assert summary["gap_progression"]["gaps_remaining"] == 0
        assert summary["gap_progression"]["avg_followups_per_question"] == 0.0

    @pytest.mark.asyncio
    async def test_generate_summary_no_voice_metrics(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test speaking_score defaults to 50.0 when no voice metrics."""
        await mock_interview_repo.save(sample_interview_adaptive)

        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        # Answer without voice metrics
        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Good answer",
            is_voice=False,
            similarity_score=0.80,
            gaps={"concepts": [], "keywords": [], "confirmed": False},
            voice_metrics=None,  # No voice metrics
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=80.0,
                semantic_similarity=0.80,
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

        use_case = GenerateSummaryUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        summary = await use_case.execute(sample_interview_adaptive.id)

        # Verify default speaking score
        assert summary["speaking_score_avg"] == 50.0
        # Overall = 80 * 0.7 + 50 * 0.3 = 56 + 15 = 71.0
        assert summary["overall_score"] == 71.0

    @pytest.mark.asyncio
    async def test_generate_summary_missing_gaps_none(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
        mock_interview_repo,
        mock_answer_repo,
        mock_question_repo,
        mock_follow_up_question_repo,
        mock_llm,
    ):
        """Test handles None gaps gracefully."""
        await mock_interview_repo.save(sample_interview_adaptive)

        q1_id = sample_interview_adaptive.question_ids[0]
        q1 = sample_question_with_ideal_answer
        q1.id = q1_id
        await mock_question_repo.save(q1)

        # Answer with None gaps
        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=q1_id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Good answer",
            is_voice=False,
            similarity_score=0.85,
            gaps=None,  # None gaps
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

        use_case = GenerateSummaryUseCase(
            interview_repository=mock_interview_repo,
            answer_repository=mock_answer_repo,
            question_repository=mock_question_repo,
            follow_up_question_repository=mock_follow_up_question_repo,
            llm=mock_llm,
        )

        # Should not raise error
        summary = await use_case.execute(sample_interview_adaptive.id)
        assert summary["overall_score"] > 0.0


class TestMetricsCalculation:
    """Test aggregate metrics calculations."""

    @pytest.mark.asyncio
    async def test_calculate_metrics_overall_weighted_score(
        self,
        sample_interview_adaptive,
    ):
        """Test overall_score = 70% theoretical + 30% speaking."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        # Create answers with specific scores
        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer 1",
            is_voice=True,
            voice_metrics={"overall_score": 80.0},
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=70.0,
                semantic_similarity=0.7,
                completeness=0.7,
                relevance=0.8,
                sentiment="confident",
                reasoning="Test",
                strengths=["Good"],
                weaknesses=[],
                improvement_suggestions=[],
            )
        )

        answer2 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer 2",
            is_voice=True,
            voice_metrics={"overall_score": 60.0},
        )
        answer2.evaluate(
            AnswerEvaluation(
                score=90.0,
                semantic_similarity=0.9,
                completeness=0.9,
                relevance=0.95,
                sentiment="confident",
                reasoning="Test",
                strengths=["Excellent"],
                weaknesses=[],
                improvement_suggestions=[],
            )
        )

        metrics = use_case._calculate_aggregate_metrics([answer1, answer2])

        # Theoretical avg = (70 + 90) / 2 = 80.0
        # Speaking avg = (80 + 60) / 2 = 70.0
        # Overall = 80 * 0.7 + 70 * 0.3 = 56 + 21 = 77.0
        assert metrics["theoretical_avg"] == 80.0
        assert metrics["speaking_avg"] == 70.0
        assert metrics["overall_score"] == 77.0

    @pytest.mark.asyncio
    async def test_calculate_metrics_no_evaluated_answers(
        self,
        sample_interview_adaptive,
    ):
        """Test returns 0.0 for all scores when no evaluated answers."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        # Unevaluated answer
        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="No evaluation",
            is_voice=False,
        )

        metrics = use_case._calculate_aggregate_metrics([answer1])

        assert metrics["overall_score"] == 0.0
        assert metrics["theoretical_avg"] == 0.0
        assert metrics["speaking_avg"] == 0.0


class TestGapProgressionAnalysis:
    """Test gap progression analysis logic."""

    @pytest.mark.asyncio
    async def test_analyze_gap_progression_gaps_filled(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
    ):
        """Test gap progression tracks concepts filled after follow-ups."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        # Main answer with gaps
        main_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Main answer",
            is_voice=False,
            gaps={"concepts": ["base case", "call stack", "recursion depth"]},
        )

        # Follow-up answer with fewer gaps
        follow_up_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Follow-up answer",
            is_voice=False,
            gaps={"concepts": ["recursion depth"]},  # 2 gaps filled
        )

        question_groups = {
            sample_question_with_ideal_answer.id: {
                "question": sample_question_with_ideal_answer,
                "main_answer": main_answer,
                "follow_ups": [],
                "follow_up_answers": [follow_up_answer],
            }
        }

        progression = await use_case._analyze_gap_progression(question_groups)

        assert progression["questions_with_followups"] == 1
        assert progression["gaps_filled"] == 2  # "base case", "call stack" filled
        assert progression["gaps_remaining"] == 1  # "recursion depth" remains
        assert progression["avg_followups_per_question"] == 1.0

    @pytest.mark.asyncio
    async def test_analyze_gap_progression_no_followups(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
    ):
        """Test gap progression with no follow-ups."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        main_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Main answer",
            is_voice=False,
            gaps={"concepts": ["base case"]},
        )

        question_groups = {
            sample_question_with_ideal_answer.id: {
                "question": sample_question_with_ideal_answer,
                "main_answer": main_answer,
                "follow_ups": [],
                "follow_up_answers": [],  # No follow-ups
            }
        }

        progression = await use_case._analyze_gap_progression(question_groups)

        assert progression["questions_with_followups"] == 0
        assert progression["gaps_filled"] == 0
        assert progression["gaps_remaining"] == 0
        assert progression["avg_followups_per_question"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_gap_progression_multiple_followups(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
    ):
        """Test gap progression with multiple follow-ups."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        main_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Main answer",
            is_voice=False,
            gaps={"concepts": ["concept1", "concept2", "concept3"]},
        )

        fu_answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="FU 1",
            is_voice=False,
            gaps={"concepts": ["concept2", "concept3"]},
        )

        fu_answer2 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="FU 2",
            is_voice=False,
            gaps={"concepts": ["concept3"]},
        )

        fu_answer3 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="FU 3",
            is_voice=False,
            gaps={"concepts": []},  # All filled
        )

        question_groups = {
            sample_question_with_ideal_answer.id: {
                "question": sample_question_with_ideal_answer,
                "main_answer": main_answer,
                "follow_ups": [],
                "follow_up_answers": [fu_answer1, fu_answer2, fu_answer3],
            }
        }

        progression = await use_case._analyze_gap_progression(question_groups)

        assert progression["questions_with_followups"] == 1
        assert progression["gaps_filled"] == 3  # All 3 concepts filled
        assert progression["gaps_remaining"] == 0
        assert progression["avg_followups_per_question"] == 3.0


class TestQuestionSummaries:
    """Test per-question summary generation."""

    @pytest.mark.asyncio
    async def test_create_question_summaries_with_improvement(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
    ):
        """Test question summary shows improvement when gaps filled."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        main_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Main answer",
            is_voice=False,
            gaps={"concepts": ["gap1", "gap2"]},
        )
        main_answer.evaluate(
            AnswerEvaluation(
                score=60.0,
                semantic_similarity=0.6,
                completeness=0.6,
                relevance=0.8,
                sentiment="uncertain",
                reasoning="Weak",
                strengths=[],
                weaknesses=["Missing concepts"],
                improvement_suggestions=["Add details"],
            )
        )

        follow_up_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Follow-up answer",
            is_voice=False,
            gaps={"concepts": ["gap2"]},  # 1 gap filled
        )

        question_groups = {
            sample_question_with_ideal_answer.id: {
                "question": sample_question_with_ideal_answer,
                "main_answer": main_answer,
                "follow_ups": [],
                "follow_up_answers": [follow_up_answer],
            }
        }

        summaries = await use_case._create_question_summaries(question_groups)

        assert len(summaries) == 1
        summary = summaries[0]
        assert summary["question_id"] == str(sample_question_with_ideal_answer.id)
        assert summary["question_text"] == sample_question_with_ideal_answer.text
        assert summary["main_answer_score"] == 60.0
        assert summary["follow_up_count"] == 1
        assert summary["initial_gaps"] == ["gap1", "gap2"]
        assert summary["final_gaps"] == ["gap2"]
        assert summary["improvement"] is True  # len(final) < len(initial)

    @pytest.mark.asyncio
    async def test_create_question_summaries_no_improvement(
        self,
        sample_interview_adaptive,
        sample_question_with_ideal_answer,
    ):
        """Test question summary shows no improvement when gaps remain same."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=None,  # type: ignore
        )

        main_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=sample_question_with_ideal_answer.id,
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Main answer",
            is_voice=False,
            gaps={"concepts": ["gap1"]},
        )
        main_answer.evaluate(
            AnswerEvaluation(
                score=65.0,
                semantic_similarity=0.65,
                completeness=0.65,
                relevance=0.8,
                sentiment="uncertain",
                reasoning="OK",
                strengths=[],
                weaknesses=[],
                improvement_suggestions=[],
            )
        )

        follow_up_answer = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Follow-up answer",
            is_voice=False,
            gaps={"concepts": ["gap1"]},  # Same gaps
        )

        question_groups = {
            sample_question_with_ideal_answer.id: {
                "question": sample_question_with_ideal_answer,
                "main_answer": main_answer,
                "follow_ups": [],
                "follow_up_answers": [follow_up_answer],
            }
        }

        summaries = await use_case._create_question_summaries(question_groups)

        assert len(summaries) == 1
        summary = summaries[0]
        assert summary["improvement"] is False  # len(final) == len(initial)


class TestLLMRecommendations:
    """Test LLM-powered recommendations generation."""

    @pytest.mark.asyncio
    async def test_generate_recommendations_called_with_context(
        self,
        sample_interview_adaptive,
        mock_llm,
    ):
        """Test LLM.generate_interview_recommendations called with correct context."""
        from src.application.use_cases.generate_summary import GenerateSummaryUseCase
        from unittest.mock import AsyncMock

        # Mock LLM with explicit return
        mock_llm.generate_interview_recommendations = AsyncMock(
            return_value={
                "strengths": ["Clear communication", "Good examples"],
                "weaknesses": ["Missing depth", "Needs more detail"],
                "study_topics": ["Recursion patterns", "Algorithm complexity"],
                "technique_tips": ["Speak slower", "Use more examples"],
            }
        )

        use_case = GenerateSummaryUseCase(
            interview_repository=None,  # type: ignore
            answer_repository=None,  # type: ignore
            question_repository=None,  # type: ignore
            follow_up_question_repository=None,  # type: ignore
            llm=mock_llm,
        )

        answer1 = Answer(
            interview_id=sample_interview_adaptive.id,
            question_id=uuid4(),
            candidate_id=sample_interview_adaptive.candidate_id,
            text="Answer 1",
            is_voice=False,
        )
        answer1.evaluate(
            AnswerEvaluation(
                score=75.0,
                semantic_similarity=0.75,
                completeness=0.8,
                relevance=0.9,
                sentiment="confident",
                reasoning="Good",
                strengths=["Clear"],
                weaknesses=["Could improve"],
                improvement_suggestions=["Add details"],
            )
        )

        gap_progression = {
            "questions_with_followups": 1,
            "gaps_filled": 2,
            "gaps_remaining": 1,
            "avg_followups_per_question": 1.0,
        }

        recommendations = await use_case._generate_recommendations(
            sample_interview_adaptive,
            [answer1],
            gap_progression,
        )

        # Verify LLM called once
        assert mock_llm.generate_interview_recommendations.call_count == 1

        # Verify context structure
        call_args = mock_llm.generate_interview_recommendations.call_args
        context = call_args[0][0]
        assert context["interview_id"] == str(sample_interview_adaptive.id)
        assert context["total_answers"] == 1
        assert context["gap_progression"] == gap_progression
        assert len(context["evaluations"]) == 1

        # Verify recommendations structure
        assert "strengths" in recommendations
        assert "weaknesses" in recommendations
        assert "study_topics" in recommendations
        assert "technique_tips" in recommendations
