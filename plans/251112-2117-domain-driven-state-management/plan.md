# Implementation Plan: Domain-Driven State Management

**Plan ID**: 251112-2117
**Created**: 2025-11-12
**Status**: Ready for Review
**Estimated Effort**: 8-12 hours

## Executive Summary

Migrate from dual state machines (orchestrator `SessionState` + domain `InterviewStatus`) to single source of truth in domain model. Eliminates state inconsistency between WebSocket sessions and database.

## Problem Statement

Currently `InterviewSessionOrchestrator` maintains in-memory `self.state` that doesn't sync with `interview.status` in database. This causes:
- State divergence between WebSocket and REST API views
- Duplicate business logic in orchestrator layer
- Lost tracking data (follow-up counts) on any disruption
- Violation of Clean Architecture (domain should own state rules)

## Solution Approach

**Approach 1: Single Source of Truth (Domain-Driven)**
- Remove all in-memory state from orchestrator
- Domain model becomes authoritative for all state
- Orchestrator loads fresh state from DB before operations
- Domain enforces valid state transitions with transition table

## Requirements Clarifications

1. **Reconnection**: Not required - simplifies migration
2. **Concurrent Access**: Single client only - no locking needed
3. **Performance**: 7-10 questions over 20-30 min = ~2 queries/min (negligible)
4. **State Validation**: Domain enforces transitions (prevent COMPLETE → QUESTIONING)
5. **Follow-Up Tracking**: Move `self.follow_up_count` to domain model

## Implementation Phases

### Phase 1: Domain Model Enhancement ⏳ Not Started
**File**: [phase-01-domain-model-enhancement.md](./phase-01-domain-model-enhancement.md)
**Effort**: 2-3 hours
**Priority**: CRITICAL
**Dependencies**: None

- Add state transition validation table (include PLANNING status)
- Add follow-up tracking fields (current_parent_question_id, current_followup_count)
- Implement transition guard methods (transition_to, ask_followup, answer_followup)
- Full unit test coverage

**Progress**: 0% (0/14 tasks)

### Phase 2: Database Migration ⏳ Not Started
**File**: [phase-02-database-migration.md](./phase-02-database-migration.md)
**Effort**: 1-2 hours
**Priority**: HIGH
**Dependencies**: Phase 1

- Create Alembic migration script
- Add `current_parent_question_id` column
- Add `current_followup_count` column
- Test upgrade/downgrade paths

**Progress**: 0% (0/5 tasks)

### Phase 3: Orchestrator Refactoring ⏳ Not Started
**File**: [phase-03-orchestrator-refactoring.md](./phase-03-orchestrator-refactoring.md)
**Effort**: 3-4 hours
**Priority**: CRITICAL
**Dependencies**: Phases 1, 2

- Remove `SessionState` enum and in-memory state
- Load `interview` entity before operations
- Replace state transitions with domain methods
- Simplify orchestrator to stateless coordinator

**Progress**: 0% (0/12 tasks)

### Phase 4: Test Suite Updates ⏳ Not Started
**File**: [phase-04-test-suite-updates.md](./phase-04-test-suite-updates.md)
**Effort**: 2-3 hours
**Priority**: HIGH
**Dependencies**: Phase 3

- Update orchestrator unit tests
- Update integration tests
- Verify state consistency
- Add negative test cases

**Progress**: 0% (0/7 tasks)

### Phase 5: Documentation & Cleanup ⏳ Not Started
**File**: [phase-05-documentation-cleanup.md](./phase-05-documentation-cleanup.md)
**Effort**: 1 hour
**Priority**: MEDIUM
**Dependencies**: Phase 4

- Update system architecture docs
- Update codebase summary
- Add state machine diagram
- Remove obsolete comments

**Progress**: 0% (0/4 tasks)

## Overall Progress

**Total Tasks**: 42
**Completed**: 0 (0%)
**In Progress**: 0 (0%)
**Not Started**: 42 (100%)

## Success Criteria

✅ All tests pass (unit + integration)
✅ State transitions validated by domain
✅ No `SessionState` references in codebase
✅ Follow-up counts persist in database
✅ REST and WebSocket show consistent state
✅ Interview flow works end-to-end

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Orchestrator regression | HIGH | Comprehensive test coverage before refactoring |
| Migration breaks in-progress interviews | MEDIUM | Default values for new fields, acceptable reset |
| Performance degradation | LOW | Profile shows 2 queries/min negligible |
| State validation bugs | MEDIUM | Unit test all transition paths |

## Resources

- **Research Reports**: [./research/](./research/)
- **Scout Reports**: [./scout/](./scout/)
- **Related Docs**:
  - `docs/system-architecture.md`
  - `src/domain/models/interview.py`
  - `src/adapters/api/websocket/session_orchestrator.py`
