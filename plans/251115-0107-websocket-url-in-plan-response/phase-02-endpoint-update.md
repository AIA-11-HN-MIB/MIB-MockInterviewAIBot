# Phase 2: Endpoint Update

**Phase**: 2 of 2
**File**: `src/adapters/api/rest/interview_routes.py`
**Status**: ✅ Complete
**Complexity**: Low
**Estimated Time**: 10 minutes
**Actual Time**: ~10 minutes

## Context

Update both planning endpoints (POST /api/interviews/plan, GET /api/interviews/{id}/plan) to inject Settings, construct ws_url, and include in PlanningStatusResponse.

**Related Docs**:
- [System Architecture](../../../docs/system-architecture.md#rest-api-design)
- [Code Standards](../../../docs/code-standards.md#asyncawait-patterns)
- [Codebase Summary](../../../docs/codebase-summary.md#api-adapters)

**Depends On**: Phase 1 (DTO modification) complete

## Overview

Inject Settings dependency into 2 endpoints, extract ws_base_url, construct WebSocket URL using interview_id, pass to PlanningStatusResponse constructor. Follows existing pattern from get_interview endpoint.

## Key Insights

### Reference Pattern (get_interview endpoint)

**File**: `src/adapters/api/rest/interview_routes.py` (lines 84-117)

```python
async def get_interview(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    container = get_container()
    settings = get_settings()  # ✅ Settings injection

    # ... fetch interview ...

    base_url = settings.ws_base_url  # ✅ Extract base_url
    return InterviewResponse.from_domain(interview, base_url)  # ✅ Pass to DTO
```

**Key Takeaways**:
- Use `get_settings()` directly (not Depends) - already imported
- Extract `settings.ws_base_url` to variable for clarity
- Construct URL before returning response
- No need for static factory method (simpler than InterviewResponse)

### WebSocket URL Format

**Pattern**: `{base_url}/ws/interviews/{interview_id}`

**Examples**:
```python
# Development
ws_url = "ws://localhost:8000/ws/interviews/a1b2c3d4-..."

# Production
ws_url = "wss://api.elios.ai/ws/interviews/a1b2c3d4-..."
```

**Source**: `settings.ws_base_url` from Settings class

## Requirements

### Functional
- [x] Inject Settings in plan_interview endpoint
- [x] Inject Settings in get_planning_status endpoint
- [x] Construct ws_url using f-string interpolation
- [x] Pass ws_url to PlanningStatusResponse constructor
- [x] Maintain existing error handling

### Non-Functional
- [x] Follow Clean Architecture (adapter accesses settings)
- [x] Use existing get_settings() function
- [x] Preserve async/await patterns
- [x] No breaking changes to other endpoints

## Architecture

### Dependency Flow

```
Settings (Infrastructure)
    ↓ (get_settings())
Endpoint Function (Adapter)
    ↓ (extract ws_base_url)
ws_url Construction (f-string)
    ↓ (pass to constructor)
PlanningStatusResponse(ws_url=...)
```

### Clean Architecture Compliance

**Adapter Layer** (interview_routes.py):
- ✅ CAN access Settings (infrastructure)
- ✅ CAN construct URL (adapter responsibility)
- ✅ CAN inject dependencies via FastAPI Depends

**Application Layer** (PlanningStatusResponse):
- ✅ Receives ws_url as string (no Settings dependency)
- ✅ Remains pure data structure

## Related Code Files

### Primary File
- **src/adapters/api/rest/interview_routes.py**
  - Lines 227-291: POST /api/interviews/plan
  - Lines 294-341: GET /api/interviews/{id}/plan

### Dependency Files (No Changes)
- **src/application/dto/interview_dto.py**
  - PlanningStatusResponse (Phase 1 modified)
- **src/infrastructure/config/settings.py**
  - Settings.ws_base_url (already configured)
- **src/infrastructure/config/settings.py**
  - get_settings() function (already imported line 20, 23)

## Implementation Steps

### Endpoint 1: POST /api/interviews/plan

#### Step 1.1: Inject Settings
**File**: `src/adapters/api/rest/interview_routes.py`
**Line**: 233-236

**Before**:
```python
async def plan_interview(
    request: PlanInterviewRequest,
    session: AsyncSession = Depends(get_async_session),
):
```

**After**:
```python
async def plan_interview(
    request: PlanInterviewRequest,
    session: AsyncSession = Depends(get_async_session),
):
    # No function signature change - get_settings() called in body
```

**Rationale**: get_settings() already imported (line 20, 23), call directly in function body.

#### Step 1.2: Construct ws_url
**File**: `src/adapters/api/rest/interview_routes.py`
**Line**: After 278, before return statement (line 280)

**Insert after `interview = await use_case.execute(...)`** (line 275-278):

```python
        interview = await use_case.execute(
            cv_analysis_id=request.cv_analysis_id,
            candidate_id=request.candidate_id,
        )

        # ✅ NEW: Construct WebSocket URL
        settings = get_settings()
        ws_url = f"{settings.ws_base_url}/ws/interviews/{interview.id}"

        return PlanningStatusResponse(
            # ... existing fields ...
```

**Details**:
- Add after line 278 (after use_case execution)
- Extract settings.ws_base_url for clarity
- Use f-string interpolation with interview.id
- Variable name: `ws_url` (matches field name)

#### Step 1.3: Update Return Statement
**File**: `src/adapters/api/rest/interview_routes.py`
**Line**: 280-286

**Before**:
```python
        return PlanningStatusResponse(
            interview_id=interview.id,
            status=interview.status.value,
            planned_question_count=interview.planned_question_count,
            plan_metadata=interview.plan_metadata,
            message=f"Interview planned with {interview.planned_question_count} questions",
        )
```

**After**:
```python
        return PlanningStatusResponse(
            interview_id=interview.id,
            status=interview.status.value,
            planned_question_count=interview.planned_question_count,
            plan_metadata=interview.plan_metadata,
            message=f"Interview planned with {interview.planned_question_count} questions",
            ws_url=ws_url,  # ✅ NEW: WebSocket URL for interview session
        )
```

**Details**:
- Add `ws_url=ws_url` parameter
- Position: After `message` parameter (matches DTO field order)
- Include inline comment for clarity

### Endpoint 2: GET /api/interviews/{id}/plan

#### Step 2.1: Inject Settings
**File**: `src/adapters/api/rest/interview_routes.py`
**Line**: 299-302

**Before**:
```python
async def get_planning_status(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
```

**After**:
```python
async def get_planning_status(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    # No function signature change - get_settings() called in body
```

**Rationale**: Same as Endpoint 1 - get_settings() already imported.

#### Step 2.2: Construct ws_url
**File**: `src/adapters/api/rest/interview_routes.py`
**Line**: After 333, before return statement (line 335)

**Insert after message construction logic** (after line 333):

```python
        else:
            message = f"Interview status: {interview.status.value}"

        # ✅ NEW: Construct WebSocket URL
        settings = get_settings()
        ws_url = f"{settings.ws_base_url}/ws/interviews/{interview.id}"

        return PlanningStatusResponse(
            # ... existing fields ...
```

**Details**:
- Add after line 333 (after message assignment)
- Identical construction pattern as Endpoint 1
- Reuse `ws_url` variable name

#### Step 2.3: Update Return Statement
**File**: `src/adapters/api/rest/interview_routes.py`
**Line**: 335-341

**Before**:
```python
        return PlanningStatusResponse(
            interview_id=interview.id,
            status=interview.status.value,
            planned_question_count=interview.planned_question_count,
            plan_metadata=interview.plan_metadata,
            message=message,
        )
```

**After**:
```python
        return PlanningStatusResponse(
            interview_id=interview.id,
            status=interview.status.value,
            planned_question_count=interview.planned_question_count,
            plan_metadata=interview.plan_metadata,
            message=message,
            ws_url=ws_url,  # ✅ NEW: WebSocket URL for interview session
        )
```

**Details**: Same as Endpoint 1 - add ws_url parameter with comment.

### Step 3: Code Quality Check

#### Run Black Formatter
```bash
black src/adapters/api/rest/interview_routes.py
```

**Expected**: Minimal changes (new lines only)

#### Run Ruff Linter
```bash
ruff check src/adapters/api/rest/interview_routes.py
```

**Expected**: No errors (no new imports, no unused variables)

#### Type Check (Optional)
```bash
mypy src/adapters/api/rest/interview_routes.py
```

**Expected**: No errors (ws_url is str, matches DTO type)

## Todo List ✅

### Endpoint 1: POST /api/interviews/plan ✅
- [x] Open `src/adapters/api/rest/interview_routes.py`
- [x] Locate plan_interview function (line 227)
- [x] After line 278, add settings extraction: `settings = get_settings()`
- [x] Add ws_url construction: `ws_url = f"{settings.ws_base_url}/ws/interviews/{interview.id}"`
- [x] Locate return statement (line 280)
- [x] Add `ws_url=ws_url,` parameter to PlanningStatusResponse (after message)
- [x] Add inline comment: `# WebSocket URL for interview session`

### Endpoint 2: GET /api/interviews/{id}/plan ✅
- [x] Locate get_planning_status function (line 294)
- [x] After line 333, add settings extraction: `settings = get_settings()`
- [x] Add ws_url construction: `ws_url = f"{settings.ws_base_url}/ws/interviews/{interview.id}"`
- [x] Locate return statement (line 335)
- [x] Add `ws_url=ws_url,` parameter to PlanningStatusResponse (after message)
- [x] Add inline comment: `# WebSocket URL for interview session`

### Code Quality ✅
- [x] Save file
- [x] Run black formatter: `black src/adapters/api/rest/interview_routes.py`
- [x] Run ruff linter: `ruff check src/adapters/api/rest/interview_routes.py`
- [x] Verify no errors
- [x] Commit changes: `git add src/adapters/api/rest/interview_routes.py`

### Testing (Manual) ✅
- [x] Start server: `python -m src.main`
- [x] Test POST /api/interviews/plan with curl/Postman
- [x] Verify response includes ws_url field
- [x] Verify ws_url format: `ws://localhost:8000/ws/interviews/{uuid}`
- [x] Test GET /api/interviews/{id}/plan
- [x] Verify ws_url matches interview_id

## Success Criteria

### Functional
- [x] Both endpoints return ws_url in response
- [x] ws_url format matches: `{base_url}/ws/interviews/{interview_id}`
- [x] ws_url uses settings.ws_base_url (configurable)
- [x] interview_id in URL matches interview.id

### Code Quality
- [x] Black formatting passes
- [x] Ruff linting passes (no errors)
- [x] Type hints correct (mypy clean)
- [x] Inline comments clear and consistent

### Architecture
- [x] Settings accessed in adapter layer only
- [x] DTO receives ws_url as string (no Settings dependency)
- [x] Follows existing pattern from get_interview endpoint
- [x] Clean Architecture maintained

### Testing
- [x] Manual test: POST /api/interviews/plan returns ws_url
- [x] Manual test: GET /api/interviews/{id}/plan returns ws_url
- [x] ws_url format validated
- [x] No breaking changes to other endpoints

## Risk Assessment

### Low Risk Changes
- ✅ Small, focused changes (2 endpoints)
- ✅ Follows existing pattern (get_interview)
- ✅ No database changes
- ✅ No business logic changes
- ✅ Settings already configured

### Potential Issues
- ⚠️ If get_settings() fails, endpoint will 500 (unlikely - cached singleton)
- ⚠️ If ws_base_url not configured, will use default "ws://localhost:8000" (acceptable)
- ⚠️ Missing ws_url parameter → Pydantic ValidationError (caught immediately)

**Mitigation**: Phase 1 ensures DTO expects ws_url, Phase 2 provides it.

## Security Considerations

### No Security Concerns
- ✅ ws_url is public information (no secrets)
- ✅ WebSocket authentication handled separately
- ✅ URL construction uses safe f-string (no injection risk)
- ✅ interview_id is UUID (already exposed in response)

### Settings Access
- ✅ get_settings() returns singleton (safe)
- ✅ ws_base_url is non-sensitive configuration
- ✅ No secrets exposed in URL

## Performance Considerations

### Negligible Impact
- ✅ get_settings() cached via @lru_cache (no overhead)
- ✅ f-string interpolation (microseconds)
- ✅ One additional variable assignment
- ✅ No additional database queries

### Benchmarks (Expected)
- Endpoint latency: < 1ms increase
- Memory: < 100 bytes per request (string allocation)
- CPU: Negligible (string concatenation)

## Testing Strategy

### Manual Testing

#### Test 1: POST /api/interviews/plan
```bash
# Request
curl -X POST http://localhost:8000/api/interviews/plan \
  -H "Content-Type: application/json" \
  -d '{
    "cv_analysis_id": "a1b2c3d4-...",
    "candidate_id": "e5f6g7h8-..."
  }'

# Expected Response
{
  "interview_id": "i9j0k1l2-...",
  "status": "IDLE",
  "planned_question_count": 5,
  "plan_metadata": {...},
  "message": "Interview planned with 5 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/i9j0k1l2-..."  // ✅ NEW
}
```

**Validation**:
- ws_url field present
- ws_url format: `ws://{host}:{port}/ws/interviews/{interview_id}`
- interview_id in ws_url matches interview_id field

#### Test 2: GET /api/interviews/{id}/plan
```bash
# Request
curl http://localhost:8000/api/interviews/{interview_id}/plan

# Expected Response
{
  "interview_id": "{interview_id}",
  "status": "IDLE",
  "planned_question_count": 5,
  "plan_metadata": {...},
  "message": "Interview ready with 5 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/{interview_id}"  // ✅ NEW
}
```

**Validation**: Same as Test 1.

### Automated Testing (Future)

**Unit Tests** (`tests/unit/adapters/api/test_interview_routes.py`):
```python
async def test_plan_interview_returns_ws_url():
    # Mock dependencies
    # Call endpoint
    # Assert response.ws_url == f"ws://localhost:8000/ws/interviews/{interview_id}"
```

**Integration Tests**:
```python
async def test_ws_url_connects_to_websocket():
    # Plan interview via POST /api/interviews/plan
    # Extract ws_url from response
    # Connect to WebSocket using ws_url
    # Assert connection succeeds
```

## Next Steps

After Phase 2 completion:
1. ✅ Manual test both endpoints
2. ✅ Verify ws_url format correct
3. ✅ Update integration tests (if exist)
4. ✅ Update API documentation (Swagger auto-updated)
5. ✅ Commit changes with descriptive message
6. ✅ Mark task complete in plan.md

---

**Phase 2 Status**: ✅ COMPLETE
**Completed**: 2025-11-15 01:45
**Blocked By**: None
**Blocking**: None (final phase)
