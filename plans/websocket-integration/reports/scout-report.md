# Scout Report: Interview Planning & WebSocket Integration

**Date**: 2025-11-15  
**Status**: Complete

## Key Findings

### 1. Plan Interview Use Case
- **File**: /h/AI-course/EliosAIService/src/application/use_cases/plan_interview.py
- **Class**: PlanInterviewUseCase
- **Execute Method**: async def execute(cv_analysis_id: UUID, candidate_id: UUID) -> Interview
- **Process**: Loads CV → Calculates question count (2-5 based on skills) → Generates questions with ideal answers → Updates interview to IDLE status
- **Key methods**: _calculate_question_count(), _generate_question_with_ideal_answer(), _find_exemplar_questions()

### 2. REST API Endpoints
- **File**: /h/AI-course/EliosAIService/src/adapters/api/rest/interview_routes.py
- **Planning**: POST /interviews/plan (202 ACCEPTED) - triggers async planning
- **Get Status**: GET /{interview_id}/plan (200 OK) - returns PlanningStatusResponse
- **Get Interview**: GET /{interview_id} (200 OK) - returns InterviewResponse with ws_url field
- **Start Interview**: PUT /{interview_id}/start - transitions from IDLE to QUESTIONING
- **Critical**: ws_url generated via InterviewResponse.from_domain() using settings.ws_base_url

### 3. WebSocket Infrastructure
- **Handler**: /h/AI-course/EliosAIService/src/adapters/api/websocket/interview_handler.py
  - handle_interview_websocket(websocket, interview_id)
  - Routes message types: text_answer, audio_chunk, get_next_question
  
- **Connection Manager**: /h/AI-course/EliosAIService/src/adapters/api/websocket/connection_manager.py
  - Maintains dict[UUID, WebSocket] for active connections
  - Global instance: manager = ConnectionManager()
  
- **Session Orchestrator**: /h/AI-course/EliosAIService/src/adapters/api/websocket/session_orchestrator.py
  - Stateless orchestrator (loads fresh state from DB before each operation)
  - Key methods: start_session(), handle_answer(), _handle_main_question_answer(), _handle_followup_answer()
  - Manages question flow, evaluations, follow-ups, and completion

### 4. WebSocket Configuration
- **File**: /h/AI-course/EliosAIService/src/infrastructure/config/settings.py
- **Settings**: 
  - ws_host: str = "localhost"
  - ws_port: int = 8000
  - ws_base_url: str = "ws://localhost:8000"
- **Default URL**: ws://localhost:8000 (development)
- **Production**: Must update ws_base_url to wss://api.example.com

### 5. FastAPI Application Setup
- **File**: /h/AI-course/EliosAIService/src/main.py
- **WebSocket Route**: @app.websocket("/ws/interviews/{interview_id}")
- **Route Handler**: Delegates to handle_interview_websocket()
- **REST Router**: Interview router included at /api prefix

### 6. Interview DTO - WebSocket URL Injection
- **File**: /h/AI-course/EliosAIService/src/application/dto/interview_dto.py
- **InterviewResponse**: Contains ws_url field
- **Generation**: from_domain(interview, base_url) → ws_url = f"{base_url}/ws/interviews/{interview.id}"
- **PlanningStatusResponse**: No WebSocket URL (for async planning phase)

## URL Generation Flow

```
GET /api/interviews/{interview_id}
  → interview_routes.get_interview()
  → settings.ws_base_url = "ws://localhost:8000"
  → InterviewResponse.from_domain(interview, base_url)
  → ws_url = "ws://localhost:8000/ws/interviews/{id}"
  → Client connects to WebSocket at URL
  → FastAPI /ws/interviews/{interview_id} endpoint
  → ConnectionManager + InterviewSessionOrchestrator
```

## Message Protocol

**Client to Server**:
- {"type": "text_answer", "question_id": UUID, "answer_text": str}
- {"type": "audio_chunk", ...}

**Server to Client**:
- {"type": "question", "question_id": UUID, "text": str, "audio_data": str, ...}
- {"type": "evaluation", "score": float, "feedback": str, ...}
- {"type": "follow_up_question", "text": str, "order_in_sequence": int, ...}
- {"type": "interview_complete", "overall_score": float, ...}
- {"type": "error", "code": str, "message": str}

## Files Summary

| Component | Path | Lines |
|-----------|------|-------|
| Plan Interview Use Case | src/application/use_cases/plan_interview.py | 20-384 |
| REST Routes | src/adapters/api/rest/interview_routes.py | 227-401 |
| WebSocket Handler | src/adapters/api/websocket/interview_handler.py | 15-131 |
| Session Orchestrator | src/adapters/api/websocket/session_orchestrator.py | 37-669 |
| Connection Manager | src/adapters/api/websocket/connection_manager.py | 11-61 |
| Settings Config | src/infrastructure/config/settings.py | 131-134 |
| Interview DTOs | src/application/dto/interview_dto.py | 11-96 |
| FastAPI App | src/main.py | 87-93 |

## Integration Flow

1. Client uploads CV → AnalyzeCVUseCase → CVAnalysis saved
2. Client calls POST /api/interviews/plan → PlanInterviewUseCase → Interview created with questions (status=IDLE)
3. Client calls GET /api/interviews/{id} → Receives ws_url from settings
4. Client connects to WebSocket at ws_url → interview_handler → ConnectionManager + Orchestrator
5. Orchestrator.start_session() → sends first question with TTS audio
6. Client sends answer → handle_answer() → evaluates → decides on follow-up or next question
7. Repeat until all questions answered → complete_interview() → sends summary

## Current Status
- Planning phase: Fully implemented
- WebSocket connection: Fully implemented
- Message handling: Partially implemented (text_answer complete, audio_chunk is mock)
- Session orchestration: Fully implemented
- Configuration: Flexible with environment-based ws_base_url

## Limitations
- Vector search for exemplars commented out (lines 207-220 in plan_interview.py)
- Audio/STT integration incomplete
- No WebSocket reconnection/recovery
- No adaptive question count adjustment during interview
