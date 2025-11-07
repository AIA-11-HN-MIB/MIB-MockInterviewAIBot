# Phase 5: Documentation & Examples

## Context

Phases 1-4 created comprehensive mock infrastructure. Must document for developers: when to use mocks, how to create tests, mock behavior details, troubleshooting.

Documentation scattered (CLAUDE.md, README, code comments). Need centralized guide.

## Overview

Create documentation covering:
1. Mock adapter guide (what, when, why)
2. Testing patterns and examples
3. Mock behavior reference (each adapter)
4. Configuration guide
5. Troubleshooting common issues

Update existing docs (README, CLAUDE.md) with mock references.

## Key Insights

- Developers need quick start (copy-paste examples)
- Mock limitations must be clear (vs real adapters)
- Configuration options (USE_MOCK_ADAPTERS, mixed mode)
- CI/CD integration patterns

## Requirements

### New Documentation Files

**`docs/testing-guide.md`**:
- Introduction to test infrastructure
- Using mocks vs real adapters
- Writing unit tests with mocks
- Writing integration tests
- Test data factories
- Custom assertions

**`docs/mock-adapters.md`**:
- Overview of all mock adapters
- When to use each mock
- Mock behavior details (data patterns, edge cases)
- Limitations and differences from real adapters
- Configuration options

**Code examples**:
- Unit test template
- Integration test template
- Use case test with full mocking
- Mixed mode test (mock LLM, real DB)

### Updates to Existing Docs

**README.md**:
- Add "Testing" section
- Quick start with mocks (no API keys)
- Link to testing-guide.md

**CLAUDE.md**:
- Update "Testing Strategy" section
- Add mock adapter usage
- Link to mock-adapters.md

**Database_SETUP.md**:
- Note: mocks don't need DB (optional for tests)

## Architecture

**Documentation structure**:
```
docs/
├── testing-guide.md  # NEW: comprehensive test guide
├── mock-adapters.md  # NEW: mock adapter reference
└── (existing docs)

tests/
├── README.md  # NEW: quick reference
└── examples/
    ├── test_unit_example.py  # NEW
    ├── test_integration_example.py  # NEW
    └── test_mixed_mode.py  # NEW
```

## Related Code Files

**Will create**:
- `docs/testing-guide.md`
- `docs/mock-adapters.md`
- `tests/README.md`
- `tests/examples/test_unit_example.py`
- `tests/examples/test_integration_example.py`
- `tests/examples/test_mixed_mode.py`

**Will modify**:
- `README.md` (add Testing section)
- `CLAUDE.md` (update Testing Strategy)
- `.env.example` (add comments for mock mode)

## Implementation Steps

### Step 1: Create Testing Guide (90 mins)

1. Create `docs/testing-guide.md` with sections:

**Introduction** (15 mins):
- Overview of test infrastructure
- Test types (unit, integration, e2e)
- Mock vs real adapters decision tree

**Quick Start** (20 mins):
```markdown
## Quick Start

### Running Tests with Mocks

1. Set environment variable:
   ```bash
   export USE_MOCK_ADAPTERS=true
   ```

2. Run tests:
   ```bash
   pytest tests/unit/
   ```

### Writing Your First Test

```python
import pytest
from tests.utils.factories import create_sample_candidate

def test_example(mock_container):
    # Get mock repository from container
    repo = mock_container.candidate_repository_port()

    # Create test data
    candidate = create_sample_candidate()

    # Test use case
    saved = await repo.save(candidate)
    assert saved.id == candidate.id
```
```

**Unit Testing Patterns** (30 mins):
- Testing domain models (no mocks needed)
- Testing use cases with mocked ports
- Testing adapters in isolation
- Mock data strategies

**Integration Testing Patterns** (25 mins):
- Testing with real DB, mock external services
- Testing API endpoints
- WebSocket testing
- Mixed mode testing

### Step 2: Create Mock Adapter Reference (60 mins)

1. Create `docs/mock-adapters.md`:

**Overview** (10 mins):
- What are mock adapters
- Benefits (speed, cost, isolation)
- When to use mocks vs real

**Adapter Details** (50 mins, 5 min each):

For each adapter (LLM, Vector, CV, Analytics, STT, TTS, 5 repos):

```markdown
### MockLLMAdapter

**Interface**: `LLMPort`

**Behavior**:
- `generate_question()`: Returns formatted question based on skill/difficulty
- `evaluate_answer()`: Scores 70-95 based on answer length
- `generate_feedback_report()`: Returns template report with avg scores
- `summarize_cv()`: Returns generic summary
- `extract_skills_from_text()`: Returns 3 hardcoded skills

**Mock Data Patterns**:
- Scores: Random 70-95 (realistic range)
- Sentiment: "confident" (>85), "positive" (75-85), "uncertain" (<75)
- Strengths/Weaknesses: 2-4 items each

**Limitations**:
- Not context-aware (doesn't analyze actual content)
- Fixed skill extraction (doesn't parse text)
- No retry/rate limiting logic

**Configuration**: None (no API key needed)

**Example**:
```python
mock_llm = MockLLMAdapter()
eval = await mock_llm.evaluate_answer(question, "My answer", {})
assert 70 <= eval.score <= 95
```
```

Repeat for all 12 adapters.

### Step 3: Create Example Tests (75 mins)

1. **Unit test example** (25 mins):
   Create `tests/examples/test_unit_example.py`:
   ```python
   """Example unit test using mock adapters."""
   import pytest
   from tests.utils.factories import create_sample_question, create_sample_candidate
   from src.application.use_cases.process_answer import ProcessAnswerUseCase

   @pytest.mark.asyncio
   async def test_process_answer_use_case(
       mock_container,
       mock_question_repo,
       mock_interview_repo,
       mock_answer_repo,
       mock_llm,
   ):
       """Test ProcessAnswerUseCase with all mocks."""
       # Setup test data
       question = create_sample_question()
       await mock_question_repo.save(question)

       # Create use case
       use_case = ProcessAnswerUseCase(
           question_repo=mock_question_repo,
           interview_repo=mock_interview_repo,
           answer_repo=mock_answer_repo,
           llm=mock_llm,
       )

       # Execute
       result = await use_case.execute(...)

       # Assert
       assert result.answer.is_evaluated()
       assert 70 <= result.answer.evaluation.score <= 95
   ```

2. **Integration test example** (25 mins):
   Create `tests/examples/test_integration_example.py`:
   ```python
   """Example integration test with real DB and mock services."""
   import pytest
   from sqlalchemy.ext.asyncio import AsyncSession
   from src.infrastructure.dependency_injection.container import Container

   @pytest.mark.asyncio
   async def test_interview_flow_integration(
       db_session: AsyncSession,  # Real database
       mock_settings: Settings,   # Mocks enabled
   ):
       """Test full interview flow with real DB, mock LLM."""
       # Container with mock LLM but real DB
       container = Container(mock_settings)

       # Get real repository (with session)
       candidate_repo = container.candidate_repository_port(db_session)

       # Test flow
       candidate = create_sample_candidate()
       saved = await candidate_repo.save(candidate)

       # Verify in DB
       found = await candidate_repo.get_by_id(saved.id)
       assert found is not None
   ```

3. **Mixed mode example** (25 mins):
   Create `tests/examples/test_mixed_mode.py`:
   ```python
   """Example mixed mode: mock LLM, real database, real vector DB."""

   @pytest.fixture
   def mixed_settings() -> Settings:
       return Settings(
           use_mock_adapters=False,  # Don't mock everything
           llm_provider="mock",       # But mock LLM specifically
           vector_db_provider="pinecone",  # Real vector DB
       )

   # ... test implementation
   ```

### Step 4: Update README.md (30 mins)

1. Open `README.md`
2. Find "## 🧪 Development" section (line ~243)
3. Add subsection after "Running Tests":

```markdown
### Testing with Mock Adapters

For fast testing without external API calls:

```bash
# Enable mock mode
export USE_MOCK_ADAPTERS=true

# Run tests (no API keys needed)
pytest tests/unit/

# Run specific test
pytest tests/unit/use_cases/test_process_answer.py -v
```

**Benefits**:
- ⚡ 10x faster (no network calls)
- 💰 Zero API costs
- 🔒 No credentials needed
- ✅ Deterministic results

See [Testing Guide](docs/testing-guide.md) for details.
```

4. Update "Quick Start" section (line ~134) with mock option:
```markdown
### ⚡ 5-Minute Setup (Mock Mode)

**Want to try without API keys?**

```bash
# Setup and run with mocks
python -m venv venv && venv\Scripts\activate && pip install -e ".[dev]"
export USE_MOCK_ADAPTERS=true
pytest tests/unit/  # All tests pass, no setup needed!
```
```

### Step 5: Update CLAUDE.md (20 mins)

1. Open `CLAUDE.md`
2. Find "Testing Strategy" section (line ~577)
3. Update with mock adapter info:

```markdown
### Testing Strategy

**Unit Tests** (`tests/unit/`) ⏳:
- Test domain logic in isolation
- **Use mock adapters via `USE_MOCK_ADAPTERS=true`**
- Fast execution (<5 seconds)
- Target coverage: >80%

**Integration Tests** (`tests/integration/`) ⏳:
- Test adapters with real services (or mocks)
- Use test environments for external APIs
- Verify port implementations
- Mixed mode: mock LLM, real DB

**Mock Adapters**:
- 12 mock implementations (LLM, Vector DB, Repositories, etc.)
- Enabled via `use_mock_adapters` setting
- See [Mock Adapter Reference](docs/mock-adapters.md)

**Example**:
```python
# conftest.py provides mock fixtures
def test_use_case(mock_container):
    use_case = AnalyzeCVUseCase(
        cv_analyzer=mock_container.cv_analyzer_port(),
        llm=mock_container.llm_port(),
    )
    # Test without external calls
```
```

### Step 6: Create tests/README.md (30 mins)

1. Create `tests/README.md`:

```markdown
# Test Infrastructure

Quick reference for writing tests in Elios AI Interview Service.

## Directory Structure

```
tests/
├── conftest.py          # Global fixtures (mocks, sample data)
├── utils/
│   ├── factories.py     # Entity creation helpers
│   └── assertions.py    # Custom assertions
├── unit/                # Unit tests (fast, isolated)
├── integration/         # Integration tests (with DB/APIs)
├── e2e/                 # End-to-end tests
└── examples/            # Example test patterns
```

## Quick Start

### Run All Tests
```bash
pytest
```

### Run with Mock Adapters (Fast)
```bash
export USE_MOCK_ADAPTERS=true
pytest tests/unit/
```

### Run Specific Test
```bash
pytest tests/unit/use_cases/test_process_answer.py::test_specific -v
```

## Common Fixtures

Available in all tests via `conftest.py`:

- `mock_container`: DI container with all mocks
- `mock_llm`: Mock LLM adapter
- `mock_question_repo`: Mock question repository
- `sample_cv_analysis`: Sample CVAnalysis entity
- `sample_question`: Sample Question entity

See `conftest.py` for full list.

## Example Tests

See `tests/examples/` for:
- Unit test template
- Integration test template
- Mixed mode testing

## Documentation

- [Testing Guide](../docs/testing-guide.md) - Comprehensive guide
- [Mock Adapters](../docs/mock-adapters.md) - Mock behavior reference
```

### Step 7: Add Inline Documentation (45 mins)

Add docstrings to mock adapters explaining behavior:

1. **MockLLMAdapter** (`mock_llm_adapter.py`):
   ```python
   class MockLLMAdapter(LLMPort):
       """Mock LLM adapter for testing without API calls.

       Behavior:
       - Scores answers 70-95 based on length
       - Sentiment varies by score threshold
       - Returns realistic but deterministic data

       Limitations:
       - Not context-aware (doesn't analyze actual content)
       - No retry or rate limiting

       Example:
           >>> mock_llm = MockLLMAdapter()
           >>> eval = await mock_llm.evaluate_answer(question, "answer", {})
           >>> assert 70 <= eval.score <= 95
       """
   ```

2. Repeat for all 12 mock adapters (5 mins each)

## TODO

- [ ] Create docs/testing-guide.md with 4 sections
- [ ] Write Quick Start section
- [ ] Write Unit Testing Patterns section
- [ ] Write Integration Testing Patterns section
- [ ] Create docs/mock-adapters.md
- [ ] Document all 12 mock adapters (behavior, limitations)
- [ ] Create test_unit_example.py
- [ ] Create test_integration_example.py
- [ ] Create test_mixed_mode.py
- [ ] Update README.md Testing section
- [ ] Update README.md Quick Start with mock option
- [ ] Update CLAUDE.md Testing Strategy
- [ ] Create tests/README.md quick reference
- [ ] Add docstrings to all mock adapters
- [ ] Review all docs for consistency
- [ ] Test code examples (copy-paste and run)

## Success Criteria

- [ ] Comprehensive testing-guide.md (>1000 words)
- [ ] Complete mock-adapters.md reference
- [ ] 3 working example tests
- [ ] README.md updated with mock testing
- [ ] CLAUDE.md updated with mock strategy
- [ ] tests/README.md quick reference created
- [ ] All mock adapters have detailed docstrings
- [ ] Code examples tested and working

## Risk Assessment

**Low Risk**: Documentation only

**Quality Checks**:
- Verify code examples actually work
- Check links between docs
- Ensure examples copy-paste cleanly

## Security Considerations

Document security implications:
- Mock mode bypasses auth (dev/test only)
- Don't commit USE_MOCK_ADAPTERS=true in prod configs

## Next Steps

After completion:
1. Project ready for full mock-based development
2. CI/CD can use mocks for fast tests
3. New developers can start without API keys

## Unresolved Questions

1. Video tutorials needed? (Defer: written docs sufficient for now)
2. API documentation generation (Swagger)? (Separate task)
3. Performance benchmarks (mock vs real)? (Optional: add if requested)
