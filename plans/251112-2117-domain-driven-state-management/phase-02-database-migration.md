# Phase 2: Database Migration

## Context Links
- **Parent Plan**: [plan.md](./plan.md)
- **Dependencies**: Phase 1 (Domain Model Enhancement)
- **Related Docs**:
  - `docs/deployment-guide.md`
  - Scout: [scout-01-affected-files.md](./scout/scout-01-affected-files.md)

## Overview

**Date**: 2025-11-12
**Description**: Create Alembic migration to add follow-up tracking columns
**Priority**: HIGH (blocks Phase 3)
**Effort Estimate**: 1-2 hours
**Implementation Status**: ⏳ Not Started
**Review Status**: ⏳ Pending

## Key Insights

1. **New Columns**: `current_parent_question_id` (UUID, nullable), `current_followup_count` (INT, default 0)
2. **Backward Compatible**: Defaults allow existing interviews to continue
3. **No Data Migration**: In-progress interviews reset counters (acceptable per requirements)
4. **Safe Rollback**: Downgrade simply drops new columns

## Requirements

### Functional Requirements
- ✅ Add `current_parent_question_id` column to `interviews` table
- ✅ Add `current_followup_count` column with default value 0
- ✅ Update SQLAlchemy model to include new fields
- ✅ Update mapper to serialize/deserialize new fields
- ✅ Test migration upgrade path
- ✅ Test migration downgrade (rollback)

### Non-Functional Requirements
- ✅ Migration runs in <1 second (simple column additions)
- ✅ No downtime required (nullable/default values)
- ✅ Idempotent migration (safe to re-run)
- ✅ Clear migration message/description

## Architecture

### Database Schema Changes

**Table**: `interviews`

**New Columns**:
```sql
current_parent_question_id UUID NULL DEFAULT NULL
current_followup_count INTEGER NOT NULL DEFAULT 0
```

### SQLAlchemy Model Changes

**File**: `src/adapters/persistence/models.py`
```python
class InterviewModel(Base):
    # ... existing fields ...

    # NEW: Follow-up tracking
    current_parent_question_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        default=None
    )
    current_followup_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
```

### Mapper Updates

**File**: `src/adapters/persistence/mappers.py`
```python
def domain_to_db_interview(interview: Interview) -> InterviewModel:
    return InterviewModel(
        # ... existing mappings ...
        current_parent_question_id=interview.current_parent_question_id,
        current_followup_count=interview.current_followup_count,
    )

def db_to_domain_interview(db_model: InterviewModel) -> Interview:
    return Interview(
        # ... existing mappings ...
        current_parent_question_id=db_model.current_parent_question_id,
        current_followup_count=db_model.current_followup_count,
    )
```

## Related Code Files

### To Modify
- `src/adapters/persistence/models.py` (lines 111-161)
- `src/adapters/persistence/mappers.py` (mapper functions)

### To Create
- `alembic/versions/YYYYMMDD_HHMM_add_followup_tracking.py` (migration script)

## Implementation Steps

### Step 1: Generate Migration Script
```bash
cd H:\AI-course\EliosAIService
alembic revision -m "add_followup_tracking"
```

### Step 2: Write Migration Upgrade
**File**: `alembic/versions/YYYYMMDD_HHMM_add_followup_tracking.py`

```python
"""Add follow-up tracking fields to interviews table.

Revision ID: <generated>
Revises: <previous_revision>
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '<generated>'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade():
    """Add current_parent_question_id and current_followup_count columns."""
    op.add_column(
        'interviews',
        sa.Column(
            'current_parent_question_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            server_default=None
        )
    )
    op.add_column(
        'interviews',
        sa.Column(
            'current_followup_count',
            sa.Integer(),
            nullable=False,
            server_default='0'
        )
    )

def downgrade():
    """Remove follow-up tracking columns."""
    op.drop_column('interviews', 'current_followup_count')
    op.drop_column('interviews', 'current_parent_question_id')
```

### Step 3: Update SQLAlchemy Model
**File**: `src/adapters/persistence/models.py`
**Location**: After line 151 (after `adaptive_follow_ups`)

Add field definitions as shown in Architecture section.

### Step 4: Update Domain Mappers
**File**: `src/adapters/persistence/mappers.py`

Add new fields to both `domain_to_db_interview()` and `db_to_domain_interview()` functions.

### Step 5: Test Migration Locally
```bash
# Backup database first (if production-like data exists)
pg_dump elios_interview_db > backup_pre_migration.sql

# Run migration
alembic upgrade head

# Verify columns added
psql elios_interview_db -c "\d interviews"

# Check default values work
psql elios_interview_db -c "SELECT id, current_followup_count FROM interviews LIMIT 5;"

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

## Todo List

- [ ] Generate Alembic migration script
- [ ] Write `upgrade()` function with column additions
- [ ] Write `downgrade()` function with column removals
- [ ] Add `current_parent_question_id` to `InterviewModel`
- [ ] Add `current_followup_count` to `InterviewModel`
- [ ] Update `domain_to_db_interview()` mapper
- [ ] Update `db_to_domain_interview()` mapper
- [ ] Test migration on local database
- [ ] Verify default values applied correctly
- [ ] Test downgrade/rollback path
- [ ] Verify existing interviews load successfully

## Success Criteria

✅ **Migration Execution**
- `alembic upgrade head` completes without errors
- Both columns added to `interviews` table
- Default values applied correctly

✅ **Data Integrity**
- Existing interviews load with `current_followup_count=0`
- Existing interviews have `current_parent_question_id=NULL`
- No data loss on upgrade

✅ **Rollback Safety**
- `alembic downgrade -1` removes columns cleanly
- Database returns to previous state
- Can re-run upgrade after downgrade

✅ **Mapper Functionality**
- Domain → DB mapping includes new fields
- DB → Domain mapping includes new fields
- Repository save/load works correctly

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Migration fails on production | HIGH | LOW | Test thoroughly locally, use backup |
| Existing interviews broken | HIGH | LOW | Default values ensure compatibility |
| Rollback data loss | MEDIUM | LOW | New columns only, rollback safe |
| Mapper serialization bugs | MEDIUM | MEDIUM | Integration test after migration |

## Security Considerations

- **Database Backup**: Always backup before production migration
- **Credentials**: Migration uses same DB credentials as application
- **SQL Injection**: Alembic uses parameterized queries (safe)
- **Audit**: Migration creates audit trail in `alembic_version` table

## Next Steps

After completion:
1. **Verify**: Check all repositories load/save correctly
2. **Integration Test**: Run end-to-end interview flow
3. **Proceed**: Move to Phase 3 (Orchestrator Refactoring)
4. **Production Plan**: Document migration rollout strategy
