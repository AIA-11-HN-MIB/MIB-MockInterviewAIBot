# Implementation Plan Summary
## Domain-Driven State Management Migration

**Plan ID**: 251112-2117
**Created**: 2025-11-12
**Status**: ✅ Ready for Review
**Estimated Effort**: 8-12 hours

---

## Executive Summary

Migrate from dual state machines (orchestrator `SessionState` + domain `InterviewStatus`) to **single source of truth** in domain model. This eliminates state inconsistency between WebSocket sessions and database, aligns with Clean Architecture principles, and simplifies testing.

## Problem Solved

**Current Issues**:
1. Orchestrator's `self.state` doesn't sync with `interview.status` in database
2. State divergence between WebSocket and REST API views
3. Duplicate business logic in orchestrator layer
4. Lost follow-up tracking on session disruption
5. Violation of Clean Architecture (domain should own state rules)

**Solution**: Domain model becomes authoritative for all state, orchestrator loads fresh state from DB before operations.

## Implementation Strategy

### Phased Approach (5 Phases)

```
Phase 1: Domain Model Enhancement (2-3h) ✅ CRITICAL
├─ Add state transition validation table (include PLANNING status)
├─ Add follow-up tracking fields
└─ Implement transition guard methods

Phase 2: Database Migration (1-2h) ✅ HIGH
├─ Create Alembic migration script
├─ Add current_parent_question_id column
└─ Add current_followup_count column

Phase 3: Orchestrator Refactoring (3-4h) ✅ CRITICAL
├─ Remove SessionState enum
├─ Remove in-memory state fields
├─ Load interview entity before operations
└─ Use domain methods for transitions

Phase 4: Test Suite Updates (2-3h) ✅ HIGH
├─ Create domain state transition tests
├─ Update orchestrator unit tests
├─ Update integration tests
└─ Verify state consistency

Phase 5: Documentation & Cleanup (1h) ⚡ MEDIUM
├─ Update system architecture docs
├─ Add state machine diagram
└─ Clean up obsolete comments
```

## Key Technical Decisions

### 1. State Transition Validation
**Pattern**: Transition table + guard methods
```python
VALID_TRANSITIONS = {
    InterviewStatus.PLANNING: [InterviewStatus.IDLE, InterviewStatus.CANCELLED],
    InterviewStatus.IDLE: [InterviewStatus.QUESTIONING, InterviewStatus.CANCELLED],
    InterviewStatus.QUESTIONING: [InterviewStatus.EVALUATING, InterviewStatus.CANCELLED],
    # ... etc
}
```

### 2. Follow-Up Tracking
**Location**: Domain model (not orchestrator)
```python
class Interview:
    current_parent_question_id: UUID | None = None
    current_followup_count: int = 0  # Max 3 per question
```

### 3. Orchestrator Pattern
**Design**: Stateless coordinator
```python
# Before: self.state = SessionState.QUESTIONING
# After: interview.start() + interview_repo.update(interview)
```

## Performance Analysis

**Query Frequency**: ~2 queries/minute (50-75 total over 20-30 min interview)
**Overhead**: Negligible for long-running sessions
**Benefit**: State consistency across all interfaces

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Orchestrator regression | HIGH | Comprehensive test coverage before refactoring |
| Migration breaks in-progress interviews | MEDIUM | Default values for new fields |
| State validation bugs | MEDIUM | Unit test all transition paths |
| Performance degradation | LOW | Profile confirms <2 queries/min negligible |

## Success Criteria

✅ All tests pass (unit + integration)
✅ State transitions validated by domain
✅ No `SessionState` references in codebase
✅ Follow-up counts persist in database
✅ REST and WebSocket show consistent state
✅ Interview flow works end-to-end

## Files Affected

**Production**: 8 files
- `src/domain/models/interview.py` (domain model)
- `src/adapters/api/websocket/session_orchestrator.py` (orchestrator)
- `src/adapters/persistence/models.py` (DB schema)
- `src/adapters/persistence/mappers.py` (serialization)
- Migration script (new)
- Use cases (minor updates)

**Tests**: 4 files
- Domain state transition tests (new)
- Orchestrator unit tests (refactor)
- Integration tests (update)
- Use case tests (verify)

**Documentation**: 2 files
- `docs/system-architecture.md`
- `docs/codebase-summary.md`

## Deliverables

1. **Enhanced Domain Model** with state validation and follow-up tracking
2. **Database Migration** adding tracking fields
3. **Stateless Orchestrator** using domain methods
4. **Comprehensive Tests** covering all state transitions
5. **Updated Documentation** with state machine diagram

## Timeline Estimate

- **Phase 1**: 2-3 hours (domain foundation)
- **Phase 2**: 1-2 hours (database schema)
- **Phase 3**: 3-4 hours (orchestrator refactoring)
- **Phase 4**: 2-3 hours (test updates)
- **Phase 5**: 1 hour (documentation)

**Total**: 8-12 hours (1-2 days for single developer)

## Next Steps

1. **Review this plan** - Validate approach and estimates
2. **Assign Phase 1** - Start with domain model enhancement
3. **Code Review** - After each phase completion
4. **Integration Test** - Full interview flow after Phase 3
5. **Deploy** - After Phase 5 completion

## Resources

- **Detailed Plans**: See `phase-XX-*.md` files
- **Research**: See `research/` directory
- **Scout Report**: See `scout/scout-01-affected-files.md`
- **Parent Plan**: See `plan.md`

---

**Plan prepared by**: Claude Code
**Review Status**: ⏳ Awaiting User Review
**Questions?**: See unresolved questions in phase documents
