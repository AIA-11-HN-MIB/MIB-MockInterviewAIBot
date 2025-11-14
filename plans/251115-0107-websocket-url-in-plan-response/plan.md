# Implementation Plan: Add WebSocket URL to PlanningStatusResponse

**Created**: 2025-11-15 01:07
**Completed**: 2025-11-15 01:45
**Task ID**: 251115-0107-websocket-url-in-plan-response
**Status**: ✅ Complete
**Complexity**: Low
**Estimated Time**: 15 minutes total

## Executive Summary

Modify POST /api/interviews/plan endpoint to return WebSocket URL immediately after planning completes, eliminating need for separate GET request. Change involves adding ws_url field to PlanningStatusResponse DTO and updating 2 endpoints to construct and return URL.

**Impact**: Client can connect to WebSocket immediately after planning without additional API call.

## Task Overview

### Current State
- POST /api/interviews/plan returns: `{interview_id, status, question_count}`
- WebSocket URL only available via separate GET /api/interviews/{id} call
- Client must make 2 requests before connecting to WebSocket

### Target State
- POST /api/interviews/plan returns: `{interview_id, status, question_count, ws_url}`
- WebSocket URL immediately available in planning response
- Client can connect to WebSocket in single round trip

### Requirements
1. Add ws_url field to PlanningStatusResponse DTO
2. Inject settings.ws_base_url into plan_interview endpoint
3. Construct ws_url: `f"{ws_base_url}/ws/interviews/{interview_id}"`
4. Maintain backward compatibility (additive change)
5. Follow existing pattern from InterviewResponse.from_domain()

## Architecture Overview

### Clean Architecture Compliance

```
Settings (Infrastructure)
    ↓ (get_settings())
Endpoint (Adapter) - constructs ws_url
    ↓ (pass string)
PlanningStatusResponse (Application) - receives ws_url
```

**Layer Responsibilities**:
- **Infrastructure**: Provides Settings.ws_base_url configuration
- **Adapter**: Accesses settings, constructs ws_url, injects into DTO
- **Application**: Receives ws_url as plain string (no Settings dependency)

### Existing Pattern Reference

**InterviewResponse** (src/application/dto/interview_dto.py):
```python
class InterviewResponse(BaseModel):
    ws_url: str  # WebSocket URL for real-time communication

    @staticmethod
    def from_domain(interview: Any, base_url: str):
        return InterviewResponse(
            ws_url=f"{base_url}/ws/interviews/{interview.id}",
            # ... other fields
        )
```

**get_interview endpoint** (src/adapters/api/rest/interview_routes.py):
```python
async def get_interview(interview_id: UUID, session: AsyncSession):
    settings = get_settings()
    # ... fetch interview ...
    base_url = settings.ws_base_url
    return InterviewResponse.from_domain(interview, base_url)
```

**Our approach**: Simpler - direct constructor call (no static factory method needed).

## Files to Modify

### 1. src/application/dto/interview_dto.py
**Lines**: 60-66 (PlanningStatusResponse)
**Change**: Add `ws_url: str` field
**Complexity**: Low

### 2. src/adapters/api/rest/interview_routes.py
**Lines**: 227-291 (POST /api/interviews/plan)
**Change**: Inject settings, construct ws_url, add to response
**Complexity**: Low

**Lines**: 294-341 (GET /api/interviews/{id}/plan)
**Change**: Same as POST endpoint
**Complexity**: Low

## Implementation Phases

### Phase 1: DTO Modification (5 minutes) ✅
**File**: `src/application/dto/interview_dto.py`
**Status**: Complete

**Tasks**:
- [x] Add ws_url field to PlanningStatusResponse
- [x] Type hint as `str` (required, not optional)
- [x] Include inline comment
- [x] Run black formatter

**See**: [phase-01-dto-modification.md](./phase-01-dto-modification.md)

### Phase 2: Endpoint Update (10 minutes) ✅
**File**: `src/adapters/api/rest/interview_routes.py`
**Status**: Complete
**Depends On**: Phase 1

**Tasks**:
- [x] Update POST /api/interviews/plan
  - Get settings via get_settings()
  - Construct ws_url using f-string
  - Add ws_url to PlanningStatusResponse constructor
- [x] Update GET /api/interviews/{id}/plan
  - Same changes as POST endpoint
- [x] Run black formatter and ruff linter
- [x] Manual testing

**See**: [phase-02-endpoint-update.md](./phase-02-endpoint-update.md)

## Related Documentation

### Context Documents
- [Architecture Analysis](./reports/architecture-analysis.md) - Architecture compliance and pattern analysis
- [Codebase Review](./reports/codebase-review.md) - Current implementation and dependencies
- [Codebase Summary](../../docs/codebase-summary.md) - Full codebase overview
- [System Architecture](../../docs/system-architecture.md) - System design and API architecture
- [Code Standards](../../docs/code-standards.md) - Coding conventions and best practices

### Phase Documents
- [Phase 1: DTO Modification](./phase-01-dto-modification.md)
- [Phase 2: Endpoint Update](./phase-02-endpoint-update.md)

## Success Criteria

### Functional Requirements ✅
- [x] ws_url field added to PlanningStatusResponse
- [x] POST /api/interviews/plan returns ws_url
- [x] GET /api/interviews/{id}/plan returns ws_url
- [x] ws_url format: `{base_url}/ws/interviews/{interview_id}`
- [x] ws_url uses configurable settings.ws_base_url

### Code Quality ✅
- [x] Black formatting passes
- [x] Ruff linting passes (no errors)
- [x] Type hints correct (mypy clean)
- [x] Inline comments clear and consistent
- [x] No code duplication

### Architecture ✅
- [x] Clean Architecture maintained (no layer violations)
- [x] DTO has no external dependencies
- [x] Settings accessed in adapter layer only
- [x] Follows existing InterviewResponse pattern

### Testing ✅
- [x] Manual test: POST /api/interviews/plan returns ws_url
- [x] Manual test: GET /api/interviews/{id}/plan returns ws_url
- [x] ws_url format validated
- [x] WebSocket connection works using returned URL

## Risk Assessment

### Low Risk ✅
- ✅ Small, focused change (2 files, ~10 lines)
- ✅ Follows proven pattern (InterviewResponse)
- ✅ Settings already configured (ws_base_url exists)
- ✅ No database changes
- ✅ No business logic changes

### Potential Issues
- ⚠️ Breaking change for strict schema validators (minor impact)
- ⚠️ Requires Phase 1 before Phase 2 (Pydantic will fail if ws_url missing)

**Mitigation**: Implement phases sequentially, test after each phase.

## Security Considerations

### No Security Concerns ✅
- ✅ ws_url is public information (no secrets)
- ✅ interview_id already exposed in response
- ✅ WebSocket authentication handled separately
- ✅ URL construction uses safe f-string (no injection risk)

## Performance Considerations

### Negligible Impact ✅
- ✅ get_settings() cached via @lru_cache (no overhead)
- ✅ f-string interpolation (microseconds)
- ✅ No additional database queries
- ✅ Response size increase: ~50 bytes (ws_url string)

**Benchmarks (Expected)**:
- Endpoint latency: < 1ms increase
- Memory: < 100 bytes per request
- CPU: Negligible

## Testing Strategy

### Manual Testing

**Test 1: POST /api/interviews/plan**
```bash
curl -X POST http://localhost:8000/api/interviews/plan \
  -H "Content-Type: application/json" \
  -d '{"cv_analysis_id": "...", "candidate_id": "..."}'
```

**Expected Response**:
```json
{
  "interview_id": "a1b2c3d4-...",
  "status": "IDLE",
  "planned_question_count": 5,
  "plan_metadata": {},
  "message": "Interview planned with 5 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/a1b2c3d4-..."  // ✅ NEW
}
```

**Test 2: GET /api/interviews/{id}/plan**
```bash
curl http://localhost:8000/api/interviews/{interview_id}/plan
```

**Expected Response**: Same structure as Test 1.

**Test 3: WebSocket Connection**
```javascript
const ws = new WebSocket(response.ws_url);
ws.onopen = () => console.log('✅ Connected using returned URL');
```

### Automated Testing (Future)

**Unit Tests**: Validate ws_url field presence and format
**Integration Tests**: Verify WebSocket connection using returned URL
**E2E Tests**: Full interview flow using ws_url

## Implementation Checklist

### Pre-Implementation
- [x] Read all related documentation
- [x] Review existing codebase (InterviewResponse pattern)
- [x] Understand Settings configuration
- [x] Plan phases sequentially

### Phase 1: DTO Modification ✅
- [x] Open src/application/dto/interview_dto.py
- [x] Add ws_url field to PlanningStatusResponse (line 69)
- [x] Add inline comment
- [x] Run black formatter
- [x] Verify no linting errors
- [x] Commit: `feat(dto): add ws_url to PlanningStatusResponse`

### Phase 2: Endpoint Update ✅
- [x] Open src/adapters/api/rest/interview_routes.py
- [x] Update POST /api/interviews/plan (line 280-282)
  - [x] Get settings after use_case execution
  - [x] Construct ws_url using f-string
  - [x] Add ws_url to response constructor
- [x] Update GET /api/interviews/{id}/plan (line 343-345, 350)
  - [x] Same changes as POST endpoint
- [x] Run black formatter
- [x] Run ruff linter
- [x] Commit: `feat(api): inject ws_url in planning endpoints`

### Testing ✅
- [x] Start server: `python -m src.main`
- [x] Test POST /api/interviews/plan
- [x] Verify ws_url in response
- [x] Verify ws_url format correct
- [x] Test GET /api/interviews/{id}/plan
- [x] Verify ws_url matches interview_id
- [x] Test WebSocket connection using ws_url

### Documentation ✅
- [x] Update API documentation (Swagger auto-updated)
- [x] Mark phases complete in plan.md
- [x] Update task status: ✅ Complete

## Timeline

- **Phase 1**: 5 minutes (DTO modification)
- **Phase 2**: 10 minutes (endpoint update)
- **Total Estimated Time**: 15 minutes

## Rollback Plan

### If Issues Arise

**After Phase 1** (DTO only):
```bash
git revert HEAD  # Remove ws_url field
```
**Impact**: None (endpoints unchanged)

**After Phase 2** (Endpoints updated):
```bash
git revert HEAD~2..HEAD  # Revert both commits
```
**Impact**: Clients won't receive ws_url (falls back to original behavior)

## Completion Summary

Implementation successfully completed on 2025-11-15 at 01:45 (15 minutes total).

### Changes Delivered
1. **DTO Modified**: Added `ws_url: str` field to PlanningStatusResponse (line 69)
   - Type: required string (not optional)
   - Comment: `# WebSocket URL for real-time interview session`
   - File: `src/application/dto/interview_dto.py`

2. **POST /api/interviews/plan Updated** (lines 280-282)
   - Injects Settings via get_settings()
   - Constructs ws_url: `f"{settings.ws_base_url}/ws/interviews/{interview.id}"`
   - Returns ws_url in PlanningStatusResponse

3. **GET /api/interviews/{id}/plan Updated** (lines 343-345, 350)
   - Same ws_url injection & construction as POST endpoint
   - Maintains backward compatibility

### Testing Results
- Type checking: ✅ PASS (no mypy errors)
- Code formatting: ✅ PASS (black clean)
- Linting: ✅ PASS (ruff clean)
- Manual testing: ✅ PASS
  - POST /api/interviews/plan returns ws_url
  - GET /api/interviews/{id}/plan returns ws_url
  - WebSocket URL format correct: ws://localhost:8000/ws/interviews/{interview_id}

### Impact
- Clients can now connect to WebSocket immediately after planning (single request)
- No breaking changes (additive field to response)
- Follows existing InterviewResponse pattern
- Clean Architecture maintained (Settings accessed only in adapter layer)

## Next Steps After Completion

1. ✅ Verify both endpoints return ws_url
2. Update frontend to use returned ws_url (eliminates GET /api/interviews/{id} call)
3. Monitor production for any client-side issues
4. Update integration tests to validate ws_url

## Unresolved Questions

None. Feature complete and tested.

---

**Plan Status**: ✅ COMPLETE
**Completed**: 2025-11-15 01:45
**Actual Time**: ~15 minutes total
**Blocked By**: None
**Blocking**: None

**Implementation Order**:
1. Phase 1: DTO Modification
2. Phase 2: Endpoint Update
3. Testing
4. Deployment
