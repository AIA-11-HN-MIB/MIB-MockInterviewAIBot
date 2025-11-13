# Phase 3: Orchestrator Refactoring

## Context Links
- **Parent Plan**: [plan.md](./plan.md)
- **Dependencies**: Phase 1 (Domain Model), Phase 2 (Database Migration)
- **Related Docs**:
  - Research: [researcher-02-orchestrator-refactoring.md](./research/researcher-02-orchestrator-refactoring.md)
  - Scout: [scout-01-affected-files.md](./scout/scout-01-affected-files.md)

## Overview

**Date**: 2025-11-12
**Description**: Convert stateful WebSocket orchestrator to stateless coordinator
**Priority**: CRITICAL (core refactoring)
**Effort Estimate**: 3-4 hours
**Implementation Status**: ⏳ Not Started
**Review Status**: ⏳ Pending

## Key Insights

1. **Stateless Pattern**: Orchestrator loads `interview` entity at start of each operation
2. **Domain Delegates**: All state transitions through domain methods
3. **No Duplicate Data**: Remove `current_question_id`, `parent_question_id`, `follow_up_count`
4. **Simplified Logic**: Orchestrator becomes thin coordination layer

## Requirements

### Functional Requirements
- ✅ Remove `SessionState` enum entirely
- ✅ Remove all in-memory state fields from orchestrator
- ✅ Load `interview` entity from DB before operations
- ✅ Use domain methods for all state transitions
- ✅ Pass `interview` entity through call chain
- ✅ Get question IDs from domain instead of tracking locally
- ✅ Maintain same WebSocket message protocol

### Non-Functional Requirements
- ✅ No behavior changes from client perspective
- ✅ All existing WebSocket tests pass (after updates)
- ✅ Clean separation: orchestrator coordinates, domain decides
- ✅ Clear error messages propagated from domain

## Architecture

### Before: Stateful Orchestrator
```python
class InterviewSessionOrchestrator:
    def __init__(self, interview_id, websocket, container):
        self.interview_id = interview_id
        self.websocket = websocket
        self.container = container
        self.state = SessionState.IDLE              # ❌ Remove
        self.current_question_id = None             # ❌ Remove
        self.parent_question_id = None              # ❌ Remove
        self.follow_up_count = 0                    # ❌ Remove
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()

    def _transition(self, new_state: SessionState):  # ❌ Remove
        # ... validation logic ...
```

### After: Stateless Coordinator
```python
class InterviewSessionOrchestrator:
    def __init__(self, interview_id, websocket, container):
        self.interview_id = interview_id
        self.websocket = websocket
        self.container = container
        # ✅ No state tracking - everything from domain
```

### Operation Pattern
```python
async def handle_answer(self, answer_text: str) -> None:
    """Handle answer based on domain state."""
    # Load fresh state
    async for session in get_async_session():
        interview_repo = self.container.interview_repository_port(session)
        interview = await interview_repo.get_by_id(self.interview_id)

        # Route based on domain state
        if interview.status == InterviewStatus.QUESTIONING:
            await self._handle_main_question(answer_text, interview, session)
        elif interview.status == InterviewStatus.FOLLOW_UP:
            await self._handle_followup(answer_text, interview, session)
        else:
            raise ValueError(f"Cannot handle answer in {interview.status}")
        break
```

## Related Code Files

### To Modify
- `src/adapters/api/websocket/session_orchestrator.py` (major refactoring)

### Supporting Files
- `src/adapters/api/websocket/connection_manager.py` (verify compatibility)
- `src/adapters/api/websocket/chat_handler.py` (if it instantiates orchestrator)

## Implementation Steps

### Step 1: Remove SessionState Enum
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 31-38

Delete entire `SessionState` class.

### Step 2: Clean __init__ Method
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 53-79

Remove:
- `self.state = SessionState.IDLE`
- `self.current_question_id: UUID | None = None`
- `self.parent_question_id: UUID | None = None`
- `self.follow_up_count = 0`

Keep:
- `self.interview_id`
- `self.websocket`
- `self.container`
- Optionally keep `created_at`, `last_activity` for connection tracking

### Step 3: Remove _transition() Method
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 81-128

Delete entire method. State transitions now handled by domain.

### Step 4: Refactor start_session()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 130-195

**Changes**:
```python
async def start_session(self) -> None:
    """Start interview session by sending first question."""
    async for session in get_async_session():
        interview_repo = self.container.interview_repository_port(session)
        question_repo = self.container.question_repository_port(session)
        tts = self.container.text_to_speech_port()

        # Load interview
        interview = await interview_repo.get_by_id(self.interview_id)
        if not interview:
            raise ValueError(f"Interview {self.interview_id} not found")

        # Validate state
        if interview.status != InterviewStatus.IDLE:
            raise ValueError(f"Interview already started: {interview.status}")

        # Get first question
        use_case = GetNextQuestionUseCase(interview_repo, question_repo)
        question = await use_case.execute(self.interview_id)
        if not question:
            raise ValueError("No questions available")

        # Domain transition
        interview.start()  # Sets QUESTIONING status
        await interview_repo.update(interview)

        # Generate TTS and send
        audio_bytes = await tts.synthesize_speech(question.text)
        audio_data = base64.b64encode(audio_bytes).decode("utf-8")

        await self._send_message({
            "type": "question",
            "question_id": str(question.id),
            "text": question.text,
            "index": interview.current_question_index,
            "total": len(interview.question_ids),
            "audio_data": audio_data,
        })
        break
```

### Step 5: Refactor handle_answer()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 197-216

**Changes**:
```python
async def handle_answer(self, answer_text: str) -> None:
    """Handle answer based on domain state."""
    async for session in get_async_session():
        interview_repo = self.container.interview_repository_port(session)
        interview = await interview_repo.get_by_id(self.interview_id)

        if interview.status == InterviewStatus.QUESTIONING:
            await self._handle_main_question_answer(answer_text, interview, session)
        elif interview.status == InterviewStatus.FOLLOW_UP:
            await self._handle_followup_answer(answer_text, interview, session)
        else:
            raise ValueError(f"Cannot handle answer in {interview.status}")
        break
```

### Step 6: Refactor _handle_main_question_answer()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 218-289

**Key Changes**:
- Add `interview: Interview` and `session: AsyncSession` parameters
- Remove `self._transition()` calls
- Use `interview.begin_evaluation()` → `interview_repo.update(interview)`
- Get current question from `interview.get_current_question_id()`
- Reload interview after use case execution

**Pattern**:
```python
async def _handle_main_question_answer(
    self,
    answer_text: str,
    interview: Interview,
    session: AsyncSession
) -> None:
    """Process main question answer."""
    # Transition to evaluating
    interview.begin_evaluation()  # Or interview.transition_to(EVALUATING)
    await interview_repo.update(interview)

    # Get current question ID from domain
    current_question_id = interview.get_current_question_id()

    # Process answer
    answer, has_more = await use_case.execute(
        interview_id=self.interview_id,
        question_id=current_question_id,
        answer_text=answer_text
    )

    # Reload interview (use case may have modified it)
    interview = await interview_repo.get_by_id(self.interview_id)

    # Make decision
    if needs_followup:
        await self._generate_and_send_followup(
            answer, decision, interview, session
        )
    elif has_more:
        await self._send_next_main_question(interview, session)
    else:
        await self._complete_interview(interview, session)
```

### Step 7: Refactor _handle_followup_answer()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 291-362

Similar pattern to Step 6:
- Add `interview` and `session` parameters
- Use `interview.answer_followup()` to transition back to EVALUATING
- Get current question from domain
- Reload after use case

### Step 8: Refactor _generate_and_send_followup()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 364-432

**Key Changes**:
- Add `interview: Interview` parameter
- Remove `self.follow_up_count` tracking
- Use `interview.ask_followup(followup_id, parent_question_id)`
- Update `interview_repo.update(interview)` after domain method
- Get parent question from `interview.current_parent_question_id`

```python
async def _generate_and_send_followup(
    self,
    answer: Answer,
    decision: dict,
    interview: Interview,
    session: AsyncSession
) -> None:
    """Generate and send follow-up question."""
    # Check if more follow-ups allowed
    if not interview.can_ask_more_followups():
        logger.warning("Max follow-ups reached, skipping")
        return

    # Get parent question
    parent_question_id = interview.current_parent_question_id or interview.get_current_question_id()

    # Generate follow-up
    follow_up_text = await self.container.llm_port().generate_followup_question(...)

    # Create entity
    follow_up = FollowUpQuestion(
        parent_question_id=parent_question_id,
        interview_id=self.interview_id,
        text=follow_up_text,
        ...
    )
    await follow_up_repo.save(follow_up)

    # Domain transition
    interview.ask_followup(follow_up.id, parent_question_id)
    await interview_repo.update(interview)

    # Send message
    await self._send_message({
        "type": "follow_up_question",
        "question_id": str(follow_up.id),
        "text": follow_up.text,
        ...
    })
```

### Step 9: Refactor _send_next_main_question()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 434-487

**Key Changes**:
- Add `interview: Interview` parameter
- Use `interview.proceed_to_next_question()` (resets counters + transitions)
- Get question from `interview.get_current_question_id()` after transition

```python
async def _send_next_main_question(
    self,
    interview: Interview,
    session: AsyncSession
) -> None:
    """Send next main question."""
    # Domain handles transition + counter reset
    interview.proceed_to_next_question()
    await interview_repo.update(interview)

    # Get next question
    question_id = interview.get_current_question_id()
    question = await question_repo.get_by_id(question_id)

    # Send message
    await self._send_message({
        "type": "question",
        "question_id": str(question.id),
        "text": question.text,
        "index": interview.current_question_index,
        "total": len(interview.question_ids),
        ...
    })
```

### Step 10: Refactor _complete_interview()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 489-562

**Key Changes**:
- Add `interview: Interview` parameter
- Use `CompleteInterviewUseCase` (already uses domain methods)
- Remove manual state transition

### Step 11: Update/Remove get_state()
**File**: `src/adapters/api/websocket/session_orchestrator.py`
**Lines**: 608-622

**Options**:
- Remove entirely (no longer needed)
- OR simplify to return only `interview_id` and connection metadata

### Step 12: Clean Up Imports
Remove unused imports:
- `SessionState` enum
- Any other orphaned imports

## Todo List

- [ ] Delete `SessionState` enum
- [ ] Remove `self.state`, `self.current_question_id`, `self.parent_question_id`, `self.follow_up_count` from `__init__`
- [ ] Delete `_transition()` method
- [ ] Refactor `start_session()` to use domain methods
- [ ] Refactor `handle_answer()` to load domain state
- [ ] Refactor `_handle_main_question_answer()` with `interview` parameter
- [ ] Refactor `_handle_followup_answer()` with `interview` parameter
- [ ] Refactor `_generate_and_send_followup()` to use domain counter check
- [ ] Refactor `_send_next_main_question()` to use `proceed_to_next_question()`
- [ ] Refactor `_complete_interview()` to use domain methods
- [ ] Update or remove `get_state()` method
- [ ] Clean up unused imports

## Success Criteria

✅ **Code Quality**
- No `SessionState` references remain
- No in-memory state fields in orchestrator
- All operations load `interview` from DB
- Clean separation: orchestrator coordinates, domain decides

✅ **Functional Correctness**
- Start session works (sends first question)
- Answer handling routes correctly based on `interview.status`
- Follow-up generation uses domain counter
- Next question navigation resets counters
- Interview completion works

✅ **Integration**
- WebSocket messages unchanged (client compatibility)
- Error messages clear and propagate from domain
- No regressions in interview flow

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Logic errors in refactoring | HIGH | MEDIUM | Comprehensive testing before/after |
| Missing domain method calls | MEDIUM | MEDIUM | Code review checklist |
| Performance degradation | LOW | LOW | Profile shows negligible overhead |
| Breaking WebSocket protocol | HIGH | LOW | Integration tests verify messages |

## Security Considerations

- **State Validation**: Domain enforces valid transitions (orchestrator can't bypass)
- **Input Validation**: Domain validates all inputs (max follow-ups, etc.)
- **Error Exposure**: Don't leak internal state details in error messages
- **Authorization**: Still handled at API layer (unchanged)

## Next Steps

After completion:
1. **Code Review**: Verify all `SessionState` removed
2. **Testing**: Run Phase 4 test updates
3. **Integration Test**: Full interview flow end-to-end
4. **Performance**: Profile to confirm <2 queries/min
5. **Proceed**: Move to Phase 4 (Test Suite Updates)
