# Phase 1: Analysis & Design

**Date**: 2025-11-11
**Status**: Complete
**Priority**: High
**Implementation Status**: Complete
**Review Status**: Approved

## Context

**Parent Plan**: [Refactor Plan Interview Flow](./plan.md)
**Dependencies**: None (initial phase)
**Related Docs**:
- [System Architecture](../../docs/system-architecture.md)
- [Codebase Summary](../../docs/codebase-summary.md)
- [Current plan_interview.py](../../src/application/use_cases/plan_interview.py)

## Overview

Analyze current implementation and design vector search integration approach for exemplar-based question generation. Document architectural decisions and interface changes.

**Duration**: 1 day
**Completion**: 2025-11-11

## Key Insights

### Current Implementation Analysis

**File**: `src/application/use_cases/plan_interview.py` (255 lines)

**Workflow**:
1. Load CV analysis from repository
2. Calculate question count (n=2-5) based on skill diversity
3. Create interview entity (status=PREPARING)
4. Generate n questions sequentially:
   - `llm.generate_question()` - question text
   - `llm.generate_ideal_answer()` - ideal answer
   - `llm.generate_rationale()` - rationale
5. Store questions in DB
6. Update interview (status=READY)

**Key Methods**:
- `execute()` - Main orchestration
- `_calculate_question_count()` - Skill-based calculation
- `_generate_question_with_ideal_answer()` - Question generation
- `_get_question_distribution()` - Type/difficulty distribution

**Dependencies**:
- LLMPort (4 methods used)
- CVAnalysisRepositoryPort
- InterviewRepositoryPort
- QuestionRepositoryPort

### Gap Analysis

**Missing Integration**:
- No vector search for similar questions
- No exemplar-based question generation
- No embedding storage after question creation
- CV upload/validation not integrated into planning flow

**Required Changes**:
1. Add VectorSearchPort dependency to use case
2. Modify question generation to retrieve exemplars
3. Store question embeddings after generation
4. Update LLM methods to accept exemplar parameter

### New Flow Design

```
┌─────────────────────────────────────────────────────┐
│ PlanInterviewUseCase.execute()                      │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ 1. Load CV Analysis (CVAnalysisRepository)          │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ 2. Calculate n questions (skill diversity)          │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ 3. Create Interview (status=PREPARING)              │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ 4. FOR each question i=1..n:                        │
│    ┌────────────────────────────────────────────┐   │
│    │ 4.1 Determine type/difficulty              │   │
│    │ 4.2 Get skill to test                      │   │
│    │ 4.3 Generate embedding for search query    │   │
│    │     (VectorSearch.get_embedding)           │   │
│    │ 4.4 Find similar questions (exemplars)     │   │
│    │     (VectorSearch.find_similar_questions)  │   │
│    │ 4.5 Generate question with exemplars       │   │
│    │     (LLM.generate_question)                │   │
│    │ 4.6 Generate ideal answer                  │   │
│    │     (LLM.generate_ideal_answer)            │   │
│    │ 4.7 Generate rationale                     │   │
│    │     (LLM.generate_rationale)               │   │
│    │ 4.8 Create Question entity                 │   │
│    │ 4.9 Store question in DB                   │   │
│    │ 4.10 Generate & store embedding            │   │
│    │     (VectorSearch.store_question_embedding)│   │
│    └────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ 5. Update Interview (status=READY, metadata)        │
└─────────────────────────────────────────────────────┘
```

### Vector Search Strategy

**Query Construction**:
```python
# Build search query from CV context + skill
query_text = f"{skill} interview question for candidate with: {cv_summary}"
query_embedding = await vector_search.get_embedding(query_text)

# Search with filters
similar_questions = await vector_search.find_similar_questions(
    query_embedding=query_embedding,
    top_k=3,  # Get 3 exemplars
    filters={
        "question_type": question_type.value,
        "difficulty": difficulty.value,
    }
)
```

**Exemplar Selection**:
- Retrieve top 3 similar questions by cosine similarity
- Filter by question type and difficulty
- Use as context for LLM question generation
- Fallback: generate without exemplars if none found

**Embedding Storage**:
```python
# After generating question
question_embedding = await vector_search.get_embedding(question.text)
await vector_search.store_question_embedding(
    question_id=question.id,
    embedding=question_embedding,
    metadata={
        "text": question.text,
        "skills": question.skills,
        "difficulty": question.difficulty.value,
        "question_type": question.question_type.value,
    }
)
```

## Requirements

### Functional Requirements

1. **Vector Search Integration**
   - Retrieve 3-5 similar questions as exemplars
   - Filter by question type and difficulty
   - Handle empty result set gracefully

2. **Exemplar-Based Generation**
   - Pass exemplar questions to LLM
   - LLM generates new question inspired by exemplars
   - Maintain consistency with CV context

3. **Embedding Storage**
   - Store question embeddings after generation
   - Include metadata for filtering
   - Support vector search queries

4. **Error Handling**
   - Fallback to non-exemplar generation if vector search fails
   - Rollback questions on error (existing logic)
   - Log vector search failures

### Non-Functional Requirements

1. **Performance**
   - Vector search < 500ms per query
   - Total planning time < 30 seconds for 5 questions
   - Parallel embedding generation (future optimization)

2. **Testability**
   - Support MockVectorSearchAdapter for unit tests
   - Mock exemplar results for consistent tests
   - Verify vector search calls in tests

3. **Maintainability**
   - Clean separation of concerns
   - Clear error messages
   - Comprehensive logging

## Architecture

### Component Changes

**PlanInterviewUseCase**:
```python
class PlanInterviewUseCase:
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

**LLMPort Extension** (optional parameter):
```python
class LLMPort(ABC):
    @abstractmethod
    async def generate_question(
        self,
        context: dict[str, Any],
        skill: str,
        difficulty: str,
        exemplars: list[dict[str, Any]] | None = None,  # NEW (optional)
    ) -> str:
        """Generate question, optionally using exemplars."""
        pass
```

**VectorSearchPort** (existing methods used):
```python
class VectorSearchPort(ABC):
    async def get_embedding(self, text: str) -> list[float]: ...
    async def find_similar_questions(
        self, query_embedding, top_k, filters
    ) -> list[dict]: ...
    async def store_question_embedding(
        self, question_id, embedding, metadata
    ) -> None: ...
```

### Dependency Injection

Update `Container.py`:
```python
def plan_interview_use_case(self, session: AsyncSession) -> PlanInterviewUseCase:
    return PlanInterviewUseCase(
        llm=self.llm_port(),
        vector_search=self.vector_search_port(),  # NEW
        cv_analysis_repo=self.cv_analysis_repository_port(session),
        interview_repo=self.interview_repository_port(session),
        question_repo=self.question_repository_port(session),
    )
```

### Sequence Diagram

```
User → API: POST /interviews/plan
API → PlanInterviewUseCase: execute(cv_analysis_id, candidate_id)
PlanInterviewUseCase → CVAnalysisRepo: get_by_id(cv_analysis_id)
CVAnalysisRepo → PlanInterviewUseCase: CVAnalysis

PlanInterviewUseCase → InterviewRepo: save(Interview[PREPARING])

loop For each question i=1..n
    PlanInterviewUseCase → VectorSearch: get_embedding(query_text)
    VectorSearch → PlanInterviewUseCase: query_embedding

    PlanInterviewUseCase → VectorSearch: find_similar_questions(query_embedding)
    VectorSearch → PlanInterviewUseCase: exemplar_questions[]

    PlanInterviewUseCase → LLM: generate_question(context, skill, exemplars)
    LLM → PlanInterviewUseCase: question_text

    PlanInterviewUseCase → LLM: generate_ideal_answer(question_text)
    LLM → PlanInterviewUseCase: ideal_answer

    PlanInterviewUseCase → LLM: generate_rationale(question, answer)
    LLM → PlanInterviewUseCase: rationale

    PlanInterviewUseCase → QuestionRepo: save(Question)

    PlanInterviewUseCase → VectorSearch: get_embedding(question.text)
    VectorSearch → PlanInterviewUseCase: question_embedding

    PlanInterviewUseCase → VectorSearch: store_question_embedding(...)
end

PlanInterviewUseCase → InterviewRepo: update(Interview[READY])
PlanInterviewUseCase → API: Interview
API → User: 202 Accepted (Interview ready)
```

## Related Code Files

**Use Case**:
- `src/application/use_cases/plan_interview.py` (MODIFY)

**Domain Ports**:
- `src/domain/ports/llm_port.py` (EXTEND - optional parameter)
- `src/domain/ports/vector_search_port.py` (USE existing)

**Adapters**:
- `src/adapters/llm/openai_adapter.py` (MODIFY)
- `src/adapters/mock/mock_llm_adapter.py` (MODIFY)
- `src/adapters/vector_db/pinecone_adapter.py` (USE existing)
- `src/adapters/mock/mock_vector_search_adapter.py` (USE existing)

**Infrastructure**:
- `src/infrastructure/dependency_injection/container.py` (MODIFY)

**API**:
- `src/adapters/api/rest/interview_routes.py` (REVIEW - may need updates)

**Tests**:
- `tests/unit/use_cases/test_plan_interview.py` (CREATE/MODIFY)
- `tests/integration/test_plan_interview_integration.py` (CREATE)

## Implementation Steps

### Step 1: Extend LLM Port Interface (Optional Parameter)
- [ ] Add `exemplars` parameter to `generate_question()` method
- [ ] Update docstring with exemplar usage
- [ ] Ensure backward compatibility (default=None)

### Step 2: Update OpenAI Adapter
- [ ] Modify `generate_question()` to accept exemplars
- [ ] Update prompt engineering to use exemplars
- [ ] Test prompt with sample exemplars
- [ ] Add logging for exemplar usage

### Step 3: Update MockLLM Adapter
- [ ] Add exemplar parameter support
- [ ] Return deterministic questions for testing
- [ ] Ensure tests remain predictable

### Step 4: Refactor PlanInterviewUseCase
- [ ] Add VectorSearchPort to constructor
- [ ] Create `_get_query_embedding()` helper method
- [ ] Create `_find_exemplar_questions()` helper method
- [ ] Modify `_generate_question_with_ideal_answer()` to use exemplars
- [ ] Add `_store_question_embedding()` method
- [ ] Update error handling for vector search failures
- [ ] Add logging for vector operations

### Step 5: Update Dependency Injection
- [ ] Inject VectorSearchPort into use case
- [ ] Ensure mock adapters work in tests
- [ ] Test with real adapters in integration

### Step 6: Testing
- [ ] Unit tests with MockVectorSearch
- [ ] Verify exemplar retrieval logic
- [ ] Test fallback when no exemplars found
- [ ] Integration tests with real Pinecone
- [ ] Performance testing

## Todo List

- [x] Analyze current implementation
- [x] Design vector search integration
- [x] Document flow and architecture
- [x] Define interface changes
- [ ] Create Phase 2 plan (LLM Port Enhancement)
- [ ] Create Phase 3 plan (Vector Search Integration)
- [ ] Create Phase 4 plan (API Endpoint)

## Success Criteria

- [x] Current implementation fully analyzed
- [x] New flow designed and documented
- [x] Architectural decisions documented
- [x] Interface changes defined
- [x] Sequence diagram created
- [ ] Team review completed
- [ ] Phase 2 plan approved

## Risk Assessment

### Technical Risks

**Risk**: Vector DB may not have sufficient exemplar questions
- **Mitigation**: Seed database with 50+ example questions covering various skills/difficulties
- **Fallback**: Generate questions without exemplars if search returns < 1 result

**Risk**: LLM prompt engineering complex for exemplar-based generation
- **Mitigation**: Iterative prompt refinement with A/B testing
- **Fallback**: Reduce exemplar count or omit if quality degraded

**Risk**: Performance impact of additional vector search calls
- **Mitigation**: Implement caching for frequent queries
- **Target**: Vector search < 500ms per query

**Risk**: Breaking changes to LLMPort interface
- **Mitigation**: Make exemplars parameter optional (backward compatible)
- **Strategy**: Gradual rollout with feature flag

### Implementation Risks

**Risk**: Complex refactoring may introduce bugs
- **Mitigation**: Comprehensive unit tests with mock adapters
- **Coverage Target**: >80% code coverage

**Risk**: Integration testing requires real API keys
- **Mitigation**: Use mock adapters by default, integration tests optional
- **Environment**: USE_MOCK_ADAPTERS=true in dev

## Security Considerations

### Data Privacy
- Question exemplars may contain sensitive information
- **Action**: Sanitize metadata before storing in vector DB
- **Action**: Implement access controls on vector DB

### API Security
- Vector search queries may be exploited for data extraction
- **Action**: Rate limiting on API endpoints
- **Action**: Input validation on search parameters

### Error Handling
- Don't expose internal errors to API consumers
- **Action**: Generic error messages for production
- **Action**: Detailed logging for debugging

## Next Steps

1. **Create Phase 2 Plan**: LLM Port Enhancement (exemplar parameter)
2. **Create Phase 3 Plan**: Vector Search Integration (use case refactor)
3. **Create Phase 4 Plan**: Unified API Endpoint (CV upload + planning)
4. **Team Review**: Architectural decisions and interface changes
5. **Seed Vector DB**: Create exemplar question dataset (50+ questions)
6. **Begin Implementation**: Phase 2 (LLM adapter changes)

## Unresolved Questions

1. **Exemplar Count**: Use 3 or 5 exemplar questions? (Trade-off: quality vs. prompt length)
2. **Caching Strategy**: Cache vector search results? For how long?
3. **Seed Data**: Who creates exemplar questions? Manual or LLM-generated?
4. **Performance Target**: Is 30 seconds acceptable for 5 questions, or aim for <20s?
5. **API Design**: Unified CV upload endpoint or keep separate? (Phase 4 decision)
6. **Backward Compatibility**: Support old questions without embeddings?

---

**Document Status**: Complete
**Next Review**: Before Phase 2 implementation
**Approved By**: TBD
