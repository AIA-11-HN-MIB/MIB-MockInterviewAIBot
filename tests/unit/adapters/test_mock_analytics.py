"""Unit tests for MockAnalyticsAdapter."""

import pytest
from uuid import uuid4

from src.adapters.mock.mock_analytics import MockAnalyticsAdapter
from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.question import Question, QuestionType, DifficultyLevel


@pytest.fixture
def analytics():
    """Create analytics adapter instance."""
    return MockAnalyticsAdapter()


@pytest.fixture
def sample_question():
    """Create sample question."""
    return Question(
        id=uuid4(),
        text="What is Python?",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.MEDIUM,
        skills=["Python", "Programming"],
        reference_answer="Python is a high-level programming language...",
        evaluation_criteria="Understanding Python fundamentals",
    )


def _create_answer(question_id):
    """Helper to create sample answer."""
    evaluation = AnswerEvaluation(
        score=85.0,
        semantic_similarity=0.9,
        completeness=0.85,
        relevance=0.95,
        sentiment="confident",
        reasoning="Good answer with examples",
        strengths=["Clear explanation", "Good examples"],
        weaknesses=["Could add more depth"],
        improvement_suggestions=["Add advanced use cases"],
    )

    return Answer(
        id=uuid4(),
        question_id=question_id,
        candidate_id=uuid4(),
        interview_id=uuid4(),
        text="Python is a versatile programming language known for readability",
        evaluation=evaluation,
    )



@pytest.fixture
def sample_answer(sample_question):
    """Create sample answer with evaluation."""
    return _create_answer(sample_question.id)


class TestRecordAnswerEvaluation:
    """Test record_answer_evaluation method."""

    @pytest.mark.asyncio
    async def test_record_single_answer(self, analytics, sample_answer):
        """Test recording single answer."""
        interview_id = uuid4()

        await analytics.record_answer_evaluation(interview_id, sample_answer)

        # Verify it was stored
        stats = await analytics.get_interview_statistics(interview_id)
        assert stats["answers_count"] == 1

    @pytest.mark.asyncio
    async def test_record_multiple_answers(self, analytics, sample_answer):
        """Test recording multiple answers."""
        interview_id = uuid4()

        # Record 3 answers
        for _ in range(3):
            await analytics.record_answer_evaluation(interview_id, sample_answer)

        stats = await analytics.get_interview_statistics(interview_id)
        assert stats["answers_count"] == 3


class TestGetInterviewStatistics:
    """Test get_interview_statistics method."""

    @pytest.mark.asyncio
    async def test_empty_interview(self, analytics):
        """Test statistics for interview with no answers."""
        interview_id = uuid4()

        stats = await analytics.get_interview_statistics(interview_id)

        assert stats["interview_id"] == str(interview_id)
        assert stats["question_count"] == 0
        assert stats["answers_count"] == 0
        assert stats["avg_score"] == 0.0
        assert stats["completion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_statistics_calculation(self, analytics, sample_question):
        """Test statistics are calculated correctly."""
        interview_id = uuid4()

        # Create answers with different scores
        scores = [80.0, 90.0, 70.0]
        for score in scores:
            evaluation = AnswerEvaluation(
                score=score,
                semantic_similarity=0.8,
                completeness=0.8,
                relevance=0.8,
                sentiment="positive",
                reasoning="Test",
                strengths=["Test"],
                weaknesses=[],
                improvement_suggestions=[],
            )
            answer = Answer(
                id=uuid4(),
                question_id=sample_question.id,
                candidate_id=uuid4(),
                interview_id=interview_id,
                text="Test answer",
                evaluation=evaluation,
            )
            await analytics.record_answer_evaluation(interview_id, answer)

        stats = await analytics.get_interview_statistics(interview_id)

        assert stats["question_count"] == 3
        assert stats["answers_count"] == 3
        assert stats["avg_score"] == 80.0  # (80+90+70)/3
        assert stats["completion_rate"] == 100.0
        assert stats["highest_score"] == 90.0
        assert stats["lowest_score"] == 70.0
        assert stats["time_spent_minutes"] > 0

    @pytest.mark.asyncio
    async def test_completion_rate(self, analytics, sample_question):
        """Test completion rate calculation."""
        interview_id = uuid4()

        # Create 2 answers with text and 1 without
        for i in range(3):
            evaluation = AnswerEvaluation(
                score=80.0,
                semantic_similarity=0.8,
                completeness=0.8,
                relevance=0.8,
                sentiment="positive",
                reasoning="Test",
                strengths=[],
                weaknesses=[],
                improvement_suggestions=[],
            )
            answer = Answer(
                id=uuid4(),
                question_id=sample_question.id,
                interview_id=interview_id,
                candidate_id=uuid4(),
                text="Answer" if i < 2 else "",  # 2 with text, 1 empty
                evaluation=evaluation,
            )
            await analytics.record_answer_evaluation(interview_id, answer)

        stats = await analytics.get_interview_statistics(interview_id)
        assert stats["completion_rate"] == pytest.approx(66.67, rel=0.1)


class TestGetCandidatePerformanceHistory:
    """Test get_candidate_performance_history method."""

    @pytest.mark.asyncio
    async def test_first_time_candidate(self, analytics):
        """Test history for first-time candidate."""
        candidate_id = uuid4()

        history = await analytics.get_candidate_performance_history(candidate_id)

        assert isinstance(history, list)
        assert len(history) >= 0  # Mock generates 0-3 past interviews

    @pytest.mark.asyncio
    async def test_history_structure(self, analytics):
        """Test history entries have correct structure."""
        candidate_id = uuid4()

        history = await analytics.get_candidate_performance_history(candidate_id)

        if history:
            entry = history[0]
            assert "interview_date" in entry
            assert "avg_score" in entry
            assert "questions_answered" in entry
            assert "completion_rate" in entry
            assert "strong_skills" in entry
            assert "weak_skills" in entry

    @pytest.mark.asyncio
    async def test_history_shows_improvement(self, analytics):
        """Test that mock history shows score improvement."""
        candidate_id = uuid4()

        history = await analytics.get_candidate_performance_history(candidate_id)

        if len(history) >= 2:
            # Scores should improve over time
            assert history[1]["avg_score"] >= history[0]["avg_score"]


class TestGenerateImprovementRecommendations:
    """Test generate_improvement_recommendations method."""

    @pytest.mark.asyncio
    async def test_no_answers(self, analytics):
        """Test recommendations with no answers."""
        interview_id = uuid4()
        recommendations = await analytics.generate_improvement_recommendations(
            interview_id, [], []
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("Complete the interview" in r for r in recommendations)

    @pytest.mark.asyncio
    async def test_low_score_recommendations(self, analytics, sample_question):
        """Test recommendations for low scores (<60)."""
        interview_id = uuid4()

        # Create low-scoring answers
        questions = [sample_question, sample_question, sample_question]  # 3 questions for 3 answers
        answers = []
        for _ in range(3):
            evaluation = AnswerEvaluation(
                score=50.0,
                semantic_similarity=0.5,
                completeness=0.5,
                relevance=0.6,
                sentiment="uncertain",
                reasoning="Lacks depth",
                strengths=[],
                weaknesses=["Lacks depth", "Missing examples"],
                improvement_suggestions=["Study fundamentals"],
            )
            answer = Answer(
                id=uuid4(),
                question_id=sample_question.id,
                interview_id=interview_id,
                candidate_id=uuid4(),
                text="Brief answer",
                evaluation=evaluation,
            )
            answers.append(answer)

        recommendations = await analytics.generate_improvement_recommendations(
            interview_id, questions, answers
        )

        assert len(recommendations) >= 3
        assert len(recommendations) <= 5
        assert any("fundamental" in r.lower() for r in recommendations)

    @pytest.mark.asyncio
    async def test_mid_score_recommendations(self, analytics, sample_question):
        """Test recommendations for mid-range scores (60-80)."""
        interview_id = uuid4()

        questions = [sample_question]
        answers = []
        evaluation = AnswerEvaluation(
            score=70.0,
            semantic_similarity=0.7,
            completeness=0.7,
            relevance=0.75,
            sentiment="positive",
            reasoning="Good but could improve",
            strengths=["Clear"],
            weaknesses=["Could add more detail"],
            improvement_suggestions=["Add examples"],
        )
        answer = Answer(
            id=uuid4(),
            question_id=sample_question.id,
            interview_id=interview_id,
            candidate_id=uuid4(),
            text="Decent answer",
            evaluation=evaluation,
        )
        answers.append(answer)

        recommendations = await analytics.generate_improvement_recommendations(
            interview_id, questions, answers
        )

        assert len(recommendations) >= 2
        assert len(recommendations) <= 5

    @pytest.mark.asyncio
    async def test_high_score_recommendations(self, analytics, sample_question):
        """Test recommendations for high scores (>80)."""
        interview_id = uuid4()

        questions = [sample_question]
        answers = []
        evaluation = AnswerEvaluation(
            score=90.0,
            semantic_similarity=0.95,
            completeness=0.9,
            relevance=0.95,
            sentiment="confident",
            reasoning="Excellent answer",
            strengths=["Comprehensive", "Clear", "Good examples"],
            weaknesses=["Minor formatting"],
            improvement_suggestions=["Consider edge cases"],
        )
        answer = Answer(
            id=uuid4(),
            question_id=sample_question.id,
            interview_id=interview_id,
            candidate_id=uuid4(),
            text="Excellent detailed answer",
            evaluation=evaluation,
        )
        answers.append(answer)

        recommendations = await analytics.generate_improvement_recommendations(
            interview_id, questions, answers
        )

        assert len(recommendations) > 0
        assert len(recommendations) <= 5
        assert any("excellent" in r.lower() or "continue" in r.lower() for r in recommendations)


class TestCalculateSkillScores:
    """Test calculate_skill_scores method."""

    @pytest.mark.asyncio
    async def test_empty_data(self, analytics):
        """Test with no answers."""
        scores = await analytics.calculate_skill_scores([], [])
        assert scores == {}

    @pytest.mark.asyncio
    async def test_single_skill(self, analytics):
        """Test scoring for single skill."""
        question = Question(
            id=uuid4(),
            text="What is Python?",
            question_type=QuestionType.TECHNICAL,
            difficulty=DifficultyLevel.MEDIUM,
            skills=["Python"],
        )

        evaluation = AnswerEvaluation(
            score=85.0,
            semantic_similarity=0.85,
            completeness=0.85,
            relevance=0.9,
            sentiment="confident",
            reasoning="Good",
            strengths=[],
            weaknesses=[],
            improvement_suggestions=[],
        )
        answer = Answer(
            id=uuid4(),
            question_id=question.id,
            interview_id=uuid4(),
            candidate_id=uuid4(),
            text="Answer",
            evaluation=evaluation,
        )

        scores = await analytics.calculate_skill_scores([answer], [question])

        assert "Python" in scores
        assert scores["Python"] == 85.0

    @pytest.mark.asyncio
    async def test_multiple_skills(self, analytics):
        """Test scoring across multiple skills."""
        questions = [
            Question(
                id=uuid4(),
                text="Q1",
                question_type=QuestionType.TECHNICAL,
                difficulty=DifficultyLevel.MEDIUM,
                skills=["Python", "FastAPI"],
            ),
            Question(
                id=uuid4(),
                text="Q2",
                question_type=QuestionType.TECHNICAL,
                difficulty=DifficultyLevel.MEDIUM,
                skills=["Python"],
            ),
        ]

        answers = [
            Answer(
                id=uuid4(),
                question_id=questions[0].id,
                interview_id=uuid4(),
                candidate_id=uuid4(),
                text="A1",
                evaluation=AnswerEvaluation(
                    score=80.0,
                    semantic_similarity=0.8,
                    completeness=0.8,
                    relevance=0.8,
                    sentiment="positive",
                    reasoning="",
                    strengths=[],
                    weaknesses=[],
                    improvement_suggestions=[],
                ),
            ),
            Answer(
                id=uuid4(),
                question_id=questions[1].id,
                interview_id=uuid4(),
                candidate_id=uuid4(),
                text="A2",
                evaluation=AnswerEvaluation(
                    score=90.0,
                    semantic_similarity=0.9,
                    completeness=0.9,
                    relevance=0.9,
                    sentiment="confident",
                    reasoning="",
                    strengths=[],
                    weaknesses=[],
                    improvement_suggestions=[],
                ),
            ),
        ]

        scores = await analytics.calculate_skill_scores(answers, questions)

        assert "Python" in scores
        assert "FastAPI" in scores
        assert scores["Python"] == 85.0  # Average of 80 and 90
        assert scores["FastAPI"] == 80.0

    @pytest.mark.asyncio
    async def test_mismatched_lengths(self, analytics, sample_question):
        """Test with mismatched answer/question counts."""
        answer = _create_answer(sample_question.id)
        scores = await analytics.calculate_skill_scores([answer], [])
        assert scores == {}
