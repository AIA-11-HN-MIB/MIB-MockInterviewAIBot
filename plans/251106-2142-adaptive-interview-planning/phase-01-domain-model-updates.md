# Phase 01: Domain Model Updates

**Phase ID**: phase-01-domain-model-updates
**Created**: 2025-11-06
**Status**: ⏳ Pending
**Priority**: P0 (Critical)
**Estimated Effort**: 4 hours

## Context

**Parent Plan**: [Main Plan](./plan.md)
**Dependencies**: None (foundation phase)
**Related Docs**: [Code Standards](../../docs/code-standards.md) | [Domain Models](../../docs/codebase-summary.md#1-domain-layer-core-business-logic)

## Overview

Extend 3 domain entities (Question, Interview, Answer) with fields for planning + adaptive evaluation. Keep changes minimal, preserve backward compatibility, maintain Clean Architecture (no external dependencies in domain).

**Date**: 2025-11-06
**Description**: Add planning/evaluation fields to domain models
**Priority**: P0 - Blocks all other phases
**Status Breakdown**:
- Question model: ⏳ Pending
- Interview model: ⏳ Pending
- Answer model: ⏳ Pending
- Validation methods: ⏳ Pending
- Tests: ⏳ Pending

## Key Insights

- **Backward compatibility**: New fields must be `Optional` to avoid breaking existing data
- **Validation**: Add domain validation methods (e.g., `has_ideal_answer()`, `is_follow_up()`)
- **No DB coupling**: Domain models remain pure, DB-specific logic stays in mappers
- **Rich models**: Add behavior methods for planning/adaptive logic (not anemic data containers)

## Requirements

### Functional Requirements

1. **Question model** must store:
   - `ideal_answer: str | None` - Reference answer for similarity comparison
   - `rationale: str | None` - Explanation of why answer is ideal
   - `is_follow_up: bool` - Flag for adaptive follow-up questions
   - `parent_question_id: UUID | None` - Link to parent if follow-up

2. **Interview model** must store:
   - `plan_metadata: dict[str, Any]` - Planning info (n, generated_at, strategy)
   - `adaptive_follow_ups: list[UUID]` - IDs of dynamically generated follow-ups

3. **Answer model** must store:
   - `similarity_score: float | None` - Cosine similarity vs ideal_answer (0-1)
   - `gaps: dict[str, Any] | None` - Detected concept gaps (missing keywords, entities)
   - `speaking_score: float | None` - Prosody/confidence score (0-100)

### Non-Functional Requirements

- Fields must be `Optional` (nullable) for backward compatibility
- Type hints required per code standards
- Docstrings for all new fields + methods
- No breaking changes to existing methods
- Performance: Additional fields should not slow down model instantiation

## Architecture

### Domain Layer Changes

```python
# BEFORE (existing)
class Question(BaseModel):
    id: UUID
    text: str
    reference_answer: str | None  # Existing field
    # ... other fields

# AFTER (extended)
class Question(BaseModel):
    id: UUID
    text: str
    reference_answer: str | None  # Kept for backward compat
    ideal_answer: str | None = None  # NEW: For similarity scoring
    rationale: str | None = None  # NEW: Why this answer is ideal
    is_follow_up: bool = False  # NEW: Identifies adaptive follow-ups
    parent_question_id: UUID | None = None  # NEW: Links to parent
    # ... other fields

    def has_ideal_answer(self) -> bool:
        """Check if question has pre-planned ideal answer."""
        return self.ideal_answer is not None and len(self.ideal_answer.strip()) > 0

    def is_adaptive_followup(self) -> bool:
        """Check if this is an adaptive follow-up question."""
        return self.is_follow_up and self.parent_question_id is not None
```

### Validation Logic

**Question validation**:
- `ideal_answer` length >10 chars if present
- `rationale` length >20 chars if present
- If `is_follow_up=True`, must have `parent_question_id`
- Parent cannot be self-referential

**Interview validation**:
- `plan_metadata` must contain `n`, `generated_at` if status=READY
- `adaptive_follow_ups` must be valid UUIDs
- Follow-up count ≤ 3 per main question (enforced in use case, validated here)

**Answer validation**:
- `similarity_score` must be 0-1 if present
- `speaking_score` must be 0-100 if present
- `gaps` must be valid JSON dict if present

## Related Code Files

### Files to Modify (3)

1. **src/domain/models/question.py** (current: 85 lines)
   - Add 4 new fields
   - Add 2 validation methods
   - Estimated: +30 lines

2. **src/domain/models/interview.py** (current: 138 lines)
   - Add 2 new fields
   - Add 1 validation method
   - Estimated: +20 lines

3. **src/domain/models/answer.py** (current: 94 lines)
   - Add 3 new fields
   - Add 2 helper methods
   - Estimated: +25 lines

### Tests to Create (3)

1. **tests/unit/domain/test_question_planning.py** (new)
   - Test ideal_answer validation
   - Test follow-up relationships
   - Test has_ideal_answer() method

2. **tests/unit/domain/test_interview_planning.py** (new)
   - Test plan_metadata structure
   - Test adaptive_follow_ups management
   - Test validation of planning state

3. **tests/unit/domain/test_answer_evaluation.py** (new)
   - Test similarity_score bounds
   - Test gaps structure
   - Test speaking_score validation

## Implementation Steps

### Step 1: Update Question Model (60 min)

**File**: `src/domain/models/question.py`

**Changes**:
```python
# Add after existing fields (around line 40)
ideal_answer: str | None = None
rationale: str | None = None
is_follow_up: bool = False
parent_question_id: UUID | None = None

# Add methods after is_suitable_for_difficulty() (around line 85)
def has_ideal_answer(self) -> bool:
    """Check if question has ideal answer for similarity scoring.

    Returns:
        True if ideal_answer is present and non-empty
    """
    return self.ideal_answer is not None and len(self.ideal_answer.strip()) > 10

def is_adaptive_followup(self) -> bool:
    """Check if this is an adaptive follow-up question.

    Returns:
        True if flagged as follow-up with parent reference
    """
    return self.is_follow_up and self.parent_question_id is not None

@property
def is_planned(self) -> bool:
    """Check if question is part of pre-planned interview.

    Returns:
        True if has ideal_answer and rationale
    """
    return self.has_ideal_answer() and self.rationale is not None
```

**Validation**: Run mypy, black formatting

### Step 2: Update Interview Model (45 min)

**File**: `src/domain/models/interview.py`

**Changes**:
```python
from typing import Any

# Add after existing fields (around line 36)
plan_metadata: dict[str, Any] = Field(default_factory=dict)
adaptive_follow_ups: list[UUID] = Field(default_factory=list)

# Add method after get_progress_percentage() (around line 130)
def add_adaptive_followup(self, question_id: UUID) -> None:
    """Add adaptive follow-up question to interview.

    Args:
        question_id: UUID of follow-up question

    Raises:
        ValueError: If follow-up limit exceeded
    """
    # Limit check (max 3 per main question enforced in use case)
    self.adaptive_follow_ups.append(question_id)
    self.updated_at = datetime.utcnow()

def is_planned(self) -> bool:
    """Check if interview has planning metadata.

    Returns:
        True if plan_metadata contains required keys
    """
    return (
        "n" in self.plan_metadata
        and "generated_at" in self.plan_metadata
    )

@property
def planned_question_count(self) -> int:
    """Get number of planned questions.

    Returns:
        Value of n from plan_metadata, or 0 if not planned
    """
    return self.plan_metadata.get("n", 0)
```

**Validation**: Ensure backward compatibility with existing Interview instances

### Step 3: Update Answer Model (45 min)

**File**: `src/domain/models/answer.py`

**Changes**:
```python
from typing import Any

# Add after existing fields (around line 56)
similarity_score: float | None = Field(None, ge=0.0, le=1.0)
gaps: dict[str, Any] | None = None
speaking_score: float | None = Field(None, ge=0.0, le=100.0)

# Add methods after is_complete() (around line 94)
def has_similarity_score(self) -> bool:
    """Check if similarity score is available.

    Returns:
        True if similarity_score is set
    """
    return self.similarity_score is not None

def has_gaps(self) -> bool:
    """Check if concept gaps were detected.

    Returns:
        True if gaps dict is present and non-empty
    """
    return self.gaps is not None and len(self.gaps) > 0

def meets_threshold(self, similarity_threshold: float = 0.8) -> bool:
    """Check if answer meets similarity threshold.

    Args:
        similarity_threshold: Minimum similarity (default 0.8)

    Returns:
        True if similarity_score >= threshold
    """
    if not self.has_similarity_score():
        return False
    return self.similarity_score >= similarity_threshold

def is_adaptive_complete(self) -> bool:
    """Check if answer meets adaptive criteria (no follow-up needed).

    Returns:
        True if similarity >=0.8 OR speaking >=85 OR no gaps
    """
    similarity_ok = self.similarity_score and self.similarity_score >= 0.8
    speaking_ok = self.speaking_score and self.speaking_score >= 85.0
    no_gaps = not self.has_gaps()

    return similarity_ok or speaking_ok or no_gaps
```

**Validation**: Run Pydantic field validators, test bound checking

### Step 4: Write Unit Tests (90 min)

**Create 3 test files**:

**File 1**: `tests/unit/domain/test_question_planning.py`
```python
import pytest
from uuid import uuid4
from src.domain.models.question import Question, QuestionType, DifficultyLevel

def test_question_has_ideal_answer_when_present():
    q = Question(
        text="What is Python?",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.EASY,
        ideal_answer="Python is a high-level programming language...",
    )
    assert q.has_ideal_answer() is True

def test_question_has_ideal_answer_when_absent():
    q = Question(
        text="What is Python?",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.EASY,
    )
    assert q.has_ideal_answer() is False

def test_question_is_adaptive_followup_when_true():
    parent_id = uuid4()
    q = Question(
        text="Can you elaborate?",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.EASY,
        is_follow_up=True,
        parent_question_id=parent_id,
    )
    assert q.is_adaptive_followup() is True

# Add 5+ more test cases...
```

**File 2**: `tests/unit/domain/test_interview_planning.py`
**File 3**: `tests/unit/domain/test_answer_evaluation.py`

Run tests: `pytest tests/unit/domain/ -v`

## Todo List

### Question Model
- [ ] Add ideal_answer field with Optional type
- [ ] Add rationale field with Optional type
- [ ] Add is_follow_up boolean field (default False)
- [ ] Add parent_question_id field with Optional UUID type
- [ ] Implement has_ideal_answer() method
- [ ] Implement is_adaptive_followup() method
- [ ] Add is_planned property
- [ ] Write 8+ unit tests for Question planning fields
- [ ] Run mypy type checking
- [ ] Format with black

### Interview Model
- [ ] Add plan_metadata dict field with default_factory
- [ ] Add adaptive_follow_ups list field with default_factory
- [ ] Implement add_adaptive_followup() method
- [ ] Implement is_planned() method
- [ ] Add planned_question_count property
- [ ] Write 6+ unit tests for Interview planning
- [ ] Test backward compatibility with existing interviews
- [ ] Run mypy type checking
- [ ] Format with black

### Answer Model
- [ ] Add similarity_score field with bounds (0-1)
- [ ] Add gaps dict field with Optional type
- [ ] Add speaking_score field with bounds (0-100)
- [ ] Implement has_similarity_score() method
- [ ] Implement has_gaps() method
- [ ] Implement meets_threshold() method
- [ ] Implement is_adaptive_complete() method
- [ ] Write 8+ unit tests for Answer evaluation fields
- [ ] Test Pydantic field validation (bounds)
- [ ] Run mypy type checking
- [ ] Format with black

### Integration
- [ ] Run full domain test suite: `pytest tests/unit/domain/`
- [ ] Verify no breaking changes to existing tests
- [ ] Check test coverage >80% for new code
- [ ] Document new fields in docstrings

## Success Criteria

- [ ] Question model has 4 new fields + 3 methods
- [ ] Interview model has 2 new fields + 3 methods
- [ ] Answer model has 3 new fields + 4 methods
- [ ] All new fields are Optional (nullable)
- [ ] Type hints pass mypy check
- [ ] Code formatted with black (100 char lines)
- [ ] Unit tests cover new fields/methods (>80% coverage)
- [ ] No breaking changes to existing domain logic
- [ ] Docstrings follow Google style guide
- [ ] All tests pass: `pytest tests/unit/domain/ --cov=src/domain/models`

## Risk Assessment

**Low Risk**:
- Domain models are pure Python (no DB/API coupling)
- Changes are additive (no removal of existing fields)
- Optional fields maintain backward compatibility

**Potential Issues**:
- Pydantic v2 field validation edge cases
  - *Mitigation*: Comprehensive unit tests for bounds
- Circular reference if parent_question_id not validated
  - *Mitigation*: Add validation in Question.__init__ or use_case

## Security Considerations

- Ideal answers may contain sensitive technical info → no special handling in domain (handled in API layer)
- Plan metadata should not expose internal AI strategies → validated in use case
- Gaps dict should sanitize inputs → validated in adapters before domain

## Next Steps

1. Complete all checkboxes in Todo List
2. Review code changes with team
3. Merge to feature branch
4. **Proceed to Phase 02**: Database migration (depends on these domain changes)

---

**Phase Status**: Ready for implementation
**Blocking**: Phase 02, 03, 04 (all depend on domain models)
**Owner**: Backend domain team
