# Plan: Refactor Plan Interview Flow with Vector-Based Question Generation

**Date**: 2025-11-11
**Status**: Planning
**Priority**: High
**Epic**: EA-10 Adaptive Interview Implementation

## Overview

Refactor `plan_interview.py` use case to implement CV-based interview planning with vector search for exemplar-driven question generation. Align with sequence diagram requirements: CV upload → CV analysis → Question generation (using vector exemplars) → Store questions → Mark interview READY.

## Context

Current implementation generates questions sequentially using only LLM without vector search. New requirement: use vector DB to retrieve similar questions as exemplars before generating new questions, enabling better question quality and consistency.

## Scope

- Refactor `PlanInterviewUseCase` to integrate vector search
- Enhance LLM adapter methods for exemplar-based generation
- Update API endpoint to support unified CV upload + planning flow
- Maintain backward compatibility with existing interviews
- Support both real and mock adapters

## Phases

### Phase 1: Analysis & Design ✅
**Status**: Complete
**Duration**: 1 day
- Analyze current implementation
- Design vector search integration approach
- Define interface changes
- Document architectural decisions

### Phase 2: Enhance LLM Port for Exemplar-Based Generation
**Status**: Pending
**Duration**: 2 days
- Add exemplar parameter to `generate_question()` method
- Update OpenAI adapter implementation
- Update MockLLM adapter for testing
- Add unit tests

### Phase 3: Integrate Vector Search into Question Generation
**Status**: Pending
**Duration**: 3 days
- Refactor `PlanInterviewUseCase._generate_question_with_ideal_answer()`
- Add vector search for similar questions
- Implement exemplar-based question generation flow
- Add error handling and fallback logic
- Update unit tests

### Phase 4: Unified CV Upload API Endpoint
**Status**: Pending
**Duration**: 2 days
- Create new POST /interview/cv endpoint
- Integrate CV upload, analysis, and planning
- Update API documentation
- Add integration tests

### Phase 5: Database Schema Validation
**Status**: Pending
**Duration**: 1 day
- Verify question embedding storage
- Test vector search queries
- Validate question metadata structure
- Performance testing

### Phase 6: Testing & Documentation
**Status**: Pending
**Duration**: 2 days
- Comprehensive unit tests (mock adapters)
- Integration tests (real adapters)
- Update API documentation
- Update architecture docs

## Success Criteria

- Vector search successfully retrieves exemplar questions
- LLM generates questions using exemplars
- Questions stored with proper embeddings
- API endpoint handles full CV → interview flow
- All tests pass (unit + integration)
- Documentation complete

## Risks

- Vector DB may not have sufficient exemplar questions (seed data needed)
- LLM prompt engineering for exemplar-based generation requires tuning
- Performance impact of vector search calls (caching needed)
- Breaking changes to existing LLM port interface

## Dependencies

- VectorSearchPort implementation (Pinecone/ChromaDB)
- LLMPort implementation (OpenAI/Mock)
- Question repository with embedding support
- Seed data for vector DB (exemplar questions)

## Notes

- Maintain Clean Architecture principles
- Support both mock and real adapters
- Keep backward compatibility where possible
- Follow existing code standards and patterns

---

**Total Estimated Duration**: 11 days
**Next Review**: After Phase 2 completion
