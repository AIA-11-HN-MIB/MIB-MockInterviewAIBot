# Codebase Summary

**Last Updated**: 2025-11-15
**Version**: 0.2.2
**Repository**: https://github.com/elios/elios-ai-service

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Core Technologies](#core-technologies)
- [Key Components](#key-components)
- [Entry Points](#entry-points)
- [Development Workflow](#development-workflow)
- [Development Principles](#development-principles)
- [Implementation Status](#implementation-status)
- [File Statistics](#file-statistics)
- [Dependencies Overview](#dependencies-overview)
- [Performance Considerations](#performance-considerations)
- [Security Measures](#security-measures)
- [Deployment](#deployment)
- [Related Documentation](#related-documentation)
- [External Resources](#external-resources)
- [Unresolved Questions](#unresolved-questions)

## Overview

Elios AI Interview Service is Python-based AI-powered mock interview platform built with Clean Architecture principles (Hexagonal/Ports & Adapters pattern). Platform emphasizes separation of concerns, testability, flexibility through abstract interfaces and dependency injection. Integrates OpenAI GPT-4 for NLP, Pinecone for vector-based semantic search, PostgreSQL for persistent storage.

**Recent Major Changes** (2025-11-15):
- WebSocket URL injection in planning responses (seamless client flow)
- Context-aware evaluation with entity separation
- Domain-Driven State Management (migrated from WebSocket orchestrator)
- Follow-up question evaluation refactoring
- Enhanced LLM response parsing with JSON extraction

## Project Structure

```
EliosAIService/
├── src/                          # Source code (Clean Architecture layers)
│   ├── domain/                   # Core business logic (no external dependencies)
│   │   ├── models/              # Domain entities (8 files)
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py     # Candidate entity
│   │   │   ├── interview.py     # Interview aggregate root (Domain-Driven State)
│   │   │   ├── question.py      # Question value object
│   │   │   ├── answer.py        # Answer entity with evaluation
│   │   │   ├── follow_up_question.py  # Follow-up question for adaptive interviews
│   │   │   ├── cv_analysis.py   # CV analysis entity
│   │   │   ├── evaluation.py    # Evaluation entity with context separation
│   │   │   └── error_codes.py   # Error code enumeration
│   │   └── ports/               # Abstract interfaces (13 files)
│   │       ├── llm_port.py                      # LLM interface
│   │       ├── vector_search_port.py            # Vector DB interface
│   │       ├── cv_analyzer_port.py              # CV processing interface
│   │       ├── speech_to_text_port.py           # STT interface
│   │       ├── text_to_speech_port.py           # TTS interface
│   │       ├── analytics_port.py                # Analytics interface
│   │       ├── question_repository_port.py      # Question persistence
│   │       ├── candidate_repository_port.py     # Candidate persistence
│   │       ├── interview_repository_port.py     # Interview persistence
│   │       ├── answer_repository_port.py        # Answer persistence
│   │       ├── cv_analysis_repository_port.py   # CV analysis persistence
│   │       ├── follow_up_question_repository_port.py  # Follow-up persistence
│   │       └── evaluation_repository_port.py    # Evaluation persistence (NEW)
│   ├── application/             # Use cases and orchestration
│   │   ├── dto/                 # Data Transfer Objects (4 files)
│   │   │   ├── interview_dto.py # Interview DTOs (incl. PlanningStatusResponse w/ ws_url)
│   │   │   ├── answer_dto.py    # Answer request/response DTOs
│   │   │   ├── audio_dto.py     # Audio processing DTOs (NEW)
│   │   │   └── websocket_dto.py # WebSocket message DTOs
│   │   └── use_cases/           # Application business flows (8 files)
│   │       ├── analyze_cv.py    # CV analysis workflow
│   │       ├── plan_interview.py # Interview planning with adaptive questions
│   │       ├── get_next_question.py # Retrieve next question
│   │       ├── process_answer_adaptive.py # Adaptive answer evaluation
│   │       ├── complete_interview.py # Finalize interview session
│   │       ├── generate_summary.py # Interview summary generation
│   │       ├── follow_up_decision.py # Follow-up decision logic
│   │       └── combine_evaluation.py # Combine evaluations (NEW)
│   ├── adapters/                # External service implementations
│   │   ├── llm/                 # LLM provider adapters
│   │   │   ├── openai_adapter.py # OpenAI GPT-4 implementation
│   │   │   └── azure_openai_adapter.py # Azure OpenAI implementation
│   │   ├── vector_db/           # Vector database adapters
│   │   │   ├── pinecone_adapter.py # Pinecone implementation
│   │   │   └── chroma_adapter.py # ChromaDB implementation (NEW)
│   │   ├── mock/                # Mock adapters for development (6 total)
│   │   │   ├── mock_llm_adapter.py
│   │   │   ├── mock_vector_search_adapter.py
│   │   │   ├── mock_stt_adapter.py
│   │   │   ├── mock_tts_adapter.py
│   │   │   ├── mock_cv_analyzer.py
│   │   │   └── mock_analytics.py
│   │   ├── persistence/         # Database adapters (10 files)
│   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   ├── mappers.py       # Domain ↔ DB model conversion
│   │   │   ├── candidate_repository.py
│   │   │   ├── question_repository.py
│   │   │   ├── interview_repository.py
│   │   │   ├── answer_repository.py
│   │   │   ├── cv_analysis_repository.py
│   │   │   ├── follow_up_question_repository.py
│   │   │   └── evaluation_repository.py  # Evaluation persistence (NEW)
│   │   ├── speech/              # Speech service adapters (NEW)
│   │   │   ├── azure_stt_adapter.py # Azure Speech-to-Text
│   │   │   └── azure_tts_adapter.py # Azure Text-to-Speech
│   │   ├── cv_processing/       # CV processing adapters (NEW)
│   │   │   └── cv_processing_adapter.py
│   │   └── api/                 # API layer
│   │       ├── rest/            # REST endpoints (2 files)
│   │       │   ├── health_routes.py     # Health check endpoint
│   │       │   └── interview_routes.py  # Interview CRUD endpoints
│   │       └── websocket/       # WebSocket handlers (3 files)
│   │           ├── connection_manager.py # WebSocket connection pool
│   │           ├── session_orchestrator.py # Session orchestrator (delegated to domain)
│   │           └── interview_handler.py  # Simplified WebSocket I/O handler
│   └── infrastructure/          # Cross-cutting concerns
│       ├── config/              # Configuration management
│       │   └── settings.py      # Pydantic settings
│       ├── database/            # Database infrastructure
│       │   ├── base.py          # SQLAlchemy base class
│       │   └── session.py       # Async session management
│       └── dependency_injection/
│           └── container.py     # DI container
├── alembic/                     # Database migrations
│   └── versions/                # Migration scripts
│       ├── 0001_create_tables.py
│       ├── 0002_insert_seed_data.py
│       └── 0003_create_evaluations_tables.py (NEW)
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests (150+ tests)
│   ├── integration/             # Integration tests
│   └── conftest.py              # Test fixtures
├── docs/                        # Project documentation
│   ├── project-overview-pdr.md
│   ├── codebase-summary.md     # This file
│   ├── code-standards.md
│   ├── system-architecture.md
│   └── project-roadmap.md
├── .env.example                # Environment variables template
├── pyproject.toml              # Project metadata & dependencies
├── CLAUDE.md                   # Claude Code instructions
└── README.md                   # Project overview
```

## Core Technologies

### Runtime & Language
- **Python**: 3.11+ (type hints, async/await)
- **Package Manager**: pip with pyproject.toml
- **Build System**: setuptools
- **License**: MIT

### Web Framework
- **FastAPI**: 0.104.0+ (async REST API, WebSocket, OpenAPI)
- **Uvicorn**: 0.24.0+ (ASGI server with standard extras)
- **Pydantic**: 2.5.0+ (data validation and settings)
- **Pydantic Settings**: 2.1.0+ (environment variable management)

### AI & Machine Learning
- **OpenAI**: 1.3.0+ (GPT-4 for NLP, embeddings, evaluation)
- **Anthropic**: 0.7.0+ (Claude support - planned)
- **spaCy**: 3.7.0+ (NLP text processing - planned)
- **LangChain**: 0.1.0+ (LLM workflow orchestration - planned)

### Vector Database
- **Pinecone Client**: 3.0.0+ (semantic search, embeddings storage)
- **ChromaDB**: Local vector database alternative (NEW)

### Database & ORM
- **PostgreSQL**: 14+ (Neon cloud database)
- **SQLAlchemy**: 2.0.0+ with asyncio support
- **asyncpg**: 0.29.0+ (async PostgreSQL driver)
- **Alembic**: 1.13.0+ (database migrations)

### Development Tools
- **pytest**: 7.4.0+ (testing framework)
- **pytest-asyncio**: 0.21.0+ (async test support)
- **pytest-cov**: 4.1.0+ (coverage reporting)
- **pytest-mock**: 3.12.0+ (mocking utilities)
- **ruff**: 0.1.6+ (fast Python linter)
- **black**: 23.11.0+ (code formatter)
- **mypy**: 1.7.0+ (static type checker)

## Key Components

### 1. Domain Layer (Core Business Logic)

**Location**: `src/domain/`
**Responsibility**: Pure business logic with zero external dependencies

#### Models (`src/domain/models/`)

**Interview** (`interview.py` - 150+ lines):
- **NEW**: Domain-Driven State Management (migrated from WebSocket orchestrator)
- Aggregate root controlling interview lifecycle
- States: IDLE, QUESTIONING, EVALUATING, REVIEWING, COMPLETED
- Methods: `transition_to()`, `can_transition_to()`, `validate_state_transition()`
- Business rules: State machine enforces valid transitions, tracks progress
- Progress tracking: `has_more_questions()`, `get_current_question_id()`, `get_progress_percentage()`

**Evaluation** (`evaluation.py` - NEW):
- **Context-aware evaluation entity** with parent/child separation
- Types: PARENT_QUESTION, FOLLOW_UP, COMBINED
- Fields: `parent_evaluation`, `child_evaluations`, `context_type`
- Methods: `add_child_evaluation()`, `get_combined_score()`, `has_children()`

**Answer** (`answer.py`):
- Entity containing candidate responses
- Includes evaluation results (scores, feedback)
- Methods: `evaluate()`, `is_evaluated()`, `get_score()`, `has_gaps()`, `is_adaptive_complete()`
- Support for both text and voice answers

**Question** (`question.py` - 84 lines):
- Value object representing interview questions
- Types: TECHNICAL, BEHAVIORAL, SITUATIONAL
- Difficulty: EASY, MEDIUM, HARD
- Methods: `has_skill()`, `has_tag()`, `is_suitable_for_difficulty()`, `has_ideal_answer()`
- Supports semantic search via embeddings

**CVAnalysis** (`cv_analysis.py` - 118 lines):
- Entity storing structured CV analysis
- Contains: ExtractedSkill list, experience, education, embeddings
- Methods: `get_technical_skills()`, `has_skill()`, `get_top_skills()`, `is_experienced()`

**Candidate** (`candidate.py` - 41 lines):
- Rich domain model for interview candidates
- Methods: `update_cv()`, `has_cv()`
- Fields: id, name, email, cv_file_path, timestamps

**FollowUpQuestion** (`follow_up_question.py`):
- Entity for adaptive follow-up questions
- Fields: `parent_question_id`, `order`, `context`
- Methods: `is_first_follow_up()`, `is_second_follow_up()`, `is_third_follow_up()`

### 2. Application Layer (Use Cases)

**Location**: `src/application/`
**Responsibility**: Orchestrate domain objects to accomplish business flows

#### DTOs (`application/dto/`)

**PlanningStatusResponse** (`interview_dto.py`):
- Response for interview planning endpoints
- **Field Added (2025-11-15)**: `ws_url` - WebSocket URL for real-time session
- Client receives ws_url immediately after planning completes
- Enables seamless transition to WebSocket interview without URL construction
- Fields: interview_id, status, planned_question_count, plan_metadata, message, ws_url

#### Use Cases (`application/use_cases/`)

**CombineEvaluationUseCase** (`combine_evaluation.py` - NEW):
```python
Workflow:
1. Fetch parent evaluation (main question answer)
2. Fetch all child evaluations (follow-up answers)
3. Calculate combined metrics:
   ├─ average_score = weighted avg of all scores
   ├─ gap_resolution = tracking gaps filled through follow-ups
   └─ overall_improvement = comparing first vs last answer
4. Create COMBINED evaluation entity
→ Returns: Evaluation with context_type=COMBINED
```

**ProcessAnswerAdaptiveUseCase** (`process_answer_adaptive.py`):
```python
Workflow:
1. Retrieve interview and question
2. Evaluate answer using LLM (context-aware)
3. Detect knowledge gaps
4. Create Answer entity with evaluation
5. Create Evaluation entity (PARENT_QUESTION or FOLLOW_UP)
6. Store answer and evaluation in repositories
7. Update interview state
→ Returns: Answer entity + has_more flag
```

**FollowUpDecisionUseCase** (`follow_up_decision.py`):
```python
Workflow:
1. Count existing follow-ups for parent question
2. Check break conditions:
   ├─ follow_up_count >= 3 → Exit
   ├─ similarity_score >= 0.8 → Exit
   └─ no gaps detected → Exit
3. Accumulate gaps from previous follow-ups
4. Return decision dict with needs_followup flag
→ Returns: decision dict (needs_followup, reason, count, cumulative_gaps)
```

**GenerateSummaryUseCase** (`generate_summary.py` - 376 lines):
```python
Workflow:
1. Fetch all answers for interview
2. Calculate aggregate metrics:
   ├─ overall_score = 70% theoretical + 30% speaking
   ├─ theoretical_score = avg(similarity_scores)
   ├─ speaking_score = avg(voice_metrics.overall_quality)
   └─ defaults: speaking=85 if no voice answers
3. Analyze gap progression:
   ├─ Count answers with follow-ups
   ├─ Identify gaps_filled (confirmed→False after follow-up)
   ├─ Identify gaps_remaining (still confirmed=True)
   └─ Build progression dict
4. Generate LLM recommendations:
   ├─ Pass evaluations, scores, gaps to LLM
   └─ Returns: strengths, weaknesses, study_topics, technique_tips
5. Build final summary dict (9 fields)
→ Returns: dict with all metrics + LLM recommendations
```

**PlanInterviewUseCase** (`plan_interview.py` - 381 lines):
```python
Workflow:
1. Load CV analysis
2. Calculate n (2-5) based on skill diversity
3. Create Interview entity (status=IDLE)
4. FOR each question:
   ├─ Build search query (skill + difficulty + experience)
   ├─ Find 3 exemplar questions (vector search with filters)
   ├─ Generate question with exemplars (LLM)
   ├─ Generate ideal answer + rationale
   ├─ Store question in DB
   └─ Store question embedding in vector DB (non-blocking)
5. Transition interview to QUESTIONING state
→ Returns: Interview entity
```

### 3. Adapters Layer (External Integrations)

**Location**: `src/adapters/`
**Responsibility**: Implement domain ports with concrete technologies

#### LLM Adapters (`adapters/llm/`)

**OpenAIAdapter** (`openai_adapter.py` - 400+ lines):
- Implements `LLMPort` interface
- Uses OpenAI GPT-4 for all LLM operations
- **NEW**: Enhanced JSON extraction from markdown responses
- Features:
  - Structured JSON output for evaluations
  - Configurable model and temperature
  - Async operations
  - Context-aware question generation
  - Multi-dimensional answer evaluation
  - JSON extraction with `extract_json_from_markdown()`

**AzureOpenAIAdapter** (`azure_openai_adapter.py` - NEW):
- Azure-hosted OpenAI GPT-4 implementation
- Same features as OpenAIAdapter
- Region-specific deployment configuration

#### Vector Database Adapters (`adapters/vector_db/`)

**PineconeAdapter** (`pinecone_adapter.py`):
- Implements `VectorSearchPort` interface
- Serverless Pinecone with 1536 dimensions (OpenAI embeddings)
- Features: Auto-creates index, cosine similarity search, metadata filtering

**ChromaAdapter** (`chroma_adapter.py` - NEW):
- Local vector database implementation
- In-memory or persistent storage
- Good for development and testing

#### Persistence Adapters (`adapters/persistence/`)

**NEW: Evaluation Repository** (`evaluation_repository.py`):
- Stores context-aware evaluations
- Supports parent-child relationships
- Queries: `get_by_parent_question()`, `get_by_type()`, `get_combined()`

**Database Models** (`models.py`):
- SQLAlchemy 2.0 async models
- **NEW**: EvaluationModel with parent_id, context_type, evaluation_data
- Tables: CandidateModel, InterviewModel, QuestionModel, AnswerModel, CVAnalysisModel, FollowUpQuestionModel, EvaluationModel
- Features: UUID PKs, timestamps, foreign keys, indexes, JSONB columns

**Mappers** (`mappers.py`):
- Bidirectional conversion: Domain models ↔ Database models
- **NEW**: EvaluationMapper with parent-child serialization
- Classes: CandidateMapper, InterviewMapper, QuestionMapper, AnswerMapper, CVAnalysisMapper, FollowUpQuestionMapper, EvaluationMapper

#### Speech Adapters (`adapters/speech/` - NEW)

**AzureSTTAdapter** (`azure_stt_adapter.py`):
- Azure Speech-to-Text implementation
- Supports streaming recognition
- Language detection

**AzureTTSAdapter** (`azure_tts_adapter.py`):
- Azure Text-to-Speech implementation
- Multiple voice options
- SSML support for prosody control

#### CV Processing Adapters (`adapters/cv_processing/` - NEW)

**CVProcessingAdapter** (`cv_processing_adapter.py`):
- PDF and DOCX parsing
- Skill extraction using NLP
- Education and experience analysis

### 4. Infrastructure Layer (Cross-Cutting Concerns)

**Location**: `src/infrastructure/`
**Responsibility**: Application bootstrap, configuration, utilities

#### Configuration (`infrastructure/config/`)

**Settings** (`settings.py` - 150+ lines):
- Pydantic Settings for type-safe configuration
- **NEW**: Azure Speech service configuration
- **NEW**: ChromaDB configuration
- Configuration groups: Application, API, LLM Provider, Vector DB, PostgreSQL, Speech Services, File Storage, Interview, Logging
- Special features: `async_database_url` property, environment detection methods

#### Database (`infrastructure/database/`)

**Session Management** (`session.py` - 129 lines):
- Async SQLAlchemy 2.0 session factory
- Features: Global engine, session factory, connection pooling, automatic rollback
- Functions: `create_engine()`, `init_db()`, `close_db()`, `get_async_session()`, `get_engine()`

#### Dependency Injection (`infrastructure/dependency_injection/`)

**Container** (`container.py` - 300+ lines):
- Central DI container for all dependencies
- **NEW**: Evaluation repository injection
- **NEW**: Speech service adapters injection
- Configuration-driven implementation selection
- Methods: `llm_port()`, `vector_search_port()`, repository methods, speech service methods

## Entry Points

### For Users
- **README.md**: Project overview and quick start
- **docs/project-overview-pdr.md**: Product requirements and roadmap

### For Developers
- **pyproject.toml**: Dependencies, scripts, tool configuration
- **CLAUDE.md**: Development instructions and architecture overview
- **src/main.py**: Application entry point (FastAPI app)

### For Testing
- **tests/**: Test suites (150+ tests)
- **pytest.ini**: Test configuration
- **tests/conftest.py**: Shared test fixtures

## Development Workflow

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/elios/elios-ai-service.git
cd EliosAIService

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env.local
# Edit .env.local with API keys

# 5. Run migrations
alembic upgrade head

# 6. Start development server
python src/main.py
```

### Testing Strategy

**Unit Tests** (`tests/unit/`):
- Test domain logic in isolation
- Mock all ports
- Fast execution (milliseconds)
- 150+ tests, 85%+ coverage

**Integration Tests** (`tests/integration/`):
- Test adapters with real services
- Use test environments for external APIs
- Verify port implementations

## Development Principles

### Clean Architecture

**Dependency Rule**: Dependencies point inward
- Domain → No dependencies
- Application → Domain only
- Adapters → Domain + Application
- Infrastructure → All layers

**Port-Adapter Pattern**:
- All external dependencies behind abstract interfaces
- Easy to swap implementations
- Domain logic remains pure

### Domain-Driven State Management

**NEW**: State management moved from WebSocket orchestrator to domain layer
- Interview aggregate root owns state transitions
- State machine validates transitions: IDLE → QUESTIONING → EVALUATING → REVIEWING → COMPLETED
- Business rules enforced at domain level
- WebSocket orchestrator delegates state management to domain

### Code Standards

**Python Style**:
- PEP 8 compliance
- Type hints throughout
- Docstrings for all public APIs
- Line length: 100 characters

**Architecture**:
- Rich domain models (not anemic)
- Async-first design
- Repository pattern for data access
- Dependency injection for flexibility

## Implementation Status

### ✅ Complete (v0.2.1 Current)

**Phase 1 Foundation**:
- Domain models (8 entities including Evaluation)
- Repository ports (13 interfaces)
- PostgreSQL persistence (10 repositories)
- OpenAI + Azure OpenAI LLM adapters
- Pinecone + ChromaDB vector adapters
- Mock adapters (6 total)
- Database migrations (Alembic + async support)
- Configuration management
- Dependency injection container

**Phase 2 Evaluation Enhancement**:
- Context-aware evaluation with entity separation
- Parent-child evaluation relationships
- Combined evaluation use case
- Evaluation repository and persistence

**Phase 3 State Management**:
- Domain-Driven State Management
- Interview state machine in domain layer
- State transition validation
- WebSocket orchestrator delegates to domain

**Phase 4 Additional Features**:
- JSON extraction from LLM markdown responses
- Azure Speech services adapters
- CV processing adapter
- ChromaDB vector database adapter

**Use Cases**:
- AnalyzeCV, PlanInterview, GetNextQuestion
- ProcessAnswerAdaptive, CompleteInterview
- GenerateSummary, FollowUpDecision
- CombineEvaluation (NEW)

**API Layer**:
- REST API (health + interview endpoints)
- WebSocket handler (real-time interview sessions)
- DTOs (4 files: interview, answer, audio, websocket)

### 🔄 In Progress

- Speech service integration (Azure STT/TTS)
- CV processing refinement
- Advanced analytics

### ⏳ Planned (Future Phases)

- Claude and Llama LLM adapters
- Weaviate vector adapter alternative
- Authentication & authorization
- Rate limiting
- Comprehensive E2E test suites
- Docker deployment
- CI/CD pipeline

## File Statistics

**Total Python Files**: ~75 files
**Domain Layer**: 21 files (8 models + 13 ports)
**Application Layer**: 14 files (8 use cases + 4 DTOs + __init__)
**Adapters Layer**: 35 files (LLM, vector DB, 6 mocks, persistence, API, speech, CV)
**Infrastructure Layer**: 9 files (config, database, DI)
**Tests**: 150+ tests (85%+ coverage on core features)

**Lines of Code**:
- Domain: ~850 lines (+100 for Evaluation)
- Application: ~1200 lines (+150 for CombineEvaluation)
- Adapters: ~3000 lines (+300 for new adapters)
- Infrastructure: ~450 lines
- Total: ~5500 lines production code
- Tests: ~3000 lines

## Dependencies Overview

### Production Dependencies (20+ packages)
Core framework, LLM providers, vector DB, database, speech services, document processing, utilities

### Development Dependencies (9 packages)
Testing, linting, formatting, type checking, development tools

**Total Dependencies**: 30+ packages

## Performance Considerations

### Async Operations
- All I/O operations are async (database, API calls)
- Non-blocking request handling
- Concurrent interview sessions supported

### Database Optimization
- Async SQLAlchemy with asyncpg driver
- Connection pooling (configurable)
- Indexed columns for frequent queries
- Efficient ORM query patterns

### Scalability
- Stateless API design (state in domain, not WebSocket)
- Horizontal scaling ready
- Database connection pooling
- Async request handling

## Security Measures

### Implemented ✅
- Environment variables for secrets
- .env.local gitignored
- SQL injection prevention (parameterized queries)
- Input validation via Pydantic

### Planned ⏳
- JWT authentication
- Rate limiting per user
- API key rotation
- Encryption at rest
- HTTPS enforcement
- CORS configuration
- Security headers

## Deployment

### Current Setup
- Development: Local Python + PostgreSQL (Neon cloud)
- Configuration: .env.local files
- Database: Neon serverless PostgreSQL

### Planned
- Docker containerization
- Docker Compose for local development
- Kubernetes for production
- Environment-specific configurations
- CI/CD with GitHub Actions
- Monitoring and logging
- Health checks and readiness probes

## Related Documentation

- [Project Overview & PDR](./project-overview-pdr.md) - Product requirements and roadmap
- [System Architecture](./system-architecture.md) - Detailed architecture documentation
- [Code Standards](./code-standards.md) - Coding conventions and best practices
- [Project Roadmap](./project-roadmap.md) - Development timeline and milestones

## External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Clean Architecture Guide](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## Unresolved Questions

1. **Test Coverage Target**: Maintain 85%+ or push for 90%?
2. **API Versioning**: v1 in URL or headers when API stabilizes?
3. **Logging Strategy**: JSON logs in production? Which logging library?
4. **Monitoring**: Prometheus/Grafana or cloud-native solutions?
5. **Deployment Target**: AWS, GCP, Azure, or multi-cloud?
6. **State Persistence**: How to handle WebSocket disconnections with domain state?

---

**Document Status**: Living document, updated with each milestone
**Next Review**: After major architectural changes
**Maintainers**: Elios Development Team
