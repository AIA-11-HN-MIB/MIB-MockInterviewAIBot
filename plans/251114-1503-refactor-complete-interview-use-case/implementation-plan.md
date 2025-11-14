# Refactor "Complete Interview" Use Case - Implementation Plan

**Created**: 2025-11-14 15:03
**Author**: AI Planning Agent
**Status**: Draft - Pending User Review
**Complexity**: Medium (3-4 hours)
**Risk Level**: Low-Medium

---

## Executive Summary

Merge `CompleteInterviewUseCase` and `GenerateSummaryUseCase` into single cohesive use case that handles both interview completion state transition and comprehensive summary generation. Eliminates use case composition anti-pattern, reduces optional dependencies, simplifies API surface.

**Key Goals**:
- Single responsibility: Complete interview + generate summary (atomic operation)
- Remove 5 optional dependencies (`| None = None`) - all required
- Simplify API: `execute(interview_id)` always generates summary
- Optional polling endpoint: `GET /interviews/{id}/summary` for reconnect scenarios
- Maintain WebSocket as primary completion mechanism

---

## Current Architecture Issues

### 1. Use Case Composition Anti-Pattern
```python
# CompleteInterviewUseCase internally calls GenerateSummaryUseCase
summary_use_case = GenerateSummaryUseCase(...)
summary = await summary_use_case.execute(interview_id)
```

**Problem**: Use cases should not compose other use cases. This creates:
- Hidden dependencies (GenerateSummaryUseCase not in constructor)
- Difficult to test (nested instantiation)
- Unclear dependency graph
- Violates Single Responsibility Principle

### 2. Optional Dependencies Pattern
```python
def __init__(
    self,
    interview_repository: InterviewRepositoryPort,
    answer_repository: AnswerRepositoryPort | None = None,  # Optional
    question_repository: QuestionRepositoryPort | None = None,  # Optional
    follow_up_question_repository: FollowUpQuestionRepositoryPort | None = None,  # Optional
    evaluation_repository: EvaluationRepositoryPort | None = None,  # Optional
    llm: LLMPort | None = None,  # Optional
):
```

**Problem**: 5/6 dependencies optional leads to:
- Complex conditional logic (if self.answer_repo and self.question_repo and ...)
- Multiple execution paths (with summary vs without)
- Hard to reason about behavior
- Encourages partial construction

### 3. Confusing API Surface
```python
# User must specify flag to get summary
interview, summary = await use_case.execute(interview_id, generate_summary=True)
```

**Problem**:
- `generate_summary=True` flag creates choice (should always generate)
- Two return types: `(Interview, dict | None)` - None case never desired
- Caller must check `if summary is not None` before using

### 4. Two Separate Use Cases for Related Work
- **CompleteInterviewUseCase**: 89 lines, state transition + optional summary call
- **GenerateSummaryUseCase**: 392 lines, comprehensive summary logic

**Problem**:
- Related work split across files
- Code duplication (both load interview, both use same repos)
- Artificial boundary (completion always needs summary)

---

## Proposed Architecture

### Single Unified Use Case
```python
class CompleteInterviewUseCase:
    """Complete interview and generate comprehensive summary (atomic operation)."""

    def __init__(
        self,
        interview_repository: InterviewRepositoryPort,
        answer_repository: AnswerRepositoryPort,
        question_repository: QuestionRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
        evaluation_repository: EvaluationRepositoryPort,
        llm: LLMPort,
    ):
        # All dependencies required (no | None)
        self.interview_repo = interview_repository
        self.answer_repo = answer_repository
        self.question_repo = question_repository
        self.follow_up_repo = follow_up_question_repository
        self.evaluation_repo = evaluation_repository
        self.llm = llm

    async def execute(self, interview_id: UUID) -> InterviewCompletionResult:
        """Complete interview and generate summary.

        Returns:
            InterviewCompletionResult with interview + summary (always both)

        Raises:
            ValueError: If interview not found or invalid state
        """
        # 1. Validate interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.EVALUATING:
            raise ValueError(f"Cannot complete interview with status: {interview.status}")

        # 2. Generate comprehensive summary (inline, not delegated)
        summary = await self._generate_summary(interview)

        # 3. Store summary in interview metadata
        if interview.plan_metadata is None:
            interview.plan_metadata = {}
        interview.plan_metadata["completion_summary"] = summary

        # 4. Mark interview as complete (state transition)
        interview.complete()
        updated_interview = await self.interview_repo.update(interview)

        # 5. Return result DTO
        return InterviewCompletionResult(
            interview=updated_interview,
            summary=summary,
        )

    async def _generate_summary(self, interview: Interview) -> dict[str, Any]:
        """Generate comprehensive summary (moved from GenerateSummaryUseCase)."""
        # All logic from GenerateSummaryUseCase.execute() inlined here
        # (see detailed implementation section below)
```

### New Result DTO
```python
@dataclass
class InterviewCompletionResult:
    """Result of interview completion."""
    interview: Interview
    summary: dict[str, Any]  # Always present (never None)
```

**Benefits**:
- ✅ Single atomic operation (completion + summary)
- ✅ All dependencies required (clear contract)
- ✅ Simplified API: `execute(interview_id)` always returns both
- ✅ No conditional logic for summary generation
- ✅ Testability: All paths fully deterministic

---

## Implementation Steps

### Phase 1: Preparation (No Breaking Changes)

#### Step 1.1: Create New Result DTO
**File**: `src/application/dto/interview_completion_dto.py` (NEW)

```python
"""Interview completion result DTO."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ...domain.models.interview import Interview


@dataclass
class InterviewCompletionResult:
    """Result of interview completion with summary.

    Attributes:
        interview: Completed interview entity
        summary: Comprehensive interview summary dict
    """
    interview: Interview
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "interview_id": str(self.interview.id),
            "status": self.interview.status.value,
            "summary": self.summary,
        }
```

**Tests**: `tests/unit/dto/test_interview_completion_dto.py` (NEW)
- Test instantiation
- Test to_dict() serialization
- Test with real Interview + summary objects

---

#### Step 1.2: Refactor CompleteInterviewUseCase (Inline GenerateSummaryUseCase)
**File**: `src/application/use_cases/complete_interview.py` (MODIFY)

**Changes**:
1. **Remove optional dependencies** - all required:
   ```python
   def __init__(
       self,
       interview_repository: InterviewRepositoryPort,
       answer_repository: AnswerRepositoryPort,  # No | None
       question_repository: QuestionRepositoryPort,  # No | None
       follow_up_question_repository: FollowUpQuestionRepositoryPort,  # No | None
       evaluation_repository: EvaluationRepositoryPort,  # No | None
       llm: LLMPort,  # No | None
   ):
   ```

2. **Remove generate_summary flag** - always generate:
   ```python
   async def execute(self, interview_id: UUID) -> InterviewCompletionResult:
   ```

3. **Inline summary generation logic**:
   - Move all private methods from `GenerateSummaryUseCase` into `CompleteInterviewUseCase`
   - Methods to move:
     - `_group_answers_by_main_question()`
     - `_load_evaluations()`
     - `_calculate_aggregate_metrics()`
     - `_analyze_gap_progression()`
     - `_generate_recommendations()`
     - `_create_question_summaries()`

4. **Remove GenerateSummaryUseCase instantiation**:
   ```python
   # OLD (REMOVE):
   summary_use_case = GenerateSummaryUseCase(...)
   summary = await summary_use_case.execute(interview_id)

   # NEW (INLINE):
   summary = await self._generate_summary(interview)
   ```

5. **Return new DTO**:
   ```python
   return InterviewCompletionResult(
       interview=updated_interview,
       summary=summary,
   )
   ```

**Estimated LOC**: ~450 lines (89 existing + 360 from GenerateSummaryUseCase - 20 removed boilerplate)

---

#### Step 1.3: Deprecate GenerateSummaryUseCase
**File**: `src/application/use_cases/generate_summary.py` (DEPRECATE)

**Changes**:
1. Add deprecation warning to class docstring:
   ```python
   """Generate comprehensive interview summary.

   DEPRECATED: This use case is deprecated. Use CompleteInterviewUseCase instead.
   Will be removed in next major version.

   Reason: Summary generation now integrated into interview completion (atomic operation).
   Migration: Replace GenerateSummaryUseCase with CompleteInterviewUseCase.
   """
   ```

2. Add runtime deprecation warning:
   ```python
   def __init__(self, ...):
       import warnings
       warnings.warn(
           "GenerateSummaryUseCase is deprecated. Use CompleteInterviewUseCase instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       # ... existing code
   ```

**Rationale**: Gradual deprecation allows external consumers to migrate before removal.

---

### Phase 2: Update Integration Points

#### Step 2.1: Update WebSocket Session Orchestrator
**File**: `src/adapters/api/websocket/session_orchestrator.py` (MODIFY)

**Current code** (lines 500-584):
```python
async def _complete_interview(
    self,
    interview_repo: InterviewRepositoryPort,
    answer_repo: AnswerRepositoryPort | None,
    question_repo: QuestionRepositoryPort | None = None,
    follow_up_repo: FollowUpQuestionRepositoryPort | None = None,
    evaluation_repo: EvaluationRepositoryPort | None = None,
) -> None:
    # ...
    complete_use_case = CompleteInterviewUseCase(
        interview_repository=interview_repo,
        answer_repository=answer_repo,  # Optional
        question_repository=question_repo,  # Optional
        follow_up_question_repository=follow_up_repo,  # Optional
        evaluation_repository=evaluation_repo,  # Optional
        llm=llm,  # Optional
    )
    interview, summary = await complete_use_case.execute(
        self.interview_id, generate_summary=True  # Flag removed
    )

    # Send summary message
    if summary:  # Always present now
        await self._send_message({...})
    else:  # Remove fallback
        # Fallback if summary generation failed
        # ...
```

**New code**:
```python
async def _complete_interview(
    self,
    interview_repo: InterviewRepositoryPort,
    answer_repo: AnswerRepositoryPort,  # Required
    question_repo: QuestionRepositoryPort,  # Required
    follow_up_repo: FollowUpQuestionRepositoryPort,  # Required
    evaluation_repo: EvaluationRepositoryPort,  # Required
) -> None:
    """Complete interview using domain methods, generate summary, send results."""

    llm = self.container.llm_port()

    complete_use_case = CompleteInterviewUseCase(
        interview_repository=interview_repo,
        answer_repository=answer_repo,
        question_repository=question_repo,
        follow_up_question_repository=follow_up_repo,
        evaluation_repository=evaluation_repo,
        llm=llm,
    )

    # Execute (always returns both interview + summary)
    result = await complete_use_case.execute(self.interview_id)

    # Send summary message (always present)
    await self._send_message(
        {
            "type": "interview_complete",
            "interview_id": str(result.interview.id),
            "overall_score": result.summary["overall_score"],
            "theoretical_score_avg": result.summary["theoretical_score_avg"],
            "speaking_score_avg": result.summary["speaking_score_avg"],
            "total_questions": result.summary["total_questions"],
            "total_follow_ups": result.summary["total_follow_ups"],
            "gap_progression": result.summary["gap_progression"],
            "strengths": result.summary["strengths"],
            "weaknesses": result.summary["weaknesses"],
            "study_recommendations": result.summary["study_recommendations"],
            "technique_tips": result.summary["technique_tips"],
            "completion_time": result.summary["completion_time"],
            "feedback_url": f"/api/interviews/{self.interview_id}/summary",  # New endpoint
        }
    )

    logger.info(f"Interview {self.interview_id} completed with summary")
```

**Changes**:
- Remove `| None` from all repository parameters
- Remove `generate_summary=True` flag
- Use `result.interview` and `result.summary` instead of tuple unpacking
- Remove fallback `else` block (summary always present)
- Update `feedback_url` to new polling endpoint (see Step 2.2)

**Callers to update** (3 locations in same file):
- Line 251: `await self._complete_interview(...)`
- Line 344: `await self._complete_interview(...)`
- Line 466: `await self._complete_interview(interview_repo, None, None, None, None)`

**Update line 466** (timeout handler):
```python
# OLD: Pass None for optional dependencies
await self._complete_interview(interview_repo, None, None, None, None)

# NEW: Load all required dependencies from container
async for session in get_async_session():
    interview_repo = self.container.interview_repository_port(session)
    answer_repo = self.container.answer_repository_port(session)
    question_repo = self.container.question_repository_port(session)
    follow_up_repo = self.container.follow_up_question_repository_port(session)
    evaluation_repo = self.container.evaluation_repository_port(session)

    await self._complete_interview(
        interview_repo,
        answer_repo,
        question_repo,
        follow_up_repo,
        evaluation_repo,
    )
```

---

#### Step 2.2: Add Polling Endpoint (Optional - Reconnect Scenario)
**File**: `src/adapters/api/rest/interview_routes.py` (MODIFY)

**Add new endpoint**:
```python
@router.get(
    "/{interview_id}/summary",
    response_model=InterviewSummaryResponse,
    summary="Get interview summary",
)
async def get_interview_summary(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get comprehensive interview summary.

    Use case: Client reconnects after WebSocket disconnect and needs summary.

    Args:
        interview_id: Interview UUID
        session: Database session

    Returns:
        Interview summary with all metrics and recommendations

    Raises:
        HTTPException: If interview not found or not completed
    """
    container = get_container()
    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    if interview.status != InterviewStatus.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview not completed (status: {interview.status.value})",
        )

    # Extract summary from metadata
    summary = interview.plan_metadata.get("completion_summary") if interview.plan_metadata else None

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found (interview completed without summary generation)",
        )

    return InterviewSummaryResponse(**summary)
```

**Create response DTO**:
**File**: `src/application/dto/interview_dto.py` (MODIFY)

```python
class InterviewSummaryResponse(BaseModel):
    """Interview summary response."""
    interview_id: str
    overall_score: float
    theoretical_score_avg: float
    speaking_score_avg: float
    total_questions: int
    total_follow_ups: int
    question_summaries: list[dict[str, Any]]
    gap_progression: dict[str, Any]
    strengths: list[str]
    weaknesses: list[str]
    study_recommendations: list[str]
    technique_tips: list[str]
    completion_time: str
```

**Benefits**:
- ✅ Clients can retrieve summary via REST if WebSocket disconnects
- ✅ Stateless polling (no session needed)
- ✅ Idempotent (GET request, safe to retry)
- ✅ No additional computation (reads from metadata)

---

### Phase 3: Update Tests

#### Step 3.1: Update CompleteInterviewUseCase Tests
**File**: `tests/unit/use_cases/test_complete_interview.py` (MODIFY)

**Changes**:
1. Remove all optional dependency tests:
   - `test_complete_interview_without_summary_generation` (DELETE)
   - `test_complete_interview_missing_dependencies` (DELETE)

2. Update all test signatures to require all dependencies:
   ```python
   async def test_complete_interview_with_summary_generation(
       self,
       sample_interview_adaptive,
       sample_question_with_ideal_answer,
       mock_interview_repo,
       mock_answer_repo,
       mock_question_repo,
       mock_follow_up_question_repo,
       mock_evaluation_repo,  # Always required
       mock_llm,  # Always required
   ):
   ```

3. Update assertions to use new DTO:
   ```python
   # OLD:
   interview, summary = await use_case.execute(interview_id, generate_summary=True)
   assert summary is not None

   # NEW:
   result = await use_case.execute(interview_id)
   assert result.interview.status == InterviewStatus.COMPLETE
   assert result.summary["overall_score"] > 0.0
   ```

4. Add tests for inlined summary generation:
   - `test_complete_interview_summary_metrics_calculated`
   - `test_complete_interview_gap_progression_analyzed`
   - `test_complete_interview_llm_recommendations_generated`

**Tests to keep** (update for new API):
- `test_complete_interview_not_found`
- `test_complete_interview_invalid_status`
- `test_complete_interview_initializes_metadata`
- `test_complete_interview_preserves_existing_metadata`
- `test_complete_flow_with_multiple_answers`

**Estimated changes**: ~15 test methods, ~300 lines modified

---

#### Step 3.2: Keep GenerateSummaryUseCase Tests (Deprecated but Tested)
**File**: `tests/unit/use_cases/test_generate_summary.py` (NO CHANGE)

**Rationale**: Keep tests to ensure backward compatibility during deprecation period.

---

#### Step 3.3: Update Session Orchestrator Tests
**File**: `tests/unit/websocket/test_session_orchestrator.py` (MODIFY if exists)

**Changes**:
- Update `_complete_interview` call sites to pass all required dependencies
- Update assertions to use `InterviewCompletionResult`

---

#### Step 3.4: Add Integration Test for Polling Endpoint
**File**: `tests/integration/api/test_interview_routes.py` (MODIFY)

```python
@pytest.mark.asyncio
async def test_get_interview_summary_success(
    client: AsyncClient,
    completed_interview_with_summary,
):
    """Test GET /interviews/{id}/summary returns summary."""
    response = await client.get(f"/api/interviews/{completed_interview_with_summary.id}/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["interview_id"] == str(completed_interview_with_summary.id)
    assert "overall_score" in summary
    assert "strengths" in summary

@pytest.mark.asyncio
async def test_get_interview_summary_not_completed(
    client: AsyncClient,
    in_progress_interview,
):
    """Test GET /interviews/{id}/summary returns 400 if not completed."""
    response = await client.get(f"/api/interviews/{in_progress_interview.id}/summary")

    assert response.status_code == 400
    assert "not completed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_interview_summary_not_found(client: AsyncClient):
    """Test GET /interviews/{id}/summary returns 404 if interview not found."""
    response = await client.get(f"/api/interviews/{uuid4()}/summary")

    assert response.status_code == 404
```

---

### Phase 4: Cleanup (Next Major Version)

#### Step 4.1: Remove GenerateSummaryUseCase
**Files to delete**:
- `src/application/use_cases/generate_summary.py`
- `tests/unit/use_cases/test_generate_summary.py`

**Reason**: After deprecation period (1-2 releases), remove completely.

---

## Error Handling Strategy

### 1. Validation Errors
**Scenario**: Interview not found, invalid state

**Current behavior**: `ValueError` raised, caught in WebSocket handler

**New behavior**: Same (no change)

```python
# CompleteInterviewUseCase.execute()
if not interview:
    raise ValueError(f"Interview {interview_id} not found")

if interview.status != InterviewStatus.EVALUATING:
    raise ValueError(f"Cannot complete interview with status: {interview.status}")
```

**WebSocket handling** (no change needed):
```python
# session_orchestrator.py
try:
    result = await complete_use_case.execute(interview_id)
except ValueError as e:
    await self._send_error("INVALID_STATE", str(e))
    return
```

---

### 2. Summary Generation Failures
**Scenario**: LLM API timeout, database query fails during summary generation

**Current behavior**: Exception propagates, summary returns `None`, fallback message sent

**New behavior**: **No fallback** - exception propagates, interview NOT marked complete

**Rationale**:
- Summary generation is part of completion contract (atomic operation)
- If summary fails, completion fails (transaction rolled back)
- Client sees error, can retry later
- Prevents partial state (completed interview without summary)

**Implementation**:
```python
# CompleteInterviewUseCase.execute()
try:
    summary = await self._generate_summary(interview)
except Exception as e:
    logger.error(f"Summary generation failed: {e}", exc_info=True)
    raise  # Propagate to caller (transaction rollback)

# State transition only happens if summary succeeds
interview.complete()
await self.interview_repo.update(interview)
```

**WebSocket error handling**:
```python
# session_orchestrator.py
try:
    result = await complete_use_case.execute(interview_id)
except Exception as e:
    logger.error(f"Interview completion failed: {e}", exc_info=True)
    await self._send_error(
        "COMPLETION_FAILED",
        "Failed to complete interview. Please try again later.",
    )
    return
```

**Trade-off**:
- ❌ Completion can fail due to summary generation issues
- ✅ No partial state (interview always has summary if completed)
- ✅ Idempotent retry (client can reconnect and retry)
- ✅ Clear error message

**Mitigation**:
- Add retry logic with exponential backoff for LLM calls
- Use database transactions (rollback if summary fails)
- Monitor error rates (alert if >5% failures)

---

### 3. Database Transaction Consistency
**Scenario**: Summary generated successfully, but update fails

**Solution**: Wrap in transaction
```python
async def execute(self, interview_id: UUID) -> InterviewCompletionResult:
    async with self.interview_repo.transaction():  # If supported
        interview = await self.interview_repo.get_by_id(interview_id)
        # ... validation

        summary = await self._generate_summary(interview)

        interview.plan_metadata = interview.plan_metadata or {}
        interview.plan_metadata["completion_summary"] = summary

        interview.complete()
        updated = await self.interview_repo.update(interview)

        return InterviewCompletionResult(interview=updated, summary=summary)
```

**Note**: If repository doesn't support transactions, rely on database-level ACID properties.

---

## Edge Cases

### 1. Interview Already Completed
**Scenario**: Client calls `complete_interview` twice

**Current behavior**: Raises `ValueError` (invalid state)

**New behavior**: Same

**Test**:
```python
@pytest.mark.asyncio
async def test_complete_interview_already_completed(
    completed_interview,
    mock_interview_repo,
    # ... all required deps
):
    use_case = CompleteInterviewUseCase(...)

    with pytest.raises(ValueError, match="Cannot complete interview with status: complete"):
        await use_case.execute(completed_interview.id)
```

---

### 2. No Answers Submitted
**Scenario**: Interview started but no answers submitted

**Current behavior**: Summary generated with 0.0 scores

**New behavior**: Same

**Rationale**: Valid scenario (candidate abandoned interview)

**Summary output**:
```json
{
  "overall_score": 0.0,
  "theoretical_score_avg": 0.0,
  "speaking_score_avg": 0.0,
  "total_questions": 3,
  "total_follow_ups": 0,
  "gap_progression": {"questions_with_followups": 0, ...},
  "strengths": [],
  "weaknesses": [],
  "study_recommendations": [],
  "technique_tips": []
}
```

---

### 3. Partial Answers (Some Questions Unanswered)
**Scenario**: Candidate answered 2/5 questions

**Current behavior**: Summary includes only answered questions

**New behavior**: Same

**Rationale**: Summary reflects actual performance

---

### 4. Summary Metadata Already Exists
**Scenario**: Interview metadata already contains `completion_summary`

**Current behavior**: Overwrites existing summary

**New behavior**: Same (idempotent)

**Rationale**: Latest completion overwrites previous (should never happen in normal flow)

**Test**:
```python
@pytest.mark.asyncio
async def test_complete_interview_overwrites_existing_summary(
    sample_interview_adaptive,
    # ... all deps
):
    # Setup interview with existing summary
    sample_interview_adaptive.plan_metadata = {
        "completion_summary": {"overall_score": 50.0, "outdated": True}
    }

    use_case = CompleteInterviewUseCase(...)
    result = await use_case.execute(sample_interview_adaptive.id)

    # Verify new summary replaced old
    assert result.summary["overall_score"] != 50.0
    assert "outdated" not in result.summary
```

---

## Testing Strategy

### Unit Tests (95%+ Coverage Target)

#### CompleteInterviewUseCase
**File**: `tests/unit/use_cases/test_complete_interview.py`

**Test cases** (15 total):
1. ✅ Happy path: Complete interview with multiple evaluated answers
2. ✅ Summary metrics calculated correctly (70% theoretical + 30% speaking)
3. ✅ Gap progression analyzed (initial gaps → final gaps)
4. ✅ LLM recommendations generated
5. ✅ Interview not found → ValueError
6. ✅ Invalid status (IDLE, QUESTIONING, COMPLETE) → ValueError
7. ✅ Metadata initialized if None
8. ✅ Metadata preserved if exists (custom fields retained)
9. ✅ No answers submitted → 0.0 scores, empty recommendations
10. ✅ No follow-ups → gap_progression shows 0
11. ✅ No voice metrics → speaking_score defaults to 50.0
12. ✅ Missing evaluation data → handles gracefully
13. ✅ Summary stored in interview metadata
14. ✅ Returns InterviewCompletionResult DTO
15. ✅ Multiple follow-ups tracked correctly

**Mocks required**:
- `mock_interview_repo`
- `mock_answer_repo`
- `mock_question_repo`
- `mock_follow_up_question_repo`
- `mock_evaluation_repo`
- `mock_llm`

---

#### Session Orchestrator
**File**: `tests/unit/websocket/test_session_orchestrator.py`

**Test cases** (5 new/updated):
1. ✅ `_complete_interview` calls CompleteInterviewUseCase with all deps
2. ✅ Summary message sent via WebSocket
3. ✅ Completion error handled gracefully
4. ✅ Timeout scenario passes all required dependencies
5. ✅ Result DTO fields mapped to WebSocket message correctly

---

#### REST API Polling Endpoint
**File**: `tests/integration/api/test_interview_routes.py`

**Test cases** (4 new):
1. ✅ GET /interviews/{id}/summary returns 200 + summary (completed interview)
2. ✅ GET /interviews/{id}/summary returns 404 (interview not found)
3. ✅ GET /interviews/{id}/summary returns 400 (interview not completed)
4. ✅ GET /interviews/{id}/summary returns 404 (summary not in metadata)

---

### Integration Tests

#### End-to-End Interview Flow
**File**: `tests/e2e/test_interview_completion.py` (NEW)

**Scenario**: Full interview flow via WebSocket
1. Start interview (WebSocket connect)
2. Answer all questions
3. Receive `interview_complete` message
4. Verify summary in message
5. GET /interviews/{id}/summary (polling endpoint)
6. Verify summary matches WebSocket message

---

## Migration Checklist

### Pre-Deployment
- [ ] All unit tests passing (95%+ coverage)
- [ ] All integration tests passing
- [ ] Code review approved (2+ reviewers)
- [ ] Documentation updated (API docs, architecture docs)
- [ ] Deprecation warnings added to GenerateSummaryUseCase
- [ ] Migration guide written (for external consumers)

### Deployment
- [ ] Deploy to staging environment
- [ ] Run smoke tests (end-to-end interview completion)
- [ ] Monitor error rates (<1% failure rate)
- [ ] Verify WebSocket completion messages include summary
- [ ] Verify polling endpoint `/interviews/{id}/summary` works

### Post-Deployment
- [ ] Monitor production metrics (completion rate, error rate)
- [ ] No increase in failure rates (baseline: 0.5%)
- [ ] WebSocket reconnect scenarios tested
- [ ] Client feedback collected (frontend team)

### Deprecation Period (1-2 Releases)
- [ ] Announce deprecation in release notes
- [ ] Monitor usage of GenerateSummaryUseCase (should be 0)
- [ ] Plan removal for next major version

### Final Cleanup
- [ ] Remove GenerateSummaryUseCase
- [ ] Remove tests for GenerateSummaryUseCase
- [ ] Update all references in documentation

---

## Rollback Plan

### If Critical Bugs Found
1. **Revert commit** (git revert)
2. **Redeploy previous version**
3. **Restore GenerateSummaryUseCase** (undeprecate)
4. **Fix bugs in separate branch**
5. **Re-test and redeploy**

### Rollback triggers:
- Completion failure rate >5%
- Summary generation failures >10%
- Client-reported missing summaries
- Database corruption

---

## Risks & Mitigation

### Risk 1: LLM API Failures Block Completion
**Probability**: Medium
**Impact**: High (interviews cannot complete)

**Mitigation**:
- Retry logic with exponential backoff (3 retries)
- Circuit breaker pattern (fail fast if LLM down)
- Fallback: Store minimal summary without LLM recommendations
- Monitoring: Alert if LLM failure rate >5%

---

### Risk 2: Database Transaction Rollback
**Probability**: Low
**Impact**: Medium (interview not completed, client retries)

**Mitigation**:
- Use database transactions (rollback on failure)
- Idempotent retry (client can retry safely)
- Monitor rollback rate (<1% acceptable)

---

### Risk 3: Breaking Change for External Consumers
**Probability**: Low (no external consumers identified)
**Impact**: Medium (if they exist)

**Mitigation**:
- Deprecation period (1-2 releases)
- Migration guide in CHANGELOG
- Backward compatibility (keep GenerateSummaryUseCase temporarily)

---

### Risk 4: Increased Latency (Summary Blocks Completion)
**Probability**: Low
**Impact**: Low (acceptable trade-off)

**Mitigation**:
- Profile summary generation (target <2s p95)
- Optimize LLM call (parallel requests if possible)
- Monitor latency (alert if >5s p95)

**Baseline latency**: ~1-3 seconds (LLM call + DB queries)

---

## Performance Considerations

### Current Performance
- **CompleteInterviewUseCase**: ~50ms (state transition only)
- **GenerateSummaryUseCase**: ~1-3s (LLM call + aggregation)
- **Total**: ~1-3.05s (sequential)

### New Performance
- **CompleteInterviewUseCase** (unified): ~1-3s (inlined summary)
- **Total**: ~1-3s (same, but atomic)

**Optimization opportunities**:
1. Parallel LLM calls (recommendations generation)
2. Database query batching (fetch all evaluations in 1 query)
3. Caching (completed interview summaries)

**Target SLA**: <3s p95 (acceptable for interview completion)

---

## Acceptance Criteria

### Functional Requirements
- ✅ CompleteInterviewUseCase always generates summary (no optional flag)
- ✅ All dependencies required (no `| None`)
- ✅ Returns `InterviewCompletionResult` DTO with interview + summary
- ✅ WebSocket sends `interview_complete` message with full summary
- ✅ Polling endpoint `GET /interviews/{id}/summary` works
- ✅ Summary stored in `interview.plan_metadata["completion_summary"]`
- ✅ GenerateSummaryUseCase deprecated (warning logged)

### Non-Functional Requirements
- ✅ Test coverage ≥95% (CompleteInterviewUseCase)
- ✅ Completion latency <3s (p95)
- ✅ Error rate <1% (production)
- ✅ No breaking changes (backward compatible via deprecation)
- ✅ Code review approved (2+ reviewers)
- ✅ Documentation updated (API docs, architecture)

### Edge Cases Handled
- ✅ Interview not found → ValueError
- ✅ Invalid status → ValueError
- ✅ No answers → 0.0 scores
- ✅ No voice metrics → speaking_score=50.0
- ✅ Summary generation failure → transaction rollback
- ✅ Retry idempotent (overwrite existing summary)

---

## Open Questions

1. **Should polling endpoint support partial summaries?**
   - **Context**: If summary generation failed, should endpoint return partial data?
   - **Recommendation**: No - return 404 if summary missing (KISS principle)

2. **Should we add summary caching?**
   - **Context**: Completed interview summaries never change
   - **Recommendation**: Not in MVP - add if performance issues arise

3. **Should GenerateSummaryUseCase removal be in minor or major version?**
   - **Context**: Semantic versioning (breaking change = major version)
   - **Recommendation**: Major version (v1.0.0 → v2.0.0)

4. **Should we support re-generating summaries?**
   - **Context**: If LLM recommendations improve, re-run summary generation
   - **Recommendation**: Not in MVP - add dedicated use case if needed

---

## Files Modified Summary

### New Files (3)
1. `src/application/dto/interview_completion_dto.py` - Result DTO
2. `tests/unit/dto/test_interview_completion_dto.py` - DTO tests
3. `tests/e2e/test_interview_completion.py` - E2E test

### Modified Files (6)
1. `src/application/use_cases/complete_interview.py` - Inline summary logic
2. `src/application/use_cases/generate_summary.py` - Add deprecation
3. `src/adapters/api/websocket/session_orchestrator.py` - Use new API
4. `src/adapters/api/rest/interview_routes.py` - Add polling endpoint
5. `src/application/dto/interview_dto.py` - Add `InterviewSummaryResponse`
6. `tests/unit/use_cases/test_complete_interview.py` - Update tests

### Deleted Files (2) - LATER (after deprecation period)
1. `src/application/use_cases/generate_summary.py`
2. `tests/unit/use_cases/test_generate_summary.py`

**Total LOC**:
- Added: ~600 lines (inlined summary logic + tests)
- Removed: ~420 lines (GenerateSummaryUseCase + boilerplate)
- **Net**: +180 lines

---

## Timeline Estimate

**Total**: 3-4 hours (1 developer)

### Phase 1: Preparation (1.5 hours)
- Step 1.1: Create result DTO + tests (20 min)
- Step 1.2: Refactor CompleteInterviewUseCase (60 min)
- Step 1.3: Deprecate GenerateSummaryUseCase (10 min)

### Phase 2: Integration (1 hour)
- Step 2.1: Update WebSocket orchestrator (30 min)
- Step 2.2: Add polling endpoint + DTO (30 min)

### Phase 3: Testing (1 hour)
- Step 3.1: Update CompleteInterviewUseCase tests (30 min)
- Step 3.3: Update orchestrator tests (15 min)
- Step 3.4: Add polling endpoint tests (15 min)

### Phase 4: Review & Deploy (30 min)
- Code review (15 min)
- Documentation updates (10 min)
- Deployment (5 min)

---

## Conclusion

This refactoring simplifies the "Complete Interview" feature by:
1. ✅ Eliminating use case composition anti-pattern
2. ✅ Removing 5 optional dependencies
3. ✅ Simplifying API surface (`execute(id)` always returns both)
4. ✅ Adding polling endpoint for reconnect scenarios
5. ✅ Maintaining backward compatibility via deprecation

**Recommendation**: Proceed with implementation. Risk is low-medium, benefits are clear, and migration path is safe.

---

**Next Steps**:
1. User reviews plan
2. User approves or requests changes
3. Implement Phase 1-3
4. Deploy to staging
5. Production deployment after 1-2 releases (deprecation period)
