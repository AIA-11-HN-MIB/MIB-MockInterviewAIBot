# Add WebSocket URL to PlanningStatusResponse

**Plan ID**: 251115-0107-websocket-url-in-plan-response
**Created**: 2025-11-15 01:07
**Status**: 🔲 Pending
**Complexity**: Low
**Time Estimate**: 15 minutes

## Quick Summary

Modify POST /api/interviews/plan to return WebSocket URL immediately, eliminating need for separate GET request.

**Change**: Add `ws_url` field to PlanningStatusResponse + update 2 endpoints to construct/return it.

## Files Modified

1. `src/application/dto/interview_dto.py` - Add ws_url field
2. `src/adapters/api/rest/interview_routes.py` - Update 2 endpoints

## Implementation Phases

| Phase | File | Status | Time | Description |
|-------|------|--------|------|-------------|
| 1 | interview_dto.py | 🔲 Pending | 5 min | Add ws_url field to DTO |
| 2 | interview_routes.py | 🔲 Pending | 10 min | Inject settings, construct ws_url |

## Quick Start

```bash
# 1. Review plan
cat plan.md

# 2. Review phase details
cat phase-01-dto-modification.md
cat phase-02-endpoint-update.md

# 3. Implement Phase 1
# Edit: src/application/dto/interview_dto.py
# Add: ws_url: str  # WebSocket URL for real-time interview session

# 4. Implement Phase 2
# Edit: src/adapters/api/rest/interview_routes.py
# Add in both endpoints:
#   settings = get_settings()
#   ws_url = f"{settings.ws_base_url}/ws/interviews/{interview.id}"
#   # Include ws_url in PlanningStatusResponse constructor

# 5. Test
python -m src.main
curl -X POST http://localhost:8000/api/interviews/plan ...
# Verify ws_url in response
```

## Expected Response Change

### Before
```json
{
  "interview_id": "a1b2c3d4-...",
  "status": "IDLE",
  "planned_question_count": 5,
  "message": "Interview planned with 5 questions"
}
```

### After
```json
{
  "interview_id": "a1b2c3d4-...",
  "status": "IDLE",
  "planned_question_count": 5,
  "message": "Interview planned with 5 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/a1b2c3d4-..."
}
```

## Documentation

- **[plan.md](./plan.md)** - Complete implementation plan with all details
- **[phase-01-dto-modification.md](./phase-01-dto-modification.md)** - DTO changes (5 min)
- **[phase-02-endpoint-update.md](./phase-02-endpoint-update.md)** - Endpoint changes (10 min)
- **[reports/architecture-analysis.md](./reports/architecture-analysis.md)** - Architecture review
- **[reports/codebase-review.md](./reports/codebase-review.md)** - Code analysis

## Success Criteria

- ✅ ws_url field in PlanningStatusResponse
- ✅ POST /api/interviews/plan returns ws_url
- ✅ GET /api/interviews/{id}/plan returns ws_url
- ✅ Format: `ws://localhost:8000/ws/interviews/{uuid}`
- ✅ Clean Architecture maintained
- ✅ All linters pass (black, ruff)

## Risk Level

🟢 **LOW RISK**
- Small change (2 files, ~10 lines)
- Follows existing pattern
- No database changes
- No business logic changes

---

**Start with**: [plan.md](./plan.md) → [phase-01-dto-modification.md](./phase-01-dto-modification.md) → [phase-02-endpoint-update.md](./phase-02-endpoint-update.md)
