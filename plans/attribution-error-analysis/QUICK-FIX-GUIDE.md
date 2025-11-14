# Quick Fix Guide - AttributeError: 'MockLLMAdapter' has no attribute 'client'

## Problem (30 seconds)

```python
# ❌ WRONG (lines 334, 432 in process_answer_adaptive.py)
response = await self.llm.client.chat.completions.create(...)
```

**Why it breaks**:
- `MockLLMAdapter` doesn't have `.client` attribute
- `OpenAIAdapter` does (but it's an implementation detail)
- Use case should use port methods, not adapter internals

## Quick Fix (5 minutes) - RECOMMENDED

### Step 1: Add to `src/domain/ports/llm_port.py`
```python
@abstractmethod
async def detect_concept_gaps(
    self, answer_text: str, ideal_answer: str,
    question_text: str, keyword_gaps: list[str]
) -> dict[str, Any]:
    pass

@abstractmethod
async def generate_followup_question(
    self, parent_question: str, answer_text: str,
    missing_concepts: list[str], severity: str, order: int
) -> str:
    pass
```

### Step 2: Add to `src/adapters/llm/mock_adapter.py`
```python
async def detect_concept_gaps(self, answer_text: str, ideal_answer: str,
                               question_text: str, keyword_gaps: list[str]) -> dict[str, Any]:
    word_count = len(answer_text.split())
    if word_count < 30:
        return {"concepts": keyword_gaps[:2], "confirmed": True, "severity": "moderate"}
    return {"concepts": [], "confirmed": False, "severity": "minor"}

async def generate_followup_question(self, parent_question: str, answer_text: str,
                                      missing_concepts: list[str], severity: str, order: int) -> str:
    concepts_str = ', '.join(missing_concepts[:2]) if missing_concepts else "that"
    return f"Can you elaborate on {concepts_str}? Provide examples."
```

### Step 3: Add to `src/adapters/llm/openai_adapter.py`
```python
async def detect_concept_gaps(self, answer_text: str, ideal_answer: str,
                               question_text: str, keyword_gaps: list[str]) -> dict[str, Any]:
    prompt = f"Question: {question_text}\nIdeal: {ideal_answer}\nAnswer: {answer_text}\n" \
             f"Missing keywords: {', '.join(keyword_gaps[:10])}\n\n" \
             f"Return JSON: concepts[], confirmed (bool), severity (minor/moderate/major)"

    response = await self.client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Identify real conceptual gaps, not synonyms."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content or "{}")
    return {
        "concepts": result.get("concepts", []),
        "keywords": keyword_gaps[:5],
        "confirmed": result.get("confirmed", False),
        "severity": result.get("severity", "minor")
    }

async def generate_followup_question(self, parent_question: str, answer_text: str,
                                      missing_concepts: list[str], severity: str, order: int) -> str:
    prompt = f"Original: {parent_question}\nAnswer: {answer_text}\n" \
             f"Missing: {', '.join(missing_concepts)}\nSeverity: {severity}\n\n" \
             f"Generate concise follow-up #{order} targeting missing concepts."

    response = await self.client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate targeted follow-up questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=150
    )

    return response.choices[0].message.content.strip() or "Can you elaborate?"
```

### Step 4: Fix `src/application/use_cases/process_answer_adaptive.py`

**Line 334** - Replace entire method:
```python
async def _detect_gaps_with_llm(self, answer_text: str, ideal_answer: str,
                                 question_text: str, keyword_gaps: list[str]) -> dict[str, Any]:
    """Use LLM to confirm gap detection."""
    return await self.llm.detect_concept_gaps(
        answer_text=answer_text,
        ideal_answer=ideal_answer,
        question_text=question_text,
        keyword_gaps=keyword_gaps
    )
```

**Line 432** - Replace in `_generate_followup()`:
```python
async def _generate_followup(self, interview_id: UUID, parent_question: Any,
                              answer: Answer, gaps: dict[str, Any], order: int) -> FollowUpQuestion:
    missing_concepts = gaps.get("concepts", [])
    severity = gaps.get("severity", "moderate")

    # ✅ Use port method
    follow_up_text = await self.llm.generate_followup_question(
        parent_question=parent_question.text,
        answer_text=answer.text,
        missing_concepts=missing_concepts,
        severity=severity,
        order=order
    )

    return FollowUpQuestion(
        parent_question_id=parent_question.id,
        interview_id=interview_id,
        text=follow_up_text,
        generated_reason=f"Missing: {', '.join(missing_concepts[:3])}",
        order_in_sequence=order
    )
```

### Step 5: Fix Test Fixture
`tests/unit/use_cases/test_process_answer_adaptive.py`:
```python
@pytest.fixture
def sample_interview_adaptive(sample_candidate):
    interview = Interview(
        candidate_id=sample_candidate.id,
        status=InterviewStatus.READY,
        plan_metadata={},
        adaptive_follow_ups=[]
    )
    interview.start()  # ✅ FIX: Change to IN_PROGRESS
    return interview
```

## Test
```bash
pytest tests/unit/use_cases/test_process_answer_adaptive.py -v
# Should pass 14/14 tests
```

## Files Modified
1. `src/domain/ports/llm_port.py` (+2 methods)
2. `src/adapters/llm/mock_adapter.py` (+2 methods)
3. `src/adapters/llm/openai_adapter.py` (+2 methods)
4. `src/application/use_cases/process_answer_adaptive.py` (2 method updates)
5. `tests/unit/use_cases/test_process_answer_adaptive.py` (1 fixture fix)

## Root Cause
Use case bypassed port abstraction to access OpenAI-specific API directly. Violates Clean Architecture.

## See Full Report
`./plans/attribution-error-analysis/251109-llm-client-violation-report.md`
