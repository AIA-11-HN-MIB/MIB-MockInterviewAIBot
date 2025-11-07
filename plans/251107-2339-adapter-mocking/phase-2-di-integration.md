# Phase 2: DI Container Integration

## Context

Phase 1 created 2 new mock adapters (CV, Analytics). Must integrate with DI container to enable config-driven adapter selection: `use_mock_adapters=true` → use mocks, `false` → use real adapters.

Existing pattern in `container.py` already handles LLM, Vector, STT, TTS mocks. Extend for CV analyzer and analytics.

## Overview

Update `Container` class to:
1. Add `use_mock_adapters` config flag to Settings
2. Wire CV analyzer and analytics mocks
3. Update environment variable examples
4. Add validation for mock mode (no API keys required)

Minimal code changes (existing pattern proven).

## Key Insights

- Container already uses `if self.settings.use_mock_adapters:` pattern (lines 73, 111, 223, 247)
- Settings class in `infrastructure/config/settings.py` needs new field
- Only 2 adapters to integrate (CV, Analytics)

## Requirements

### Settings Updates
**Add to Settings class**:
```python
# Mock Adapters (for testing/development)
use_mock_adapters: bool = False  # Enable all mocks
```

**Environment variable**:
- `USE_MOCK_ADAPTERS=true` in .env.local for dev
- Default `false` for production

### Container Methods to Update

**CV Analyzer** (already has stub at line 199):
```python
def cv_analyzer_port(self) -> CVAnalyzerPort:
    if self.settings.use_mock_adapters:
        return MockCVAnalyzerAdapter()
    else:
        # Real implementation (Phase 5+)
        raise NotImplementedError("CV analyzer not yet implemented")
```

**Analytics** (new method):
```python
def analytics_port(self) -> AnalyticsPort:
    if self.settings.use_mock_adapters:
        return MockAnalyticsAdapter()
    else:
        # Real implementation (Phase 5+)
        raise NotImplementedError("Analytics adapter not yet implemented")
```

## Architecture

**Conditional DI pattern**:
```python
def cv_analyzer_port(self) -> CVAnalyzerPort:
    if self.settings.use_mock_adapters:
        from ...adapters.mock import MockCVAnalyzerAdapter
        return MockCVAnalyzerAdapter()
    else:
        raise NotImplementedError("CV analyzer not yet implemented")
```

**Repository Strategy**: Use real PostgreSQL adapters (no mocks needed)

## Related Code Files

**Will modify**:
- `src/infrastructure/config/settings.py` (add use_mock_adapters)
- `src/infrastructure/dependency_injection/container.py` (2 methods)
- `.env.example` (document USE_MOCK_ADAPTERS)

**Reference**:
- Existing mock integration pattern (lines 73-98, 111-140, 223-256)

## Implementation Steps

### Step 1: Update Settings (15 mins)

1. Open `src/infrastructure/config/settings.py`
2. Add after line ~60 (Mock Adapters section):
   ```python
   # Mock Adapters (Development/Testing)
   use_mock_adapters: bool = Field(
       default=False,
       description="Enable mock adapters for all external services (no API calls)",
   )
   ```
3. Add validation method (optional):
   ```python
   @model_validator(mode='after')
   def validate_mock_mode(self) -> 'Settings':
       if self.use_mock_adapters:
           # In mock mode, API keys not required
           logger.info("Mock adapters enabled - external services disabled")
       return self
   ```
4. Update docstring to document mock mode

### Step 2: Update Container - CV Analyzer (10 mins)

1. Open `src/infrastructure/dependency_injection/container.py`
2. Find `cv_analyzer_port()` method (line 199)
3. Replace implementation:
   ```python
   def cv_analyzer_port(self) -> CVAnalyzerPort:
       if self.settings.use_mock_adapters:
           from ...adapters.mock import MockCVAnalyzerAdapter
           return MockCVAnalyzerAdapter()
       else:
           # TODO: Implement real CV analyzer
           raise NotImplementedError("CV analyzer not yet implemented")
   ```
4. Remove TODO comment at top of method

### Step 3: Update Container - Analytics (15 mins)

1. Find `analytics_port()` method (line 258)
2. Update implementation:
   ```python
   def analytics_port(self) -> AnalyticsPort:
       if self.settings.use_mock_adapters:
           from ...adapters.mock import MockAnalyticsAdapter
           return MockAnalyticsAdapter()
       else:
           # TODO: Implement analytics service
           raise NotImplementedError("Analytics adapter not yet implemented")
   ```
3. Add to imports at top of file:
   ```python
   from ...adapters.mock import MockAnalyticsAdapter
   ```

### Step 4: Update Environment Variables (10 mins)

1. Open `.env.example`
2. Add section after line ~40 (Mock Adapters):
   ```bash
   # Mock Adapters (Development/Testing)
   # Set to true to use in-memory mocks instead of real services
   # Useful for: local dev without API keys, fast testing, CI/CD
   USE_MOCK_ADAPTERS=false
   ```
3. Add comment explaining when to use mocks

### Step 5: Integration Testing (30 mins)

1. Create test file: `tests/integration/test_mock_integration.py`
2. Test container returns mocks when flag enabled:
   ```python
   def test_container_uses_mocks_when_enabled():
       settings = Settings(use_mock_adapters=True)
       container = Container(settings)

       llm = container.llm_port()
       assert isinstance(llm, MockLLMAdapter)

       cv = container.cv_analyzer_port()
       assert isinstance(cv, MockCVAnalyzerAdapter)
   ```
3. Test container returns real adapters when flag disabled
4. Test use case works with mocks end-to-end
5. Run: `pytest tests/integration/test_mock_integration.py`

## TODO

- [ ] Add use_mock_adapters field to Settings
- [ ] Add validation method for mock mode
- [ ] Update cv_analyzer_port() in container
- [ ] Update analytics_port() in container
- [ ] Add mock imports to container.py
- [ ] Update .env.example with USE_MOCK_ADAPTERS
- [ ] Create integration test for mock mode
- [ ] Test container with flag enabled/disabled
- [ ] Run mypy to check types
- [ ] Update CLAUDE.md with mock usage instructions

## Success Criteria

- [ ] `USE_MOCK_ADAPTERS=true` enables all mocks via DI
- [ ] Container methods support both mock and real adapters
- [ ] No API keys required when use_mock_adapters=true
- [ ] Integration tests pass in mock mode
- [ ] Type checking passes (mypy)
- [ ] Documentation updated

## Risk Assessment

**Low Risk**:
- Extends existing proven pattern
- Backward compatible (default: false)
- Type system enforces correct usage

**Mitigations**:
- Test both mock and real modes
- Document when to use mocks
- Validate settings on startup

## Security Considerations

**Risk**: Mock mode bypasses authentication/authorization
**Mitigation**: Only enable in dev/test envs (not production)
**Validation**: Add environment check in Settings:
```python
if self.is_production() and self.use_mock_adapters:
    raise ValueError("Mock adapters not allowed in production")
```

## Next Steps

After completion:
1. Proceed to Phase 3 (Test Infrastructure Updates)
2. Update CI/CD to use mock mode (fast tests)
3. Document mock mode in README

## Unresolved Questions

1. Mixed mode: mock LLM but real DB? (Yes: allow via use_mock_adapters flag)
2. Production safeguard: block mock mode in prod? (Yes: add validation)
