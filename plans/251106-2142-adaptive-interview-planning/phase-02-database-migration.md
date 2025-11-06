# Phase 02: Database Schema Migration

**Phase ID**: phase-02-database-migration
**Created**: 2025-11-06
**Status**: ⏳ Pending
**Priority**: P0 (Critical)
**Estimated Effort**: 6 hours

## Context

**Parent Plan**: [Main Plan](./plan.md)
**Dependencies**: [Phase 01 - Domain Models](./phase-01-domain-model-updates.md)
**Related Docs**: [Database Architecture](../../docs/system-architecture.md#database-architecture) | [Current Schema](../../alembic/versions/a4047ce5a909_initial_database_schema_with_all_tables.py)

## Overview

Create Alembic migration to extend 3 tables (questions, interviews, answers) with nullable columns for planning/evaluation. Includes rollback safety, index optimization, data validation.

**Date**: 2025-11-06
**Description**: Add planning/evaluation columns to PostgreSQL schema
**Priority**: P0 - Blocks use case implementation
**Status Breakdown**:
- Migration script: ⏳ Pending
- SQLAlchemy models updated: ⏳ Pending
- Mappers updated: ⏳ Pending
- Indexes created: ⏳ Pending
- Tested on staging: ⏳ Pending

## Key Insights

- **Nullable columns**: All new columns must be NULL-able for backward compatibility
- **No backfill**: Existing rows keep NULL values (no data migration needed for MVP)
- **Index strategy**: Add GIN index on gaps JSONB, B-tree on similarity_score for filtering
- **Rollback safety**: Migration must be reversible without data loss
- **Performance**: New columns should not impact existing query performance

## Requirements

### Functional Requirements

1. **questions table** adds columns:
   - `ideal_answer TEXT NULL` - Reference answer text
   - `rationale TEXT NULL` - Explanation of ideal answer
   - `is_follow_up BOOLEAN DEFAULT FALSE` - Follow-up flag
   - `parent_question_id UUID NULL` - Foreign key to questions.id

2. **interviews table** adds columns:
   - `plan_metadata JSONB DEFAULT '{}'::jsonb` - Planning metadata
   - `adaptive_follow_ups UUID[] DEFAULT ARRAY[]::uuid[]` - Follow-up IDs

3. **answers table** adds columns:
   - `similarity_score FLOAT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1)` - Cosine similarity
   - `gaps JSONB NULL` - Detected concept gaps
   - `speaking_score FLOAT NULL CHECK (speaking_score >= 0 AND speaking_score <= 100)` - Prosody score

### Non-Functional Requirements

- Migration runs in <30s on DB with 10k interviews
- Rollback completes in <10s
- No downtime required (nullable columns)
- Indexes created concurrently (PostgreSQL 11+)
- All constraints validated

## Architecture

### Schema Changes

```sql
-- BEFORE (existing tables)
CREATE TABLE questions (
    id UUID PRIMARY KEY,
    text TEXT NOT NULL,
    reference_answer TEXT,
    -- ... other columns
);

CREATE TABLE interviews (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id),
    question_ids UUID[],
    -- ... other columns
);

CREATE TABLE answers (
    id UUID PRIMARY KEY,
    interview_id UUID REFERENCES interviews(id),
    evaluation JSONB,
    -- ... other columns
);

-- AFTER (extended tables)
CREATE TABLE questions (
    id UUID PRIMARY KEY,
    text TEXT NOT NULL,
    reference_answer TEXT,
    ideal_answer TEXT NULL,  -- NEW
    rationale TEXT NULL,  -- NEW
    is_follow_up BOOLEAN DEFAULT FALSE NOT NULL,  -- NEW
    parent_question_id UUID NULL REFERENCES questions(id),  -- NEW
    -- ... other columns
);

CREATE TABLE interviews (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id),
    question_ids UUID[],
    plan_metadata JSONB DEFAULT '{}'::jsonb NOT NULL,  -- NEW
    adaptive_follow_ups UUID[] DEFAULT ARRAY[]::uuid[] NOT NULL,  -- NEW
    -- ... other columns
);

CREATE TABLE answers (
    id UUID PRIMARY KEY,
    interview_id UUID REFERENCES interviews(id),
    evaluation JSONB,
    similarity_score FLOAT NULL,  -- NEW
    gaps JSONB NULL,  -- NEW
    speaking_score FLOAT NULL,  -- NEW
    -- ... other columns
);

-- Indexes
CREATE INDEX CONCURRENTLY idx_questions_parent_question_id
    ON questions(parent_question_id) WHERE parent_question_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_answers_similarity_score
    ON answers(similarity_score) WHERE similarity_score IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_answers_gaps
    ON answers USING GIN(gaps) WHERE gaps IS NOT NULL;

-- Constraints
ALTER TABLE answers
    ADD CONSTRAINT check_similarity_score_bounds
    CHECK (similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1));

ALTER TABLE answers
    ADD CONSTRAINT check_speaking_score_bounds
    CHECK (speaking_score IS NULL OR (speaking_score >= 0 AND speaking_score <= 100));
```

### SQLAlchemy Model Changes

```python
# src/adapters/persistence/models.py

class QuestionModel(Base):
    __tablename__ = "questions"

    # Existing columns...

    # NEW columns
    ideal_answer = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    is_follow_up = Column(Boolean, default=False, nullable=False)
    parent_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)

class InterviewModel(Base):
    __tablename__ = "interviews"

    # Existing columns...

    # NEW columns
    plan_metadata = Column(JSONB, default={}, nullable=False)
    adaptive_follow_ups = Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)

class AnswerModel(Base):
    __tablename__ = "answers"

    # Existing columns...

    # NEW columns
    similarity_score = Column(Float, nullable=True)
    gaps = Column(JSONB, nullable=True)
    speaking_score = Column(Float, nullable=True)
```

## Related Code Files

### Files to Modify (2)

1. **src/adapters/persistence/models.py** (current: ~200 lines)
   - Add 7 new columns across 3 models
   - Add foreign key relationship (parent_question_id)
   - Estimated: +30 lines

2. **src/adapters/persistence/mappers.py** (current: ~300 lines)
   - Update 3 mappers (to_domain, to_db_model)
   - Handle None → default conversions
   - Estimated: +40 lines

### Files to Create (2)

1. **alembic/versions/xxx_add_planning_fields.py** (new)
   - Migration script (up + down)
   - Estimated: ~150 lines

2. **tests/integration/test_planning_migration.py** (new)
   - Test migration forward/backward
   - Estimated: ~100 lines

## Implementation Steps

### Step 1: Generate Migration Script (30 min)

**Command**:
```bash
alembic revision --autogenerate -m "add planning and adaptive evaluation fields"
```

**Review autogenerated script**:
- Verify column types match domain models
- Add CHECK constraints manually (autogenerate may miss)
- Add indexes manually (CONCURRENTLY not auto-detected)
- Add comments to explain schema changes

**Expected output**: `alembic/versions/YYYYMMDD_HHMM_add_planning_fields.py`

### Step 2: Customize Migration (60 min)

**File**: `alembic/versions/xxx_add_planning_fields.py`

**Template**:
```python
"""Add planning and adaptive evaluation fields.

Revision ID: xxx
Revises: a4047ce5a909
Create Date: 2025-11-06

Changes:
- questions: ideal_answer, rationale, is_follow_up, parent_question_id
- interviews: plan_metadata, adaptive_follow_ups
- answers: similarity_score, gaps, speaking_score
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx'
down_revision = 'a4047ce5a909'
branch_labels = None
depends_on = None

def upgrade():
    # === Questions table ===
    op.add_column('questions',
        sa.Column('ideal_answer', sa.Text(), nullable=True)
    )
    op.add_column('questions',
        sa.Column('rationale', sa.Text(), nullable=True)
    )
    op.add_column('questions',
        sa.Column('is_follow_up', sa.Boolean(), server_default='false', nullable=False)
    )
    op.add_column('questions',
        sa.Column('parent_question_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_questions_parent_question_id',
        'questions', 'questions',
        ['parent_question_id'], ['id'],
        ondelete='SET NULL'
    )

    # === Interviews table ===
    op.add_column('interviews',
        sa.Column('plan_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False)
    )
    op.add_column('interviews',
        sa.Column('adaptive_follow_ups', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=False)
    )

    # === Answers table ===
    op.add_column('answers',
        sa.Column('similarity_score', sa.Float(), nullable=True)
    )
    op.add_column('answers',
        sa.Column('gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('answers',
        sa.Column('speaking_score', sa.Float(), nullable=True)
    )

    # === Constraints ===
    op.create_check_constraint(
        'check_similarity_score_bounds',
        'answers',
        'similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)'
    )
    op.create_check_constraint(
        'check_speaking_score_bounds',
        'answers',
        'speaking_score IS NULL OR (speaking_score >= 0 AND speaking_score <= 100)'
    )

    # === Indexes (CONCURRENTLY requires raw SQL) ===
    op.execute(
        'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_parent_question_id '
        'ON questions(parent_question_id) WHERE parent_question_id IS NOT NULL'
    )
    op.execute(
        'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_answers_similarity_score '
        'ON answers(similarity_score) WHERE similarity_score IS NOT NULL'
    )
    op.execute(
        'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_answers_gaps '
        'ON answers USING GIN(gaps) WHERE gaps IS NOT NULL'
    )

def downgrade():
    # Drop indexes
    op.drop_index('idx_answers_gaps', table_name='answers')
    op.drop_index('idx_answers_similarity_score', table_name='answers')
    op.drop_index('idx_questions_parent_question_id', table_name='questions')

    # Drop constraints
    op.drop_constraint('check_speaking_score_bounds', 'answers', type_='check')
    op.drop_constraint('check_similarity_score_bounds', 'answers', type_='check')

    # Drop columns (answers)
    op.drop_column('answers', 'speaking_score')
    op.drop_column('answers', 'gaps')
    op.drop_column('answers', 'similarity_score')

    # Drop columns (interviews)
    op.drop_column('interviews', 'adaptive_follow_ups')
    op.drop_column('interviews', 'plan_metadata')

    # Drop columns (questions)
    op.drop_constraint('fk_questions_parent_question_id', 'questions', type_='foreignkey')
    op.drop_column('questions', 'parent_question_id')
    op.drop_column('questions', 'is_follow_up')
    op.drop_column('questions', 'rationale')
    op.drop_column('questions', 'ideal_answer')
```

### Step 3: Update SQLAlchemy Models (45 min)

**File**: `src/adapters/persistence/models.py`

**Changes**:
```python
from sqlalchemy import Column, Text, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

class QuestionModel(Base):
    # ... existing fields ...

    ideal_answer = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    is_follow_up = Column(Boolean, default=False, nullable=False)
    parent_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)

class InterviewModel(Base):
    # ... existing fields ...

    plan_metadata = Column(JSONB, default=dict, nullable=False)
    adaptive_follow_ups = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)

class AnswerModel(Base):
    # ... existing fields ...

    similarity_score = Column(Float, nullable=True)
    gaps = Column(JSONB, nullable=True)
    speaking_score = Column(Float, nullable=True)
```

### Step 4: Update Mappers (60 min)

**File**: `src/adapters/persistence/mappers.py`

**QuestionMapper changes**:
```python
class QuestionMapper:
    @staticmethod
    def to_domain(db_model: QuestionModel) -> Question:
        return Question(
            # ... existing fields ...
            ideal_answer=db_model.ideal_answer,
            rationale=db_model.rationale,
            is_follow_up=db_model.is_follow_up,
            parent_question_id=db_model.parent_question_id,
        )

    @staticmethod
    def to_db_model(domain: Question) -> QuestionModel:
        return QuestionModel(
            # ... existing fields ...
            ideal_answer=domain.ideal_answer,
            rationale=domain.rationale,
            is_follow_up=domain.is_follow_up,
            parent_question_id=domain.parent_question_id,
        )
```

**InterviewMapper changes**:
```python
class InterviewMapper:
    @staticmethod
    def to_domain(db_model: InterviewModel) -> Interview:
        return Interview(
            # ... existing fields ...
            plan_metadata=db_model.plan_metadata or {},
            adaptive_follow_ups=db_model.adaptive_follow_ups or [],
        )

    @staticmethod
    def to_db_model(domain: Interview) -> InterviewModel:
        return InterviewModel(
            # ... existing fields ...
            plan_metadata=domain.plan_metadata or {},
            adaptive_follow_ups=domain.adaptive_follow_ups or [],
        )
```

**AnswerMapper changes**: Similar pattern for 3 new fields

### Step 5: Test Migration (90 min)

**Create integration test**:

**File**: `tests/integration/test_planning_migration.py`
```python
import pytest
from sqlalchemy import select
from src.adapters.persistence.models import QuestionModel, InterviewModel, AnswerModel
from src.infrastructure.database.session import get_async_session

async def test_migration_adds_question_fields():
    """Verify questions table has new columns."""
    async with get_async_session() as session:
        # Create question with new fields
        question = QuestionModel(
            text="What is Python?",
            ideal_answer="Python is a high-level...",
            rationale="This answer covers key concepts...",
            is_follow_up=False,
        )
        session.add(question)
        await session.commit()

        # Query back
        stmt = select(QuestionModel).where(QuestionModel.id == question.id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.ideal_answer == "Python is a high-level..."
        assert retrieved.rationale == "This answer covers key concepts..."
        assert retrieved.is_follow_up is False

async def test_migration_handles_null_values():
    """Verify backward compatibility with NULL values."""
    async with get_async_session() as session:
        # Create question WITHOUT new fields
        question = QuestionModel(text="What is Java?")
        session.add(question)
        await session.commit()

        # Verify NULL handling
        stmt = select(QuestionModel).where(QuestionModel.id == question.id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.ideal_answer is None
        assert retrieved.rationale is None
        assert retrieved.is_follow_up is False  # Default

async def test_migration_rollback():
    """Verify downgrade removes columns."""
    # Run downgrade command
    # Verify columns no longer exist
    # Run upgrade to restore
    pass  # Implement using subprocess to call alembic downgrade/upgrade
```

**Run tests**:
```bash
# Apply migration
alembic upgrade head

# Run integration tests
pytest tests/integration/test_planning_migration.py -v

# Test rollback
alembic downgrade -1
alembic upgrade head
```

## Todo List

### Migration Script
- [ ] Generate migration with alembic revision --autogenerate
- [ ] Review autogenerated script for correctness
- [ ] Add CHECK constraints for similarity_score bounds (0-1)
- [ ] Add CHECK constraints for speaking_score bounds (0-100)
- [ ] Add foreign key for parent_question_id → questions.id
- [ ] Add CONCURRENTLY indexes (3 indexes)
- [ ] Test upgrade on empty database
- [ ] Test upgrade on database with existing data
- [ ] Test downgrade (rollback)
- [ ] Verify migration reversibility

### SQLAlchemy Models
- [ ] Update QuestionModel with 4 new columns
- [ ] Update InterviewModel with 2 new columns
- [ ] Update AnswerModel with 3 new columns
- [ ] Add ForeignKey relationship for parent_question_id
- [ ] Set correct default values (False, {}, [])
- [ ] Run mypy type checking on models.py
- [ ] Format with black

### Mappers
- [ ] Update QuestionMapper.to_domain() with new fields
- [ ] Update QuestionMapper.to_db_model() with new fields
- [ ] Update InterviewMapper.to_domain() with new fields
- [ ] Update InterviewMapper.to_db_model() with new fields
- [ ] Update AnswerMapper.to_domain() with new fields
- [ ] Update AnswerMapper.to_db_model() with new fields
- [ ] Handle None → default conversions (plan_metadata: {} if None)
- [ ] Run mypy type checking on mappers.py
- [ ] Format with black

### Testing
- [ ] Write test for questions table schema changes
- [ ] Write test for interviews table schema changes
- [ ] Write test for answers table schema changes
- [ ] Write test for NULL value handling (backward compat)
- [ ] Write test for constraint validation (similarity 0-1)
- [ ] Write test for foreign key constraint (parent_question_id)
- [ ] Write test for index existence
- [ ] Write test for migration rollback
- [ ] Run all integration tests: `pytest tests/integration/`

### Deployment Preparation
- [ ] Document migration steps in CHANGELOG
- [ ] Create backup script for production DB
- [ ] Test migration on staging environment
- [ ] Estimate migration time on production-size DB
- [ ] Create rollback plan if migration fails

## Success Criteria

- [ ] Migration script runs without errors on empty DB (<10s)
- [ ] Migration script runs without errors on DB with 1k+ interviews (<30s)
- [ ] Rollback (downgrade) completes without data loss (<10s)
- [ ] All 7 new columns added with correct types
- [ ] All 3 indexes created (verify with `\d questions`, `\d answers`)
- [ ] All 2 CHECK constraints active (verify with `\d answers`)
- [ ] Foreign key constraint enforces parent_question_id validity
- [ ] Existing interviews/questions/answers unaffected (NULL values)
- [ ] SQLAlchemy models match database schema
- [ ] Mappers correctly handle new fields + NULL cases
- [ ] Integration tests pass with >90% coverage for persistence layer

## Risk Assessment

**Medium Risks**:
- **Production migration failure**: Large table locks
  - *Mitigation*: Use CONCURRENTLY for indexes, test on staging first
- **Constraint violations**: Existing data may violate new constraints
  - *Mitigation*: All new columns NULL-able, constraints only apply to new data
- **Downgrade data loss**: Rollback drops columns
  - *Mitigation*: Backup before migration, only rollback if zero new data written

**Low Risks**:
- Schema mismatch between SQLAlchemy + PostgreSQL
  - *Mitigation*: Autogenerate + manual review + integration tests

## Security Considerations

- Ideal answers stored in plaintext → no encryption needed (not PII)
- Plan metadata may contain AI strategy → sanitize before exposing via API
- Gaps dict validated in application layer → SQL injection prevented via ORM

## Next Steps

1. Complete all checkboxes in Todo List
2. Test migration on local development DB
3. Test migration on staging with production-like data volume
4. Create deployment runbook for production migration
5. **Proceed to Phase 03**: PlanInterviewUseCase implementation (depends on schema)

---

**Phase Status**: Ready for implementation after Phase 01
**Blocking**: Phase 03, 04 (require schema changes)
**Owner**: Database + backend team
