"""Tests for Phase 01: Domain model updates for adaptive interviews."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.follow_up_question import FollowUpQuestion
from src.domain.models.interview import Interview, InterviewStatus
from src.domain.models.question import DifficultyLevel, Question, QuestionType


class TestQuestionAdaptiveFields:
    """Test Question model adaptive fields (ideal_answer, rationale)."""

    def test_question_with_ideal_answer(self):
        """Test question with ideal answer and rationale."""
        question = Question(
            text="Explain recursion",
            question_type=QuestionType.TECHNICAL,
            difficulty=DifficultyLevel.MEDIUM,
            skills=["Python"],
            ideal_answer="Recursion is a function calling itself with a base case...",
            rationale="This answer demonstrates mastery by covering base case and examples",
        )

        assert question.has_ideal_answer() is True
        assert question.is_planned is True
        assert question.ideal_answer is not None
        assert question.rationale is not None

    def test_question_without_ideal_answer(self):
        """Test legacy question without ideal answer."""
        question = Question(
            text="Tell me about yourself",
            question_type=QuestionType.BEHAVIORAL,
            difficulty=DifficultyLevel.EASY,
            skills=["Communication"],
        )

        assert question.has_ideal_answer() is False
        assert question.is_planned is False
        assert question.ideal_answer is None
        assert question.rationale is None

    def test_has_ideal_answer_empty_string(self):
        """Test has_ideal_answer with empty or short string."""
        question = Question(
            text="Test",
            question_type=QuestionType.TECHNICAL,
            difficulty=DifficultyLevel.EASY,
            skills=["Test"],
            ideal_answer="   ",  # Only whitespace
        )

        assert question.has_ideal_answer() is False

        question.ideal_answer = "Short"  # < 10 chars
        assert question.has_ideal_answer() is False


class TestInterviewAdaptiveFields:
    """Test Interview model adaptive fields (plan_metadata, adaptive_follow_ups)."""

    def test_interview_with_planning_metadata(self):
        """Test interview with plan_metadata."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.READY,
        )
        interview.plan_metadata = {
            "n": 4,
            "generated_at": datetime.utcnow().isoformat(),
            "strategy": "adaptive_planning_v1",
        }

        assert interview.planned_question_count == 4
        assert "strategy" in interview.plan_metadata

    def test_interview_without_planning_metadata(self):
        """Test legacy interview without plan_metadata."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.IN_PROGRESS,
        )

        assert interview.plan_metadata == {}
        assert interview.planned_question_count == 0

    def test_add_adaptive_followup(self):
        """Test adding adaptive follow-up questions."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.IN_PROGRESS,
        )

        follow_up_id = uuid4()
        interview.add_adaptive_followup(follow_up_id)

        assert len(interview.adaptive_follow_ups) == 1
        assert follow_up_id in interview.adaptive_follow_ups

    def test_mark_ready_with_cv_analysis(self):
        """Test marking interview as READY after planning."""
        cv_analysis_id = uuid4()
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.PREPARING,
        )

        interview.mark_ready(cv_analysis_id)

        assert interview.status == InterviewStatus.READY
        assert interview.cv_analysis_id == cv_analysis_id


class TestAnswerAdaptiveFields:
    """Test Answer model adaptive fields (similarity_score, gaps)."""

    def test_answer_with_similarity_score(self):
        """Test answer with similarity score."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Recursion calls itself with base case",
            is_voice=False,
            similarity_score=0.85,
        )

        assert answer.has_similarity_score() is True
        assert answer.similarity_score == 0.85
        assert answer.meets_threshold(0.8) is True
        assert answer.meets_threshold(0.9) is False

    def test_answer_without_similarity_score(self):
        """Test legacy answer without similarity score."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Some answer",
            is_voice=False,
        )

        assert answer.has_similarity_score() is False
        assert answer.similarity_score is None
        assert answer.meets_threshold(0.8) is False

    def test_answer_with_gaps(self):
        """Test answer with detected gaps."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Brief answer",
            is_voice=False,
            gaps={
                "concepts": ["base case", "recursive case"],
                "keywords": ["base", "recursive"],
                "confirmed": True,
                "severity": "moderate",
            },
        )

        assert answer.has_gaps() is True
        assert len(answer.gaps["concepts"]) == 2  # type: ignore
        assert answer.gaps["confirmed"] is True  # type: ignore

    def test_answer_without_gaps(self):
        """Test answer without gaps."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Complete answer",
            is_voice=False,
            gaps={"concepts": [], "confirmed": False},
        )

        assert answer.has_gaps() is False

    def test_is_adaptive_complete_high_similarity(self):
        """Test adaptive completion with high similarity (>= 80%)."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Good answer",
            is_voice=False,
            similarity_score=0.85,
            gaps={"concepts": ["minor"], "confirmed": True},
        )

        assert answer.is_adaptive_complete() is True

    def test_is_adaptive_complete_no_gaps(self):
        """Test adaptive completion with no confirmed gaps."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Good answer",
            is_voice=False,
            similarity_score=0.75,
            gaps={"concepts": [], "confirmed": False},
        )

        assert answer.is_adaptive_complete() is True

    def test_is_adaptive_incomplete(self):
        """Test answer that needs follow-up."""
        answer = Answer(
            interview_id=uuid4(),
            question_id=uuid4(),
            candidate_id=uuid4(),
            text="Brief answer",
            is_voice=False,
            similarity_score=0.60,
            gaps={"concepts": ["base case"], "confirmed": True},
        )

        assert answer.is_adaptive_complete() is False


class TestFollowUpQuestion:
    """Test FollowUpQuestion model."""

    def test_follow_up_question_creation(self):
        """Test creating a follow-up question."""
        parent_id = uuid4()
        interview_id = uuid4()

        follow_up = FollowUpQuestion(
            parent_question_id=parent_id,
            interview_id=interview_id,
            text="Can you explain the base case in recursion?",
            generated_reason="Missing concepts: base case",
            order_in_sequence=1,
        )

        assert follow_up.parent_question_id == parent_id
        assert follow_up.interview_id == interview_id
        assert follow_up.order_in_sequence == 1
        assert follow_up.is_last_allowed() is False

    def test_is_last_allowed(self):
        """Test detection of 3rd follow-up (max allowed)."""
        follow_up_third = FollowUpQuestion(
            parent_question_id=uuid4(),
            interview_id=uuid4(),
            text="Third follow-up",
            generated_reason="Still missing concepts",
            order_in_sequence=3,
        )

        assert follow_up_third.is_last_allowed() is True

    def test_follow_up_has_created_at(self):
        """Test follow-up question has timestamp."""
        follow_up = FollowUpQuestion(
            parent_question_id=uuid4(),
            interview_id=uuid4(),
            text="Follow-up",
            generated_reason="Gaps detected",
            order_in_sequence=1,
        )

        assert follow_up.created_at is not None
        assert isinstance(follow_up.created_at, datetime)


class TestSimilarityScoreValidation:
    """Test similarity_score field validation (0-1 range)."""

    def test_valid_similarity_scores(self):
        """Test valid similarity scores (0.0 to 1.0)."""
        for score in [0.0, 0.5, 0.8, 1.0]:
            answer = Answer(
                interview_id=uuid4(),
                question_id=uuid4(),
                candidate_id=uuid4(),
                text="Test",
                is_voice=False,
                similarity_score=score,
            )
            assert answer.similarity_score == score

    def test_invalid_similarity_score_too_high(self):
        """Test invalid similarity score > 1.0."""
        with pytest.raises(Exception):  # Pydantic validation error
            Answer(
                interview_id=uuid4(),
                question_id=uuid4(),
                candidate_id=uuid4(),
                text="Test",
                is_voice=False,
                similarity_score=1.5,
            )

    def test_invalid_similarity_score_negative(self):
        """Test invalid negative similarity score."""
        with pytest.raises(Exception):  # Pydantic validation error
            Answer(
                interview_id=uuid4(),
                question_id=uuid4(),
                candidate_id=uuid4(),
                text="Test",
                is_voice=False,
                similarity_score=-0.1,
            )
