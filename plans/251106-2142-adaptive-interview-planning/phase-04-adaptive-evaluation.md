# Phase 04: Adaptive Evaluation & Follow-ups

**Phase ID**: phase-04-adaptive-evaluation
**Created**: 2025-11-06
**Status**: ⏳ Pending
**Priority**: P0 (Critical)
**Estimated Effort**: 12 hours

## Context

**Parent Plan**: [Main Plan](./plan.md)
**Dependencies**: [Phase 01](./phase-01-domain-model-updates.md), [Phase 02](./phase-02-database-migration.md), [Phase 03](./phase-03-planning-use-case.md)
**Related Docs**: [OpenAI Adapter](../../src/adapters/llm/openai_adapter.py) | [Vector Adapter](../../src/adapters/vector_db/pinecone_adapter.py)

## Overview

Replace ProcessAnswerUseCase with EvaluateAnswerAdaptiveUseCase: evaluate answer, calculate similarity vs ideal_answer, detect gaps, analyze speaking metrics, generate follow-ups (0-3) based on thresholds. Core adaptive logic.

**Date**: 2025-11-06
**Description**: Enhanced answer evaluation with adaptive follow-up generation
**Priority**: P0 - Core adaptive behavior
**Status**: ⏳ Pending

## Key Insights

- **Similarity calculation**: Cosine similarity between answer embedding + ideal_answer embedding (0-1 scale)
- **Gap detection**: Keyword extraction from ideal_answer → check presence in candidate answer
- **Follow-up triggers**: similarity <0.8 OR speaking <85 OR gaps detected
- **Stop conditions**: threshold met OR 3 follow-ups max OR improvement trend (2 consecutive improvements)
- **Speaking metrics**: Stub for MVP (returns 85.0), replace with Azure Speech API later

## Requirements

### Functional Requirements

1. **Enhanced evaluation**:
   - Calculate similarity_score (cosine between answer + ideal_answer embeddings)
   - Detect gaps (missing keywords/concepts from ideal_answer)
   - Calculate speaking_score (stub: 85.0 for MVP)

2. **Follow-up logic**:
   - IF similarity <0.8 OR speaking <85 OR len(gaps) >0:
     - Generate targeted follow-up question via LLM
     - Create Question entity (is_follow_up=True, parent_question_id=main_q_id)
     - Add to interview.adaptive_follow_ups[]
     - Deliver follow-up to candidate
   - ELSE: Move to next main question

3. **Stop conditions**:
   - Max 3 follow-ups per main question
   - If similarity ≥0.8 AND speaking ≥85: stop
   - If 2 consecutive answers show improvement: stop

### Non-Functional Requirements

- Evaluation completes in <5s (includes similarity + gap detection)
- Follow-up generation <3s
- Speaking metrics stub <100ms (will be replaced with real API)

## Architecture

### Use Case Flow

```
EvaluateAnswerAdaptiveUseCase.execute(interview_id, question_id, answer_text)
│
├─→ Step 1: Load context
│   ├─→ interview = interview_repo.find_by_id(interview_id)
│   ├─→ question = question_repo.find_by_id(question_id)
│   └─→ Validate question has ideal_answer
│
├─→ Step 2: Evaluate answer (existing logic + enhancements)
│   ├─→ evaluation = llm.evaluate_answer(question, answer_text)
│   ├─→ answer_embedding = vector.get_embedding(answer_text)
│   └─→ ideal_embedding = vector.get_embedding(question.ideal_answer)
│
├─→ Step 3: Calculate similarity
│   └─→ similarity_score = cosine_similarity(answer_embedding, ideal_embedding)
│
├─→ Step 4: Detect gaps
│   ├─→ ideal_keywords = extract_keywords(question.ideal_answer)
│   ├─→ answer_keywords = extract_keywords(answer_text)
│   └─→ gaps = ideal_keywords - answer_keywords
│
├─→ Step 5: Analyze speaking (stub)
│   └─→ speaking_score = speaking_analyzer.analyze(answer_text) # Returns 85.0
│
├─→ Step 6: Store Answer
│   ├─→ answer = Answer(...)
│   ├─→ answer.similarity_score = similarity_score
│   ├─→ answer.gaps = {missing: list(gaps), found: list(answer_keywords)}
│   ├─→ answer.speaking_score = speaking_score
│   ├─→ answer.evaluation = evaluation
│   └─→ answer_repo.save(answer)
│
├─→ Step 7: Decide follow-up
│   ├─→ need_followup = _should_generate_followup(answer, question)
│   │   └─→ Returns True if: similarity <0.8 OR speaking <85 OR gaps exists
│   │
│   ├─→ IF need_followup AND followup_count <3:
│   │   ├─→ followup_q = _generate_followup(question, answer, gaps)
│   │   ├─→ question_repo.save(followup_q)
│   │   ├─→ interview.add_adaptive_followup(followup_q.id)
│   │   └─→ interview_repo.update(interview)
│   │
│   └─→ ELSE: Mark question complete, move to next
│
└─→ Step 8: Return AnswerEvaluation + has_followup flag
```

### Similarity Calculation

```python
import numpy as np

def cosine_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    """Calculate cosine similarity between two embeddings.

    Args:
        embedding_a: First embedding vector
        embedding_b: Second embedding vector

    Returns:
        Similarity score (0-1, higher is more similar)
    """
    a = np.array(embedding_a)
    b = np.array(embedding_b)

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)
    return float(max(0.0, min(1.0, similarity)))  # Clamp to [0, 1]
```

### Gap Detection (Simple Keyword-Based)

```python
import spacy
from typing import set

def extract_keywords(text: str) -> set[str]:
    """Extract important keywords from text using spaCy.

    Args:
        text: Input text

    Returns:
        Set of normalized keywords (nouns, verbs, adjectives)
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text.lower())

    keywords = {
        token.lemma_
        for token in doc
        if token.pos_ in {"NOUN", "VERB", "ADJ", "PROPN"}
        and not token.is_stop
        and len(token.text) > 2
    }

    return keywords
```

## Related Code Files

### Files to Create (4)

1. **src/application/use_cases/evaluate_answer_adaptive.py** (~300 lines)
2. **src/domain/ports/speaking_analyzer_port.py** (~40 lines)
3. **src/adapters/speech/speaking_analyzer_stub.py** (~60 lines)
4. **tests/unit/use_cases/test_evaluate_answer_adaptive.py** (~250 lines)

### Files to Modify (3)

1. **src/adapters/llm/openai_adapter.py** - Add generate_followup_question()
2. **src/adapters/vector_db/pinecone_adapter.py** - Ensure get_embedding() available
3. **src/infrastructure/dependency_injection/container.py** - Wire new use case + ports

## Implementation Steps

### Step 1: Create SpeakingAnalyzerPort (30 min)

**File**: `src/domain/ports/speaking_analyzer_port.py`

```python
from abc import ABC, abstractmethod

class SpeakingMetrics(BaseModel):
    confidence_score: float  # 0-100
    prosody_score: float  # 0-100
    fluency_score: float  # 0-100
    overall_score: float  # 0-100 (average)

class SpeakingAnalyzerPort(ABC):
    @abstractmethod
    async def analyze(self, text: str, audio_file: str | None = None) -> SpeakingMetrics:
        """Analyze speaking quality from text/audio."""
        pass
```

### Step 2: Create SpeakingAnalyzerStub (30 min)

**File**: `src/adapters/speech/speaking_analyzer_stub.py`

```python
class SpeakingAnalyzerStub(SpeakingAnalyzerPort):
    """Stub implementation returning default values for MVP."""

    async def analyze(self, text: str, audio_file: str | None = None) -> SpeakingMetrics:
        # For MVP: Return fixed high scores
        return SpeakingMetrics(
            confidence_score=85.0,
            prosody_score=85.0,
            fluency_score=85.0,
            overall_score=85.0,
        )
```

### Step 3: Implement EvaluateAnswerAdaptiveUseCase (180 min)

**File**: `src/application/use_cases/evaluate_answer_adaptive.py`

```python
import numpy as np
import spacy
from typing import Any

class EvaluateAnswerAdaptiveUseCase:
    def __init__(
        self,
        llm: LLMPort,
        vector_search: VectorSearchPort,
        speaking_analyzer: SpeakingAnalyzerPort,
        interview_repo: InterviewRepositoryPort,
        question_repo: QuestionRepositoryPort,
        answer_repo: AnswerRepositoryPort,
    ):
        self.llm = llm
        self.vector_search = vector_search
        self.speaking_analyzer = speaking_analyzer
        self.interview_repo = interview_repo
        self.question_repo = question_repo
        self.answer_repo = answer_repo
        self.nlp = spacy.load("en_core_web_sm")

    async def execute(
        self,
        interview_id: UUID,
        question_id: UUID,
        answer_text: str,
        audio_file: str | None = None,
    ) -> tuple[Answer, bool]:
        """Evaluate answer with adaptive follow-up logic.

        Returns:
            (Answer entity, has_followup flag)
        """
        # Step 1: Load context
        interview = await self.interview_repo.find_by_id(interview_id)
        question = await self.question_repo.find_by_id(question_id)

        if not question.has_ideal_answer():
            raise ValueError("Question missing ideal_answer for adaptive evaluation")

        # Step 2: Evaluate answer
        evaluation = await self.llm.evaluate_answer(question, answer_text, {})

        # Step 3: Calculate similarity
        answer_embedding = await self.vector_search.get_embedding(answer_text)
        ideal_embedding = await self.vector_search.get_embedding(question.ideal_answer)
        similarity_score = self._cosine_similarity(answer_embedding, ideal_embedding)

        # Step 4: Detect gaps
        gaps = self._detect_gaps(question.ideal_answer, answer_text)

        # Step 5: Analyze speaking
        speaking_metrics = await self.speaking_analyzer.analyze(answer_text, audio_file)

        # Step 6: Store Answer
        answer = Answer(
            interview_id=interview_id,
            question_id=question_id,
            candidate_id=interview.candidate_id,
            text=answer_text,
            audio_file_path=audio_file,
            evaluation=evaluation,
            similarity_score=similarity_score,
            gaps=gaps,
            speaking_score=speaking_metrics.overall_score,
        )
        await self.answer_repo.save(answer)

        # Step 7: Decide follow-up
        followup_count = self._count_followups_for_question(interview, question_id)
        has_followup = False

        if self._should_generate_followup(answer, followup_count):
            followup_q = await self._generate_followup(question, answer, gaps)
            await self.question_repo.save(followup_q)
            interview.add_adaptive_followup(followup_q.id)
            await self.interview_repo.update(interview)
            has_followup = True

        return answer, has_followup

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity."""
        a_np = np.array(a)
        b_np = np.array(b)
        similarity = np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
        return float(max(0.0, min(1.0, similarity)))

    def _detect_gaps(self, ideal_answer: str, candidate_answer: str) -> dict[str, Any]:
        """Detect missing concepts using keyword extraction."""
        ideal_keywords = self._extract_keywords(ideal_answer)
        answer_keywords = self._extract_keywords(candidate_answer)

        missing = ideal_keywords - answer_keywords
        found = ideal_keywords & answer_keywords

        return {
            "missing_keywords": list(missing),
            "found_keywords": list(found),
            "coverage_percentage": len(found) / len(ideal_keywords) * 100 if ideal_keywords else 100,
        }

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract keywords using spaCy."""
        doc = self.nlp(text.lower())
        return {
            token.lemma_
            for token in doc
            if token.pos_ in {"NOUN", "VERB", "ADJ", "PROPN"}
            and not token.is_stop
            and len(token.text) > 2
        }

    def _should_generate_followup(self, answer: Answer, followup_count: int) -> bool:
        """Decide if follow-up needed."""
        if followup_count >= 3:
            return False  # Max 3 follow-ups

        # Trigger conditions
        low_similarity = answer.similarity_score < 0.8
        low_speaking = answer.speaking_score < 85.0
        has_gaps = answer.gaps["coverage_percentage"] < 70.0

        return low_similarity or low_speaking or has_gaps

    async def _generate_followup(
        self, parent_question: Question, answer: Answer, gaps: dict
    ) -> Question:
        """Generate targeted follow-up question."""
        context = {
            "original_question": parent_question.text,
            "candidate_answer": answer.text,
            "missing_concepts": gaps["missing_keywords"][:5],  # Top 5 gaps
        }

        followup_text = await self.llm.generate_followup_question(context)

        return Question(
            text=followup_text,
            question_type=parent_question.question_type,
            difficulty=parent_question.difficulty,
            skills=parent_question.skills,
            is_follow_up=True,
            parent_question_id=parent_question.id,
        )

    def _count_followups_for_question(
        self, interview: Interview, question_id: UUID
    ) -> int:
        """Count existing follow-ups for a question."""
        # Query adaptive_follow_ups with parent_question_id filter
        # Simplified: Return 0 for MVP (track in memory)
        return 0
```

### Step 4: Extend OpenAIAdapter with Follow-up Generation (45 min)

**File**: `src/adapters/llm/openai_adapter.py`

```python
async def generate_followup_question(self, context: dict[str, Any]) -> str:
    """Generate follow-up question based on gaps.

    Args:
        context: Dict with original_question, candidate_answer, missing_concepts

    Returns:
        Follow-up question text
    """
    prompt = f"""
Original Question: {context['original_question']}

Candidate's Answer: {context['candidate_answer']}

The candidate's answer is missing these key concepts:
{', '.join(context['missing_concepts'])}

Generate a follow-up question that helps the candidate address the missing concepts.
The question should:
- Be specific and targeted
- Guide the candidate without giving away the answer
- Be answerable in 1-2 minutes

Output only the follow-up question.
"""

    response = await self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()
```

## Todo List

### SpeakingAnalyzerPort + Stub
- [ ] Create speaking_analyzer_port.py with interface
- [ ] Create SpeakingMetrics Pydantic model
- [ ] Create speaking_analyzer_stub.py with stub implementation
- [ ] Return fixed values (85.0) for MVP
- [ ] Add TODO comments for Azure Speech API integration
- [ ] Write unit tests for stub
- [ ] Run mypy + black

### EvaluateAnswerAdaptiveUseCase
- [ ] Implement execute() method with 7 steps
- [ ] Implement _cosine_similarity() helper
- [ ] Implement _detect_gaps() with keyword extraction
- [ ] Implement _extract_keywords() using spaCy
- [ ] Implement _should_generate_followup() logic
- [ ] Implement _generate_followup() method
- [ ] Implement _count_followups_for_question() helper
- [ ] Add logging at each step
- [ ] Add error handling
- [ ] Write 15+ unit tests (mock all deps)
- [ ] Write integration test with real embeddings
- [ ] Run mypy + black

### OpenAI Adapter Extension
- [ ] Add generate_followup_question() method
- [ ] Design prompt for targeted follow-ups
- [ ] Handle LLM errors gracefully
- [ ] Test with mocked OpenAI responses
- [ ] Test with real API
- [ ] Run mypy + black

### DI Container
- [ ] Wire speaking_analyzer_port() → SpeakingAnalyzerStub
- [ ] Wire evaluate_answer_adaptive_use_case() with 6 dependencies
- [ ] Test container wiring

### Testing
- [ ] Test similarity calculation (known embeddings)
- [ ] Test gap detection (known text)
- [ ] Test follow-up decision logic (multiple scenarios)
- [ ] Test max 3 follow-ups enforcement
- [ ] Test stop conditions (threshold met)
- [ ] Test speaking metrics integration
- [ ] Test full evaluation flow with mocks
- [ ] Run integration test with real DB + Pinecone
- [ ] Check test coverage >80%

## Success Criteria

- [ ] EvaluateAnswerAdaptiveUseCase calculates similarity (0-1)
- [ ] Gap detection identifies missing keywords
- [ ] Speaking metrics stub returns 85.0
- [ ] Follow-up triggered when similarity <0.8 OR speaking <85 OR gaps >30%
- [ ] Max 3 follow-ups enforced per main question
- [ ] Follow-up questions are targeted (address specific gaps)
- [ ] Answer entity stores similarity_score, gaps, speaking_score
- [ ] Interview tracks adaptive_follow_ups[]
- [ ] Evaluation completes in <5s
- [ ] Follow-up generation completes in <3s
- [ ] Unit tests cover all decision branches
- [ ] Integration test validates full adaptive flow

## Risk Assessment

**High Risks**:
- **Gap detection accuracy**: Keyword-based may miss semantic gaps
  - *Mitigation*: Start simple, iterate with LLM-based gap detection later
- **Follow-up loop complexity**: State management across multiple follow-ups
  - *Mitigation*: Clear state machine, comprehensive tests

## Security Considerations

- Gaps dict sanitized before storage (no malicious keywords)
- Follow-up generation prompts validated (no injection)

## Next Steps

1. Complete checkboxes
2. Test locally with real Pinecone + OpenAI
3. **Proceed to Phase 05**: API integration

---

**Phase Status**: Ready after Phase 03
**Blocking**: Phase 05
**Owner**: Backend evaluation team
