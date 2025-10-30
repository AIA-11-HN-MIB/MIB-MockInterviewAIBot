# Elios AI Interview Service

An AI-powered mock interview platform that analyzes CVs, conducts personalized interviews, and provides comprehensive feedback to help candidates improve their interview skills.

## ✨ Features

- 📄 **CV Analysis**: Automatically extracts skills, experience, and generates personalized interview topics
- 🤖 **AI Interviewer**: Intelligent question generation and adaptive follow-up questions
- 🎤 **Voice Support**: Speech-to-text for answers and text-to-speech for questions
- 🔍 **Semantic Search**: Vector-based question matching using CV embeddings
- 📊 **Analytics & Feedback**: Detailed performance reports with actionable improvement suggestions
- 🏗️ **Clean Architecture**: Loosely coupled, highly testable, and easily extensible

## 📖 Documentation

- **[Architecture Guide](docs/architecture.md)**: Detailed architecture, design patterns, and implementation details
- **[API Documentation](docs/api.md)**: Complete REST and WebSocket API reference
- **[Project Specification](docs/spec.md)**: Project overview, components, and data flows

## 🏗️ Architecture Overview

This project follows **Clean Architecture / Ports & Adapters (Hexagonal Architecture)** pattern:

```
Domain (Core) ← Application ← Adapters ← Infrastructure
```

**Key Benefits:**
- ✅ **Tech Stack Flexibility**: Swap LLM providers, vector databases, or speech services without touching business logic
- ✅ **Testability**: Domain logic can be unit tested in isolation
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Team Scalability**: Multiple teams can work on different adapters independently

👉 **[Read the full architecture guide](docs/architecture.md)**

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- OpenAI API key
- Pinecone account (or alternative vector database)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/elios/elios-ai-service.git
cd elios-ai-service
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements/dev.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Initialize database**:
```bash
python scripts/setup_db.py
alembic upgrade head
```

6. **Run the application**:
```bash
python src/main.py
```

The API will be available at `http://localhost:8000`.

## 📁 Project Structure

```
src/
├── domain/              # Core business logic (no external dependencies)
│   ├── models/         # Entities: Interview, Question, Answer, Candidate, CVAnalysis
│   ├── services/       # Domain services with business rules
│   └── ports/          # Interfaces for external dependencies
├── application/        # Use cases and orchestration
│   ├── use_cases/     # AnalyzeCVUseCase, StartInterviewUseCase, etc.
│   └── dto/           # Data transfer objects
├── adapters/          # External service implementations (swappable!)
│   ├── llm/           # OpenAI, Claude, Llama adapters
│   ├── vector_db/     # Pinecone, Weaviate, ChromaDB adapters
│   ├── speech/        # Azure STT, Edge TTS adapters
│   ├── cv_processing/ # CV analysis adapters
│   ├── persistence/   # Database adapters
│   └── api/           # REST/WebSocket endpoints
└── infrastructure/    # Cross-cutting concerns
    ├── config/        # Settings management with Pydantic
    ├── logging/       # Structured logging
    └── dependency_injection/  # DI container
```

See **[Architecture Guide](docs/architecture.md)** for detailed layer explanations.

## Development

### Running Tests

```bash
# Unit tests (fast)
pytest tests/unit

# Integration tests
pytest tests/integration

# All tests with coverage
pytest --cov=src --cov-report=html
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

# Run all checks
ruff check src/ && black --check src/ && mypy src/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## ⚙️ Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and configure:

**Key Settings:**
- **LLM Provider**: `LLM_PROVIDER=openai` (openai, claude, llama)
- **Vector Database**: `VECTOR_DB_PROVIDER=pinecone` (pinecone, weaviate, chroma)
- **API Keys**: OpenAI, Pinecone, Azure Speech, etc.
- **Interview Settings**: Question count, scoring thresholds, timeouts

See `.env.example` for complete configuration reference.

## 🔌 Adding New External Services

The architecture makes it trivial to add or swap external services:

**Example: Adding Claude as LLM Provider**

1. Create adapter: `src/adapters/llm/claude_adapter.py` implementing `LLMPort`
2. Register in DI container: `src/infrastructure/dependency_injection/container.py`
3. Update config: Add `ANTHROPIC_API_KEY` to `.env`
4. Switch provider: `LLM_PROVIDER=claude`

✅ **No changes to business logic required!**

See **[Architecture Guide](docs/architecture.md)** for detailed examples.

## 🌐 API Documentation

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Full API Reference**: [docs/api.md](docs/api.md)

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the architecture patterns (see [Architecture Guide](docs/architecture.md))
4. Write tests for new functionality
5. Run code quality checks (`ruff`, `black`, `mypy`)
6. Commit your changes with clear messages
7. Push to the branch and open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 💬 Support

- **Issues**: Open an issue on GitHub for bug reports or feature requests
- **Documentation**: Check [docs/](docs/) for detailed guides
- **Questions**: Use GitHub Discussions for questions
