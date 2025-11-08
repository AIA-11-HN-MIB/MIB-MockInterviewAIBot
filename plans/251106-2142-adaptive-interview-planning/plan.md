# Adaptive Interview Planning - Implementation Plan

**Plan ID**: 251106-2142-adaptive-interview-planning
**Created**: 2025-11-06
**Strategy**: Approach 1 (Minimal Changes)
**Target**: Pre-planning interview flow with adaptive follow-ups

## Context

**Repository**: [Codebase Summary](../../docs/codebase-summary.md) | [System Architecture](../../docs/system-architecture.md) | [Code Standards](../../docs/code-standards.md)

**Objective**: Transform interview flow into 2-phase process:
- **Phase 1 (Planning)**: Generate n questions upfront with ideal answers + rationale
- **Phase 2 (Execution)**: Sequential delivery with adaptive follow-ups (0-3) based on gaps

## Overview

Extend existing Clean Architecture with minimal schema changes. Add planning orchestration layer, enhanced evaluation with gap detection, speaking metrics tracking (stub for MVP).

**Key Design Decisions**:
- n = dynamic (5-12 based on CV complexity: junior ~5, senior ~12)
- Follow-up triggers: similarity <80% OR speaking <85% OR concept gaps detected
- Stop conditions: threshold met OR 3 follow-ups max OR improvement trend detected
- Storage: Extend Questions table (`ideal_answer`, `rationale`), Interviews (`plan_metadata`, `adaptive_follow_ups`), Answers (`similarity_score`, `gaps`, `speaking_score`)

## Implementation Phases

### Status Legend
- ⏳ Pending
- 🔄 In Progress
- ✅ Complete
- ❌ Blocked

| Phase                                    | Description               | Status | Priority | Risk   |
|------------------------------------------|---------------------------|--------|----------|--------|
| [01](./phase-01-domain-model-updates.md) | Domain model updates      | ⏳      | P0       | Low    |
| [02](./phase-02-database-migration.md)   | Database schema migration | ⏳      | P0       | Medium |
| [03](./phase-03-planning-use-case.md)    | PlanInterviewUseCase      | ⏳      | P0       | High   |
| [04](./phase-04-adaptive-evaluation.md)  | Adaptive evaluation logic | ⏳      | P0       | High   |
| [05](./phase-05-api-integration.md)      | REST/WebSocket updates    | ⏳      | P1       | Medium |
| [06](./phase-06-testing-validation.md)   | Testing & validation      | ⏳      | P1       | Low    |

## High-Level Architecture Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEW INTERVIEW FLOW                           │
└─────────────────────────────────────────────────────────────────┘

Phase 1: PRE-PLANNING (status: PREPARING → READY)
┌─────────────────────────────────────────────────────────────────┐
│ PlanInterviewUseCase                                             │
│  ├─→ Calculate n (5-12) based on CV complexity                  │
│  ├─→ Generate n questions (LLMPort)                             │
│  ├─→ For each question:                                         │
│  │    ├─→ Generate ideal_answer (LLMPort)                       │
│  │    ├─→ Generate rationale/"why" (LLMPort)                    │
│  │    └─→ Store in Questions table                              │
│  ├─→ Store plan_metadata in Interview (n, generated_at)         │
│  └─→ Mark Interview.status = READY                              │
└─────────────────────────────────────────────────────────────────┘

Phase 2: IN-INTERVIEW (status: IN_PROGRESS)
┌─────────────────────────────────────────────────────────────────┐
│ For each main question (1..n):                                   │
│  ├─→ Deliver question via WebSocket/REST                        │
│  ├─→ ProcessAnswerAdaptiveUseCase:                              │
│  │    ├─→ Evaluate answer (LLMPort)                             │
│  │    ├─→ Calculate similarity vs ideal_answer (VectorPort)     │
│  │    ├─→ Detect concept gaps (NLP analysis)                    │
│  │    ├─→ Analyze speaking metrics (SpeakingAnalyzerPort)       │
│  │    └─→ Store Answer with metrics (similarity, gaps, speaking)│
│  ├─→ IF need_followup(similarity <80% OR speaking <85% OR gaps):│
│  │    ├─→ Generate targeted follow-up (LLMPort)                 │
│  │    ├─→ Add to adaptive_follow_ups[] in Interview             │
│  │    ├─→ Deliver follow-up question                            │
│  │    └─→ Repeat (max 3 follow-ups OR threshold met)            │
│  └─→ Move to next main question                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Files to Create/Modify

### New Files (8)
- `src/domain/ports/speaking_analyzer_port.py` - Speaking metrics interface
- `src/application/use_cases/plan_interview.py` - Planning orchestration
- `src/application/use_cases/evaluate_answer_adaptive.py` - Enhanced evaluation
- `src/adapters/analytics/analytics_service.py` - Answer metrics tracking
- `src/adapters/speech/speaking_analyzer_stub.py` - MVP stub for speaking metrics
- `alembic/versions/xxx_add_planning_fields.py` - Schema migration
- `tests/unit/use_cases/test_plan_interview.py` - Planning tests
- `tests/integration/test_adaptive_flow.py` - End-to-end tests

### Modified Files (7)
- `src/domain/models/question.py` - Add ideal_answer, rationale
- `src/domain/models/interview.py` - Add plan_metadata, adaptive_follow_ups
- `src/domain/models/answer.py` - Add similarity_score, gaps, speaking_score
- `src/adapters/persistence/models.py` - Update DB models
- `src/adapters/persistence/mappers.py` - Update mappers
- `src/adapters/llm/openai_adapter.py` - Add ideal_answer generation
- `src/infrastructure/dependency_injection/container.py` - Wire new ports

## Success Criteria

- [ ] All 5 domain models updated (Question, Interview, Answer, FollowUpQuestion)
- [ ] Database migration runs cleanly (forward + rollback)
- [ ] PlanInterviewUseCase generates 2-5 questions based on skill count in <40s
- [ ] EvaluateAnswerAdaptiveUseCase triggers follow-ups based on similarity + gaps
- [ ] Follow-up logic stops at 3 attempts or threshold (similarity ≥80% OR no gaps)
- [ ] Hybrid gap detection (keywords → LLM validation) implemented
- [ ] REST endpoints handle planning phase
- [ ] WebSocket delivers follow-up questions seamlessly
- [ ] Test coverage >80% for new code
- [ ] Backward compatible with existing interviews (status != PREPARING)

## Risk Assessment

**High Risks**:
- **LLM cost**: n * (1 question + 1 ideal_answer + 1 rationale) = 3n API calls during planning
  - *Mitigation*: Batch prompts, use cheaper model for rationale (gpt-3.5-turbo)
- **Planning latency**: 90s for 12 questions unacceptable
  - *Mitigation*: Async planning as background job, show progress bar
- **Gap detection accuracy**: NLP-based gap detection may produce false positives
  - *Mitigation*: Start with simple keyword matching, iterate based on metrics

**Medium Risks**:
- Schema migration on production interviews
  - *Mitigation*: Add columns as nullable, backfill old data
- Follow-up loop complexity
  - *Mitigation*: Clear state machine, comprehensive unit tests

## Performance Targets

- Planning phase: <40s for 5 questions (avg 8s/question)
- Answer evaluation: <5s (includes similarity calc + gap detection)
- Follow-up generation: <3s
- No speaking metrics (skipped for MVP)

## Security Considerations

- Ideal answers contain sensitive technical knowledge → ensure proper access control
- Plan metadata may expose interview structure → sanitize in API responses
- Follow-up rationale could reveal AI logic → mask in candidate-facing endpoints

## Next Steps

1. **Start with Phase 01**: Domain model updates (low risk, foundation for all)
2. **Then Phase 02**: Database migration (test on staging first)
3. **Implement Phase 03**: Planning use case (core new functionality)
4. **Build Phase 04**: Adaptive evaluation (complex logic)
5. **Integrate Phase 05**: API updates (connect all pieces)
6. **Validate Phase 06**: Testing (ensure quality)

## Resolved Decisions (2025-11-06)

1. ✅ **n-calculation algorithm**: Based on skill diversity only (max n=5)
   - 1-2 skills: n=2
   - 3-4 skills: n=3
   - 5-7 skills: n=4
   - 8+ skills: n=5
   - **Ignore experience years entirely**

2. ✅ **Gap detection method**: Hybrid (Keywords + LLM confirmation)
   - Fast keyword extraction to detect potential gaps
   - LLM validates if gaps are real (reduces false positives)
   - Balanced cost/accuracy trade-off

3. ✅ **Speaking metrics**: **SKIP for MVP**
   - Remove speaking_score from Answer model
   - Follow-up logic based on similarity + gaps only
   - Can add Azure Speech integration in future phase

4. ✅ **Follow-up storage**: **Separate FollowUpQuestions table**
   - Cleaner architecture than extending Questions
   - Schema: id, parent_question_id, interview_id, text, generated_reason, order, timestamps
   - Easier to query and manage follow-up history

5. ⏳ **Cost optimization**: Sequential for MVP (parallel in future)
6. ⏳ **Caching strategy**: No caching for MVP (evaluate based on usage)

## Plan Adjustments

**Phase 01 Changes**:
- ❌ Remove speaking_score from Answer model
- ✅ Add FollowUpQuestion domain entity (new)

**Phase 02 Changes**:
- ❌ Remove speaking_score column from answers table
- ✅ Add follow_up_questions table with schema

**Phase 04 Changes**:
- ❌ Remove SpeakingAnalyzerPort and stub adapter
- ✅ Implement hybrid gap detection (keywords → LLM)
- ✅ Simplify follow-up logic (no speaking metrics)

---

**Document Status**: Decisions resolved, ready for implementation
**Next Action**: Update phase files, start Phase 01
**Owner**: Implementation team
