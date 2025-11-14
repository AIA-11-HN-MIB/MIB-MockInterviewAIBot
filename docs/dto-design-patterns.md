# DTO Design Patterns for Interview Feedback

**Purpose**: Concrete Pydantic models and JSON examples for implementing industry-standard interview feedback responses.

---

## 1. Dimension Score DTO

```python
# src/application/dto/dimension_score_dto.py

from pydantic import BaseModel, Field

class DimensionScoreDTO(BaseModel):
    """Single dimension score (1-4 scale)."""

    name: str  # "communication" | "problem_solving" | "technical_competency" | "testing"
    score: float = Field(ge=1.0, le=4.0)
    max_score: float = 4.0
    percentage: float = Field(ge=0, le=100)  # (score/max) * 100
    description: str  # e.g., "Clear explanations but missed one edge case"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "communication",
                "score": 3.5,
                "max_score": 4.0,
                "percentage": 87.5,
                "description": "Clear explanation of approach; good articulation of tradeoffs"
            }
        }
```

### JSON Example
```json
{
  "name": "communication",
  "score": 3.5,
  "max_score": 4.0,
  "percentage": 87.5,
  "description": "Clear explanation; could be more concise"
}
```

---

## 2. Concept Gap DTO (Detailed)

```python
# src/application/dto/concept_gap_dto.py

from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class GapSeverityEnum(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"

class ConceptGapDetailDTO(BaseModel):
    """Detailed gap tracking across attempts."""

    gap_id: UUID
    concept: str  # e.g., "null_safety", "off_by_one_errors"
    severity: GapSeverityEnum
    description: str  # Context of why this gap matters

    # Resolution tracking
    resolved: bool = False
    resolved_at_attempt: int | None = None  # Which attempt closed the gap (2 or 3)

    # First identification
    first_identified_at: datetime
    identified_in_attempt: int = 1

    # Resolution context
    resolution_score_improvement: float | None = None  # Score delta when resolved

    class Config:
        json_schema_extra = {
            "example": {
                "gap_id": "550e8400-e29b-41d4-a716-446655440000",
                "concept": "null_safety",
                "severity": "major",
                "description": "Did not check for null/empty input in main function",
                "resolved": True,
                "resolved_at_attempt": 2,
                "first_identified_at": "2025-11-15T10:30:00Z",
                "identified_in_attempt": 1,
                "resolution_score_improvement": 5.0
            }
        }
```

### JSON Example
```json
{
  "gap_id": "550e8400-e29b-41d4-a716-446655440000",
  "concept": "null_safety",
  "severity": "major",
  "description": "Did not check for null/empty input in main function",
  "resolved": true,
  "resolved_at_attempt": 2,
  "first_identified_at": "2025-11-15T10:30:00Z",
  "identified_in_attempt": 1,
  "resolution_score_improvement": 5.0
}
```

---

## 3. Individual Attempt DTO

```python
# src/application/dto/attempt_detail_dto.py

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from .dimension_score_dto import DimensionScoreDTO
from .concept_gap_dto import ConceptGapDetailDTO

class AttemptDetailDTO(BaseModel):
    """Single attempt (main question or follow-up)."""

    attempt_number: int = Field(ge=1, le=3)
    attempt_id: UUID  # Unique ID for this attempt

    # Scoring
    raw_score: float = Field(ge=0, le=100, description="Score before penalty")
    penalty: float = Field(ge=-15, le=0, description="Attempt penalty: 0, -5, or -15")
    final_score: float = Field(ge=0, le=100, description="raw_score + penalty")

    # Dimension breakdown
    dimensions: dict[str, DimensionScoreDTO]  # Keys: communication, problem_solving, etc.
    dimension_average: float = Field(ge=1, le=4)  # Avg of all dimensions

    # Semantic metrics
    completeness: float = Field(ge=0, le=1)  # 0-1 scale
    relevance: float = Field(ge=0, le=1)  # 0-1 scale
    sentiment: str  # "confident" | "uncertain" | "nervous"

    # Narrative feedback
    summary: str  # 1-2 sentence summary
    strengths: list[str] = Field(max_items=5)
    weaknesses: list[str] = Field(max_items=5)
    improvement_suggestions: list[str] = Field(max_items=5)

    # Gap tracking
    gaps_identified: list[ConceptGapDetailDTO]

    # Follow-up decision
    follow_up_triggered: bool
    follow_up_reason: str | None = None  # Why follow-up needed
    follow_up_gap_id: UUID | None = None  # Which gap triggered it

    # Metadata
    created_at: datetime
    evaluated_at: datetime
    evaluation_time_ms: int  # How long LLM took to evaluate

    class Config:
        json_schema_extra = {
            "example": {
                "attempt_number": 1,
                "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
                "raw_score": 75.5,
                "penalty": 0.0,
                "final_score": 75.5,
                "dimensions": {
                    "communication": {
                        "name": "communication",
                        "score": 3.0,
                        "max_score": 4.0,
                        "percentage": 75.0,
                        "description": "Clear explanation but could be more concise"
                    }
                },
                "dimension_average": 3.2,
                "completeness": 0.82,
                "relevance": 0.90,
                "sentiment": "confident",
                "summary": "Good approach with solid implementation; some edge cases missed.",
                "strengths": ["Clean code", "Explained approach", "Good algorithm choice"],
                "weaknesses": ["Missed null check", "Did not test empty array", "No complexity discussion"],
                "improvement_suggestions": ["Always ask about input constraints", "Test edge cases first"],
                "gaps_identified": [],
                "follow_up_triggered": true,
                "follow_up_reason": "Major gap: null safety",
                "created_at": "2025-11-15T10:30:00Z",
                "evaluated_at": "2025-11-15T10:31:30Z",
                "evaluation_time_ms": 90
            }
        }
```

### JSON Example
```json
{
  "attempt_number": 1,
  "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
  "raw_score": 75.5,
  "penalty": 0.0,
  "final_score": 75.5,
  "dimensions": {
    "communication": {
      "name": "communication",
      "score": 3.0,
      "max_score": 4.0,
      "percentage": 75.0,
      "description": "Clear but could be concise"
    },
    "problem_solving": {
      "name": "problem_solving",
      "score": 3.5,
      "max_score": 4.0,
      "percentage": 87.5,
      "description": "Good approach; missed optimization"
    }
  },
  "dimension_average": 3.25,
  "completeness": 0.82,
  "relevance": 0.90,
  "sentiment": "confident",
  "summary": "Good approach with solid implementation; edge cases missed.",
  "strengths": ["Clean code", "Explained approach", "Good algorithm choice"],
  "weaknesses": ["Missed null check", "No complexity analysis", "Limited testing"],
  "improvement_suggestions": ["Ask about input constraints", "Test edge cases first"],
  "gaps_identified": [
    {
      "gap_id": "550e8400-e29b-41d4-a716-446655440002",
      "concept": "null_safety",
      "severity": "major",
      "description": "Did not check for null input",
      "resolved": false,
      "resolved_at_attempt": null
    }
  ],
  "follow_up_triggered": true,
  "follow_up_reason": "Major gap: null safety",
  "created_at": "2025-11-15T10:30:00Z",
  "evaluated_at": "2025-11-15T10:31:30Z",
  "evaluation_time_ms": 90
}
```

---

## 4. Follow-Up Progression DTO

```python
# src/application/dto/follow_up_progression_dto.py

from uuid import UUID
from pydantic import BaseModel, Field
from .attempt_detail_dto import AttemptDetailDTO

class FollowUpProgressionDTO(BaseModel):
    """Aggregates all attempts (1-3) for a single question."""

    question_id: UUID
    question_text: str
    question_difficulty: str  # "easy" | "medium" | "hard"

    # Attempt sequence
    attempts: list[AttemptDetailDTO] = Field(min_items=1, max_items=3)
    total_attempts: int  # 1, 2, or 3

    # Gap analysis
    initial_gaps: list[str]  # Gap concepts from attempt 1
    resolved_gaps: list[str]  # Concepts closed by follow-ups
    persistent_gaps: list[str]  # Still unresolved after all attempts
    gap_resolution_rate: float = Field(ge=0, le=1)  # resolved_count / initial_count

    # Score progression
    score_progression: list[float]  # [75, 72, 60] for 3 attempts
    score_trend: str  # "improving" | "declining" | "stable"
    average_score: float
    highest_score: float
    highest_score_attempt: int

    # Dimension trends
    dimension_trends: dict[str, list[float]]  # "communication": [3.0, 3.2, 3.1]

    # Completion logic
    completion_reason: str  # Why attempts stopped
    # Options: "gaps_resolved" | "max_attempts_reached" | "threshold_met"

    # Recommendations
    recommended_focus_areas: list[str]

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "550e8400-e29b-41d4-a716-446655440000",
                "question_text": "Implement binary search",
                "question_difficulty": "medium",
                "attempts": [],  # Would contain AttemptDetailDTO items
                "total_attempts": 2,
                "initial_gaps": ["off_by_one_errors", "null_safety"],
                "resolved_gaps": ["null_safety"],
                "persistent_gaps": ["off_by_one_errors"],
                "gap_resolution_rate": 0.5,
                "score_progression": [75, 72],
                "score_trend": "declining",
                "average_score": 73.5,
                "highest_score": 75,
                "highest_score_attempt": 1,
                "dimension_trends": {
                    "communication": [3.0, 3.2],
                    "problem_solving": [3.5, 3.5]
                },
                "completion_reason": "max_attempts_reached",
                "recommended_focus_areas": ["Off-by-one boundary conditions", "Loop invariants"]
            }
        }
```

### JSON Example
```json
{
  "question_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_text": "Implement binary search",
  "question_difficulty": "medium",
  "attempts": [
    {
      "attempt_number": 1,
      "final_score": 75,
      "gaps_identified": [
        {
          "concept": "off_by_one_errors",
          "severity": "moderate",
          "resolved": false
        },
        {
          "concept": "null_safety",
          "severity": "major",
          "resolved": false
        }
      ],
      "follow_up_triggered": true
    },
    {
      "attempt_number": 2,
      "final_score": 72,
      "gaps_identified": [
        {
          "concept": "off_by_one_errors",
          "severity": "moderate",
          "resolved": false
        }
      ],
      "follow_up_triggered": false
    }
  ],
  "total_attempts": 2,
  "initial_gaps": ["off_by_one_errors", "null_safety"],
  "resolved_gaps": ["null_safety"],
  "persistent_gaps": ["off_by_one_errors"],
  "gap_resolution_rate": 0.5,
  "score_progression": [75, 72],
  "score_trend": "declining",
  "average_score": 73.5,
  "completion_reason": "max_attempts_reached",
  "recommended_focus_areas": ["Off-by-one boundary conditions"]
}
```

---

## 5. Question Summary DTO (For Report)

```python
# src/application/dto/question_summary_dto.py

from uuid import UUID
from pydantic import BaseModel

class QuestionSummaryDTO(BaseModel):
    """High-level question summary for interview report."""

    question_id: UUID
    sequence_number: int  # Q1, Q2, Q3, etc.
    text: str
    difficulty: str

    # Final result
    final_score: float
    is_passing: bool
    attempt_count: int

    # Dimension scores (final attempt)
    communication_score: float
    problem_solving_score: float
    technical_competency_score: float
    testing_score: float
    dimension_average: float

    # Feedback highlights
    key_strength: str
    key_improvement_area: str
    gap_count_initial: int
    gap_count_resolved: int
    gap_count_persistent: int

    # Trend
    score_trend: str  # "improving" | "declining" | "stable"

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "550e8400-e29b-41d4-a716-446655440000",
                "sequence_number": 1,
                "text": "Implement binary search",
                "difficulty": "medium",
                "final_score": 72,
                "is_passing": true,
                "attempt_count": 2,
                "communication_score": 3.1,
                "problem_solving_score": 3.5,
                "technical_competency_score": 3.6,
                "testing_score": 2.75,
                "dimension_average": 3.24,
                "key_strength": "Clean code implementation",
                "key_improvement_area": "Edge case handling",
                "gap_count_initial": 2,
                "gap_count_resolved": 1,
                "gap_count_persistent": 1,
                "score_trend": "declining"
            }
        }
```

---

## 6. Dimension Aggregate DTO (Interview-Wide)

```python
# src/application/dto/dimension_aggregate_dto.py

from pydantic import BaseModel, Field

class DimensionAggregateDTO(BaseModel):
    """Aggregated dimension scores across all questions."""

    communication_avg: float = Field(ge=1, le=4)
    communication_count: int  # Questions evaluating this dimension

    problem_solving_avg: float = Field(ge=1, le=4)
    problem_solving_count: int

    technical_competency_avg: float = Field(ge=1, le=4)
    technical_competency_count: int

    testing_avg: float = Field(ge=1, le=4)
    testing_count: int

    overall_dimension_avg: float = Field(ge=1, le=4)  # Avg of all dimensions

    # Ranking
    strongest_dimension: str  # Name of highest-scoring dimension
    weakest_dimension: str  # Name of lowest-scoring dimension

    class Config:
        json_schema_extra = {
            "example": {
                "communication_avg": 3.15,
                "communication_count": 3,
                "problem_solving_avg": 3.23,
                "problem_solving_count": 3,
                "technical_competency_avg": 3.40,
                "technical_competency_count": 3,
                "testing_avg": 2.80,
                "testing_count": 3,
                "overall_dimension_avg": 3.15,
                "strongest_dimension": "technical_competency",
                "weakest_dimension": "testing"
            }
        }
```

### JSON Example
```json
{
  "communication_avg": 3.15,
  "communication_count": 3,
  "problem_solving_avg": 3.23,
  "problem_solving_count": 3,
  "technical_competency_avg": 3.40,
  "technical_competency_count": 3,
  "testing_avg": 2.80,
  "testing_count": 3,
  "overall_dimension_avg": 3.15,
  "strongest_dimension": "technical_competency",
  "weakest_dimension": "testing"
}
```

---

## 7. Interview Completion Summary DTO

```python
# src/application/dto/interview_summary_comprehensive_dto.py

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from .question_summary_dto import QuestionSummaryDTO
from .dimension_aggregate_dto import DimensionAggregateDTO
from .concept_gap_dto import ConceptGapDetailDTO

class InterviewCompletionSummaryDTO(BaseModel):
    """Complete interview feedback and analytics."""

    # Interview metadata
    interview_id: UUID
    candidate_name: str
    interview_duration_minutes: int
    completed_at: datetime
    total_questions: int
    total_follow_ups: int

    # Overall assessment
    overall_score: float = Field(ge=0, le=100)
    assessment_band: str  # "Strong Hire" | "Hire" | "No Hire" | etc.
    percentile_score: int = Field(ge=0, le=100)  # vs. historical cohort
    recommendation: str

    # Per-question summaries
    questions_summary: list[QuestionSummaryDTO]

    # Dimension aggregates
    dimension_scores: DimensionAggregateDTO

    # Performance trend
    performance_trend: str  # "improving" | "declining" | "stable"
    score_progression: list[float]  # Overall scores across questions

    # Gap analysis (interview-wide)
    all_gaps_identified: list[ConceptGapDetailDTO]
    gap_summary: {
        "total_unique": int,
        "resolved": int,
        "persistent": int,
        "resolution_rate": float
    }
    top_persistent_gaps: list[str]  # Top 3 unresolved concepts

    # Pattern analysis
    strengths_pattern: list[str]  # Cross-question observations
    weaknesses_pattern: list[str]

    # Recommendations
    improvement_areas: list[str]  # Priority learning areas
    preparation_focus: list[str]  # Specific topics to study
    next_interview_tips: list[str]  # Actionable advice

    # Metadata
    interview_type: str  # "technical" | "behavioral" | "system_design"
    difficulty_level: str  # "easy" | "medium" | "hard"
    questions_passed: int  # Count of passing scores
    questions_failed: int

    class Config:
        json_schema_extra = {
            "example": {
                "interview_id": "550e8400-e29b-41d4-a716-446655440000",
                "candidate_name": "Alice Johnson",
                "interview_duration_minutes": 45,
                "completed_at": "2025-11-15T11:30:00Z",
                "total_questions": 3,
                "total_follow_ups": 2,
                "overall_score": 72.3,
                "assessment_band": "Hire",
                "percentile_score": 72,
                "recommendation": "Proceed to next round",
                "questions_summary": [],
                "dimension_scores": {},
                "performance_trend": "stable",
                "all_gaps_identified": [],
                "gap_summary": {
                    "total_unique": 5,
                    "resolved": 2,
                    "persistent": 3,
                    "resolution_rate": 0.4
                },
                "top_persistent_gaps": ["off_by_one_errors", "distributed_systems", "complexity_analysis"],
                "strengths_pattern": ["Systematic problem decomposition", "Clean code implementation"],
                "weaknesses_pattern": ["Insufficient edge case testing", "Limited complexity discussion"],
                "improvement_areas": ["Edge case handling", "Scalability patterns"],
                "preparation_focus": ["Boundary conditions", "System design basics"],
                "next_interview_tips": ["Always ask about constraints", "Test edge cases first"],
                "interview_type": "technical",
                "difficulty_level": "medium",
                "questions_passed": 2,
                "questions_failed": 1
            }
        }
```

---

## 8. Complete API Response Example

### GET /interviews/{interview_id}

```json
{
  "interview_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_name": "Alice Johnson",
  "interview_duration_minutes": 45,
  "completed_at": "2025-11-15T11:30:00Z",
  "total_questions": 2,
  "total_follow_ups": 1,
  "overall_score": 72.3,
  "assessment_band": "Hire",
  "percentile_score": 72,
  "recommendation": "Proceed to next round",

  "questions_summary": [
    {
      "question_id": "550e8400-e29b-41d4-a716-446655440001",
      "sequence_number": 1,
      "text": "Implement binary search",
      "difficulty": "medium",
      "final_score": 75,
      "is_passing": true,
      "attempt_count": 2,
      "communication_score": 3.1,
      "problem_solving_score": 3.5,
      "technical_competency_score": 3.6,
      "testing_score": 2.75,
      "dimension_average": 3.24,
      "key_strength": "Clean code",
      "key_improvement_area": "Edge case testing",
      "gap_count_initial": 2,
      "gap_count_resolved": 1,
      "gap_count_persistent": 1,
      "score_trend": "stable"
    },
    {
      "question_id": "550e8400-e29b-41d4-a716-446655440002",
      "sequence_number": 2,
      "text": "Design a rate limiter",
      "difficulty": "hard",
      "final_score": 70,
      "is_passing": true,
      "attempt_count": 1,
      "communication_score": 3.0,
      "problem_solving_score": 3.0,
      "technical_competency_score": 3.2,
      "testing_score": 2.8,
      "dimension_average": 3.0,
      "key_strength": "Understands problem",
      "key_improvement_area": "Scalability design",
      "gap_count_initial": 2,
      "gap_count_resolved": 0,
      "gap_count_persistent": 2
    }
  ],

  "dimension_scores": {
    "communication_avg": 3.05,
    "problem_solving_avg": 3.25,
    "technical_competency_avg": 3.4,
    "testing_avg": 2.78,
    "overall_dimension_avg": 3.12,
    "strongest_dimension": "technical_competency",
    "weakest_dimension": "testing"
  },

  "performance_trend": "stable",
  "score_progression": [75, 70],

  "gap_summary": {
    "total_unique": 4,
    "resolved": 1,
    "persistent": 3,
    "resolution_rate": 0.25
  },
  "top_persistent_gaps": ["distributed_rate_limiting", "off_by_one_errors", "complexity_analysis"],

  "strengths_pattern": [
    "Systematic problem decomposition",
    "Clean code implementation",
    "Good high-level understanding"
  ],
  "weaknesses_pattern": [
    "Insufficient edge case testing",
    "Limited discussion of distributed/scalable solutions",
    "Missing complexity analysis"
  ],

  "improvement_areas": ["Edge case handling", "Distributed systems concepts", "Complexity analysis"],
  "preparation_focus": ["Boundary conditions", "System design patterns", "Big-O notation"],
  "next_interview_tips": [
    "Always ask about input constraints upfront",
    "Test edge cases before coding",
    "Discuss time/space complexity explicitly"
  ],

  "interview_type": "technical",
  "difficulty_level": "medium",
  "questions_passed": 2,
  "questions_failed": 0
}
```

---

## 9. Implementation Checklist

```python
# Create these DTOs in order:

# Step 1: Base DTOs
[ ] DimensionScoreDTO  # Single 1-4 score
[ ] ConceptGapDetailDTO  # Gap tracking

# Step 2: Attempt-level DTO
[ ] AttemptDetailDTO  # Single attempt with all feedback

# Step 3: Aggregation DTOs
[ ] FollowUpProgressionDTO  # Multi-attempt sequence
[ ] QuestionSummaryDTO  # High-level question summary
[ ] DimensionAggregateDTO  # Interview-wide dimension averages

# Step 4: Final summary DTO
[ ] InterviewCompletionSummaryDTO  # Complete report

# Step 5: Add to API responses
[ ] Update AnswerEvaluationResponse to include AttemptDetailDTO
[ ] Update GET /interviews/{id} to return InterviewCompletionSummaryDTO
[ ] Add new endpoint GET /interviews/{id}/questions/{qid} → FollowUpProgressionDTO
```

---

## 10. Key Design Principles

1. **Separation of Concerns**: Attempt DTO ≠ Progression DTO ≠ Summary DTO
   - Prevents data duplication, enables reuse

2. **Nested Aggregation**: Summary contains Questions, Questions contain Attempts
   - Natural drill-down for client apps

3. **Immutable for API**: All DTOs frozen=True (read-only responses)
   - Prevents accidental mutations in transit

4. **Explicit Schemas**: json_schema_extra with examples for API docs
   - Enables Swagger/OpenAPI auto-generation

5. **Metric Consistency**: Always include percentages, averages, trends
   - Enables analytics and visualization

---

**Reference**: `docs/interview-feedback-research.md` (full research)
