# Phase 1: CV Processing & Analytics Mocks

## Context

CV analysis and analytics are critical for interview flow but require external LLM services (OpenAI) for real implementation. Mocks enable use case testing without API costs/latency.

## Overview

Create 2 mock adapters:
1. **MockCVAnalyzerAdapter**: Simulates CV parsing, skill extraction
2. **MockAnalyticsAdapter**: Simulates performance tracking, reporting

Both return realistic, deterministic data for predictable testing.

## Key Insights

- CVAnalyzerPort has 2 methods (analyze_cv, extract_text_from_file)
- AnalyticsPort has 5 methods (record, statistics, history, recommendations, skill scores)
- Existing MockLLMAdapter shows good pattern: realistic scores, configurable behavior
- conftest.py has no CV/analytics mocks currently

## Requirements

### MockCVAnalyzerAdapter
**Must implement**:
- `analyze_cv(cv_file_path, candidate_id) -> CVAnalysis`
  - Return CVAnalysis with 4-6 skills (mix of technical/soft)
  - Include realistic experience (2-10 years based on file name pattern)
  - Generate suggested topics matching skills
  - Suggest difficulty based on experience level
- `extract_text_from_file(file_path) -> str`
  - Return mock CV text (200-500 words)
  - Support .pdf, .doc, .docx extensions
  - Raise error for unsupported formats

**Data patterns**:
- Junior (<2 yrs): 2-3 skills, EASY difficulty, basic topics
- Mid (2-5 yrs): 4-5 skills, MEDIUM difficulty, intermediate topics
- Senior (5+ yrs): 5-6 skills, HARD difficulty, advanced topics

### MockAnalyticsAdapter
**Must implement**:
- `record_answer_evaluation(interview_id, answer) -> None`
  - Store in-memory dict keyed by interview_id
- `get_interview_statistics(interview_id) -> dict`
  - Calculate avg_score, completion_rate, time_spent (mock)
  - Return question_count, answers_count
- `get_candidate_performance_history(candidate_id) -> list[dict]`
  - Return 0-3 past interviews with scores
- `generate_improvement_recommendations(interview_id, questions, answers) -> list[str]`
  - Analyze scores: <60 = 3-4 recs, 60-80 = 2-3 recs, >80 = 1-2 recs
  - Base on weaknesses from answer evaluations
- `calculate_skill_scores(answers, questions) -> dict[str, float]`
  - Group answers by question.skills
  - Average scores per skill

## Architecture

**File structure**:
```
src/adapters/mock/
├── __init__.py  # Update exports
├── mock_cv_analyzer.py  # NEW
└── mock_analytics.py    # NEW
```

**Integration points**:
- DI container (phase 3)
- Use cases: AnalyzeCVUseCase, CompleteInterviewUseCase
- Test fixtures in conftest.py (phase 4)

## Related Code Files

**Read these**:
- `src/domain/ports/cv_analyzer_port.py` (interface definition)
- `src/domain/ports/analytics_port.py` (interface definition)
- `src/domain/models/cv_analysis.py` (CVAnalysis, ExtractedSkill)
- `src/adapters/mock/mock_llm_adapter.py` (pattern reference)
- `src/application/use_cases/analyze_cv.py` (usage context)

**Will modify**:
- `src/adapters/mock/__init__.py` (add exports)

**Will create**:
- `src/adapters/mock/mock_cv_analyzer.py`
- `src/adapters/mock/mock_analytics.py`

## Implementation Steps

### Step 1: Create MockCVAnalyzerAdapter (60 mins)

1. Create `src/adapters/mock/mock_cv_analyzer.py`
2. Import required types:
   ```python
   from ...domain.ports.cv_analyzer_port import CVAnalyzerPort
   from ...domain.models.cv_analysis import CVAnalysis, ExtractedSkill
   from uuid import UUID, uuid4
   from pathlib import Path
   ```
3. Define skill database (3 experience levels × 6 skills each)
4. Implement `extract_text_from_file()`:
   - Check file extension
   - Return template CV text (hardcoded, 300 words)
   - Raise `ValueError` for unsupported formats
5. Implement `analyze_cv()`:
   - Parse file name for hints (junior/senior/mid)
   - Select skills based on experience level
   - Calculate work_experience_years (2-10)
   - Generate suggested_topics from skills
   - Return CVAnalysis entity
6. Add docstrings explaining mock behavior

### Step 2: Create MockAnalyticsAdapter (90 mins)

1. Create `src/adapters/mock/mock_analytics.py`
2. Define `MockAnalyticsAdapter` class with in-memory storage:
   ```python
   def __init__(self):
       self._evaluations: dict[UUID, list[Answer]] = {}
       self._history: dict[UUID, list[dict]] = {}  # candidate_id -> interviews
   ```
3. Implement `record_answer_evaluation()`:
   - Append to `_evaluations[interview_id]`
4. Implement `get_interview_statistics()`:
   - Fetch evaluations for interview
   - Calculate avg_score, completion_rate
   - Return dict with metrics
5. Implement `get_candidate_performance_history()`:
   - Return mock historical data (0-3 past interviews)
   - Include scores trending upward
6. Implement `generate_improvement_recommendations()`:
   - Extract weaknesses from all answers
   - Aggregate and deduplicate
   - Return top 3-5 based on frequency
7. Implement `calculate_skill_scores()`:
   - Group answers by question skills
   - Average evaluation.score per skill
   - Return dict[skill_name, avg_score]
8. Add type hints and docstrings

### Step 3: Update exports (10 mins)

1. Edit `src/adapters/mock/__init__.py`:
   ```python
   from .mock_cv_analyzer import MockCVAnalyzerAdapter
   from .mock_analytics import MockAnalyticsAdapter

   __all__ = [
       "MockLLMAdapter",
       "MockSTTAdapter",
       "MockTTSAdapter",
       "MockVectorSearchAdapter",
       "MockCVAnalyzerAdapter",  # NEW
       "MockAnalyticsAdapter",   # NEW
   ]
   ```

### Step 4: Create unit tests (60 mins)

1. Create `tests/unit/adapters/test_mock_cv_analyzer.py`:
   - Test analyze_cv with different file names
   - Test extract_text_from_file with valid/invalid extensions
   - Verify CVAnalysis structure
2. Create `tests/unit/adapters/test_mock_analytics.py`:
   - Test each method independently
   - Verify calculations (avg_score, skill_scores)
   - Test edge cases (empty data)
3. Run tests: `pytest tests/unit/adapters/test_mock_*.py`

## TODO

- [ ] Create MockCVAnalyzerAdapter skeleton
- [ ] Implement extract_text_from_file with extension check
- [ ] Add skill database (junior/mid/senior tiers)
- [ ] Implement analyze_cv with experience detection
- [ ] Create MockAnalyticsAdapter skeleton
- [ ] Implement in-memory storage structure
- [ ] Implement all 5 analytics methods
- [ ] Update mock/__init__.py exports
- [ ] Write unit tests for CV analyzer mock
- [ ] Write unit tests for analytics mock
- [ ] Verify mocks match port interfaces (mypy)
- [ ] Document mock behavior in docstrings

## Success Criteria

- [ ] MockCVAnalyzerAdapter returns valid CVAnalysis entities
- [ ] Skills/experience realistic and deterministic
- [ ] MockAnalyticsAdapter calculates metrics correctly
- [ ] All 7 methods implemented with type hints
- [ ] Unit tests pass with >90% coverage
- [ ] No external dependencies (filesystem I/O is mocked)
- [ ] Mypy passes (no type errors)

## Risk Assessment

**Low Risk**:
- Straightforward mock implementations
- No external service dependencies
- Existing pattern to follow (MockLLMAdapter)

**Mitigations**:
- Use existing CVAnalysis model validation
- Test against real use cases to ensure compatibility
- Document mock limitations (e.g., no real file parsing)

## Security Considerations

None (mocks don't access real files or services)

## Next Steps

After completion:
1. Proceed to Phase 2 (Repository Mocks)
2. Keep Phase 1 mocks simple (enhance in Phase 5 if needed)
3. Document any discovered requirements for Phase 3 DI integration

## Unresolved Questions

1. Should mock CV analyzer support multiple languages? (Defer to Phase 5)
2. Analytics history: store globally or per-test? (Use dict, clear in teardown)
3. Mock file I/O or assume file exists? (Mock: return hardcoded text)
