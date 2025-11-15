# Documentation Update Report - WebSocket URL Feature

**Date**: 2025-11-15
**Feature**: WebSocket URL in Planning Response
**Impact**: API architecture, client integration flow

## Files Updated

### 1. `docs/codebase-summary.md`
**Sections Modified**:
- Header: Version 0.2.1 → 0.2.2, date updated
- Recent Changes: Added ws_url feature to top of list
- Application Layer → DTOs: Added PlanningStatusResponse details with ws_url field

**Changes**:
- Documented new `ws_url` field in PlanningStatusResponse DTO
- Clarified client benefit: seamless transition to WebSocket after planning

### 2. `docs/system-architecture.md`
**Sections Modified**:
- Header: Version 0.2.1 → 0.2.2, date updated
- API Architecture → REST Endpoints: Updated interview endpoints list
- API Architecture → WebSocket API: Added connection flow section

**Changes**:
- Added planning endpoints: POST /api/interviews/plan, GET /api/interviews/{id}/plan
- Documented WebSocket connection flow (3 steps)
- Shows ws_url returned immediately after planning completes

## Implementation Summary

### API Changes
**Endpoints returning ws_url**:
1. POST /api/interviews/plan → PlanningStatusResponse with ws_url
2. GET /api/interviews/{id}/plan → PlanningStatusResponse with ws_url

### Response Schema
```json
{
  "interview_id": "uuid",
  "status": "IDLE",
  "planned_question_count": 4,
  "plan_metadata": {...},
  "message": "Interview planned with 4 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/{id}"  // NEW FIELD
}
```

### Client Flow
Before: POST /plan → GET /plan (polling) → Manual ws URL construction → Connect
After: POST /plan → Receive ws_url → Connect immediately

## Benefits
- Eliminates URL construction logic in client
- Base URL centralized in backend config (ws_base_url)
- Reduces client-server coupling
- Clearer API contract

## No Breaking Changes
- Added field to existing response DTOs
- Backward compatible (clients can ignore ws_url if not needed)
- No changes to domain logic or use cases

## Files Changed (Code)
1. `src/application/dto/interview_dto.py` - Added ws_url field to PlanningStatusResponse
2. `src/adapters/api/rest/interview_routes.py` - Inject ws_url in 2 endpoints (lines 273, 334)

## Files Changed (Docs)
1. `docs/codebase-summary.md` - Application layer DTOs section
2. `docs/system-architecture.md` - API endpoints, WebSocket connection flow

## Unresolved Questions
None - straightforward DTO enhancement with minimal scope
