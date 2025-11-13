"""Unit tests for Interview state transitions."""

import pytest
from uuid import uuid4

from src.domain.models.interview import Interview, InterviewStatus


class TestStateTransitionValidation:
    """Test state transition validation logic."""

    def test_valid_transition_planning_to_idle(self):
        """Test valid PLANNING → IDLE transition."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.PLANNING)
        cv_analysis_id = uuid4()

        interview.mark_ready(cv_analysis_id)

        assert interview.status == InterviewStatus.IDLE
        assert interview.cv_analysis_id == cv_analysis_id

    def test_valid_transition_idle_to_questioning(self):
        """Test valid IDLE → QUESTIONING transition."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)

        interview.start()

        assert interview.status == InterviewStatus.QUESTIONING
        assert interview.started_at is not None

    def test_valid_transition_questioning_to_evaluating(self):
        """Test valid QUESTIONING → EVALUATING transition."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.QUESTIONING,
            question_ids=[uuid4()],
            current_question_index=0,
        )

        interview.add_answer(uuid4())

        assert interview.status == InterviewStatus.EVALUATING
        assert interview.current_question_index == 1

    def test_valid_transition_evaluating_to_follow_up(self):
        """Test valid EVALUATING → FOLLOW_UP transition."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q_id = uuid4()
        followup_id = uuid4()

        interview.ask_followup(followup_id, parent_q_id)

        assert interview.status == InterviewStatus.FOLLOW_UP
        assert interview.current_parent_question_id == parent_q_id
        assert interview.current_followup_count == 1
        assert followup_id in interview.adaptive_follow_ups

    def test_valid_transition_evaluating_to_questioning(self):
        """Test valid EVALUATING → QUESTIONING transition."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.EVALUATING,
            question_ids=[uuid4(), uuid4()],
            current_question_index=0,
        )

        interview.proceed_to_next_question()

        assert interview.status == InterviewStatus.QUESTIONING
        assert interview.current_followup_count == 0
        assert interview.current_parent_question_id is None

    def test_valid_transition_evaluating_to_complete(self):
        """Test valid EVALUATING → COMPLETE transition."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.EVALUATING,
            question_ids=[uuid4()],
            current_question_index=1,  # No more questions
        )

        interview.proceed_to_next_question()

        assert interview.status == InterviewStatus.COMPLETE
        assert interview.completed_at is not None

    def test_valid_transition_follow_up_to_evaluating(self):
        """Test valid FOLLOW_UP → EVALUATING transition."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.FOLLOW_UP)

        interview.answer_followup()

        assert interview.status == InterviewStatus.EVALUATING

    def test_invalid_transition_idle_to_evaluating(self):
        """Test invalid IDLE → EVALUATING transition raises error."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)

        with pytest.raises(ValueError, match="Invalid transition"):
            interview.transition_to(InterviewStatus.EVALUATING)

    def test_invalid_transition_complete_to_questioning(self):
        """Test terminal state COMPLETE cannot transition."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.COMPLETE)

        with pytest.raises(ValueError, match="Invalid transition"):
            interview.transition_to(InterviewStatus.QUESTIONING)

    def test_invalid_transition_cancelled_to_idle(self):
        """Test terminal state CANCELLED cannot transition."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.CANCELLED)

        with pytest.raises(ValueError, match="Invalid transition"):
            interview.transition_to(InterviewStatus.IDLE)

    def test_all_valid_transitions(self):
        """Test all valid state transitions succeed."""
        valid_paths = [
            (InterviewStatus.PLANNING, InterviewStatus.IDLE),
            (InterviewStatus.IDLE, InterviewStatus.QUESTIONING),
            (InterviewStatus.QUESTIONING, InterviewStatus.EVALUATING),
            (InterviewStatus.EVALUATING, InterviewStatus.FOLLOW_UP),
            (InterviewStatus.EVALUATING, InterviewStatus.QUESTIONING),
            (InterviewStatus.EVALUATING, InterviewStatus.COMPLETE),
            (InterviewStatus.FOLLOW_UP, InterviewStatus.EVALUATING),
        ]

        for from_status, to_status in valid_paths:
            interview = Interview(candidate_id=uuid4(), status=from_status)
            interview.transition_to(to_status)
            assert interview.status == to_status

    def test_cancel_from_any_non_terminal_state(self):
        """Test cancel() works from any non-terminal state."""
        states = [
            InterviewStatus.PLANNING,
            InterviewStatus.IDLE,
            InterviewStatus.QUESTIONING,
            InterviewStatus.EVALUATING,
            InterviewStatus.FOLLOW_UP,
        ]

        for state in states:
            interview = Interview(candidate_id=uuid4(), status=state)
            interview.cancel()
            assert interview.status == InterviewStatus.CANCELLED


class TestFollowUpTracking:
    """Test follow-up question counter logic."""

    def test_first_followup_sets_parent_and_count(self):
        """Test first follow-up sets parent question and count to 1."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q = uuid4()
        followup_id = uuid4()

        interview.ask_followup(followup_id, parent_q)

        assert interview.current_parent_question_id == parent_q
        assert interview.current_followup_count == 1
        assert interview.status == InterviewStatus.FOLLOW_UP

    def test_followup_counter_increments_for_same_parent(self):
        """Test follow-up counter increments for same parent question."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q = uuid4()

        # First follow-up
        interview.ask_followup(uuid4(), parent_q)
        assert interview.current_followup_count == 1

        # Second follow-up (same parent)
        interview.answer_followup()  # Back to EVALUATING
        interview.ask_followup(uuid4(), parent_q)
        assert interview.current_followup_count == 2

        # Third follow-up (same parent)
        interview.answer_followup()
        interview.ask_followup(uuid4(), parent_q)
        assert interview.current_followup_count == 3

    def test_followup_counter_resets_on_new_parent(self):
        """Test counter resets when parent question changes."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q1 = uuid4()
        parent_q2 = uuid4()

        # Add follow-up for first parent
        interview.ask_followup(uuid4(), parent_q1)
        assert interview.current_followup_count == 1

        # Add follow-up for different parent
        interview.answer_followup()
        interview.ask_followup(uuid4(), parent_q2)
        assert interview.current_followup_count == 1  # Reset to 1
        assert interview.current_parent_question_id == parent_q2

    def test_max_followups_enforced(self):
        """Test max 3 follow-ups per question enforced."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q = uuid4()

        # Add 3 follow-ups
        for i in range(3):
            interview.ask_followup(uuid4(), parent_q)
            interview.answer_followup()

        # 4th should fail
        with pytest.raises(ValueError, match="Max 3 follow-ups"):
            interview.ask_followup(uuid4(), parent_q)

    def test_proceed_to_next_question_resets_counters(self):
        """Test counters reset when moving to next main question."""
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.EVALUATING,
            question_ids=[uuid4(), uuid4()],
            current_question_index=0,
        )
        parent_q = uuid4()

        # Add follow-ups
        interview.ask_followup(uuid4(), parent_q)
        assert interview.current_followup_count == 1

        # Proceed to next question
        interview.answer_followup()
        interview.proceed_to_next_question()

        assert interview.current_followup_count == 0
        assert interview.current_parent_question_id is None
        assert interview.status == InterviewStatus.QUESTIONING

    def test_can_ask_more_followups_true_when_less_than_three(self):
        """Test can_ask_more_followups() returns True when count < 3."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q = uuid4()

        # No follow-ups yet
        assert interview.can_ask_more_followups() is True

        # One follow-up
        interview.ask_followup(uuid4(), parent_q)
        interview.answer_followup()
        assert interview.can_ask_more_followups() is True

        # Two follow-ups
        interview.ask_followup(uuid4(), parent_q)
        interview.answer_followup()
        assert interview.can_ask_more_followups() is True

    def test_can_ask_more_followups_false_when_three(self):
        """Test can_ask_more_followups() returns False when count = 3."""
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
        parent_q = uuid4()

        # Add 3 follow-ups
        for i in range(3):
            interview.ask_followup(uuid4(), parent_q)
            interview.answer_followup()

        assert interview.can_ask_more_followups() is False


class TestExistingMethods:
    """Test existing methods still work correctly."""

    def test_start_only_works_from_idle(self):
        """Test start() only works from IDLE state."""
        # Success from IDLE
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)
        interview.start()
        assert interview.status == InterviewStatus.QUESTIONING

        # Fail from other states
        interview2 = Interview(candidate_id=uuid4(), status=InterviewStatus.PLANNING)
        with pytest.raises(ValueError, match="Cannot start interview"):
            interview2.start()

    def test_complete_only_works_from_evaluating_with_no_questions(self):
        """Test complete() validation."""
        # Success case
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.EVALUATING,
            question_ids=[uuid4()],
            current_question_index=1,
        )
        interview.complete()
        assert interview.status == InterviewStatus.COMPLETE

        # Fail from wrong state
        interview2 = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)
        with pytest.raises(ValueError, match="Cannot complete interview with status"):
            interview2.complete()

        # Fail with remaining questions
        interview3 = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.EVALUATING,
            question_ids=[uuid4(), uuid4()],
            current_question_index=0,
        )
        with pytest.raises(ValueError, match="questions remain"):
            interview3.complete()

    def test_answer_followup_only_works_from_follow_up_state(self):
        """Test answer_followup() validation."""
        # Success
        interview = Interview(candidate_id=uuid4(), status=InterviewStatus.FOLLOW_UP)
        interview.answer_followup()
        assert interview.status == InterviewStatus.EVALUATING

        # Fail from wrong state
        interview2 = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)
        with pytest.raises(ValueError, match="Not in FOLLOW_UP state"):
            interview2.answer_followup()

    def test_proceed_to_next_question_only_works_from_evaluating(self):
        """Test proceed_to_next_question() validation."""
        # Success
        interview = Interview(
            candidate_id=uuid4(),
            status=InterviewStatus.EVALUATING,
            question_ids=[uuid4(), uuid4()],
        )
        interview.proceed_to_next_question()
        assert interview.status == InterviewStatus.QUESTIONING

        # Fail from wrong state
        interview2 = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)
        with pytest.raises(ValueError, match="Cannot proceed from status"):
            interview2.proceed_to_next_question()
