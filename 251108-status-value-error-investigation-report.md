# Investigation Report: status.value AttributeError

**Date:** 2025-11-08
**Investigator:** Debug Agent
**Issue:** AttributeError at `src/adapters/persistence/mappers.py:157`
**Context:** Post-fix for Question model `use_enum_values` removal

---

## Executive Summary

**Root Cause:** Interview model has `use_enum_values = True` (line 48), causing `status` field to serialize as string instead of `InterviewStatus` enum. Mapper code inconsistently calls `.value` on a string.

**Business Impact:**
- Interview creation/update operations fail with AttributeError
- Database persistence layer broken for Interview entity
- API endpoints returning interview data are affected

**Affected Components:**
- Interview domain model (1 instance)
- InterviewMapper (2 locations)
- Interview REST API routes (7 locations)

**Recommended Action:** Remove `use_enum_values = True` from Interview model Config (same fix as Question model)

---

## Technical Analysis

### 1. Root Cause Identification

**Interview Model Config (src/domain/models/interview.py:45-49):**
```python
class Config:
    """Pydantic configuration."""

    use_enum_values = True  # ← PROBLEM
    frozen = False
```

**Effect:** When `use_enum_values = True`, Pydantic automatically converts:
- `InterviewStatus.PREPARING` → `"preparing"` (string)
- `interview.status` becomes `str`, NOT `InterviewStatus` enum

**Mapper Assumption:** Code at line 157 assumes `status` is enum:
```python
status=domain_model.status.value,  # ← Calls .value on string
```

**Error:** `str` has no `.value` attribute → AttributeError

### 2. Pattern Analysis

**Comparison with Question Model Fix:**
- Question model previously had `use_enum_values = True`
- Removed in recent fix → now returns enum types
- Mappers correctly call `.value` on enums
- Interview model NOT updated → still has config flag

**Mapper Inconsistency:**
- Line 157 (`to_db_model`): Uses `domain_model.status.value` ✗
- Line 171 (`update_db_model`): Uses `domain_model.status` directly ✓
- Line 140 (`to_domain`): Correctly wraps `InterviewStatus(db_model.status)` ✓

### 3. Evidence from Codebase

**Domain Models with use_enum_values:**
```bash
$ grep -r "use_enum_values = True" src/domain/models/
src/domain/models/interview.py:48:        use_enum_values = True
```
Only Interview model affected (Question model already fixed).

**All .status.value Usage:**
1. `src/adapters/persistence/mappers.py:157` - InterviewMapper.to_db_model() ✗
2. `src/adapters/persistence/mappers.py:171` - InterviewMapper.update_db_model() - INCONSISTENT (no .value)
3. `src/adapters/api/rest/interview_routes.py:285` - PlanningStatusResponse ✗
4. `src/adapters/api/rest/interview_routes.py:329-338` - Status comparisons (6 instances) ✗
5. `src/adapters/api/rest/interview_routes.py:342` - PlanningStatusResponse ✗

**Database Model Expectations:**
- SQLAlchemy models store enums as strings in DB
- Mappers must convert enum → string via `.value`
- BUT only when domain model has enum type (NOT when `use_enum_values = True`)

### 4. Timeline of Events

1. **Original State:** Interview model had `use_enum_values = True`, mappers called `.value`
2. **Question Fix:** Question model removed `use_enum_values`, mappers updated
3. **Current State:** Interview model still has flag, mappers still call `.value` → CONFLICT
4. **Error Trigger:** Any interview save/update operation calls line 157

---

## Affected File Locations

### Critical (Breaks Persistence):
1. **src/domain/models/interview.py:48**
   - `use_enum_values = True` in Config
   - Causes status to serialize as string

2. **src/adapters/persistence/mappers.py:157**
   - `status=domain_model.status.value,`
   - Assumes enum, gets string → AttributeError

3. **src/adapters/persistence/mappers.py:171**
   - `db_model.status = domain_model.status`
   - No `.value` call (inconsistent with line 157)

### Secondary (API Layer Issues):
4. **src/adapters/api/rest/interview_routes.py:285**
   - `status=interview.status.value,`
   - Returns PlanningStatusResponse

5. **src/adapters/api/rest/interview_routes.py:329-338**
   - `if interview.status.value == "PREPARING":` (6 comparisons)
   - Status string matching logic

6. **src/adapters/api/rest/interview_routes.py:342**
   - `status=interview.status.value,`
   - Returns PlanningStatusResponse

---

## Solution Approach

### Recommended Fix: Remove use_enum_values (Align with Question Model)

**Primary Change:**
```python
# src/domain/models/interview.py:45-49
class Config:
    """Pydantic configuration."""

    # use_enum_values = True  # ← REMOVE THIS LINE
    frozen = False
```

**Consequences:**
- `interview.status` becomes `InterviewStatus` enum (not string)
- Mapper calls to `.value` become VALID
- API routes calling `.value` become VALID
- Aligns with Question model pattern

**Files Requiring NO Changes:**
- `src/adapters/persistence/mappers.py:157` - Already calls `.value` ✓
- `src/adapters/api/rest/interview_routes.py` - Already calls `.value` ✓

**Files Requiring Update:**
- `src/adapters/persistence/mappers.py:171` - Should add `.value`:
  ```python
  db_model.status = domain_model.status.value  # Add .value
  ```

### Alternative Fix: Keep use_enum_values (NOT Recommended)

If keeping `use_enum_values = True`, must REMOVE all `.value` calls:
- Lines: 157, 171, 285, 329-338, 342
- Makes code inconsistent with Question model
- Loses type safety benefits

---

## Supporting Evidence

### Mapper Code Context (Lines 152-179)

```python
@staticmethod
def to_db_model(domain_model: Interview) -> InterviewModel:
    """Convert domain model to database model."""
    return InterviewModel(
        id=domain_model.id,
        candidate_id=domain_model.candidate_id,
        status=domain_model.status.value,  # LINE 157 - ERROR HERE
        cv_analysis_id=domain_model.cv_analysis_id,
        question_ids=domain_model.question_ids,
        answer_ids=domain_model.answer_ids,
        current_question_index=domain_model.current_question_index,
        started_at=domain_model.started_at,
        completed_at=domain_model.completed_at,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
    )

@staticmethod
def update_db_model(db_model: InterviewModel, domain_model: Interview) -> None:
    """Update database model from domain model."""
    db_model.status = domain_model.status  # LINE 171 - INCONSISTENT (no .value)
    db_model.cv_analysis_id = domain_model.cv_analysis_id
    # ... rest of fields
```

### Question Model Pattern (Post-Fix)

```python
# src/domain/models/question.py:51-54
class Config:
    """Pydantic configuration."""

    pass  # ← No use_enum_values

# src/adapters/persistence/mappers.py:104-105
question_type=domain_model.question_type.value,  # ✓ Works because enum
difficulty=domain_model.difficulty.value,        # ✓ Works because enum
```

---

## Risk Assessment

**Immediate Risk (High):**
- All interview create/update operations FAIL
- API endpoints `/interview/plan` and `/{id}/plan` broken
- Database persistence completely blocked

**Fix Risk (Low):**
- Removing `use_enum_values` is safe (proven by Question model fix)
- Existing code already expects enum + `.value` pattern
- Only line 171 needs update (add `.value`)

**Rollback Risk (None):**
- Config change is reversible
- No database migration required (still stores strings)

---

## Actionable Recommendations

### Priority 1 (Critical - Fix Immediately):
1. Remove `use_enum_values = True` from `src/domain/models/interview.py:48`
2. Update `src/adapters/persistence/mappers.py:171`:
   - Change: `db_model.status = domain_model.status`
   - To: `db_model.status = domain_model.status.value`

### Priority 2 (Verification):
3. Run unit tests for InterviewMapper
4. Test interview creation via API
5. Verify status transitions (start, complete, cancel methods)

### Priority 3 (Code Quality):
6. Add type hints to catch this earlier:
   ```python
   def to_db_model(domain_model: Interview) -> InterviewModel:
       status: str = domain_model.status.value  # Explicit type
   ```

### Priority 4 (Prevention):
7. Document enum handling pattern in `docs/code-standards.md`
8. Add linter rule to detect `use_enum_values` in domain models
9. Create test suite for all mappers with enum fields

---

## Unresolved Questions

1. **Migration Path:** Are there any database records with malformed status values?
2. **API Contracts:** Do external clients expect string status or enum object?
3. **Serialization:** How does FastAPI serialize InterviewStatus enums in responses?
4. **Test Coverage:** Why didn't tests catch this inconsistency between line 157 and 171?

---

## Appendix: Full Context

### InterviewStatus Enum Definition
```python
# src/domain/models/interview.py:11-18
class InterviewStatus(str, Enum):
    """Interview status enumeration."""

    PREPARING = "preparing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

### API Route Usage Example
```python
# src/adapters/api/rest/interview_routes.py:329-338
if interview.status.value == "PREPARING":
    message = "Interview planning in progress..."
elif interview.status.value == "READY":
    message = f"Interview ready with {interview.planned_question_count} questions"
# ... etc
```

---

**End of Report**
