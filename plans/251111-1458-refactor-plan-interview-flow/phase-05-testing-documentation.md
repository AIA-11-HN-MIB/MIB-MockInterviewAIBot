# Phase 5: Comprehensive Testing & Documentation

**Date**: 2025-11-11
**Status**: Pending
**Priority**: High
**Implementation Status**: Not Started
**Review Status**: Pending

## Context

**Parent Plan**: [Refactor Plan Interview Flow](./plan.md)
**Previous Phase**: [Phase 4: Unified API Endpoint](./phase-04-unified-api-endpoint.md)
**Related Docs**:
- All previous phases
- [Code Standards](../../docs/code-standards.md)
- [System Architecture](../../docs/system-architecture.md)

## Overview

Comprehensive testing strategy covering unit, integration, and end-to-end tests. Update documentation to reflect new vector search integration and unified API endpoint.

**Duration**: 2 days
**Estimated Completion**: 2025-11-20

## Key Insights

### Testing Coverage Goals

**Current Coverage**: ~70% (unit tests with mock adapters)
**Target Coverage**: >80% overall

**Areas Needing Tests**:
1. Vector search integration in PlanInterviewUseCase
2. Exemplar-based question generation (LLM adapters)
3. Unified CV upload endpoint
4. Error handling and fallback scenarios
5. Integration tests with real adapters

### Documentation Updates Required

**Files to Update**:
1. `README.md` - Add unified endpoint usage
2. `docs/system-architecture.md` - Document vector search flow
3. `docs/codebase-summary.md` - Update component descriptions
4. `CHANGELOG.md` - Version bump and feature list
5. API documentation (Swagger/OpenAPI) - Auto-generated

## Requirements

### Functional Requirements

1. **Unit Tests**
   - Test all new helper methods
   - Test error scenarios
   - Test fallback logic
   - Mock all external dependencies
   - Target: >80% code coverage

2. **Integration Tests**
   - Test with real Pinecone adapter
   - Test with real OpenAI adapter
   - Test end-to-end CV upload flow
   - Verify embeddings stored correctly
   - Measure performance

3. **End-to-End Tests**
   - Test complete user journey
   - CV upload → analysis → planning → interview
   - Test with sample CV files
   - Verify database state

4. **Documentation**
   - API endpoint documentation
   - Architecture updates
   - Code examples
   - Troubleshooting guide

### Non-Functional Requirements

1. **Test Performance**
   - Unit tests: <5 seconds total
   - Integration tests: <2 minutes total
   - Fast feedback loop

2. **Test Reliability**
   - Deterministic results with mocks
   - Minimal flakiness
   - Clear failure messages

3. **Documentation Quality**
   - Clear examples
   - Up-to-date diagrams
   - Concise explanations

## Architecture

### Test Structure

```
tests/
├── unit/
│   ├── use_cases/
│   │   └── test_plan_interview.py (MAJOR UPDATE)
│   ├── adapters/
│   │   ├── test_openai_adapter.py (UPDATE)
│   │   └── test_mock_llm_adapter.py (UPDATE)
│   └── api/
│       └── test_interview_routes.py (UPDATE)
├── integration/
│   ├── test_plan_interview_integration.py (NEW)
│   ├── test_cv_upload_flow.py (NEW)
│   └── test_vector_search_integration.py (NEW)
└── e2e/
    └── test_full_interview_flow.py (NEW)
```

### Test Configuration

**pytest.ini** (in pyproject.toml):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term",
]
markers = [
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests (requires API keys)",
    "e2e: End-to-end tests (full flow)",
]
```

**Run Commands**:
```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests (requires API keys)
USE_MOCK_ADAPTERS=false pytest -m integration

# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html
```

## Related Code Files

### Test Files (CREATE/UPDATE)

**Unit Tests**:
- `tests/unit/use_cases/test_plan_interview.py` (MAJOR UPDATE)
- `tests/unit/adapters/test_openai_adapter.py` (UPDATE)
- `tests/unit/adapters/test_mock_llm_adapter.py` (UPDATE)
- `tests/unit/api/test_interview_routes.py` (UPDATE)

**Integration Tests**:
- `tests/integration/test_plan_interview_integration.py` (NEW)
- `tests/integration/test_cv_upload_flow.py` (NEW)
- `tests/integration/test_vector_search_integration.py` (NEW)

**E2E Tests**:
- `tests/e2e/test_full_interview_flow.py` (NEW)

### Documentation Files (UPDATE)

- `README.md` (UPDATE - add unified endpoint)
- `docs/system-architecture.md` (UPDATE - vector search flow)
- `docs/codebase-summary.md` (UPDATE - component changes)
- `CHANGELOG.md` (UPDATE - version and features)
- `docs/api-examples.md` (CREATE - usage examples)

### Test Fixtures

- `tests/fixtures/sample_cv.pdf` (CREATE)
- `tests/fixtures/mock_data.py` (UPDATE)

## Implementation Steps

### Step 1: Update Unit Tests - PlanInterviewUseCase
**File**: `tests/unit/use_cases/test_plan_interview.py`

**New Test Cases**:
- [ ] `test_build_search_query_junior()` - Query for junior developer
- [ ] `test_build_search_query_mid()` - Query for mid-level
- [ ] `test_build_search_query_senior()` - Query for senior
- [ ] `test_find_exemplar_questions_success()` - Vector search returns results
- [ ] `test_find_exemplar_questions_empty()` - No exemplars found
- [ ] `test_find_exemplar_questions_error()` - Vector search raises exception
- [ ] `test_find_exemplar_questions_filters()` - Verify filters applied
- [ ] `test_store_question_embedding_success()` - Embedding stored
- [ ] `test_store_question_embedding_failure()` - Non-blocking error
- [ ] `test_execute_with_exemplars()` - Full flow with vector search
- [ ] `test_execute_vector_search_disabled()` - Fallback without exemplars
- [ ] Run: `pytest tests/unit/use_cases/test_plan_interview.py -v`
- [ ] Commit: `test(use-case): comprehensive tests for plan interview with vector search`

### Step 2: Update Unit Tests - LLM Adapters
**Files**: `tests/unit/adapters/test_openai_adapter.py`, `test_mock_llm_adapter.py`

**Test Cases**:
- [ ] `test_generate_question_without_exemplars()` - Backward compatibility
- [ ] `test_generate_question_with_exemplars()` - Exemplar-based generation
- [ ] `test_generate_question_exemplar_limit()` - Limit to 3 exemplars
- [ ] `test_generate_question_empty_exemplars()` - Empty list handling
- [ ] `test_prompt_contains_exemplars()` - Verify prompt content
- [ ] `test_prompt_contains_no_copy_instruction()` - Verify instruction
- [ ] Run: `pytest tests/unit/adapters/test_*_adapter.py -v`
- [ ] Commit: `test(adapters): add tests for exemplar-based generation`

### Step 3: Update Unit Tests - API Routes
**File**: `tests/unit/api/test_interview_routes.py`

**Test Cases**:
- [ ] `test_upload_cv_success()` - Successful upload and planning
- [ ] `test_upload_cv_invalid_type()` - 400 for invalid file
- [ ] `test_upload_cv_too_large()` - 413 for oversized file
- [ ] `test_upload_cv_missing_candidate()` - 422 validation error
- [ ] `test_upload_cv_auto_start()` - Auto-start interview
- [ ] `test_upload_cv_analysis_failure()` - 500 with cleanup
- [ ] `test_upload_cv_planning_failure()` - Rollback scenario
- [ ] `test_file_cleanup_on_error()` - Verify file deleted
- [ ] Run: `pytest tests/unit/api/test_interview_routes.py -v`
- [ ] Commit: `test(api): add tests for unified CV upload endpoint`

### Step 4: Create Integration Tests - Plan Interview
**File**: `tests/integration/test_plan_interview_integration.py`

**Test Cases** (requires API keys):
- [ ] `test_plan_interview_with_real_adapters()` - Real OpenAI + Pinecone
- [ ] `test_vector_search_finds_exemplars()` - Verify exemplars retrieved
- [ ] `test_embeddings_stored_in_pinecone()` - Verify storage
- [ ] `test_generated_questions_differ_from_exemplars()` - Uniqueness
- [ ] `test_performance_within_budget()` - <30s for 5 questions
- [ ] Setup: Seed Pinecone with 50+ exemplar questions
- [ ] Run: `USE_MOCK_ADAPTERS=false pytest tests/integration/ -v`
- [ ] Commit: `test(integration): add plan interview integration tests`

### Step 5: Create Integration Tests - CV Upload Flow
**File**: `tests/integration/test_cv_upload_flow.py`

**Test Cases**:
- [ ] `test_upload_cv_end_to_end()` - Full flow with sample PDF
- [ ] `test_cv_analysis_extracts_skills()` - Verify CV parsing
- [ ] `test_interview_created_with_questions()` - Verify DB state
- [ ] `test_embeddings_stored()` - Verify vector DB
- [ ] `test_performance_end_to_end()` - <90s total
- [ ] Create fixture: `tests/fixtures/sample_cv.pdf`
- [ ] Run: `pytest tests/integration/test_cv_upload_flow.py -v`
- [ ] Commit: `test(integration): add CV upload flow integration tests`

### Step 6: Create E2E Tests - Full Interview Flow
**File**: `tests/e2e/test_full_interview_flow.py`

**Test Scenario**:
```python
async def test_full_interview_flow():
    """Test complete user journey: CV upload → analysis → planning → interview → completion."""
    # 1. Upload CV
    response = await client.post("/api/interview/cv", files={"file": cv_file}, data={"candidate_id": ...})
    interview_id = response.json()["interview_id"]

    # 2. Verify interview ready
    response = await client.get(f"/api/interviews/{interview_id}")
    assert response.json()["status"] == "READY"

    # 3. Start interview
    response = await client.put(f"/api/interviews/{interview_id}/start")
    assert response.json()["status"] == "IN_PROGRESS"

    # 4. Answer questions (WebSocket)
    async with websocket.connect(ws_url) as ws:
        for i in range(question_count):
            question = await ws.receive_json()
            await ws.send_json({"type": "text_answer", "question_id": question["id"], "answer_text": "..."})
            evaluation = await ws.receive_json()
            assert evaluation["type"] == "evaluation"

    # 5. Verify interview complete
    response = await client.get(f"/api/interviews/{interview_id}")
    assert response.json()["status"] == "COMPLETED"
```

- [ ] Implement full flow test
- [ ] Test with mock adapters (fast)
- [ ] Optional: Test with real adapters (slow)
- [ ] Run: `pytest tests/e2e/ -v`
- [ ] Commit: `test(e2e): add full interview flow end-to-end test`

### Step 7: Measure Coverage
- [ ] Run: `pytest --cov=src --cov-report=html`
- [ ] Open: `htmlcov/index.html`
- [ ] Identify uncovered lines
- [ ] Add tests for low-coverage areas
- [ ] Target: >80% coverage
- [ ] Commit: `test: achieve >80% code coverage`

### Step 8: Update README.md
**File**: `README.md`

**Sections to Update**:
- [ ] Add unified CV upload endpoint to "Quick Start"
- [ ] Add example curl command
- [ ] Update feature list
- [ ] Add troubleshooting section
- [ ] Commit: `docs: update README with unified CV upload endpoint`

### Step 9: Update System Architecture
**File**: `docs/system-architecture.md`

**Sections to Update**:
- [ ] Add vector search flow diagram
- [ ] Document exemplar-based question generation
- [ ] Update component interactions
- [ ] Add performance metrics
- [ ] Commit: `docs: document vector search integration in architecture`

### Step 10: Update Codebase Summary
**File**: `docs/codebase-summary.md`

**Sections to Update**:
- [ ] Update use case descriptions
- [ ] Update adapter descriptions
- [ ] Update file statistics
- [ ] Add new endpoints to API section
- [ ] Commit: `docs: update codebase summary with recent changes`

### Step 11: Create API Examples
**File**: `docs/api-examples.md` (NEW)

**Content**:
- [ ] Example: Upload CV and plan interview
- [ ] Example: Start interview
- [ ] Example: Submit answers (REST)
- [ ] Example: Real-time interview (WebSocket)
- [ ] Example: Get feedback report
- [ ] Include request/response samples
- [ ] Commit: `docs: create API examples documentation`

### Step 12: Update CHANGELOG
**File**: `CHANGELOG.md`

**Version**: 0.2.0

**Added**:
- [ ] Vector search integration for exemplar-based question generation
- [ ] Unified CV upload and planning endpoint (POST /api/interview/cv)
- [ ] Exemplar parameter for LLMPort
- [ ] Question embedding storage
- [ ] Comprehensive test suite (>80% coverage)

**Changed**:
- [ ] PlanInterviewUseCase now uses vector search for exemplars
- [ ] OpenAI adapter supports exemplar-based generation
- [ ] LLMPort interface extended with optional exemplars parameter

**Fixed**:
- [ ] N/A (new feature)

- [ ] Commit: `docs: update CHANGELOG for v0.2.0`

## Todo List

- [ ] Update unit tests for PlanInterviewUseCase
- [ ] Update unit tests for LLM adapters
- [ ] Update unit tests for API routes
- [ ] Create integration tests for plan interview
- [ ] Create integration tests for CV upload flow
- [ ] Create E2E tests for full flow
- [ ] Measure and improve code coverage (>80%)
- [ ] Update README.md
- [ ] Update system-architecture.md
- [ ] Update codebase-summary.md
- [ ] Create api-examples.md
- [ ] Update CHANGELOG.md
- [ ] Code review and approval
- [ ] Merge to main branch

## Success Criteria

- [ ] Unit test coverage >80%
- [ ] All unit tests pass (<5s)
- [ ] All integration tests pass (<2min)
- [ ] E2E test verifies full flow
- [ ] README.md updated with examples
- [ ] Architecture docs reflect new design
- [ ] CHANGELOG.md documents changes
- [ ] Code review approved
- [ ] All documentation complete

## Risk Assessment

### Testing Risks

**Risk**: Integration tests flaky due to external APIs
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: Use mock adapters for CI/CD, real adapters optional
- **Strategy**: Retry logic for flaky tests

**Risk**: E2E tests too slow for CI/CD pipeline
- **Likelihood**: High
- **Impact**: Low
- **Mitigation**: Run E2E tests separately, not in pre-commit
- **Target**: Unit tests <5s, integration <2min

**Risk**: Coverage target difficult to achieve
- **Likelihood**: Medium
- **Impact**: Low
- **Mitigation**: Focus on critical paths, document exceptions
- **Acceptance**: 75% minimum, 80% target

### Documentation Risks

**Risk**: Documentation becomes outdated quickly
- **Likelihood**: High
- **Impact**: Medium
- **Mitigation**: Link docs to code, automate where possible
- **Strategy**: Review docs in each PR

**Risk**: API examples don't work
- **Likelihood**: Medium
- **Impact**: High
- **Mitigation**: Test all examples before documenting
- **Validation**: Automated API tests

## Security Considerations

### Test Data
- Sample CVs may contain realistic PII
- **Action**: Use anonymized or fictional CVs
- **Protection**: Never commit real CVs to git

### API Keys in Tests
- Integration tests require real API keys
- **Action**: Use environment variables, CI/CD secrets
- **Protection**: Never commit keys to repository

### Test Database
- Tests may create/delete data
- **Action**: Use separate test database
- **Isolation**: Reset database between tests

## Next Steps

1. **Begin Testing**: Unit tests first (fastest feedback)
2. **Integration Testing**: Real adapters (requires setup)
3. **E2E Testing**: Full flow validation
4. **Documentation**: Update all docs in parallel
5. **Code Review**: Comprehensive review of all changes
6. **Merge**: Merge to main after approval
7. **Release**: Tag v0.2.0 with release notes

## Unresolved Questions

1. **Coverage Target**: Is 80% realistic, or adjust to 75%?
2. **Test Data**: Create comprehensive fixture library?
3. **CI/CD**: Integrate tests into GitHub Actions?
4. **Performance Benchmarks**: Track regression over time?
5. **Documentation**: Auto-generate API docs from OpenAPI spec?

---

**Document Status**: Draft
**Next Review**: Before implementation
**Dependencies**: Phases 2-4 complete
**Completion**: Final phase
