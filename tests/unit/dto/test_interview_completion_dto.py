"""Tests for InterviewCompletionResult DTO."""

from uuid import uuid4

from src.application.dto.interview_completion_dto import InterviewCompletionResult
from src.domain.models.interview import Interview, InterviewStatus


class TestInterviewCompletionResult:
    """Test InterviewCompletionResult DTO."""

    def test_instantiation(self):
        """Test creating InterviewCompletionResult."""
        interview = Interview(
            id=uuid4(),
            candidate_id=uuid4(),
            status=InterviewStatus.COMPLETE,
        )
        summary = {
            "interview_id": str(interview.id),
            "overall_score": 85.5,
            "strengths": ["Good communication"],
            "weaknesses": ["Needs more practice"],
        }

        result = InterviewCompletionResult(interview=interview, summary=summary)

        assert result.interview == interview
        assert result.summary == summary

    def test_to_dict_serialization(self):
        """Test to_dict() produces correct structure."""
        interview_id = uuid4()
        interview = Interview(
            id=interview_id,
            candidate_id=uuid4(),
            status=InterviewStatus.COMPLETE,
        )
        summary = {
            "interview_id": str(interview_id),
            "overall_score": 75.0,
            "theoretical_score_avg": 80.0,
            "speaking_score_avg": 65.0,
            "total_questions": 5,
            "total_follow_ups": 2,
        }

        result = InterviewCompletionResult(interview=interview, summary=summary)
        data = result.to_dict()

        assert data["interview_id"] == str(interview_id)
        assert data["status"] == "COMPLETE"
        assert data["summary"] == summary
        assert data["summary"]["overall_score"] == 75.0

    def test_with_comprehensive_summary(self):
        """Test with full summary structure."""
        interview = Interview(
            id=uuid4(),
            candidate_id=uuid4(),
            status=InterviewStatus.COMPLETE,
        )
        summary = {
            "interview_id": str(interview.id),
            "overall_score": 88.0,
            "theoretical_score_avg": 90.0,
            "speaking_score_avg": 84.0,
            "total_questions": 3,
            "total_follow_ups": 1,
            "question_summaries": [
                {
                    "question_id": str(uuid4()),
                    "question_text": "What is Python?",
                    "main_answer_score": 85.0,
                    "follow_up_count": 0,
                }
            ],
            "gap_progression": {
                "questions_with_followups": 1,
                "gaps_filled": 2,
                "gaps_remaining": 0,
                "avg_followups_per_question": 1.0,
            },
            "strengths": ["Clear explanations", "Good examples"],
            "weaknesses": ["Could improve depth"],
            "study_recommendations": ["Study advanced Python features"],
            "technique_tips": ["Slow down when explaining"],
            "completion_time": "2025-11-14T15:30:00Z",
        }

        result = InterviewCompletionResult(interview=interview, summary=summary)

        assert len(result.summary["question_summaries"]) == 1
        assert result.summary["gap_progression"]["gaps_filled"] == 2
        assert len(result.summary["strengths"]) == 2
        assert result.summary["completion_time"] == "2025-11-14T15:30:00Z"
