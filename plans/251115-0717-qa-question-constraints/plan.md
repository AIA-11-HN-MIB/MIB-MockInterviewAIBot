# Implementation Plan: QA Question Constraints

**Plan ID**: 251115-0717-qa-question-constraints
**Created**: 2025-11-15
**Status**: Ready for Implementation
**Complexity**: Low (Phase 1 only)
**Estimated Effort**: 1-2 hours

## Summary

Add explicit prompt constraints to prevent LLM from generating unsuitable QA interview questions (code writing tasks, diagram drawing, whiteboard exercises, system design diagrams). Focus on verbal/discussion-based questions suitable for QA interview format.

## Problem Statement

Current LLM prompts in question generation lack explicit constraints preventing:
- Code writing tasks ("write a function to...", "implement a class...")
- Diagram drawing ("draw a system architecture...", "create a diagram...")
- Whiteboard exercises ("design the schema...", "sketch the solution...")
- System design diagrams (any task requiring visual/drawing output)

These task types are unsuitable for verbal QA interview format.

## Goals

**Primary Goals**:
- Prevent generation of code writing tasks
- Prevent generation of diagram/drawing tasks
- Maintain existing exemplar-based approach
- Preserve all current prompt context (CV summary, skills, experience, covered topics, stage)
- Keep JSON structured outputs where applicable

**Non-Goals**:
- Not changing evaluation logic
- Not modifying follow-up question generation constraints (already conversational)
- Not adding new LLM models
- Not changing question bank structure

## Architecture Context

**Clean Architecture Pattern**:
- Adapters implement domain port `LLMPort` (defined in `src/domain/ports/llm_port.py`)
- Domain remains unchanged (port interface stays same)
- Only adapter implementations modified (prompts)

**Target Adapters**:
1. `src/adapters/llm/openai_adapter.py` - Primary implementation (625 lines)
2. `src/adapters/llm/azure_openai_adapter.py` - Azure variant (660 lines)
3. `src/adapters/mock/mock_llm_adapter.py` - Mock for testing (355 lines)

## Current State Analysis

**Method**: `generate_question()` (all 3 adapters)
- **Model**: gpt-4 (OpenAI), deployment (Azure), mock
- **Temperature**: 0.7
- **Output**: Plain text (no JSON)
- **Current Prompt**:
  ```
  System: "You are an expert technical interviewer. Generate a clear, relevant interview question..."
  User: "Generate a {difficulty} difficulty interview question to test: {skill}
         Context: CV summary, covered topics, stage
         [Exemplars if provided - 3 max]
         Return only the question text, no additional explanation."
  ```
- **Constraints**: None currently

**Method**: `generate_followup_question()` (all 3 adapters)
- **Model**: gpt-3.5-turbo (OpenAI/Azure), mock
- **Temperature**: 0.4
- **Output**: Plain text
- **Current Prompt**: Already conversational ("Can you elaborate...")
- **No changes needed**: Follow-ups already verbal by nature

## Solution Design

### Constraint Language

Add explicit exclusion list to `generate_question()` prompts:

```
The question MUST be verbal/discussion-based. DO NOT generate questions that require:
- Writing code ("write a function", "implement", "create a class")
- Drawing diagrams ("draw", "sketch", "diagram", "visualize")
- Whiteboard exercises ("design on whiteboard", "show on board")
- Visual outputs ("create a flowchart", "map out", "illustrate")

Focus on conceptual understanding, best practices, trade-offs, problem-solving approaches that can be explained verbally.
```

**Rationale**:
- Clear and explicit (no ambiguity)
- Lists specific phrases to avoid
- Provides positive guidance (focus on conceptual understanding)
- Doesn't overly restrict (allows scenario-based questions involving code discussion)

### Placement in Prompt

Insert constraints AFTER exemplars section, BEFORE final instruction:

```python
user_prompt += """
[EXEMPLARS SECTION IF PROVIDED]

**IMPORTANT CONSTRAINTS**:
The question MUST be verbal/discussion-based. DO NOT generate questions that require:
- Writing code ("write a function", "implement", "create a class")
- Drawing diagrams ("draw", "sketch", "diagram", "visualize")
- Whiteboard exercises ("design on whiteboard", "show on board")
- Visual outputs ("create a flowchart", "map out", "illustrate")

Focus on conceptual understanding, best practices, trade-offs, problem-solving approaches that can be explained verbally.

Return only the question text, no additional explanation.
"""
```

**Why this placement**:
- After exemplars (constraints apply to generation, not exemplar retrieval)
- Before final instruction (last thing LLM sees before generating)
- Bold header (emphasizes importance)
- Negative framing (DO NOT) followed by positive framing (Focus on)

## Implementation Phases

### Phase 1: Core Constraint Implementation (This Plan)

**Scope**: Add constraints to main question generation method in all 3 adapters

**Files Modified**:
1. `src/adapters/llm/openai_adapter.py` - `generate_question()` method (lines 39-88)
2. `src/adapters/llm/azure_openai_adapter.py` - `generate_question()` method (lines 48-97)
3. `src/adapters/mock/mock_llm_adapter.py` - `generate_question()` method (lines 20-44)

**Changes per file**:
- Insert constraint block after exemplars section (if present)
- Insert constraint block before final instruction
- No other changes to prompt structure

**Testing**:
- Manual testing via POST /api/interviews/plan (checks if questions are conversational)
- Verify exemplar-based generation still works
- Check mock adapter responses align with constraints

**Success Criteria**:
- No code writing questions generated
- No diagram/drawing questions generated
- Exemplar-based generation still functional
- Existing tests pass (no breaking changes)

### Phase 2: Validation & Monitoring (Future - Not in This Plan)

**Deferred Scope**:
- Add automated detection for constraint violations (post-generation filter)
- Logging/metrics for constraint violation rate
- A/B testing of constraint language variations
- User feedback collection on question appropriateness
- Integration tests with actual LLM calls

**Rationale for deferral**:
- Phase 1 addresses immediate need (prevent unsuitable questions)
- Validation adds complexity not required for MVP
- Monitoring requires infrastructure not currently in place
- Can iterate based on Phase 1 results

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM ignores constraints | High | Low | Test with multiple example skills/difficulties; fallback to manual review |
| Constraints too restrictive | Medium | Medium | Allow scenario-based questions with code discussion (not code writing) |
| Inconsistent across adapters | Low | Low | Use identical constraint language in all 3 adapters |
| Breaking existing tests | Low | Low | No changes to method signature or output format; existing tests should pass |

## Success Metrics

**Qualitative**:
- Manual review of 20 generated questions shows 0 code writing tasks
- Manual review shows 0 diagram/drawing tasks
- Questions remain relevant and skill-appropriate

**Quantitative** (future Phase 2):
- <5% constraint violation rate (automated detection)
- User feedback rating >4.0/5 for question appropriateness
- No increase in question generation latency

## Rollback Plan

If constraints cause issues:
1. Revert prompt changes (simple text removal)
2. No database migrations involved
3. No API changes (interface unchanged)
4. Zero downtime (deploy during low traffic)

**Rollback trigger**:
- >20% constraint violations detected
- User complaints about question quality
- LLM refusal rate increases significantly

## Testing Strategy

**Manual Testing** (Phase 1):
1. Generate questions for 10 different skills (Python, React, SQL, DevOps, etc.)
2. Vary difficulty (easy, medium, hard)
3. Test with and without exemplars
4. Verify 0 code writing tasks
5. Verify 0 diagram tasks
6. Check mock adapter responses

**Automated Testing** (future Phase 2):
- Integration tests with real LLM calls
- Regex-based constraint violation detection
- Performance benchmarks (latency)

## Dependencies

**External**:
- None (pure prompt engineering change)

**Internal**:
- No code dependencies (self-contained changes)
- No database changes
- No API changes

## Documentation Updates

**Files to update**:
- `docs/system-architecture.md` - Add note about question generation constraints (section "Question Generation Flow")
- `docs/code-standards.md` - Update exemplar-based generation pattern description (mention constraints)

**No updates needed**:
- API documentation (no interface changes)
- Database schema
- README.md

## Unresolved Questions

1. Should we add positive examples of good verbal questions in prompt? (e.g., "Good: 'Explain the trade-offs between...'")
   - **Decision deferred**: Test constraints-only approach first; add positive examples if needed

2. Should constraints apply to different question types differently? (TECHNICAL vs BEHAVIORAL)
   - **Decision**: Apply same constraints to all types; behavioral questions already verbal by nature

3. How to handle edge cases like "explain how you would implement..." vs "implement..."?
   - **Decision**: "Explain how you would implement" is allowed (discussion-based); "Implement" alone is not

## Next Steps

1. Implement Phase 1 changes (see `phase-01-constraint-implementation.md`)
2. Manual testing with 10+ skills/difficulties
3. Deploy to staging environment
4. Collect initial feedback
5. Iterate on constraint language if needed
6. Plan Phase 2 (validation & monitoring)

---

**Plan Status**: ✅ COMPLETED (Phase 1)
**Completion Date**: 2025-11-15
**Implementation Guide**: See `phase-01-constraint-implementation.md` for completed implementation details
**Completion Summary**: See `IMPLEMENTATION_COMPLETE.md`
