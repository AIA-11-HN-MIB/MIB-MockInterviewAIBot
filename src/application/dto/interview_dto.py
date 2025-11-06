"""Interview DTOs for REST API request/response."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# Request DTOs
class CreateInterviewRequest(BaseModel):
    """Request to create a new interview session."""
    candidate_id: UUID
    cv_analysis_id: UUID
    num_questions: int = Field(default=10, ge=1, le=20)


class StartInterviewRequest(BaseModel):
    """Request to start an interview (no body needed)."""
    pass


# Response DTOs
class InterviewResponse(BaseModel):
    """Response with interview details and WebSocket URL."""
    id: UUID
    candidate_id: UUID
    status: str
    cv_analysis_id: UUID | None
    question_count: int
    current_question_index: int
    progress_percentage: float
    ws_url: str  # WebSocket URL for real-time communication
    created_at: datetime
    started_at: datetime | None

    @staticmethod
    def from_domain(interview: Any, base_url: str) -> "InterviewResponse":
        """Convert domain Interview to response DTO."""
        return InterviewResponse(
            id=interview.id,
            candidate_id=interview.candidate_id,
            status=interview.status,
            cv_analysis_id=interview.cv_analysis_id,
            question_count=len(interview.question_ids),
            current_question_index=interview.current_question_index,
            progress_percentage=interview.get_progress_percentage(),
            ws_url=f"{base_url}/ws/interviews/{interview.id}",
            created_at=interview.created_at,
            started_at=interview.started_at,
        )


class QuestionResponse(BaseModel):
    """Response with question details."""
    id: UUID
    text: str
    question_type: str
    difficulty: str
    index: int
    total: int
    is_follow_up: bool = False
    parent_question_id: UUID | None = None


# NEW: Planning DTOs
class PlanInterviewRequest(BaseModel):
    """Request to plan interview with adaptive questions."""
    cv_analysis_id: UUID
    candidate_id: UUID


class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str


class FollowUpQuestionResponse(BaseModel):
    """Response with follow-up question details."""
    id: UUID
    parent_question_id: UUID
    text: str
    generated_reason: str
    order_in_sequence: int
