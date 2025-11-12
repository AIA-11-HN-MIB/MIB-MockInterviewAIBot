# Phase 5: Session Orchestration

**Duration**: 3 days
**Priority**: High
**Dependencies**: Phase 4 (Follow-up Engine)

## Context

WebSocket handler currently handles messages reactively. Need state machine pattern to manage interview lifecycle (IDLE → QUESTIONING → EVALUATING → FOLLOW_UP → COMPLETE).

**Context Links**:
- `src/adapters/api/websocket/interview_handler.py` - Current handler (435 lines)

## Requirements

### State Machine

**States**:
- IDLE - Waiting for session start
- QUESTIONING - Sent question, waiting for answer
- EVALUATING - Processing answer
- FOLLOW_UP - In follow-up loop
- COMPLETE - Interview finished

**Transitions**:
- IDLE → QUESTIONING (start interview)
- QUESTIONING → EVALUATING (answer received)
- EVALUATING → FOLLOW_UP (follow-up needed)
- EVALUATING → QUESTIONING (next main question)
- FOLLOW_UP → EVALUATING (follow-up answered)
- QUESTIONING → COMPLETE (no more questions)

## Architecture

### InterviewSessionOrchestrator

```python
# src/adapters/api/websocket/session_orchestrator.py
from enum import Enum

class SessionState(str, Enum):
    IDLE = "idle"
    QUESTIONING = "questioning"
    EVALUATING = "evaluating"
    FOLLOW_UP = "follow_up"
    COMPLETE = "complete"

class InterviewSessionOrchestrator:
    """Orchestrate interview session lifecycle."""

    def __init__(
        self,
        interview_id: UUID,
        websocket: WebSocket,
        container: Container,
    ):
        self.interview_id = interview_id
        self.websocket = websocket
        self.container = container
        self.state = SessionState.IDLE
        self.current_question_id: UUID | None = None
        self.parent_question_id: UUID | None = None
        self.follow_up_count = 0

    async def start_session(self):
        """Start interview session."""
        self._transition(SessionState.QUESTIONING)
        await self._send_first_question()

    async def handle_answer(self, answer_text: str):
        """Handle answer based on current state."""
        if self.state == SessionState.QUESTIONING:
            self._transition(SessionState.EVALUATING)
            await self._evaluate_and_decide()

        elif self.state == SessionState.FOLLOW_UP:
            self._transition(SessionState.EVALUATING)
            await self._evaluate_followup_and_decide()

    def _transition(self, new_state: SessionState):
        """Transition to new state with validation."""
        valid_transitions = {
            SessionState.IDLE: [SessionState.QUESTIONING],
            SessionState.QUESTIONING: [SessionState.EVALUATING],
            SessionState.EVALUATING: [
                SessionState.FOLLOW_UP,
                SessionState.QUESTIONING,
                SessionState.COMPLETE
            ],
            SessionState.FOLLOW_UP: [SessionState.EVALUATING],
        }

        if new_state not in valid_transitions.get(self.state, []):
            raise ValueError(
                f"Invalid transition: {self.state} → {new_state}"
            )

        logger.info(f"State transition: {self.state} → {new_state}")
        self.state = new_state
```

## Implementation Steps

### Day 1: State Machine

**Step 1**: Create InterviewSessionOrchestrator
- Define SessionState enum
- Implement state transition logic
- Add state validation

**Step 2**: Refactor WebSocket handler
- Replace reactive handlers with orchestrator
- Delegate to orchestrator methods
- Track session state

### Day 2: Progress Tracking

**Step 1**: Add session state persistence
- Track current question index
- Track follow-up count per question
- Store in memory (future: Redis)

**Step 2**: Implement error recovery
- Timeout handling per state
- Retry logic for failed operations
- Graceful degradation

### Day 3: Testing

**Step 1**: Unit tests
- Test state transitions
- Test error recovery
- Test progress tracking

**Step 2**: Integration tests
- Test full interview flow
- Test concurrent sessions
- Validate state consistency

## Todo List

**Day 1**:
- [ ] Create session_orchestrator.py
- [ ] Define SessionState enum
- [ ] Implement state transition logic
- [ ] Refactor interview_handler to use orchestrator

**Day 2**:
- [ ] Add session state persistence
- [ ] Implement progress tracking
- [ ] Add error recovery mechanisms
- [ ] Add timeout handling per state

**Day 3**:
- [ ] Write unit tests for orchestrator
- [ ] Write integration tests for full flow
- [ ] Test concurrent sessions
- [ ] Performance test state transitions

## Success Criteria

- ✅ State machine correctly manages lifecycle
- ✅ Invalid transitions rejected with errors
- ✅ Session state persisted and recovered
- ✅ Error recovery works without breaking session
- ✅ Unit test coverage >=80%
