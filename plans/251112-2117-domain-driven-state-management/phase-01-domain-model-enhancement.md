# Phase 1: Domain Model Enhancement

## Context Links
- **Parent Plan**: [plan.md](./plan.md)
- **Dependencies**: None (foundational phase)
- **Related Docs**:
  - `docs/system-architecture.md`
  - Research: [researcher-01-state-machine-patterns.md](./research/researcher-01-state-machine-patterns.md)
  - Research: [researcher-03-domain-model-enrichment.md](./research/researcher-03-domain-model-enrichment.md)

## Overview

**Date**: 2025-11-12
**Description**: Add state transition validation and follow-up tracking to Interview domain model
**Priority**: CRITICAL (blocks all other phases)
**Effort Estimate**: 2-3 hours
**Implementation Status**: ⏳ Not Started
**Review Status**: ⏳ Pending

## Key Insights

1. **State Transition Table**: Explicit transition rules prevent invalid states
2. **Follow-Up Counter**: Domain tracks per-parent-question counts (max 3)
3. **Transition Guards**: Methods validate preconditions before state changes
4. **Backward Compatible**: New fields have defaults, existing interviews unaffected

## Requirements

### Functional Requirements
- ✅ Define valid state transitions in domain constant
- ✅ Enforce max 3 follow-ups per main question
- ✅ Track current parent question for follow-up sequences
- ✅ Reset follow-up counters when advancing to next question
- ✅ Prevent invalid transitions (e.g., COMPLETE → QUESTIONING)
- ✅ Maintain existing domain API compatibility where possible

### Non-Functional Requirements
- ✅ 100% unit test coverage for new state logic
- ✅ No breaking changes to existing domain methods
- ✅ Clear error messages for validation failures
- ✅ Pydantic model validation for field types

## Architecture

### New Domain Fields
```python
class Interview(BaseModel):
    # Existing fields...
    status: InterviewStatus = InterviewStatus.IDLE

    # NEW: Follow-up tracking
    current_parent_question_id: UUID | None = None
    current_followup_count: int = 0
```

### State Transition Table
```python
VALID_TRANSITIONS = {
    InterviewStatus.PLANNING: [InterviewStatus.IDLE, InterviewStatus.CANCELLED],
    InterviewStatus.IDLE: [InterviewStatus.QUESTIONING, InterviewStatus.CANCELLED],
    InterviewStatus.QUESTIONING: [InterviewStatus.EVALUATING, InterviewStatus.CANCELLED],
    InterviewStatus.EVALUATING: [
        InterviewStatus.FOLLOW_UP,
        InterviewStatus.QUESTIONING,
        InterviewStatus.COMPLETE
    ],
    InterviewStatus.FOLLOW_UP: [InterviewStatus.EVALUATING, InterviewStatus.CANCELLED],
    InterviewStatus.COMPLETE: [],  # Terminal
    InterviewStatus.CANCELLED: [],  # Terminal
}
```

### New Domain Methods

#### Core Transition Method
```python
def transition_to(self, new_status: InterviewStatus) -> None:
    """Validate and perform state transition."""
    if new_status not in self.VALID_TRANSITIONS.get(self.status, []):
        raise ValueError(
            f"Invalid transition: {self.status} → {new_status}. "
            f"Valid: {self.VALID_TRANSITIONS[self.status]}"
        )
    self.status = new_status
    self.updated_at = datetime.utcnow()
```

#### Follow-Up Management
```python
def ask_followup(self, followup_id: UUID, parent_question_id: UUID) -> None:
    """Add follow-up question with count tracking."""
    # Handle parent question change
    if self.current_parent_question_id != parent_question_id:
        self.current_parent_question_id = parent_question_id
        self.current_followup_count = 1
    else:
        # Same parent, increment counter
        if self.current_followup_count >= 3:
            raise ValueError(
                f"Max 3 follow-ups per question. Current: {self.current_followup_count}"
            )
        self.current_followup_count += 1

    self.adaptive_follow_ups.append(followup_id)
    self.transition_to(InterviewStatus.FOLLOW_UP)

def answer_followup(self) -> None:
    """Record follow-up answered, return to evaluation."""
    if self.status != InterviewStatus.FOLLOW_UP:
        raise ValueError(f"Not in FOLLOW_UP state: {self.status}")
    self.transition_to(InterviewStatus.EVALUATING)

def can_ask_more_followups(self) -> bool:
    """Check if more follow-ups allowed."""
    return self.current_followup_count < 3
```

#### Question Navigation
```python
def proceed_to_next_question(self) -> None:
    """Move to next question or complete."""
    # Reset follow-up tracking
    self.current_parent_question_id = None
    self.current_followup_count = 0

    if self.has_more_questions():
        self.transition_to(InterviewStatus.QUESTIONING)
    else:
        self.transition_to(InterviewStatus.COMPLETE)
        self.completed_at = datetime.utcnow()
```

## Related Code Files

### To Modify
- `src/domain/models/interview.py` (lines 11-205)

### To Create
- `tests/unit/domain/test_interview_state_transitions.py` (new file)

## Implementation Steps

### Step 1: Add State Transition Table
**File**: `src/domain/models/interview.py`
**Location**: After line 20 (after `InterviewStatus` enum)

```python
class Interview(BaseModel):
    """Interview aggregate root."""

    # State transition rules
    VALID_TRANSITIONS: dict[InterviewStatus, list[InterviewStatus]] = {
        InterviewStatus.PLANNING: [InterviewStatus.IDLE, InterviewStatus.CANCELLED],
        InterviewStatus.IDLE: [InterviewStatus.QUESTIONING, InterviewStatus.CANCELLED],
        # ... rest of transitions
    }
```

### Step 2: Add Follow-Up Tracking Fields
**File**: `src/domain/models/interview.py`
**Location**: After line 39 (after `adaptive_follow_ups`)

```python
# NEW: Follow-up tracking for current session
current_parent_question_id: UUID | None = None
current_followup_count: int = 0
```

### Step 3: Implement `transition_to()` Method
**File**: `src/domain/models/interview.py`
**Location**: After line 50 (after `Config` class)

Add core transition validation method.

### Step 4: Update Existing Methods
**File**: `src/domain/models/interview.py`

Replace direct status assignments with `transition_to()`:
- `start()` → use `transition_to(InterviewStatus.QUESTIONING)`
- `complete()` → use `transition_to(InterviewStatus.COMPLETE)`
- `cancel()` → use `transition_to(InterviewStatus.CANCELLED)`
- `add_answer()` → use `transition_to(InterviewStatus.EVALUATING)`

### Step 5: Replace `add_adaptive_followup()`
**File**: `src/domain/models/interview.py`
**Location**: Lines 154-165

Replace with new `ask_followup()` method that tracks counts.

### Step 6: Add `answer_followup()` Method
**File**: `src/domain/models/interview.py`
**Location**: After `ask_followup()`

Transitions from FOLLOW_UP back to EVALUATING.

### Step 7: Replace `proceed_after_evaluation()`
**File**: `src/domain/models/interview.py`
**Location**: Lines 174-186

Replace with `proceed_to_next_question()` that resets counters.

### Step 8: Add Helper Methods
**File**: `src/domain/models/interview.py`

Add `can_ask_more_followups()` for business logic queries.

## Todo List

- [ ] Add `VALID_TRANSITIONS` constant to Interview class
- [ ] Add `current_parent_question_id` field
- [ ] Add `current_followup_count` field
- [ ] Implement `transition_to()` method
- [ ] Update `start()`, `complete()`, `cancel()` to use `transition_to()`
- [ ] Implement `ask_followup()` with counter logic
- [ ] Implement `answer_followup()` method
- [ ] Replace `proceed_after_evaluation()` with `proceed_to_next_question()`
- [ ] Add `can_ask_more_followups()` helper
- [ ] Create comprehensive unit tests for state transitions
- [ ] Test follow-up counter increment/reset logic
- [ ] Test max follow-up validation (should raise at 4th attempt)
- [ ] Test invalid transition attempts
- [ ] Run existing domain tests to ensure no regressions

## Success Criteria

✅ **State Validation**
- Invalid transitions raise `ValueError` with clear message
- All valid transitions succeed
- Terminal states (COMPLETE, CANCELLED) cannot transition

✅ **Follow-Up Tracking**
- Counter increments correctly for same parent
- Counter resets when parent changes
- Max 3 follow-ups enforced (4th raises error)
- Counter resets on `proceed_to_next_question()`

✅ **Test Coverage**
- 100% coverage for new transition logic
- All edge cases tested (terminal states, counter overflow, etc.)
- Existing tests still pass

✅ **Code Quality**
- Type hints complete
- Docstrings for all new methods
- Clear error messages

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing callers | HIGH | MEDIUM | Keep existing method signatures, add new methods |
| Invalid transition logic | MEDIUM | LOW | Comprehensive test matrix |
| Counter reset bugs | MEDIUM | MEDIUM | Test all reset scenarios |
| Pydantic validation issues | LOW | LOW | Use correct type hints |

## Security Considerations

- **Input Validation**: `transition_to()` validates enum values
- **Business Rules**: Max follow-ups enforced at domain level
- **Audit Trail**: All transitions update `updated_at` timestamp
- **No Authorization**: Domain model does not handle auth (adapter's job)

## Next Steps

After completion:
1. **Review**: Code review for transition table completeness
2. **Test**: Run full domain test suite
3. **Proceed**: Move to Phase 2 (Database Migration)
4. **Document**: Update architecture docs with state diagram
