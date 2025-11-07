# Adapter Mock Implementation Plan

**Created**: 2025-11-07 23:39
**Updated**: 2025-11-08 (removed repository mocks)
**Status**: Planning
**Priority**: High (enables testing & dev without external deps)

## Overview

Create mock implementations for CV and Analytics adapters to enable isolated testing, faster dev cycles, and CI/CD reliability. Repository ports will use real PostgreSQL adapters in tests.

## Current State

**Existing Mocks** (4):
- `MockLLMAdapter` ✅ (7 methods, realistic scores)
- `MockSTTAdapter` ✅ (3 methods)
- `MockTTSAdapter` ✅ (3 methods)
- `MockVectorSearchAdapter` ✅ (6 methods, uses seeded question IDs)

**Missing Mocks** (2):
- CVAnalyzerPort (2 methods)
- AnalyticsPort (5 methods)

**Repository Strategy**: Using real PostgreSQL adapters in tests (not mocked)

## Objectives

1. Create production-ready mock adapters for CV and Analytics ports
2. Integrate mocks with DI container via `use_mock_adapters` config flag
3. Update test infrastructure to use consistent mock pattern
4. Document mock data contracts and behavior
5. Enable use case testing without external CV/Analytics services

## Architecture

**DI Container Pattern**:
```python
# Already implemented pattern in container.py:
if self.settings.use_mock_adapters:
    return MockAdapter()
else:
    return RealAdapter()
```

**Mock Data Strategy**:
- Use realistic, predictable data (not random where deterministic needed)
- Return valid domain entities (not raw dicts)
- Simulate common edge cases (not found, validation errors)

## Phases

### [Phase 1: CV Processing & Analytics Mocks](phase-1-cv-analytics-mocks.md)
Create MockCVAnalyzerAdapter and MockAnalyticsAdapter
- **Scope**: 2 adapters, 7 methods total
- **Complexity**: Medium (realistic CV parsing, analytics calculations)
- **Dependencies**: None
- **Duration**: 2-3 hours

### [Phase 2: DI Container Integration](phase-2-di-integration.md)
Wire mocks into container, add config management
- **Scope**: Container updates for CV/Analytics, settings, env vars
- **Complexity**: Low (existing pattern to follow)
- **Dependencies**: Phase 1 complete
- **Duration**: 1 hour

### [Phase 3: Test Infrastructure Updates](phase-3-test-infrastructure.md)
Update tests to use new mocks via DI, create test utilities
- **Scope**: Test updates, helper functions for CV/Analytics mocking
- **Complexity**: Low
- **Dependencies**: Phase 2 complete
- **Duration**: 1-2 hours

### [Phase 4: Documentation & Examples](phase-4-documentation.md)
Document mock behavior, create usage examples
- **Scope**: README updates, code examples, test patterns
- **Complexity**: Low
- **Dependencies**: All phases complete
- **Duration**: 1 hour

## Success Criteria

- [ ] CVAnalyzerPort and AnalyticsPort have mock implementations
- [ ] Mocks integrated with DI container via config flag
- [ ] Use cases testable without external CV/Analytics services
- [ ] Mock behavior documented with examples
- [ ] CI/CD can run tests without CV/Analytics API credentials

## Timeline

- Phase 1: 2-3 hours
- Phase 2: 1 hour
- Phase 3: 1-2 hours
- Phase 4: 1 hour

**Total**: 5-7 hours

## Risk Assessment

**Low Risk**:
- Straightforward mock implementations (CV parsing, analytics calculations)
- Existing pattern to follow from other mocks

**Mitigation**:
- Follow existing MockLLMAdapter pattern
- Use type hints and validation to catch issues early
- Test mock behavior matches expected use case inputs/outputs

## Next Steps

1. Read phase-1-cv-analytics-mocks.md
2. Implement MockCVAnalyzerAdapter
3. Implement MockAnalyticsAdapter
4. Proceed to Phase 2
