# Research: State Machine Patterns in Domain-Driven Design

## Overview
Research on state machine patterns for interview/session management in DDD context.

## State Transition Validation Patterns

### 1. Transition Table Pattern
Define valid transitions explicitly in domain model:
```python
class Interview(BaseModel):
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
        InterviewStatus.COMPLETE: [],  # Terminal state
        InterviewStatus.CANCELLED: [],  # Terminal state
    }

    def transition_to(self, new_status: InterviewStatus) -> None:
        """Enforce valid state transitions."""
        if new_status not in self.VALID_TRANSITIONS.get(self.status, []):
            raise ValueError(
                f"Invalid transition: {self.status} → {new_status}. "
                f"Valid transitions: {self.VALID_TRANSITIONS[self.status]}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()
```

### 2. Explicit Method Pattern
Each transition has dedicated method:
```python
def begin_questioning(self) -> None:
    """Start asking questions."""
    self.transition_to(InterviewStatus.QUESTIONING)

def begin_evaluation(self) -> None:
    """Start evaluating answer."""
    self.transition_to(InterviewStatus.EVALUATING)

def ask_followup(self, followup_id: UUID) -> None:
    """Transition to follow-up mode."""
    self.transition_to(InterviewStatus.FOLLOW_UP)
    self.adaptive_follow_ups.append(followup_id)
```

## Best Practices for Long-Running Sessions (20-30 min)

### Database-Backed State
- **Acceptable latency**: Interview sessions have 2-5 min between questions
- **Query frequency**: ~10-15 state transitions per interview (7-10 questions + follow-ups)
- **DB overhead**: ~100ms per query << 2 min wait time between questions
- **Conclusion**: DB queries negligible for this workload

### State Persistence Strategy
```python
# Before each operation
interview = await interview_repo.get_by_id(interview_id)

# Validate current state
if interview.status != expected_status:
    raise ValueError(f"Expected {expected_status}, got {interview.status}")

# Perform domain operation
interview.begin_evaluation()

# Persist immediately
await interview_repo.update(interview)
```

## Preventing Invalid Transitions

### Guard Clauses in Domain Methods
```python
def complete(self) -> None:
    """Complete interview - only from EVALUATING."""
    if self.status != InterviewStatus.EVALUATING:
        raise ValueError(f"Cannot complete from {self.status}")
    if self.has_more_questions():
        raise ValueError("Cannot complete with remaining questions")

    self.status = InterviewStatus.COMPLETE
    self.completed_at = datetime.utcnow()
    self.updated_at = datetime.utcnow()
```

### Idempotent Operations
Allow safe retries for network failures:
```python
def complete(self) -> None:
    """Idempotent completion."""
    if self.status == InterviewStatus.COMPLETE:
        return  # Already complete, no-op

    if self.status != InterviewStatus.EVALUATING:
        raise ValueError(f"Cannot complete from {self.status}")
    # ... rest of logic
```

## Trade-offs: In-Memory vs Database State

### In-Memory State (Current Orchestrator)
**Pros:**
- Fast access (no I/O)
- Simple implementation

**Cons:**
- Lost on disconnection
- Inconsistent with DB
- Not observable by other processes
- Testing requires mocking both states

### Database-Backed State (Recommended)
**Pros:**
- Single source of truth
- Survives process restarts
- Observable by REST API
- Simplified testing (only domain)

**Cons:**
- DB query overhead (negligible for interviews)
- Requires transaction management

## Implementation Recommendations

1. **Remove orchestrator state** - Delete `SessionState` enum entirely
2. **Always fetch fresh** - Load interview from DB before operations
3. **Validate in domain** - Use transition table + guard clauses
4. **Update immediately** - Persist after each transition
5. **Test domain separately** - Unit test state transitions without DB

## References
- Domain-Driven Design (Evans) - Aggregate consistency boundaries
- Clean Architecture (Martin) - Domain independence principle
- State pattern for complex transitions (GoF Design Patterns)
