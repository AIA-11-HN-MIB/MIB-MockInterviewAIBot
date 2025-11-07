# Phase 3: Test Infrastructure Updates

## Context

Test suite needs updating to use new CV and Analytics mocks via DI container. Currently tests may instantiate adapters manually. Should use container for consistency.

Repositories will use real PostgreSQL adapters in tests (not mocked).

## Overview

Update test infrastructure to:
1. Add container fixture with mock mode enabled
2. Create test utilities for CV/Analytics mocking
3. Update existing tests to use DI container
4. Add mock data factories for realistic test entities
5. Ensure backward compatibility

## Key Insights

- conftest.py has existing fixtures for test entities
- Tests should use container to get adapters (consistency)
- Real DB repositories in tests (integration testing)
- Need consistent way to get mocks across tests

## Requirements

### Fixture Updates

Add container fixture for testing with CV/Analytics mocks enabled while using real DB repositories.

### Test Utilities

Create test utilities:
- Entity factories (candidates, questions, interviews, answers)
- Mock data helpers (CV content, skills, analytics metrics)
- Common assertions for domain validation

### Backward Compatibility

Ensure existing tests still work with minimal changes. Add new fixtures alongside existing ones.

## Architecture

Test layers:
- Unit: Mock external services (LLM, Vector, CV, Analytics) via container
- Integration: Real DB + mocked external APIs
- E2E: Minimal mocking

## Related Code Files

Will modify:
- tests/conftest.py (add container fixtures)
- tests/utils/factories.py (create)
- tests/utils/mock_helpers.py (create)

## Implementation Steps

### Step 1: Add Container Fixtures (20 mins)

Open tests/conftest.py and add mock container fixture with adapter fixtures.

### Step 2: Create Test Utilities (30 mins)

Create tests/utils/factories.py with entity creation helpers and tests/utils/mock_helpers.py with mock data generators.

### Step 3: Update Existing Tests (40 mins)

Update tests to use container fixtures instead of manual adapter instantiation.

### Step 4: Add Test Documentation (20 mins)

Create tests/README.md documenting fixtures, utilities, and testing strategy.

### Step 5: Validation (20 mins)

Run full test suite, check coverage, verify no failures, ensure type checking passes.

## TODO

- [ ] Add mock_container fixture to conftest.py
- [ ] Add cv_analyzer and analytics fixtures
- [ ] Create tests/utils/factories.py
- [ ] Create tests/utils/mock_helpers.py
- [ ] Update existing tests to use container
- [ ] Create tests/README.md
- [ ] Run full test suite
- [ ] Check test coverage
- [ ] Verify type checking

## Success Criteria

- [ ] All tests use container for adapter access
- [ ] Test utilities available for common patterns
- [ ] Full test suite passes
- [ ] Test coverage maintained or improved
- [ ] Type checking passes
- [ ] Test documentation complete

## Risk Assessment

Low Risk:
- Additive changes (new fixtures, utilities)
- Existing tests should continue working
- Real DB testing maintained

Mitigations:
- Run tests after each change
- Keep old fixtures temporarily for backward compat
- Document migration path

## Security Considerations

Test isolation:
- Each test should use fresh mock instances
- Real DB tests should use transactions (rollback after test)
- No shared state between tests

Mock data:
- Use realistic but non-sensitive test data
- Do not commit real CVs or personal info
- Document test data sources

## Next Steps

After completion:
1. Proceed to Phase 4 (Documentation & Examples)
2. Update CI/CD to use mock mode
3. Consider adding performance benchmarks

## Unresolved Questions

1. Should integration tests use test DB or in-memory DB? (Test DB for realism)
2. How to handle DB migrations in tests? (Run migrations in test setup)
