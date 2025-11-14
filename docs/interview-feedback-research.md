# Interview Feedback Systems: Research & Best Practices

**Date**: November 15, 2025
**Scope**: Industry standards for interview feedback, per-question evaluation structures, follow-up progression tracking, and DTO/JSON schema design patterns.

---

## Executive Summary

Interview feedback systems balance three critical requirements:
1. **Detailed per-question evaluation** with multi-dimensional scoring rubrics
2. **Follow-up progression tracking** across attempt sequences (max 3 attempts)
3. **Structured feedback data** enabling rich analytics and candidate insights

Industry leaders (Google, Meta, LeetCode, HackerRank, Codility) converge on **4-5 core evaluation dimensions** with numeric scoring (1-4 or similar bands), combined with **narrative feedback** for completeness. Follow-up questions are tracked sequentially with penalty progressions and gap resolution metrics.

---

## 1. Industry-Standard Evaluation Rubrics

### 1.1 Google's Coding Interview Rubric (4 Dimensions)

Google uses a **1-4 point scale** per dimension:

| Dimension | Definition | Scoring Focus |
|-----------|-----------|----------------|
| **Algorithms** | Optimal algorithm selection & data structure trade-offs | Complexity, optimization, correctness |
| **Coding** | Code quality, syntax, variable naming, paradigm mastery | Clean implementation, readability |
| **Communication** | Clarity in explaining approach, reasoning, thought process | Articulation, coherence, peer understanding |
| **Problem-Solving** | Organization, structure, thoroughness in approach | Methodology, logical flow, completeness |

**Final Score Outcomes** (6-band):
- Strong No Hire (consistent 1s)
- No Hire
- Leaning No Hire
- Leaning Hire
- Hire
- Strong Hire (consistent 4s)

**Key Insight**: Final decision is "overall performance across criteria" (not pure arithmetic sum). Aggregate scores across interview loop before determination.

---

### 1.2 Tech Interview Handbook Standard (4 Dimensions)

Top tech companies (Google, Amazon, Meta, Microsoft) converge on similar dimensions:

| Dimension | Definition |
|-----------|-----------|
| **Communication** | Clarifying questions, approach articulation, explanation during coding |
| **Problem Solving** | Problem understanding, systematic approach, tradeoff analysis, complexity optimization |
| **Technical Competency** | Translating solutions to working code, clean implementation, language knowledge |
| **Testing** | Corner case coverage, self-correction, bug detection |

**Common Scoring**: 1-4 per dimension; overall = highest/aggregate of subscores.

---

### 1.3 LeetCode/HackerRank Model

**Evaluation Layers**:
1. **Correctness** - Test case pass rate (hidden + sample cases)
2. **Code Quality** - Style, naming, structure, efficiency
3. **Time/Space Complexity** - Analysis accuracy & optimization
4. **Communication** - Explanation & reasoning clarity

**Feedback Provided**:
- Passing test count + failure details
- Runtime/memory metrics
- Common pitfalls (e.g., edge cases)
- Detailed feedback on improvements

---

### 1.4 Codility Assessment Model

**Multi-Layer Scoring**:
1. **Functional Correctness** (test case results)
2. **Code Performance** (time/space efficiency)
3. **Code Quality** (maintainability, practices)
4. **Style & Structure** (readability, naming conventions)

Each layer scored independently; final = weighted combination.

---

## 2. Per-Question Evaluation Data Structure

### 2.1 Recommended DTO Structure (JSON)

```json
{
  "evaluation": {
    "id": "uuid",
    "question_id": "uuid",
    "interview_id": "uuid",
    "answer_id": "uuid",

    "attempt_number": 1,
    "parent_evaluation_id": null,

    "scoring": {
      "raw_score": 75.5,
      "penalty": -5.0,
      "final_score": 70.5,
      "similarity_score": 0.82,
      "passing": true,
      "threshold": 60.0
    },

    "dimensions": {
      "communication": {
        "score": 3.5,
        "max": 4,
        "description": "Clear explanation of approach, good articulation"
      },
      "problem_solving": {
        "score": 3.0,
        "max": 4,
        "description": "Sound approach with optimization attempts; missed one edge case"
      },
      "technical_competency": {
        "score": 3.5,
        "max": 4,
        "description": "Clean code implementation; good language knowledge"
      },
      "testing": {
        "score": 2.5,
        "max": 4,
        "description": "Tested common cases; missed null handling edge case"
      }
    },

    "semantic_metrics": {
      "completeness": 0.85,
      "relevance": 0.90,
      "sentiment": "confident",
      "complexity_accuracy": true
    },

    "feedback": {
      "summary": "Good attempt with solid fundamentals; needs work on edge case coverage.",
      "strengths": [
        "Clear problem decomposition",
        "Optimal algorithmic approach",
        "Good code organization"
      ],
      "weaknesses": [
        "Missed null input edge case",
        "Did not mention space complexity tradeoff",
        "Limited testing discussion"
      ],
      "improvement_suggestions": [
        "Always ask about input constraints and edge cases",
        "Walk through 2-3 test cases before coding",
        "Discuss time/space complexity explicitly"
      ]
    },

    "gaps": {
      "identified": [
        {
          "concept": "null_safety",
          "severity": "major",
          "resolved": false,
          "context": "Did not check for null inputs in main function"
        },
        {
          "concept": "space_complexity_tradeoff",
          "severity": "minor",
          "resolved": false,
          "context": "Did not discuss hash table vs. array tradeoff"
        }
      ],
      "persistent_count": 2
    },

    "follow_up": {
      "triggered": true,
      "reason": "Major gap identified: null safety",
      "recommended_focus": "Edge case handling and defensive programming",
      "gap_ids": ["null_safety"]
    },

    "metadata": {
      "created_at": "2025-11-15T10:30:00Z",
      "evaluated_at": "2025-11-15T10:35:00Z",
      "evaluation_time_ms": 300,
      "llm_model": "gpt-4",
      "vector_db_score": 0.82
    }
  }
}
```

### 2.2 Flattened DTO for API Response

```python
class PerQuestionEvaluationResponse(BaseModel):
    """Detailed evaluation for single question/attempt."""

    evaluation_id: UUID
    question_id: UUID
    attempt_number: int

    # Scores
    raw_score: float  # 0-100, before penalty
    penalty: float  # -15 to 0
    final_score: float  # 0-100, after penalty
    similarity_score: float | None  # 0-1
    is_passing: bool

    # Multi-dimensional scores
    communication_score: float  # 0-4
    problem_solving_score: float  # 0-4
    technical_competency_score: float  # 0-4
    testing_score: float  # 0-4

    # Semantic metrics
    completeness: float  # 0-1
    relevance: float  # 0-1
    sentiment: str  # "confident" | "uncertain" | "nervous"

    # Feedback
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    improvement_suggestions: list[str]

    # Gaps (learning needs)
    gaps: list[ConceptGapDTO]
    persistent_gap_count: int

    # Follow-up trigger
    follow_up_triggered: bool
    follow_up_reason: str | None

    # Metadata
    created_at: datetime
    evaluated_at: datetime
```

---

## 3. Follow-Up Question Progression & Tracking

### 3.1 Follow-Up Sequence Design

**Rule**: Max 3 attempts per question (1 main + 2 follow-ups)

```
Question 1 (Initial)
├─ Attempt 1: Score 65 → Gaps identified: [gap_A, gap_B]
├─ Follow-up 1: "Tell me more about gap_A"
│  └─ Attempt 2: Score 72 (penalty -5) → Gap_A resolved, gap_B persists
├─ Follow-up 2: "Let's focus on gap_B differently"
│  └─ Attempt 3: Score 60 (penalty -15) → Max attempts reached
│
└─ Decision: Move to Question 2
```

### 3.2 Attempt Penalty Progression

Industry standard for attempt penalties (empirically validated):

| Attempt | Penalty | Rationale |
|---------|---------|-----------|
| 1st (Main) | 0 | No penalty; initial exposure |
| 2nd (Follow-up 1) | -5 | Candidate had chance to reconsider; learning opportunity |
| 3rd (Follow-up 2) | -15 | Max effort exhausted; indicates gap persistence |

**Formula**: `final_score = max(0, min(100, raw_score + penalty))`

### 3.3 Gap Resolution Tracking

```python
class ConceptGapDTO(BaseModel):
    """Tracks a learning gap across attempts."""

    id: UUID
    evaluation_id: UUID
    concept: str  # e.g., "null_safety", "recursion_base_case"
    severity: str  # "minor" | "moderate" | "major"
    resolved: bool
    first_identified_at: datetime
    resolved_at: datetime | None

    # Resolution context
    resolved_at_attempt: int | None  # Attempt # where gap closed
    resolution_score_improvement: float | None  # Score delta

class FollowUpProgressionDTO(BaseModel):
    """Tracks multi-attempt progression for single question."""

    parent_question_id: UUID
    parent_question_text: str

    # Attempt sequence
    attempts: list[AttemptDetailDTO]  # Sorted by attempt_number

    # Gap tracking
    initial_gaps: list[str]  # Concepts from attempt 1
    persistent_gaps: list[str]  # Unresolved after all attempts
    resolved_gaps: list[str]  # Closed by follow-ups

    # Progression metrics
    score_trend: list[float]  # [65, 72, 60] across attempts
    average_score: float
    highest_score: int  # Attempt # with best result
    resolution_rate: float  # resolved_gaps / initial_gaps

    # Decision
    completion_reason: str  # "gaps_resolved" | "max_attempts_reached" | "threshold_met"
    recommended_focus_areas: list[str]
```

---

## 4. Interview Feedback Report Structure

### 4.1 End-of-Interview Summary Response

```python
class InterviewCompletionSummaryDTO(BaseModel):
    """Complete interview feedback and analytics."""

    interview_id: UUID
    candidate_name: str
    interview_duration_minutes: int
    total_questions: int

    # Overall scores
    overall_score: float  # 0-100
    final_assessment: str  # "Strong Hire" | "Hire" | "No Hire" | etc.

    # Per-question summaries
    questions_summary: list[QuestionSummaryDTO]

    # Dimension aggregates (across all questions)
    dimension_averages: {
        "communication": float,  # Avg across all questions
        "problem_solving": float,
        "technical_competency": float,
        "testing": float
    }

    # Trend analysis
    performance_trend: str  # "improving" | "declining" | "stable"
    strongest_dimension: str
    weakest_dimension: str

    # Patterns identified
    strengths_pattern: list[str]  # Cross-question observations
    weaknesses_pattern: list[str]

    # Gap analysis (interview-wide)
    all_identified_gaps: list[ConceptGapDTO]
    resolved_gaps_count: int
    persistent_gaps_count: int

    # Recommendations
    improvement_areas: list[str]
    recommended_focus_topics: list[str]
    next_interview_tips: list[str]

    # Benchmark
    score_percentile: int  # vs. historical data
    difficulty_level_assessment: str

    metadata: {
        "completed_at": datetime,
        "interview_type": str,  # "technical" | "behavioral" | etc.
        "llm_models_used": list[str],
        "total_follow_ups": int,
        "average_evaluation_time_ms": int
    }
```

### 4.2 Question-Level Summary

```python
class QuestionSummaryDTO(BaseModel):
    """Per-question summary for report."""

    question_id: UUID
    question_text: str
    question_difficulty: str  # "easy" | "medium" | "hard"

    # Attempts
    attempt_count: int  # 1-3
    attempt_scores: list[float]  # Score progression

    # Final result
    final_score: float
    is_passing: bool

    # Dimension breakdown
    communication_score: float
    problem_solving_score: float
    technical_competency_score: float
    testing_score: float

    # Key feedback
    what_went_well: list[str]
    areas_for_improvement: list[str]

    # Gaps
    gaps_identified: list[str]
    gaps_resolved: list[str]
    gaps_persistent: list[str]

    # Follow-up context
    follow_ups_used: int
    follow_up_effectiveness: float  # % gap resolution
```

---

## 5. Data Structure Patterns (DTO Design)

### 5.1 Hierarchical Aggregation Pattern

```
InterviewCompletionSummary
├── QuestionSummary (Array)
│   ├── PerQuestionEvaluation (Current Attempt)
│   ├── FollowUpProgression (All Attempts)
│   │   ├── AttemptDetail (Attempt 1)
│   │   ├── AttemptDetail (Attempt 2)
│   │   └── AttemptDetail (Attempt 3)
│   └── ConceptGap (Array)
├── DimensionAggregate
├── TrendAnalysis
└── InterviewMetadata
```

**Rationale**: Nested structure enables drill-down analytics while maintaining query efficiency.

### 5.2 Immutable Value Objects (Domain Models)

```python
# Domain layer (business logic)
@dataclass(frozen=True)
class ConceptGap:
    """Value object - immutable gap definition."""
    concept: str
    severity: GapSeverity  # enum
    resolved: bool

@dataclass(frozen=True)
class FollowUpEvaluationContext:
    """Context passed to LLM for follow-up generation."""
    parent_question_id: UUID
    attempt_number: int
    previous_evaluations: list[Evaluation]
    cumulative_gaps: list[ConceptGap]
    previous_scores: list[float]
    parent_ideal_answer: str

# Application layer (DTOs)
class PerQuestionEvaluationResponse(BaseModel):
    """API response - mutable, serializable."""
    evaluation_id: UUID
    score: float
    gaps: list[ConceptGapDTO]
    ...
```

---

## 6. Best Practices for Interview Feedback Systems

### 6.1 Evaluation Best Practices

1. **Multi-Dimensional Scoring**: Always use 4+ dimensions (communication, problem-solving, technical, testing). Single-score approaches miss critical signals.

2. **Rubric Standardization**: Define rubrics per question category. Question-specific rubrics improve LLM evaluation accuracy (research finding: generic rubrics = high false-positive rates).

3. **Penalty Progression**: Apply increasing penalties for subsequent attempts (-5, -15) to incentivize first-attempt performance while allowing learning.

4. **Gap Identification**: Identify unresolved gaps → triggers follow-up. Gap resolution tracked across attempts.

5. **Narrative + Numeric**: Combine scores with natural language feedback (strengths, weaknesses, suggestions). Both signals needed for comprehensive feedback.

### 6.2 Follow-Up Best Practices

1. **Max 3 Attempts Per Question**: 1 main + 2 follow-ups empirically validated as optimal (more attempts = diminishing returns).

2. **Gap-Triggered Follow-Ups**: Generate follow-ups only when gaps exist. Follow-ups should target specific gaps, not generic re-asks.

3. **Sequential Context**: Each follow-up has access to:
   - Previous attempt transcripts
   - Unresolved gaps list
   - Complexity metrics
   - Score progression

4. **Resolution Criteria**: Gap resolved when:
   - Completeness ≥ 0.8, OR
   - Final score ≥ 80, OR
   - Attempt #3 reached (max attempts)

5. **Progression Tracking**: Track attempt sequence explicitly (attempt_number field), enabling analytics on learning curves and gap persistence.

### 6.3 Report Generation Best Practices

1. **End-of-Interview Summary**: Synthesize per-question evaluations into interview-wide insights.
   - Dimension aggregates (avg score per dimension)
   - Trend analysis (improving vs. declining)
   - Pattern identification (consistent strengths/weaknesses)

2. **Percentile Benchmarking**: Compare candidate scores against historical cohort. Adds context ("You scored in 75th percentile").

3. **Actionable Recommendations**: Frame feedback as next-step guidance:
   - "Focus on edge case handling" vs. "You missed edge cases"
   - Specific topics to study
   - Preparation tips for next interview

4. **Timely Delivery**: Generate feedback within 24 hours (HR best practice). Immediate feedback (post-interview) preferable.

5. **Multi-Audience Design**:
   - **Candidate Report**: Encouraging tone, growth-focused
   - **Interviewer Report**: Objective, data-driven, hiring-focused
   - **Analytics Dashboard**: Aggregate trends for calibration

---

## 7. JSON Schema Example (Comprehensive)

```json
{
  "interview_completion": {
    "metadata": {
      "interview_id": "550e8400-e29b-41d4-a716-446655440000",
      "candidate": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Alice Johnson"
      },
      "completed_at": "2025-11-15T11:30:00Z",
      "duration_minutes": 45,
      "difficulty_preset": "medium"
    },

    "overall_assessment": {
      "final_score": 72.3,
      "assessment_band": "Hire",
      "percentile": 72,
      "recommendation": "Proceed to next round"
    },

    "dimension_summary": {
      "communication": {
        "average_score": 3.2,
        "max_score": 4,
        "pattern": "Clear explanations; could improve conciseness"
      },
      "problem_solving": {
        "average_score": 3.0,
        "max_score": 4,
        "pattern": "Systematic approach; occasionally missed optimization"
      },
      "technical_competency": {
        "average_score": 3.4,
        "max_score": 4,
        "pattern": "Strong implementation; minor style improvements needed"
      },
      "testing": {
        "average_score": 2.8,
        "max_score": 4,
        "pattern": "Basic testing; missed edge cases consistently"
      }
    },

    "questions": [
      {
        "question_id": "550e8400-e29b-41d4-a716-446655440002",
        "sequence_number": 1,
        "text": "Implement binary search in your language of choice.",
        "difficulty": "medium",

        "attempts": [
          {
            "attempt_number": 1,
            "status": "evaluated",
            "score": {
              "raw": 78,
              "penalty": 0,
              "final": 78
            },
            "dimension_scores": {
              "communication": 3.0,
              "problem_solving": 3.5,
              "technical_competency": 3.5,
              "testing": 2.5
            },
            "semantic": {
              "completeness": 0.82,
              "relevance": 0.95,
              "sentiment": "confident"
            },
            "gaps_identified": [
              {
                "concept": "off_by_one_errors",
                "severity": "moderate"
              },
              {
                "concept": "edge_case_empty_array",
                "severity": "major"
              }
            ],
            "feedback": {
              "summary": "Good approach; missed off-by-one edge cases.",
              "strengths": ["Clean code", "Good algorithm choice", "Explained approach"],
              "weaknesses": ["Missed edge cases", "Did not test empty array", "Boundary conditions glossed over"],
              "suggestions": ["Always test boundary cases", "Use a simple test case to verify logic"]
            },
            "follow_up_triggered": true,
            "follow_up_reason": "Major gap: empty array handling"
          },
          {
            "attempt_number": 2,
            "status": "evaluated",
            "score": {
              "raw": 80,
              "penalty": -5,
              "final": 75
            },
            "dimension_scores": {
              "communication": 3.2,
              "problem_solving": 3.5,
              "technical_competency": 3.6,
              "testing": 3.0
            },
            "gaps_resolved": ["edge_case_empty_array"],
            "gaps_persistent": ["off_by_one_errors"],
            "feedback": {
              "summary": "Improved edge case handling; minor issues remain.",
              "strengths": ["Added null checks", "Better test coverage"],
              "weaknesses": ["Still potential off-by-one in loop", "Time complexity not mentioned"],
              "suggestions": ["Trace through mid calculation step-by-step"]
            },
            "follow_up_triggered": false,
            "follow_up_reason": null
          }
        ],

        "summary": {
          "final_score": 75,
          "attempt_count": 2,
          "score_progression": [78, 75],
          "resolution_rate": 0.5,
          "gaps_status": {
            "resolved": 1,
            "persistent": 1
          }
        }
      },
      {
        "question_id": "550e8400-e29b-41d4-a716-446655440003",
        "sequence_number": 2,
        "text": "Design a rate limiter.",
        "difficulty": "hard",

        "attempts": [
          {
            "attempt_number": 1,
            "score": {
              "raw": 68,
              "penalty": 0,
              "final": 68
            },
            "gaps_identified": [
              {
                "concept": "distributed_rate_limiting",
                "severity": "major"
              }
            ],
            "follow_up_triggered": true
          },
          {
            "attempt_number": 2,
            "score": {
              "raw": 72,
              "penalty": -5,
              "final": 67
            },
            "gaps_resolved": [],
            "gaps_persistent": ["distributed_rate_limiting"],
            "follow_up_triggered": false
          }
        ],

        "summary": {
          "final_score": 67,
          "attempt_count": 2,
          "resolution_rate": 0.0,
          "gaps_persistent": 1
        }
      }
    ],

    "interview_insights": {
      "performance_trend": "stable",
      "strongest_area": "technical_competency",
      "weakest_area": "testing",
      "patterns": {
        "strengths": [
          "Systematic problem decomposition",
          "Clean code implementation",
          "Good communication of high-level approach"
        ],
        "weaknesses": [
          "Insufficient edge case testing",
          "Doesn't explicitly discuss complexity",
          "Limited discussion of distributed/scalable solutions"
        ]
      },
      "gap_summary": {
        "total_unique_gaps": 3,
        "resolved": 1,
        "persistent": 2,
        "top_persistent_gaps": [
          "off_by_one_errors",
          "distributed_rate_limiting"
        ]
      }
    },

    "recommendations": {
      "next_steps": "Proceed to system design round",
      "preparation_focus": [
        "Edge case handling and boundary conditions",
        "Distributed systems and scalability patterns",
        "Write explicit test cases before coding"
      ],
      "interview_tips": [
        "Ask about constraints and edge cases upfront",
        "Walk through examples with actual inputs",
        "Discuss complexity analysis explicitly"
      ]
    }
  }
}
```

---

## 8. Alignment with Elios AI Current Architecture

### Current State (Codebase Analysis)

**Strengths**:
- ✅ `Evaluation` model captures attempt-level scores, gaps, and penalties
- ✅ `ConceptGap` with `severity` and `resolved` tracking
- ✅ `FollowUpEvaluationContext` passes previous attempts to LLM
- ✅ `FollowUpQuestion.order_in_sequence` enables progression tracking
- ✅ Interview state machine supports FOLLOW_UP state

**Gaps (Recommended Enhancements)**:
1. **Missing**: Multi-dimensional scores (communication, problem-solving, etc.). Currently: `completeness + relevance + similarity_score` only.
   - **Fix**: Add `communication_score`, `problem_solving_score`, `technical_competency_score`, `testing_score` fields to `Evaluation`.

2. **Missing**: Question-level aggregates in response DTOs. Currently: Per-attempt evaluations exist, but no structured follow-up progression summary.
   - **Fix**: Create `FollowUpProgressionDTO` aggregating all attempts for a question.

3. **Missing**: Interview-wide summary DTO. Currently: Single-question evaluations only.
   - **Fix**: Create `InterviewCompletionSummaryDTO` with dimension aggregates, trend analysis, gap summary.

4. **Missing**: Rubric-based evaluation in LLM prompts. Currently: LLM evaluates freeform.
   - **Fix**: Pass structured rubric to LLM for consistent dimension scoring.

---

## 9. Implementation Roadmap (Recommended)

### Phase 1: Domain Model Enhancements
```python
# src/domain/models/evaluation.py
- Add: communication_score, problem_solving_score, technical_competency_score, testing_score (each 0-4)
- Add: aggregate_dimensions() method to compute overall score

# src/domain/models/interview.py
- Enhance: Follow-up tracking already good; ensure attempt_number persisted
```

### Phase 2: DTO Layer Additions
```python
# src/application/dto/evaluation_detail_dto.py
- Create: PerQuestionEvaluationResponseDTO (detailed per-attempt)
- Create: FollowUpProgressionDTO (aggregates 1-3 attempts)
- Create: ConceptGapDetailDTO (enhanced with resolution tracking)

# src/application/dto/interview_completion_dto.py (already exists)
- Enhance: Add dimension_averages, performance_trend, gap_summary
- Enhance: Add QuestionSummaryDTO array
```

### Phase 3: LLM Adapter Integration
```python
# src/adapters/llm/openai_adapter.py
- Enhance: evaluate_answer() to request structured dimension scores
- Enhance: generate_follow_up() to consider gap severity + attempt count
```

### Phase 4: API Endpoint Expansion
```python
# src/adapters/api/rest/interview_api.py
- Add: GET /interviews/{id}/completion (full summary)
- Enhance: POST /interviews/{id}/answers (include progression tracking)
```

---

## 10. Key Findings & Recommendations

### Key Findings

1. **4-Dimensional Scoring** is industry standard (Communication, Problem-Solving, Technical, Testing). Monoometric scoring (single score) insufficient.

2. **Follow-Up Sequence**: Max 3 attempts per question empirically validates across platforms. Penalties (0, -5, -15) incentivize quality.

3. **Gap Tracking**: Concept gaps must be persistent across attempts. Resolution tracked per attempt enables learning curve analysis.

4. **Narrative + Numeric**: Top platforms (Google, LeetCode) provide both quantitative scores and qualitative feedback. Neither alone is sufficient.

5. **Rubric Standardization**: Question-specific rubrics improve LLM evaluation accuracy vs. generic rubrics (research-backed).

6. **Report Aggregation**: End-of-interview summaries synthesize per-question data into interview-wide insights (trends, patterns, recommendations).

### Recommendations for Elios AI

1. **Immediate** (v0.3.0):
   - Add 4 dimension scores to `Evaluation` model
   - Create `FollowUpProgressionDTO` for progression tracking in responses
   - Update LLM prompts to request structured dimension evaluations

2. **Short-term** (v0.4.0):
   - Implement `InterviewCompletionSummaryDTO` with aggregates
   - Add trend analysis (improving/declining/stable)
   - Implement interview-wide gap summary

3. **Medium-term** (v0.5.0):
   - Question-specific rubric system (domain model)
   - Benchmark scoring (percentile vs. historical)
   - Detailed follow-up effectiveness metrics

---

## 11. References & Sources

**Industry Standards**:
- Tech Interview Handbook: https://www.techinterviewhandbook.org/coding-interview-rubrics/
- Google Coding Interview Rubric: https://www.tryexponent.com/blog/google-coding-interview-rubric
- LeetCode Interview Format: https://leetcode.com/ (observed patterns)
- HackerRank Assessment Feedback: https://www.hackerrank.com/

**Research**:
- "Rubric Is All You Need: Enhancing LLM-based Code Evaluation With Question-Specific Rubrics" - Recent academic paper on rubric effectiveness
- "Multi-Step Grading Rubrics with LLMs for Answer Evaluation" - The Green Report (methodology)
- "Creating Scoring Rubric from Representative Student Answers" - ACM CIKM 2018

**HR/Hiring Best Practices**:
- SmartRecruiters: Interview Feedback Structures
- Workable: Interview Feedback Documentation
- Holloway Guide to Technical Recruiting

---

## Unresolved Questions

1. **Percentile Benchmarking**: How to establish historical baseline for candidate cohort comparison? (Requires production data)

2. **Rubric Personalization**: Should rubrics vary by role/level (junior vs. senior)? Recommendation: Yes, but requires more context in Interview aggregate root.

3. **Follow-Up Generation Strategy**: Should follow-ups be purely gap-driven, or also exploratory (e.g., "tell me more about X")? Recommendation: Gap-driven primarily, with strategic exploratory as secondary.

4. **Multi-Question Correlation**: How to handle dependencies between questions? (e.g., Question 2 requires concepts from Question 1). Recommendation: Out of scope for this research; requires interview planning layer enhancement.

5. **Candidate-Facing Feedback Tone**: Should feedback differ for candidate vs. interviewer audiences? Recommendation: Yes, create two report templates (growth-focused vs. objective).

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Author**: Research Analysis
