# Root Cause Analysis: FollowUpQuestion AttributeError

**Date**: 2025-11-09
**Error**: `'FollowUpQuestion' object has no attribute 'question_type'`
**Status**: Root cause identified

---

## Executive Summary

**Issue**: WebSocket interview handler attempts to access `question_type` and `difficulty` attributes on `FollowUpQuestion` objects, but these attributes do not exist in the `FollowUpQuestion` domain model.

**Impact**: Interview flow breaks when follow-up questions are generated, preventing candidates from continuing interviews.

**Root Cause**: Type mismatch between `FollowUpQuestion` and `Question` models in WebSocket handler logic.

**Priority**: HIGH - Blocks core interview functionality

---

## Technical Analysis

### 1. Error Location Chain

**Primary Failure Point**: `src/adapters/api/websocket/interview_handler.py:360`

```
Flow: handle_interview_websocket (line 21)
  → handle_text_answer (line 322)
  → _send_follow_up_question (line 227)
  → ERROR: Accessing follow_up_question.question_type (implicitly)
```

**Secondary Failure Point**: `src/adapters/api/websocket/interview_handler.py:158-159`

In `_send_initial_question()` and `_send_next_question()`, code accesses:
```python
"question_type": question.question_type,  # line 158, 280
"difficulty": question.difficulty,        # line 159, 281
```

These work fine for `Question` objects but fail for `FollowUpQuestion`.

### 2. Model Structure Analysis

#### FollowUpQuestion Model (`src/domain/models/follow_up_question.py`)

**Actual Attributes**:
- `id: UUID`
- `parent_question_id: UUID`
- `interview_id: UUID`
- `text: str`
- `generated_reason: str`
- `order_in_sequence: int`
- `created_at: datetime`

**Missing Attributes**: `question_type`, `difficulty`

#### Question Model (`src/domain/models/question.py`)

**Has All Attributes**:
- `id: UUID`
- `text: str`
- `question_type: QuestionType` ✓
- `difficulty: DifficultyLevel` ✓
- `skills: list[str]`
- `tags: list[str]`
- `evaluation_criteria: str | None`
- `ideal_answer: str | None`
- etc.

### 3. Where the Issue Occurs

**File**: `src/adapters/api/websocket/interview_handler.py`

**Function**: `_send_follow_up_question()` (lines 227-249)

Current implementation sends follow-up without these fields:
```python
async def _send_follow_up_question(interview_id: UUID, follow_up_question, tts):
    """Send follow-up question with audio."""
    audio_bytes = await tts.synthesize_speech(follow_up_question.text)
    audio_data = base64.b64encode(audio_bytes).decode("utf-8")

    await manager.send_message(
        interview_id,
        {
            "type": "follow_up_question",
            "question_id": str(follow_up_question.id),
            "parent_question_id": str(follow_up_question.parent_question_id),
            "text": follow_up_question.text,
            "generated_reason": follow_up_question.generated_reason,
            "order_in_sequence": follow_up_question.order_in_sequence,
            "audio_data": audio_data,
            # NO question_type or difficulty here!
        },
    )
```

**The Problem**: Frontend/client likely expects consistent message structure OR somewhere downstream code assumes all question objects have these attributes.

### 4. Repository Save Issue

**File**: `src/application/use_cases/process_answer_adaptive.py:158`

```python
await self.question_repo.save(follow_up_question)  # type: ignore
```

**Problem**: `QuestionRepositoryPort.save()` expects `Question` type, not `FollowUpQuestion`.

**Port Definition** (`src/domain/ports/question_repository_port.py:17-26`):
```python
@abstractmethod
async def save(self, question: Question) -> Question:
    """Save a question.

    Args:
        question: Question to save

    Returns:
        Saved question with updated metadata
    """
    pass
```

**Repository Implementation** (`src/adapters/persistence/question_repository.py:29-35`):
```python
async def save(self, question: Question) -> Question:
    """Save a new question to the database."""
    db_model = QuestionMapper.to_db_model(question)  # Expects Question
    self.session.add(db_model)
    await self.session.commit()
    await self.session.refresh(db_model)
    return QuestionMapper.to_domain(db_model)
```

**The `# type: ignore` comment** indicates the developer KNEW there was a type mismatch but suppressed it.

### 5. Design Inconsistency

**Current Architecture**:
- `Question` = Main questions (pre-planned, from question bank)
- `FollowUpQuestion` = Adaptive follow-ups (generated dynamically)

**Issue**: These are separate domain models with different attributes, but the code tries to treat them uniformly.

**Where This Breaks**:
1. WebSocket message format expectations
2. Repository save operations
3. Type hints and type checking

---

## Evidence from Code

### Evidence 1: FollowUpQuestion Creation

**File**: `src/application/use_cases/process_answer_adaptive.py:386-394`

```python
# Create FollowUpQuestion entity
follow_up = FollowUpQuestion(
    parent_question_id=parent_question.id,
    interview_id=interview_id,
    text=follow_up_text,
    generated_reason=f"Missing concepts: {', '.join(missing_concepts[:3])}",
    order_in_sequence=order,
)
```

No `question_type` or `difficulty` set.

### Evidence 2: Attempt to Save via Wrong Repository

**File**: `src/application/use_cases/process_answer_adaptive.py:158`

```python
await self.question_repo.save(follow_up_question)  # type: ignore
```

This calls `QuestionRepositoryPort.save()` which expects `Question`, not `FollowUpQuestion`.

### Evidence 3: WebSocket Handler Assumptions

**File**: `src/adapters/api/websocket/interview_handler.py:158-163`

```python
await manager.send_message(
    interview_id,
    {
        "type": "question",
        "question_id": str(question.id),
        "text": question.text,
        "question_type": question.question_type,  # ✓ Works for Question
        "difficulty": question.difficulty,        # ✓ Works for Question
        "index": interview.current_question_index,
        "total": len(interview.question_ids),
        "audio_data": audio_data,
    },
)
```

This pattern is used for main questions but NOT for follow-ups.

---

## Root Cause Summary

**Primary Root Cause**: Architectural type mismatch between `FollowUpQuestion` and `Question` models.

**Contributing Factors**:
1. No `FollowUpQuestionRepositoryPort` - trying to save through `QuestionRepositoryPort`
2. Different attribute sets between models
3. No inheritance relationship to ensure compatibility
4. Type ignore suppressing the error at development time

**Manifestation**: When `ProcessAnswerAdaptiveUseCase.execute()` generates a follow-up and tries to:
1. Save it via `question_repo.save()` → Type error (suppressed with `# type: ignore`)
2. Handler tries to access `.question_type` or `.difficulty` → AttributeError

---

## Recommended Fixes

### Option 1: Add Missing Attributes to FollowUpQuestion (QUICK FIX)

**File**: `src/domain/models/follow_up_question.py`

Add default values:
```python
class FollowUpQuestion(BaseModel):
    # ... existing fields ...
    question_type: QuestionType = QuestionType.TECHNICAL  # Default
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM  # Default or inherit from parent
```

**Pros**: Minimal changes, fast implementation
**Cons**: Duplicates data, doesn't fix repository type mismatch

### Option 2: Make FollowUpQuestion Inherit from Question (PROPER FIX)

**File**: `src/domain/models/follow_up_question.py`

```python
class FollowUpQuestion(Question):
    """Follow-up question extends base Question."""
    parent_question_id: UUID
    generated_reason: str
    order_in_sequence: int

    # Override fields not needed for follow-ups
    skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
```

**Pros**: Type-safe, proper OOP, reuses existing repository
**Cons**: Requires database migration, more extensive changes

### Option 3: Create Separate FollowUpQuestionRepository (CLEAN ARCHITECTURE)

**New Files**:
- `src/domain/ports/follow_up_question_repository_port.py`
- `src/adapters/persistence/follow_up_question_repository.py`
- `src/adapters/persistence/models.py` (add `FollowUpQuestionModel`)

**Changes**:
- Update `ProcessAnswerAdaptiveUseCase` to use new repository
- Keep models separate but create proper persistence layer

**Pros**: Follows clean architecture, proper separation of concerns
**Cons**: Most work, requires new database table + migration

### Option 4: Unified Question Interface (RECOMMENDED)

Create abstract base class or protocol:

**New File**: `src/domain/models/question_base.py`

```python
class QuestionBase(ABC):
    """Base interface for all question types."""
    id: UUID
    text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
```

Both `Question` and `FollowUpQuestion` implement this interface.

**Pros**: Type-safe, minimal changes, works with existing repository
**Cons**: Requires careful refactoring

---

## Immediate Action Required

**File to Fix**: `src/adapters/api/websocket/interview_handler.py:360`

**Temporary Workaround** (until proper fix):

```python
async def _send_follow_up_question(interview_id: UUID, follow_up_question, tts):
    """Send follow-up question with audio."""
    audio_bytes = await tts.synthesize_speech(follow_up_question.text)
    audio_data = base64.b64encode(audio_bytes).decode("utf-8")

    await manager.send_message(
        interview_id,
        {
            "type": "follow_up_question",
            "question_id": str(follow_up_question.id),
            "parent_question_id": str(follow_up_question.parent_question_id),
            "text": follow_up_question.text,
            # Add these missing fields:
            "question_type": "technical",  # Default for follow-ups
            "difficulty": "medium",        # Default for follow-ups
            "generated_reason": follow_up_question.generated_reason,
            "order_in_sequence": follow_up_question.order_in_sequence,
            "audio_data": audio_data,
        },
    )
```

---

## Unresolved Questions

1. **Where is logs.txt?** - User mentioned `./logs.txt` but file doesn't exist in project root. Need actual stack trace for 100% confirmation.

2. **Frontend Expectations** - Does frontend require `question_type`/`difficulty` for ALL question messages? Or only for main questions?

3. **Database State** - Are there existing follow-up questions in the database? If yes, how were they saved?

4. **Parent Question Inheritance** - Should follow-ups inherit `question_type` and `difficulty` from parent question?

5. **Migration Strategy** - If we add database table for follow-ups, how do we handle existing data?

---

## Testing Strategy

After fix implementation:

1. **Unit Tests**:
   - Test `FollowUpQuestion` model with all required attributes
   - Test repository save/retrieve for follow-ups
   - Test WebSocket message serialization

2. **Integration Tests**:
   - Full interview flow with follow-up generation
   - Verify WebSocket messages contain all required fields
   - Test database persistence

3. **Regression Tests**:
   - Ensure main questions still work
   - Verify existing interviews not broken

---

**Next Steps**: User to provide actual `logs.txt` content for stack trace confirmation, then implement recommended fix based on architectural preference.
