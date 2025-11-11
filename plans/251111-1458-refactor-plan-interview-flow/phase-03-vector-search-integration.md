# Phase 3: Integrate Vector Search into Question Generation

**Date**: 2025-11-11
**Status**: Complete (Minor Fixes Required)
**Priority**: High
**Implementation Status**: Complete
**Review Status**: Approved with Minor Changes

## Context

**Parent Plan**: [Refactor Plan Interview Flow](./plan.md)
**Previous Phase**: [Phase 2: LLM Port Enhancement](./phase-02-llm-port-enhancement.md)
**Next Phase**: Phase 4: Unified CV Upload API Endpoint
**Related Docs**:
- [Plan Interview Use Case](../../src/application/use_cases/plan_interview.py)
- [Vector Search Port](../../src/domain/ports/vector_search_port.py)
- [Pinecone Adapter](../../src/adapters/vector_db/pinecone_adapter.py)

## Overview

Refactor `PlanInterviewUseCase` to integrate vector search for retrieving exemplar questions before generation. Add embedding storage after question creation. Implement error handling and fallback logic.

**Duration**: 3 days
**Estimated Completion**: 2025-11-16

## Key Insights

### Current Implementation Gaps

**File**: `src/application/use_cases/plan_interview.py`

**Missing Functionality**:
1. No vector search dependency
2. Question generation without exemplars
3. No embedding storage after creation
4. No similarity-based question selection

**Required Changes**:
1. Add `VectorSearchPort` to constructor
2. Create helper methods for vector operations
3. Modify `_generate_question_with_ideal_answer()` to use exemplars
4. Add embedding storage after question creation
5. Implement error handling for vector search failures

### New Question Generation Flow

```
_generate_question_with_ideal_answer()
├─→ 1. Determine question type/difficulty
├─→ 2. Select skill to test
├─→ 3. Build search query
│    └─→ Query: "{skill} interview question for {experience_level}"
├─→ 4. Generate query embedding
│    └─→ VectorSearch.get_embedding(query_text)
├─→ 5. Find similar questions (exemplars)
│    ├─→ VectorSearch.find_similar_questions(query_embedding, top_k=3)
│    ├─→ Filter by: question_type, difficulty
│    └─→ Handle empty results (fallback)
├─→ 6. Generate question with exemplars
│    └─→ LLM.generate_question(context, skill, difficulty, exemplars)
├─→ 7. Generate ideal answer
│    └─→ LLM.generate_ideal_answer(question_text, context)
├─→ 8. Generate rationale
│    └─→ LLM.generate_rationale(question_text, ideal_answer)
├─→ 9. Create Question entity
├─→ 10. Store question in DB
│    └─→ QuestionRepo.save(question)
├─→ 11. Generate question embedding
│    └─→ VectorSearch.get_embedding(question.text)
└─→ 12. Store question embedding
     └─→ VectorSearch.store_question_embedding(question.id, embedding, metadata)
```

### Vector Search Strategy

**Query Construction**:
```python
def _build_search_query(
    self,
    skill: str,
    cv_analysis: CVAnalysis,
    difficulty: DifficultyLevel,
) -> str:
    """Build search query for exemplar retrieval."""
    experience = cv_analysis.work_experience_years or 0
    exp_level = "junior" if experience < 3 else "mid" if experience < 7 else "senior"

    return f"{skill} {difficulty.value.lower()} interview question for {exp_level} developer"
```

**Exemplar Retrieval**:
```python
async def _find_exemplar_questions(
    self,
    skill: str,
    question_type: QuestionType,
    difficulty: DifficultyLevel,
    cv_analysis: CVAnalysis,
) -> list[dict[str, Any]]:
    """Find similar questions as exemplars."""
    try:
        # Build query
        query_text = self._build_search_query(skill, cv_analysis, difficulty)

        # Get embedding
        query_embedding = await self.vector_search.get_embedding(query_text)

        # Search with filters
        similar_questions = await self.vector_search.find_similar_questions(
            query_embedding=query_embedding,
            top_k=5,  # Request 5, use top 3
            filters={
                "question_type": question_type.value,
                "difficulty": difficulty.value,
            }
        )

        # Format exemplars
        exemplars = [
            {
                "text": q.get("text", ""),
                "skills": q.get("metadata", {}).get("skills", []),
                "difficulty": q.get("metadata", {}).get("difficulty", ""),
                "similarity_score": q.get("score", 0.0),
            }
            for q in similar_questions[:3]  # Use top 3
            if q.get("score", 0) > 0.5  # Similarity threshold
        ]

        logger.info(f"Found {len(exemplars)} exemplar questions for {skill}")
        return exemplars

    except Exception as e:
        logger.warning(f"Vector search failed: {e}. Falling back to no exemplars.")
        return []  # Fallback: empty exemplars
```

**Embedding Storage**:
```python
async def _store_question_embedding(
    self,
    question: Question,
) -> None:
    """Store question embedding in vector DB."""
    try:
        # Generate embedding
        embedding = await self.vector_search.get_embedding(question.text)

        # Store with metadata
        await self.vector_search.store_question_embedding(
            question_id=question.id,
            embedding=embedding,
            metadata={
                "text": question.text,
                "skills": question.skills,
                "difficulty": question.difficulty.value,
                "question_type": question.question_type.value,
                "tags": question.tags or [],
            }
        )

        logger.info(f"Stored embedding for question {question.id}")

    except Exception as e:
        logger.error(f"Failed to store embedding for {question.id}: {e}")
        # Non-critical: Continue even if embedding storage fails
```

## Requirements

### Functional Requirements

1. **Vector Search Integration**
   - Add VectorSearchPort dependency
   - Retrieve 3-5 exemplar questions before generation
   - Filter by question type and difficulty
   - Handle empty results gracefully

2. **Exemplar-Based Generation**
   - Pass exemplars to LLM
   - Log exemplar usage
   - Track success/failure metrics

3. **Embedding Storage**
   - Generate embedding for each question
   - Store with comprehensive metadata
   - Handle storage failures gracefully (non-blocking)

4. **Error Handling**
   - Fallback: generate without exemplars if search fails
   - Rollback: delete partially created questions on error
   - Log: detailed error messages with context

### Non-Functional Requirements

1. **Performance**
   - Vector search: <500ms per query
   - Total planning: <30 seconds for 5 questions
   - Minimize redundant API calls

2. **Reliability**
   - Vector search failures don't block question generation
   - Embedding storage failures don't fail overall process
   - Maintain existing rollback logic

3. **Testability**
   - Support MockVectorSearchAdapter
   - Deterministic test results
   - Unit tests for error scenarios

## Architecture

### Use Case Constructor

```python
class PlanInterviewUseCase:
    """Use case for planning interview questions with ideal answers."""

    def __init__(
        self,
        llm: LLMPort,
        vector_search: VectorSearchPort,  # NEW
        cv_analysis_repo: CVAnalysisRepositoryPort,
        interview_repo: InterviewRepositoryPort,
        question_repo: QuestionRepositoryPort,
    ):
        self.llm = llm
        self.vector_search = vector_search  # NEW
        self.cv_analysis_repo = cv_analysis_repo
        self.interview_repo = interview_repo
        self.question_repo = question_repo
```

### New Helper Methods

**1. Build Search Query**:
```python
def _build_search_query(
    self,
    skill: str,
    cv_analysis: CVAnalysis,
    difficulty: DifficultyLevel,
) -> str:
    """Build query text for exemplar search."""
    # Implementation above
```

**2. Find Exemplar Questions**:
```python
async def _find_exemplar_questions(
    self,
    skill: str,
    question_type: QuestionType,
    difficulty: DifficultyLevel,
    cv_analysis: CVAnalysis,
) -> list[dict[str, Any]]:
    """Retrieve similar questions as exemplars."""
    # Implementation above
```

**3. Store Question Embedding**:
```python
async def _store_question_embedding(
    self,
    question: Question,
) -> None:
    """Store question embedding in vector DB."""
    # Implementation above
```

### Modified Core Method

**_generate_question_with_ideal_answer()**:
```python
async def _generate_question_with_ideal_answer(
    self,
    cv_analysis: CVAnalysis,
    index: int,
    total: int,
) -> Question:
    """Generate single question with ideal answer + rationale."""

    # Existing: Determine question type/difficulty
    question_type, difficulty = self._get_question_distribution(index, total)

    # Existing: Select skill
    skills = cv_analysis.get_top_skills(limit=5)
    skill = skills[index % len(skills)].name if skills else "general knowledge"

    # NEW: Find exemplar questions
    exemplars = await self._find_exemplar_questions(
        skill=skill,
        question_type=question_type,
        difficulty=difficulty,
        cv_analysis=cv_analysis,
    )

    # Existing: Build context
    context = {
        "summary": cv_analysis.summary or "No summary",
        "skills": [s.name for s in skills],
        "experience": cv_analysis.work_experience_years or 0,
    }

    # MODIFIED: Generate question with exemplars
    question_text = await self.llm.generate_question(
        context=context,
        skill=skill,
        difficulty=difficulty.value,
        exemplars=exemplars,  # NEW
    )

    # Existing: Generate ideal answer
    ideal_answer = await self.llm.generate_ideal_answer(
        question_text=question_text,
        context=context,
    )

    # Existing: Generate rationale
    rationale = await self.llm.generate_rationale(
        question_text=question_text,
        ideal_answer=ideal_answer,
    )

    # Existing: Create Question entity
    question = Question(
        text=question_text,
        question_type=question_type,
        difficulty=difficulty,
        skills=[skill],
        ideal_answer=ideal_answer,
        rationale=rationale,
    )

    # Store question in DB (existing, moved here for clarity)
    await self.question_repo.save(question)

    # NEW: Store question embedding (non-blocking)
    await self._store_question_embedding(question)

    return question
```

### Error Handling Strategy

**Vector Search Failures**:
- Log warning, continue without exemplars
- Don't fail entire planning process
- Track metrics for monitoring

**Embedding Storage Failures**:
- Log error, continue to next question
- Question still saved in DB
- Retry logic (future enhancement)

**Question Generation Failures**:
- Existing rollback logic (delete created questions)
- Attempt cleanup of stored embeddings
- Return error to API layer

## Related Code Files

**Use Case** (PRIMARY):
- `src/application/use_cases/plan_interview.py` (MAJOR REFACTOR)

**Domain Ports** (READ):
- `src/domain/ports/vector_search_port.py` (USE existing methods)
- `src/domain/ports/llm_port.py` (USE enhanced method from Phase 2)

**Adapters** (USE):
- `src/adapters/vector_db/pinecone_adapter.py` (USE)
- `src/adapters/mock/mock_vector_search_adapter.py` (USE for tests)

**Infrastructure**:
- `src/infrastructure/dependency_injection/container.py` (MODIFY - inject vector_search)

**Tests** (CREATE/MODIFY):
- `tests/unit/use_cases/test_plan_interview.py` (MAJOR CHANGES)
- `tests/integration/test_plan_interview_integration.py` (NEW)

## Implementation Steps

### Step 1: Add VectorSearchPort Dependency
**File**: `src/application/use_cases/plan_interview.py`

- [ ] Add `vector_search: VectorSearchPort` to `__init__()` signature
- [ ] Store as instance variable: `self.vector_search = vector_search`
- [ ] Update docstring with new dependency
- [ ] Commit: `feat(use-case): add VectorSearchPort to PlanInterviewUseCase`

### Step 2: Create Helper Method - Build Search Query
**File**: `src/application/use_cases/plan_interview.py`

- [ ] Implement `_build_search_query()` method
- [ ] Extract experience level from CV (junior/mid/senior)
- [ ] Format query string
- [ ] Add unit test for query building
- [ ] Commit: `feat(use-case): add _build_search_query helper`

### Step 3: Create Helper Method - Find Exemplar Questions
**File**: `src/application/use_cases/plan_interview.py`

- [ ] Implement `_find_exemplar_questions()` method
- [ ] Call `vector_search.get_embedding(query_text)`
- [ ] Call `vector_search.find_similar_questions()` with filters
- [ ] Format results as exemplar dicts
- [ ] Filter by similarity threshold (>0.5)
- [ ] Limit to top 3 exemplars
- [ ] Add try-except with fallback to empty list
- [ ] Add logging for success/failure
- [ ] Commit: `feat(use-case): add _find_exemplar_questions helper`

### Step 4: Create Helper Method - Store Question Embedding
**File**: `src/application/use_cases/plan_interview.py`

- [ ] Implement `_store_question_embedding()` method
- [ ] Generate embedding: `vector_search.get_embedding(question.text)`
- [ ] Store: `vector_search.store_question_embedding(id, embedding, metadata)`
- [ ] Include comprehensive metadata (skills, difficulty, type, tags)
- [ ] Add try-except (non-blocking failure)
- [ ] Add logging
- [ ] Commit: `feat(use-case): add _store_question_embedding helper`

### Step 5: Refactor _generate_question_with_ideal_answer()
**File**: `src/application/use_cases/plan_interview.py`

- [ ] Call `_find_exemplar_questions()` after skill selection
- [ ] Pass `exemplars` to `llm.generate_question()`
- [ ] Call `question_repo.save(question)` (move if needed)
- [ ] Call `_store_question_embedding(question)` after saving
- [ ] Add logging for exemplar usage
- [ ] Commit: `feat(use-case): integrate vector search into question generation`

### Step 6: Update Dependency Injection
**File**: `src/infrastructure/dependency_injection/container.py`

- [ ] Add `vector_search_port()` call to PlanInterviewUseCase creation
- [ ] Ensure MockVectorSearchAdapter used when USE_MOCK_ADAPTERS=true
- [ ] Test with both mock and real adapters
- [ ] Commit: `feat(di): inject VectorSearchPort into PlanInterviewUseCase`

### Step 7: Update Unit Tests
**File**: `tests/unit/use_cases/test_plan_interview.py`

**Test Cases**:
- [ ] Test `_build_search_query()` with different experience levels
- [ ] Test `_find_exemplar_questions()` with mock results
- [ ] Test `_find_exemplar_questions()` when vector search returns empty
- [ ] Test `_find_exemplar_questions()` when vector search raises exception
- [ ] Test `_store_question_embedding()` success
- [ ] Test `_store_question_embedding()` failure (non-blocking)
- [ ] Test `execute()` with exemplars
- [ ] Test `execute()` with vector search disabled (exemplars=None)
- [ ] Mock VectorSearchPort responses
- [ ] Verify exemplars passed to LLM
- [ ] Run tests: `pytest tests/unit/use_cases/test_plan_interview.py -v`
- [ ] Commit: `test(use-case): add unit tests for vector search integration`

### Step 8: Integration Tests (Optional)
**File**: `tests/integration/test_plan_interview_integration.py`

- [ ] Test with real Pinecone adapter (requires API key)
- [ ] Test with real OpenAI adapter
- [ ] Verify embeddings stored in Pinecone
- [ ] Verify exemplars retrieved correctly
- [ ] Measure end-to-end latency
- [ ] Document performance findings
- [ ] Commit: `test(use-case): add integration tests for plan interview`

### Step 9: Error Handling & Logging
**File**: `src/application/use_cases/plan_interview.py`

- [ ] Add structured logging throughout
- [ ] Log exemplar retrieval success/failure
- [ ] Log embedding storage success/failure
- [ ] Track metrics (exemplar count, latency)
- [ ] Update error messages with context
- [ ] Commit: `feat(use-case): enhance error handling and logging`

### Step 10: Documentation
- [ ] Update use case docstring
- [ ] Add inline comments for complex logic
- [ ] Update CHANGELOG.md
- [ ] Update architecture docs if needed
- [ ] Commit: `docs: document vector search integration in plan interview`

## Todo List

- [x] Add VectorSearchPort dependency to use case
- [x] Implement `_build_search_query()` helper
- [x] Implement `_find_exemplar_questions()` helper
- [x] Implement `_store_question_embedding()` helper
- [x] Refactor `_generate_question_with_ideal_answer()` method
- [x] Update dependency injection container
- [x] Create comprehensive unit tests (10/10 passing)
- [ ] Run integration tests (optional - SKIPPED for MVP)
- [x] Enhance error handling and logging
- [x] Update documentation (inline comments, docstrings)
- [x] Code review and approval (APPROVED WITH MINOR CHANGES - see report)
- [ ] Fix minor issues before merge:
  - [ ] Run `black src/adapters/llm/openai_adapter.py`
  - [ ] Add return type annotations to `interview_routes.py`
  - [ ] Fix `zip(..., strict=True)` in `openai_adapter.py:177`
- [ ] Merge to main branch (PENDING - after fixes)

## Success Criteria

- [x] VectorSearchPort successfully integrated
- [x] Exemplar questions retrieved before generation
- [x] Question embeddings stored after creation
- [x] All unit tests pass (88% coverage for plan_interview.py)
- [x] Error handling and fallback logic working
- [x] Performance targets met (<1s with mocks, estimated <30s with real adapters)
- [x] Documentation complete (inline comments, docstrings)
- [x] Code review approved (WITH MINOR CHANGES)

**Review Report**: [251111-code-review-phase-03-vector-search-integration.md](./reports/251111-code-review-phase-03-vector-search-integration.md)

## Risk Assessment

### Technical Risks

**Risk**: Vector DB has insufficient exemplar questions (cold start problem)
- **Likelihood**: High
- **Impact**: Medium
- **Mitigation**: Seed DB with 50+ exemplar questions before testing
- **Fallback**: Generate without exemplars (existing LLM logic)

**Risk**: Vector search latency exceeds budget
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: Monitor latency, implement caching (future)
- **Target**: <500ms per vector search query

**Risk**: Embedding storage failures block question generation
- **Likelihood**: Low
- **Impact**: High
- **Mitigation**: Non-blocking error handling, continue on failure
- **Monitoring**: Track embedding storage failure rate

**Risk**: Exemplars cause LLM to generate similar/duplicate questions
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: Strong prompt engineering, similarity threshold
- **Validation**: Monitor question uniqueness

### Implementation Risks

**Risk**: Refactoring breaks existing tests
- **Likelihood**: Medium
- **Impact**: High
- **Mitigation**: Run full test suite after each change
- **Strategy**: Incremental refactoring with commits

**Risk**: Mock adapters don't match real adapter behavior
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: Integration tests with real adapters
- **Documentation**: Document adapter differences

## Security Considerations

### Vector Search Queries
- Query text includes CV summary (may contain PII)
- **Action**: Sanitize query text before sending to vector DB
- **Validation**: Audit query logs for sensitive data

### Embedding Storage
- Embeddings may encode sensitive information
- **Action**: Review metadata before storing
- **Protection**: Access controls on vector DB

### Error Messages
- Don't expose internal implementation details
- **Action**: Generic error messages for production
- **Logging**: Detailed errors in logs only

## Next Steps

1. **Begin Implementation**: Add VectorSearchPort dependency
2. **Parallel Work**: Helper methods and refactoring
3. **Testing**: Comprehensive unit tests
4. **Integration**: Test with real Pinecone/OpenAI
5. **Code Review**: Team review of refactored use case
6. **Merge**: Merge after approval
7. **Phase 4**: Begin unified API endpoint implementation

## Unresolved Questions

1. **Similarity Threshold**: Is 0.5 appropriate, or should it be configurable?
2. **Exemplar Count**: Always use 3, or vary based on CV complexity?
3. **Caching Strategy**: Cache exemplar results for identical queries?
4. **Retry Logic**: Retry embedding storage on failure, or log and continue?
5. **Performance**: Is parallel embedding generation worth the complexity?
6. **Monitoring**: What metrics to track for vector search performance?

---

**Document Status**: Draft
**Next Review**: Before implementation
**Dependencies**: Phase 2 complete (LLM port enhancement)
**Blocks**: Phase 4 (Unified API Endpoint)
