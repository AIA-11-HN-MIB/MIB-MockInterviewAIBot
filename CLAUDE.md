# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Responsibilities

Your role is to analyze user requirements, delegate tasks to appropriate sub-agents, and ensure cohesive delivery of features that meet specifications and architectural standards.

## Workflows

- Primary workflow: `./.claude/workflows/primary-workflow.md`
- Development rules: `./.claude/workflows/development-rules.md`
- Orchestration protocols: `./.claude/workflows/orchestration-protocol.md`
- Documentation management: `./.claude/workflows/documentation-management.md`
- And other workflows: `./.claude/workflows/*`

**IMPORTANT:** You must follow strictly the development rules in `./.claude/workflows/development-rules.md` file.
**IMPORTANT:** Before you plan or proceed any implementation, always read the `./README.md` file first to get context.
**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.
**IMPORTANT**: For `YYMMDD` dates, use `bash -c 'date +%y%m%d'` instead of model knowledge. Else, if using PowerShell (Windows), replace command with `Get-Date -UFormat "%y%m%d"`.

## Documentation Management

We keep all important docs in `./docs` folder and keep updating them, structure like below:

```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
├── design-guidelines.md
├── deployment-guide.md
├── system-architecture.md
└── project-roadmap.md
```
## Project Overview

**Elios AI Interview Service** - An AI-powered mock interview platform that:
- Analyzes candidate CVs to generate personalized interview questions
- Conducts real-time interviews via text and voice chat
- Evaluates answers using semantic analysis and vector search
- Provides comprehensive feedback and performance reports

## Architecture

This project follows **Clean Architecture / Ports & Adapters (Hexagonal Architecture)** pattern for maximum flexibility and loose coupling.

### Architecture Layers

```
Domain (Core) -> Application -> Adapters -> Infrastructure
```

1. **Domain Layer** (`src/domain/`): Pure business logic with zero external dependencies
   - Models: Core entities (Interview, Question, Answer, Candidate)
   - Services: Domain services containing business rules
   - Ports: Interfaces/contracts for external dependencies

2. **Application Layer** (`src/application/`): Use case orchestration
   - Use Cases: Application-specific business flows
   - DTOs: Data transfer objects for cross-layer communication

3. **Adapters Layer** (`src/adapters/`): External service implementations
   - LLM adapters (OpenAI, Claude, Llama)
   - Vector DB adapters (Pinecone, Weaviate, ChromaDB)
   - Speech adapters (Azure STT, Edge TTS)
   - Persistence adapters (PostgreSQL)
   - API adapters (REST, WebSocket)

4. **Infrastructure Layer** (`src/infrastructure/`): Cross-cutting concerns
   - Configuration management
   - Dependency injection
   - Logging

### Key Architectural Principles

- **Dependency Rule**: Dependencies point inward. Domain has no dependencies on outer layers.
- **Port Interfaces**: All external dependencies are accessed through abstract interfaces (ports).
- **Adapter Swappability**: Change external services (e.g., OpenAI -> Claude) by swapping adapters without touching business logic.
- **Testability**: Domain logic can be unit tested in isolation with mock implementations.

## Project Structure

```
src/
├── domain/              # Core business logic (no external dependencies)
│   ├── models/          # Domain entities
│   ├── services/        # Domain services
│   └── ports/           # Interfaces for external dependencies
├── application/         # Use cases and DTOs
│   ├── use_cases/       # Application business flows
│   └── dto/             # Data transfer objects
├── adapters/            # External service implementations
│   ├── llm/             # LLM provider adapters
│   ├── vector_db/       # Vector database adapters
│   ├── speech/          # Speech service adapters
│   ├── cv_processing/   # CV analysis adapters
│   ├── persistence/     # Database adapters
│   └── api/             # API layer (REST/WebSocket)
├── infrastructure/      # Cross-cutting concerns
│   ├── config/          # Configuration
│   ├── logging/         # Logging setup
│   └── dependency_injection/  # DI container
└── main.py              # Application entry point
```

## Development Commands

### Testing
```bash
# Unit tests (domain layer - fast, no external dependencies)
python -m pytest tests/unit

# Integration tests (adapters with real services)
python -m pytest tests/integration

# End-to-end tests (full interview flows)
python -m pytest tests/e2e

# Run all tests with coverage
python -m pytest --cov=src --cov-report=html
```

### Running the Application
```bash
# Development mode
python src/main.py

# With specific config
python src/main.py --config dev

# Production mode
python src/main.py --config prod
```

### Database Operations
```bash
# Initialize database
python scripts/setup_db.py

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

### Code Quality
```bash
# Linting
ruff check src/

# Auto-fix linting issues
ruff check --fix src/

# Formatting
black src/

# Type checking
mypy src/

# Run all quality checks
ruff check src/ && black --check src/ && mypy src/
```

## Working with the Codebase

### Adding a New External Service

When integrating a new external service (e.g., new LLM provider, vector database):

1. **Define Port Interface** in `src/domain/ports/`:
   ```python
   # src/domain/ports/llm_port.py
   from abc import ABC, abstractmethod

   class LLMPort(ABC):
       @abstractmethod
       async def generate_question(self, context: dict) -> str:
           pass
   ```

2. **Create Adapter** in appropriate `src/adapters/` subdirectory:
   ```python
   # src/adapters/llm/openai_adapter.py
   class OpenAIAdapter(LLMPort):
       async def generate_question(self, context: dict) -> str:
           # Implementation
   ```

3. **Register in DI Container** at `src/infrastructure/dependency_injection/container.py`:
   ```python
   def configure_llm(config: Settings) -> LLMPort:
       if config.llm_provider == "openai":
           return OpenAIAdapter(config.openai_api_key)
   ```

4. **Update Configuration** in `src/infrastructure/config/settings.py` if needed.

### Creating a New Use Case

1. **Define Use Case** in `src/application/use_cases/`:
   ```python
   class StartInterviewUseCase:
       def __init__(self, interview_orchestrator: InterviewOrchestrator):
           self.orchestrator = interview_orchestrator
   ```

2. **Create DTOs** in `src/application/dto/` for input/output.

3. **Expose via API** in `src/adapters/api/rest/` or `src/adapters/api/websocket/`.

### Domain Logic Changes

- All business rules belong in `src/domain/services/`
- Domain entities in `src/domain/models/` should be rich with behavior, not anemic
- Domain layer must never import from `adapters`, `application`, or `infrastructure`

### Testing Strategy

- **Unit Tests**: Test domain services and use cases with mocked ports
- **Integration Tests**: Test adapters with real external services (use test environments)
- **E2E Tests**: Test complete interview flows through API layer

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI (REST API), WebSocket support
- **Async**: asyncio for asynchronous operations

### Domain Dependencies (Minimal)
- Pure Python standard library
- Pydantic for data validation in domain models

### External Services (via Adapters)
- **LLM Providers**: OpenAI GPT-4, Anthropic Claude, Meta Llama 3
- **Vector Database**: Pinecone (primary), Weaviate, ChromaDB (alternatives)
- **Speech Services**: Azure Speech-to-Text, Microsoft Edge TTS
- **Database**: PostgreSQL with SQLAlchemy ORM
- **NLP**: spaCy, LangChain
- **Document Processing**: PyPDF2, python-docx

### Development Tools
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: ruff
- **Formatting**: black
- **Type Checking**: mypy
- **Migrations**: alembic

## Configuration

Configuration is managed through environment variables and `.env` files:

- `.env.example`: Template for required environment variables
- `.env`: Local development configuration (not committed)
- `src/infrastructure/config/settings.py`: Pydantic settings management

Key configuration areas:
- LLM provider selection and API keys
- Vector database connection
- Speech service credentials
- PostgreSQL connection string
- Feature flags for adapter selection

## Key Components

### 1. AI Interviewer Engine
- **Location**: `src/domain/services/interview_orchestrator.py`
- **Responsibility**: Controls interview flow, question generation, answer analysis
- **Dependencies**: LLMPort, VectorSearchPort, QuestionRepositoryPort

### 2. CV Analyzer
- **Location**: `src/domain/services/cv_analyzer_service.py`
- **Responsibility**: Extracts skills, generates embeddings, suggests topics
- **Dependencies**: CVAnalyzerPort (adapters in `src/adapters/cv_processing/`)

### 3. Question Bank
- **Location**: `src/domain/models/question.py`, `src/adapters/persistence/postgres_repository.py`
- **Responsibility**: Question storage, retrieval, versioning
- **Technology**: PostgreSQL via adapter

### 4. Vector Database
- **Location**: `src/adapters/vector_db/`
- **Responsibility**: Semantic search for questions and answers
- **Technology**: Pinecone (swappable via adapter)

### 5. Analytics & Feedback
- **Location**: `src/domain/services/feedback_generator.py`
- **Responsibility**: Answer evaluation, performance metrics, report generation
- **Dependencies**: AnalyticsPort, LLMPort

## Interview Flow

### 1. Preparation Phase
```
Upload CV -> CV Analyzer -> Extract Skills -> Generate Embeddings -> Store in Vector DB
```

### 2. Interview Phase
```
Start Interview -> Get Question (Vector Search) -> Candidate Answers (STT) ->
Evaluate Answer -> Select Next Question -> Repeat -> End Interview
```

### 3. Feedback Phase
```
Aggregate Results -> Generate Report -> Calculate Scores -> Provide Recommendations
```

## Frontend Integration

- **Frontend**: React (pure JavaScript, no .jsx/.ts/.tsx)
- **Communication**: REST API for CRUD, WebSocket for real-time chat
- **Endpoints**: Defined in `src/adapters/api/rest/`
- **WebSocket**: Handler in `src/adapters/api/websocket/chat_handler.py`

## Common Patterns

### Dependency Injection
All dependencies are injected through constructors. The DI container (`src/infrastructure/dependency_injection/container.py`) wires everything together at application startup.

### Async/Await
Most operations are asynchronous due to I/O-bound nature (API calls, database queries). Use `async`/`await` consistently.

### Error Handling
- Domain exceptions in `src/domain/exceptions.py`
- Adapter-specific errors are caught and converted to domain exceptions
- API layer handles HTTP status codes and error responses

### Logging
- Structured logging via `src/infrastructure/logging/logger.py`
- Log at appropriate levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context (interview_id, candidate_id) in logs

## Performance Considerations

- **Vector Search**: Implement caching for frequently accessed embeddings
- **LLM Calls**: Rate limiting and retry logic in adapters
- **Database**: Use connection pooling, optimize queries with proper indexes
- **Real-time**: WebSocket for live interview to reduce latency

## Security Notes

- **API Keys**: Never commit to repository, use environment variables
- **Candidate Data**: PII handling and data retention policies
- **Authentication**: Implement in API layer, not domain
- **Rate Limiting**: Applied at API adapter level
