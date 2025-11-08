# System Architecture

**Last Updated**: 2025-11-02
**Version**: 0.1.0
**Project**: Elios AI Interview Service
**Repository**: https://github.com/elios/elios-ai-service

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Architectural Patterns](#architectural-patterns)
3. [Layer Architecture](#layer-architecture)
4. [Component Diagrams](#component-diagrams)
5. [Data Flow](#data-flow)
6. [Database Architecture](#database-architecture)
7. [External Service Integration](#external-service-integration)
8. [API Architecture](#api-architecture)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [Scalability & Performance](#scalability--performance)

## Architecture Overview

Elios AI Interview Service implements **Clean Architecture** (also known as Hexagonal Architecture or Ports & Adapters pattern) to achieve maximum flexibility, testability, and maintainability. The system is designed as a modular, loosely-coupled platform that can easily adapt to new technologies and requirements.

### Core Architectural Principles

**1. Dependency Inversion**
- Dependencies flow inward toward the domain
- Domain layer has zero external dependencies
- External services accessed through abstract interfaces (ports)

**2. Separation of Concerns**
- Each layer has a single, well-defined responsibility
- Business logic isolated from infrastructure
- Technology decisions deferred to outer layers

**3. Technology Independence**
- Swap LLM providers (OpenAI → Claude → Llama) without touching business logic
- Change databases without affecting domain models
- Switch frameworks without rewriting core logic

**4. Testability**
- Domain logic testable in complete isolation
- Mock external dependencies via ports
- Fast unit tests, comprehensive integration tests

### High-Level System Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         Users / Clients                        │
│                  (Web, Mobile, API Consumers)                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                       │
│              REST Endpoints + WebSocket Handlers               │
│                    (src/adapters/api/)                         │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────────┐
│                    Application Layer                           │
│           Use Cases (Business Flow Orchestration)              │
│                 (src/application/use_cases/)                   │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────────┐
│                     Domain Layer                               │
│          Pure Business Logic (Models + Services + Ports)       │
│                    (src/domain/)                               │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────────┐
│                    Adapters Layer                              │
│         External Service Implementations (Ports → Adapters)    │
│                   (src/adapters/)                              │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   LLM        │  Vector DB   │  Database    │  Speech      │ │
│  │  (OpenAI)    │  (Pinecone)  │ (PostgreSQL) │  (Azure)     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                          │
│       Config, Database Setup, DI Container, Logging            │
│                 (src/infrastructure/)                          │
└────────────────────────────────────────────────────────────────┘
```

## Architectural Patterns

### 1. Clean Architecture (Hexagonal/Ports & Adapters)

**Core Concept**: Business logic at the center, surrounded by adapters that connect to external world.

```
┌─────────────────────────────────────────────────────────┐
│                     Infrastructure                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │                     Adapters                      │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │                 Application                 │  │  │
│  │  │  ┌───────────────────────────────────────┐  │  │  │
│  │  │  │                Domain                 │  │  │  │
│  │  │  │  • Models (Entities)                  │  │  │  │
│  │  │  │  • Business Rules                     │  │  │  │
│  │  │  │  • Ports (Interfaces)                 │  │  │  │
│  │  │  │  • NO external dependencies           │  │  │  │
│  │  │  └───────────────────────────────────────┘  │  │  │
│  │  │          Use Cases (Orchestration)          │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │      Implementations (LLM, DB, API, Vector)       │  │
│  └───────────────────────────────────────────────────┘  │
│          Config, DI Container, Database Setup           │
└─────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Domain logic independent of frameworks and tools
- ✅ Easy to test (mock external dependencies)
- ✅ Easy to swap implementations
- ✅ Clear separation of concerns
- ✅ Delays technology decisions

### 2. Repository Pattern

**Purpose**: Abstract data access behind interfaces

```python
# Port (Interface) - in Domain
class CandidateRepositoryPort(ABC):
    @abstractmethod
    async def save(self, candidate: Candidate) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Optional[Candidate]:
        pass

# Adapter (Implementation) - in Adapters
class PostgreSQLCandidateRepository(CandidateRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, candidate: Candidate) -> None:
        # PostgreSQL-specific implementation
        db_model = CandidateMapper.to_db_model(candidate)
        self.session.add(db_model)
        await self.session.commit()

    async def find_by_id(self, id: UUID) -> Optional[Candidate]:
        # PostgreSQL-specific query
        stmt = select(CandidateModel).where(CandidateModel.id == id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return CandidateMapper.to_domain(db_model) if db_model else None
```

**Benefits**:
- Swap databases without changing domain logic
- Test domain logic with in-memory repositories
- Centralize data access logic

### 3. Dependency Injection

**Purpose**: Provide dependencies from outside, enable loose coupling

```python
# DI Container
class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._llm_port = None

    def llm_port(self) -> LLMPort:
        if self._llm_port is None:
            if self.settings.llm_provider == "openai":
                self._llm_port = OpenAIAdapter(...)
            elif self.settings.llm_provider == "claude":
                self._llm_port = ClaudeAdapter(...)
        return self._llm_port

# Use Case receives dependencies
class AnalyzeCVUseCase:
    def __init__(self, cv_analyzer: CVAnalyzerPort, vector_search: VectorSearchPort):
        self.cv_analyzer = cv_analyzer  # Injected
        self.vector_search = vector_search  # Injected
```

**Benefits**:
- Easy to test (inject mocks)
- Configuration-driven implementation selection
- Clear dependency graph

### 4. Aggregate Pattern (Domain-Driven Design)

**Purpose**: Group related entities with a root that controls access

```python
class Interview(BaseModel):  # Aggregate Root
    """Controls access to interview-related entities."""
    id: UUID
    candidate_id: UUID
    question_ids: List[UUID]  # References, not embedded
    answer_ids: List[UUID]    # References, not embedded
    status: InterviewStatus

    def add_question(self, question_id: UUID) -> None:
        """Interview controls how questions are added."""
        if self.status != InterviewStatus.READY:
            raise InvalidStateError("Cannot add questions after starting")
        self.question_ids.append(question_id)

    def add_answer(self, answer_id: UUID) -> None:
        """Interview controls how answers are recorded."""
        if not self.has_more_questions():
            raise InvalidStateError("No more questions to answer")
        self.answer_ids.append(answer_id)
        self.current_question_index += 1
```

**Benefits**:
- Enforces business invariants
- Clear ownership and boundaries
- Transactional consistency

## Layer Architecture

### Domain Layer (`src/domain/`)

**Responsibility**: Pure business logic with zero external dependencies

**Components**:

#### Models (`domain/models/`)
Rich entities with behavior, not anemic data containers:

```python
# Candidate.py - 41 lines
class Candidate(BaseModel):
    id: UUID
    name: str
    email: str
    cv_file_path: Optional[str]

    def update_cv(self, cv_file_path: str) -> None:
        """Business logic for updating CV."""
        self.cv_file_path = cv_file_path
        self.updated_at = datetime.utcnow()

# Interview.py - 137 lines (Aggregate Root)
class Interview(BaseModel):
    # 5 states: PREPARING, READY, IN_PROGRESS, COMPLETED, CANCELLED
    def start(self) -> None:
        """Business rule: Can only start if READY."""
        if self.status != InterviewStatus.READY:
            raise ValueError("Cannot start interview")
        self.status = InterviewStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

# Question.py - 84 lines
class Question(BaseModel):
    question_type: QuestionType  # TECHNICAL, BEHAVIORAL, SITUATIONAL
    difficulty: DifficultyLevel  # EASY, MEDIUM, HARD

    def is_suitable_for_difficulty(self, max_difficulty: DifficultyLevel) -> bool:
        """Business logic for question selection."""
        return self.difficulty <= max_difficulty

# CVAnalysis.py - 118 lines
class CVAnalysis(BaseModel):
    def get_technical_skills(self) -> List[ExtractedSkill]:
        """Business logic for filtering skills."""
        return [s for s in self.skills if s.is_technical()]
```

#### Ports (`domain/ports/`)
Abstract interfaces for external dependencies:

```python
# LLMPort - AI language model operations
class LLMPort(ABC):
    @abstractmethod
    async def generate_question(context: dict, skill: str) -> str: ...

    @abstractmethod
    async def evaluate_answer(question: Question, answer: str) -> AnswerEvaluation: ...

# VectorSearchPort - Semantic search operations
class VectorSearchPort(ABC):
    @abstractmethod
    async def find_similar_questions(embedding: List[float]) -> List[Question]: ...

# Repository Ports (5 total)
class CandidateRepositoryPort(ABC): ...
class InterviewRepositoryPort(ABC): ...
class QuestionRepositoryPort(ABC): ...
class AnswerRepositoryPort(ABC): ...
class CVAnalysisRepositoryPort(ABC): ...
```

**Dependencies**: Python stdlib, Pydantic only (no frameworks)

**Rules**:
- ✅ Can define interfaces (ports)
- ✅ Can have business logic
- ❌ Cannot import from adapters
- ❌ Cannot import frameworks (FastAPI, SQLAlchemy, etc.)
- ❌ Cannot make API calls or database queries

### Application Layer (`src/application/`)

**Responsibility**: Orchestrate domain objects to accomplish business flows

**Components**:

#### Use Cases (`application/use_cases/`)
Application-specific workflows:

```python
# AnalyzeCVUseCase.py - 83 lines
class AnalyzeCVUseCase:
    """Orchestrates CV analysis workflow."""

    def __init__(self, cv_analyzer: CVAnalyzerPort, vector_search: VectorSearchPort):
        self.cv_analyzer = cv_analyzer
        self.vector_search = vector_search

    async def execute(self, cv_file_path: str, candidate_id: UUID) -> CVAnalysis:
        # Step 1: Analyze CV
        cv_analysis = await self.cv_analyzer.analyze_cv(cv_file_path, candidate_id)

        # Step 2: Generate embeddings
        embedding = await self.vector_search.get_embedding(...)
        cv_analysis.embedding = embedding

        # Step 3: Store in vector DB
        await self.vector_search.store_cv_embedding(cv_analysis.id, embedding)

        return cv_analysis

# StartInterviewUseCase.py
class StartInterviewUseCase:
    """Orchestrates interview initialization."""

    async def execute(self, candidate_id: UUID, cv_analysis_id: UUID) -> Interview:
        # Step 1: Create interview
        interview = Interview(candidate_id=candidate_id)

        # Step 2: Select questions (semantic search)
        questions = await self.find_relevant_questions(cv_analysis_id)

        # Step 3: Add questions to interview
        for question in questions:
            interview.add_question(question.id)

        # Step 4: Mark as ready
        interview.mark_ready(cv_analysis_id)

        return interview
```

**Dependencies**: Domain models and ports only

**Rules**:
- ✅ Can orchestrate domain objects
- ✅ Can depend on domain ports
- ❌ Cannot depend on adapters
- ❌ Cannot contain business logic (delegate to domain)

### Adapters Layer (`src/adapters/`)

**Responsibility**: Implement domain ports with concrete technologies

**Components**:

#### LLM Adapters (`adapters/llm/`)

```python
# OpenAIAdapter.py - 269 lines ✅
class OpenAIAdapter(LLMPort):
    """OpenAI GPT-4 implementation of LLM port."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_question(self, context: dict, skill: str) -> str:
        # OpenAI-specific API call
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[...],
        )
        return response.choices[0].message.content

    async def evaluate_answer(self, question: Question, answer: str) -> AnswerEvaluation:
        # Structured JSON output from GPT-4
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[...],
            response_format={"type": "json_object"},
        )
        return AnswerEvaluation(**json.loads(response.choices[0].message.content))

# Future: ClaudeAdapter, LlamaAdapter
```

#### Vector Database Adapters (`adapters/vector_db/`)

```python
# PineconeAdapter.py ✅
class PineconeAdapter(VectorSearchPort):
    """Pinecone serverless implementation."""

    def __init__(self, api_key: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    async def find_similar_questions(self, embedding: List[float], limit: int) -> List[Question]:
        # Pinecone similarity search
        results = self.index.query(
            vector=embedding,
            top_k=limit,
            include_metadata=True,
        )
        return [self._to_question(match) for match in results.matches]

# Future: WeaviateAdapter, ChromaAdapter
```

#### Persistence Adapters (`adapters/persistence/`)

**5 PostgreSQL Repositories** ✅:

```python
# PostgreSQLCandidateRepository.py
class PostgreSQLCandidateRepository(CandidateRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, candidate: Candidate) -> None:
        db_model = CandidateMapper.to_db_model(candidate)
        self.session.add(db_model)
        await self.session.commit()

    async def find_by_id(self, id: UUID) -> Optional[Candidate]:
        stmt = select(CandidateModel).where(CandidateModel.id == id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return CandidateMapper.to_domain(db_model) if db_model else None

# Similarly: PostgreSQLInterviewRepository, PostgreSQLQuestionRepository,
#            PostgreSQLAnswerRepository, PostgreSQLCVAnalysisRepository
```

**Database Models** (`persistence/models.py`):
- SQLAlchemy 2.0 async models
- Separate from domain models (persistence ignorance)
- PostgreSQL-specific types (UUID, JSONB, ARRAY)

**Mappers** (`persistence/mappers.py`):
- Bidirectional conversion: Domain ↔ Database
- Handle type conversions, relationships, null values

#### API Adapters (`adapters/api/`)

```python
# REST API (FastAPI)
@router.post("/candidates", response_model=CandidateResponse)
async def create_candidate(
    request: CreateCandidateRequest,
    container: Container = Depends(get_container),
):
    # Get use case from DI container
    use_case = CreateCandidateUseCase(
        repository=container.candidate_repository_port(session),
    )

    # Execute use case
    candidate = await use_case.execute(name=request.name, email=request.email)

    # Return response DTO
    return CandidateResponse.from_domain(candidate)

# WebSocket (planned)
@router.websocket("/ws/interviews/{interview_id}")
async def interview_chat(websocket: WebSocket, interview_id: UUID):
    await websocket.accept()
    # Real-time interview handling
```

**Dependencies**: All layers (can import everything)

**Rules**:
- ✅ Can implement domain ports
- ✅ Can use external libraries
- ✅ Must be swappable
- ❌ Should not depend on other adapters

### Infrastructure Layer (`src/infrastructure/`)

**Responsibility**: Cross-cutting concerns and application bootstrap

**Components**:

#### Configuration (`infrastructure/config/`)

```python
# settings.py - 124 lines ✅
class Settings(BaseSettings):
    """Type-safe configuration from environment variables."""

    # Application
    app_name: str = "Elios AI Service"
    environment: str = "development"

    # LLM Provider
    llm_provider: str = "openai"
    openai_api_key: str
    openai_model: str = "gpt-4"

    # Vector DB
    vector_db_provider: str = "pinecone"
    pinecone_api_key: str
    pinecone_index_name: str

    # Database
    database_url: str

    @property
    def async_database_url(self) -> str:
        """Convert to async URL, strip SSL params for asyncpg."""
        url = re.sub(r'^postgresql:', 'postgresql+asyncpg:', self.database_url)
        url = re.sub(r'\?sslmode=[^&]*', '', url)  # Strip incompatible params
        return url

    class Config:
        env_file = ".env.local"  # Priority: .env.local → .env → system
```

#### Database (`infrastructure/database/`)

```python
# session.py - 129 lines ✅
async_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None

async def init_db() -> None:
    """Initialize database on application startup."""
    global async_engine, AsyncSessionLocal

    settings = get_settings()
    async_engine = create_async_engine(
        settings.async_database_url,
        poolclass=QueuePool if settings.is_production() else NullPool,
        pool_size=10 if settings.is_production() else 0,
    )
    AsyncSessionLocal = async_sessionmaker(async_engine, ...)

async def close_db() -> None:
    """Close database on application shutdown."""
    if async_engine:
        await async_engine.dispose()

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection function for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

#### Dependency Injection (`infrastructure/dependency_injection/`)

```python
# container.py - 259 lines ✅
class Container:
    """Central DI container wiring all dependencies."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._llm_port = None
        self._vector_search_port = None

    def llm_port(self) -> LLMPort:
        """Get LLM implementation based on config."""
        if self._llm_port is None:
            if self.settings.llm_provider == "openai":
                self._llm_port = OpenAIAdapter(
                    api_key=self.settings.openai_api_key,
                    model=self.settings.openai_model,
                )
            elif self.settings.llm_provider == "claude":
                # Future implementation
                raise NotImplementedError("Claude not yet implemented")
        return self._llm_port

    def candidate_repository_port(self, session: AsyncSession) -> CandidateRepositoryPort:
        """Get candidate repository."""
        return PostgreSQLCandidateRepository(session)

    # Similar for all other dependencies...

@lru_cache
def get_container() -> Container:
    """Singleton container instance."""
    return Container(get_settings())
```

## Component Diagrams

### Interview Flow Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Request                            │
│                  POST /api/cv/upload                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer                                   │
│  upload_cv_endpoint(file, candidate_id)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Use Case Layer                                  │
│  AnalyzeCVUseCase.execute()                                     │
│    ├─→ cv_analyzer.analyze_cv()          [CVAnalyzerPort]      │
│    ├─→ vector_search.get_embedding()     [VectorSearchPort]    │
│    └─→ vector_search.store_cv_embedding()[VectorSearchPort]    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Domain Layer                                    │
│  CVAnalysis (entity with business logic)                        │
│    └─→ get_technical_skills()                                   │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Adapter Layer                                   │
│  SpacyCVAnalyzer (implements CVAnalyzerPort)                    │
│  PineconeAdapter (implements VectorSearchPort)                  │
│  OpenAIAdapter (for embeddings)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Question Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Start Interview                               │
│              StartInterviewUseCase                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│          Get CV Analysis from Repository                         │
│      cv_analysis_repo.find_by_id(cv_analysis_id)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│         Find Similar Questions (Semantic Search)                 │
│  vector_search.find_similar_questions(cv_analysis.embedding)    │
│    → Returns questions matching candidate's skills               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              Filter & Rank Questions                             │
│  Domain logic: difficulty, skill coverage, diversity            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              Create Interview Entity                             │
│  interview = Interview(candidate_id, status=PREPARING)          │
│  interview.add_question(q1.id)                                  │
│  interview.add_question(q2.id)                                  │
│  interview.mark_ready(cv_analysis_id)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              Persist Interview                                   │
│  interview_repo.save(interview)                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### CV Upload to Interview Ready Flow

```
1. User Uploads CV
   ├─→ POST /api/cv/upload
   │   ├─ file: CV document (PDF/DOC)
   │   └─ candidate_id: UUID

2. API Layer validates request
   └─→ Calls AnalyzeCVUseCase

3. AnalyzeCVUseCase orchestrates:
   ├─→ Extract text from CV file
   │   └─ SpacyCVAnalyzer (future) / PyPDF2
   │
   ├─→ Analyze CV content
   │   ├─ OpenAI GPT-4: extract skills, summarize
   │   └─ Create CVAnalysis entity
   │
   ├─→ Generate embeddings
   │   └─ OpenAI Embeddings API (1536 dimensions)
   │
   ├─→ Store embeddings in Pinecone
   │   └─ PineconeAdapter.store_cv_embedding()
   │
   └─→ Save CVAnalysis to database
       └─ PostgreSQLCVAnalysisRepository.save()

4. Return CVAnalysis to client
   └─ Status 201 Created

5. Start Interview Flow (separate request)
   ├─→ POST /api/interviews
   │   ├─ candidate_id: UUID
   │   └─ cv_analysis_id: UUID
   │
   └─→ StartInterviewUseCase
       ├─ Find similar questions (vector search)
       ├─ Create Interview entity
       ├─ Add selected questions
       ├─ Mark as READY
       └─ Save to database

6. Interview Ready
   └─ Client can now start asking questions
```

### Answer Evaluation Flow

```
1. Candidate Submits Answer
   ├─→ POST /api/interviews/{id}/answers
   │   ├─ question_id: UUID
   │   └─ answer_text: string

2. API Layer calls ProcessAnswerUseCase

3. ProcessAnswerUseCase orchestrates:
   ├─→ Get Question from repository
   │   └─ QuestionRepository.find_by_id()
   │
   ├─→ Get Interview context
   │   └─ InterviewRepository.find_by_id()
   │
   ├─→ Evaluate answer (Multi-dimensional)
   │   ├─ OpenAI GPT-4: evaluate quality
   │   │   ├─ Score (0-100)
   │   │   ├─ Completeness (0-1)
   │   │   ├─ Relevance (0-1)
   │   │   ├─ Sentiment analysis
   │   │   ├─ Strengths
   │   │   ├─ Weaknesses
   │   │   └─ Improvement suggestions
   │   │
   │   ├─ Generate answer embedding
   │   │   └─ OpenAI Embeddings API
   │   │
   │   └─ Semantic similarity with reference answer
   │       └─ Pinecone similarity search
   │
   ├─→ Create Answer entity with evaluation
   │   └─ Answer(question_id, text, evaluation)
   │
   ├─→ Update Interview
   │   ├─ interview.add_answer(answer.id)
   │   └─ interview.current_question_index++
   │
   ├─→ Save Answer to database
   │   └─ AnswerRepository.save()
   │
   └─→ Update Interview in database
       └─ InterviewRepository.update()

4. Return AnswerEvaluation to client
   └─ Real-time feedback displayed

5. Check if interview complete
   ├─ if interview.has_more_questions():
   │   └─ Return next question
   └─ else:
       └─ Trigger CompleteInterviewUseCase
```

## Database Architecture

### Schema Design

```sql
-- Core Tables (5 total)

-- Candidates
CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    cv_file_path VARCHAR(500),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- CV Analyses
CREATE TABLE cv_analyses (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    cv_file_path VARCHAR(500) NOT NULL,
    extracted_text TEXT NOT NULL,
    skills JSONB,  -- Array of ExtractedSkill
    work_experience_years FLOAT,
    education_level VARCHAR(100),
    suggested_topics TEXT[],  -- PostgreSQL array
    suggested_difficulty VARCHAR(50),
    embedding FLOAT[],  -- 1536 dimensions
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_cv_analyses_candidate ON cv_analyses(candidate_id);
CREATE INDEX idx_cv_analyses_skills ON cv_analyses USING GIN(skills);

-- Questions
CREATE TABLE questions (
    id UUID PRIMARY KEY,
    text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,  -- TECHNICAL, BEHAVIORAL, SITUATIONAL
    difficulty VARCHAR(50) NOT NULL,     -- EASY, MEDIUM, HARD
    skills TEXT[],  -- PostgreSQL array
    tags TEXT[],
    reference_answer TEXT,
    evaluation_criteria TEXT,
    version INT DEFAULT 1,
    embedding FLOAT[],  -- 1536 dimensions for semantic search
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_skills ON questions USING GIN(skills);

-- Interviews
CREATE TABLE interviews (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    status VARCHAR(50) NOT NULL,  -- PREPARING, READY, IN_PROGRESS, COMPLETED, CANCELLED
    cv_analysis_id UUID REFERENCES cv_analyses(id),
    question_ids UUID[],  -- Ordered array of question IDs
    answer_ids UUID[],    -- Ordered array of answer IDs
    current_question_index INT DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_interviews_candidate ON interviews(candidate_id);
CREATE INDEX idx_interviews_status ON interviews(status);
CREATE INDEX idx_interviews_cv_analysis ON interviews(cv_analysis_id);

-- Answers
CREATE TABLE answers (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL REFERENCES interviews(id),
    question_id UUID NOT NULL REFERENCES questions(id),
    answer_text TEXT NOT NULL,
    answer_mode VARCHAR(50),  -- TEXT, VOICE
    audio_file_path VARCHAR(500),
    transcript TEXT,
    evaluation JSONB,  -- AnswerEvaluation object
    metadata JSONB,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_answers_interview ON answers(interview_id);
CREATE INDEX idx_answers_question ON answers(question_id);

-- Alembic version tracking
CREATE TABLE alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);
```

### Entity Relationships

```
Candidate (1) ──────→ (N) CVAnalysis
    │
    └──────────→ (N) Interview
                       │
                       ├──→ (1) CVAnalysis
                       ├──→ (N) Question (via question_ids array)
                       └──→ (N) Answer
                              └──→ (1) Question
```

### Database Access Patterns

**1. Candidate Lookup** (by email):
```python
stmt = select(CandidateModel).where(CandidateModel.email == email)
# Uses index: candidates(email) UNIQUE
```

**2. Interview by Status** (find active interviews):
```python
stmt = select(InterviewModel).where(InterviewModel.status == "in_progress")
# Uses index: interviews(status)
```

**3. Questions by Skills** (semantic search preparation):
```python
stmt = select(QuestionModel).where(QuestionModel.skills.contains(["Python"]))
# Uses GIN index: questions(skills)
```

**4. Answers for Interview** (fetch all):
```python
stmt = select(AnswerModel).where(AnswerModel.interview_id == interview_id)
# Uses index: answers(interview_id)
```

## External Service Integration

### LLM Integration (OpenAI GPT-4)

**Use Cases**:
1. Question Generation
2. Answer Evaluation
3. Feedback Report Generation
4. CV Summarization
5. Skill Extraction

**Architecture**:
```python
# Port (Interface)
class LLMPort(ABC):
    @abstractmethod
    async def generate_question(...) -> str: pass

    @abstractmethod
    async def evaluate_answer(...) -> AnswerEvaluation: pass

# Adapter (Implementation)
class OpenAIAdapter(LLMPort):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def evaluate_answer(self, question, answer_text, context) -> AnswerEvaluation:
        # Structured output with JSON mode
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[...],
            temperature=0.3,  # Low for consistent evaluation
            response_format={"type": "json_object"},
        )
        return AnswerEvaluation(**json.loads(response.choices[0].message.content))
```

**Configuration**:
- Model: `gpt-4` (primary), `gpt-4-turbo-preview` (faster alternative)
- Temperature: 0.7 (generation), 0.3 (evaluation)
- Max tokens: Varies by use case
- Timeout: 30 seconds
- Retry: 3 attempts with exponential backoff

### Vector Database Integration (Pinecone)

**Use Cases**:
1. Store question embeddings
2. Store CV embeddings
3. Semantic similarity search
4. Question recommendation

**Architecture**:
```python
# Port (Interface)
class VectorSearchPort(ABC):
    @abstractmethod
    async def store_cv_embedding(cv_id: UUID, embedding: List[float], metadata: dict): pass

    @abstractmethod
    async def find_similar_questions(embedding: List[float], limit: int) -> List[Question]: pass

# Adapter (Implementation)
class PineconeAdapter(VectorSearchPort):
    def __init__(self, api_key: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    async def find_similar_questions(self, embedding, limit):
        results = self.index.query(
            vector=embedding,
            top_k=limit,
            include_metadata=True,
        )
        return [self._to_question(match) for match in results.matches]
```

**Configuration**:
- Index: Serverless (AWS us-east-1)
- Dimensions: 1536 (OpenAI embeddings)
- Metric: Cosine similarity
- Pods: Serverless auto-scales

### Database Integration (PostgreSQL via Neon)

**Connection**:
- Provider: Neon (serverless PostgreSQL)
- Driver: asyncpg (async Python driver)
- ORM: SQLAlchemy 2.0 async
- Pooling: QueuePool in production, NullPool in development

**Configuration**:
```python
# Development
create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    poolclass=NullPool,  # No pooling
    echo=True,  # Log SQL
)

# Production
create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

## API Architecture

### REST API Design

**Base URL**: `/api`

**Endpoints**:

```
# Health
GET  /health                                      # Health check ✅

# Interviews ✅
POST   /api/interviews                            # Create interview session ✅
GET    /api/interviews/{id}                       # Get interview details ✅
PUT    /api/interviews/{id}/start                 # Start interview ✅
GET    /api/interviews/{id}/questions/current     # Get current question ✅

# Planned
# Candidates
POST   /api/candidates                            # Create candidate ⏳
GET    /api/candidates/{id}                       # Get candidate ⏳
PUT    /api/candidates/{id}                       # Update candidate ⏳
DELETE /api/candidates/{id}                       # Delete candidate ⏳

# CV Analysis
POST /api/cv/upload                               # Upload and analyze CV ⏳
GET  /api/cv/{id}                                 # Get CV analysis ⏳

# Answers
POST /api/interviews/{id}/answers                 # Submit answer ⏳
GET  /api/interviews/{id}/answers                 # Get all answers ⏳

# Questions (Admin)
POST   /api/questions                             # Create question ⏳
GET    /api/questions                             # List questions ⏳
GET    /api/questions/{id}                        # Get question ⏳
PUT    /api/questions/{id}                        # Update question ⏳
DELETE /api/questions/{id}                        # Delete question ⏳

# Feedback
GET /api/interviews/{id}/feedback                 # Get comprehensive feedback ⏳
```

### WebSocket API ✅

**Endpoint**: `/ws/interviews/{interview_id}`

**Protocol**:

```json
// Client → Server: Submit text answer
{
  "type": "text_answer",
  "question_id": "uuid",
  "answer_text": "string"
}

// Client → Server: Submit audio chunk
{
  "type": "audio_chunk",
  "audio_data": "base64_encoded_audio",
  "is_final": false
}

// Client → Server: Request next question
{
  "type": "get_next_question"
}

// Server → Client: Send question with audio
{
  "type": "question",
  "question_id": "uuid",
  "text": "What is...?",
  "question_type": "technical",
  "difficulty": "medium",
  "index": 0,
  "total": 5,
  "audio_data": "base64_encoded_tts_audio"
}

// Server → Client: Answer evaluation
{
  "type": "evaluation",
  "answer_id": "uuid",
  "score": 85.5,
  "feedback": "Good answer...",
  "strengths": ["Clear explanation", "Good examples"],
  "weaknesses": ["Missing edge cases"]
}

// Server → Client: Interview complete
{
  "type": "interview_complete",
  "interview_id": "uuid",
  "overall_score": 78.5,
  "total_questions": 5,
  "feedback_url": "/api/interviews/{id}/feedback"
}

// Server → Client: Error
{
  "type": "error",
  "code": "INTERVIEW_NOT_FOUND",
  "message": "Interview {id} not found"
}

// Server → Client: Audio transcription (STT)
{
  "type": "transcription",
  "text": "Transcribed text...",
  "is_final": true
}
```

**Features**:
- Real-time bi-directional communication
- Automatic question delivery with TTS audio
- Answer evaluation and immediate feedback
- Progress tracking (current/total questions)
- Error handling with descriptive codes
- Support for both text and voice answers
- Connection management via ConnectionManager

## Security Architecture

### Authentication & Authorization (Planned)

**JWT-based authentication**:
```
1. User logs in → Receives JWT token
2. Include token in Authorization header
3. Verify token on each request
4. Extract user identity from token claims
```

**Authorization levels**:
- **Candidate**: Can manage own interviews
- **Recruiter**: Can view candidate results
- **Admin**: Full system access

### Data Protection

**In Transit**:
- HTTPS for all API communications
- TLS 1.3 minimum
- Secure WebSocket (WSS)

**At Rest**:
- Database encryption (Neon built-in)
- Encrypted CV file storage
- Environment variables for secrets

**PII Handling**:
- Minimal PII collection
- Data retention policies
- GDPR compliance (right to deletion)
- Anonymization for analytics

### Input Validation

**Layers**:
1. **API Layer**: Pydantic models validate request data
2. **Domain Layer**: Business rule validation
3. **Database Layer**: Constraints and checks

**SQL Injection Prevention**:
- Parameterized queries only
- SQLAlchemy ORM (not raw SQL)
- No string interpolation in queries

**XSS Prevention**:
- Output encoding
- Content Security Policy headers
- Sanitize user-generated content

## Deployment Architecture

### Development Environment

```
Developer Machine
├── Python 3.11+ virtual environment
├── PostgreSQL (Neon cloud)
├── Environment variables (.env.local)
└── FastAPI development server (uvicorn)
```

### Production Environment (Planned)

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
│                  (AWS ALB / Nginx)                       │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
┌──────────────────┐  ┌──────────────────┐
│  API Server 1    │  │  API Server 2    │  (Horizontal scaling)
│  (Docker)        │  │  (Docker)        │
│  FastAPI/Uvicorn │  │  FastAPI/Uvicorn │
└──────────────────┘  └──────────────────┘
          │                     │
          └──────────┬──────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│  ┌──────────────┬──────────────┬──────────────────┐     │
│  │ PostgreSQL   │  Pinecone    │  OpenAI          │     │
│  │ (Neon)       │  (Serverless)│  (GPT-4)         │     │
│  └──────────────┴──────────────┴──────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Docker Deployment (Planned)

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install -e .

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml** (local development):
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - postgres

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: elios_dev
      POSTGRES_USER: elios
      POSTGRES_PASSWORD: elios
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Scalability & Performance

### Horizontal Scaling

**Stateless Design**:
- No session state in API servers
- All state in database or external services
- Can run N instances behind load balancer

**Database Connection Pooling**:
- Connection pool per API instance
- Pool size: 10 connections
- Max overflow: 20 connections
- Prevents connection exhaustion

**Async Operations**:
- Non-blocking I/O throughout
- Concurrent request handling
- Efficient resource utilization

### Caching Strategy (Planned)

**Question Cache**:
- Cache frequent question queries
- TTL: 1 hour
- Invalidate on question update

**CV Embedding Cache**:
- Cache recent CV embeddings
- TTL: 24 hours
- Reduce redundant API calls

**Redis Integration** (future):
```python
# Cache expensive operations
async def get_cv_analysis(cv_id: UUID) -> CVAnalysis:
    # Try cache first
    cached = await redis.get(f"cv:{cv_id}")
    if cached:
        return CVAnalysis.parse_raw(cached)

    # Cache miss - fetch from DB
    analysis = await repository.find_by_id(cv_id)
    await redis.setex(f"cv:{cv_id}", 3600, analysis.json())
    return analysis
```

### Performance Targets

- **API Response Time**: < 200ms (p95)
- **Database Query Time**: < 100ms (p95)
- **CV Analysis**: < 30 seconds
- **Question Generation**: < 3 seconds
- **Answer Evaluation**: < 5 seconds
- **Concurrent Interviews**: 100+
- **Uptime**: 99.5%

### Monitoring & Observability (Planned)

**Metrics**:
- Request latency (p50, p95, p99)
- Error rates
- Database connection pool usage
- External API success rates
- Interview completion rates

**Logging**:
- Structured JSON logs
- Correlation IDs for request tracing
- Error stack traces
- Performance markers

**Alerting**:
- High error rates
- Slow response times
- Database connection issues
- External API failures

## References

### Internal Documentation
- [Project Overview & PDR](./project-overview-pdr.md)
- [Codebase Summary](./codebase-summary.md)
- [Code Standards](./code-standards.md)
- [Database Setup Guide](../DATABASE_SETUP.md)

### External Resources
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

---

**Document Status**: Living document, updated with architectural changes
**Next Review**: After Phase 1 completion or major architectural decisions
**Maintainers**: Elios Development Team
