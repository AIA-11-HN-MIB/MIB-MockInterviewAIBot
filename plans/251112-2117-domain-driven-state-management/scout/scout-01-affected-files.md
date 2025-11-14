# Scout Report: Files Affected by State Management Refactoring

## Overview
Complete list of files requiring modification for domain-driven state management.

## Core Files to Modify

### 1. Domain Model
**File**: `src/domain/models/interview.py`
**Lines**: 11-205
**Changes Required**:
- Add `VALID_TRANSITIONS` table (after line 20)
- Add `transition_to()` method for state validation (after line 50)
- Add `current_parent_question_id: UUID | None` field (after line 39)
- Add `current_followup_count: int` field (after line 39)
- Modify `ask_followup()` to track count (line 154-165)
- Add `answer_followup()` method (new)
- Add `proceed_to_next_question()` method (replace `proceed_after_evaluation()` line 174-186)
- Add `can_ask_more_followups()` method (new)
- Update existing state transition methods to use `transition_to()`

**Impact**: HIGH - Core domain logic changes

### 2. WebSocket Orchestrator
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 1-623
**Changes Required**:
- Remove `SessionState` enum (lines 31-38)
- Remove `self.state` from `__init__` (line 69)
- Remove `self.current_question_id` (line 70)
- Remove `self.parent_question_id` (line 71)
- Remove `self.follow_up_count` (line 72)
- Remove `_transition()` method entirely (lines 81-128)
- Refactor `start_session()` to load domain state (lines 130-195)
- Refactor `handle_answer()` to check `interview.status` instead of `self.state` (lines 197-216)
- Refactor `_handle_main_question_answer()` to pass `interview` entity (lines 218-289)
- Refactor `_handle_followup_answer()` to pass `interview` entity (lines 291-362)
- Refactor `_generate_and_send_followup()` to use domain methods (lines 364-432)
- Refactor `_send_next_main_question()` to use domain methods (lines 434-487)
- Update `_complete_interview()` to use domain methods (lines 489-562)
- Remove `get_state()` method or simplify (lines 608-622)

**Impact**: HIGH - Major refactoring

### 3. Database Models
**File**: `src/adapters/persistence/models.py`
**Lines**: 111-161
**Changes Required**:
- Add `current_parent_question_id` column (after line 151)
- Add `current_followup_count` column (after line 151)

**Impact**: MEDIUM - Schema change requires migration

### 4. Database Mappers
**File**: `src/adapters/persistence/mappers.py`
**Lines**: Check mapping logic
**Changes Required**:
- Map new `current_parent_question_id` field
- Map new `current_followup_count` field

**Impact**: LOW - Simple field addition

## Use Cases to Update

### 5. Process Answer Use Case
**File**: `src/application/use_cases/process_answer_adaptive.py`
**Lines**: 88-100
**Changes Required**:
- Update state validation to use domain transition rules
- Ensure interview entity is passed through and updated

**Impact**: LOW - Already validates interview.status

### 6. Complete Interview Use Case
**File**: `src/application/use_cases/complete_interview.py`
**Lines**: 50-60
**Changes Required**:
- Use domain `complete()` method instead of direct status assignment
- May already be correct if using domain methods

**Impact**: LOW - Verify current implementation

### 7. Plan Interview Use Case
**File**: `src/application/use_cases/plan_interview.py`
**Lines**: Check initialization logic
**Changes Required**:
- Ensure new fields initialized with defaults

**Impact**: LOW - Defaults handle this

## REST API Routes

### 8. Interview Routes
**File**: `src/adapters/api/rest/interview_routes.py`
**Lines**: 267-274
**Changes Required**:
- Verify status display logic still works
- No changes likely needed (reads from domain)

**Impact**: MINIMAL - Read-only access

## Test Files to Update

### 9. Orchestrator Unit Tests
**File**: `tests/unit/adapters/api/websocket/test_session_orchestrator.py`
**Changes Required**:
- Remove tests for `SessionState` enum
- Remove tests for `_transition()` method
- Add tests for domain state loading
- Update mocks to return interview entities
- Test orchestrator routes based on `interview.status`

**Impact**: HIGH - Major test refactoring

### 10. Orchestrator Integration Tests
**File**: `tests/integration/test_interview_flow_orchestrator.py`
**Changes Required**:
- Update to verify state persisted in DB
- Add tests for follow-up count tracking
- Test state consistency after operations

**Impact**: MEDIUM - Update assertions

### 11. Domain Model Unit Tests
**File**: `tests/unit/domain/test_interview.py` (if exists)
**Changes Required**:
- Add tests for `transition_to()` validation
- Add tests for follow-up counter logic
- Add tests for invalid state transitions
- Test `can_ask_more_followups()` logic

**Impact**: HIGH - New test coverage needed

### 12. Complete Interview Use Case Tests
**File**: `tests/unit/use_cases/test_complete_interview.py`
**Changes Required**:
- Verify tests still pass with domain methods
- Add test for invalid completion attempts

**Impact**: LOW - Minor updates

## Database Migration

### 13. New Migration Script
**File**: `alembic/versions/YYYYMMDD_add_followup_tracking.py` (new)
**Changes Required**:
- Add `current_parent_question_id` column
- Add `current_followup_count` column with default 0
- Test upgrade and downgrade paths

**Impact**: MEDIUM - New migration

## Documentation

### 14. System Architecture Doc
**File**: `docs/system-architecture.md`
**Changes Required**:
- Update state management section
- Document single source of truth pattern
- Update sequence diagrams if present

**Impact**: LOW - Documentation update

### 15. Codebase Summary
**File**: `docs/codebase-summary.md`
**Changes Required**:
- Update orchestrator description
- Note removal of dual state machines

**Impact**: LOW - Documentation update

## Summary Statistics

**Total Files**: 15 (8 production, 4 test, 1 migration, 2 docs)
**High Impact**: 4 files (domain model, orchestrator, orchestrator tests, domain tests)
**Medium Impact**: 3 files (DB models, integration tests, migration)
**Low Impact**: 8 files (mappers, use cases, routes, docs)

## Execution Order

1. **Phase 1**: Domain model changes + tests
2. **Phase 2**: Database migration
3. **Phase 3**: Orchestrator refactoring
4. **Phase 4**: Test updates
5. **Phase 5**: Documentation

## Risk Areas

- **Orchestrator refactoring**: Most complex changes, high regression risk
- **Database migration**: Affects existing interviews in-progress
- **Test coverage**: Ensure state transitions fully tested before refactoring orchestrator
