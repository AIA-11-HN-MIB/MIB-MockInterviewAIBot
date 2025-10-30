# Setup Guide - Elios AI Interview Service

This guide will help you get the project running locally.

## Current Status

✅ **What's Working:**
- Project structure and architecture
- Domain models (Interview, Question, Answer, Candidate, CVAnalysis)
- Port interfaces (LLMPort, VectorSearchPort, etc.)
- OpenAI and Pinecone adapters (ready to use)
- Configuration system
- Dependency injection container
- Basic FastAPI application with health check

⚠️ **What's Not Yet Implemented:**
- CV analyzer adapter (file parsing and analysis)
- Speech adapters (STT/TTS)
- Database persistence layer
- Complete API routes (CV upload, interview management)
- WebSocket handler for real-time chat

## Prerequisites

- **Python 3.11 or 3.12**
- **pip** (Python package manager)
- **Git** (for version control)

## Step-by-Step Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (Git Bash):
source venv/Scripts/activate

# On Linux/Mac:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 2. Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install development dependencies
pip install -r requirements/dev.txt
```

**Expected output:** Installation of FastAPI, Pydantic, OpenAI, Pinecone, and other packages.

**If you get errors**, install minimal dependencies for testing:
```bash
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

**Edit `.env` file** with minimal configuration:

```env
# Minimal config for testing
APP_NAME="Elios AI Interview Service"
ENVIRONMENT="development"
DEBUG=true

API_HOST="0.0.0.0"
API_PORT=8000

# Leave these empty for now (not needed for basic testing)
OPENAI_API_KEY=""
PINECONE_API_KEY=""
POSTGRES_PASSWORD=""
```

### 4. Run the Application

```bash
# Run from project root
python src/main.py
```

OR using uvicorn directly:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Starting Elios AI Interview Service v0.1.0
INFO:     Environment: development
INFO:     Debug mode: True
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. Test the Application

Open your browser and visit:

1. **Root endpoint**: http://localhost:8000
   - Should show welcome message

2. **Health check**: http://localhost:8000/health
   - Should return JSON with status, version, environment

3. **API Documentation**: http://localhost:8000/docs
   - Interactive Swagger UI

4. **Alternative Docs**: http://localhost:8000/redoc
   - ReDoc interface

## What You Can Do Now

### ✅ Currently Working Features

1. **Health Check API**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Interactive API Documentation**
   - Visit http://localhost:8000/docs
   - Try the health endpoint

3. **Domain Models**
   - You can import and use domain models in Python:
   ```python
   from src.domain.models import Interview, Question, Answer, Candidate

   # Create a candidate
   candidate = Candidate(name="John Doe", email="john@example.com")

   # Create an interview
   interview = Interview(candidate_id=candidate.id)
   ```

4. **Configuration System**
   ```python
   from src.infrastructure.config import get_settings

   settings = get_settings()
   print(settings.app_name)
   print(settings.environment)
   ```

### ⚠️ To Enable Full Functionality

To use the complete system, you need to:

#### 1. Add OpenAI API Key (for LLM features)

Edit `.env`:
```env
OPENAI_API_KEY="sk-your-actual-openai-key-here"
LLM_PROVIDER="openai"
OPENAI_MODEL="gpt-4"
```

Then you can use the OpenAI adapter:
```python
from src.infrastructure.dependency_injection import get_container

container = get_container()
llm = container.llm_port()

# Generate a question
question = await llm.generate_question(
    context={"cv_summary": "Python developer"},
    skill="Python",
    difficulty="medium"
)
```

#### 2. Add Pinecone API Key (for vector search)

Edit `.env`:
```env
PINECONE_API_KEY="your-pinecone-key-here"
PINECONE_ENVIRONMENT="us-east-1"
PINECONE_INDEX_NAME="elios-interviews"
```

#### 3. Implement Missing Components

The following need implementation:

**A. CV Analyzer Adapter** (`src/adapters/cv_processing/`)
```python
# TODO: Implement
class SpacyCVAnalyzer(CVAnalyzerPort):
    async def analyze_cv(self, cv_file_path: str, candidate_id: str) -> CVAnalysis:
        # Parse PDF/DOC
        # Extract skills
        # Generate embeddings
        pass
```

**B. Database Repositories** (`src/adapters/persistence/`)
```python
# TODO: Implement
class PostgresQuestionRepository(QuestionRepositoryPort):
    async def save(self, question: Question) -> Question:
        # Save to PostgreSQL
        pass
```

**C. API Routes** (`src/adapters/api/rest/`)
- `cv_routes.py`: CV upload and analysis
- `interview_routes.py`: Interview management
- `question_routes.py`: Question CRUD

**D. Speech Adapters** (`src/adapters/speech/`)
- `azure_stt_adapter.py`: Speech-to-text
- `edge_tts_adapter.py`: Text-to-speech

## Troubleshooting

### Issue: `ModuleNotFoundError`

**Solution:**
```bash
# Make sure you're in the project root
cd H:\FPTU\SEP\project\Elios\EliosAIService

# Activate virtual environment
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements/dev.txt
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use a different port
python src/main.py --port 8001

# Or find and kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

### Issue: `ImportError: cannot import name 'get_settings'`

**Solution:**
Make sure all `__init__.py` files exist:
```bash
# Check if files exist
ls src/__init__.py
ls src/infrastructure/__init__.py
ls src/infrastructure/config/__init__.py
```

### Issue: Pydantic validation errors

**Solution:**
Check your `.env` file has valid values. For testing, minimal config works:
```env
ENVIRONMENT="development"
DEBUG=true
```

## Development Workflow

### 1. Check Code Quality

```bash
# Linting
ruff check src/

# Formatting
black src/

# Type checking
mypy src/
```

### 2. Run Tests (when implemented)

```bash
# Unit tests
pytest tests/unit

# All tests
pytest
```

### 3. Make Changes

1. Edit files in `src/`
2. Server auto-reloads (if using `--reload` flag)
3. Test at http://localhost:8000/docs

## Next Steps for Development

### Immediate (Get Basic Functionality Working)

1. **Implement CV Upload Route**
   - Create `src/adapters/api/rest/cv_routes.py`
   - Handle file upload
   - Return placeholder analysis

2. **Implement Question Routes**
   - Create `src/adapters/api/rest/question_routes.py`
   - CRUD operations for questions
   - Use in-memory storage for now

3. **Create Mock Adapters**
   - Create `src/adapters/cv_processing/mock_cv_analyzer.py`
   - Create `src/adapters/persistence/in_memory_repository.py`
   - Use for testing without external dependencies

### Short-term (Add External Services)

1. Set up PostgreSQL database
2. Implement database repositories
3. Add OpenAI integration
4. Add Pinecone vector database
5. Implement CV parsing

### Medium-term (Complete Features)

1. Implement interview flow
2. Add speech services
3. Create WebSocket handler
4. Build analytics system
5. Generate feedback reports

## Getting Help

- **Documentation**: See `docs/` folder
- **Architecture**: Read `docs/architecture.md`
- **API Reference**: Read `docs/api.md`
- **AI Assistant**: Use Claude Code with `CLAUDE.md` context

## Quick Test Script

Save this as `test_basic.py` in project root:

```python
"""Quick test script to verify setup."""

import asyncio
from src.domain.models import Candidate, Interview, Question, DifficultyLevel, QuestionType
from src.infrastructure.config import get_settings


async def main():
    print("=== Testing Elios AI Service Setup ===\n")

    # Test 1: Configuration
    print("1. Testing Configuration...")
    settings = get_settings()
    print(f"   ✓ App Name: {settings.app_name}")
    print(f"   ✓ Environment: {settings.environment}")
    print(f"   ✓ API Port: {settings.api_port}\n")

    # Test 2: Domain Models
    print("2. Testing Domain Models...")
    candidate = Candidate(name="Test User", email="test@example.com")
    print(f"   ✓ Created Candidate: {candidate.name} ({candidate.id})")

    interview = Interview(candidate_id=candidate.id)
    print(f"   ✓ Created Interview: {interview.id}")
    print(f"   ✓ Interview Status: {interview.status}\n")

    question = Question(
        text="What is dependency injection?",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.MEDIUM,
        skills=["Software Architecture"]
    )
    print(f"   ✓ Created Question: {question.text[:40]}...")
    print(f"   ✓ Question Difficulty: {question.difficulty}\n")

    # Test 3: Interview Flow
    print("3. Testing Interview Flow...")
    interview.mark_ready(candidate.id)
    print(f"   ✓ Interview marked ready")

    interview.start()
    print(f"   ✓ Interview started: {interview.status}")

    interview.add_question(question.id)
    print(f"   ✓ Added question to interview")
    print(f"   ✓ Progress: {interview.get_progress_percentage()}%\n")

    print("=== All Tests Passed! ===")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_basic.py
```

---

**You're now ready to develop!** 🚀

The architecture is in place, domain logic is working, and you can start implementing adapters and API routes incrementally.
