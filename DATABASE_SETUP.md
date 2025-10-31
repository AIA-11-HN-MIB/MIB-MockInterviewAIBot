# Database Setup Guide

This guide explains how to set up and use the PostgreSQL database persistence layer for the Elios AI Interview Service.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Database Configuration](#database-configuration)
- [Initial Setup](#initial-setup)
- [Database Migrations](#database-migrations)
- [Database Schema](#database-schema)
- [Using Repositories](#using-repositories)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before setting up the database, ensure you have:

1. **PostgreSQL 14+** installed and running
2. **Python 3.11+** with project dependencies installed
3. Database user with CREATE DATABASE privileges

### Installing PostgreSQL

**Windows:**
```bash
# Using Chocolatey
choco install postgresql

# Or download from https://www.postgresql.org/download/windows/
```

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Database Configuration

The application reads configuration from environment files in this order:
1. `.env.local` (highest priority, not committed to git)
2. `.env` (fallback, can be committed with placeholders)
3. System environment variables

### Recommended Setup

Create a `.env.local` file for your local configuration:

```bash
# Copy from example
cp .env.example .env.local

# Edit with your actual credentials
nano .env.local
```

### Option 1: Using DATABASE_URL (Recommended)

In your `.env.local` file:

```bash
# Full PostgreSQL connection string
DATABASE_URL="postgresql://elios:your-password@localhost:5432/elios_interviews"
```

### Option 2: Using Individual Parameters

Alternatively, configure individual connection parameters:

```bash
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="elios"
POSTGRES_PASSWORD="your-secure-password"
POSTGRES_DB="elios_interviews"
```

> **Note:** The application automatically converts `postgresql://` to `postgresql+asyncpg://` for async support.
>
> **Security:** Use `.env.local` for sensitive credentials. This file is in `.gitignore` and won't be committed. See [[ENV_SETUP.md]] for details.

## Initial Setup

### Step 1: Create PostgreSQL User and Database

Connect to PostgreSQL as superuser:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database user
CREATE USER elios WITH PASSWORD 'your-secure-password';

# Create database
CREATE DATABASE elios_interviews OWNER elios;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE elios_interviews TO elios;

# Exit psql
\q
```

### Step 2: Verify Connection

Test the database connection:

```bash
# Using psql
psql -U elios -d elios_interviews -h localhost

# Or using Python
python scripts/setup_db.py
```

### Step 3: Run Database Migrations

Apply the initial database schema:

```bash
# Run all pending migrations
alembic upgrade head
```

This creates the following tables:
- `candidates` - Candidate information and CV paths
- `questions` - Interview question bank
- `cv_analyses` - CV analysis results with extracted skills
- `interviews` - Interview sessions and state
- `answers` - Candidate answers with evaluations

## Database Migrations

### Creating New Migrations

When you modify the SQLAlchemy models:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/
# Then apply it
alembic upgrade head
```

### Migration Commands

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Downgrade to base (empty database)
alembic downgrade base
```

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│  Candidates │◄────┬───┤  Interviews  │
└─────────────┘     │   └──────────────┘
      ▲             │          ▲
      │             │          │
      │             │   ┌──────────────┐
      │             └───┤ CV Analyses  │
      │                 └──────────────┘
      │
      │             ┌──────────────┐
      └─────────────┤   Answers    │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Questions   │
                    └──────────────┘
```

### Key Tables

**candidates**
- Stores candidate profile information
- Links to interviews, CV analyses, and answers

**questions**
- Question bank with metadata (type, difficulty, skills)
- Supports semantic search via vector embeddings
- Uses GIN indexes for array columns (skills, tags)

**cv_analyses**
- Stores extracted CV data and skills
- JSONB storage for flexible skill metadata
- Linked to candidates and interviews

**interviews**
- Tracks interview state and progress
- Stores question/answer order as UUID arrays
- Status workflow: PREPARING → READY → IN_PROGRESS → COMPLETED

**answers**
- Candidate responses to questions
- JSONB evaluation scores and feedback
- Optional voice recording paths

## Using Repositories

### Repository Pattern

Repositories provide clean separation between business logic and data access:

```python
from infrastructure.database import get_async_session
from infrastructure.dependency_injection import get_container
from domain.models.candidate import Candidate

async def example_usage():
    # Get database session
    async for session in get_async_session():
        # Get repository from DI container
        container = get_container()
        candidate_repo = container.candidate_repository_port(session)

        # Create new candidate
        new_candidate = Candidate(
            name="John Doe",
            email="john@example.com"
        )
        saved = await candidate_repo.save(new_candidate)

        # Query candidate
        candidate = await candidate_repo.get_by_email("john@example.com")

        # Update candidate
        candidate.update_cv("/path/to/cv.pdf")
        await candidate_repo.update(candidate)

        # The session is automatically committed/rolled back
```

### Available Repositories

All repositories follow the same pattern:

- `CandidateRepositoryPort` → `PostgreSQLCandidateRepository`
- `QuestionRepositoryPort` → `PostgreSQLQuestionRepository`
- `InterviewRepositoryPort` → `PostgreSQLInterviewRepository`
- `AnswerRepositoryPort` → `PostgreSQLAnswerRepository`
- `CVAnalysisRepositoryPort` → `PostgreSQLCVAnalysisRepository`

### FastAPI Integration

Use dependency injection in API routes:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database import get_async_session
from infrastructure.dependency_injection import get_container

router = APIRouter()

@router.get("/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    container = get_container()
    repo = container.candidate_repository_port(session)

    candidate = await repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return candidate
```

## Troubleshooting

### Connection Issues

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Verify PostgreSQL is running: `pg_isready`
2. Check connection parameters in `.env`
3. Ensure PostgreSQL allows connections (check `pg_hba.conf`)

### Migration Errors

**Problem:** `alembic.util.exc.CommandError: Can't locate revision identified by 'xxxx'`

**Solution:**
```bash
# Reset migration history
alembic stamp head

# Or start fresh
alembic downgrade base
alembic upgrade head
```

### Permission Errors

**Problem:** `permission denied for schema public`

**Solution:**
```sql
-- Grant permissions to your user
GRANT ALL ON SCHEMA public TO elios;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO elios;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO elios;
```

### Array/JSONB Query Issues

**Problem:** Queries on array or JSONB columns are slow

**Solution:**
- Ensure GIN indexes are created (should be automatic with migrations)
- Use PostgreSQL-specific array operators:
  ```python
  # Contains
  query = select(QuestionModel).where(QuestionModel.skills.contains(["Python"]))

  # Overlap
  query = select(QuestionModel).where(QuestionModel.tags.overlap(["algorithms", "data-structures"]))
  ```

## Performance Optimization

### Connection Pooling

The application uses SQLAlchemy's built-in connection pooling:

- **Development:** NullPool (no pooling, prevents connection leaks)
- **Production:** QueuePool with 10 connections, 20 overflow

### Indexes

The following indexes are automatically created:

- B-tree indexes on foreign keys and frequently queried columns
- GIN indexes on array columns (`skills`, `tags`)
- Unique indexes on email addresses

### Query Optimization

```python
# ✅ Good: Use select with specific columns
from sqlalchemy import select
result = await session.execute(
    select(CandidateModel.id, CandidateModel.name)
)

# ✅ Good: Use relationships with selectinload
from sqlalchemy.orm import selectinload
result = await session.execute(
    select(InterviewModel)
    .options(selectinload(InterviewModel.candidate))
)

# ❌ Bad: N+1 queries
interviews = await interview_repo.list_all()
for interview in interviews:
    candidate = await candidate_repo.get_by_id(interview.candidate_id)
```

## Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
