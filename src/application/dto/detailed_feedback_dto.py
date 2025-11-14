"""Detailed interview feedback DTOs for comprehensive evaluation reporting.

This module provides strongly-typed DTOs for delivering detailed per-question
evaluations when an interview completes. Replaces untyped dict[str, Any] summary
with Pydantic models for type safety and validation.

Architecture:
    DetailedInterviewFeedback (root)
    └── question_feedback: list[QuestionDetailedFeedback]
        └── main_evaluation: EvaluationDetail
        └── follow_up_evaluations: list[EvaluationDetail]
            └── gaps: list[ConceptGapDetail]
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConceptGapDetail(BaseModel):
    """Detail for one missing concept in an answer.

    Extracted from domain.models.evaluation.ConceptGap for DTO serialization.

    Attributes:
        concept: Missing concept name (e.g., "event loop", "closure")
        severity: Gap severity level (minor/moderate/major)
        resolved: Whether gap was filled in follow-up attempts

    Example:
        {
            "concept": "microtask queue",
            "severity": "major",
            "resolved": true
        }
    """

    concept: str
    severity: str  # minor/moderate/major (from GapSeverity enum)
    resolved: bool


class EvaluationDetail(BaseModel):
    """Complete evaluation detail for one answer (main or follow-up).

    Contains all scoring components, LLM analysis, and gap tracking from
    domain.models.evaluation.Evaluation entity.

    Attributes:
        answer_id: UUID of answer entity
        question_id: UUID of question (main or follow-up)
        question_text: Full question text for context
        attempt_number: 1=main, 2=follow-up #1, 3=follow-up #2

        raw_score: LLM score before penalty (0-100)
        penalty: Attempt penalty (0/-5/-15 based on attempt_number)
        final_score: raw_score + penalty (0-100)
        similarity_score: Cosine similarity to ideal answer (0-1)

        completeness: How complete answer is (0-1)
        relevance: How relevant to question (0-1)
        sentiment: Candidate sentiment (confident/uncertain/nervous)
        reasoning: LLM explanation of evaluation

        strengths: List of answer strengths
        weaknesses: List of answer weaknesses
        improvement_suggestions: Concrete tips for improvement

        gaps: List of missing concepts with resolution status

        evaluated_at: Timestamp of evaluation completion

    Example:
        {
            "answer_id": "660e8400-e29b-41d4-a716-446655440001",
            "question_id": "550e8400-e29b-41d4-a716-446655440000",
            "question_text": "Explain the event loop in Node.js",
            "attempt_number": 1,
            "raw_score": 65.0,
            "penalty": 0.0,
            "final_score": 65.0,
            "similarity_score": 0.72,
            "completeness": 0.7,
            "relevance": 0.85,
            "sentiment": "uncertain",
            "reasoning": "Mentioned call stack but missed microtask queue",
            "strengths": ["Identified call stack role", "Non-blocking I/O concept"],
            "weaknesses": ["No microtask queue explanation"],
            "improvement_suggestions": ["Study microtask vs macrotask priority"],
            "gaps": [
                {"concept": "microtask queue", "severity": "major", "resolved": false}
            ],
            "evaluated_at": "2025-11-15T10:30:00Z"
        }
    """

    answer_id: UUID
    question_id: UUID
    question_text: str
    attempt_number: int = Field(ge=1, le=3)

    # Scores
    raw_score: float = Field(ge=0.0, le=100.0)
    penalty: float = Field(ge=-15.0, le=0.0)
    final_score: float = Field(ge=0.0, le=100.0)
    similarity_score: float | None = Field(None, ge=0.0, le=1.0)

    # LLM analysis
    completeness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    sentiment: str | None = None
    reasoning: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)

    # Gaps
    gaps: list[ConceptGapDetail] = Field(default_factory=list)

    # Metadata
    evaluated_at: datetime | None = None


class QuestionDetailedFeedback(BaseModel):
    """Detailed feedback for one main question with follow-up progression.

    Groups main question evaluation with follow-up evaluations to show
    candidate's learning progression across attempts.

    Attributes:
        question_id: UUID of main question
        question_text: Full main question text

        main_evaluation: Evaluation of initial answer (attempt 1)
        follow_up_evaluations: Evaluations of follow-up answers (attempts 2-3)

        score_progression: Scores across attempts [main, fu1, fu2]
        gap_filled_count: Number of gaps resolved via follow-ups

    Example:
        {
            "question_id": "550e8400-e29b-41d4-a716-446655440000",
            "question_text": "Explain the event loop in Node.js",
            "main_evaluation": { /* EvaluationDetail */ },
            "follow_up_evaluations": [
                { /* Follow-up #1 EvaluationDetail */ },
                { /* Follow-up #2 EvaluationDetail */ }
            ],
            "score_progression": [65.0, 70.0, 80.0],
            "gap_filled_count": 2
        }
    """

    question_id: UUID
    question_text: str

    # Evaluations
    main_evaluation: EvaluationDetail
    follow_up_evaluations: list[EvaluationDetail] = Field(default_factory=list)

    # Progression summary
    score_progression: list[float] = Field(
        default_factory=list,
        description="Final scores across attempts [main, fu1, fu2]",
    )
    gap_filled_count: int = Field(
        ge=0,
        default=0,
        description="Count of gaps resolved through follow-ups",
    )


class DetailedInterviewFeedback(BaseModel):
    """Complete detailed feedback for interview completion.

    Root DTO replacing dict[str, Any] summary with strongly-typed structure.
    Includes aggregate metrics, per-question detailed feedback, and
    interview-wide analysis.

    Attributes:
        interview_id: UUID of completed interview

        overall_score: Weighted average (70% theoretical + 30% speaking)
        theoretical_score_avg: Average of all final_scores
        speaking_score_avg: Average of voice quality metrics

        total_questions: Count of main questions
        total_follow_ups: Count of follow-up questions

        question_feedback: Detailed feedback per main question

        gap_progression: Interview-wide gap analysis
            - questions_with_followups: int
            - gaps_filled: int
            - gaps_remaining: int
            - avg_followups_per_question: float

        strengths: Top 3-5 candidate strengths (LLM-generated)
        weaknesses: Top 3-5 candidate weaknesses (LLM-generated)
        study_recommendations: Topic-specific study suggestions
        technique_tips: Interview technique improvements

        completion_time: ISO timestamp of completion

    Example:
        {
            "interview_id": "110e8400-e29b-41d4-a716-446655440000",
            "overall_score": 72.5,
            "theoretical_score_avg": 68.0,
            "speaking_score_avg": 55.0,
            "total_questions": 5,
            "total_follow_ups": 7,
            "question_feedback": [ /* 5 QuestionDetailedFeedback objects */ ],
            "gap_progression": {
                "questions_with_followups": 4,
                "gaps_filled": 6,
                "gaps_remaining": 3,
                "avg_followups_per_question": 1.75
            },
            "strengths": ["Strong async patterns understanding"],
            "weaknesses": ["Needs more concrete examples"],
            "study_recommendations": ["Review event loop phases"],
            "technique_tips": ["Structure answers before speaking"],
            "completion_time": "2025-11-15T10:45:00Z"
        }
    """

    interview_id: UUID

    # Aggregate metrics
    overall_score: float = Field(ge=0.0, le=100.0)
    theoretical_score_avg: float = Field(ge=0.0, le=100.0)
    speaking_score_avg: float = Field(ge=0.0, le=100.0)

    # Counts
    total_questions: int = Field(ge=0)
    total_follow_ups: int = Field(ge=0)

    # Per-question detailed feedback
    question_feedback: list[QuestionDetailedFeedback] = Field(default_factory=list)

    # Interview-wide analysis
    gap_progression: dict[str, int | float] = Field(
        default_factory=dict,
        description="Keys: questions_with_followups, gaps_filled, gaps_remaining, avg_followups_per_question",
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    study_recommendations: list[str] = Field(default_factory=list)
    technique_tips: list[str] = Field(default_factory=list)

    # Metadata
    completion_time: datetime
