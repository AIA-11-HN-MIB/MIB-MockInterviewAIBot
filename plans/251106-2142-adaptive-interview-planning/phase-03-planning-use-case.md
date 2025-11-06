# Phase 03: Planning Use Case Implementation

**Phase ID**: phase-03-planning-use-case
**Created**: 2025-11-06
**Status**: ⏳ Pending
**Priority**: P0 (Critical)
**Estimated Effort**: 10 hours

## Context

**Parent Plan**: [Main Plan](./plan.md)
**Dependencies**: [Phase 01 - Domain Models](./phase-01-domain-model-updates.md), [Phase 02 - Database](./phase-02-database-migration.md)
**Related Docs**: [Use Cases](../../docs/codebase-summary.md#2-application-layer-use-cases) | [LLM Adapter](../../docs/codebase-summary.md#llm-adapters-srcadaptersllm)

## Overview

Implement PlanInterviewUseCase orchestrating pre-planning phase: calculate n, generate n questions with ideal answers + rationale, store in DB, mark Interview.status=READY. Core new functionality enabling adaptive flow.

**Date**: 2025-11-06
**Description**: Create PlanInterviewUseCase for pre-planning interview questions
**Priority**: P0 - Core new feature
**Status Breakdown**:
- n-calculation logic: ⏳ Pending
- Question generation: ⏳ Pending
- Ideal answer generation: ⏳ Pending
- Rationale generation: ⏳ Pending
- Storage + transaction: ⏳ Pending
- Error handling: ⏳ Pending
- Tests: ⏳ Pending

## Key Insights

- **LLM cost**: 3n API calls (1 question + 1 ideal_answer + 1 rationale per question)
  - *Optimization*: Batch prompts when possible, use cheaper model for rationale
- **Latency**: 90s for 12 questions unacceptable for synchronous API
  - *Solution*: Async background job + progress tracking (future enhancement)
- **Atomic transaction**: All questions must save or rollback on failure
- **n-calculation**: Dynamic based on CV complexity (skill diversity + experience years)

## Requirements

### Functional Requirements

1. **Calculate n** (question count) based on CV analysis:
   - Junior (0-2 yrs experience, <5 skills): n=5
   - Mid (2-5 yrs, 5-10 skills): n=8
   - Senior (5+ yrs, 10+ skills): n=12
   - Cap at 12 to control LLM costs

2. **Generate n questions** via LLMPort:
   - Context: CV summary, skills, experience, suggested topics
   - Balanced distribution: 60% technical, 30% behavioral, 10% situational
   - Progressive difficulty: 50% easy, 30% medium, 20% hard

3. **Generate ideal_answer + rationale** for each question:
   - Ideal answer: 150-300 words, technically correct, complete
   - Rationale: 50-100 words explaining why answer is ideal (key concepts covered)

4. **Store questions** in database:
   - Save all n questions atomically (transaction)
   - Link questions to interview via question_ids[]
   - Update plan_metadata: {n, generated_at, strategy, cv_summary}

5. **Mark interview READY**:
   - Update Interview.status = READY
   - Update Interview.plan_metadata
   - Return Interview entity

### Non-Functional Requirements

- Planning phase completes in <90s for n=12 (avg 7.5s per question)
- Atomic transaction (all or nothing)
- Graceful error handling (LLM failures, rate limits)
- Logging at each step for debugging
- Cost tracking (log LLM token usage)

## Architecture

### Use Case Flow

```
PlanInterviewUseCase.execute(cv_analysis_id, candidate_id)
│
├─→ Step 1: Load CV Analysis
│   └─→ cv_analysis_repo.find_by_id(cv_analysis_id)
│
├─→ Step 2: Calculate n
│   ├─→ Extract: experience_years, skill_count
│   ├─→ Calculate: n = calculate_question_count(experience, skills)
│   └─→ Range: 5-12 questions
│
├─→ Step 3: Create Interview (status=PREPARING)
│   ├─→ Interview(candidate_id, status=PREPARING, cv_analysis_id)
│   └─→ interview_repo.save(interview)
│
├─→ Step 4: Generate n questions (parallel if possible)
│   ├─→ FOR i in range(n):
│   │   ├─→ Generate question (LLMPort)
│   │   ├─→ Generate ideal_answer (LLMPort)
│   │   ├─→ Generate rationale (LLMPort)
│   │   ├─→ Create Question entity
│   │   └─→ question_repo.save(question)
│   └─→ Collect question_ids[]
│
├─→ Step 5: Update Interview
│   ├─→ interview.question_ids = question_ids
│   ├─→ interview.plan_metadata = {n, generated_at, ...}
│   ├─→ interview.mark_ready(cv_analysis_id)
│   └─→ interview_repo.update(interview)
│
└─→ Step 6: Return Interview (status=READY)
```

### n-Calculation Logic

```python
def calculate_question_count(cv_analysis: CVAnalysis) -> int:
    """Calculate optimal question count based on CV complexity.

    Args:
        cv_analysis: Analyzed CV data

    Returns:
        Question count (5-12)
    """
    experience = cv_analysis.work_experience_years or 0
    skill_count = len(cv_analysis.skills)

    # Base calculation
    if experience <= 2 and skill_count < 5:
        n = 5  # Junior
    elif experience <= 5 and skill_count < 10:
        n = 8  # Mid-level
    else:
        n = 12  # Senior

    # Adjust for skill diversity (variety bonus)
    technical_skills = cv_analysis.get_technical_skills()
    if len(technical_skills) >= 15:
        n = min(n + 2, 12)  # Bonus for diverse skillset

    return max(5, min(n, 12))  # Clamp to 5-12
```

### LLM Prompt Engineering

**Question generation prompt**:
```python
prompt = f"""
Generate a {difficulty} {question_type} interview question for a candidate with the following profile:

CV Summary: {cv_analysis.summary}
Key Skills: {', '.join(skills)}
Experience: {experience} years

Requirements:
- Question should assess practical understanding of {skill}
- Difficulty: {difficulty}
- Format: Open-ended, requires 2-3 minute answer
- Avoid yes/no questions

Output only the question text.
"""
```

**Ideal answer generation prompt**:
```python
prompt = f"""
Question: {question.text}

Generate an ideal answer for this interview question. The answer should:
- Be 150-300 words
- Demonstrate expert-level understanding
- Cover key concepts comprehensively
- Include practical examples if relevant
- Be technically accurate

Output only the ideal answer text.
"""
```

**Rationale generation prompt**:
```python
prompt = f"""
Question: {question.text}
Ideal Answer: {ideal_answer}

Explain WHY this is an ideal answer in 50-100 words. Focus on:
- What key concepts are covered
- Why this demonstrates mastery
- What would be missing in a weaker answer

Output only the rationale text.
"""
```

## Related Code Files

### Files to Create (3)

1. **src/application/use_cases/plan_interview.py** (new, ~250 lines)
   - PlanInterviewUseCase class
   - calculate_question_count() helper
   - _generate_question_with_ideal_answer() private method
   - Error handling + logging

2. **src/application/dto/plan_request_dto.py** (new, ~30 lines)
   - PlanInterviewRequest DTO
   - PlanInterviewResponse DTO

3. **tests/unit/use_cases/test_plan_interview.py** (new, ~200 lines)
   - Test n-calculation logic
   - Test question generation flow (mocked LLM)
   - Test error handling
   - Test transaction rollback

### Files to Modify (2)

1. **src/adapters/llm/openai_adapter.py** (current: 269 lines)
   - Add generate_ideal_answer() method
   - Add generate_rationale() method
   - Estimated: +60 lines

2. **src/infrastructure/dependency_injection/container.py** (current: 259 lines)
   - Wire PlanInterviewUseCase
   - Estimated: +15 lines

## Implementation Steps

### Step 1: Extend OpenAIAdapter (90 min)

**File**: `src/adapters/llm/openai_adapter.py`

**Add methods**:
```python
async def generate_ideal_answer(
    self,
    question_text: str,
    context: dict[str, Any],
) -> str:
    """Generate ideal answer for a question.

    Args:
        question_text: The interview question
        context: CV summary, skills, etc.

    Returns:
        Ideal answer text (150-300 words)

    Raises:
        LLMError: If generation fails
    """
    prompt = f"""
Question: {question_text}

Generate an ideal answer for this interview question...
[Full prompt as above]
"""

    try:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Low for consistency
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise LLMError(f"Failed to generate ideal answer: {e}") from e

async def generate_rationale(
    self,
    question_text: str,
    ideal_answer: str,
) -> str:
    """Generate rationale explaining why answer is ideal.

    Args:
        question_text: The question
        ideal_answer: The ideal answer

    Returns:
        Rationale text (50-100 words)

    Raises:
        LLMError: If generation fails
    """
    prompt = f"""
Question: {question_text}
Ideal Answer: {ideal_answer}

Explain WHY this is an ideal answer...
[Full prompt as above]
"""

    try:
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper model for rationale
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise LLMError(f"Failed to generate rationale: {e}") from e
```

### Step 2: Implement PlanInterviewUseCase (120 min)

**File**: `src/application/use_cases/plan_interview.py`

```python
"""Plan interview use case."""

import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.models.cv_analysis import CVAnalysis
from ...domain.models.interview import Interview, InterviewStatus
from ...domain.models.question import Question, QuestionType, DifficultyLevel
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.cv_analysis_repository_port import CVAnalysisRepositoryPort
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort

logger = logging.getLogger(__name__)


class PlanInterviewUseCase:
    """Use case for planning interview questions with ideal answers."""

    def __init__(
        self,
        llm: LLMPort,
        cv_analysis_repo: CVAnalysisRepositoryPort,
        interview_repo: InterviewRepositoryPort,
        question_repo: QuestionRepositoryPort,
    ):
        self.llm = llm
        self.cv_analysis_repo = cv_analysis_repo
        self.interview_repo = interview_repo
        self.question_repo = question_repo

    async def execute(
        self,
        cv_analysis_id: UUID,
        candidate_id: UUID,
    ) -> Interview:
        """Plan interview by generating n questions with ideal answers.

        Args:
            cv_analysis_id: CV analysis to base questions on
            candidate_id: Candidate being interviewed

        Returns:
            Interview entity with status=READY

        Raises:
            ValueError: If CV analysis not found
            LLMError: If question generation fails
            RepositoryError: If database operations fail
        """
        logger.info(
            "Starting interview planning",
            extra={
                "cv_analysis_id": str(cv_analysis_id),
                "candidate_id": str(candidate_id),
            },
        )

        # Step 1: Load CV analysis
        cv_analysis = await self.cv_analysis_repo.find_by_id(cv_analysis_id)
        if not cv_analysis:
            raise ValueError(f"CV analysis {cv_analysis_id} not found")

        # Step 2: Calculate n
        n = self._calculate_question_count(cv_analysis)
        logger.info(f"Calculated n={n} questions based on CV complexity")

        # Step 3: Create interview (status=PREPARING)
        interview = Interview(
            candidate_id=candidate_id,
            status=InterviewStatus.PREPARING,
            cv_analysis_id=cv_analysis_id,
        )
        await self.interview_repo.save(interview)

        # Step 4: Generate n questions (sequential for MVP)
        question_ids = []
        try:
            for i in range(n):
                question = await self._generate_question_with_ideal_answer(
                    cv_analysis, i, n
                )
                await self.question_repo.save(question)
                question_ids.append(question.id)
                logger.info(f"Generated question {i+1}/{n}: {question.id}")

        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            # Rollback: Delete partially created questions
            for qid in question_ids:
                try:
                    await self.question_repo.delete(qid)
                except Exception:
                    pass  # Best effort cleanup
            raise

        # Step 5: Update interview (status=READY)
        interview.question_ids = question_ids
        interview.plan_metadata = {
            "n": n,
            "generated_at": datetime.utcnow().isoformat(),
            "strategy": "adaptive_planning_v1",
            "cv_summary": cv_analysis.summary,
        }
        interview.mark_ready(cv_analysis_id)
        await self.interview_repo.update(interview)

        logger.info(
            "Interview planning complete",
            extra={
                "interview_id": str(interview.id),
                "question_count": n,
            },
        )

        return interview

    def _calculate_question_count(self, cv_analysis: CVAnalysis) -> int:
        """Calculate optimal question count based on CV complexity."""
        experience = cv_analysis.work_experience_years or 0
        skill_count = len(cv_analysis.skills)

        # Base calculation
        if experience <= 2 and skill_count < 5:
            n = 5  # Junior
        elif experience <= 5 and skill_count < 10:
            n = 8  # Mid-level
        else:
            n = 12  # Senior

        # Bonus for skill diversity
        technical_skills = cv_analysis.get_technical_skills()
        if len(technical_skills) >= 15:
            n = min(n + 2, 12)

        return max(5, min(n, 12))  # Clamp to 5-12

    async def _generate_question_with_ideal_answer(
        self,
        cv_analysis: CVAnalysis,
        index: int,
        total: int,
    ) -> Question:
        """Generate single question with ideal answer + rationale.

        Args:
            cv_analysis: CV data for context
            index: Current question index (0-based)
            total: Total questions to generate

        Returns:
            Question entity with ideal_answer + rationale populated
        """
        # Determine question type/difficulty based on index
        question_type, difficulty = self._get_question_distribution(index, total)

        # Select skill to test
        skills = cv_analysis.get_top_skills(limit=5)
        skill = skills[index % len(skills)].name if skills else "general knowledge"

        # Generate question
        context = {
            "summary": cv_analysis.summary,
            "skills": [s.name for s in skills],
            "experience": cv_analysis.work_experience_years,
        }
        question_text = await self.llm.generate_question(
            context=context,
            skill=skill,
            question_type=question_type.value,
            difficulty=difficulty.value,
        )

        # Generate ideal answer
        ideal_answer = await self.llm.generate_ideal_answer(
            question_text=question_text,
            context=context,
        )

        # Generate rationale
        rationale = await self.llm.generate_rationale(
            question_text=question_text,
            ideal_answer=ideal_answer,
        )

        # Create Question entity
        question = Question(
            text=question_text,
            question_type=question_type,
            difficulty=difficulty,
            skills=[skill],
            ideal_answer=ideal_answer,
            rationale=rationale,
            is_follow_up=False,
        )

        return question

    def _get_question_distribution(
        self, index: int, total: int
    ) -> tuple[QuestionType, DifficultyLevel]:
        """Determine question type and difficulty based on index.

        Distribution:
        - 60% technical, 30% behavioral, 10% situational
        - 50% easy, 30% medium, 20% hard

        Args:
            index: Current question index
            total: Total questions

        Returns:
            (QuestionType, DifficultyLevel)
        """
        # Question type distribution
        technical_count = int(total * 0.6)
        behavioral_count = int(total * 0.3)

        if index < technical_count:
            q_type = QuestionType.TECHNICAL
        elif index < technical_count + behavioral_count:
            q_type = QuestionType.BEHAVIORAL
        else:
            q_type = QuestionType.SITUATIONAL

        # Difficulty distribution
        easy_count = int(total * 0.5)
        medium_count = int(total * 0.3)

        if index < easy_count:
            difficulty = DifficultyLevel.EASY
        elif index < easy_count + medium_count:
            difficulty = DifficultyLevel.MEDIUM
        else:
            difficulty = DifficultyLevel.HARD

        return q_type, difficulty
```

### Step 3: Create DTOs (30 min)

**File**: `src/application/dto/plan_request_dto.py`

```python
"""DTOs for plan interview use case."""

from uuid import UUID
from pydantic import BaseModel


class PlanInterviewRequest(BaseModel):
    """Request to plan interview."""

    candidate_id: UUID
    cv_analysis_id: UUID


class PlanInterviewResponse(BaseModel):
    """Response from plan interview."""

    interview_id: UUID
    question_count: int
    status: str
    plan_metadata: dict[str, Any]
```

### Step 4: Wire DI Container (15 min)

**File**: `src/infrastructure/dependency_injection/container.py`

```python
from ..application.use_cases.plan_interview import PlanInterviewUseCase

class Container:
    # ... existing methods ...

    def plan_interview_use_case(self, session: AsyncSession) -> PlanInterviewUseCase:
        """Get PlanInterviewUseCase with dependencies."""
        return PlanInterviewUseCase(
            llm=self.llm_port(),
            cv_analysis_repo=self.cv_analysis_repository_port(session),
            interview_repo=self.interview_repository_port(session),
            question_repo=self.question_repository_port(session),
        )
```

### Step 5: Write Tests (120 min)

**File**: `tests/unit/use_cases/test_plan_interview.py`

```python
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.plan_interview import PlanInterviewUseCase
from src.domain.models.cv_analysis import CVAnalysis, ExtractedSkill
from src.domain.models.interview import Interview, InterviewStatus
from src.domain.models.question import Question


@pytest.fixture
def mock_llm():
    mock = AsyncMock()
    mock.generate_question.return_value = "What is Python?"
    mock.generate_ideal_answer.return_value = "Python is a high-level..."
    mock.generate_rationale.return_value = "This answer covers..."
    return mock


@pytest.fixture
def mock_cv_repo():
    mock = AsyncMock()
    return mock


@pytest.fixture
def plan_use_case(mock_llm, mock_cv_repo):
    return PlanInterviewUseCase(
        llm=mock_llm,
        cv_analysis_repo=mock_cv_repo,
        interview_repo=AsyncMock(),
        question_repo=AsyncMock(),
    )


async def test_calculate_question_count_junior():
    """Test n=5 for junior candidate."""
    cv = CVAnalysis(
        candidate_id=uuid4(),
        cv_file_path="test.pdf",
        extracted_text="test",
        skills=[ExtractedSkill(name="Python", confidence=0.9)],
        work_experience_years=1,
    )
    use_case = PlanInterviewUseCase(...)
    assert use_case._calculate_question_count(cv) == 5


async def test_calculate_question_count_senior():
    """Test n=12 for senior candidate."""
    cv = CVAnalysis(
        candidate_id=uuid4(),
        cv_file_path="test.pdf",
        extracted_text="test",
        skills=[ExtractedSkill(name=f"Skill{i}", confidence=0.9) for i in range(12)],
        work_experience_years=8,
    )
    use_case = PlanInterviewUseCase(...)
    assert use_case._calculate_question_count(cv) == 12


async def test_execute_generates_n_questions(plan_use_case, mock_cv_repo):
    """Test that execute generates correct number of questions."""
    # Arrange
    cv_id = uuid4()
    candidate_id = uuid4()
    cv = CVAnalysis(
        id=cv_id,
        candidate_id=candidate_id,
        cv_file_path="test.pdf",
        extracted_text="test",
        skills=[ExtractedSkill(name="Python", confidence=0.9)],
        work_experience_years=1,
        summary="Junior Python developer",
    )
    mock_cv_repo.find_by_id.return_value = cv

    # Act
    interview = await plan_use_case.execute(cv_id, candidate_id)

    # Assert
    assert interview.status == InterviewStatus.READY
    assert len(interview.question_ids) == 5  # Junior = 5 questions
    assert interview.plan_metadata["n"] == 5
    assert "generated_at" in interview.plan_metadata


# Add 10+ more test cases...
```

## Todo List

### OpenAIAdapter Extension
- [ ] Implement generate_ideal_answer() method
- [ ] Implement generate_rationale() method
- [ ] Add LLM error handling (rate limits, timeouts)
- [ ] Add token usage logging
- [ ] Use gpt-3.5-turbo for rationale (cost optimization)
- [ ] Test methods with real OpenAI API
- [ ] Test methods with mocked responses
- [ ] Run mypy type checking
- [ ] Format with black

### PlanInterviewUseCase
- [ ] Implement execute() method
- [ ] Implement _calculate_question_count() helper
- [ ] Implement _generate_question_with_ideal_answer() method
- [ ] Implement _get_question_distribution() method
- [ ] Add transaction rollback on failure
- [ ] Add logging at each step
- [ ] Add error handling for LLM failures
- [ ] Add error handling for repo failures
- [ ] Test with mocked dependencies
- [ ] Run mypy type checking
- [ ] Format with black

### DTOs
- [ ] Create PlanInterviewRequest DTO
- [ ] Create PlanInterviewResponse DTO
- [ ] Add Pydantic validation
- [ ] Run mypy type checking

### DI Container
- [ ] Add plan_interview_use_case() method
- [ ] Wire all 4 dependencies
- [ ] Test container wiring

### Testing
- [ ] Write test for n-calculation (junior/mid/senior)
- [ ] Write test for question distribution (60/30/10 split)
- [ ] Write test for difficulty distribution (50/30/20 split)
- [ ] Write test for full execute flow (mocked LLM)
- [ ] Write test for CV not found error
- [ ] Write test for LLM failure + rollback
- [ ] Write test for partial generation failure
- [ ] Write test for plan_metadata structure
- [ ] Write integration test with real DB
- [ ] Run all tests: `pytest tests/unit/use_cases/test_plan_interview.py -v`
- [ ] Check test coverage >80%

### Performance
- [ ] Measure planning time for n=5 (target <40s)
- [ ] Measure planning time for n=12 (target <90s)
- [ ] Log LLM token usage per interview
- [ ] Consider parallel question generation (future)

## Success Criteria

- [ ] PlanInterviewUseCase generates 5-12 questions based on CV
- [ ] Each question has ideal_answer (150-300 words)
- [ ] Each question has rationale (50-100 words)
- [ ] Interview status transitions PREPARING → READY
- [ ] plan_metadata contains n, generated_at, strategy
- [ ] Atomic transaction (all questions saved or rollback)
- [ ] LLM failures trigger rollback + error propagation
- [ ] Planning completes in <90s for n=12
- [ ] Unit tests cover n-calculation, distribution logic
- [ ] Integration test validates full flow with mocked LLM
- [ ] Code passes mypy, black, ruff checks

## Risk Assessment

**High Risks**:
- **LLM cost explosion**: 3n API calls per interview
  - *Mitigation*: Use gpt-3.5-turbo for rationale, log costs, cap n at 12
- **Latency**: Sequential generation too slow
  - *Mitigation*: Accept 90s for MVP, optimize with parallel calls in Phase 2
- **LLM failures**: Rate limits, timeouts, API errors
  - *Mitigation*: Retry logic with exponential backoff, rollback on permanent failure

## Security Considerations

- Ideal answers stored in DB → ensure proper access control in API
- Plan metadata sanitized before exposing to candidates
- LLM prompts validated to prevent injection attacks

## Next Steps

1. Complete all checkboxes in Todo List
2. Test locally with real OpenAI API + test DB
3. Measure performance (latency, cost)
4. **Proceed to Phase 04**: Adaptive evaluation logic

---

**Phase Status**: Ready for implementation after Phase 01+02
**Blocking**: Phase 04 (depends on planning being complete)
**Owner**: Backend use case team
