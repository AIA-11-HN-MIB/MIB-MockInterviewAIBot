# Phase 05: REST/WebSocket API Integration

**Phase ID**: phase-05-api-integration
**Created**: 2025-11-06
**Status**: ⏳ Pending
**Priority**: P1 (High)
**Estimated Effort**: 8 hours

## Context

**Parent Plan**: [Main Plan](./plan.md)
**Dependencies**: [Phase 03](./phase-03-planning-use-case.md), [Phase 04](./phase-04-adaptive-evaluation.md)
**Related Docs**: [REST API](../../src/adapters/api/rest/interview_routes.py) | [WebSocket](../../src/adapters/api/websocket/interview_handler.py)

## Overview

Expose planning + adaptive evaluation via REST endpoints + WebSocket. Add POST /api/interviews/plan, update WebSocket to deliver follow-ups, modify response DTOs.

**Date**: 2025-11-06
**Description**: API layer integration for adaptive interview flow
**Priority**: P1 - Exposes new functionality to frontend
**Status**: ⏳ Pending

## Requirements

### Functional Requirements

1. **REST Endpoints**:
   - `POST /api/interviews/plan` - Trigger planning phase (async recommended)
   - `GET /api/interviews/{id}/plan` - Get plan metadata + status
   - Modify `POST /api/interviews/{id}/answers` - Use adaptive evaluation

2. **WebSocket Protocol**:
   - Server sends follow-up questions automatically after answer evaluation
   - Client receives follow-up indicator in evaluation response
   - Support for `get_followup_question` message type

3. **Response DTOs**:
   - Add plan_metadata to InterviewResponse
   - Add similarity_score, gaps, speaking_score to AnswerResponse
   - Add has_followup flag to evaluation response

## Architecture

### REST Endpoint Design

```python
# POST /api/interviews/plan
# Request:
{
  "candidate_id": "uuid",
  "cv_analysis_id": "uuid"
}

# Response (202 Accepted for async):
{
  "interview_id": "uuid",
  "status": "planning",  # PREPARING
  "message": "Interview planning in progress",
  "estimated_time_seconds": 90
}

# GET /api/interviews/{id}/plan
# Response:
{
  "interview_id": "uuid",
  "status": "ready",  # READY
  "plan_metadata": {
    "n": 8,
    "generated_at": "2025-11-06T21:42:00Z",
    "strategy": "adaptive_planning_v1",
    "cv_summary": "Mid-level Python developer..."
  },
  "question_count": 8,
  "adaptive_followups_count": 0
}
```

### WebSocket Flow Update

```
Client sends answer:
{
  "type": "text_answer",
  "question_id": "uuid",
  "answer_text": "My answer..."
}

Server evaluates + responds:
{
  "type": "evaluation",
  "answer_id": "uuid",
  "score": 75.5,
  "similarity_score": 0.72,
  "speaking_score": 85.0,
  "gaps": {
    "missing_keywords": ["polymorphism", "inheritance"],
    "coverage_percentage": 68
  },
  "feedback": "Good start, but missing key OOP concepts...",
  "has_followup": true
}

Server sends follow-up (if needed):
{
  "type": "question",
  "question_id": "uuid",
  "text": "Can you elaborate on polymorphism in Python?",
  "is_followup": true,
  "parent_question_id": "uuid",
  "index": "1a",  # Follow-up indicator
  "total": 5  # Main question count
}
```

## Related Code Files

### Files to Modify (3)

1. **src/adapters/api/rest/interview_routes.py** (+80 lines)
   - Add POST /api/interviews/plan
   - Add GET /api/interviews/{id}/plan
   - Modify answer submission to use adaptive evaluation

2. **src/adapters/api/websocket/interview_handler.py** (+50 lines)
   - Update handle_text_answer() to trigger follow-ups
   - Add send_followup_question() method

3. **src/application/dto/interview_dto.py** (+40 lines)
   - Add PlanInterviewRequest/Response
   - Update InterviewResponse with plan_metadata
   - Update AnswerResponse with adaptive fields

## Implementation Steps

### Step 1: Create Plan Endpoint (90 min)

**File**: `src/adapters/api/rest/interview_routes.py`

```python
from ..dto.plan_request_dto import PlanInterviewRequest, PlanInterviewResponse
from ...application.use_cases.plan_interview import PlanInterviewUseCase

@router.post("/interviews/plan", response_model=PlanInterviewResponse, status_code=202)
async def plan_interview(
    request: PlanInterviewRequest,
    container: Container = Depends(get_container),
    session: AsyncSession = Depends(get_async_session),
) -> PlanInterviewResponse:
    """Plan interview by generating questions with ideal answers.

    Status: 202 Accepted (planning in progress, async recommended)
    """
    logger.info("Planning interview request received")

    use_case = container.plan_interview_use_case(session)

    # For MVP: Synchronous (future: background job with Celery)
    interview = await use_case.execute(
        cv_analysis_id=request.cv_analysis_id,
        candidate_id=request.candidate_id,
    )

    return PlanInterviewResponse(
        interview_id=interview.id,
        status=interview.status.value,
        question_count=interview.planned_question_count,
        plan_metadata=interview.plan_metadata,
    )


@router.get("/interviews/{interview_id}/plan", response_model=PlanStatusResponse)
async def get_plan_status(
    interview_id: UUID,
    container: Container = Depends(get_container),
    session: AsyncSession = Depends(get_async_session),
) -> PlanStatusResponse:
    """Get interview planning status and metadata."""
    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.find_by_id(interview_id)

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    return PlanStatusResponse(
        interview_id=interview.id,
        status=interview.status.value,
        plan_metadata=interview.plan_metadata,
        question_count=len(interview.question_ids),
        adaptive_followups_count=len(interview.adaptive_follow_ups),
    )
```

### Step 2: Update WebSocket Handler (60 min)

**File**: `src/adapters/api/websocket/interview_handler.py`

```python
from ...application.use_cases.evaluate_answer_adaptive import EvaluateAnswerAdaptiveUseCase

async def handle_text_answer(self, websocket: WebSocket, data: dict):
    """Handle text answer with adaptive follow-up logic."""
    question_id = UUID(data["question_id"])
    answer_text = data["answer_text"]

    # Use adaptive evaluation
    use_case = self.container.evaluate_answer_adaptive_use_case(self.session)

    answer, has_followup = await use_case.execute(
        interview_id=self.interview_id,
        question_id=question_id,
        answer_text=answer_text,
    )

    # Send evaluation response
    await websocket.send_json({
        "type": "evaluation",
        "answer_id": str(answer.id),
        "score": answer.evaluation.score,
        "similarity_score": answer.similarity_score,
        "speaking_score": answer.speaking_score,
        "gaps": answer.gaps,
        "feedback": answer.evaluation.reasoning,
        "strengths": answer.evaluation.strengths,
        "weaknesses": answer.evaluation.weaknesses,
        "has_followup": has_followup,
    })

    # Send follow-up question if needed
    if has_followup:
        interview = await self.interview_repo.find_by_id(self.interview_id)
        followup_id = interview.adaptive_follow_ups[-1]  # Latest follow-up
        followup_q = await self.question_repo.find_by_id(followup_id)

        await websocket.send_json({
            "type": "question",
            "question_id": str(followup_q.id),
            "text": followup_q.text,
            "is_followup": True,
            "parent_question_id": str(followup_q.parent_question_id),
            "index": f"{self._get_main_question_index()}a",  # e.g., "3a"
            "total": len(interview.question_ids),
        })

    # Check if interview complete
    if not interview.has_more_questions() and not has_followup:
        await self._handle_interview_complete(websocket)
```

### Step 3: Update DTOs (45 min)

**Files**: Update existing DTOs in `src/application/dto/`

```python
# interview_dto.py
class InterviewResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    status: str
    plan_metadata: dict[str, Any] = {}  # NEW
    question_count: int
    adaptive_followups_count: int = 0  # NEW
    # ... existing fields

class PlanStatusResponse(BaseModel):
    interview_id: UUID
    status: str
    plan_metadata: dict[str, Any]
    question_count: int
    adaptive_followups_count: int

# answer_dto.py
class AnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    text: str
    score: float
    similarity_score: float | None = None  # NEW
    speaking_score: float | None = None  # NEW
    gaps: dict[str, Any] | None = None  # NEW
    feedback: str
    strengths: list[str]
    weaknesses: list[str]
    # ... existing fields
```

## Todo List

### REST Endpoints
- [ ] Create POST /api/interviews/plan endpoint
- [ ] Create GET /api/interviews/{id}/plan endpoint
- [ ] Update POST /api/interviews/{id}/answers to use adaptive evaluation
- [ ] Add 202 Accepted status for async planning
- [ ] Add error handling (404, 500)
- [ ] Add request validation (Pydantic)
- [ ] Test endpoints with curl/Postman
- [ ] Write OpenAPI docs
- [ ] Run mypy + black

### WebSocket Updates
- [ ] Update handle_text_answer() to use EvaluateAnswerAdaptiveUseCase
- [ ] Add send_followup_question() method
- [ ] Update evaluation response with adaptive fields
- [ ] Add is_followup flag to question messages
- [ ] Test WebSocket flow end-to-end
- [ ] Handle WebSocket errors gracefully
- [ ] Run mypy + black

### DTOs
- [ ] Update InterviewResponse with plan_metadata
- [ ] Create PlanStatusResponse DTO
- [ ] Update AnswerResponse with similarity/gaps/speaking
- [ ] Add validation for new fields
- [ ] Write unit tests for DTO serialization
- [ ] Run mypy + black

### Integration Testing
- [ ] Test POST /plan with real DB + LLM
- [ ] Test GET /plan status endpoint
- [ ] Test WebSocket adaptive flow with follow-ups
- [ ] Test max 3 follow-ups via WebSocket
- [ ] Test error scenarios (invalid IDs, LLM failures)
- [ ] Test backward compatibility with non-planned interviews

### Documentation
- [ ] Update API docs (Swagger/OpenAPI)
- [ ] Add examples for plan endpoint
- [ ] Document WebSocket follow-up protocol
- [ ] Update frontend integration guide

## Success Criteria

- [ ] POST /api/interviews/plan triggers planning use case
- [ ] GET /api/interviews/{id}/plan returns metadata + status
- [ ] WebSocket delivers follow-up questions automatically
- [ ] Answer responses include similarity, gaps, speaking scores
- [ ] Follow-up questions marked with is_followup=True
- [ ] API returns 202 Accepted for async planning
- [ ] OpenAPI docs updated with new endpoints
- [ ] Integration tests pass for full adaptive flow
- [ ] Backward compatible with existing interview flow

## Risk Assessment

**Medium Risks**:
- **Synchronous planning**: 90s request timeout on some hosting platforms
  - *Mitigation*: Return 202 Accepted, implement background job in Phase 2
- **WebSocket state management**: Follow-up delivery timing
  - *Mitigation*: Clear event sequence, integration tests

## Security Considerations

- Plan metadata sanitized before exposing (no internal AI strategy)
- Gaps dict validated to prevent XSS
- Rate limiting on /plan endpoint (expensive operation)

## Next Steps

1. Complete checkboxes
2. Test API locally with Postman
3. **Proceed to Phase 06**: Testing & validation

---

**Phase Status**: Ready after Phase 04
**Blocking**: Phase 06
**Owner**: API team
