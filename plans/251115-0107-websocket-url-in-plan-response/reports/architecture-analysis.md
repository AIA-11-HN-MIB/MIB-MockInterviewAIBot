# Architecture Analysis Report

**Created**: 2025-11-15
**Task**: Add WebSocket URL to PlanningStatusResponse
**Status**: Analysis Complete

## Current Architecture

### Clean Architecture Layers
- **Application Layer**: DTOs (interview_dto.py) - NO external dependencies
- **Adapter Layer**: REST endpoints (interview_routes.py) - CAN access Settings
- **Infrastructure Layer**: Settings (settings.py) - Configuration source

### Existing Pattern (InterviewResponse)

**File**: `src/application/dto/interview_dto.py` (lines 11-38)

```python
class InterviewResponse(BaseModel):
    ws_url: str  # WebSocket URL for real-time communication

    @staticmethod
    def from_domain(interview: Any, base_url: str) -> "InterviewResponse":
        return InterviewResponse(
            ws_url=f"{base_url}/ws/interviews/{interview.id}",
            # ... other fields
        )
```

**Usage**: `src/adapters/api/rest/interview_routes.py` (lines 88-117)

```python
async def get_interview(interview_id: UUID, session: AsyncSession):
    settings = get_settings()
    # ...
    base_url = settings.ws_base_url  # "ws://localhost:8000"
    return InterviewResponse.from_domain(interview, base_url)
```

### Settings Configuration

**File**: `src/infrastructure/config/settings.py` (lines 131-134)

```python
class Settings(BaseSettings):
    ws_host: str = "localhost"
    ws_port: int = 8000
    ws_base_url: str = "ws://localhost:8000"  # ✅ Already configured
```

## Target DTO Structure

### PlanningStatusResponse (Current)

**File**: `src/application/dto/interview_dto.py` (lines 60-66)

```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
    # ❌ Missing: ws_url field
```

### PlanningStatusResponse (Target)

```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
    ws_url: str  # ✅ NEW: WebSocket URL for interview session
```

## Current Usage Analysis

### Endpoint: POST /api/interviews/plan

**File**: `src/adapters/api/rest/interview_routes.py` (lines 227-291)

**Current Implementation** (line 280-286):
```python
return PlanningStatusResponse(
    interview_id=interview.id,
    status=interview.status.value,
    planned_question_count=interview.planned_question_count,
    plan_metadata=interview.plan_metadata,
    message=f"Interview planned with {interview.planned_question_count} questions",
    # ❌ Missing: ws_url parameter
)
```

**Required Changes**:
1. Inject `settings` (get_settings())
2. Construct ws_url: `f"{settings.ws_base_url}/ws/interviews/{interview.id}"`
3. Add ws_url to response

### Endpoint: GET /api/interviews/{id}/plan

**File**: `src/adapters/api/rest/interview_routes.py` (lines 294-341)

**Current Implementation** (line 335-341):
```python
return PlanningStatusResponse(
    interview_id=interview.id,
    status=interview.status.value,
    planned_question_count=interview.planned_question_count,
    plan_metadata=interview.plan_metadata,
    message=message,
    # ❌ Missing: ws_url parameter
)
```

**Required Changes**: Same as POST endpoint above.

## Dependency Graph

```
Settings (Infrastructure)
    ↓
get_settings() dependency injection
    ↓
plan_interview() endpoint (Adapter)
    ↓
PlanningStatusResponse constructor (Application)
    ↓
ws_url field construction
```

## Architecture Compliance

### ✅ Clean Architecture Rules
- DTO changes in Application layer (interview_dto.py)
- Settings access in Adapter layer (interview_routes.py)
- NO cross-layer violations
- Application layer receives data from adapter (not vice versa)

### ✅ Existing Pattern Reuse
- Follows InterviewResponse.from_domain() pattern
- Same settings.ws_base_url configuration
- Consistent URL construction: `{base_url}/ws/interviews/{id}`

### ✅ Backward Compatibility
- Adding field to Pydantic model (non-breaking)
- Required field → clients MUST handle it
- Alternative: Make optional with `ws_url: str | None = None` (safer)

## Risk Assessment

### Low Risk
- ✅ Simple field addition to DTO
- ✅ Existing settings already configured
- ✅ Pattern already proven in InterviewResponse
- ✅ No database changes
- ✅ No business logic changes

### Potential Issues
- ⚠️ Breaking change if clients expect exact fields (minor - Pydantic handles)
- ⚠️ Need to update 2 endpoints (plan_interview, get_planning_status)
- ⚠️ Tests may need updates if they validate response schema

## Recommendations

### Implementation Approach
1. **Phase 1**: Modify DTO (add ws_url field)
2. **Phase 2**: Update both endpoints (inject settings, construct URL)
3. Test both endpoints for correct URL generation

### Backward Compatibility Strategy
**Option A (Recommended)**: Required field
- Simpler, cleaner API
- Clients MUST handle new field
- Frontend expects it immediately

**Option B**: Optional field
- `ws_url: str | None = None`
- Gradual migration possible
- More complex logic

**Decision**: Use **Option A** (required field) - matches task requirements.

## Next Steps

1. ✅ Read phase-01-dto-modification.md
2. ✅ Read phase-02-endpoint-update.md
3. Implement changes per detailed phase plans
4. Test both endpoints
5. Verify URL format matches WebSocket handler expectations

---

**Analysis Complete** - Proceed to Phase 1 implementation.
