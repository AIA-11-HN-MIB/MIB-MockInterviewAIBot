# Phase 1: DTO Modification

**Phase**: 1 of 2
**File**: `src/application/dto/interview_dto.py`
**Status**: ✅ Complete
**Complexity**: Low
**Estimated Time**: 5 minutes
**Actual Time**: ~5 minutes

## Context

Modify PlanningStatusResponse DTO to include ws_url field, enabling clients to connect to WebSocket immediately after interview planning completes without separate GET request.

**Related Docs**:
- [Codebase Summary](../../../docs/codebase-summary.md#application-layer)
- [Code Standards](../../../docs/code-standards.md#naming-conventions)
- [System Architecture](../../../docs/system-architecture.md#api-architecture)

## Overview

Add WebSocket URL field to PlanningStatusResponse following pattern established in InterviewResponse. Change is additive, non-breaking, maintains Clean Architecture principles.

## Key Insights

### Existing Pattern (InterviewResponse)
```python
class InterviewResponse(BaseModel):
    ws_url: str  # WebSocket URL for real-time communication
    # ... other fields
```

### Current State (PlanningStatusResponse)
```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
    # ❌ Missing ws_url
```

### Target State
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

## Requirements

### Functional
- [x] Add ws_url field to PlanningStatusResponse
- [x] Use required field (not optional)
- [x] Type hint as `str` (not `str | None`)
- [x] Include inline comment explaining purpose

### Non-Functional
- [x] Maintain Clean Architecture (no external dependencies in DTO)
- [x] Follow existing naming conventions
- [x] Update docstring if needed
- [x] Preserve Pydantic BaseModel inheritance

## Architecture

### Clean Architecture Compliance

**Application Layer** (interview_dto.py):
- ✅ NO external dependencies
- ✅ Pure data structure (Pydantic model)
- ✅ No business logic
- ✅ Consumed by adapter layer

**Layer Responsibilities**:
```
Infrastructure (Settings)
    ↓
Adapter (interview_routes.py) - constructs ws_url
    ↓
Application (PlanningStatusResponse) - receives ws_url as string
```

### Type Safety

**Field Type**: `str` (not optional)
- Rationale: URL always available after planning
- Pydantic validates non-null string at runtime
- FastAPI validates in response schema

## Related Code Files

### Primary File
- **src/application/dto/interview_dto.py** (lines 60-66)
  - Modify PlanningStatusResponse class
  - Add ws_url field after message field

### Reference Files (No Changes)
- **src/application/dto/interview_dto.py** (lines 11-38)
  - InterviewResponse - reference pattern
- **src/infrastructure/config/settings.py** (lines 131-134)
  - Settings.ws_base_url - config source

### Dependent Files (Phase 2)
- **src/adapters/api/rest/interview_routes.py**
  - Will inject settings and construct ws_url
  - Phase 2 implementation

## Implementation Steps

### Step 1: Locate PlanningStatusResponse Class
**File**: `src/application/dto/interview_dto.py`
**Lines**: 60-66

```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
```

### Step 2: Add ws_url Field
**Action**: Add new field after `message` field (line 66)

**Before** (line 60-66):
```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
```

**After** (line 60-67):
```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
    ws_url: str  # WebSocket URL for real-time interview session
```

**Details**:
- Add after line 66 (after `message: str`)
- Type: `str` (required, not optional)
- Comment: Explains purpose clearly
- Follows existing field formatting

### Step 3: Verify Pydantic Model
**Action**: Ensure class still inherits from BaseModel

**Validation**:
```python
# ✅ Inherits from Pydantic BaseModel
class PlanningStatusResponse(BaseModel):
    # ... fields
```

**Auto-validation**:
- Pydantic validates ws_url is non-null string
- FastAPI includes in OpenAPI schema automatically
- JSON serialization works out of the box

### Step 4: Code Quality Check
**Action**: Run black formatter

```bash
black src/application/dto/interview_dto.py
```

**Expected**: No changes (formatting already correct)

## Todo List ✅

- [x] Open `src/application/dto/interview_dto.py` in editor
- [x] Locate PlanningStatusResponse class (line 60)
- [x] Add `ws_url: str` field after `message: str` (line 69)
- [x] Add inline comment: `# WebSocket URL for real-time interview session`
- [x] Save file
- [x] Run black formatter: `black src/application/dto/interview_dto.py`
- [x] Verify no formatting changes
- [x] Commit change: `git add src/application/dto/interview_dto.py`
- [x] Mark phase complete: Update status to ✅ Complete

## Success Criteria

### Code Quality
- [x] Field added with correct type (`str`)
- [x] Inline comment present and clear
- [x] Black formatting passes
- [x] No linting errors (ruff)
- [x] File imports unchanged

### Architecture
- [x] No external dependencies added
- [x] Clean Architecture maintained
- [x] Pydantic BaseModel inheritance preserved
- [x] Field ordering logical (ws_url after message)

### Testing (Deferred to Phase 2)
- Unit tests will be updated after Phase 2 endpoint changes
- Integration tests will validate complete flow

## Risk Assessment

### Low Risk Changes
- ✅ Adding field to Pydantic model (safe)
- ✅ Required field (no null handling needed)
- ✅ Follows existing pattern (InterviewResponse)
- ✅ No database changes
- ✅ No business logic changes

### Potential Issues
- ⚠️ Endpoints must provide ws_url in Phase 2 (Pydantic will fail if missing)
- ⚠️ Breaking change for strict schema validators (minor)

**Mitigation**: Phase 2 immediately follows to provide ws_url value.

## Security Considerations

### No Security Concerns
- ✅ ws_url is public information (no secrets)
- ✅ Interview ID already exposed in response
- ✅ WebSocket authentication handled separately
- ✅ URL format does not expose sensitive data

## Next Steps

After Phase 1 completion:
1. ✅ Proceed to Phase 2: Endpoint Update
2. Update plan_interview endpoint to inject settings
3. Update get_planning_status endpoint to inject settings
4. Construct ws_url in both endpoints
5. Test both endpoints return correct ws_url

---

**Phase 1 Status**: ✅ COMPLETE
**Completed**: 2025-11-15 01:30
**Blocked By**: None
**Blocking**: None (Phase 2 completed)
