# Codebase Review Report

**Created**: 2025-11-15
**Task**: Add WebSocket URL to PlanningStatusResponse
**Scope**: Review current implementation and dependencies

## Files Under Review

### 1. src/application/dto/interview_dto.py

**Purpose**: Data Transfer Objects for REST API
**Lines**: 96 total
**Dependencies**: Pydantic, UUID, datetime, typing

#### PlanningStatusResponse (lines 60-66)
```python
class PlanningStatusResponse(BaseModel):
    """Response with planning status."""
    interview_id: UUID
    status: str  # PREPARING, READY, IN_PROGRESS
    planned_question_count: int | None
    plan_metadata: dict | None
    message: str
```

**Analysis**:
- ❌ Missing ws_url field
- ✅ Clean, focused DTO
- ✅ No external dependencies (Clean Architecture compliant)
- ✅ Uses Pydantic BaseModel for validation

**Required Change**: Add `ws_url: str` field

#### InterviewResponse (lines 11-38) - Reference Pattern

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

**Key Insights**:
- ✅ Static factory method pattern for domain → DTO conversion
- ✅ Accepts base_url parameter from caller (adapter layer)
- ✅ Constructs ws_url using f-string interpolation
- ✅ URL pattern: `{base_url}/ws/interviews/{interview_id}`

**Decision**: PlanningStatusResponse does NOT need static factory method (simpler use case)

### 2. src/adapters/api/rest/interview_routes.py

**Purpose**: REST API endpoints for interview management
**Lines**: 401 total
**Dependencies**: FastAPI, SQLAlchemy, Use Cases, DTOs, Settings

#### POST /api/interviews/plan (lines 227-291)

**Current Implementation**:
```python
async def plan_interview(
    request: PlanInterviewRequest,
    session: AsyncSession = Depends(get_async_session),
):
    # ... planning logic (lines 254-278)

    return PlanningStatusResponse(  # line 280
        interview_id=interview.id,
        status=interview.status.value,
        planned_question_count=interview.planned_question_count,
        plan_metadata=interview.plan_metadata,
        message=f"Interview planned with {interview.planned_question_count} questions",
    )
```

**Analysis**:
- ❌ No settings injection
- ❌ No ws_url construction
- ✅ Clean use case orchestration
- ✅ Proper error handling (try-except with HTTPException)

**Required Changes**:
1. Add dependency: `settings: Settings = Depends(get_settings)`
2. Construct ws_url: `ws_url=f"{settings.ws_base_url}/ws/interviews/{interview.id}"`
3. Add ws_url to PlanningStatusResponse constructor

#### GET /api/interviews/{id}/plan (lines 294-341)

**Current Implementation**:
```python
async def get_planning_status(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    # ... status logic (lines 315-333)

    return PlanningStatusResponse(  # line 335
        interview_id=interview.id,
        status=interview.status.value,
        planned_question_count=interview.planned_question_count,
        plan_metadata=interview.plan_metadata,
        message=message,
    )
```

**Analysis**: Same issues and required changes as POST endpoint above.

#### GET /api/interviews/{id} (lines 84-117) - Reference Pattern

**Current Implementation**:
```python
async def get_interview(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    container = get_container()
    settings = get_settings()  # ✅ Settings injection

    # ... fetch interview logic

    base_url = settings.ws_base_url  # ✅ Extract base_url
    return InterviewResponse.from_domain(interview, base_url)  # ✅ Pass to DTO
```

**Key Insights**:
- ✅ Demonstrates correct pattern: get_settings() → extract ws_base_url → pass to DTO
- ✅ Uses static factory method (our case is simpler - direct constructor)
- ✅ Clean separation: adapter gets config, DTO receives data

### 3. src/infrastructure/config/settings.py

**Purpose**: Application configuration management
**Lines**: 179 total
**Dependencies**: Pydantic Settings, dotenv, os, re

#### WebSocket Configuration (lines 131-134)

```python
class Settings(BaseSettings):
    # WebSocket Configuration
    ws_host: str = "localhost"
    ws_port: int = 8000
    ws_base_url: str = "ws://localhost:8000"  # ✅ Already configured
```

**Analysis**:
- ✅ ws_base_url already defined with default value
- ✅ Configurable via environment variable (WS_BASE_URL)
- ✅ Default matches local development setup
- ✅ No changes needed to Settings

**Example Production Values**:
```bash
# .env.production
WS_BASE_URL=wss://api.elios.ai  # Secure WebSocket
```

## Dependency Analysis

### Current Dependencies

**PlanningStatusResponse**:
- Used in: interview_routes.py (2 endpoints)
- Depends on: Pydantic (BaseModel)
- Zero coupling to infrastructure

**interview_routes.py**:
- Uses: PlanningStatusResponse, PlanInterviewRequest
- Depends on: FastAPI, SQLAlchemy, Use Cases, Container, Settings
- Clean dependency injection via FastAPI Depends()

**Settings**:
- Consumed by: All adapters (via get_settings())
- Provides: All configuration values
- Singleton pattern via @lru_cache

### Post-Change Dependencies

```
Settings (ws_base_url)
    ↓ (get_settings dependency injection)
plan_interview() endpoint
    ↓ (extract base_url)
ws_url construction (f-string)
    ↓ (pass to constructor)
PlanningStatusResponse(ws_url=...)
```

**Coupling**: Loose (adapter depends on config, DTO receives string)

## Breaking Changes Analysis

### API Response Schema Change

**Before**:
```json
{
  "interview_id": "uuid",
  "status": "IDLE",
  "planned_question_count": 5,
  "plan_metadata": {},
  "message": "Interview planned with 5 questions"
}
```

**After**:
```json
{
  "interview_id": "uuid",
  "status": "IDLE",
  "planned_question_count": 5,
  "plan_metadata": {},
  "message": "Interview planned with 5 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/{uuid}"  // ✅ NEW
}
```

**Impact**:
- ✅ Additive change (non-breaking in most clients)
- ✅ Pydantic will serialize new field automatically
- ⚠️ Clients with strict schema validation may need updates
- ⚠️ Frontend expects this field (per task requirements)

### Backward Compatibility Strategy

**Option 1**: Required field (Chosen)
```python
ws_url: str  # Always present
```
- Pros: Cleaner API, matches requirements
- Cons: Clients MUST handle new field

**Option 2**: Optional field
```python
ws_url: str | None = None  # Nullable
```
- Pros: Gradual migration
- Cons: More complex, unnecessary for this use case

**Decision**: Use Option 1 (required field) per task requirements.

## Test Impact Analysis

### Files Likely Needing Updates

1. **Unit Tests**: `tests/unit/application/dto/test_interview_dto.py`
   - Test PlanningStatusResponse construction
   - Validate ws_url field presence

2. **Integration Tests**: `tests/integration/api/test_interview_routes.py`
   - Test POST /api/interviews/plan response
   - Test GET /api/interviews/{id}/plan response
   - Validate ws_url format

3. **E2E Tests**: `tests/e2e/test_interview_flow.py`
   - Verify WebSocket URL correctness
   - Test connection using returned ws_url

### Test Coverage Requirements

- ✅ DTO validation with ws_url field
- ✅ Endpoint returns ws_url in response
- ✅ URL format matches WebSocket handler expectations
- ✅ URL constructed correctly with settings.ws_base_url

## Code Quality Checks

### Style Compliance (PEP 8)
- ✅ All files use black formatting
- ✅ Type hints present throughout
- ✅ Docstrings for public APIs
- ✅ Line length < 100 characters

### Architecture Compliance (Clean Architecture)
- ✅ DTO in application layer (no external dependencies)
- ✅ Settings access in adapter layer only
- ✅ Dependency flow: Infrastructure → Adapter → Application
- ✅ No circular dependencies

### Naming Conventions
- ✅ DTOs use descriptive names (*Response, *Request)
- ✅ Endpoints use async def with clear verbs
- ✅ Settings use lowercase with underscores

## Security Considerations

### No Security Issues Identified
- ✅ ws_url is public information (no secrets)
- ✅ Interview ID already exposed in response
- ✅ WebSocket URL follows standard format
- ✅ No authentication changes required

### WebSocket Security (Out of Scope)
- WebSocket endpoint security handled separately
- Connection authentication handled by WebSocket handler
- URL exposure does not grant access

## Performance Considerations

### Negligible Performance Impact
- ✅ f-string interpolation (microseconds)
- ✅ One additional settings access (cached via @lru_cache)
- ✅ Pydantic serialization (unchanged)
- ✅ No database queries added

## Unresolved Questions

None identified. All requirements clear from codebase analysis.

---

**Review Complete** - Ready for implementation planning.
