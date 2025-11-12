# Research: Orchestrator Refactoring Patterns

## Overview
Patterns for converting stateful WebSocket orchestrators to stateless coordinators.

## Removing In-Memory State

### Before: Stateful Orchestrator
```python
class InterviewSessionOrchestrator:
    def __init__(self, interview_id, websocket, container):
        self.interview_id = interview_id
        self.websocket = websocket
        self.container = container
        self.state = SessionState.IDLE  # ❌ In-memory state
        self.current_question_id = None  # ❌ Duplicate of domain
        self.parent_question_id = None   # ❌ Duplicate of domain
        self.follow_up_count = 0         # ❌ Should be in domain
```

### After: Stateless Coordinator
```python
class InterviewSessionOrchestrator:
    def __init__(self, interview_id, websocket, container):
        self.interview_id = interview_id
        self.websocket = websocket
        self.container = container
        # ✅ No state - everything loaded from domain
```

## Fetching Domain State Pattern

### Pattern 1: Load-Process-Save
```python
async def handle_answer(self, answer_text: str) -> None:
    """Handle answer based on current domain state."""
    # Load current state
    async for session in get_async_session():
        interview_repo = self.container.interview_repository_port(session)
        interview = await interview_repo.get_by_id(self.interview_id)

        # Validate and route based on domain state
        if interview.status == InterviewStatus.QUESTIONING:
            await self._handle_main_question_answer(answer_text, interview, session)
        elif interview.status == InterviewStatus.FOLLOW_UP:
            await self._handle_followup_answer(answer_text, interview, session)
        else:
            raise ValueError(f"Cannot handle answer in state {interview.status}")
        break
```

### Pattern 2: Pass Domain Entity Through Call Chain
```python
async def _handle_main_question_answer(
    self,
    answer_text: str,
    interview: Interview,  # ✅ Passed from caller
    session: AsyncSession
) -> None:
    """Process with domain entity."""
    # Transition in domain
    interview.begin_evaluation()
    await interview_repo.update(interview)

    # Process answer...
    answer, has_more = await use_case.execute(...)

    # Reload to ensure fresh state
    interview = await interview_repo.get_by_id(self.interview_id)

    # Make decision based on fresh state
    if needs_followup:
        interview.ask_followup(followup_id)
        await interview_repo.update(interview)
```

## Performance Analysis

### Query Frequency
- **Interview duration**: 20-30 minutes
- **Questions**: 7-10 main + up to 3 follow-ups each = ~25 total questions
- **State transitions per question**: 2-3 (QUESTIONING → EVALUATING → FOLLOW_UP/QUESTIONING)
- **Total queries**: ~50-75 over 30 minutes = 1.6-2.5 queries/minute
- **Conclusion**: Negligible overhead

### Query Optimization
```python
# Single query per handler invocation
async def handle_answer(self, answer_text: str) -> None:
    async for session in get_async_session():
        interview_repo = self.container.interview_repository_port(session)

        # One query at start
        interview = await interview_repo.get_by_id(self.interview_id)

        # Use same entity throughout handler
        await self._process_with_entity(interview, session)
        break
```

## Race Condition Handling

### Not Required (Per Requirements)
- **No reconnections**: Client cannot resume after disconnect
- **No concurrent access**: Single client per interview
- **Conclusion**: No optimistic locking needed

### Defensive Pattern (Future-Proof)
```python
async def update_with_retry(self, interview: Interview) -> None:
    """Update with version check for future concurrency."""
    try:
        await interview_repo.update(interview)
    except StaleDataError:
        # Reload and retry (not needed now, but safe)
        interview = await interview_repo.get_by_id(interview.id)
        raise ValueError("State changed during operation")
```

## Testing Strategies

### Unit Tests for Stateless Orchestrator
```python
async def test_handle_answer_questioning_state():
    """Test answer handling when in QUESTIONING state."""
    # Arrange - mock domain entity
    interview = Interview(
        id=uuid4(),
        candidate_id=uuid4(),
        status=InterviewStatus.QUESTIONING
    )

    repo_mock = Mock(spec=InterviewRepositoryPort)
    repo_mock.get_by_id.return_value = interview

    orchestrator = InterviewSessionOrchestrator(
        interview_id=interview.id,
        websocket=Mock(),
        container=Mock()
    )

    # Act
    await orchestrator.handle_answer("My answer")

    # Assert - verify domain transition called
    assert interview.status == InterviewStatus.EVALUATING
    repo_mock.update.assert_called_once_with(interview)
```

### Integration Tests
```python
async def test_full_interview_flow():
    """Test complete interview with real DB."""
    # Create interview in IDLE state
    interview = await create_interview(candidate_id, cv_analysis_id)

    # Start session
    orchestrator = InterviewSessionOrchestrator(interview.id, ws, container)
    await orchestrator.start_session()

    # Verify state persisted
    reloaded = await interview_repo.get_by_id(interview.id)
    assert reloaded.status == InterviewStatus.QUESTIONING

    # Answer question
    await orchestrator.handle_answer("Test answer")

    # Verify state persisted again
    reloaded = await interview_repo.get_by_id(interview.id)
    assert reloaded.status == InterviewStatus.EVALUATING
```

## Migration Strategy

### Phase 1: Add Domain Fetching
- Keep existing state
- Add parallel domain loading
- Compare states in assertions

### Phase 2: Replace State Checks
- Replace `self.state` checks with `interview.status`
- Keep updating both states

### Phase 3: Remove Orchestrator State
- Delete `self.state`, `SessionState` enum
- Remove all state transition logic from orchestrator

### Phase 4: Cleanup
- Remove unused imports
- Update documentation
- Simplify tests

## Key Takeaways

1. **Stateless = Simpler**: No state management complexity in orchestrator
2. **Domain Owns Logic**: All state rules in one place
3. **Negligible Overhead**: DB queries trivial for interview workload
4. **Easier Testing**: Mock only repositories, not state machines
5. **Consistent View**: REST and WebSocket see same state
