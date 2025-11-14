# Research: Domain Model Enrichment for Session Tracking

## Overview
Patterns for moving orchestrator session metadata into domain model.

## Follow-Up Count Tracking

### Current Problem
```python
# Orchestrator tracks this separately
self.follow_up_count = 0  # ❌ Lost on reconnection
```

### Solution: Add to Domain Model
```python
class Interview(BaseModel):
    # Existing fields...
    adaptive_follow_ups: list[UUID] = Field(default_factory=list)

    # NEW: Current follow-up tracking
    current_parent_question_id: UUID | None = None
    current_followup_count: int = 0

    def ask_followup(self, followup_id: UUID, parent_question_id: UUID) -> None:
        """Add follow-up and track count."""
        # Validate max follow-ups
        if self.current_parent_question_id == parent_question_id:
            if self.current_followup_count >= 3:
                raise ValueError(f"Max 3 follow-ups per question")
            self.current_followup_count += 1
        else:
            # New parent question, reset counter
            self.current_parent_question_id = parent_question_id
            self.current_followup_count = 1

        self.adaptive_follow_ups.append(followup_id)
        self.transition_to(InterviewStatus.FOLLOW_UP)

    def proceed_to_next_question(self) -> None:
        """Move to next main question, reset follow-up tracking."""
        # Reset follow-up tracking
        self.current_parent_question_id = None
        self.current_followup_count = 0

        if self.has_more_questions():
            self.transition_to(InterviewStatus.QUESTIONING)
        else:
            self.transition_to(InterviewStatus.COMPLETE)
            self.completed_at = datetime.utcnow()
```

## Session Progress Tracking

### Current Orchestrator State
```python
self.current_question_id: UUID | None = None      # ❌ Duplicate
self.parent_question_id: UUID | None = None       # ❌ Duplicate
self.follow_up_count = 0                          # ❌ Duplicate
```

### Domain Model Already Has Most Info
```python
class Interview(BaseModel):
    current_question_index: int = 0  # ✅ Already tracked
    question_ids: list[UUID]         # ✅ Already tracked
    adaptive_follow_ups: list[UUID]  # ✅ Already tracked

    def get_current_question_id(self) -> UUID | None:
        """Current main question being asked."""
        if self.has_more_questions():
            return self.question_ids[self.current_question_index]
        return None
```

### Add Follow-Up Context
```python
class Interview(BaseModel):
    # NEW: Track current follow-up context
    current_parent_question_id: UUID | None = None
    current_followup_count: int = 0

    def get_followup_context(self) -> dict[str, Any]:
        """Get current follow-up context."""
        return {
            "parent_question_id": self.current_parent_question_id,
            "count": self.current_followup_count,
            "max_reached": self.current_followup_count >= 3
        }
```

## Counter Reset Logic

### When Moving Between Main Questions
```python
def add_answer(self, answer_id: UUID) -> None:
    """Add answer and advance to next question."""
    self.answer_ids.append(answer_id)
    self.current_question_index += 1

    # Reset follow-up tracking for new question
    self.current_parent_question_id = None
    self.current_followup_count = 0

    self.transition_to(InterviewStatus.EVALUATING)
```

### When Asking Follow-Ups
```python
def ask_followup(self, followup_id: UUID, parent_question_id: UUID) -> None:
    """Track follow-up sequence."""
    # First follow-up for this parent
    if self.current_parent_question_id != parent_question_id:
        self.current_parent_question_id = parent_question_id
        self.current_followup_count = 1
    else:
        # Subsequent follow-up
        if self.current_followup_count >= 3:
            raise ValueError("Max 3 follow-ups per main question")
        self.current_followup_count += 1

    self.adaptive_follow_ups.append(followup_id)
    self.transition_to(InterviewStatus.FOLLOW_UP)
```

## Database Schema Changes

### New Fields Required
```python
class InterviewModel(Base):
    # Existing fields...
    adaptive_follow_ups: Mapped[list[UUID]] = mapped_column(...)

    # NEW fields for follow-up tracking
    current_parent_question_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        default=None
    )
    current_followup_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
```

### Migration Script
```python
"""Add follow-up tracking fields.

Revision ID: YYYYMMDD_followup_tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column(
        'interviews',
        sa.Column('current_parent_question_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'interviews',
        sa.Column('current_followup_count', sa.Integer(), nullable=False, server_default='0')
    )

def downgrade():
    op.drop_column('interviews', 'current_followup_count')
    op.drop_column('interviews', 'current_parent_question_id')
```

## Backward Compatibility

### Default Values for New Fields
```python
class Interview(BaseModel):
    current_parent_question_id: UUID | None = None  # ✅ Defaults to None
    current_followup_count: int = 0                 # ✅ Defaults to 0

    # Pydantic handles missing fields gracefully
```

### Migration Strategy for Existing Interviews
```python
# Existing interviews in-progress will get defaults
# No data migration needed since tracking starts fresh
# Worst case: follow-up count resets mid-interview (acceptable)
```

## Domain Methods for Follow-Up Lifecycle

### Complete Set of Methods
```python
def ask_followup(self, followup_id: UUID, parent_question_id: UUID) -> None:
    """Transition to follow-up mode."""
    # ... validation logic above ...

def answer_followup(self) -> None:
    """Record that follow-up was answered, return to evaluation."""
    if self.status != InterviewStatus.FOLLOW_UP:
        raise ValueError(f"Not in FOLLOW_UP state: {self.status}")
    self.transition_to(InterviewStatus.EVALUATING)

def proceed_to_next_question(self) -> None:
    """Move to next main question or complete."""
    # Reset follow-up context
    self.current_parent_question_id = None
    self.current_followup_count = 0

    if self.has_more_questions():
        self.transition_to(InterviewStatus.QUESTIONING)
    else:
        self.transition_to(InterviewStatus.COMPLETE)
        self.completed_at = datetime.utcnow()

def can_ask_more_followups(self) -> bool:
    """Check if more follow-ups allowed for current question."""
    return self.current_followup_count < 3
```

## Key Benefits

1. **Persistence**: Follow-up counts survive process restarts
2. **Single Source**: Orchestrator doesn't track duplicate data
3. **Business Rules**: Max 3 follow-ups enforced in domain
4. **Testability**: Follow-up logic tested independently
5. **Observability**: REST API can see follow-up progress

## Testing Strategy

```python
def test_followup_counter_increments():
    """Test follow-up counter increments correctly."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
    parent_q = uuid4()

    # First follow-up
    interview.ask_followup(uuid4(), parent_q)
    assert interview.current_followup_count == 1

    # Second follow-up (same parent)
    interview.answer_followup()  # Back to EVALUATING
    interview.ask_followup(uuid4(), parent_q)
    assert interview.current_followup_count == 2

def test_followup_counter_resets_on_new_question():
    """Test counter resets when moving to new main question."""
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.EVALUATING)
    parent_q = uuid4()

    # Add follow-up
    interview.ask_followup(uuid4(), parent_q)
    assert interview.current_followup_count == 1

    # Move to next question
    interview.answer_followup()
    interview.proceed_to_next_question()
    assert interview.current_followup_count == 0
    assert interview.current_parent_question_id is None
```
