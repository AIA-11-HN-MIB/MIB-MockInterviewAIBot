# Phase 2: Enhance LLM Port for Exemplar-Based Generation

**Date**: 2025-11-11
**Status**: Pending
**Priority**: High
**Implementation Status**: Not Started
**Review Status**: Pending

## Context

**Parent Plan**: [Refactor Plan Interview Flow](./plan.md)
**Previous Phase**: [Phase 1: Analysis & Design](./phase-01-analysis-design.md)
**Next Phase**: Phase 3: Vector Search Integration
**Related Docs**:
- [LLM Port](../../src/domain/ports/llm_port.py)
- [OpenAI Adapter](../../src/adapters/llm/openai_adapter.py)
- [Mock LLM Adapter](../../src/adapters/mock/mock_llm_adapter.py)

## Overview

Enhance LLMPort interface and adapters to support exemplar-based question generation. Add optional `exemplars` parameter to `generate_question()` method while maintaining backward compatibility.

**Duration**: 2 days
**Estimated Completion**: 2025-11-13

## Key Insights

### Current LLM Port Interface

```python
# src/domain/ports/llm_port.py
async def generate_question(
    self,
    context: dict[str, Any],
    skill: str,
    difficulty: str,
) -> str:
    """Generate an interview question."""
    pass
```

**Current Usage**:
- Context: CV summary, skills, experience
- Skill: Target skill to test
- Difficulty: EASY/MEDIUM/HARD

**Limitation**: No way to pass exemplar questions for inspiration.

### Proposed Enhancement

```python
# src/domain/ports/llm_port.py
async def generate_question(
    self,
    context: dict[str, Any],
    skill: str,
    difficulty: str,
    exemplars: list[dict[str, Any]] | None = None,  # NEW
) -> str:
    """Generate an interview question.

    Args:
        exemplars: Optional list of similar questions (dicts with 'text', 'skills', 'difficulty')
    """
    pass
```

**Benefits**:
- Backward compatible (optional parameter)
- LLM can learn from existing questions
- Maintains consistency across questions
- Improves question quality

### Exemplar Format

```python
exemplars = [
    {
        "text": "Explain the difference between list and tuple in Python.",
        "skills": ["Python", "Data Structures"],
        "difficulty": "EASY",
        "similarity_score": 0.85,
    },
    {
        "text": "How would you optimize a slow Python function?",
        "skills": ["Python", "Performance"],
        "difficulty": "MEDIUM",
        "similarity_score": 0.78,
    },
]
```

### Prompt Engineering Strategy

**Without Exemplars** (current):
```
Generate a MEDIUM difficulty interview question to test: Python

Context:
- Candidate's background: 3 years Python experience, FastAPI projects
- Skills: Python, FastAPI, PostgreSQL

Return only the question text.
```

**With Exemplars** (new):
```
Generate a MEDIUM difficulty interview question to test: Python

Context:
- Candidate's background: 3 years Python experience, FastAPI projects
- Skills: Python, FastAPI, PostgreSQL

Similar questions for inspiration (do NOT copy these exactly):
1. "Explain the difference between list and tuple in Python." (EASY)
2. "How would you optimize a slow Python function?" (MEDIUM)

Generate a NEW question inspired by the style and structure above.
Return only the question text.
```

## Requirements

### Functional Requirements

1. **LLMPort Interface**
   - Add optional `exemplars` parameter to `generate_question()`
   - Maintain backward compatibility (default=None)
   - Document exemplar format in docstring

2. **OpenAI Adapter**
   - Accept exemplars parameter
   - Enhance prompt to include exemplars when provided
   - Generate quality questions inspired by exemplars
   - Handle empty exemplars list gracefully

3. **MockLLM Adapter**
   - Accept exemplars parameter (for interface consistency)
   - Return deterministic questions for testing
   - Optionally incorporate exemplar info into mock response

4. **Prompt Engineering**
   - Clear instructions to avoid copying exemplars
   - Emphasize generating NEW questions
   - Maintain consistency with difficulty/skill

### Non-Functional Requirements

1. **Backward Compatibility**
   - Existing calls without exemplars still work
   - No breaking changes to dependent code
   - Gradual adoption possible

2. **Testability**
   - Unit tests verify exemplar handling
   - Mock adapter supports test scenarios
   - Deterministic test results

3. **Performance**
   - No significant latency increase with exemplars
   - Prompt length remains within token limits
   - Target: <3 seconds per question generation

## Architecture

### Component Changes

**1. LLMPort Interface** (`src/domain/ports/llm_port.py`):
```python
@abstractmethod
async def generate_question(
    self,
    context: dict[str, Any],
    skill: str,
    difficulty: str,
    exemplars: list[dict[str, Any]] | None = None,
) -> str:
    """Generate an interview question.

    Args:
        context: Interview context (CV analysis, previous answers, etc.)
        skill: Target skill to test
        difficulty: Question difficulty level
        exemplars: Optional list of similar questions for inspiration.
                   Each dict should contain: 'text', 'skills', 'difficulty', 'similarity_score'

    Returns:
        Generated question text
    """
    pass
```

**2. OpenAI Adapter** (`src/adapters/llm/openai_adapter.py`):
```python
async def generate_question(
    self,
    context: dict[str, Any],
    skill: str,
    difficulty: str,
    exemplars: list[dict[str, Any]] | None = None,
) -> str:
    """Generate question using OpenAI, optionally with exemplars."""

    system_prompt = """You are an expert technical interviewer.
    Generate a clear, relevant interview question based on the context provided."""

    # Build user prompt
    user_prompt = f"""
    Generate a {difficulty} difficulty interview question to test: {skill}

    Context:
    - Candidate's background: {context.get('summary', 'Not provided')}
    - Skills: {context.get('skills', [])}
    - Experience: {context.get('experience', 0)} years
    """

    # Add exemplars if provided
    if exemplars:
        user_prompt += "\n\nSimilar questions for inspiration (do NOT copy exactly):\n"
        for i, ex in enumerate(exemplars[:3], 1):  # Limit to 3
            user_prompt += f"{i}. \"{ex['text']}\" ({ex['difficulty']})\n"
        user_prompt += "\nGenerate a NEW question inspired by the style above."

    user_prompt += "\n\nReturn only the question text, no additional explanation."

    response = await self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=self.temperature,
    )

    return response.choices[0].message.content.strip()
```

**3. MockLLM Adapter** (`src/adapters/mock/mock_llm_adapter.py`):
```python
async def generate_question(
    self,
    context: dict[str, Any],
    skill: str,
    difficulty: str,
    exemplars: list[dict[str, Any]] | None = None,
) -> str:
    """Generate mock question (deterministic for testing)."""

    # Deterministic mock question
    base_question = f"[MOCK] What is your experience with {skill}?"

    # Optionally indicate exemplars were provided
    if exemplars:
        base_question += f" (Generated with {len(exemplars)} exemplars)"

    return base_question
```

### Prompt Engineering Guidelines

**Best Practices**:
1. Limit exemplars to 3 (avoid prompt bloat)
2. Use clear instruction: "do NOT copy exactly"
3. Emphasize "NEW question"
4. Include similarity scores for context
5. Maintain original context priority

**Token Management**:
- Exemplars add ~100-200 tokens per question
- GPT-4 limit: 8192 tokens (safe margin)
- Monitor prompt length in logs

## Related Code Files

**Domain Layer**:
- `src/domain/ports/llm_port.py` (MODIFY - add parameter)

**Adapters Layer**:
- `src/adapters/llm/openai_adapter.py` (MODIFY - implement exemplar logic)
- `src/adapters/mock/mock_llm_adapter.py` (MODIFY - add parameter)

**Tests**:
- `tests/unit/adapters/test_openai_adapter.py` (CREATE/MODIFY)
- `tests/unit/adapters/test_mock_llm_adapter.py` (CREATE/MODIFY)

## Implementation Steps

### Step 1: Update LLMPort Interface
**File**: `src/domain/ports/llm_port.py`

- [ ] Add `exemplars` parameter to `generate_question()` signature
- [ ] Set default value: `exemplars: list[dict[str, Any]] | None = None`
- [ ] Update docstring with exemplar format documentation
- [ ] Add type hints and validation notes
- [ ] Commit: `feat(domain): add exemplars parameter to LLMPort.generate_question`

### Step 2: Update OpenAI Adapter
**File**: `src/adapters/llm/openai_adapter.py`

- [ ] Add `exemplars` parameter to `generate_question()` method
- [ ] Implement prompt enhancement logic:
  - [ ] Check if exemplars provided
  - [ ] Limit to top 3 exemplars
  - [ ] Format exemplars into prompt
  - [ ] Add instruction to avoid copying
- [ ] Test prompt manually with sample exemplars
- [ ] Add logging for exemplar count
- [ ] Commit: `feat(llm): implement exemplar-based question generation in OpenAI adapter`

### Step 3: Update MockLLM Adapter
**File**: `src/adapters/mock/mock_llm_adapter.py`

- [ ] Add `exemplars` parameter to `generate_question()` method
- [ ] Return deterministic mock response
- [ ] Optionally include exemplar count in response (for testing)
- [ ] Ensure backward compatibility (existing tests pass)
- [ ] Commit: `feat(mock): add exemplars parameter to MockLLM adapter`

### Step 4: Create Unit Tests
**Files**: `tests/unit/adapters/test_openai_adapter.py`, `test_mock_llm_adapter.py`

**Test Cases**:
- [ ] Test `generate_question()` without exemplars (backward compatibility)
- [ ] Test `generate_question()` with exemplars
- [ ] Test exemplar count limiting (>3 exemplars provided)
- [ ] Test empty exemplars list
- [ ] Verify prompt contains exemplar text
- [ ] Verify prompt includes "do NOT copy" instruction
- [ ] Test mock adapter returns consistent results
- [ ] Run tests: `pytest tests/unit/adapters/ -v`
- [ ] Commit: `test(llm): add unit tests for exemplar-based generation`

### Step 5: Integration Testing
**File**: `tests/integration/test_openai_adapter_integration.py` (optional)

- [ ] Test with real OpenAI API (requires API key)
- [ ] Verify generated questions differ from exemplars
- [ ] Check question quality with exemplars vs. without
- [ ] Measure latency impact
- [ ] Document findings
- [ ] Commit: `test(llm): add integration tests for exemplar generation`

### Step 6: Documentation
- [ ] Update CHANGELOG.md with interface changes
- [ ] Update API documentation (if applicable)
- [ ] Add inline comments explaining exemplar logic
- [ ] Document prompt engineering decisions
- [ ] Commit: `docs: document exemplar-based question generation`

## Todo List

- [ ] Update LLMPort interface with exemplars parameter
- [ ] Implement OpenAI adapter prompt enhancement
- [ ] Update MockLLM adapter for test compatibility
- [ ] Create comprehensive unit tests
- [ ] Run integration tests (optional)
- [ ] Update documentation
- [ ] Code review and approval
- [ ] Merge to main branch

## Success Criteria

- [ ] LLMPort interface updated with backward-compatible parameter
- [ ] OpenAI adapter generates questions using exemplars
- [ ] MockLLM adapter supports exemplars for testing
- [ ] All unit tests pass (>80% coverage)
- [ ] No breaking changes to existing code
- [ ] Documentation complete
- [ ] Code review approved

## Risk Assessment

### Technical Risks

**Risk**: Exemplars increase prompt length, causing token limit issues
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: Limit to 3 exemplars, monitor prompt length
- **Fallback**: Truncate exemplar text if needed

**Risk**: LLM copies exemplars instead of generating new questions
- **Likelihood**: Medium
- **Impact**: High
- **Mitigation**: Strong prompt instruction, A/B test prompts
- **Validation**: Compare generated question similarity to exemplars

**Risk**: Quality regression without exemplars
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: Make exemplars optional, backward compatible
- **Testing**: Compare question quality with/without exemplars

### Implementation Risks

**Risk**: Breaking changes to existing use cases
- **Likelihood**: Low
- **Impact**: High
- **Mitigation**: Optional parameter (default=None), comprehensive tests
- **Validation**: Run full test suite after changes

**Risk**: Mock adapter doesn't match real adapter behavior
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: Keep mock logic simple, document differences
- **Testing**: Integration tests with real adapter

## Security Considerations

### Prompt Injection
- Exemplar text may contain malicious prompts
- **Action**: Sanitize exemplar text before including in prompt
- **Validation**: Strip special characters, limit length

### API Key Exposure
- Integration tests require OpenAI API key
- **Action**: Use environment variables, never commit keys
- **Protection**: .env.local in .gitignore

### Rate Limiting
- Additional exemplar processing may increase API calls
- **Action**: Implement caching for frequent queries (future)
- **Monitoring**: Track API usage and costs

## Next Steps

1. **Begin Implementation**: Update LLMPort interface
2. **Parallel Work**: OpenAI and Mock adapters
3. **Testing**: Comprehensive unit tests
4. **Code Review**: Team review of prompt engineering
5. **Merge**: Merge to main after approval
6. **Phase 3**: Begin vector search integration

## Unresolved Questions

1. **Exemplar Count**: Is 3 exemplars optimal, or should it be configurable?
2. **Prompt Tuning**: How much weight to give exemplars vs. CV context?
3. **Quality Metrics**: How to measure question quality improvement?
4. **A/B Testing**: Should we test different prompt variations?
5. **Caching**: Cache LLM responses for identical exemplar sets?

---

**Document Status**: Draft
**Next Review**: Before implementation
**Dependencies**: Phase 1 complete
**Blocks**: Phase 3 (Vector Search Integration)
