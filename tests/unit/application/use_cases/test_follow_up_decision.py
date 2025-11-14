"""Tests for FollowUpDecisionUseCase."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.application.use_cases.follow_up_decision import FollowUpDecisionUseCase
from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.follow_up_question import FollowUpQuestion


class MockAnswerRepository:
    """Mock answer repository for testing."""

    def __init__(self):
        self.answers = {}

    async def get_by_question_id(self, question_id: UUID) -> Answer | None:
        return self.answers.get(question_id)

    def add_answer(self, question_id: UUID, answer: Answer):
        self.answers[question_id] = answer


class MockFollowUpQuestionRepository:
    """Mock follow-up question repository for testing."""

    def __init__(self):
        self.follow_ups = {}

    async def get_by_parent_question_id(
        self, parent_question_id: UUID
    ) -> list[FollowUpQuestion]:
        return self.follow_ups.get(parent_question_id, [])

    def add_follow_ups(self, parent_question_id: UUID, follow_ups: list[FollowUpQuestion]):
        self.follow_ups[parent_question_id] = follow_ups


@pytest.fixture
def answer_repo():
    return MockAnswerRepository()


@pytest.fixture
def follow_up_repo():
    return MockFollowUpQuestionRepository()


@pytest.fixture
def use_case(answer_repo, follow_up_repo):
    return FollowUpDecisionUseCase(
        answer_repository=answer_repo,
        follow_up_question_repository=follow_up_repo,
    )


@pytest.fixture
def interview_id():
    return uuid4()


@pytest.fixture
def parent_question_id():
    return uuid4()


@pytest.fixture
def candidate_id():
    return uuid4()


@pytest.mark.asyncio
async def test_no_followup_when_max_reached(
    use_case, interview_id, parent_question_id, candidate_id, follow_up_repo, answer_repo
):
    """Test that no follow-up is generated when max (3) already reached."""
    # Create 3 existing follow-ups
    follow_ups = [
        FollowUpQuestion(
            id=uuid4(),
            parent_question_id=parent_question_id,
            interview_id=interview_id,
            text=f"Follow-up {i+1}",
            generated_reason="Missing concepts",
            order_in_sequence=i + 1,
        )
        for i in range(3)
    ]
    follow_up_repo.add_follow_ups(parent_question_id, follow_ups)

    # Create latest answer with gaps
    latest_answer = Answer(
        interview_id=interview_id,
        question_id=uuid4(),
        candidate_id=candidate_id,
        text="Incomplete answer",
        similarity_score=0.5,
        gaps={"concepts": ["concept1", "concept2"], "confirmed": True},
    )

    # Execute decision
    decision = await use_case.execute(
        interview_id=interview_id,
        parent_question_id=parent_question_id,
        latest_answer=latest_answer,
    )

    assert decision["needs_followup"] is False
    assert "Max follow-ups (3)" in decision["reason"]
    assert decision["follow_up_count"] == 3


@pytest.mark.asyncio
async def test_no_followup_when_similarity_high(
    use_case, interview_id, parent_question_id, candidate_id, follow_up_repo
):
    """Test that no follow-up is generated when similarity >= 0.8."""
    # No existing follow-ups
    follow_up_repo.add_follow_ups(parent_question_id, [])

    # Create latest answer with high similarity
    latest_answer = Answer(
        interview_id=interview_id,
        question_id=uuid4(),
        candidate_id=candidate_id,
        text="Complete answer",
        similarity_score=0.85,
        gaps={"concepts": [], "confirmed": False},
    )

    # Execute decision
    decision = await use_case.execute(
        interview_id=interview_id,
        parent_question_id=parent_question_id,
        latest_answer=latest_answer,
    )

    assert decision["needs_followup"] is False
    assert "0.85" in decision["reason"]
    assert decision["follow_up_count"] == 0


@pytest.mark.asyncio
async def test_no_followup_when_no_gaps(
    use_case, interview_id, parent_question_id, candidate_id, follow_up_repo
):
    """Test that no follow-up is generated when no gaps detected."""
    # No existing follow-ups
    follow_up_repo.add_follow_ups(parent_question_id, [])

    # Create latest answer with no gaps
    latest_answer = Answer(
        interview_id=interview_id,
        question_id=uuid4(),
        candidate_id=candidate_id,
        text="Complete answer",
        similarity_score=0.7,
        gaps={"concepts": [], "confirmed": False},
    )

    # Execute decision
    decision = await use_case.execute(
        interview_id=interview_id,
        parent_question_id=parent_question_id,
        latest_answer=latest_answer,
    )

    assert decision["needs_followup"] is False
    assert "No concept gaps" in decision["reason"] or "No cumulative gaps" in decision["reason"]
    assert decision["follow_up_count"] == 0


@pytest.mark.asyncio
async def test_followup_needed_with_gaps(
    use_case, interview_id, parent_question_id, candidate_id, follow_up_repo
):
    """Test that follow-up is generated when gaps exist."""
    # No existing follow-ups
    follow_up_repo.add_follow_ups(parent_question_id, [])

    # Create latest answer with confirmed gaps
    latest_answer = Answer(
        interview_id=interview_id,
        question_id=uuid4(),
        candidate_id=candidate_id,
        text="Incomplete answer",
        similarity_score=0.5,
        gaps={"concepts": ["recursion", "base case"], "confirmed": True},
    )

    # Execute decision
    decision = await use_case.execute(
        interview_id=interview_id,
        parent_question_id=parent_question_id,
        latest_answer=latest_answer,
    )

    assert decision["needs_followup"] is True
    assert "2 missing concepts" in decision["reason"]
    assert decision["follow_up_count"] == 0
    assert set(decision["cumulative_gaps"]) == {"recursion", "base case"}


@pytest.mark.asyncio
async def test_gap_accumulation_across_followups(
    use_case, interview_id, parent_question_id, candidate_id, follow_up_repo, answer_repo
):
    """Test that gaps accumulate across multiple follow-up answers."""
    # Create 2 existing follow-ups
    follow_up1_id = uuid4()
    follow_up2_id = uuid4()
    follow_ups = [
        FollowUpQuestion(
            id=follow_up1_id,
            parent_question_id=parent_question_id,
            interview_id=interview_id,
            text="Follow-up 1",
            generated_reason="Missing concepts",
            order_in_sequence=1,
        ),
        FollowUpQuestion(
            id=follow_up2_id,
            parent_question_id=parent_question_id,
            interview_id=interview_id,
            text="Follow-up 2",
            generated_reason="Missing concepts",
            order_in_sequence=2,
        ),
    ]
    follow_up_repo.add_follow_ups(parent_question_id, follow_ups)

    # Add answers for follow-ups with different gaps
    answer_repo.add_answer(
        follow_up1_id,
        Answer(
            interview_id=interview_id,
            question_id=follow_up1_id,
            candidate_id=candidate_id,
            text="Answer 1",
            gaps={"concepts": ["concept1", "concept2"], "confirmed": True},
        ),
    )
    answer_repo.add_answer(
        follow_up2_id,
        Answer(
            interview_id=interview_id,
            question_id=follow_up2_id,
            candidate_id=candidate_id,
            text="Answer 2",
            gaps={"concepts": ["concept2", "concept3"], "confirmed": True},
        ),
    )

    # Create latest answer with new gaps
    latest_answer = Answer(
        interview_id=interview_id,
        question_id=uuid4(),
        candidate_id=candidate_id,
        text="Latest answer",
        similarity_score=0.6,
        gaps={"concepts": ["concept3", "concept4"], "confirmed": True},
    )

    # Execute decision
    decision = await use_case.execute(
        interview_id=interview_id,
        parent_question_id=parent_question_id,
        latest_answer=latest_answer,
    )

    assert decision["needs_followup"] is True
    assert decision["follow_up_count"] == 2
    # Should have unique concepts: concept1, concept2, concept3, concept4
    assert set(decision["cumulative_gaps"]) == {"concept1", "concept2", "concept3", "concept4"}


@pytest.mark.asyncio
async def test_no_followup_when_count_2_and_no_new_gaps(
    use_case, interview_id, parent_question_id, candidate_id, follow_up_repo
):
    """Test that no follow-up when count=2 but no new gaps in latest answer."""
    # Create 2 existing follow-ups
    follow_ups = [
        FollowUpQuestion(
            id=uuid4(),
            parent_question_id=parent_question_id,
            interview_id=interview_id,
            text=f"Follow-up {i+1}",
            generated_reason="Missing concepts",
            order_in_sequence=i + 1,
        )
        for i in range(2)
    ]
    follow_up_repo.add_follow_ups(parent_question_id, follow_ups)

    # Create latest answer with no gaps
    latest_answer = Answer(
        interview_id=interview_id,
        question_id=uuid4(),
        candidate_id=candidate_id,
        text="Complete answer now",
        similarity_score=0.75,
        gaps={"concepts": [], "confirmed": False},
    )

    # Execute decision
    decision = await use_case.execute(
        interview_id=interview_id,
        parent_question_id=parent_question_id,
        latest_answer=latest_answer,
    )

    assert decision["needs_followup"] is False
    assert decision["follow_up_count"] == 2
