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
- **🤖 Adaptive Questions**: Generate personalized interview questions using vector-based exemplar retrieval
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

### Main flows

#### 1. Preparation Phase (Scan CV & Generate Topics)

```mermaid
sequenceDiagram
    actor Candidate
    participant ChatUI as Chat UI / Frontend
    participant CVAnalyzer as 📄 CV Analyzer Component
    participant VectorDB as 🧠 Vector Database
    participant AIEngine as 🤖 AI Interviewer Engine

    Candidate->>ChatUI: Upload CV file
    ChatUI->>CVAnalyzer: Send CV for analysis
    CVAnalyzer->>VectorDB: Generate & store CV embeddings
    VectorDB-->>CVAnalyzer: Confirm embeddings stored
    CVAnalyzer-->>ChatUI: Return extracted skills & suggested topics
    ChatUI-->>Candidate: Display preparation summary
    ChatUI->>AIEngine: Notify readiness (skills, topics)
    AIEngine-->>ChatUI: Acknowledged
```

#### 2. Interview Phase (Real-time Q&A)

```mermaid
sequenceDiagram
    actor Candidate
    participant ChatUI as Chat UI / Frontend
    participant AIEngine as 🤖 AI Interviewer Engine
    participant VectorDB as 🧠 Vector Database
    participant QBank as 📚 Question Bank Service
    participant STT as 🎤 Speech-to-Text
    participant TTS as 🗣️ Text-to-Speech
    participant Analytics as 📊 Analytics & Feedback Service

    %% --- Start Interview ---
    Candidate->>ChatUI: Start interview
    ChatUI->>AIEngine: Request first question
    AIEngine->>VectorDB: Query similar question embeddings (based on CV topics)
    VectorDB-->>AIEngine: Return question candidates
    AIEngine->>QBank: Fetch selected question
    QBank-->>AIEngine: Return question details
    AIEngine-->>ChatUI: Send question text
    ChatUI-->>TTS: Convert question text to speech
    TTS-->>Candidate: Play AI voice question

    %% --- Candidate answers ---
    Candidate->>STT: Speak answer
    STT-->>AIEngine: Send transcript text
    AIEngine->>VectorDB: Compare answer embeddings & evaluate quality
    VectorDB-->>AIEngine: Return similarity & semantic score
    AIEngine->>Analytics: Send answer evaluation (score, sentiment, reasoning)
    Analytics-->>AIEngine: Acknowledged

    alt More questions remain
        AIEngine->>VectorDB: Retrieve next suitable question
        VectorDB-->>AIEngine: Return next question candidate
        AIEngine-->>ChatUI: Send next question
        ChatUI-->>TTS: Convert to speech & play
        TTS-->>Candidate: Play next question
    else Interview finished
        AIEngine-->>ChatUI: Notify interview end
    end

```

#### 3. Final Stage (Evaluation & Reporting)

```mermaid
sequenceDiagram
    actor Candidate
    participant ChatUI as Chat UI / Frontend
    participant AIEngine as 🤖 AI Interviewer Engine
    participant Analytics as 📊 Analytics & Feedback Service

    AIEngine->>Analytics: Send final interview summary (scores, metrics, transcript)
    Analytics->>Analytics: Aggregate results & generate report
    Analytics-->>AIEngine: Acknowledged

    AIEngine-->>ChatUI: Notify interview completion
    ChatUI->>Analytics: Request final feedback report
    Analytics-->>ChatUI: Return detailed feedback & improvement suggestions
    ChatUI-->>Candidate: Display performance summary & insights

```

---

## 🏗️ Architecture

This project follows **Clean Architecture** (Hexagonal/Ports & Adapters): Domain Layer (pure business logic) → Application Layer (use cases) → Adapters Layer (external services) → Infrastructure Layer (config, DI).

📚 **[Full Architecture Details →](docs/system-architecture.md)**

---

## 🚀 Quick Start

### ⚡ 5-Minute Setup

**Just want to run it?** Copy and paste these commands:

```bash
# Setup environment and install dependencies
python -m venv venv && venv\Scripts\activate && pip install -e ".[dev]"

# Configure and run migrations
cp .env.example .env.local && alembic upgrade head

# Start the server
python -m src.main
```

Then visit: **http://localhost:8000/docs**

⚠️ **Note**: Edit `.env.local` with your API keys before full functionality works.

---

### 📋 Detailed Setup Instructions

#### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL database (or Neon account)
- OpenAI API key
- Pinecone API key

#### Installation

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
   python -m src.main
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

### Mock Adapters for Testing

**Mock adapters** simulate external services without API costs or network latency. Enabled by default in development.

**Available Mocks** (6 total):
- `MockLLMAdapter` - Simulates OpenAI/LLM responses
- `MockVectorSearchAdapter` - In-memory vector search
- `MockSTTAdapter` - Simulates speech-to-text
- `MockTTSAdapter` - Simulates text-to-speech
- `MockCVAnalyzerAdapter` - Filename-based CV parsing
- `MockAnalyticsAdapter` - In-memory performance tracking

**Configuration**:
```env
# .env.local
USE_MOCK_ADAPTERS=true   # Use mocks (default, fast tests)
USE_MOCK_ADAPTERS=false  # Use real services (requires API keys)
```

**Benefits**:
- Tests run 10x faster (~5s vs ~30s)
- No API costs during development
- No network dependency
- Deterministic test results

**Note**: Repositories (PostgreSQL) intentionally NOT mocked - use real database for data integrity tests.

### Running Tests

```bash
# Run all tests (with mocks enabled by default)
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/         # Unit tests only
pytest tests/integration/  # Integration tests only
pytest tests/e2e/          # End-to-end tests only

# Test with real adapters (requires API keys)
USE_MOCK_ADAPTERS=false pytest
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
        "http://localhost:8000/api/candidates",
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
            "http://localhost:8000/api/cv/upload",
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
        "http://localhost:8000/api/interviews",
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
        f"http://localhost:8000/api/interviews/{interview['id']}/answers",
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
│   ├── domain/              # Core business logic (8 models, 13 ports)
│   ├── application/         # Use cases (8 total)
│   ├── adapters/            # External service implementations (20+)
│   └── infrastructure/      # Config, DI, database
├── alembic/                 # Database migrations
├── docs/                    # Documentation
└── tests/                   # Test suites
```

📚 **[Complete Structure →](docs/codebase-summary.md)**

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

### Phase 1: Foundation (v0.1.0 - v0.2.1) - COMPLETE ✅
- ✅ Domain models (8 entities) and ports (13 interfaces)
- ✅ PostgreSQL persistence layer (7 repositories)
- ✅ OpenAI & Azure OpenAI LLM adapters
- ✅ Pinecone & ChromaDB vector adapters
- ✅ Azure Speech services (STT/TTS)
- ✅ Database migrations
- ✅ REST API implementation (5 endpoints)
- ✅ WebSocket real-time protocol
- ✅ Domain-driven state management
- ✅ Context-aware evaluation with follow-ups
- ✅ Session orchestrator (state machine)

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

**Version**: 0.2.1 (Foundation + Adaptive Interviews + Session Orchestration)

**Implemented**:
- ✅ Clean Architecture structure
- ✅ Domain models (8 entities including Evaluation, ErrorCodes)
- ✅ Repository ports (13 interfaces including EvaluationRepositoryPort)
- ✅ PostgreSQL persistence (7 repositories)
- ✅ OpenAI & Azure OpenAI LLM adapters
- ✅ Pinecone & ChromaDB vector adapters
- ✅ Azure Speech services (STT/TTS adapters)
- ✅ Async SQLAlchemy 2.0 with Alembic
- ✅ Configuration management
- ✅ Dependency injection container
- ✅ Use cases (8 total: AnalyzeCV, PlanInterview, ProcessAnswerAdaptive, FollowUpDecision, CombineEvaluation, GenerateSummary, CompleteInterview, GetNextQuestion)
- ✅ REST API (5 interview endpoints) + WebSocket protocol
- ✅ Domain-driven state management (Interview state machine)
- ✅ Context-aware evaluation with follow-up questions
- ✅ Session orchestrator (state machine pattern for WebSocket)
- ✅ Comprehensive interview summary generation

**In Progress**:
- 🔄 CV processing adapters (spaCy, PyPDF2)
- 🔄 Test coverage expansion (85%+ on core features)

**Planned**:
- ⏳ Authentication & authorization
- ⏳ Rate limiting
- ⏳ Docker deployment
- ⏳ Production optimization

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
