# Phase 6: Final Summary Generation

**Duration**: 2 days
**Priority**: Medium
**Dependencies**: Phase 5 (Session Orchestration)

## Context

After interview completes, need to generate comprehensive feedback report aggregating all evaluations (main questions + follow-ups).

**Context Links**:
- `src/application/use_cases/complete_interview.py` - Current completion (25 lines, minimal)
- `src/adapters/api/websocket/interview_handler.py` - _complete_interview() helper (lines 290-320)

## Requirements

### Comprehensive Summary

**Aggregate Metrics**:
- Overall score (weighted avg of all evaluations)
- Theoretical score avg
- Speaking score avg
- Total questions (main + follow-ups)
- Total follow-ups generated
- Concepts mastered vs gaps remaining

**Per-Question Analysis**:
- Main question evaluations
- Follow-up question evaluations (grouped by parent)
- Gap progression (initial → after follow-ups)
- Improvement trajectory

**Recommendations**:
- Strengths (top 3-5)
- Weaknesses (top 3-5)
- Study recommendations (topic-specific)
- Interview technique tips (voice, pacing, structure)

## Architecture

### GenerateSummaryUseCase

```python
# src/application/use_cases/generate_summary.py
class GenerateSummaryUseCase:
    """Generate comprehensive interview summary."""

    def __init__(
        self,
        interview_repository: InterviewRepositoryPort,
        answer_repository: AnswerRepositoryPort,
        question_repository: QuestionRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
        llm: LLMPort,
    ):
        self.interview_repo = interview_repository
        self.answer_repo = answer_repository
        self.question_repo = question_repository
        self.follow_up_repo = follow_up_question_repository
        self.llm = llm

    async def execute(self, interview_id: UUID) -> dict[str, Any]:
        """Generate comprehensive summary.

        Returns:
            {
                "interview_id": UUID,
                "overall_score": float,
                "theoretical_score_avg": float,
                "speaking_score_avg": float,
                "total_questions": int,
                "total_follow_ups": int,
                "question_summaries": [...],
                "gap_progression": {...},
                "strengths": [str],
                "weaknesses": [str],
                "recommendations": [str],
                "completion_time": datetime,
            }
        """
        # Fetch interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        # Fetch all answers (main + follow-ups)
        all_answers = await self.answer_repo.get_by_interview_id(interview_id)

        # Group answers by main question
        question_groups = await self._group_answers_by_main_question(
            interview, all_answers
        )

        # Calculate aggregate metrics
        metrics = self._calculate_aggregate_metrics(all_answers)

        # Analyze gap progression
        gap_progression = await self._analyze_gap_progression(question_groups)

        # Generate LLM-powered recommendations
        recommendations = await self._generate_recommendations(
            interview, all_answers, gap_progression
        )

        return {
            "interview_id": interview_id,
            "overall_score": metrics["overall_score"],
            "theoretical_score_avg": metrics["theoretical_avg"],
            "speaking_score_avg": metrics["speaking_avg"],
            "total_questions": len(interview.question_ids),
            "total_follow_ups": len(interview.adaptive_follow_ups),
            "question_summaries": await self._create_question_summaries(
                question_groups
            ),
            "gap_progression": gap_progression,
            "strengths": recommendations["strengths"],
            "weaknesses": recommendations["weaknesses"],
            "study_recommendations": recommendations["study_topics"],
            "technique_tips": recommendations["technique_tips"],
            "completion_time": datetime.utcnow(),
        }

    async def _group_answers_by_main_question(
        self,
        interview: Interview,
        all_answers: list[Answer],
    ) -> dict[UUID, dict[str, Any]]:
        """Group answers by main question with follow-ups."""
        groups = {}

        for main_question_id in interview.question_ids:
            main_question = await self.question_repo.get_by_id(main_question_id)

            # Find main answer
            main_answer = next(
                (a for a in all_answers if a.question_id == main_question_id),
                None
            )

            # Find follow-up answers
            follow_ups = await self.follow_up_repo.get_by_parent_question_id(
                main_question_id
            )
            follow_up_answers = [
                next((a for a in all_answers if a.question_id == fu.id), None)
                for fu in follow_ups
            ]

            groups[main_question_id] = {
                "question": main_question,
                "main_answer": main_answer,
                "follow_ups": follow_ups,
                "follow_up_answers": follow_up_answers,
            }

        return groups

    def _calculate_aggregate_metrics(
        self,
        all_answers: list[Answer]
    ) -> dict[str, float]:
        """Calculate aggregate scores."""
        evaluated_answers = [a for a in all_answers if a.is_evaluated()]

        if not evaluated_answers:
            return {
                "overall_score": 0.0,
                "theoretical_avg": 0.0,
                "speaking_avg": 0.0,
            }

        overall_scores = [a.evaluation.score for a in evaluated_answers]
        theoretical_scores = [
            a.evaluation.score * 0.7 for a in evaluated_answers
        ]
        speaking_scores = [
            a.voice_metrics.get("overall_score", 50) * 0.3
            for a in evaluated_answers if a.voice_metrics
        ]

        return {
            "overall_score": sum(overall_scores) / len(overall_scores),
            "theoretical_avg": sum(theoretical_scores) / len(theoretical_scores),
            "speaking_avg": sum(speaking_scores) / len(speaking_scores) if speaking_scores else 50.0,
        }

    async def _analyze_gap_progression(
        self,
        question_groups: dict[UUID, dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze how gaps changed after follow-ups."""
        progression = {
            "questions_with_followups": 0,
            "gaps_filled": 0,
            "gaps_remaining": 0,
            "avg_followups_per_question": 0.0,
        }

        questions_with_followups = 0
        total_followups = 0
        gaps_filled = 0
        gaps_remaining = 0

        for group in question_groups.values():
            main_answer = group["main_answer"]
            follow_up_answers = group["follow_up_answers"]

            if not follow_up_answers:
                continue

            questions_with_followups += 1
            total_followups += len(follow_up_answers)

            # Compare initial gaps vs final gaps
            initial_gaps = set(
                main_answer.gaps.get("concepts", []) if main_answer.gaps else []
            )
            final_answer = follow_up_answers[-1]
            final_gaps = set(
                final_answer.gaps.get("concepts", []) if final_answer.gaps else []
            )

            gaps_filled += len(initial_gaps - final_gaps)
            gaps_remaining += len(final_gaps)

        progression["questions_with_followups"] = questions_with_followups
        progression["gaps_filled"] = gaps_filled
        progression["gaps_remaining"] = gaps_remaining
        progression["avg_followups_per_question"] = (
            total_followups / questions_with_followups
            if questions_with_followups > 0 else 0.0
        )

        return progression

    async def _generate_recommendations(
        self,
        interview: Interview,
        all_answers: list[Answer],
        gap_progression: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Use LLM to generate personalized recommendations."""
        context = {
            "interview_id": str(interview.id),
            "total_answers": len(all_answers),
            "gap_progression": gap_progression,
            "evaluations": [
                {
                    "question_id": str(a.question_id),
                    "score": a.evaluation.score,
                    "strengths": a.evaluation.strengths,
                    "weaknesses": a.evaluation.weaknesses,
                }
                for a in all_answers if a.is_evaluated()
            ],
        }

        return await self.llm.generate_interview_recommendations(context)
```

## Implementation Steps

### Day 1: Use Case Implementation

**Step 1**: Create GenerateSummaryUseCase
- Implement aggregate metrics calculation
- Implement answer grouping by main question
- Implement gap progression analysis

**Step 2**: Enhance LLMPort
- Add generate_interview_recommendations() method
- Implement in OpenAIAdapter and MockLLMAdapter

### Day 2: Integration & Testing

**Step 1**: Update CompleteInterviewUseCase
- Call GenerateSummaryUseCase
- Store summary in Interview metadata
- Send summary message to WebSocket

**Step 2**: Testing
- Unit tests for summary generation
- Integration tests with real data
- Validate recommendation quality

## Todo List

**Day 1**:
- [ ] Create GenerateSummaryUseCase
- [ ] Implement aggregate metrics calculation
- [ ] Implement gap progression analysis
- [ ] Add generate_interview_recommendations() to LLMPort
- [ ] Implement in OpenAIAdapter

**Day 2**:
- [ ] Update CompleteInterviewUseCase to use summary
- [ ] Update WebSocket handler to send summary
- [ ] Write unit tests for summary generation
- [ ] Write integration tests with real interviews
- [ ] Validate recommendation quality

## Success Criteria

- ✅ Summary aggregates all evaluations (main + follow-ups)
- ✅ Gap progression analysis shows before/after
- ✅ LLM-generated recommendations are actionable
- ✅ Overall score correctly weighted
- ✅ Unit test coverage >=80%
