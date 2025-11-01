# Codebase Summary

**Last Updated**: 2025-10-31
**Version**: 0.1.0
**Repository**: https://github.com/elios/elios-ai-service

## Overview

Elios AI Interview Service is a Python-based AI-powered mock interview platform built with Clean Architecture principles (Hexagonal/Ports & Adapters pattern). The codebase emphasizes separation of concerns, testability, and flexibility through abstract interfaces and dependency injection. The platform integrates with OpenAI GPT-4 for natural language processing, Pinecone for vector-based semantic search, and PostgreSQL for persistent storage.

## Project Structure

```
EliosAIService/
├── src/                          # Source code (Clean Architecture layers)
│   ├── domain/                   # Core business logic (no external dependencies)
│   │   ├── models/              # Domain entities (5 files)
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py     # Candidate entity
│   │   │   ├── interview.py     # Interview aggregate root
│   │   │   ├── question.py      # Question value object
│   │   │   ├── answer.py        # Answer entity with evaluation
│   │   │   └── cv_analysis.py   # CV analysis entity
│   │   └── ports/               # Abstract interfaces (11 files)
│   │       ├── __init__.py
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
│   │       └── cv_analysis_repository_port.py   # CV analysis persistence
│   ├── application/             # Use cases and orchestration
│   │   ├── __init__.py
│   │   └── use_cases/           # Application business flows (2 files)
│   │       ├── __init__.py
│   │       ├── analyze_cv.py    # CV analysis workflow
│   │       └── start_interview.py # Interview initialization workflow
│   ├── adapters/                # External service implementations
│   │   ├── __init__.py
│   │   ├── llm/                 # LLM provider adapters
│   │   │   ├── __init__.py
│   │   │   └── openai_adapter.py # OpenAI GPT-4 implementation ✅
│   │   ├── vector_db/           # Vector database adapters
│   │   │   ├── __init__.py
│   │   │   └── pinecone_adapter.py # Pinecone implementation ✅
│   │   ├── persistence/         # Database adapters (7 files)
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   ├── mappers.py       # Domain ↔ DB model conversion
│   │   │   ├── candidate_repository.py      ✅
│   │   │   ├── question_repository.py       ✅
│   │   │   ├── interview_repository.py      ✅
│   │   │   ├── answer_repository.py         ✅
│   │   │   └── cv_analysis_repository.py    ✅
│   │   └── api/                 # API layer
│   │       ├── __init__.py
│   │       └── rest/            # REST endpoints
│   │           ├── __init__.py
│   │           └── health_routes.py # Health check endpoint ✅
│   └── infrastructure/          # Cross-cutting concerns
│       ├── __init__.py
│       ├── config/              # Configuration management
│       │   ├── __init__.py
│       │   └── settings.py      # Pydantic settings ✅
│       ├── database/            # Database infrastructure
│       │   ├── __init__.py
│       │   ├── base.py          # SQLAlchemy base class
│       │   └── session.py       # Async session management ✅
│       └── dependency_injection/
│           ├── __init__.py
│           └── container.py     # DI container ✅
├── alembic/                     # Database migrations
│   ├── versions/                # Migration scripts
│   │   └── a4047ce5a909_initial_database_schema_with_all_tables.py ✅
│   ├── env.py                   # Alembic environment config
│   └── script.py.mako          # Migration template
├── scripts/                     # Utility scripts
│   ├── setup_db.py             # Database initialization ✅
│   ├── verify_db.py            # Database verification ✅
│   ├── test_env.py             # Environment testing ✅
│   ├── setup_and_migrate.sh    # Unix migration script ✅
│   └── setup_and_migrate.bat   # Windows migration script ✅
├── docs/                        # Project documentation
│   ├── project-overview-pdr.md # Product requirements ✅
│   ├── codebase-summary.md     # This file ✅
│   ├── code-standards.md       # Coding standards 🔄
│   ├── system-architecture.md  # Architecture details 🔄
│   ├── api.md                  # API reference (template)
│   ├── spec.md                 # Project specification (template)
│   ├── architecture.md         # Architecture guide (template)
│   └── RELEASE.md             # Release notes
├── tests/                       # Test suites (planned)
│   ├── unit/                   # Unit tests ⏳
│   ├── integration/            # Integration tests ⏳
│   └── e2e/                    # End-to-end tests ⏳
├── .env.example                # Environment variables template ✅
├── .env.local                  # Local config (gitignored) ✅
├── .gitignore                  # Git exclusions ✅
├── alembic.ini                 # Alembic configuration ✅
├── pyproject.toml              # Project metadata & dependencies ✅
├── CLAUDE.md                   # Claude Code instructions ✅
├── README.md                   # Project overview ✅
├── DATABASE_SETUP.md           # Database setup guide ✅
├── ENV_SETUP.md                # Environment setup guide ✅
└── CHANGELOG_ENV.md            # Environment config changelog ✅
```

## Core Technologies

### Runtime & Language
- **Python**: 3.11+ (type hints, async/await, modern syntax)
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

### Database & ORM
- **PostgreSQL**: 14+ (Neon cloud database)
- **SQLAlchemy**: 2.0.0+ with asyncio support
- **asyncpg**: 0.29.0+ (async PostgreSQL driver)
- **Alembic**: 1.13.0+ (database migrations)

### Document Processing
- **PyPDF2**: 3.0.0+ (PDF parsing - planned)
- **python-docx**: 1.1.0+ (DOCX parsing - planned)

### Utilities
- **python-multipart**: 0.0.6+ (file upload support)
- **python-jose**: 3.3.0+ with cryptography (JWT tokens - planned)
- **passlib**: 1.7.4+ with bcrypt (password hashing - planned)
- **httpx**: 0.25.0+ (async HTTP client)
- **python-dotenv**: 1.0.0+ (development environment loading)

### Development Tools
- **pytest**: 7.4.0+ (testing framework)
- **pytest-asyncio**: 0.21.0+ (async test support)
- **pytest-cov**: 4.1.0+ (coverage reporting)
- **pytest-mock**: 3.12.0+ (mocking utilities)
- **ruff**: 0.1.6+ (fast Python linter)
- **black**: 23.11.0+ (code formatter)
- **mypy**: 1.7.0+ (static type checker)
- **ipython**: 8.18.0+ (enhanced REPL)

## Key Components

### 1. Domain Layer (Core Business Logic)

**Location**: `src/domain/`
**Responsibility**: Pure business logic with zero external dependencies

#### Models (`src/domain/models/`)

**Candidate** (`candidate.py` - 41 lines):
- Rich domain model for interview candidates
- Methods: `update_cv()`, `has_cv()`
- Fields: id, name, email, cv_file_path, timestamps

**Interview** (`interview.py` - 137 lines):
- Aggregate root controlling interview lifecycle
- States: PREPARING, READY, IN_PROGRESS, COMPLETED, CANCELLED
- Methods: `start()`, `complete()`, `cancel()`, `mark_ready()`, `add_question()`, `add_answer()`
- Business rules: Can't start without CV analysis, tracks progress, manages Q&A flow
- Progress tracking: `has_more_questions()`, `get_current_question_id()`, `get_progress_percentage()`

**Question** (`question.py` - 84 lines):
- Value object representing interview questions
- Types: TECHNICAL, BEHAVIORAL, SITUATIONAL
- Difficulty: EASY, MEDIUM, HARD
- Methods: `has_skill()`, `has_tag()`, `is_suitable_for_difficulty()`
- Supports semantic search via embeddings

**Answer** (`answer.py`):
- Entity containing candidate responses
- Includes evaluation results (scores, feedback)
- Methods: `evaluate()`, `is_evaluated()`, `get_score()`
- Support for both text and voice answers

**CVAnalysis** (`cv_analysis.py` - 118 lines):
- Entity storing structured CV analysis
- Contains: ExtractedSkill list, experience, education, embeddings
- Methods: `get_technical_skills()`, `has_skill()`, `get_top_skills()`, `is_experienced()`
- Suggested topics and difficulty levels

#### Ports (`src/domain/ports/`)

**LLMPort** - Large Language Model interface:
- `generate_question()`: Create interview questions
- `evaluate_answer()`: Assess response quality
- `generate_feedback_report()`: Create comprehensive feedback
- `summarize_cv()`: Summarize CV content
- `extract_skills_from_text()`: Extract skills using NLP

**VectorSearchPort** - Vector database interface:
- `store_question_embedding()`: Store question vectors
- `store_cv_embedding()`: Store CV vectors
- `find_similar_questions()`: Semantic search
- `find_similar_answers()`: Answer similarity
- `get_embedding()`: Generate text embeddings

**Repository Ports** (5 interfaces):
- `QuestionRepositoryPort`: Question CRUD operations
- `CandidateRepositoryPort`: Candidate persistence
- `InterviewRepositoryPort`: Interview management
- `AnswerRepositoryPort`: Answer storage
- `CVAnalysisRepositoryPort`: CV analysis persistence

**Other Ports**:
- `CVAnalyzerPort`: CV text extraction and analysis
- `SpeechToTextPort`: Audio transcription
- `TextToSpeechPort`: Speech synthesis
- `AnalyticsPort`: Performance metrics and reporting

### 2. Application Layer (Use Cases)

**Location**: `src/application/`
**Responsibility**: Orchestrate domain objects and coordinate workflows

#### Use Cases (`src/application/use_cases/`)

**AnalyzeCVUseCase** (`analyze_cv.py` - 83 lines):
```python
Workflow:
1. Extract text from CV file (CVAnalyzerPort)
2. Analyze and extract structured info
3. Generate CV embeddings (VectorSearchPort)
4. Store embeddings in vector database
→ Returns: CVAnalysis entity
```

**StartInterviewUseCase** (`start_interview.py`):
```python
Workflow:
1. Validate CV analysis exists
2. Find suitable questions via semantic search
3. Create Interview entity with selected questions
4. Mark interview as READY
→ Returns: Interview entity
```

**Planned Use Cases**:
- `GetNextQuestionUseCase`: Retrieve next question
- `ProcessAnswerUseCase`: Handle answer and evaluation
- `CompleteInterviewUseCase`: Finalize and generate report
- `GenerateFeedbackUseCase`: Create comprehensive feedback

### 3. Adapters Layer (External Integrations)

**Location**: `src/adapters/`
**Responsibility**: Implement domain ports with concrete technologies

#### LLM Adapters (`src/adapters/llm/`)

**OpenAIAdapter** (`openai_adapter.py` - 269 lines) ✅:
- Implements `LLMPort` interface
- Uses OpenAI GPT-4 for all LLM operations
- Features:
  - Structured JSON output for evaluations
  - Configurable model and temperature
  - Async operations
  - Context-aware question generation
  - Multi-dimensional answer evaluation
- Methods fully implemented:
  - `generate_question()`: Context-aware question generation
  - `evaluate_answer()`: Returns AnswerEvaluation with scores
  - `generate_feedback_report()`: Comprehensive interview feedback
  - `summarize_cv()`: 3-4 sentence CV summary
  - `extract_skills_from_text()`: Structured skill extraction

**Planned Adapters**:
- `ClaudeAdapter`: Anthropic Claude implementation
- `LlamaAdapter`: Meta Llama 3 implementation

#### Vector Database Adapters (`src/adapters/vector_db/`)

**PineconeAdapter** (`pinecone_adapter.py`) ✅:
- Implements `VectorSearchPort` interface
- Serverless Pinecone with 1536 dimensions (OpenAI embeddings)
- Features:
  - Auto-creates index if missing
  - Cosine similarity search
  - Metadata filtering
  - Batch operations support
- Methods: Question/CV embedding storage, similarity search

**Planned Adapters**:
- `WeaviateAdapter`: Weaviate implementation
- `ChromaAdapter`: ChromaDB for local development

#### Persistence Adapters (`src/adapters/persistence/`)

**Database Models** (`models.py`) ✅:
- SQLAlchemy 2.0 async models
- Tables: CandidateModel, InterviewModel, QuestionModel, AnswerModel, CVAnalysisModel
- Features:
  - UUID primary keys
  - Timestamps (created_at, updated_at)
  - Foreign key relationships
  - Indexes on frequently queried columns
  - JSONB columns for flexible metadata
  - PostgreSQL-specific types (UUID, ARRAY, JSONB)
  - GIN indexes on array columns

**Mappers** (`mappers.py`) ✅:
- Bidirectional conversion: Domain models ↔ Database models
- Classes: CandidateMapper, InterviewMapper, QuestionMapper, AnswerMapper, CVAnalysisMapper
- Methods: `to_domain()`, `to_db_model()`

**Repositories** (5 files) ✅:
- `PostgreSQLCandidateRepository`: Candidate CRUD
- `PostgreSQLQuestionRepository`: Question management with filtering
- `PostgreSQLInterviewRepository`: Interview lifecycle with status queries
- `PostgreSQLAnswerRepository`: Answer storage and retrieval
- `PostgreSQLCVAnalysisRepository`: CV analysis persistence

Each repository:
- Implements corresponding port interface
- Uses async SQLAlchemy sessions
- Handles mapping between layers
- Provides CRUD operations + domain-specific queries

#### API Adapters (`src/adapters/api/`)

**REST API** (`api/rest/`) 🔄:
- `health_routes.py`: Health check endpoint ✅
- Planned: CV upload, interview management, question CRUD, feedback endpoints

**WebSocket** (planned) ⏳:
- Real-time interview chat handler
- Bi-directional communication
- Session management

### 4. Infrastructure Layer (Cross-Cutting Concerns)

**Location**: `src/infrastructure/`
**Responsibility**: Application bootstrap, configuration, utilities

#### Configuration (`infrastructure/config/`)

**Settings** (`settings.py` - 124 lines) ✅:
- Pydantic Settings for type-safe configuration
- Environment variable loading (.env.local → .env)
- Configuration groups:
  - Application (name, version, environment)
  - API (host, port, CORS, prefix)
  - LLM Provider (OpenAI, Claude configs)
  - Vector DB (Pinecone, Weaviate, ChromaDB)
  - PostgreSQL (connection, credentials)
  - Speech Services (Azure STT, region)
  - File Storage (upload directories)
  - Interview (question count, scoring, timeouts)
  - Logging (level, format)
- Special features:
  - `async_database_url` property: Converts postgresql:// to postgresql+asyncpg://
  - Strips SSL parameters incompatible with asyncpg
  - Environment detection methods: `is_production()`, `is_development()`

#### Database (`infrastructure/database/`)

**Session Management** (`session.py` - 129 lines) ✅:
- Async SQLAlchemy 2.0 session factory
- Features:
  - Global engine and session factory
  - Connection pooling (configurable by environment)
  - Pool pre-ping for connection verification
  - Automatic rollback on errors
  - Proper cleanup with `async with` context
- Functions:
  - `create_engine()`: Configure async engine
  - `init_db()`: Initialize on startup
  - `close_db()`: Cleanup on shutdown
  - `get_async_session()`: Dependency injection function
  - `get_engine()`: Access engine instance

**Base** (`base.py`) ✅:
- SQLAlchemy DeclarativeBase for all models

#### Dependency Injection (`infrastructure/dependency_injection/`)

**Container** (`container.py` - 259 lines) ✅:
- Central DI container for all dependencies
- Configuration-driven implementation selection
- Methods:
  - `llm_port()`: Returns OpenAI (or Claude/Llama based on config)
  - `vector_search_port()`: Returns Pinecone (or Weaviate/ChromaDB)
  - Repository methods (5): Return PostgreSQL repositories
  - `cv_analyzer_port()`: CV processing (not implemented yet)
  - `speech_to_text_port()`: STT service (not implemented yet)
  - `text_to_speech_port()`: TTS service (not implemented yet)
  - `analytics_port()`: Analytics service (not implemented yet)
- Singleton pattern with `@lru_cache` for get_container()

### 5. Database Migrations

**Location**: `alembic/`
**Tool**: Alembic with async support

**Migrations**:
- `a4047ce5a909_initial_database_schema_with_all_tables.py` ✅
  - Creates 5 tables: candidates, interviews, questions, answers, cv_analyses
  - Establishes foreign key relationships
  - Adds indexes for performance
  - Includes proper constraints

**Configuration**:
- `alembic.ini`: Alembic settings
- `env.py`: Async-compatible environment configuration
- Uses `asyncio.run()` for async migrations

### 6. Utility Scripts

**Location**: `scripts/`

**Database Scripts** ✅:
- `setup_db.py`: Initialize database with verification
- `verify_db.py`: Check tables and count rows
- `test_env.py`: Test environment configuration loading
- `setup_and_migrate.sh`: Unix automated setup
- `setup_and_migrate.bat`: Windows automated setup (cloud PostgreSQL compatible)

## Entry Points

### For Users
- **README.md**: Project overview and quick start
- **DATABASE_SETUP.md**: Comprehensive database setup guide
- **ENV_SETUP.md**: Environment configuration best practices
- **docs/project-overview-pdr.md**: Product requirements and roadmap

### For Developers
- **pyproject.toml**: Dependencies, scripts, and tool configuration
- **CLAUDE.md**: Development instructions and architecture overview
- **alembic.ini**: Database migration configuration
- **.env.example**: Template for required environment variables
- **src/main.py**: Application entry point (FastAPI app)

### For Testing
- **tests/**: Test suites (planned structure)
- **pytest.ini**: Test configuration in pyproject.toml
- **Coverage config**: htmlcov/ output directory

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

# 6. Verify database
python scripts/verify_db.py

# 7. Start development server
python src/main.py
```

### Testing Strategy

**Unit Tests** (`tests/unit/`) ⏳:
- Test domain logic in isolation
- Mock all ports
- Fast execution (milliseconds)
- Target coverage: >80%

**Integration Tests** (`tests/integration/`) ⏳:
- Test adapters with real services
- Use test environments for external APIs
- Verify port implementations
- Slower execution (seconds)

**E2E Tests** (`tests/e2e/`) ⏳:
- Test complete user flows
- Use test database
- Verify API endpoints
- Full system integration

### Code Quality Tools

**Linting** (ruff):
```bash
ruff check src/
ruff check --fix src/  # Auto-fix issues
```

**Formatting** (black):
```bash
black src/
black --check src/  # Check without modifying
```

**Type Checking** (mypy):
```bash
mypy src/
```

**All Quality Checks**:
```bash
ruff check src/ && black --check src/ && mypy src/
```

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

### Code Standards

**Python Style**:
- PEP 8 compliance
- Type hints throughout
- Docstrings for all public APIs
- Line length: 100 characters (black/ruff)

**Architecture**:
- Rich domain models (not anemic)
- Async-first design
- Repository pattern for data access
- Dependency injection for flexibility

**Testing**:
- Unit tests for domain logic
- Integration tests for adapters
- E2E tests for API flows
- High coverage (>80% target)

## Implementation Status

### ✅ Complete (v0.1.0 Foundation)
- Domain models (5 entities)
- Repository ports (5 interfaces)
- PostgreSQL persistence (5 repositories + models + mappers)
- OpenAI LLM adapter (full implementation)
- Pinecone vector adapter (full implementation)
- Database migrations (Alembic + async support)
- Configuration management (Pydantic Settings)
- Dependency injection container
- Use cases (AnalyzeCV, StartInterview)
- Database setup scripts
- Health check API endpoint

### 🔄 In Progress
- Complete REST API implementation
- WebSocket chat handler
- CV processing adapters
- Analytics service

### ⏳ Planned (Future Phases)
- Claude and Llama LLM adapters
- Weaviate and ChromaDB vector adapters
- Speech service adapters (Azure STT, Edge TTS)
- Additional use cases (ProcessAnswer, CompleteInterview, GenerateFeedback)
- Authentication & authorization
- Rate limiting
- Comprehensive test suites
- API documentation (OpenAPI/Swagger)
- Docker deployment
- CI/CD pipeline

## File Statistics

**Total Python Files**: ~40 files
**Domain Layer**: 16 files (models + ports)
**Application Layer**: 3 files (use cases)
**Adapters Layer**: 15 files (implementations)
**Infrastructure Layer**: 9 files (config, database, DI)
**Tests**: 0 files (pending)

**Lines of Code** (estimated):
- Domain: ~600 lines
- Application: ~150 lines
- Adapters: ~1200 lines
- Infrastructure: ~400 lines
- Total: ~2350 lines (excluding tests)

## Dependencies Overview

### Production Dependencies (16 packages)
Core framework, LLM providers, vector DB, database, document processing, utilities

### Development Dependencies (9 packages)
Testing, linting, formatting, type checking, development tools

**Total Dependencies**: 25 packages

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

### Caching Strategy (Planned)
- Frequent question embedding caching
- LLM response caching for similar prompts
- Vector search result caching

### Scalability
- Stateless API design
- Horizontal scaling ready
- Database connection pooling
- Async request handling

## Security Measures

### Implemented ✅
- Environment variable for secrets
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
- [API Documentation](./system-architecture.md#api-architecture) - REST API reference
- [Database Setup](../DATABASE_SETUP.md) - Database configuration guide

## External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Clean Architecture Guide](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## Unresolved Questions

1. **Test Coverage Target**: Aim for 80% or 90%?
2. **API Versioning**: v1 in URL or headers?
3. **Logging Strategy**: JSON logs in production? Which logging library?
4. **Monitoring**: Prometheus/Grafana or cloud-native solutions?
5. **Deployment Target**: AWS, GCP, Azure, or multi-cloud?

---

**Document Status**: Living document, updated with each milestone
**Next Review**: After Phase 1 completion
**Maintainers**: Elios Development Team
