# Interview Feedback System Architecture

Visual guide to interview feedback data structures, flow, and implementation patterns.

---

## 1. Evaluation Data Flow (Per Question)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CANDIDATE SUBMITS ANSWER                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Question Attempt #1  │
        │    (Initial Answer)    │
        └────────────┬───────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │  LLM Evaluation (Rubric)     │
      │  ┌────────────────────────┐  │
      │  │ Communication:    3.0  │  │
      │  │ Problem-Solving:  3.5  │  │
      │  │ Technical:        3.5  │  │
      │  │ Testing:          2.5  │  │
      │  │ ────────────────────  │  │
      │  │ Raw Score:       74.5  │  │
      │  └────────────────────────┘  │
      │                              │
      │  Gaps Identified:            │
      │  - null_safety (major)       │
      │  - edge_cases (moderate)     │
      └──────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Apply Attempt Penalty:    │
        │  Raw (74.5) + Penalty (0)  │
        │  = Final Score (74.5)      │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Gap Analysis Decision     │
        │                            │
        │  Gaps exist & not         │
        │  resolved? → Follow-up    │
        │  Trigger!                 │
        └────────────┬───────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
        ▼                           ▼
  ┌──────────────┐        ┌──────────────────┐
  │  Attempt #2  │        │  Move to Next Q  │
  │ (Follow-up)  │        │   (No gaps)      │
  └──────┬───────┘        └──────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Penalty: -5     │
    │ Score: (80)-5   │
    │ = 75            │
    └────────┬────────┘
             │
             ▼
         ┌─────────────┐
         │ Gaps still? │
         └────┬────┬───┘
         YES  │    │  NO
             ▼    ▼
        Q2/Q3  Next Q


═══════════════════════════════════════════════════════════════

RESULT: AttemptDetailDTO
├── attempt_number: 1
├── final_score: 74.5
├── dimensions: {comm: 3.0, problem: 3.5, ...}
├── gaps_identified: ["null_safety", "edge_cases"]
├── follow_up_triggered: true
└── follow_up_reason: "Major gap: null_safety"
```

---

## 2. Follow-Up Progression Sequence

```
QUESTION 1: "Implement binary search"
│
├── ATTEMPT 1 (Main)
│   ├── Score: 75 (raw 75, penalty 0)
│   ├── Dimensions: [3.0, 3.5, 3.5, 2.5]
│   ├── Gaps: ["off_by_one", "null_check"]
│   └── → Trigger Follow-up
│
├── FOLLOW-UP QUESTION 1
│   │ (Gap-targeted: "Let's focus on null safety...")
│   │
│   └── ATTEMPT 2 (Follow-up 1)
│       ├── Score: 72 (raw 77, penalty -5)
│       ├── Dimensions: [3.1, 3.5, 3.6, 3.0]
│       ├── Gaps: ["off_by_one" PERSISTENT]
│       ├── Gap Status: null_check RESOLVED
│       └── → No more follow-ups
│
└── DECISION: Proceed to Q2
    ├── Score progression: [75, 72]
    ├── Gaps resolved: 1/2
    ├── Trend: Declining but resolved critical gap


═══════════════════════════════════════════════════════════════

RESULT: FollowUpProgressionDTO
├── parent_question_id: Q1_UUID
├── attempts: [AttemptDetail#1, AttemptDetail#2]
├── initial_gaps: ["off_by_one", "null_check"]
├── resolved_gaps: ["null_check"]
├── persistent_gaps: ["off_by_one"]
├── gap_resolution_rate: 0.5
├── score_progression: [75, 72]
└── completion_reason: "max_attempts_reached"
```

---

## 3. DTO Hierarchy (Nested Structure)

```
┌──────────────────────────────────────────────────────────────┐
│        InterviewCompletionSummaryDTO                         │
│                                                              │
│  overall_score: 72.3                                        │
│  assessment_band: "Hire"                                    │
│  questions_summary: [...]     ◄────┐                       │
│  dimension_scores: {...}      ◄─┐  │                       │
│  performance_trend: "stable"    │  │                       │
│  all_gaps_identified: [...]    │  │                       │
│  gap_summary: {...}            │  │                       │
│  strengths_pattern: [...]      │  │                       │
│                                │  │                       │
└────────────────┬───────────────┘  │                       │
                 │                  │                       │
       ┌─────────┴───────────┐      │                       │
       │                     │      │                       │
       ▼                     ▼      │                       │
  ┌──────────────────┐  ┌──────────────────┐               │
  │ QuestionSummary  │  │ DimensionAggreg. │◄──────────────┘
  │ [Q1, Q2, Q3]     │  │                  │
  │                  │  │ comm_avg: 3.15   │
  │ final_score: 75  │  │ problem_avg: 3.2 │
  │ attempt_count: 2 │  │ tech_avg: 3.4    │
  │                  │  │ testing_avg: 2.8 │
  │ ┌────────────────┤  └──────────────────┘
  │ │ progression    │
  │ │ (nested ▼)     │
  │ └────────────────┘
  │
  ▼
  ┌──────────────────────────┐
  │ FollowUpProgressionDTO   │
  │                          │
  │ attempts: [             │
  │   {                      │
  │     attempt_number: 1    │
  │     final_score: 75      │
  │     dimensions: {...}    │ ◄─ DimensionScoreDTO[]
  │     gaps: [...]          │ ◄─ ConceptGapDetailDTO[]
  │   },                      │
  │   {                       │
  │     attempt_number: 2     │
  │     final_score: 72       │
  │     ...                   │
  │   }                       │
  │ ]                        │
  │                          │
  │ score_progression: [75, 72]
  └──────────────────────────┘


KEY: ► Nested structure allows drill-down queries
     ► Enables clients to show summary or detailed views
     ► Maintains data relationships (gaps → attempts → questions)
```

---

## 4. Evaluation Dimension Scoring Model

```
                    EACH DIMENSION
                    ┌──────────┐
                    │  Score   │ 1-4 scale
                    │ 1: Poor  │
                    │ 2: Fair  │
                    │ 3: Good  │
                    │ 4: Exc.  │
                    └──────────┘

    DIMENSION 1               DIMENSION 2
   Communication          Problem-Solving
   ┌────────────────┐    ┌────────────────┐
   │ Score: 3.0     │    │ Score: 3.5     │
   │ % 75%          │    │ % 87.5%        │
   │ Clear? ✓ Mostly│    │ Sound? ✓ Yes   │
   │ Vocal? ✓ Good │    │ Optimal? ~ Near│
   └────────────────┘    └────────────────┘


    DIMENSION 3               DIMENSION 4
   Technical Comp.            Testing
   ┌────────────────┐    ┌────────────────┐
   │ Score: 3.5     │    │ Score: 2.5     │
   │ % 87.5%        │    │ % 62.5%        │
   │ Code? ✓ Clean  │    │ Edges? ✗ Missed│
   │ Lang? ✓ Good   │    │ Cases? ~ Some  │
   └────────────────┘    └────────────────┘

                         └─ WEAKEST DIMENSION
                            Focus area for improvement


AGGREGATION:
───────────────────────────
(3.0 + 3.5 + 3.5 + 2.5) / 4 = 3.125 avg per dimension
                            = 78.1% overall
```

---

## 5. Gap Tracking Across Attempts

```
ATTEMPT 1:
┌─────────────────────────────────────┐
│ Gaps Identified:                    │
│ ┌─ null_safety       [MAJOR]        │
│ │  - Unresolved                     │
│ │  - Severity: High impact          │
│ │                                   │
│ └─ off_by_one_error [MODERATE]      │
│    - Unresolved                     │
│    - Severity: Medium impact        │
│                                     │
│ Score: 75                           │
│ Completeness: 0.78 (< 0.8 threshold)
└─────────────────────────────────────┘
           │
           │ Follow-up triggered
           │ (Major gap exists)
           ▼
ATTEMPT 2 (Follow-up):
┌─────────────────────────────────────┐
│ Focus: null_safety                  │
│ Previous gaps to consider:          │
│ - null_safety, off_by_one_error     │
│ - Previous score: 75                │
│                                     │
│ Gaps After Attempt 2:               │
│ ┌─ null_safety       [RESOLVED!] ✓  │
│ │  - Candidate addressed directly   │
│ │  - Score improved to 77           │
│ │                                   │
│ └─ off_by_one_error [PERSISTENT]    │
│    - Still unresolved               │
│    - Needs more practice            │
│                                     │
│ Score: 72 (raw 77, penalty -5)      │
│ Completeness: 0.82 (≥ 0.8 threshold)
└─────────────────────────────────────┘
           │
           │ Gap resolution achieved
           │ (1 resolved, 1 persistent)
           │ Max attempts = 2 sufficient
           ▼
DECISION:
┌─────────────────────────────────────┐
│ Move to Question 2                  │
│                                     │
│ Gap Resolution Rate: 1/2 = 50%      │
│ Score Trend: Declining (75 → 72)    │
│ but critical gap (null_safety)      │
│ resolved - acceptable progress      │
└─────────────────────────────────────┘


═════════════════════════════════════════════════════════════

RESULT: ConceptGapDetailDTO[] for both attempts
├── [null_safety]
│   ├── resolved: true
│   ├── resolved_at_attempt: 2
│   ├── resolution_score_improvement: 2.0
│   └── first_identified_at: attempt_1
│
└── [off_by_one_error]
    ├── resolved: false
    ├── resolved_at_attempt: null
    ├── severity: moderate
    └── persistent_since: attempt_1
```

---

## 6. Interview-Wide Analytics Aggregation

```
INTERVIEW QUESTIONS: Q1, Q2, Q3
│
├─ Q1: Binary Search
│  ├─ Score: 75 (attempt 1), 72 (attempt 2) → avg 73.5
│  ├─ Comm: 3.0, Problem: 3.5, Tech: 3.5, Test: 2.5
│  └─ Gaps: 2 identified, 1 resolved, 1 persistent
│
├─ Q2: Rate Limiter
│  ├─ Score: 70 (attempt 1 only)
│  ├─ Comm: 3.0, Problem: 3.0, Tech: 3.2, Test: 2.8
│  └─ Gaps: 2 identified, 0 resolved, 2 persistent
│
└─ Q3: Database Design
   ├─ Score: 68 (attempt 1 only)
   ├─ Comm: 3.2, Problem: 2.8, Tech: 3.4, Test: 2.6
   └─ Gaps: 1 identified, 0 resolved, 1 persistent

═══════════════════════════════════════════════════════════════

AGGREGATION:
┌──────────────────────────────────────────────────┐
│ Overall Score: 72.3                              │
│ (Weighted average across questions)              │
│                                                  │
│ Dimension Averages (across all questions):       │
│ ┌──────────────────────────────────────────────┐ │
│ │ Communication:           (3.0+3.0+3.2)/3     │ │
│ │                          = 3.07              │ │
│ │                          = 77% of dimension  │ │
│ │                          → Good              │ │
│ │                                              │ │
│ │ Problem-Solving:         (3.5+3.0+2.8)/3     │ │
│ │                          = 3.10              │ │
│ │                          → Good              │ │
│ │                                              │ │
│ │ Technical Competency:    (3.5+3.2+3.4)/3     │ │
│ │                          = 3.37              │ │
│ │                          = 84% of dimension  │ │
│ │                          → STRONGEST         │ │
│ │                                              │ │
│ │ Testing:                 (2.5+2.8+2.6)/3     │ │
│ │                          = 2.63              │ │
│ │                          = 66% of dimension  │ │
│ │                          → WEAKEST ✗         │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ Performance Trend:                               │
│ Q1→Q2: 73.5 → 70   (declining -3.5)              │
│ Q2→Q3: 70 → 68     (declining -2)                │
│ Overall: DECLINING TREND                        │
│                                                  │
│ Gap Summary:                                     │
│ Total identified: 5 unique gaps                  │
│ Resolved: 1 (20%)                                │
│ Persistent: 4 (80%)                              │
│ Top gaps: off_by_one, distributed_systems,      │
│           complexity_analysis                   │
│                                                  │
│ Assessment: LEANING NO HIRE                      │
│ (Declining trend + high gap persistence)        │
└──────────────────────────────────────────────────┘
```

---

## 7. LLM Evaluation Prompt Structure

```
┌───────────────────────────────────────────────────┐
│        LLM EVALUATION WORKFLOW                    │
└───────┬───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────┐
│ INPUT: Question + Answer + Context                │
│                                                   │
│ On Follow-ups:                                    │
│ ┌─────────────────────────────────────────────┐   │
│ │ Previous Attempts:                          │   │
│ │ - Attempt 1 Score: 75                       │   │
│ │ - Attempt 1 Gaps: [null_safety, off_by_one] │   │
│ │                                              │   │
│ │ Unresolved from Previous:                    │   │
│ │ - off_by_one_error (severity: moderate)     │   │
│ │                                              │   │
│ │ Ideal Answer Reference: (for comparison)     │   │
│ │ "Check bounds, handle off-by-one..."        │   │
│ └─────────────────────────────────────────────┘   │
│                                                   │
│ RUBRIC PROVIDED:                                  │
│ ┌─────────────────────────────────────────────┐   │
│ │ Evaluate on 1-4 scale:                      │   │
│ │ - Communication: Clarity of explanation     │   │
│ │ - Problem-Solving: Sound approach           │   │
│ │ - Technical Competency: Code quality        │   │
│ │ - Testing: Edge case coverage               │   │
│ │                                              │   │
│ │ For each gap identified:                     │   │
│ │ - Concept name (e.g., "null_safety")        │   │
│ │ - Severity (minor/moderate/major)           │   │
│ │ - Context (why it matters)                  │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────┐
│ LLM ANALYSIS                                      │
│                                                   │
│ Step 1: Evaluate dimensions                       │
│ Step 2: Calculate raw score                       │
│ Step 3: Assess completeness/relevance             │
│ Step 4: Identify gaps                             │
│ Step 5: Generate narrative feedback               │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────┐
│ OUTPUT: Structured JSON                           │
│                                                   │
│ {                                                 │
│   "dimension_scores": {                           │
│     "communication": 3.0,                         │
│     "problem_solving": 3.5,                       │
│     "technical_competency": 3.5,                  │
│     "testing": 2.5                                │
│   },                                              │
│   "raw_score": 74.5,                              │
│   "completeness": 0.78,                           │
│   "relevance": 0.90,                              │
│   "sentiment": "confident",                       │
│   "gaps": [                                       │
│     {                                             │
│       "concept": "off_by_one_error",             │
│       "severity": "moderate",                     │
│       "description": "Loop condition issue"       │
│     }                                             │
│   ],                                              │
│   "strengths": ["Clear logic", ...],             │
│   "weaknesses": ["Missed edge case", ...],       │
│   "suggestions": ["Test boundary...", ...]       │
│ }                                                 │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────┐
│ APPLICATION LAYER: Applies Penalties              │
│                                                   │
│ raw_score: 74.5                                   │
│ attempt_number: 1 → penalty = 0                   │
│ final_score = 74.5 + 0 = 74.5                     │
│                                                   │
│ (Or if attempt 2: penalty = -5)                   │
│ (Or if attempt 3: penalty = -15)                  │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────┐
│ RESPONSE: AttemptDetailDTO                        │
└───────────────────────────────────────────────────┘
```

---

## 8. Decision Tree: Follow-Up vs. Move On

```
                    AFTER ATTEMPT #1
                         │
                         ▼
                  ┌──────────────┐
                  │ Gaps exist?  │
                  └──────┬───────┘
                       ╱ ╲
                    YES   NO
                    /       \
                   ▼         ▼
            ┌────────────┐ ┌────────┐
            │ Check each │ │ Move   │
            │   gap      │ │ to Q2  │
            └──────┬─────┘ └────────┘
                   │
                   ▼
          ┌──────────────────────┐
          │ Severity high?       │
          │ OR Score < 70?       │
          │ OR Completeness      │
          │    < 0.8?            │
          └──────┬───────────────┘
              ╱   ╲
           YES     NO
           /         \
          ▼           ▼
     ┌─────────┐  ┌──────────┐
     │Follow-UP│  │ Move Q2  │
     │Question │  │(gaps OK) │
     └────┬────┘  └──────────┘
          │
          ▼
   ┌─────────────────┐
   │ Ask Attempt #2  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │Gaps resolved in │
   │ attempt #2?     │
   └────────┬────────┘
       ╱     │      ╲
    YES   SOME   NO
    /      │      \
   ▼       ▼       ▼
  Q2  Follow-up  Max attempts
         Q3       reached
                   │
                   ▼
                 Q2 anyway
```

---

## 9. Penalty Application Timeline

```
TIME ────────────────────────────────────────────────────
      │
      ├─ 0:00 Attempt 1 submitted
      │        │
      │        ├─ Evaluated: raw_score = 75
      │        ├─ Penalty applied: 0 (first attempt)
      │        ├─ Final = 75 + 0 = 75
      │        └─ Gaps identified: 2
      │
      ├─ 0:30 Follow-up question generated
      │
      ├─ 2:00 Attempt 2 submitted (follow-up answer)
      │        │
      │        ├─ Evaluated: raw_score = 80
      │        ├─ Penalty applied: -5 (second attempt)
      │        ├─ Final = 80 - 5 = 75
      │        ├─ Gaps: 1 resolved, 1 persistent
      │        └─ Score: "decent but declining penalty"
      │
      ├─ 2:30 Gap resolved? Check...
      │        NO → More work needed
      │
      ├─ 3:00 Follow-up #2 generated
      │
      ├─ 4:30 Attempt 3 submitted
      │        │
      │        ├─ Evaluated: raw_score = 82
      │        ├─ Penalty applied: -15 (third attempt)
      │        ├─ Final = 82 - 15 = 67
      │        ├─ Score: "lower despite high raw score"
      │        └─ Reason: Max attempts exhausted
      │
      ├─ 5:00 Decision: Move to Question 2
      │        └─ (Gap persistence signals need for more practice)
      │
      └─ 5:15 Interview continues...


═════════════════════════════════════════════════════════════

PENALTY RATIONALE:

Attempt #1 (0):
  - Candidate sees question first time
  - No prior context about gaps
  - Fair to expect struggle

Attempt #2 (-5):
  - Candidate knows what gap exists
  - Follow-up is targeted hint
  - Should improve with second try
  - Penalty = "you should have caught it"

Attempt #3 (-15):
  - Max attempts reached
  - Interview time limited
  - Persistent gap = candidate can't apply feedback
  - Severe penalty indicates learning gap
```

---

## 10. API Response Structure (Summary)

```
GET /interviews/{interview_id}
│
├─ Status: 200 OK
│
└─ Body: InterviewCompletionSummaryDTO
   │
   ├─ metadata
   │  ├─ interview_id
   │  ├─ candidate_name
   │  ├─ completed_at
   │  └─ duration_minutes
   │
   ├─ overall_assessment
   │  ├─ overall_score: 72.3
   │  ├─ assessment_band: "Hire"
   │  └─ recommendation: "Proceed to next round"
   │
   ├─ questions_summary[]
   │  ├─ [0] Q1
   │  │  ├─ final_score: 73.5
   │  │  ├─ attempt_count: 2
   │  │  ├─ dimensions: {communication: 3.05, ...}
   │  │  └─ gap_summary: {identified: 2, resolved: 1}
   │  │
   │  ├─ [1] Q2
   │  │  ├─ final_score: 70
   │  │  ├─ attempt_count: 1
   │  │  └─ ...
   │  │
   │  └─ [2] Q3
   │     ├─ final_score: 68
   │     └─ ...
   │
   ├─ dimension_scores
   │  ├─ communication_avg: 3.07
   │  ├─ problem_solving_avg: 3.10
   │  ├─ technical_competency_avg: 3.37
   │  ├─ testing_avg: 2.63
   │  ├─ strongest_dimension: "technical_competency"
   │  └─ weakest_dimension: "testing"
   │
   ├─ performance_trend: "declining"
   │
   ├─ gap_summary
   │  ├─ total_unique: 5
   │  ├─ resolved: 1
   │  ├─ persistent: 4
   │  └─ top_persistent_gaps: ["off_by_one", ...]
   │
   ├─ strengths_pattern
   │  ├─ "Systematic problem decomposition"
   │  ├─ "Clean code implementation"
   │  └─ "Good high-level understanding"
   │
   ├─ weaknesses_pattern
   │  ├─ "Insufficient edge case testing"
   │  ├─ "Limited distributed systems knowledge"
   │  └─ "No complexity analysis discussion"
   │
   └─ improvement_areas
      ├─ "Edge case handling"
      ├─ "Distributed systems patterns"
      └─ "Complexity analysis"
```

---

## Key Takeaways

1. **4-Dimensional Scoring**: Always rate communication, problem-solving, technical, and testing separately
2. **Attempt-Aware Penalties**: Use 0/-5/-15 progression (not -5 flat)
3. **Gap-Driven Follow-Ups**: Only trigger when unresolved gaps exist
4. **Nested DTO Hierarchy**: Enables drill-down analytics without data duplication
5. **Rubric-Based LLM**: Consistent evaluation via structured prompts
6. **Aggregate Insights**: Synthesize per-question data into interview-wide trends
7. **Narrative + Numeric**: Both scores and feedback required for actionable insights

---

**Reference Docs**:
- `interview-feedback-research.md` - Full technical details
- `feedback-patterns-quick-reference.md` - TL;DR version
- `dto-design-patterns.md` - Code-ready implementations
