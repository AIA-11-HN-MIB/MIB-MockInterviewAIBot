# Interview State Management Guide

**Last Updated**: 2025-11-13
**Architecture**: Domain-Driven State Management

---

## Overview

Interview state is managed **exclusively** by the `Interview` domain entity. The orchestrator is a **stateless coordinator** that loads fresh state from the database before each operation.

## State Lifecycle

```
┌─────────┐
│ PLANNING│  Interview being planned
└────┬────┘
     │
     v
┌─────────┐
│  IDLE   │  Ready to start, waiting
└────┬────┘
     │ start()
     v
┌──────────────┐
│ QUESTIONING  │  Asking a main question
└──────┬───────┘
       │ handle_answer()
       v
┌─────────────┐
│ EVALUATING  │  Processing answer
└──┬───┬───┬──┘
   │   │   │
   │   │   └─ proceed_to_next_question() → QUESTIONING (more questions)
   │   │
   │   └─ proceed_to_next_question() → COMPLETE (no more questions)
   │
   └─ ask_followup() → FOLLOW_UP
                       │
                       └─ answer_followup() → EVALUATING
```

## State Transition Rules

| From State | Valid Next States | Trigger Method |
|------------|------------------|----------------|
| PLANNING | IDLE, CANCELLED | `mark_ready()`, `cancel()` |
| IDLE | QUESTIONING, CANCELLED | `start()`, `cancel()` |
| QUESTIONING | EVALUATING, CANCELLED | `add_answer()`, `cancel()` |
| EVALUATING | FOLLOW_UP, QUESTIONING, COMPLETE, CANCELLED | `ask_followup()`, `proceed_to_next_question()`, `complete()`, `cancel()` |
| FOLLOW_UP | EVALUATING, CANCELLED | `answer_followup()`, `cancel()` |
| COMPLETE | *(none)* | Terminal state |
| CANCELLED | *(none)* | Terminal state |

## Domain Methods

### Starting Interview

```python
# ✅ Correct
interview = await interview_repo.get_by_id(interview_id)
interview.start()  # IDLE → QUESTIONING
await interview_repo.update(interview)

# ❌ Wrong
interview.status = InterviewStatus.QUESTIONING  # Never set status directly
```

### Follow-up Questions

```python
# Ask first follow-up
interview = await interview_repo.get_by_id(interview_id)
interview.ask_followup(followup_id, parent_question_id)  # EVALUATING → FOLLOW_UP
await interview_repo.update(interview)

# Answer follow-up
interview.answer_followup()  # FOLLOW_UP → EVALUATING
await interview_repo.update(interview)

# Check if more follow-ups allowed (max 3 per parent question)
if interview.can_ask_more_followups():
    # Generate another follow-up
    pass
```

### Proceeding to Next Question

```python
interview = await interview_repo.get_by_id(interview_id)

if interview.has_more_questions():
    interview.proceed_to_next_question()  # EVALUATING → QUESTIONING
    # Resets follow-up counter and parent question ID
else:
    interview.proceed_to_next_question()  # EVALUATING → COMPLETE
    # Sets completed_at timestamp

await interview_repo.update(interview)
```

## Orchestrator Pattern

The `InterviewSessionOrchestrator` is **stateless** and follows this pattern:

### 1. Load Fresh State

```python
async for session in get_async_session():
    interview_repo = self.container.interview_repository_port(session)

    # ALWAYS load from DB first
    interview = await interview_repo.get_by_id(self.interview_id)
    if not interview:
        raise ValueError(f"Interview {self.interview_id} not found")
```

### 2. Use Domain Methods

```python
    # Never check orchestrator state (doesn't exist)
    # Use domain methods for transitions

    interview.start()  # Or other domain method
    await interview_repo.update(interview)
```

### 3. Perform Coordination

```python
    # Generate TTS, send WebSocket messages, etc.
    audio_bytes = await tts.synthesize_speech(question.text)
    await self._send_message({...})
```

## Follow-up Tracking

### Fields

- `current_parent_question_id`: UUID of main question (set when first follow-up asked)
- `current_followup_count`: Number of follow-ups for current parent (0-3)

### Behavior

1. **First follow-up**: Sets parent ID, count = 1
2. **Same parent**: Increments count (2, 3)
3. **Max enforcement**: Raises error if count ≥ 3
4. **New main question**: Resets both to None/0 via `proceed_to_next_question()`
5. **Different parent**: Resets count to 1, updates parent ID

### Example Flow

```python
# Main question answered
interview.status  # EVALUATING
interview.current_parent_question_id  # None
interview.current_followup_count  # 0

# First follow-up
interview.ask_followup(fu1_id, main_q_id)
interview.status  # FOLLOW_UP
interview.current_parent_question_id  # main_q_id
interview.current_followup_count  # 1

# Answer follow-up
interview.answer_followup()
interview.status  # EVALUATING
# Counters unchanged

# Second follow-up (same parent)
interview.ask_followup(fu2_id, main_q_id)
interview.current_followup_count  # 2

# Proceed to next main question
interview.proceed_to_next_question()
interview.status  # QUESTIONING
interview.current_parent_question_id  # None (reset)
interview.current_followup_count  # 0 (reset)
```

## Error Handling

### Invalid Transitions

```python
try:
    interview.start()  # If not in IDLE
except ValueError as e:
    # e.g., "Cannot start interview with status: QUESTIONING"
    # Message includes valid transitions from current state
```

### Follow-up Limit

```python
try:
    interview.ask_followup(fu4_id, parent_id)  # 4th follow-up
except ValueError as e:
    # "Max 3 follow-ups per question. Current: 3"
```

## Testing

### Unit Tests

Test domain methods in isolation:

```python
def test_start_transitions_from_idle():
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.IDLE)

    interview.start()

    assert interview.status == InterviewStatus.QUESTIONING
    assert interview.started_at is not None
```

### Integration Tests

Test orchestrator coordination:

```python
async def test_orchestrator_starts_interview():
    # Load interview from mocked repo
    interview = await interview_repo.get_by_id(interview_id)
    assert interview.status == InterviewStatus.IDLE

    # Orchestrator calls domain method
    await orchestrator.start_session()

    # Verify messages sent (not orchestrator state)
    question_calls = [c for c in mock_manager.send_message.call_args_list
                     if c[0][1].get("type") == "question"]
    assert len(question_calls) == 1
```

## Common Pitfalls

### ❌ Checking Orchestrator State

```python
# WRONG - orchestrator has no state
if orchestrator.state == SessionState.IDLE:
    pass
```

**Fix**: Load interview and check domain status:
```python
interview = await interview_repo.get_by_id(interview_id)
if interview.status == InterviewStatus.IDLE:
    pass
```

### ❌ Setting Status Directly

```python
# WRONG - bypasses validation
interview.status = InterviewStatus.QUESTIONING
```

**Fix**: Use domain methods:
```python
interview.start()  # Validates transition
```

### ❌ Caching Interview State

```python
# WRONG - state may be stale
self.interview = interview  # In orchestrator __init__
# ...later...
if self.interview.status == InterviewStatus.IDLE:  # Stale!
```

**Fix**: Load fresh every time:
```python
interview = await interview_repo.get_by_id(self.interview_id)
if interview.status == InterviewStatus.IDLE:
    pass
```

### ❌ Forgetting Counter Reset

```python
# WRONG - manual reset
interview.proceed_to_next_question()
interview.current_followup_count = 0  # Don't do manually
```

**Fix**: Domain method handles it:
```python
interview.proceed_to_next_question()  # Resets counters automatically
```

## Migration Notes

### For Developers

If you have code using the old `SessionState`:

1. **Remove** `SessionState` imports
2. **Load** interview from repo before operations
3. **Use** domain methods instead of `_transition()`
4. **Remove** checks of `orchestrator.state`, `orchestrator.current_question_id`, etc.

### Database

Migration `a34e5ae1ab40` adds:
- `current_parent_question_id` (UUID, nullable)
- `current_followup_count` (INTEGER, default 0)

Safe for existing interviews (NULL/0 defaults).

## Quick Reference

| Task | Method | State Transition |
|------|--------|------------------|
| Start interview | `interview.start()` | IDLE → QUESTIONING |
| Add answer | `interview.add_answer(answer_id)` | QUESTIONING → EVALUATING |
| Ask follow-up | `interview.ask_followup(fu_id, parent_id)` | EVALUATING → FOLLOW_UP |
| Answer follow-up | `interview.answer_followup()` | FOLLOW_UP → EVALUATING |
| Next question | `interview.proceed_to_next_question()` | EVALUATING → QUESTIONING/COMPLETE |
| Complete | `interview.complete()` | EVALUATING → COMPLETE (auto via proceed) |
| Cancel | `interview.cancel()` | Any → CANCELLED |
| Check state | `interview.status` | Read-only |
| Check follow-ups | `interview.can_ask_more_followups()` | Returns bool |

---

**Related Files**:
- `src/domain/models/interview.py` - Domain model implementation
- `tests/unit/domain/test_interview_state_transitions.py` - State tests
- `src/adapters/api/websocket/session_orchestrator.py` - Stateless orchestrator
- `plans/251112-2117-domain-driven-state-management/IMPLEMENTATION_SUMMARY.md` - Full migration details
