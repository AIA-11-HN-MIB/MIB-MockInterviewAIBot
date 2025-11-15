# Interview Feedback Patterns: Quick Reference

**TL;DR**: Use 4-dimensional scoring (Communication/Problem-Solving/Technical/Testing), track attempts 1-3 with penalties (0/-5/-15), identify + resolve concept gaps, synthesize per-question data into interview-wide summary with dimension aggregates.

---

## 1. Evaluation Scoring (Per Question/Attempt)

### Four Dimensions (Google/Meta Standard)

| Dimension | Scale | Focus |
|-----------|-------|-------|
| Communication | 1-4 | Clarity of explanation, thought process articulation |
| Problem-Solving | 1-4 | Approach soundness, optimization, tradeoff analysis |
| Technical Competency | 1-4 | Code quality, implementation correctness, language knowledge |
| Testing | 1-4 | Edge case coverage, self-correction, bug detection |

**Final Score Formula**: `final = raw_score + penalty`

### Attempt Penalties (Validated Pattern)

```
Attempt 1 (Main):        penalty = 0      (no penalty for initial try)
Attempt 2 (Follow-up 1): penalty = -5     (candidate had chance to reconsider)
Attempt 3 (Follow-up 2): penalty = -15    (max attempts reached; gap persistence indicator)
```

---

## 2. Per-Question Evaluation DTO (Minimal)

```python
class QuestionEvaluationDTO(BaseModel):
    evaluation_id: UUID
    question_id: UUID
    attempt_number: int  # 1, 2, or 3

    # Numeric scores
    raw_score: float  # 0-100
    penalty: float  # 0, -5, or -15
    final_score: float  # max(0, min(100, raw + penalty))

    # Dimension breakdown
    communication: float  # 1-4
    problem_solving: float  # 1-4
    technical_competency: float  # 1-4
    testing: float  # 1-4

    # Semantic metrics
    completeness: float  # 0-1
    relevance: float  # 0-1
    sentiment: str  # "confident" | "uncertain" | "nervous"

    # Narrative feedback
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]

    # Gap tracking
    gaps_identified: list[ConceptGapDTO]
    follow_up_triggered: bool
```

---

## 3. Follow-Up Progression (Multi-Attempt Sequence)

```python
class FollowUpProgressionDTO(BaseModel):
    """Aggregates 1-3 attempts for single question."""

    parent_question_id: UUID
    parent_question_text: str

    # Attempt sequence
    attempts: list[QuestionEvaluationDTO]  # 1-3 items

    # Gap tracking across attempts
    initial_gaps: list[str]  # From attempt 1
    persistent_gaps: list[str]  # Unresolved after all attempts
    resolved_gaps: list[str]  # Closed by follow-ups

    # Progression metrics
    score_progression: list[float]  # [65, 72, 60] for 3 attempts
    average_score: float
    best_attempt_num: int
    resolution_rate: float  # resolved_count / initial_count

    # Completion decision
    completion_reason: str  # "gaps_resolved" | "max_attempts" | "threshold_met"
```

---

## 4. Interview-Wide Summary (End Report)

```python
class InterviewSummaryDTO(BaseModel):
    interview_id: UUID
    interview_duration_minutes: int
    completed_at: datetime

    # Overall result
    overall_score: float  # 0-100
    final_assessment: str  # "Strong Hire" | "Hire" | "No Hire"

    # Per-question summaries
    questions: list[QuestionSummaryDTO]

    # Dimension aggregates (avg across all questions)
    dimension_scores: {
        "communication": 3.2,  # Avg 1-4 score
        "problem_solving": 3.0,
        "technical_competency": 3.4,
        "testing": 2.8
    }

    # Interview-wide insights
    performance_trend: str  # "improving" | "declining" | "stable"
    strongest_dimension: str
    weakest_dimension: str

    # Gap analysis
    all_gaps_identified: int
    gaps_resolved: int
    gaps_persistent: int
    top_persistent_gaps: list[str]

    # Recommendations
    improvement_areas: list[str]
    preparation_focus: list[str]
```

---

## 5. Concept Gap Model

```python
class ConceptGapDTO(BaseModel):
    concept: str  # "null_safety", "recursion", "off_by_one"
    severity: str  # "minor" | "moderate" | "major"
    resolved: bool  # True if fixed in follow-up
    resolution_attempt: int | None  # Attempt # where resolved (e.g., 2)

    # Context
    first_identified_at: datetime
    resolved_at: datetime | None
```

---

## 6. LLM Prompt Structure (Recommended)

```
You are evaluating a candidate's answer to the following question:

QUESTION: {question_text}

[Optional for Follow-ups]:
PREVIOUS ATTEMPTS: {previous_attempts}
UNRESOLVED GAPS: {gap_list}
PARENT IDEAL ANSWER: {ideal_answer}

CANDIDATE ANSWER: {answer_text}

Evaluate the answer and provide:

1. NUMERIC SCORES (1-4 for each):
   - Communication: [score] (Did they explain their thinking?)
   - Problem-Solving: [score] (Is approach sound and optimized?)
   - Technical Competency: [score] (Is code correct and clean?)
   - Testing: [score] (Did they consider edge cases?)

2. OVERALL SCORE (0-100): [score]

3. SEMANTIC METRICS:
   - Completeness (0-1): [score]
   - Relevance (0-1): [score]
   - Sentiment: confident | uncertain | nervous

4. KEY FEEDBACK:
   - Summary: [1-2 sentences]
   - Strengths: [3 bullets]
   - Weaknesses: [3 bullets]
   - Improvement suggestions: [3 bullets]

5. GAPS IDENTIFIED:
   - [Gap concept]: [severity: minor/moderate/major]
   - ...

6. FOLLOW-UP RECOMMENDATION:
   - Follow-up needed? Yes/No
   - If yes, focus on: [gap_name]
```

---

## 7. Implementation Checklist

### Domain Layer
- [ ] Add 4 dimension scores to `Evaluation` model (communication, problem_solving, technical_competency, testing)
- [ ] Ensure `ConceptGap.resolved` and `attempt_number` tracked properly
- [ ] Validate attempt_number enforcement (1-3 max)

### Application Layer
- [ ] Create `PerQuestionEvaluationDTO` response
- [ ] Create `FollowUpProgressionDTO` for aggregated attempts
- [ ] Enhance `InterviewCompletionSummaryDTO` with dimension aggregates and trends
- [ ] Create `ConceptGapDetailDTO` with resolution tracking

### Adapter Layer (LLM)
- [ ] Update LLM evaluation prompts to request 4 dimension scores
- [ ] Update follow-up generation to consider `FollowUpEvaluationContext`

### API Layer
- [ ] Endpoint: `GET /interviews/{id}` returns full `InterviewSummaryDTO`
- [ ] Endpoint: `GET /interviews/{id}/questions/{qid}` returns `FollowUpProgressionDTO`
- [ ] Ensure attempt_number visible in all responses

---

## 8. Data Flow Example

```
Attempt 1 (Initial):
  Answer submitted → LLM evaluation (rubric-based)
  → Scores: [3.0, 3.5, 3.5, 2.5] (dims), raw_score=75, penalty=0, final=75
  → Gaps: ["null_safety" (major), "complexity_discussion" (minor)]
  → Follow-up triggered? YES (major gap exists)

Attempt 2 (Follow-up 1):
  Follow-up question: "Let me ask more about null safety..."
  Answer submitted → LLM evaluation (with context: parent gaps, previous scores)
  → Scores: [3.2, 3.5, 3.6, 3.0], raw_score=80, penalty=-5, final=75
  → Gaps: ["null_safety" RESOLVED, "complexity_discussion" unresolved]
  → Follow-up triggered? NO (only 1 gap remains, threshold met)

Interview Summary:
  Question 1: final_score=75, attempts=2, gaps_resolved=1/2
  Dimension averages: [3.1, 3.5, 3.55, 2.75]
  Overall: 72 (aggregate + penalties)
  Assessment: "Hire" (meets threshold, shows improvement)
```

---

## 9. Decision Outcomes (Final Assessment)

**Based on overall_score and pattern analysis**:

- **Strong Hire** (80+): Excellent across dimensions, gaps minimal or well-resolved
- **Hire** (70-80): Good fundamentals, some gaps identified but resolvable
- **Leaning Hire** (60-70): Decent attempt, multiple gaps or weak dimension
- **Leaning No Hire** (40-60): Struggles evident, poor gap resolution
- **No Hire** (0-40): Fundamental misunderstanding or very weak
- **Strong No Hire** (<20): Critical gaps, no improvement across attempts

---

## 10. Key Principles (Remember!)

1. **Attempt-aware**: Same answer on attempt 1 vs. attempt 3 = different penalties
2. **Gap-driven**: Follow-ups triggered by concept gaps, not generic re-asks
3. **Multi-dimensional**: Score 4 dimensions, NOT single overall score first
4. **Progression-tracked**: Attempt sequence visible in all responses
5. **Narrative-supported**: Numeric scores backed by strengths/weaknesses/suggestions
6. **Aggregated-for-insights**: Synthesize per-question into interview-wide trends

---

**See full research**: `docs/interview-feedback-research.md`
