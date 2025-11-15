# Plan Summary: QA Question Constraints

**Date**: 2025-11-15
**Plan ID**: 251115-0717-qa-question-constraints
**Status**: READY FOR IMPLEMENTATION
**Complexity**: Low
**Estimated Effort**: 1-2 hours

## Overview

Plan adds explicit prompt constraints to prevent LLM from generating unsuitable interview questions (code writing, diagram drawing, whiteboard exercises). Maintains discussion-based, verbal QA interview format.

## Target Files

**3 Adapter Files Modified**:
1. `src/adapters/llm/openai_adapter.py` - Update `generate_question()` (lines 39-88)
2. `src/adapters/llm/azure_openai_adapter.py` - Update `generate_question()` (lines 48-97)
3. `src/adapters/mock/mock_llm_adapter.py` - Update `generate_question()` (lines 20-44)

**Domain/Application Layers**: No changes (port interface unchanged)

## Implementation Approach

### Constraint Language
```
**IMPORTANT CONSTRAINTS**:
The question MUST be verbal/discussion-based. DO NOT generate questions that require:
- Writing code ("write a function", "implement", "create a class", "code a solution")
- Drawing diagrams ("draw", "sketch", "diagram", "visualize", "map out")
- Whiteboard exercises ("design on whiteboard", "show on board", "illustrate")
- Visual outputs ("create a flowchart", "design a schema visually")

Focus on conceptual understanding, best practices, trade-offs, and problem-solving approaches that can be explained verbally.
```

### Placement Strategy
- Insert AFTER exemplars section (if present)
- Insert BEFORE final instruction ("Return only question text...")
- Use bold header (**IMPORTANT CONSTRAINTS**) for emphasis
- Same constraint block in all adapters (consistency)

## Changes Per File

### OpenAI Adapter
- Insert constraint block after line 74 (exemplar section)
- Before line 76 (final instruction)
- No signature changes

### Azure OpenAI Adapter
- Insert IDENTICAL constraint block after line 83
- Before line 85 (final instruction)
- Mirror OpenAI approach exactly

### Mock Adapter
- Change base question from `"Mock question about {skill}..."`
- To `"Explain the trade-offs when using {skill}..."`
- Update docstring to mention constraint alignment
- Preserve exemplar indicator for testing

## Testing Strategy

### Manual Testing Matrix
| Skill | Difficulty | Adapter | Expected |
|-------|------------|---------|----------|
| Python | easy | OpenAI | Conceptual (no code writing) |
| React | hard | OpenAI | Best practices/trade-offs |
| SQL | medium | Azure | Query explanation (not "write query") |
| DevOps | hard | Azure | Architecture discussion (not diagram) |
| FastAPI | easy | Mock | Trade-offs explanation |

### Success Criteria
- ✅ 0/10 code writing tasks in manual testing
- ✅ 0/10 diagram tasks in manual testing
- ✅ 10/10 questions discussion-based ("Explain", "Describe", etc.)
- ✅ Questions remain skill-relevant and difficulty-appropriate
- ✅ Exemplar-based generation still functional
- ✅ Existing tests pass unchanged

### Failure Triggers
- >2 code writing tasks in 10 test questions
- >1 diagram task in 10 test questions
- Questions too generic/vague
- LLM refusals due to overly restrictive constraints

## Architecture Compliance

**Clean Architecture Principles** ✅:
- Changes confined to adapter layer
- Domain port interface unchanged
- No business logic modifications
- Swappable implementations maintained

**YAGNI, KISS, DRY** ✅:
- YAGNI: Only implementing constraint addition (no validation infrastructure)
- KISS: Simple prompt addition, no complex logic
- DRY: Same constraint text reused across adapters

**Backward Compatibility** ✅:
- No method signature changes
- No output format changes
- No breaking API changes
- Existing tests pass without modification

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM ignores constraints | High | Low | Test multiple skills/difficulties; fallback to manual review |
| Constraints too restrictive | Medium | Medium | Allow scenario-based discussions; iterate if needed |
| Inconsistent behavior | Low | Low | Identical constraint text in all adapters |
| Breaking tests | Low | Low | No signature changes; interface unchanged |

**Overall Risk**: LOW

## Rollback Plan

**Trigger Conditions**:
- >20% constraint violations detected
- User complaints about question quality
- LLM refusal rate increases significantly

**Rollback Steps** (Zero downtime):
1. Revert constraint block in OpenAI adapter (remove added lines)
2. Revert constraint block in Azure adapter (remove added lines)
3. Revert mock adapter changes (restore original base_question)
4. No database migrations to rollback
5. No API changes to rollback
6. Deploy during low traffic window

## Excluded from Scope (Phase 2)

**Deferred Items**:
- Automated constraint violation detection (post-generation filter)
- Logging/metrics for violation rate
- A/B testing of constraint language variations
- User feedback collection on question appropriateness
- Integration tests with real LLM calls

**Rationale**:
- Phase 1 addresses immediate need (prevent unsuitable questions)
- Validation adds complexity not required for MVP
- Can iterate based on Phase 1 results

## Documentation Updates

**Required Updates**:
- `docs/system-architecture.md` - Add note in "Question Generation Flow" section
- `docs/code-standards.md` - Update exemplar-based generation pattern description

**No Updates Needed**:
- API documentation (no interface changes)
- Database schema
- README.md

## Next Steps

1. **Implementation** (30 min):
   - Modify OpenAI adapter
   - Modify Azure adapter
   - Modify Mock adapter

2. **Testing** (30-60 min):
   - Manual testing with 10+ skills/difficulties
   - Verify zero code writing tasks
   - Verify zero diagram tasks
   - Check exemplar-based generation

3. **Validation**:
   - Run existing unit tests
   - Code quality checks (ruff, black, mypy)
   - Review constraint consistency

4. **Deployment**:
   - Deploy to staging
   - Monitor initial results
   - Collect feedback

5. **Post-Implementation**:
   - Update documentation
   - Plan Phase 2 (validation/monitoring)
   - Iterate on constraints if needed

## Unresolved Questions

1. **Positive Examples**: Should we add positive examples of good verbal questions in prompt?
   - **Decision**: Test constraints-only approach first; add if needed

2. **Question Type Differentiation**: Should constraints apply differently to TECHNICAL vs BEHAVIORAL?
   - **Decision**: Apply same constraints to all types (behavioral already verbal)

3. **Edge Cases**: How to handle "explain how you would implement..." vs "implement..."?
   - **Decision**: "Explain how you would implement" allowed (discussion-based)

## References

- **Main Plan**: `plan.md`
- **Detailed Implementation**: `phase-01-constraint-implementation.md`
- **Architecture Doc**: `docs/system-architecture.md` (Question Generation Flow section)
- **Code Standards**: `docs/code-standards.md` (Exemplar-Based Generation Pattern)
- **LLM Port**: `src/domain/ports/llm_port.py` (lines 19-41)

---

**Summary Status**: ✅ Plan comprehensive and ready for execution
**Recommendation**: Proceed with implementation following `phase-01-constraint-implementation.md`
