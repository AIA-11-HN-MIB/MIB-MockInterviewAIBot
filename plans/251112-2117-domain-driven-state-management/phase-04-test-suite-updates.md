# Phase 4: Test Suite Updates

## Context Links
- **Parent Plan**: [plan.md](./plan.md)
- **Dependencies**: Phase 3 (Orchestrator Refactoring)
- **Related Docs**:
  - Scout: [scout-01-affected-files.md](./scout/scout-01-affected-files.md)

## Overview

**Date**: 2025-11-12
**Description**: Update test suite to reflect stateless orchestrator and domain state management
**Priority**: HIGH (validates refactoring correctness)
**Effort Estimate**: 2-3 hours
**Implementation Status**: ⏳ Not Started
**Review Status**: ⏳ Pending

## Key Insights

1. **Unit Tests**: Mock domain entities instead of orchestrator state
2. **Integration Tests**: Verify state persisted to DB after operations
3. **Domain Tests**: Add comprehensive state transition test coverage
4. **Negative Tests**: Verify invalid transitions raise proper errors

## Requirements

### Functional Requirements
- ✅ Remove all `SessionState` test references
- ✅ Update mocks to return `Interview` entities
- ✅ Verify orchestrator loads state from domain
- ✅ Test state consistency before/after operations
- ✅ Add domain state transition tests
- ✅ Test follow-up counter logic
- ✅ Test invalid transition handling

### Non-Functional Requirements
- ✅ All tests pass after refactoring
- ✅ Test coverage ≥90% for domain state logic
- ✅ Fast unit tests (<1s per test)
- ✅ Clear test names describing scenarios

## Architecture

### Test Structure Changes

#### Before: Testing Orchestrator State
```python
def test_handle_answer_transitions_to_evaluating():
    orchestrator = InterviewSessionOrchestrator(...)
    orchestrator.state = SessionState.QUESTIONING  # ❌ Direct state

    await orchestrator.handle_answer("Test answer")

    assert orchestrator.state == SessionState.EVALUATING  # ❌ Check local state
```

#### After: Testing Domain State
```python
async def test_handle_answer_updates_domain_state():
    # Arrange - mock domain entity
    interview = Interview(
        id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewStatus.QUESTIONING
    )

    interview_repo_mock = Mock()
    interview_repo_mock.get_by_id.return_value = interview

    orchestrator = InterviewSessionOrchestrator(interview.id, ws_mock, container_mock)

    # Act
    await orchestrator.handle_answer("Test answer")

    # Assert - verify domain state updated
    assert interview.status == InterviewStatus.EVALUATING
    interview_repo_mock.update.assert_called_once()
```

## Related Code Files

### To Modify
- `tests/unit/adapters/api/websocket/test_session_orchestrator.py`
- `tests/integration/test_interview_flow_orchestrator.py`
- `tests/unit/use_cases/test_complete_interview.py`

### To Create
- `tests/unit/domain/test_interview_state_transitions.py` (if doesn't exist)
- `tests/unit/domain/test_interview_followup_tracking.py`

## Implementation Steps

### Step 1: Create Domain State Transition Tests
**File**: `tests/unit/domain/test_interview_state_transitions.py` (new)

```python
import pytest
from uuid import uuid4
from src.domain.models.interview import Interview, InterviewStatus

def test_valid_transition_idle_to_questioning():
    """Test valid IDLE → QUESTIONING transition."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)

    interview.start()

    assert interview.status == InterviewStatus.QUESTIONING
    assert interview.started_at is not None

def test_invalid_transition_idle_to_evaluating():
    """Test invalid IDLE → EVALUATING transition raises error."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)

    with pytest.raises(ValueError, match="Invalid transition"):
        interview.transition_to(InterviewStatus.EVALUATING)

def test_terminal_state_complete_no_transitions():
    """Test COMPLETE state cannot transition."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.COMPLETE)

    with pytest.raises(ValueError, match="Invalid transition"):
        interview.transition_to(InterviewStatus.QUESTIONING)

def test_all_valid_transitions():
    """Test all valid state transitions."""
    valid_paths = [
        (InterviewStatus.PLANNING, InterviewStatus.IDLE),
        (InterviewStatus.IDLE, InterviewStatus.QUESTIONING),
        (InterviewStatus.QUESTIONING, InterviewStatus.EVALUATING),
        (InterviewStatus.EVALUATING, InterviewStatus.FOLLOW_UP),
        (InterviewStatus.EVALUATING, InterviewStatus.QUESTIONING),
        (InterviewStatus.EVALUATING, InterviewStatus.COMPLETE),
        (InterviewStatus.FOLLOW_UP, InterviewStatus.EVALUATING),
    ]

    for from_status, to_status in valid_paths:
        interview = Interview(candidate_id=uuid4(), status=from_status)
        interview.transition_to(to_status)
        assert interview.status == to_status

def test_planning_to_idle_via_mark_ready():
    """Test PLANNING → IDLE transition via mark_ready()."""
    interview = Interview(
        candidate_id=uuid4(),
        status=InterviewStatus.PLANNING
    )
    cv_analysis_id = uuid4()

    interview.mark_ready(cv_analysis_id)

    assert interview.status == InterviewStatus.IDLE
    assert interview.cv_analysis_id == cv_analysis_id
```

### Step 2: Create Follow-Up Tracking Tests
**File**: `tests/unit/domain/test_interview_followup_tracking.py` (new)

```python
def test_followup_counter_increments():
    """Test follow-up counter increments for same parent."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
    parent_q = uuid4()

    interview.ask_followup(uuid4(), parent_q)
    assert interview.current_followup_count == 1
    assert interview.status == InterviewStatus.FOLLOW_UP

    interview.answer_followup()
    interview.ask_followup(uuid4(), parent_q)
    assert interview.current_followup_count == 2

def test_followup_counter_resets_on_new_parent():
    """Test counter resets when parent question changes."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
    parent_q1 = uuid4()
    parent_q2 = uuid4()

    interview.ask_followup(uuid4(), parent_q1)
    assert interview.current_followup_count == 1

    interview.answer_followup()
    interview.ask_followup(uuid4(), parent_q2)
    assert interview.current_followup_count == 1  # Reset
    assert interview.current_parent_question_id == parent_q2

def test_max_followups_enforced():
    """Test max 3 follow-ups per question."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
    parent_q = uuid4()

    # Add 3 follow-ups
    for i in range(3):
        interview.ask_followup(uuid4(), parent_q)
        interview.answer_followup()

    # 4th should fail
    with pytest.raises(ValueError, match="Max 3 follow-ups"):
        interview.ask_followup(uuid4(), parent_q)

def test_proceed_to_next_question_resets_counters():
    """Test counters reset when moving to next question."""
    interview = Interview(
        candidate_id=uuid4(),
        status=InterviewStatus.EVALUATING,
        question_ids=[uuid4(), uuid4()],
        current_question_index=0
    )
    parent_q = uuid4()

    interview.ask_followup(uuid4(), parent_q)
    assert interview.current_followup_count == 1

    interview.answer_followup()
    interview.proceed_to_next_question()

    assert interview.current_followup_count == 0
    assert interview.current_parent_question_id is None
    assert interview.status == InterviewStatus.QUESTIONING
```

### Step 3: Update Orchestrator Unit Tests
**File**: `tests/unit/adapters/api/websocket/test_session_orchestrator.py`

**Changes**:
- Remove all `SessionState` imports and references
- Mock `interview_repository_port` to return `Interview` entities
- Update assertions to check domain state via `interview.status`
- Add parameter passing tests (verify `interview` passed through)

**Example Refactored Test**:
```python
@pytest.mark.asyncio
async def test_start_session_transitions_to_questioning():
    """Test start_session uses domain start() method."""
    # Arrange
    interview_id = uuid4()
    interview = Interview(
        id=interview_id,
        candidate_id=uuid4(),
        status=InterviewStatus.IDLE,
        question_ids=[uuid4()]
    )

    interview_repo_mock = AsyncMock()
    interview_repo_mock.get_by_id.return_value = interview

    question_mock = Mock()
    question_mock.id = interview.question_ids[0]
    question_mock.text = "Test question"

    question_repo_mock = AsyncMock()
    question_repo_mock.get_by_id.return_value = question_mock

    container_mock = Mock()
    container_mock.interview_repository_port.return_value = interview_repo_mock
    container_mock.question_repository_port.return_value = question_repo_mock
    container_mock.text_to_speech_port.return_value = AsyncMock()

    orchestrator = InterviewSessionOrchestrator(
        interview_id=interview_id,
        websocket=AsyncMock(),
        container=container_mock
    )

    # Act
    await orchestrator.start_session()

    # Assert
    assert interview.status == InterviewStatus.QUESTIONING
    interview_repo_mock.update.assert_called_once_with(interview)
```

### Step 4: Update Integration Tests
**File**: `tests/integration/test_interview_flow_orchestrator.py`

**Changes**:
- Remove `SessionState` checks
- Add DB state verification after each operation
- Test state persistence (reload from DB and verify)

**Example Integration Test**:
```python
@pytest.mark.asyncio
async def test_full_interview_flow_persists_state():
    """Test complete interview flow with DB state persistence."""
    # Create interview
    interview = await create_test_interview()
    assert interview.status == InterviewStatus.IDLE

    # Start session
    orchestrator = InterviewSessionOrchestrator(interview.id, ws_mock, container)
    await orchestrator.start_session()

    # Verify state persisted
    reloaded = await interview_repo.get_by_id(interview.id)
    assert reloaded.status == InterviewStatus.QUESTIONING

    # Handle answer
    await orchestrator.handle_answer("Test answer")

    # Verify state persisted again
    reloaded = await interview_repo.get_by_id(interview.id)
    assert reloaded.status == InterviewStatus.EVALUATING
```

### Step 5: Update Use Case Tests
**File**: `tests/unit/use_cases/test_complete_interview.py`

**Verify**:
- Tests still pass with domain methods
- Add test for invalid completion state

```python
def test_complete_interview_invalid_state_raises_error():
    """Test completing interview from invalid state raises error."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)
    interview_repo_mock = Mock()
    interview_repo_mock.get_by_id.return_value = interview

    use_case = CompleteInterviewUseCase(interview_repo_mock, None, None, None, None)

    with pytest.raises(ValueError, match="Cannot complete interview with status"):
        await use_case.execute(interview.id)
```

### Step 6: Run Full Test Suite
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only domain tests
pytest tests/unit/domain/

# Run only orchestrator tests
pytest tests/unit/adapters/api/websocket/

# Run integration tests
pytest tests/integration/
```

### Step 7: Fix Failing Tests
Iterate on any failing tests, ensuring:
- Mocks return correct domain entities
- Assertions check domain state, not orchestrator state
- Parameter passing correct (interview entity through call chain)

## Todo List

- [ ] Create `test_interview_state_transitions.py` with full transition matrix
- [ ] Create `test_interview_followup_tracking.py` with counter tests
- [ ] Test terminal states (COMPLETE, CANCELLED) cannot transition
- [ ] Test invalid transitions raise ValueError
- [ ] Update orchestrator unit tests to mock domain entities
- [ ] Remove all `SessionState` references from tests
- [ ] Update integration tests to verify DB persistence
- [ ] Add tests for `can_ask_more_followups()` logic
- [ ] Verify use case tests still pass
- [ ] Run full test suite and fix failures
- [ ] Achieve ≥90% coverage for domain state logic

## Success Criteria

✅ **Domain Tests**
- All state transitions tested (valid + invalid)
- Follow-up counter logic fully tested
- Terminal states cannot transition
- Max follow-ups enforced

✅ **Orchestrator Tests**
- No `SessionState` references
- Mocks return `Interview` entities
- Tests verify domain state updates
- Parameter passing tests added

✅ **Integration Tests**
- State persistence verified
- Full interview flow works
- Counters reset correctly

✅ **Coverage**
- Domain state logic ≥90% coverage
- All new methods tested
- Edge cases covered

✅ **Test Suite Health**
- All tests pass
- No flaky tests
- Fast execution (<30s total)

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Many test failures | HIGH | MEDIUM | Fix incrementally, one file at a time |
| Missed edge cases | MEDIUM | MEDIUM | Code review test coverage |
| Flaky integration tests | MEDIUM | LOW | Use test database, clean state |
| Low coverage | MEDIUM | LOW | Add missing test cases |

## Security Considerations

- **Test Data Isolation**: Each test uses unique UUIDs
- **No Production Access**: Tests use test database only
- **Secrets in Tests**: Use environment variables, not hardcoded
- **Cleanup**: Integration tests clean up test data

## Next Steps

After completion:
1. **Review Coverage**: Check coverage report for gaps
2. **CI/CD**: Ensure tests pass in CI pipeline
3. **Proceed**: Move to Phase 5 (Documentation)
4. **Regression Testing**: Run manual smoke tests
