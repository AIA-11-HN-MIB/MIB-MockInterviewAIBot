# Code Standards & Development Guidelines

**Last Updated**: 2025-11-14
**Version**: 0.2.1
**Applies To**: Elios AI Interview Service
**Project**: https://github.com/elios/elios-ai-service

## Overview

This document defines the coding standards, conventions, and best practices for the Elios AI Interview Service project. All code must adhere to these standards to ensure consistency, maintainability, quality, and alignment with Clean Architecture principles.

## Table of Contents

1. [Core Development Principles](#core-development-principles)
2. [Architecture Standards](#architecture-standards)
3. [Python Code Style](#python-code-style)
4. [File Organization](#file-organization)
5. [Naming Conventions](#naming-conventions)
6. [Type Hints & Documentation](#type-hints--documentation)
7. [Error Handling](#error-handling)
8. [Testing Standards](#testing-standards)
9. [Async/Await Patterns](#asyncawait-patterns)
10. [Database Standards](#database-standards)
11. [Security Standards](#security-standards)
12. [Git Workflow](#git-workflow)
13. [Code Review Checklist](#code-review-checklist)

## Core Development Principles

### SOLID Principles

**S - Single Responsibility Principle**
- Each class/function has one reason to change
- Domain models focus on business logic only
- Adapters handle one external service
- Use cases orchestrate one business flow

```python
# ✅ Good: Single responsibility
class CandidateRepository:
    """Handles candidate persistence only."""
    async def save(self, candidate: Candidate) -> None:
        ...

# ❌ Bad: Multiple responsibilities
class CandidateManager:
    """Handles persistence, validation, email, and logging."""
    async def save_and_email_and_log(self, candidate: Candidate) -> None:
        ...
```

**O - Open/Closed Principle**
- Open for extension, closed for modification
- Use ports (interfaces) for extensibility
- Add new adapters without changing domain

```python
# ✅ Good: Extend via new adapter
class ClaudeAdapter(LLMPort):
    """New LLM provider without modifying domain."""
    ...

# ❌ Bad: Modify existing code
def generate_question(..., provider: str):
    if provider == "openai":
        ...
    elif provider == "claude":  # Modified existing function
        ...
```

**L - Liskov Substitution Principle**
- Subtypes must be substitutable for base types
- All adapters must fully implement their port

```python
# ✅ Good: Full port implementation
class PostgreSQLCandidateRepository(CandidateRepositoryPort):
    async def save(self, candidate: Candidate) -> None:
        # Complete implementation
        ...

    async def find_by_id(self, id: UUID) -> Optional[Candidate]:
        # Complete implementation
        ...
```

**I - Interface Segregation Principle**
- Clients shouldn't depend on unused interfaces
- Keep ports focused and minimal

```python
# ✅ Good: Focused interfaces
class LLMPort(ABC):
    @abstractmethod
    async def generate_question(...) -> str: ...

class VectorSearchPort(ABC):
    @abstractmethod
    async def find_similar_questions(...) -> List[Question]: ...

# ❌ Bad: God interface
class AIServicePort(ABC):
    @abstractmethod
    async def generate_question(...) -> str: ...
    @abstractmethod
    async def find_similar_questions(...) -> List[Question]: ...
    @abstractmethod
    async def transcribe_audio(...) -> str: ...
```

**D - Dependency Inversion Principle**
- Depend on abstractions, not concretions
- Domain depends on ports, not adapters

```python
# ✅ Good: Depend on abstraction
class AnalyzeCVUseCase:
    def __init__(self, cv_analyzer: CVAnalyzerPort):  # Port
        self.cv_analyzer = cv_analyzer

# ❌ Bad: Depend on concrete implementation
class AnalyzeCVUseCase:
    def __init__(self, cv_analyzer: SpacyCVAnalyzer):  # Adapter
        self.cv_analyzer = cv_analyzer
```

### DRY (Don't Repeat Yourself)

- Extract common logic into utility functions
- Use base classes for shared behavior
- Create reusable mappers and converters

```python
# ✅ Good: Reusable mapper
class BaseMapper:
    @staticmethod
    def to_domain_timestamps(db_model):
        return {
            "created_at": db_model.created_at,
            "updated_at": db_model.updated_at,
        }

# ❌ Bad: Repeated code
class CandidateMapper:
    @staticmethod
    def to_domain(db_model):
        return Candidate(
            created_at=db_model.created_at,  # Repeated
            updated_at=db_model.updated_at,  # In every mapper
        )
```

### YAGNI (You Aren't Gonna Need It)

- Implement features when needed, not speculatively
- Don't build infrastructure for hypothetical requirements
- Start simple, refactor when necessary

## Common Coding Patterns

### Exemplar-Based Generation Pattern

**When to Use**: Generate content (questions, code, responses) inspired by similar examples from a database.

**Pattern Structure**:
```python
async def generate_with_exemplars(
    self,
    target_attributes: dict[str, Any],
    context: dict[str, Any],
) -> Result:
    """Generate content using exemplar-based approach.

    Steps:
    1. Build search query from target attributes
    2. Find similar examples (exemplars) via vector search
    3. Filter exemplars by relevance threshold
    4. Pass exemplars to generation service
    5. Store generated result with embedding for future searches
    """

    # Step 1: Build search query
    query = self._build_search_query(target_attributes)

    # Step 2: Find exemplars (with fallback)
    try:
        exemplars = await self._find_exemplars(
            query=query,
            filters=target_attributes,
            top_k=3,
            threshold=0.5,
        )
    except Exception as e:
        logger.warning(f"Exemplar search failed: {e}. Continuing without exemplars.")
        exemplars = []  # Fallback

    # Step 3: Generate with exemplars
    result = await self.generator.generate(
        context=context,
        exemplars=exemplars,  # Optional parameter
    )

    # Step 4: Store result embedding (non-blocking)
    try:
        await self._store_result_embedding(result)
    except Exception as e:
        logger.error(f"Failed to store embedding: {e}")
        # Continue - embedding storage is non-critical

    return result
```

**Example: Question Generation**
```python
# In PlanInterviewUseCase
async def _generate_question_with_ideal_answer(self, cv_analysis, index, total):
    # 1. Determine target attributes
    question_type, difficulty = self._get_question_distribution(index, total)
    skill = self._select_skill(cv_analysis, index)

    # 2. Find exemplar questions (vector search)
    exemplars = await self._find_exemplar_questions(
        skill=skill,
        question_type=question_type,
        difficulty=difficulty,
        cv_analysis=cv_analysis,
    )

    # 3. Generate with exemplars
    question_text = await self.llm.generate_question(
        context=context,
        skill=skill,
        difficulty=difficulty.value,
        exemplars=exemplars,  # Inspiration, not templates
    )

    # 4. Store embedding for future searches
    await self._store_question_embedding(question)

    return question
```

**Key Principles**:
- ✅ Exemplars are inspiration, not templates (LLM generates NEW content)
- ✅ Fallback: Generate without exemplars if search fails
- ✅ Non-blocking: Embedding storage failures don't fail generation
- ✅ Filters: Use metadata filters (type, difficulty, category) for relevance
- ✅ Threshold: Require minimum similarity (e.g., >0.5)
- ✅ Top-k: Limit exemplars (3-5) to avoid prompt bloat

**Helper Methods Pattern**:
```python
def _build_search_query(self, attributes: dict) -> str:
    """Build semantic search query from attributes."""
    pass

async def _find_exemplars(self, query: str, filters: dict) -> list[dict]:
    """Find similar examples via vector search with fallback."""
    pass

async def _store_result_embedding(self, result: Entity) -> None:
    """Store result embedding for future searches (non-blocking)."""
    pass
```

### Domain-Driven State Management Pattern

**Added**: v0.2.1 (Phase 1 Architectural Improvement)

**When to Use**: Manage complex entity lifecycle with state transitions and business rules.

**Pattern Structure**:
```python
class Interview(BaseModel):
    """Aggregate root with domain-driven state machine.

    State Transitions (enforced in domain layer):
    - IDLE → QUESTIONING (start interview)
    - QUESTIONING → EVALUATING (answer received)
    - EVALUATING → QUESTIONING (next question)
    - EVALUATING → REVIEWING (interview complete)
    - REVIEWING → COMPLETED (summary generated)
    """

    status: InterviewStatus

    def transition_to_questioning(self) -> None:
        """Transition to questioning state with validation."""
        valid_from = [InterviewStatus.IDLE, InterviewStatus.EVALUATING]
        if self.status not in valid_from:
            raise InvalidStateTransitionError(
                f"Cannot transition to QUESTIONING from {self.status}"
            )
        self.status = InterviewStatus.QUESTIONING

    def transition_to_evaluating(self) -> None:
        """Transition to evaluating state with validation."""
        if self.status != InterviewStatus.QUESTIONING:
            raise InvalidStateTransitionError(
                f"Cannot transition to EVALUATING from {self.status}"
            )
        self.status = InterviewStatus.EVALUATING
```

**Key Principles**:
- ✅ State machine logic lives in domain layer (not adapters)
- ✅ Explicit transition methods with validation
- ✅ Raise domain exceptions for invalid transitions
- ✅ Adapters delegate to domain methods (don't manage state directly)
- ✅ Business rules enforced at domain level

**Migration Path**: Moved from adapter-level state management (WebSocket orchestrator) to domain-driven approach in v0.2.1.

### LLM Prompt Constraint Pattern

**Added**: v0.2.2 (QA Question Constraints)

**When to Use**: Generate LLM prompts requiring specific output format constraints (e.g., verbal-only questions, structured JSON, specific content rules).

**Pattern Structure**:
```python
class OpenAIAdapter(LLMPort):
    """LLM adapter with prompt constraint enforcement."""

    async def generate_question(
        self,
        context: dict[str, Any],
        skill: str,
        difficulty: str,
        exemplars: list[dict] | None = None,
    ) -> str:
        """Generate question with explicit constraints.

        Prompt Structure:
        1. System role definition
        2. Context (CV summary, skill, difficulty)
        3. Exemplars (if available)
        4. **CONSTRAINTS** (explicitly forbid unwanted patterns)
        5. Final instruction
        """

        # Build constraint text (identical across all real LLM adapters)
        constraint_text = """
**IMPORTANT CONSTRAINTS**:
The question MUST be verbal/discussion-based. DO NOT generate questions that require:
- Writing code ("write a function", "implement", "create a class", "code a solution")
- Drawing diagrams ("draw", "sketch", "diagram", "visualize", "map out")
- Whiteboard exercises ("design on whiteboard", "show on board", "illustrate")
- Visual outputs ("create a flowchart", "design a schema visually")

Focus on conceptual understanding, best practices, trade-offs, and problem-solving approaches that can be explained verbally.
"""

        # Constraint placement: After exemplars, before final instruction
        prompt = f"""
You are an AI interview question generator.

Context:
- Skill: {skill}
- Difficulty: {difficulty}
- CV Summary: {context.get('cv_summary', 'N/A')}

{"Exemplar Questions:\n" + "\n".join(exemplars) if exemplars else ""}

{constraint_text}

Generate ONE question for this skill and difficulty.
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
```

**Key Principles**:
- ✅ Constraint text IDENTICAL across all real LLM adapters (OpenAI, Azure)
- ✅ Placement: After context/exemplars, before final instruction
- ✅ Explicit forbidden patterns with examples ("write a function", "draw")
- ✅ Positive guidance (what TO focus on: "conceptual understanding")
- ✅ Mock adapter behavioral alignment (generates same style as real adapters)
- ✅ Constraint text extracted as constant for reusability

**Mock Adapter Alignment**:
```python
class MockLLMAdapter(LLMPort):
    """Mock adapter that generates questions matching constraint behavior."""

    async def generate_question(self, context, skill, difficulty, exemplars=None) -> str:
        # Generate questions that would pass constraint validation
        patterns = [
            f"Explain the trade-offs between {{approach_a}} and {{approach_b}} when working with {skill}.",
            f"How would you approach {{problem}} in {skill}? What factors would you consider?",
            f"Describe the key principles of {{concept}} in {skill} and when to apply them.",
        ]
        # Returns question that does NOT require code/diagrams/whiteboard
        return random.choice(patterns).format(...)
```

**Testing Constraint Compliance**:
```python
# Validation regex patterns (from testing)
CODE_PATTERNS = [
    r'\bwrite\s+(a\s+)?(function|method|class|code)',
    r'\bimplement\s+(a\s+)?(function|solution|algorithm)',
    r'\bcreate\s+(a\s+)?(class|function|method)',
    r'\bcode\s+(a\s+)?solution',
]

DIAGRAM_PATTERNS = [
    r'\bdraw\s+(a\s+)?(diagram|flowchart|chart)',
    r'\bsketch\s+(a\s+)?(diagram|solution)',
    r'\bdiagram\s+(the|a)',
]

WHITEBOARD_PATTERNS = [
    r'\bwhiteboard\s+(exercise|problem|question)',
    r'\bdesign\s+on\s+(the\s+)?whiteboard',
    r'\bshow\s+on\s+(the\s+)?board',
]

def validate_question_constraints(question_text: str) -> tuple[bool, str]:
    """Returns (is_valid, violation_reason)."""
    for pattern in CODE_PATTERNS + DIAGRAM_PATTERNS + WHITEBOARD_PATTERNS:
        if re.search(pattern, question_text, re.IGNORECASE):
            return False, f"Violates constraint: {pattern}"
    return True, ""
```

**Implementation Checklist**:
- [ ] Constraint text identical across real LLM adapters (OpenAI, Azure)
- [ ] Placement after exemplars, before final instruction
- [ ] Mock adapter generates constraint-compliant questions
- [ ] Constraint validation in tests (regex patterns)
- [ ] Documentation updated (this section + system-architecture.md)

### Context-Aware Evaluation Pattern

**Added**: v0.2.1 (Phase 4 - Adaptive Answers)

**When to Use**: Evaluate answers with follow-up question support and parent-child relationships.

**Pattern Structure**:
```python
# 1. Evaluation Entity with Parent-Child Relationships
class Evaluation(BaseModel):
    """Evaluation with parent-child tracking for follow-ups."""

    evaluation_type: EvaluationType  # PARENT_QUESTION, FOLLOW_UP, COMBINED
    parent_evaluation_id: Optional[UUID]
    similarity_score: float
    gaps: Optional[GapsAnalysis]

    def is_adaptive_complete(self) -> bool:
        """Check if answer quality is sufficient (no follow-up needed).

        Break conditions:
        - similarity_score >= 0.8 (high quality)
        - gaps.confirmed == False (no gaps detected)
        """
        return self.similarity_score >= 0.8 or (
            self.gaps and not self.gaps.confirmed
        )

# 2. Follow-Up Decision Use Case
class FollowUpDecisionUseCase:
    """Decide if follow-up needed based on break conditions.

    Break Conditions (exit if ANY met):
    1. follow_up_count >= 3 (max reached)
    2. similarity_score >= 0.8 (quality sufficient)
    3. gaps.confirmed == False (no gaps detected)
    """

    async def execute(
        self,
        parent_question_id: UUID,
        latest_answer: Answer,
    ) -> dict[str, Any]:
        # Count existing follow-ups
        follow_ups = await self.follow_up_repo.get_by_parent_question_id(
            parent_question_id
        )
        follow_up_count = len(follow_ups)

        # Break condition 1: Max reached
        if follow_up_count >= 3:
            return {"needs_followup": False, "reason": "Max follow-ups reached"}

        # Break condition 2 & 3: Quality sufficient or no gaps
        if latest_answer.evaluation.is_adaptive_complete():
            return {"needs_followup": False, "reason": "Answer complete"}

        # Accumulate gaps from all previous follow-ups
        cumulative_gaps = await self._accumulate_gaps(follow_ups, latest_answer)

        return {
            "needs_followup": True,
            "reason": f"Detected {len(cumulative_gaps)} gaps",
            "cumulative_gaps": cumulative_gaps,
        }

# 3. Combine Evaluation Use Case
class CombineEvaluationUseCase:
    """Merge parent + follow-up evaluations into COMBINED evaluation."""

    async def execute(self, parent_evaluation_id: UUID) -> Evaluation:
        # Fetch parent + all follow-ups
        parent = await self.repo.get_by_id(parent_evaluation_id)
        follow_ups = await self.repo.get_follow_ups(parent_evaluation_id)

        # Merge evaluations (weighted: 70% parent + 30% avg follow-ups)
        combined_score = self._calculate_combined_score(parent, follow_ups)

        # Create COMBINED evaluation
        return Evaluation(
            evaluation_type=EvaluationType.COMBINED,
            parent_evaluation_id=parent_evaluation_id,
            similarity_score=combined_score,
            ...
        )
```

**Key Principles**:
- ✅ Evaluation entity tracks parent-child relationships
- ✅ Break conditions prevent infinite follow-up loops
- ✅ Gap accumulation across follow-ups (not just latest)
- ✅ Combined evaluation merges parent + follow-ups
- ✅ Decision logic isolated in use case (testable)

## Architecture Standards

### Clean Architecture Layers

**Layer Dependencies** (strictly enforced):
```
Infrastructure ──→ Adapters ──→ Application ──→ Domain
                                                   ↑
                                              (no dependencies)
```

**Domain Layer** (`src/domain/`):
- ✅ CAN import: Python stdlib, Pydantic, enums, dataclasses
- ❌ CANNOT import: FastAPI, SQLAlchemy, OpenAI, Pinecone, any adapter

```python
# ✅ Good: Pure domain model
from pydantic import BaseModel
from uuid import UUID

class Candidate(BaseModel):
    id: UUID
    name: str
    # Business logic methods only
```

**Application Layer** (`src/application/`):
- ✅ CAN import: Domain models, domain ports
- ❌ CANNOT import: Adapters, infrastructure, frameworks

```python
# ✅ Good: Use case depends on ports only
from ...domain.ports.llm_port import LLMPort
from ...domain.models.question import Question

class GenerateQuestionUseCase:
    def __init__(self, llm: LLMPort):  # Port, not adapter
        self.llm = llm
```

**Adapters Layer** (`src/adapters/`):
- ✅ CAN import: Domain models, domain ports, application DTOs, external libraries
- ❌ CANNOT import: Other adapters (keep independent)

```python
# ✅ Good: Adapter implements port
from openai import AsyncOpenAI
from ...domain.ports.llm_port import LLMPort

class OpenAIAdapter(LLMPort):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
```

**Infrastructure Layer** (`src/infrastructure/`):
- ✅ CAN import: Everything (top-level orchestration)
- Handles: Configuration, DI, database setup, logging

### Port-Adapter Pattern

**Port Naming**: `<Purpose>Port`
```python
# ✅ Good names
LLMPort
VectorSearchPort
CandidateRepositoryPort

# ❌ Bad names
LLMInterface  # Use "Port"
LLMService    # Ambiguous
CandidateDAO  # Old terminology
```

**Adapter Naming**: `<Technology><Purpose>Adapter` or `<Technology><Entity>Repository`
```python
# ✅ Good names
OpenAIAdapter
PineconeAdapter
PostgreSQLCandidateRepository

# ❌ Bad names
OpenAILLM            # Missing "Adapter"
CandidatePostgres    # Unclear
DatabaseRepository   # Too generic
```

**Port Definition Standards**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

class CandidateRepositoryPort(ABC):
    """Abstract interface for candidate persistence.

    This port defines the contract for storing and retrieving candidates.
    Implementations might use PostgreSQL, MongoDB, or in-memory storage.
    """

    @abstractmethod
    async def save(self, candidate: Candidate) -> None:
        """Save a candidate.

        Args:
            candidate: Candidate entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, candidate_id: UUID) -> Optional[Candidate]:
        """Find candidate by ID.

        Args:
            candidate_id: Unique candidate identifier

        Returns:
            Candidate if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass
```

## Python Code Style

### PEP 8 Compliance

**Line Length**: 100 characters (configured in black/ruff)

**Indentation**: 4 spaces (not tabs)

**Blank Lines**:
- 2 blank lines between top-level classes/functions
- 1 blank line between methods
- Use blank lines sparingly inside methods

**Imports**:
```python
# ✅ Good: Organized imports
# Standard library
import asyncio
from typing import List, Optional
from uuid import UUID

# Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local application
from ..domain.models.candidate import Candidate
from ..domain.ports.llm_port import LLMPort
```

**Import Order** (enforced by ruff):
1. Standard library
2. Third-party packages
3. Local application imports

### Code Formatting

**Use Black** (automated):
```bash
black src/
```

**Use Ruff** (linting):
```bash
ruff check src/
ruff check --fix src/  # Auto-fix
```

**String Quotes**: Use double quotes `"` (black default)

**Trailing Commas**: Use in multi-line structures
```python
# ✅ Good
skills = [
    "Python",
    "FastAPI",
    "PostgreSQL",  # Trailing comma
]

# ❌ Bad
skills = [
    "Python",
    "FastAPI",
    "PostgreSQL"  # No trailing comma
]
```

## File Organization

### Directory Structure Rules

**No Deep Nesting**: Maximum 3 levels under `src/`
```
✅ src/domain/models/candidate.py
✅ src/adapters/llm/openai_adapter.py
❌ src/adapters/llm/openai/v4/client.py  # Too deep
```

**File Size Limit**: 500 lines maximum
- If file exceeds 500 lines, refactor into smaller modules
- Exception: Database models if needed

**Module Organization**:
```
module/
├── __init__.py      # Exports public API
├── models.py        # Related models
├── services.py      # Related services
└── utils.py         # Helper functions
```

### File Naming

**Modules**: `snake_case.py`
```
✅ candidate_repository.py
✅ cv_analyzer_port.py
❌ CandidateRepository.py  # PascalCase not for files
❌ candidate-repository.py  # No hyphens
```

**Test Files**: `test_<module_name>.py`
```
✅ test_candidate_repository.py
✅ test_analyze_cv_use_case.py
❌ candidate_repository_test.py
```

### `__init__.py` Standards

**Export Public API**:
```python
# src/domain/models/__init__.py
from .candidate import Candidate
from .interview import Interview, InterviewStatus
from .question import Question, QuestionType, DifficultyLevel
from .answer import Answer, AnswerEvaluation
from .cv_analysis import CVAnalysis, ExtractedSkill

__all__ = [
    "Candidate",
    "Interview",
    "InterviewStatus",
    "Question",
    "QuestionType",
    "DifficultyLevel",
    "Answer",
    "AnswerEvaluation",
    "CVAnalysis",
    "ExtractedSkill",
]
```

## Naming Conventions

### Variables & Functions

**Variables**: `snake_case`
```python
candidate_id = uuid4()
interview_status = InterviewStatus.IN_PROGRESS
total_score = 85.5
```

**Functions**: `snake_case` (verb-based)
```python
def calculate_score(answers: List[Answer]) -> float:
    ...

async def fetch_questions(criteria: Dict[str, Any]) -> List[Question]:
    ...

def is_valid_email(email: str) -> bool:
    ...
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_QUESTIONS_PER_INTERVIEW = 10
DEFAULT_DIFFICULTY = "medium"
API_VERSION = "v1"
TIMEOUT_SECONDS = 30
```

**Private Members**: Prefix with single underscore
```python
class Container:
    def __init__(self):
        self._llm_port: LLMPort | None = None  # Private
        self._initialized = False

    def llm_port(self) -> LLMPort:  # Public
        if self._llm_port is None:
            self._llm_port = self._create_llm_port()
        return self._llm_port

    def _create_llm_port(self) -> LLMPort:  # Private helper
        ...
```

### Classes

**Classes**: `PascalCase` (noun-based)
```python
class CandidateRepository:
    ...

class AnalyzeCVUseCase:
    ...

class OpenAIAdapter:
    ...
```

**Enums**: `PascalCase` for class, `UPPER_CASE` for members
```python
class InterviewStatus(str, Enum):
    PREPARING = "preparing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

**Exceptions**: Suffix with `Error`
```python
class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass

class QuestionNotFoundError(RepositoryError):
    """Raised when question cannot be found."""
    pass

class ValidationError(Exception):
    """Raised for invalid input data."""
    pass
```

### Type Aliases

**Type Aliases**: `PascalCase`
```python
from typing import Dict, Any, List
from uuid import UUID

MetadataDict = Dict[str, Any]
SkillList = List[str]
CandidateID = UUID
```

## Type Hints & Documentation

### Type Hints (Required)

**All public functions must have type hints**:
```python
# ✅ Good: Complete type hints
async def find_similar_questions(
    embedding: List[float],
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Question]:
    ...

# ❌ Bad: No type hints
async def find_similar_questions(embedding, limit=10, filters=None):
    ...
```

**Use modern type hint syntax (Python 3.11+)**:
```python
# ✅ Good: Modern syntax
def process_items(items: list[str]) -> dict[str, int]:
    ...

def get_candidate(id: UUID) -> Candidate | None:
    ...

# ❌ Bad: Old syntax (but still works)
from typing import List, Dict, Optional, Union

def process_items(items: List[str]) -> Dict[str, int]:
    ...

def get_candidate(id: UUID) -> Optional[Candidate]:
    ...
```

**Complex types**:
```python
from typing import TypedDict, Literal, Protocol

# TypedDict for structured dicts
class EvaluationResult(TypedDict):
    score: float
    feedback: str
    strengths: list[str]

# Literal for specific values
Status = Literal["pending", "active", "completed"]

# Protocol for structural typing
class HasEmbedding(Protocol):
    embedding: list[float]
```

### Docstrings (Required for Public API)

**Google Style Docstrings**:
```python
async def evaluate_answer(
    question: Question,
    answer_text: str,
    context: dict[str, Any],
) -> AnswerEvaluation:
    """Evaluate a candidate's answer to an interview question.

    This method uses the configured LLM to perform multi-dimensional
    evaluation of the answer, including completeness, relevance,
    and technical accuracy.

    Args:
        question: The interview question that was asked
        answer_text: The candidate's text response
        context: Additional context including CV summary and interview stage

    Returns:
        AnswerEvaluation containing scores, feedback, and recommendations

    Raises:
        LLMError: If the LLM API call fails
        ValidationError: If inputs are invalid

    Example:
        >>> question = Question(text="Explain async/await", ...)
        >>> evaluation = await evaluate_answer(question, "Async allows...", {})
        >>> print(evaluation.score)
        85.5
    """
    ...
```

**Module Docstrings**:
```python
"""OpenAI LLM adapter implementation.

This module provides the OpenAIAdapter class which implements the LLMPort
interface using OpenAI's GPT-4 model. It handles question generation,
answer evaluation, and feedback report creation.

Typical usage example:
    adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")
    question = await adapter.generate_question(context={...}, skill="Python")
"""
```

**Class Docstrings**:
```python
class Interview(BaseModel):
    """Represents an interview session between a candidate and the AI interviewer.

    Interview is the aggregate root for the interview domain. It manages the
    interview lifecycle, question sequence, and answer collection. An interview
    goes through multiple states from preparation to completion.

    Attributes:
        id: Unique interview identifier
        candidate_id: ID of the candidate being interviewed
        status: Current interview status (PREPARING, READY, IN_PROGRESS, etc.)
        question_ids: Ordered list of question IDs for this interview
        answer_ids: List of answer IDs collected so far
        current_question_index: Index of the current question (0-based)

    Example:
        >>> interview = Interview(candidate_id=candidate.id)
        >>> interview.mark_ready(cv_analysis_id=analysis.id)
        >>> interview.start()
        >>> assert interview.status == InterviewStatus.IN_PROGRESS
    """
    ...
```

## Error Handling

### Exception Hierarchy

```python
# Base exception for domain
class DomainError(Exception):
    """Base exception for domain layer errors."""
    pass

# Specific domain exceptions
class InvalidInterviewStateError(DomainError):
    """Raised when interview state transition is invalid."""
    pass

# Adapter exceptions
class AdapterError(Exception):
    """Base exception for adapter layer errors."""
    pass

class LLMError(AdapterError):
    """Raised when LLM API call fails."""
    pass

class RepositoryError(AdapterError):
    """Raised when database operation fails."""
    pass
```

### Error Handling Patterns

**Always use try-except for external calls**:
```python
# ✅ Good: Proper error handling
async def save_candidate(self, candidate: Candidate) -> None:
    try:
        db_model = CandidateMapper.to_db_model(candidate)
        self.session.add(db_model)
        await self.session.commit()
    except SQLAlchemyError as e:
        await self.session.rollback()
        raise RepositoryError(f"Failed to save candidate: {e}") from e
    except Exception as e:
        await self.session.rollback()
        raise RepositoryError(f"Unexpected error: {e}") from e

# ❌ Bad: No error handling
async def save_candidate(self, candidate: Candidate) -> None:
    db_model = CandidateMapper.to_db_model(candidate)
    self.session.add(db_model)
    await self.session.commit()  # What if this fails?
```

**Include context in exceptions**:
```python
# ✅ Good: Contextual error message
raise QuestionNotFoundError(
    f"Question with ID {question_id} not found in interview {interview_id}"
)

# ❌ Bad: Generic error
raise QuestionNotFoundError("Question not found")
```

**Use exception chaining**:
```python
# ✅ Good: Preserve original exception
try:
    result = await external_api.call()
except ExternalAPIError as e:
    raise LLMError("Failed to generate question") from e

# ❌ Bad: Lost original exception
try:
    result = await external_api.call()
except ExternalAPIError:
    raise LLMError("Failed to generate question")
```

### Logging Errors

```python
import logging

logger = logging.getLogger(__name__)

async def process_interview(interview_id: UUID) -> None:
    try:
        interview = await self.repo.find_by_id(interview_id)
        # ... processing
    except RepositoryError as e:
        logger.error(
            "Failed to load interview",
            extra={
                "interview_id": str(interview_id),
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,  # Include stack trace
        )
        raise
```

**Never log sensitive data**:
```python
# ✅ Good: Sanitized logging
logger.info("User logged in", extra={"email": user.email})

# ❌ Bad: Logging passwords
logger.info(f"Login attempt: {email}:{password}")  # NEVER!
```

## Testing Standards

### Test Structure

**Arrange-Act-Assert (AAA) Pattern**:
```python
async def test_start_interview_success():
    # Arrange: Set up test data and mocks
    interview = Interview(candidate_id=uuid4(), status=InterviewStatus.READY)

    # Act: Execute the function being tested
    interview.start()

    # Assert: Verify expected outcomes
    assert interview.status == InterviewStatus.IN_PROGRESS
    assert interview.started_at is not None
```

### Test Naming

**Pattern**: `test_<function>_<scenario>_<expected_result>`
```python
# ✅ Good: Descriptive test names
def test_start_interview_when_ready_then_sets_in_progress():
    ...

def test_start_interview_when_not_ready_then_raises_error():
    ...

def test_evaluate_answer_with_high_quality_then_returns_high_score():
    ...

# ❌ Bad: Vague test names
def test_start():
    ...

def test_interview():
    ...

def test_case_1():
    ...
```

### Test Organization

```
tests/
├── unit/                          # Fast, isolated tests
│   ├── domain/
│   │   ├── test_candidate.py
│   │   ├── test_interview.py
│   │   └── test_question.py
│   └── application/
│       └── test_analyze_cv_use_case.py
├── integration/                   # Tests with real services
│   ├── test_openai_adapter.py
│   ├── test_pinecone_adapter.py
│   └── test_repositories.py
└── e2e/                          # End-to-end flows
    └── test_interview_flow.py
```

### Mocking

**Use pytest fixtures**:
```python
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

@pytest.fixture
def mock_llm_port():
    """Mock LLM port for testing."""
    mock = AsyncMock(spec=LLMPort)
    mock.generate_question.return_value = "What is Python?"
    return mock

async def test_generate_question_use_case(mock_llm_port):
    # Use the fixture
    use_case = GenerateQuestionUseCase(llm=mock_llm_port)
    question = await use_case.execute(skill="Python")

    assert question == "What is Python?"
    mock_llm_port.generate_question.assert_called_once()
```

### Test Coverage

**Target**: >80% code coverage

**Run coverage**:
```bash
pytest --cov=src --cov-report=html
```

**Focus coverage on**:
- Domain logic (aim for 100%)
- Use cases (aim for 90%+)
- Adapters (aim for 80%+)

**Less critical**:
- Configuration files
- Simple DTOs
- Database models (tested via integration tests)

## Async/Await Patterns

### Async Best Practices

**Always use async for I/O operations**:
```python
# ✅ Good: Async for database, API calls
async def fetch_candidate(candidate_id: UUID) -> Candidate:
    async with get_async_session() as session:
        result = await session.execute(
            select(CandidateModel).where(CandidateModel.id == candidate_id)
        )
        return result.scalar_one()

# ❌ Bad: Sync for I/O
def fetch_candidate(candidate_id: UUID) -> Candidate:
    session = get_session()  # Blocking!
    result = session.execute(...)
    return result.scalar_one()
```

**Don't mix sync and async carelessly**:
```python
# ✅ Good: Consistent async
async def process_interview(interview_id: UUID) -> None:
    interview = await fetch_interview(interview_id)  # Await async
    questions = await fetch_questions(interview.question_ids)  # Await async
    await save_results(interview, questions)  # Await async

# ❌ Bad: Mixing without asyncio.run
async def process_interview(interview_id: UUID) -> None:
    interview = fetch_interview_sync(interview_id)  # Blocks event loop!
    questions = await fetch_questions(interview.question_ids)
```

**Use asyncio.gather for parallel operations**:
```python
# ✅ Good: Parallel execution
async def fetch_interview_data(interview_id: UUID) -> tuple:
    interview, questions, candidate = await asyncio.gather(
        fetch_interview(interview_id),
        fetch_questions(interview_id),
        fetch_candidate(candidate_id),
    )
    return interview, questions, candidate

# ❌ Bad: Sequential (slower)
async def fetch_interview_data(interview_id: UUID) -> tuple:
    interview = await fetch_interview(interview_id)
    questions = await fetch_questions(interview_id)
    candidate = await fetch_candidate(candidate_id)
    return interview, questions, candidate
```

### Context Managers

**Always use async context managers for resources**:
```python
# ✅ Good: Proper cleanup
async with get_async_session() as session:
    result = await session.execute(query)
    # Session automatically closed/rolled back on exception

# ❌ Bad: Manual cleanup (error-prone)
session = get_async_session()
try:
    result = await session.execute(query)
finally:
    await session.close()  # Easy to forget
```

## Database Standards

### SQLAlchemy Patterns

**Use async SQLAlchemy 2.0 style**:
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ✅ Good: SQLAlchemy 2.0 style
async def find_by_email(self, email: str) -> Optional[Candidate]:
    stmt = select(CandidateModel).where(CandidateModel.email == email)
    result = await self.session.execute(stmt)
    db_model = result.scalar_one_or_none()
    return CandidateMapper.to_domain(db_model) if db_model else None

# ❌ Bad: Legacy 1.x style
async def find_by_email(self, email: str) -> Optional[Candidate]:
    result = await self.session.query(CandidateModel).filter_by(email=email).first()
    ...
```

**Use parameterized queries (never string interpolation)**:
```python
# ✅ Good: Parameterized (SQL injection safe)
stmt = select(CandidateModel).where(CandidateModel.email == email)

# ❌ Bad: String interpolation (SQL INJECTION!)
query = f"SELECT * FROM candidates WHERE email = '{email}'"
```

**Handle transactions properly**:
```python
# ✅ Good: Explicit commit/rollback
async def save(self, candidate: Candidate) -> None:
    try:
        self.session.add(db_model)
        await self.session.commit()
    except Exception:
        await self.session.rollback()
        raise

# ❌ Bad: No error handling
async def save(self, candidate: Candidate) -> None:
    self.session.add(db_model)
    await self.session.commit()  # What if this fails?
```

### Alembic Migrations

**Migration naming**: `<description>`
```bash
# ✅ Good migration messages
alembic revision --autogenerate -m "add candidate email index"
alembic revision --autogenerate -m "add interview status column"

# ❌ Bad migration messages
alembic revision --autogenerate -m "changes"
alembic revision --autogenerate -m "update"
```

**Always review autogenerated migrations**:
- Check for unintended changes
- Add data migrations if schema changes affect existing data
- Test migrations on a copy of production data

## Security Standards

### Input Validation

**Always validate with Pydantic**:
```python
from pydantic import BaseModel, EmailStr, validator

class CreateCandidateRequest(BaseModel):
    name: str
    email: EmailStr  # Built-in email validation

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
```

### Secret Management

**Never hardcode secrets**:
```python
# ✅ Good: Environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    pinecone_api_key: str
    database_url: str

    class Config:
        env_file = ".env.local"

# ❌ Bad: Hardcoded
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxx"  # NEVER!
```

**Never log secrets**:
```python
# ✅ Good: Sanitized logging
logger.info("Connecting to database", extra={"host": db_host})

# ❌ Bad: Logging credentials
logger.info(f"Connecting: {database_url}")  # May contain password!
```

### API Security

**Use dependency injection for auth (when implemented)**:
```python
from fastapi import Depends, HTTPException

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = await verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@router.get("/interviews")
async def list_interviews(current_user: User = Depends(get_current_user)):
    # Only authenticated users can access
    ...
```

## Git Workflow

### Branch Naming

**Pattern**: `<type>/<description>`

```bash
# ✅ Good branch names
feature/cv-analysis-adapter
fix/interview-status-bug
refactor/repository-cleanup
docs/api-documentation

# ❌ Bad branch names
my-branch
fix
updates
branch-123
```

### Commit Messages

**Format**: Conventional Commits

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance

**Examples**:
```bash
# ✅ Good commit messages
feat(domain): add Interview aggregate with state management
fix(persistence): handle NULL metadata in answer mapper
refactor(llm): extract common prompt building logic
docs: update API documentation for CV upload endpoint
test(use-cases): add integration tests for AnalyzeCVUseCase

# ❌ Bad commit messages
update code
fix bug
changes
WIP
```

**Commit Message Rules**:
- Subject line: imperative mood, lowercase, no period, max 72 chars
- Body: explain WHY, not WHAT (code shows what)
- Reference issues: `Closes #123`

### Pre-Commit Checklist

Before committing:
- [ ] Code formatted with black
- [ ] No linting errors (ruff)
- [ ] Type hints added for new functions
- [ ] Docstrings added for public APIs
- [ ] Tests added/updated
- [ ] Tests pass locally
- [ ] No debug code (print, breakpoint, etc.)
- [ ] No commented-out code
- [ ] No secrets in code
- [ ] Migration created if schema changed

## Code Review Checklist

### Architecture Review
- [ ] Follows Clean Architecture layers
- [ ] Dependencies point inward
- [ ] Ports used for external dependencies
- [ ] No circular dependencies
- [ ] Single Responsibility Principle followed

### Code Quality Review
- [ ] PEP 8 compliant
- [ ] Type hints present and correct
- [ ] Docstrings for public APIs
- [ ] No code duplication
- [ ] Meaningful variable/function names
- [ ] No magic numbers (use constants)
- [ ] Error handling present
- [ ] Logging appropriate

### Testing Review
- [ ] Unit tests for domain logic
- [ ] Integration tests for adapters
- [ ] Test coverage >80%
- [ ] Tests are independent
- [ ] Tests have clear arrange-act-assert
- [ ] Edge cases tested
- [ ] Error paths tested

### Security Review
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention (parameterized queries)
- [ ] No logging of sensitive data
- [ ] Proper error messages (no stack traces to users)

### Performance Review
- [ ] Async/await used for I/O
- [ ] No blocking operations in async code
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Appropriate use of indexes

## Tool Configuration

### pyproject.toml

All tool configurations are in `pyproject.toml`:
- ruff: Linting rules
- black: Formatting
- mypy: Type checking
- pytest: Test configuration
- coverage: Coverage settings

### Running Quality Checks

```bash
# Format code
black src/

# Check linting
ruff check src/

# Type checking
mypy src/

# Run tests with coverage
pytest --cov=src --cov-report=html

# All checks at once
black src/ && ruff check src/ && mypy src/ && pytest --cov=src
```

## Enforcement

These standards are enforced through:
1. **Automated tools**: black, ruff, mypy (in CI/CD)
2. **Code reviews**: All PRs require approval
3. **Pre-commit hooks**: (planned)
4. **CI/CD pipeline**: Blocks merge if checks fail

## Exceptions

**When to deviate**:
- Performance-critical code (document why)
- External library constraints
- Generated code (mark clearly)

**Document exceptions**:
```python
"""
NOTE: This function intentionally breaks the 100-char line limit
due to SQLAlchemy query syntax limitations. Refactoring would
reduce readability.
"""
```

## References

### Internal
- [Project Overview](./project-overview-pdr.md)
- [System Architecture](./system-architecture.md)
- [Codebase Summary](./codebase-summary.md)

### External
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [PEP 257 Docstring Conventions](https://peps.python.org/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

**Document Status**: Living document, updated as standards evolve
**Next Review**: Monthly or when major architectural changes occur
**Maintainers**: Elios Development Team
