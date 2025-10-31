# Elios AI Interview Service

**An AI-powered mock interview platform that helps candidates prepare for technical interviews through personalized CV analysis, adaptive question generation, and real-time answer evaluation.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📖 Overview

Elios AI Interview Service leverages **Large Language Models (LLMs)** and **vector databases** to deliver intelligent, personalized mock interview experiences. The platform analyzes candidate CVs, generates relevant questions, evaluates answers in real-time, and provides comprehensive feedback to help candidates improve their interview performance.

### Key Features

- **🎯 CV Analysis**: Extract skills, experience, and education from resumes
- **🤖 Adaptive Questions**: Generate personalized interview questions based on candidate background
- **📊 Real-Time Evaluation**: Multi-dimensional answer assessment with instant feedback
- **💬 Voice & Text Support**: Conduct interviews via text chat or voice (planned)
- **📈 Comprehensive Reports**: Detailed performance analysis with actionable recommendations
- **🔄 Swappable AI Providers**: Easy integration of OpenAI, Claude, or Llama

### Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Database**: PostgreSQL (Neon), SQLAlchemy 2.0 (async)
- **AI/ML**: OpenAI GPT-4, Pinecone Vector Database
- **Architecture**: Clean Architecture (Hexagonal/Ports & Adapters)
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: ruff, black, mypy

---

## 🏗️ Architecture

This project follows **Clean Architecture** principles for maximum flexibility, testability, and maintainability:

```
┌─────────────────────────────────────┐
│      Domain Layer (Core)            │  ← Pure business logic
│  Models, Services, Ports            │     Zero external dependencies
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│    Application Layer                │  ← Use case orchestration
│  Use Cases, DTOs                    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│    Adapters Layer                   │  ← External integrations
│  LLM, VectorDB, API, Database       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│    Infrastructure Layer             │  ← Config, DI, Database setup
│  Settings, Container, Migrations    │
└─────────────────────────────────────┘
```

**Benefits**:
- ✅ Swap LLM providers without touching business logic
- ✅ Test domain logic in complete isolation
- ✅ Easy to understand and maintain
- ✅ Technology-independent core

📚 **[Read Full Architecture Documentation →](docs/system-architecture.md)**

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL database (or Neon account)
- OpenAI API key
- Pinecone API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/elios/elios-ai-service.git
   cd EliosAIService
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local` with your credentials:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@host:5432/elios_interviews

   # LLM Provider
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-api-key-here
   OPENAI_MODEL=gpt-4

   # Vector Database
   VECTOR_DB_PROVIDER=pinecone
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_INDEX_NAME=elios-questions
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Verify database setup**
   ```bash
   python scripts/verify_db.py
   ```

7. **Start the server**
   ```bash
   python src/main.py
   ```

   Server runs at: http://localhost:8000

   API Documentation: http://localhost:8000/docs

---

## 📖 Documentation

### For Users
- **[Project Overview & PDR](docs/project-overview-pdr.md)** - Product requirements, features, and roadmap
- **[Database Setup Guide](DATABASE_SETUP.md)** - Comprehensive database configuration
- **[Environment Setup Guide](ENV_SETUP.md)** - Environment configuration best practices

### For Developers
- **[System Architecture](docs/system-architecture.md)** - Detailed architecture documentation
- **[Codebase Summary](docs/codebase-summary.md)** - Project structure and tech stack
- **[Code Standards](docs/code-standards.md)** - Coding conventions and best practices
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines for AI assistants

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/         # Unit tests only
pytest tests/integration/  # Integration tests only
pytest tests/e2e/          # End-to-end tests only
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/
ruff check --fix src/  # Auto-fix issues

# Type checking
mypy src/

# Run all checks
black src/ && ruff check src/ && mypy src/
```

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Verify database
python scripts/verify_db.py
```

---

## 🎯 Usage Example

### 1. Create a Candidate

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/candidates",
        json={
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
    )
    candidate = response.json()
    print(f"Created candidate: {candidate['id']}")
```

### 2. Upload and Analyze CV

```python
async with httpx.AsyncClient() as client:
    with open("resume.pdf", "rb") as cv_file:
        response = await client.post(
            "http://localhost:8000/api/v1/cv/upload",
            files={"file": cv_file},
            data={"candidate_id": candidate['id']}
        )
    cv_analysis = response.json()
    print(f"Skills found: {cv_analysis['skills']}")
```

### 3. Start Interview

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/interviews",
        json={
            "candidate_id": candidate['id'],
            "cv_analysis_id": cv_analysis['id']
        }
    )
    interview = response.json()
    print(f"Interview ready with {len(interview['question_ids'])} questions")
```

### 4. Submit Answer

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"http://localhost:8000/api/v1/interviews/{interview['id']}/answers",
        json={
            "question_id": interview['question_ids'][0],
            "answer_text": "My answer here..."
        }
    )
    evaluation = response.json()
    print(f"Score: {evaluation['score']}/100")
    print(f"Feedback: {evaluation['feedback']}")
```

---

## 📦 Project Structure

```
EliosAIService/
├── src/
│   ├── domain/              # Core business logic (5 models, 11 ports)
│   │   ├── models/          # Candidate, Interview, Question, Answer, CVAnalysis
│   │   └── ports/           # Abstract interfaces for external dependencies
│   ├── application/         # Use cases and orchestration
│   │   └── use_cases/       # AnalyzeCV, StartInterview, etc.
│   ├── adapters/            # External service implementations
│   │   ├── llm/             # OpenAI, Claude (planned), Llama (planned)
│   │   ├── vector_db/       # Pinecone, Weaviate (planned)
│   │   ├── persistence/     # PostgreSQL repositories (5 total)
│   │   └── api/             # REST endpoints, WebSocket (planned)
│   └── infrastructure/      # Config, DI, database setup
│       ├── config/          # Pydantic Settings
│       ├── database/        # Async SQLAlchemy session management
│       └── dependency_injection/ # DI container
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts (setup, verify, test)
├── tests/                   # Test suites (unit, integration, e2e)
├── docs/                    # Project documentation
└── pyproject.toml          # Dependencies and tool configuration
```

---

## 🔧 Configuration

Configuration is managed through environment variables with the following priority:

1. `.env.local` (highest priority, gitignored)
2. `.env` (can be committed, template)
3. System environment variables
4. Pydantic defaults

### Key Configuration Sections

- **Application**: Name, version, environment
- **LLM Provider**: OpenAI, Claude, or Llama configuration
- **Vector Database**: Pinecone, Weaviate, or ChromaDB settings
- **PostgreSQL**: Database connection and credentials
- **Speech Services**: Azure STT, Edge TTS (planned)
- **Interview Settings**: Question count, scoring, timeouts

See [ENV_SETUP.md](ENV_SETUP.md) for detailed configuration guide.

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines (coming soon).

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our [Code Standards](docs/code-standards.md)
4. Run tests and quality checks
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Commit Message Format

```
<type>(<scope>): <subject>

Examples:
feat(domain): add Interview aggregate with state management
fix(persistence): handle NULL metadata in answer mapper
docs: update API documentation for CV upload endpoint
```

---

## 🗺️ Roadmap

### Phase 1: Foundation (Current - v0.1.0)
- ✅ Domain models and ports
- ✅ PostgreSQL persistence layer
- ✅ OpenAI LLM adapter
- ✅ Pinecone vector adapter
- ✅ Database migrations
- 🔄 REST API implementation
- 🔄 CV processing adapters

### Phase 2: Core Features (v0.2.0 - v0.5.0)
- ⏳ Voice interview support
- ⏳ Advanced question generation
- ⏳ Interview analytics
- ⏳ Performance benchmarks
- ⏳ Frontend integration

### Phase 3: Intelligence Enhancement (v0.6.0 - v0.8.0)
- ⏳ Multi-LLM support (Claude, Llama)
- ⏳ Behavioral question analysis
- ⏳ Personality insights
- ⏳ Skill gap analysis

### Phase 4: Scale & Polish (v0.9.0 - v1.0.0)
- ⏳ Multi-language support
- ⏳ Team/organization features
- ⏳ Mobile app support
- ⏳ Production deployment

See [Project Overview & PDR](docs/project-overview-pdr.md) for detailed roadmap.

---

## 📊 Current Status

**Version**: 0.1.0 (Foundation Phase)

**Implemented**:
- ✅ Clean Architecture structure
- ✅ Domain models (5 entities)
- ✅ Repository ports (5 interfaces)
- ✅ PostgreSQL persistence (5 repositories)
- ✅ OpenAI LLM adapter
- ✅ Pinecone vector adapter
- ✅ Async SQLAlchemy 2.0 with Alembic
- ✅ Configuration management
- ✅ Dependency injection container
- ✅ Use cases (AnalyzeCV, StartInterview)
- ✅ Health check API endpoint

**In Progress**:
- 🔄 Complete REST API
- 🔄 CV processing adapters
- 🔄 WebSocket chat handler

**Planned**:
- ⏳ Authentication & authorization
- ⏳ Comprehensive testing
- ⏳ API documentation
- ⏳ Docker deployment

---

## 🛡️ Security

- API keys stored in environment variables (never committed)
- SQL injection prevention via parameterized queries
- Input validation with Pydantic
- HTTPS enforcement (production)
- Data encryption at rest (Neon built-in)
- GDPR compliance considerations

Report security vulnerabilities to: security@elios.ai

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 and Embeddings API
- **Pinecone** for vector database
- **FastAPI** for the excellent web framework
- **Neon** for serverless PostgreSQL
- **Pydantic** for data validation
- **SQLAlchemy** for ORM

---

## 📞 Contact

- **Website**: https://elios.ai
- **Email**: contact@elios.ai
- **Issues**: [GitHub Issues](https://github.com/elios/elios-ai-service/issues)
- **Discussions**: [GitHub Discussions](https://github.com/elios/elios-ai-service/discussions)

---

## ⭐ Support

If you find this project helpful, please consider giving it a star on GitHub! It helps others discover the project and motivates continued development.

---

**Built with ❤️ using Clean Architecture principles**
