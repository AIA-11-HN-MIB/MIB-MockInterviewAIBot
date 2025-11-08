# Phase 06: Testing & Validation

**Phase ID**: phase-06-testing-validation
**Created**: 2025-11-06
**Status**: ⏳ Pending
**Priority**: P1 (High)
**Estimated Effort**: 10 hours

## Context

**Parent Plan**: [Main Plan](./plan.md)
**Dependencies**: All previous phases (01-05)
**Related Docs**: [Testing Standards](../../docs/code-standards.md#testing-standards)

## Overview

Comprehensive testing strategy: unit tests (domain + use cases), integration tests (DB + LLM + Pinecone), E2E tests (full adaptive flow via API). Ensure >80% coverage, validate performance targets, test error scenarios.

**Date**: 2025-11-06
**Description**: Test suite for adaptive interview planning feature
**Priority**: P1 - Quality assurance
**Status**: ⏳ Pending

## Requirements

### Functional Requirements

1. **Unit Tests** (>80% coverage):
   - Domain models (Question, Interview, Answer)
   - Use cases (PlanInterview, EvaluateAnswerAdaptive)
   - Helpers (n-calculation, similarity, gap detection)
   - Mock all external dependencies (LLM, DB, Vector)

2. **Integration Tests**:
   - Database operations (migration + CRUD)
   - LLM adapter (real API calls with test keys)
   - Vector adapter (real Pinecone with test index)
   - Full planning flow (DB + LLM)
   - Full evaluation flow (DB + LLM + Vector)

3. **E2E Tests**:
   - Complete adaptive interview via REST API
   - Complete adaptive interview via WebSocket
   - Follow-up generation + delivery
   - Max 3 follow-ups enforcement
   - Backward compatibility with non-planned interviews

### Non-Functional Requirements

- Test suite runs in <5 minutes (unit) + <15 minutes (integration)
- Coverage >80% for new code
- All tests pass on clean DB + staging environment
- Performance validated (planning <90s, evaluation <5s)

## Architecture

### Test Pyramid

```
           ┌─────────────┐
           │  E2E Tests  │  (5 tests, full system)
           │    5%       │
           └─────────────┘
         ┌─────────────────┐
         │ Integration Tests│  (20 tests, real adapters)
         │       15%        │
         └─────────────────┘
     ┌───────────────────────┐
     │     Unit Tests        │  (100+ tests, mocked)
     │         80%           │
     └───────────────────────┘
```

### Test Organization

```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_question_planning.py
│   │   ├── test_interview_planning.py
│   │   └── test_answer_evaluation.py
│   ├── use_cases/
│   │   ├── test_plan_interview.py
│   │   └── test_evaluate_answer_adaptive.py
│   └── helpers/
│       ├── test_similarity.py
│       └── test_gap_detection.py
├── integration/
│   ├── test_planning_migration.py
│   ├── test_plan_interview_integration.py
│   ├── test_adaptive_evaluation_integration.py
│   └── test_openai_adapter.py
└── e2e/
    ├── test_adaptive_interview_rest.py
    └── test_adaptive_interview_websocket.py
```

## Implementation Steps

### Step 1: Unit Tests for Domain Models (90 min)

**Files**: Already created in Phase 01
- `tests/unit/domain/test_question_planning.py`
- `tests/unit/domain/test_interview_planning.py`
- `tests/unit/domain/test_answer_evaluation.py`

**Coverage**:
- Question: has_ideal_answer(), is_adaptive_followup(), is_planned()
- Interview: add_adaptive_followup(), is_planned(), planned_question_count()
- Answer: has_similarity_score(), has_gaps(), meets_threshold(), is_adaptive_complete()

### Step 2: Unit Tests for Use Cases (120 min)

**File**: `tests/unit/use_cases/test_plan_interview.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

@pytest.fixture
def mock_dependencies():
    return {
        "llm": AsyncMock(),
        "cv_repo": AsyncMock(),
        "interview_repo": AsyncMock(),
        "question_repo": AsyncMock(),
    }

async def test_calculate_question_count_junior(mock_dependencies):
    """Test n=5 for junior (0-2 yrs, <5 skills)."""
    # Test implementation from Phase 03

async def test_calculate_question_count_senior(mock_dependencies):
    """Test n=12 for senior (5+ yrs, 10+ skills)."""
    pass

async def test_execute_generates_correct_number(mock_dependencies):
    """Test that execute generates n questions."""
    pass

async def test_execute_stores_plan_metadata(mock_dependencies):
    """Test plan_metadata structure."""
    pass

async def test_execute_rollback_on_failure(mock_dependencies):
    """Test that partial generation triggers cleanup."""
    pass

# 15+ more tests...
```

**File**: `tests/unit/use_cases/test_evaluate_answer_adaptive.py`

```python
async def test_similarity_calculation():
    """Test cosine similarity with known embeddings."""
    pass

async def test_gap_detection_identifies_missing_keywords():
    """Test keyword-based gap detection."""
    pass

async def test_should_generate_followup_low_similarity():
    """Test followup triggered when similarity <0.8."""
    pass

async def test_should_generate_followup_max_3():
    """Test followup stops at 3."""
    pass

async def test_execute_stores_adaptive_fields():
    """Test Answer has similarity/gaps/speaking."""
    pass

# 20+ more tests...
```

### Step 3: Integration Tests (120 min)

**File**: `tests/integration/test_plan_interview_integration.py`

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.use_cases.plan_interview import PlanInterviewUseCase
from src.adapters.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.database.session import get_async_session

@pytest.mark.integration
async def test_plan_interview_with_real_llm():
    """Integration test with real OpenAI API."""
    async with get_async_session() as session:
        # Setup: Create CV analysis
        cv_analysis = CVAnalysis(...)
        await cv_repo.save(cv_analysis)

        # Execute: Plan interview
        llm = OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))
        use_case = PlanInterviewUseCase(llm, cv_repo, interview_repo, question_repo)

        interview = await use_case.execute(cv_analysis.id, candidate_id)

        # Assert: Verify results
        assert interview.status == InterviewStatus.READY
        assert len(interview.question_ids) >= 5
        assert interview.plan_metadata["n"] >= 5

        # Verify questions have ideal answers
        for q_id in interview.question_ids:
            question = await question_repo.find_by_id(q_id)
            assert question.has_ideal_answer()
            assert question.rationale is not None

@pytest.mark.integration
async def test_adaptive_evaluation_with_real_pinecone():
    """Integration test with real Pinecone vector search."""
    # Test similarity calculation with real embeddings
    pass

# 10+ more integration tests...
```

### Step 4: E2E Tests (90 min)

**File**: `tests/e2e/test_adaptive_interview_rest.py`

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.e2e
async def test_full_adaptive_interview_rest():
    """E2E test: Full adaptive interview via REST API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Upload CV
        cv_upload = await client.post("/api/cv/upload", files={"file": cv_file})
        cv_id = cv_upload.json()["id"]

        # Step 2: Plan interview
        plan_response = await client.post("/api/interviews/plan", json={
            "candidate_id": str(candidate_id),
            "cv_analysis_id": cv_id,
        })
        assert plan_response.status_code == 202
        interview_id = plan_response.json()["interview_id"]

        # Step 3: Wait for planning (or poll status)
        # For MVP: Synchronous, no wait needed

        # Step 4: Get plan status
        plan_status = await client.get(f"/api/interviews/{interview_id}/plan")
        assert plan_status.json()["status"] == "ready"
        assert plan_status.json()["question_count"] >= 5

        # Step 5: Start interview
        start_response = await client.put(f"/api/interviews/{interview_id}/start")
        assert start_response.status_code == 200

        # Step 6: Get first question
        current_q = await client.get(f"/api/interviews/{interview_id}/questions/current")
        question_id = current_q.json()["id"]

        # Step 7: Submit answer (triggers evaluation + possible follow-up)
        answer_response = await client.post(
            f"/api/interviews/{interview_id}/answers",
            json={
                "question_id": question_id,
                "answer_text": "Incomplete answer missing key concepts...",
            }
        )
        result = answer_response.json()
        assert "similarity_score" in result
        assert "gaps" in result
        # If similarity <0.8, should trigger follow-up

        # Step 8: Verify follow-up (if triggered)
        if result.get("has_followup"):
            # Get next question (should be follow-up)
            followup_q = await client.get(f"/api/interviews/{interview_id}/questions/current")
            assert followup_q.json()["is_followup"] is True
```

**File**: `tests/e2e/test_adaptive_interview_websocket.py`

```python
@pytest.mark.e2e
async def test_full_adaptive_interview_websocket():
    """E2E test: Full adaptive interview via WebSocket."""
    # Connect to WebSocket
    # Send answers
    # Receive evaluations + follow-ups
    # Verify max 3 follow-ups
    pass
```

### Step 5: Performance Tests (60 min)

**File**: `tests/performance/test_planning_performance.py`

```python
import pytest
import time

@pytest.mark.performance
async def test_planning_time_within_90s():
    """Verify planning completes in <90s for n=12."""
    start = time.time()

    # Plan interview with senior CV (n=12)
    interview = await plan_use_case.execute(cv_id, candidate_id)

    elapsed = time.time() - start

    assert elapsed < 90.0, f"Planning took {elapsed}s, expected <90s"
    assert len(interview.question_ids) == 12

@pytest.mark.performance
async def test_evaluation_time_within_5s():
    """Verify evaluation completes in <5s."""
    start = time.time()

    answer, has_followup = await evaluate_use_case.execute(
        interview_id, question_id, "My answer..."
    )

    elapsed = time.time() - start

    assert elapsed < 5.0, f"Evaluation took {elapsed}s, expected <5s"
```

## Todo List

### Unit Tests
- [ ] Write 15+ tests for PlanInterviewUseCase
- [ ] Write 20+ tests for EvaluateAnswerAdaptiveUseCase
- [ ] Write 10+ tests for domain model new methods
- [ ] Write tests for similarity calculation
- [ ] Write tests for gap detection
- [ ] Write tests for follow-up decision logic
- [ ] Mock all external dependencies
- [ ] Run: `pytest tests/unit/ -v --cov=src`
- [ ] Verify coverage >80%

### Integration Tests
- [ ] Test planning with real OpenAI API
- [ ] Test evaluation with real Pinecone
- [ ] Test database migration forward/backward
- [ ] Test full planning flow (DB + LLM)
- [ ] Test full evaluation flow (DB + LLM + Vector)
- [ ] Test error scenarios (LLM failures, DB errors)
- [ ] Run: `pytest tests/integration/ -v -m integration`
- [ ] Verify all pass on staging

### E2E Tests
- [ ] Write E2E test for REST API adaptive flow
- [ ] Write E2E test for WebSocket adaptive flow
- [ ] Test max 3 follow-ups enforcement
- [ ] Test backward compatibility (non-planned interviews)
- [ ] Test complete interview lifecycle
- [ ] Run: `pytest tests/e2e/ -v -m e2e`
- [ ] Verify all pass end-to-end

### Performance Tests
- [ ] Test planning time <90s (n=12)
- [ ] Test evaluation time <5s
- [ ] Test follow-up generation time <3s
- [ ] Test concurrent interviews (10+ simultaneous)
- [ ] Run: `pytest tests/performance/ -v -m performance`

### Test Infrastructure
- [ ] Setup pytest fixtures for common mocks
- [ ] Setup test database (separate from dev)
- [ ] Setup test Pinecone index
- [ ] Setup CI/CD test pipeline
- [ ] Add test coverage reporting (htmlcov/)
- [ ] Document test execution in README

## Success Criteria

- [ ] Unit test coverage >80% for new code
- [ ] All unit tests pass (<5 min runtime)
- [ ] All integration tests pass (<15 min runtime)
- [ ] All E2E tests pass (<10 min runtime)
- [ ] Performance tests validate targets (<90s planning, <5s evaluation)
- [ ] No breaking changes to existing tests
- [ ] CI/CD pipeline green
- [ ] Test documentation complete

## Risk Assessment

**Low Risk**: Comprehensive testing reduces deployment risk

**Potential Issues**:
- Flaky integration tests (LLM API failures)
  - *Mitigation*: Retry logic + test-specific API keys with rate limits
- E2E tests timeout on slow environments
  - *Mitigation*: Increase timeouts, mock expensive operations

## Security Considerations

- Test API keys separate from production
- Test data sanitized (no real PII)
- Integration tests use isolated Pinecone index

## Next Steps

1. Complete all checkboxes
2. Run full test suite locally
3. Run test suite on CI/CD
4. Fix any failing tests
5. **Production Deployment**: After all phases pass

---

**Phase Status**: Final validation phase
**Blocking**: Production deployment
**Owner**: QA + dev team
