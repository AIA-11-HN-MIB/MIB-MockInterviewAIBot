# Interview API & WebSocket Implementation Plan

**Date**: 2025-11-02
**Version**: 0.1.0
**Feature**: Start Interview & Do Interview (REST + WebSocket)
**Scope**: API adapter layer + persistence layer, mock other adapters

---

## Overview

Implement REST API endpoint for creating interview sessions and WebSocket handler for real-time interview communication. Focus on `api` and `persistence` adapters while mocking LLM, STT, TTS, and vector search adapters.

### Sequence Flow
1. `POST /api/interviews` - Create session, return `sessionId` + `wsUrl`
2. `WebSocket /ws/interviews/{interview_id}` - Real-time bidirectional communication
   - Client → Server: audio frames OR text chat
   - Server → Client: transcription + synthesized voice + evaluation

---

## Architecture Context

**Pattern**: Clean Architecture / Hexagonal Architecture
**Layers**: Domain → Application → Adapters → Infrastructure
**Current Status**: Domain + Application + Persistence complete, API incomplete

**Existing Components**:
- Domain models: `Interview`, `Question`, `Answer`, `Candidate`, `CVAnalysis`
- Ports: All 11 ports defined
- Repositories: PostgreSQL implementations complete
- Use cases: `StartInterviewUseCase` exists, need `ProcessAnswerUseCase`, `GetNextQuestionUseCase`

---

## Files to Create

### 1. Application Layer - DTOs
```
src/application/dto/
├── __init__.py
├── interview_dto.py         # Request/Response DTOs for interviews
├── answer_dto.py            # Request/Response DTOs for answers
└── websocket_dto.py         # WebSocket message DTOs
```

### 2. Application Layer - Use Cases
```
src/application/use_cases/
├── get_next_question.py     # Get next question in interview
├── process_answer.py        # Process and evaluate answer
└── complete_interview.py    # Complete interview workflow
```

### 3. Adapters - API Layer
```
src/adapters/api/
├── rest/
│   ├── interview_routes.py  # REST endpoints for interviews
│   └── dto_mappers.py        # Map domain ↔ API DTOs
└── websocket/
    ├── __init__.py
    ├── connection_manager.py # WebSocket connection management
    ├── interview_handler.py  # WebSocket interview handler
    └── message_protocol.py   # Message types and protocol
```

### 4. Adapters - Mock Implementations
```
src/adapters/mock/
├── __init__.py
├── mock_llm_adapter.py      # Mock LLM for development
├── mock_stt_adapter.py      # Mock STT for development
├── mock_tts_adapter.py      # Mock TTS for development
└── mock_vector_adapter.py   # Mock vector search (if needed)
```

---

## Files to Modify

### 1. Main Application
- `src/main.py` - Register new routers (interview_routes, websocket)

### 2. Dependency Injection
- `src/infrastructure/dependency_injection/container.py` - Wire mock adapters

### 3. Database Models (if needed)
- `src/adapters/persistence/models.py` - Add WebSocket session tracking (optional)

---

## Implementation Details

### Phase 1: DTOs (Data Transfer Objects)

#### interview_dto.py
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# Request DTOs
class CreateInterviewRequest(BaseModel):
    candidate_id: UUID
    cv_analysis_id: UUID
    num_questions: int = Field(default=10, ge=1, le=20)

class StartInterviewRequest(BaseModel):
    pass  # No body needed

# Response DTOs
class InterviewResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    status: str
    cv_analysis_id: Optional[UUID]
    question_count: int
    current_question_index: int
    progress_percentage: float
    ws_url: str  # WebSocket URL
    created_at: datetime
    started_at: Optional[datetime]

    @staticmethod
    def from_domain(interview: Interview, base_url: str) -> "InterviewResponse":
        return InterviewResponse(
            id=interview.id,
            candidate_id=interview.candidate_id,
            status=interview.status.value,
            cv_analysis_id=interview.cv_analysis_id,
            question_count=len(interview.question_ids),
            current_question_index=interview.current_question_index,
            progress_percentage=interview.get_progress_percentage(),
            ws_url=f"{base_url}/ws/interviews/{interview.id}",
            created_at=interview.created_at,
            started_at=interview.started_at,
        )

class QuestionResponse(BaseModel):
    id: UUID
    text: str
    question_type: str
    difficulty: str
    index: int
    total: int
```

#### answer_dto.py
```python
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    answer_text: str
    audio_file_path: Optional[str] = None

class AnswerEvaluationResponse(BaseModel):
    answer_id: UUID
    question_id: UUID
    score: float
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    next_question_available: bool
```

#### websocket_dto.py
```python
from pydantic import BaseModel
from typing import Literal, Optional, Any
from uuid import UUID

# Base message
class WebSocketMessage(BaseModel):
    type: str
    payload: dict[str, Any]

# Client → Server messages
class TextAnswerMessage(BaseModel):
    type: Literal["text_answer"]
    question_id: UUID
    answer_text: str

class AudioChunkMessage(BaseModel):
    type: Literal["audio_chunk"]
    chunk_data: str  # base64 encoded
    is_final: bool

class GetNextQuestionMessage(BaseModel):
    type: Literal["get_next_question"]

# Server → Client messages
class QuestionMessage(BaseModel):
    type: Literal["question"]
    question_id: UUID
    text: str
    question_type: str
    difficulty: str
    index: int
    total: int
    audio_data: Optional[str] = None  # base64 encoded TTS

class TranscriptionMessage(BaseModel):
    type: Literal["transcription"]
    text: str
    is_final: bool

class EvaluationMessage(BaseModel):
    type: Literal["evaluation"]
    answer_id: UUID
    score: float
    feedback: str
    strengths: List[str]
    weaknesses: List[str]

class InterviewCompleteMessage(BaseModel):
    type: Literal["interview_complete"]
    interview_id: UUID
    overall_score: float
    total_questions: int
    feedback_url: str

class ErrorMessage(BaseModel):
    type: Literal["error"]
    code: str
    message: str
```

---

### Phase 2: Use Cases

#### get_next_question.py
```python
from uuid import UUID
from ...domain.models.interview import Interview
from ...domain.models.question import Question
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort

class GetNextQuestionUseCase:
    """Get next question in interview sequence."""

    def __init__(
        self,
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
    ):
        self.interview_repo = interview_repository
        self.question_repo = question_repository

    async def execute(self, interview_id: UUID) -> Optional[Question]:
        """Get next unanswered question.

        Returns:
            Next question or None if interview complete
        """
        # Get interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        # Check if more questions available
        if not interview.has_more_questions():
            return None

        # Get current question
        question_id = interview.get_current_question_id()
        if not question_id:
            return None

        question = await self.question_repo.get_by_id(question_id)
        return question
```

#### process_answer.py
```python
from uuid import UUID
from datetime import datetime
from ...domain.models.answer import Answer, AnswerEvaluation
from ...domain.models.interview import Interview
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort
from ...domain.ports.llm_port import LLMPort

class ProcessAnswerUseCase:
    """Process and evaluate candidate answer."""

    def __init__(
        self,
        answer_repository: AnswerRepositoryPort,
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
        llm: LLMPort,
    ):
        self.answer_repo = answer_repository
        self.interview_repo = interview_repository
        self.question_repo = question_repository
        self.llm = llm

    async def execute(
        self,
        interview_id: UUID,
        question_id: UUID,
        answer_text: str,
        audio_file_path: Optional[str] = None,
    ) -> tuple[Answer, bool]:
        """Process answer and return evaluation + has_more_questions.

        Returns:
            (Answer with evaluation, has_more_questions)
        """
        # Validate interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.IN_PROGRESS:
            raise ValueError(f"Interview not in progress: {interview.status}")

        # Validate question
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Create answer
        answer = Answer(
            interview_id=interview_id,
            question_id=question_id,
            candidate_id=interview.candidate_id,
            answer_text=answer_text,
            answer_mode="voice" if audio_file_path else "text",
            audio_file_path=audio_file_path,
            created_at=datetime.utcnow(),
        )

        # Evaluate answer using LLM
        evaluation = await self.llm.evaluate_answer(
            question=question,
            answer_text=answer_text,
            context={
                "interview_id": str(interview_id),
                "candidate_id": str(interview.candidate_id),
            },
        )

        # Set evaluation
        answer.evaluate(
            score=evaluation.score,
            feedback=evaluation.feedback,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            improvement_suggestions=evaluation.improvement_suggestions,
        )

        # Save answer
        saved_answer = await self.answer_repo.save(answer)

        # Update interview
        interview.add_answer(saved_answer.id)
        await self.interview_repo.update(interview)

        # Check if more questions
        has_more = interview.has_more_questions()

        return saved_answer, has_more
```

#### complete_interview.py
```python
from uuid import UUID
from ...domain.models.interview import Interview, InterviewStatus
from ...domain.ports.interview_repository_port import InterviewRepositoryPort

class CompleteInterviewUseCase:
    """Complete interview and mark as finished."""

    def __init__(self, interview_repository: InterviewRepositoryPort):
        self.interview_repo = interview_repository

    async def execute(self, interview_id: UUID) -> Interview:
        """Mark interview as completed."""
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete interview with status: {interview.status}")

        interview.complete()
        return await self.interview_repo.update(interview)
```

---

### Phase 3: REST API Endpoints

#### interview_routes.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from ....application.dto.interview_dto import (
    CreateInterviewRequest,
    InterviewResponse,
    QuestionResponse,
)
from ....application.use_cases.start_interview import StartInterviewUseCase
from ....application.use_cases.get_next_question import GetNextQuestionUseCase
from ....infrastructure.dependency_injection.container import get_container
from ....infrastructure.database.session import get_async_session
from ....domain.models.interview import InterviewStatus

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new interview session"
)
async def create_interview(
    request: CreateInterviewRequest,
    session = Depends(get_async_session),
    container = Depends(get_container),
):
    """Create interview session and prepare questions.

    Returns:
        Interview details with WebSocket URL for real-time communication
    """
    try:
        # Get CV analysis
        cv_analysis_repo = container.cv_analysis_repository_port(session)
        cv_analysis = await cv_analysis_repo.get_by_id(request.cv_analysis_id)
        if not cv_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CV analysis {request.cv_analysis_id} not found"
            )

        # Start interview use case
        use_case = StartInterviewUseCase(
            vector_search=container.vector_search_port(),
            question_repository=container.question_repository_port(session),
        )

        interview = await use_case.execute(
            candidate_id=request.candidate_id,
            cv_analysis=cv_analysis,
            num_questions=request.num_questions,
        )

        # Save interview
        interview_repo = container.interview_repository_port(session)
        saved_interview = await interview_repo.save(interview)

        # Return response with WebSocket URL
        base_url = "ws://localhost:8000"  # TODO: Get from settings
        return InterviewResponse.from_domain(saved_interview, base_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{interview_id}",
    response_model=InterviewResponse,
    summary="Get interview details"
)
async def get_interview(
    interview_id: UUID,
    session = Depends(get_async_session),
    container = Depends(get_container),
):
    """Get interview by ID."""
    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found"
        )

    base_url = "ws://localhost:8000"
    return InterviewResponse.from_domain(interview, base_url)

@router.put(
    "/{interview_id}/start",
    response_model=InterviewResponse,
    summary="Start interview (move to IN_PROGRESS)"
)
async def start_interview(
    interview_id: UUID,
    session = Depends(get_async_session),
    container = Depends(get_container),
):
    """Start interview session."""
    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found"
        )

    try:
        interview.start()
        updated = await interview_repo.update(interview)

        base_url = "ws://localhost:8000"
        return InterviewResponse.from_domain(updated, base_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{interview_id}/questions/current",
    response_model=QuestionResponse,
    summary="Get current question"
)
async def get_current_question(
    interview_id: UUID,
    session = Depends(get_async_session),
    container = Depends(get_container),
):
    """Get current unanswered question."""
    use_case = GetNextQuestionUseCase(
        interview_repository=container.interview_repository_port(session),
        question_repository=container.question_repository_port(session),
    )

    try:
        question = await use_case.execute(interview_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No more questions available"
            )

        # Get interview for context
        interview = await container.interview_repository_port(session).get_by_id(interview_id)

        return QuestionResponse(
            id=question.id,
            text=question.text,
            question_type=question.question_type.value,
            difficulty=question.difficulty.value,
            index=interview.current_question_index,
            total=len(interview.question_ids),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

---

### Phase 4: WebSocket Handler

#### connection_manager.py
```python
from typing import Dict
from uuid import UUID
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for interviews."""

    def __init__(self):
        # interview_id → websocket
        self.active_connections: Dict[UUID, WebSocket] = {}

    async def connect(self, interview_id: UUID, websocket: WebSocket):
        """Accept and register WebSocket connection."""
        await websocket.accept()
        self.active_connections[interview_id] = websocket
        logger.info(f"WebSocket connected for interview {interview_id}")

    def disconnect(self, interview_id: UUID):
        """Remove connection."""
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]
            logger.info(f"WebSocket disconnected for interview {interview_id}")

    async def send_message(self, interview_id: UUID, message: dict):
        """Send message to specific interview connection."""
        websocket = self.active_connections.get(interview_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Send message to all connections."""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)

# Global instance
manager = ConnectionManager()
```

#### interview_handler.py
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from uuid import UUID
import json
import logging

from .connection_manager import manager
from .message_protocol import (
    TextAnswerMessage,
    QuestionMessage,
    EvaluationMessage,
    InterviewCompleteMessage,
    ErrorMessage,
)
from ....application.use_cases.process_answer import ProcessAnswerUseCase
from ....application.use_cases.get_next_question import GetNextQuestionUseCase
from ....application.use_cases.complete_interview import CompleteInterviewUseCase
from ....infrastructure.dependency_injection.container import get_container
from ....infrastructure.database.session import get_async_session

logger = logging.getLogger(__name__)

async def handle_interview_websocket(
    websocket: WebSocket,
    interview_id: UUID,
):
    """WebSocket handler for interview session.

    Protocol:
        Client → Server: { type: "text_answer", question_id: UUID, answer_text: str }
        Server → Client: { type: "evaluation", ... }
        Server → Client: { type: "question", ... }
        Server → Client: { type: "interview_complete", ... }
    """
    # Connect
    await manager.connect(interview_id, websocket)

    try:
        # Get dependencies
        container = get_container()

        # Send first question
        async with get_async_session() as session:
            use_case = GetNextQuestionUseCase(
                interview_repository=container.interview_repository_port(session),
                question_repository=container.question_repository_port(session),
            )

            question = await use_case.execute(interview_id)
            if question:
                # Get interview for context
                interview = await container.interview_repository_port(session).get_by_id(interview_id)

                # Mock TTS (generate audio)
                tts = container.text_to_speech_port()
                audio_bytes = await tts.synthesize_speech(question.text)
                import base64
                audio_data = base64.b64encode(audio_bytes).decode('utf-8')

                await manager.send_message(interview_id, {
                    "type": "question",
                    "question_id": str(question.id),
                    "text": question.text,
                    "question_type": question.question_type.value,
                    "difficulty": question.difficulty.value,
                    "index": interview.current_question_index,
                    "total": len(interview.question_ids),
                    "audio_data": audio_data,
                })

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "text_answer":
                await handle_text_answer(interview_id, data, container)

            elif message_type == "audio_chunk":
                await handle_audio_chunk(interview_id, data, container)

            elif message_type == "get_next_question":
                await handle_get_next_question(interview_id, container)

            else:
                await manager.send_message(interview_id, {
                    "type": "error",
                    "code": "UNKNOWN_MESSAGE_TYPE",
                    "message": f"Unknown message type: {message_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(interview_id)
        logger.info(f"Client disconnected from interview {interview_id}")

    except Exception as e:
        logger.error(f"WebSocket error for interview {interview_id}: {e}", exc_info=True)
        await manager.send_message(interview_id, {
            "type": "error",
            "code": "INTERNAL_ERROR",
            "message": str(e),
        })
        manager.disconnect(interview_id)

async def handle_text_answer(interview_id: UUID, data: dict, container):
    """Handle text answer from client."""
    async with get_async_session() as session:
        # Process answer
        use_case = ProcessAnswerUseCase(
            answer_repository=container.answer_repository_port(session),
            interview_repository=container.interview_repository_port(session),
            question_repository=container.question_repository_port(session),
            llm=container.llm_port(),
        )

        answer, has_more = await use_case.execute(
            interview_id=interview_id,
            question_id=UUID(data["question_id"]),
            answer_text=data["answer_text"],
        )

        # Send evaluation
        await manager.send_message(interview_id, {
            "type": "evaluation",
            "answer_id": str(answer.id),
            "score": answer.evaluation.score,
            "feedback": answer.evaluation.feedback,
            "strengths": answer.evaluation.strengths,
            "weaknesses": answer.evaluation.weaknesses,
        })

        # Send next question or complete
        if has_more:
            question_use_case = GetNextQuestionUseCase(
                interview_repository=container.interview_repository_port(session),
                question_repository=container.question_repository_port(session),
            )
            question = await question_use_case.execute(interview_id)

            if question:
                interview = await container.interview_repository_port(session).get_by_id(interview_id)

                # Mock TTS
                tts = container.text_to_speech_port()
                audio_bytes = await tts.synthesize_speech(question.text)
                import base64
                audio_data = base64.b64encode(audio_bytes).decode('utf-8')

                await manager.send_message(interview_id, {
                    "type": "question",
                    "question_id": str(question.id),
                    "text": question.text,
                    "question_type": question.question_type.value,
                    "difficulty": question.difficulty.value,
                    "index": interview.current_question_index,
                    "total": len(interview.question_ids),
                    "audio_data": audio_data,
                })
        else:
            # Complete interview
            complete_use_case = CompleteInterviewUseCase(
                interview_repository=container.interview_repository_port(session),
            )
            interview = await complete_use_case.execute(interview_id)

            await manager.send_message(interview_id, {
                "type": "interview_complete",
                "interview_id": str(interview.id),
                "overall_score": 85.0,  # TODO: Calculate actual score
                "total_questions": len(interview.question_ids),
                "feedback_url": f"/api/interviews/{interview_id}/feedback",
            })

async def handle_audio_chunk(interview_id: UUID, data: dict, container):
    """Handle audio chunk from client (for voice answers)."""
    # TODO: Implement audio streaming + STT
    # For now, mock implementation
    await manager.send_message(interview_id, {
        "type": "transcription",
        "text": "[Mock transcription of audio]",
        "is_final": data.get("is_final", False),
    })

async def handle_get_next_question(interview_id: UUID, container):
    """Handle request for next question."""
    async with get_async_session() as session:
        use_case = GetNextQuestionUseCase(
            interview_repository=container.interview_repository_port(session),
            question_repository=container.question_repository_port(session),
        )

        question = await use_case.execute(interview_id)
        if not question:
            await manager.send_message(interview_id, {
                "type": "error",
                "code": "NO_MORE_QUESTIONS",
                "message": "No more questions available",
            })
            return

        interview = await container.interview_repository_port(session).get_by_id(interview_id)

        # Mock TTS
        tts = container.text_to_speech_port()
        audio_bytes = await tts.synthesize_speech(question.text)
        import base64
        audio_data = base64.b64encode(audio_bytes).decode('utf-8')

        await manager.send_message(interview_id, {
            "type": "question",
            "question_id": str(question.id),
            "text": question.text,
            "question_type": question.question_type.value,
            "difficulty": question.difficulty.value,
            "index": interview.current_question_index,
            "total": len(interview.question_ids),
            "audio_data": audio_data,
        })
```

---

### Phase 5: Mock Adapters

#### mock_llm_adapter.py
```python
from typing import Dict, Any
from ...domain.ports.llm_port import LLMPort
from ...domain.models.question import Question
from ...domain.models.answer import AnswerEvaluation
import random

class MockLLMAdapter(LLMPort):
    """Mock LLM adapter for development/testing."""

    async def generate_question(
        self,
        context: Dict[str, Any],
        skill: str,
        difficulty: str,
    ) -> str:
        """Generate mock question."""
        return f"Mock question about {skill} at {difficulty} difficulty?"

    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        context: Dict[str, Any],
    ) -> AnswerEvaluation:
        """Generate mock evaluation."""
        score = random.uniform(70, 95)

        return AnswerEvaluation(
            score=score,
            feedback=f"Mock evaluation: Your answer demonstrates understanding of the topic.",
            completeness=0.85,
            relevance=0.90,
            technical_accuracy=0.80,
            sentiment="positive",
            strengths=[
                "Clear explanation",
                "Good examples",
            ],
            weaknesses=[
                "Could provide more detail",
            ],
            improvement_suggestions=[
                "Consider adding code examples",
            ],
        )

    async def generate_feedback_report(
        self,
        interview_summary: Dict[str, Any],
    ) -> str:
        """Generate mock feedback report."""
        return "Mock feedback report: Overall performance is good."

    async def summarize_cv(self, cv_text: str) -> str:
        """Generate mock CV summary."""
        return "Mock CV summary: Experienced software engineer."

    async def extract_skills_from_text(self, text: str) -> list[str]:
        """Extract mock skills."""
        return ["Python", "FastAPI", "PostgreSQL"]
```

#### mock_stt_adapter.py
```python
from ...domain.ports.speech_to_text_port import SpeechToTextPort
from typing import Optional

class MockSTTAdapter(SpeechToTextPort):
    """Mock STT adapter for development/testing."""

    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en-US",
    ) -> str:
        """Mock transcription."""
        return f"Mock transcription from {audio_file_path}"

    async def transcribe_stream(
        self,
        audio_stream: bytes,
        language: str = "en-US",
    ) -> str:
        """Mock stream transcription."""
        return f"Mock transcription from stream ({len(audio_stream)} bytes)"

    async def detect_language(
        self,
        audio_file_path: str,
    ) -> Optional[str]:
        """Mock language detection."""
        return "en-US"
```

#### mock_tts_adapter.py
```python
from ...domain.ports.text_to_speech_port import TextToSpeechPort
from typing import Optional

class MockTTSAdapter(TextToSpeechPort):
    """Mock TTS adapter for development/testing."""

    async def synthesize_speech(
        self,
        text: str,
        language: str = "en-US",
        voice: Optional[str] = None,
    ) -> bytes:
        """Mock speech synthesis."""
        # Return mock audio bytes (empty WAV header)
        return b"RIFF" + b"\x00" * 100  # Minimal WAV structure

    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        language: str = "en-US",
        voice: Optional[str] = None,
    ) -> str:
        """Mock save to file."""
        # In real implementation, would save actual audio
        with open(output_path, "wb") as f:
            f.write(await self.synthesize_speech(text, language, voice))
        return output_path

    async def list_available_voices(
        self,
        language: Optional[str] = None,
    ) -> list[dict]:
        """Mock voice list."""
        return [
            {"name": "mock-en-US-male", "language": "en-US", "gender": "male"},
            {"name": "mock-en-US-female", "language": "en-US", "gender": "female"},
        ]
```

---

### Phase 6: Integration

#### Update main.py
```python
# Add after line 13
from .adapters.api.websocket.interview_handler import handle_interview_websocket

# Add after line 78
app.include_router(
    interview_routes.router,
    prefix=settings.api_prefix,
    tags=["Interviews"]
)

# Add WebSocket route
@app.websocket("/ws/interviews/{interview_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    interview_id: UUID,
):
    await handle_interview_websocket(websocket, interview_id)
```

#### Update container.py
```python
# Add imports
from ..adapters.mock.mock_llm_adapter import MockLLMAdapter
from ..adapters.mock.mock_stt_adapter import MockSTTAdapter
from ..adapters.mock.mock_tts_adapter import MockTTSAdapter

# Modify methods (in Container class)
def llm_port(self) -> LLMPort:
    """Get LLM implementation."""
    if self._llm_port is None:
        if self.settings.use_mock_adapters:  # Add this setting
            self._llm_port = MockLLMAdapter()
        elif self.settings.llm_provider == "openai":
            self._llm_port = OpenAIAdapter(...)
    return self._llm_port

def speech_to_text_port(self) -> SpeechToTextPort:
    """Get STT implementation."""
    if self._stt_port is None:
        if self.settings.use_mock_adapters:
            self._stt_port = MockSTTAdapter()
        else:
            # Real implementation
            pass
    return self._stt_port

def text_to_speech_port(self) -> TextToSpeechPort:
    """Get TTS implementation."""
    if self._tts_port is None:
        if self.settings.use_mock_adapters:
            self._tts_port = MockTTSAdapter()
        else:
            # Real implementation
            pass
    return self._tts_port
```

#### Update settings.py
```python
# Add to Settings class
use_mock_adapters: bool = Field(
    default=True,
    description="Use mock adapters for development"
)

# WebSocket settings
ws_host: str = Field(default="localhost")
ws_port: int = Field(default=8000)
ws_base_url: str = Field(default="ws://localhost:8000")
```

---

## Database Schema Changes

**No schema changes needed** - existing tables support all requirements:
- `interviews` table has all fields for tracking session state
- `answers` table supports both text and audio answers
- `questions` table has embeddings for semantic search

---

## WebSocket Message Protocol

### Client → Server

#### Text Answer
```json
{
  "type": "text_answer",
  "question_id": "uuid",
  "answer_text": "My answer here..."
}
```

#### Audio Chunk (streaming)
```json
{
  "type": "audio_chunk",
  "chunk_data": "base64_encoded_audio",
  "is_final": false
}
```

#### Get Next Question
```json
{
  "type": "get_next_question"
}
```

---

### Server → Client

#### Question
```json
{
  "type": "question",
  "question_id": "uuid",
  "text": "What is async/await?",
  "question_type": "technical",
  "difficulty": "medium",
  "index": 0,
  "total": 10,
  "audio_data": "base64_encoded_tts"
}
```

#### Transcription (live)
```json
{
  "type": "transcription",
  "text": "partial transcription...",
  "is_final": false
}
```

#### Evaluation
```json
{
  "type": "evaluation",
  "answer_id": "uuid",
  "score": 85.5,
  "feedback": "Good explanation...",
  "strengths": ["Clear", "Accurate"],
  "weaknesses": ["Could add examples"]
}
```

#### Interview Complete
```json
{
  "type": "interview_complete",
  "interview_id": "uuid",
  "overall_score": 82.3,
  "total_questions": 10,
  "feedback_url": "/api/interviews/{id}/feedback"
}
```

#### Error
```json
{
  "type": "error",
  "code": "INVALID_QUESTION",
  "message": "Question not found"
}
```

---

## Testing Approach

### Unit Tests
```
tests/unit/application/use_cases/
├── test_get_next_question.py
├── test_process_answer.py
└── test_complete_interview.py

tests/unit/adapters/mock/
├── test_mock_llm.py
├── test_mock_stt.py
└── test_mock_tts.py
```

**Mock all ports**: Use pytest fixtures with `AsyncMock`

### Integration Tests
```
tests/integration/api/
├── test_interview_routes.py    # REST endpoints
└── test_websocket_handler.py   # WebSocket flow
```

**Use test database**: SQLite in-memory or test PostgreSQL instance

### E2E Tests
```
tests/e2e/
└── test_interview_flow.py      # Full interview cycle
```

**Test complete flow**:
1. Create interview → Start → WebSocket connect
2. Receive question → Submit answer → Get evaluation
3. Loop questions → Complete interview

---

## Error Handling

### API Layer
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### WebSocket Layer
- Send error messages in protocol format
- Close connection on critical errors
- Log all errors with context

### Domain Layer
- Raise `ValueError` for business rule violations
- Use domain exceptions (define in `src/domain/exceptions.py`)

---

## Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# Interview lifecycle events
logger.info(f"Interview {interview_id} created")
logger.info(f"Interview {interview_id} started")
logger.info(f"Question {question_id} sent to interview {interview_id}")
logger.info(f"Answer {answer_id} received for interview {interview_id}")
logger.info(f"Interview {interview_id} completed")

# WebSocket events
logger.info(f"WebSocket connected: interview {interview_id}")
logger.info(f"WebSocket disconnected: interview {interview_id}")

# Errors
logger.error(f"Failed to process answer: {e}", exc_info=True)
```

**Log context**: Always include `interview_id`, `question_id`, `answer_id` in structured logs

---

## Performance Considerations

### Database
- Use async queries throughout
- Connection pooling already configured
- Index on `interviews.status` for filtering

### WebSocket
- Single connection per interview (no broadcasting)
- Binary audio streaming (future optimization)
- Message size limits (prevent memory issues)

### Mock Adapters
- Fast responses (<100ms)
- No external API calls
- Deterministic behavior for testing

---

## Security Considerations

### Input Validation
- Pydantic models validate all inputs
- UUID validation for IDs
- Text length limits for answers

### WebSocket
- Validate interview_id exists before accepting connection
- Rate limiting (future: prevent spam)
- Authentication (future: JWT tokens)

### Data Protection
- No sensitive data in logs
- Secure audio file storage
- Sanitize error messages (no stack traces to client)

---

## Migration to Real Adapters

When replacing mock adapters with real implementations:

1. **LLM**: Replace `MockLLMAdapter` with `OpenAIAdapter` (already exists)
2. **Vector Search**: Already using `PineconeAdapter`
3. **STT**: Implement `AzureSTTAdapter` or `GoogleSTTAdapter`
4. **TTS**: Implement `EdgeTTSAdapter` or `GoogleTTSAdapter`

**Switch via config**:
```env
USE_MOCK_ADAPTERS=false  # Use real adapters
```

**No code changes needed** - dependency injection handles swapping

---

## Implementation Order

### Sprint 1: Foundation (Week 1)
1. Create DTOs (interview, answer, websocket)
2. Create use cases (get_next_question, process_answer, complete_interview)
3. Create mock adapters (LLM, STT, TTS)

### Sprint 2: REST API (Week 1)
4. Implement REST endpoints (create, get, start interview)
5. Update main.py and container.py
6. Test REST API with Postman/httpx

### Sprint 3: WebSocket (Week 2)
7. Implement connection manager
8. Implement WebSocket handler
9. Test with WebSocket client (wscat or Python)

### Sprint 4: Integration & Testing (Week 2)
10. Write unit tests
11. Write integration tests
12. Write E2E test
13. Fix bugs and refine

---

## Acceptance Criteria

### REST API
- ✅ `POST /api/interviews` creates session and returns `sessionId` + `wsUrl`
- ✅ `GET /api/interviews/{id}` returns interview details
- ✅ `PUT /api/interviews/{id}/start` moves to IN_PROGRESS
- ✅ `GET /api/interviews/{id}/questions/current` returns current question

### WebSocket
- ✅ Client connects to `ws://host/ws/interviews/{id}`
- ✅ Server sends first question on connection
- ✅ Client sends text answer
- ✅ Server evaluates and sends evaluation
- ✅ Server sends next question or completion message
- ✅ Audio streaming (basic mock implementation)

### Mock Adapters
- ✅ Mock LLM generates evaluations with random scores
- ✅ Mock STT returns placeholder transcription
- ✅ Mock TTS returns minimal audio bytes
- ✅ All mocks have <100ms response time

### Error Handling
- ✅ Invalid interview ID returns 404
- ✅ Invalid state transitions raise errors
- ✅ WebSocket errors send error messages
- ✅ All errors logged with context

---

## Unresolved Questions

1. **Audio Format**: What audio format for streaming? (WebM, Opus, PCM?)
2. **Audio Chunk Size**: Optimal chunk size for real-time streaming?
3. **Session Timeout**: How long before WebSocket auto-disconnects?
4. **Concurrent Sessions**: Can candidate have multiple active interviews?
5. **Authentication**: JWT in WebSocket URL query param or message?
6. **Rate Limiting**: Limit answers per second to prevent spam?
7. **Score Calculation**: How to aggregate answer scores into overall score?
8. **Partial Answers**: Allow saving draft answers?
9. **Interview Pause/Resume**: Support pausing and resuming later?
10. **WebSocket URL Format**: Include auth token? `ws://host/ws/interviews/{id}?token=...`

---

## Next Steps After Implementation

1. Replace mock adapters with real implementations (OpenAI already exists)
2. Add authentication/authorization middleware
3. Implement feedback report generation use case
4. Add analytics and performance tracking
5. Implement audio streaming for voice interviews
6. Add reconnection logic for WebSocket
7. Add interview recording/replay feature
8. Implement admin dashboard for monitoring

---

## Implementation Status

**Date Updated**: 2025-11-02
**Status**: ✅ **IMPLEMENTATION COMPLETE** ⚠ **CODE REVIEW REQUIRED FIXES**

### Completion Summary

**All planned features implemented**:
- ✅ Phase 1: DTOs (3 files)
- ✅ Phase 2: Use Cases (3 files)
- ✅ Phase 3: REST API (1 file)
- ✅ Phase 4: WebSocket (2 files)
- ✅ Phase 5: Mock Adapters (3 files)
- ✅ Phase 6: Integration (4 files modified)

**Total Created**: 12 files, ~950 lines
**Total Modified**: 4 files, ~80 lines

### Code Review Results

**Review Report**: `plans/reports/251102-from-code-reviewer-to-dev-interview-api-code-review.md`

**Overall Score**: 7.0/10 (Needs Work)

**Critical Issues Found**:
1. ❌ 6 null safety issues (runtime crash risk)
2. ⚠ 280 code style issues (87% auto-fixable)
3. ❌ 0% test coverage

**Positive Findings**:
- ✅ Architecture adherence: Excellent (10/10)
- ✅ Mock adapters: Excellent quality (9/10)
- ✅ WebSocket protocol: Well-designed (9/10)
- ✅ Error handling: Good structure (8/10)
- ✅ Performance: No concerns (9/10)

### Required Fixes Before Merge

**Immediate (4-6 hours)**:

1. **Fix Null Safety Issues** (2-3 hours)
   - File: `src/adapters/api/rest/interview_routes.py` (lines 210-211)
   - File: `src/adapters/api/websocket/interview_handler.py` (5 locations)
   - Add null checks before accessing `interview` and `evaluation` attributes

2. **Run Auto-fixes** (5 minutes)
   ```bash
   python -m ruff check --fix src/
   python -m black src/
   ```

3. **Add Exception Chaining** (10 minutes)
   - File: `src/adapters/api/rest/interview_routes.py` (lines 77, 159, 214)
   - Add `from e` to all `raise HTTPException(...)` statements

4. **Create Basic Integration Tests** (2-3 hours)
   - Test interview creation
   - Test WebSocket message flow
   - Target: 40%+ coverage on new code

### Next Actions

**Developer**:
1. Fix null safety issues in `interview_routes.py` and `interview_handler.py`
2. Run `ruff check --fix src/` and `black src/`
3. Add `from e` to exception handling
4. Create integration tests

**QA**:
1. Re-test after fixes
2. Verify null safety edge cases
3. Test WebSocket error scenarios

**Code Reviewer**:
1. Re-review after fixes
2. Verify all 6 null safety issues resolved
3. Confirm test coverage >40%

**Git Manager**:
1. Merge to development branch after approval
2. Tag as `v0.1.0-interview-api`

### Production Readiness Checklist

**Before Production Deployment**:
- [ ] Fix all null safety issues
- [ ] Achieve 80%+ test coverage
- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Add session timeouts
- [ ] Tighten CORS policy
- [ ] Add monitoring/alerting
- [ ] Load testing (100+ concurrent users)
- [ ] Security audit
- [ ] Documentation review

---

**End of Plan**