# Phase 3: Enhanced Answer Evaluation

**Duration**: 3 days
**Priority**: Critical
**Dependencies**: Phase 1 (Speech Integration), Phase 2 (WebSocket Protocol)

## Context

Current `ProcessAnswerAdaptiveUseCase` only evaluates text semantically. Need to add voice metrics analysis and combine both scores into overall evaluation.

**Context Links**:
- `src/application/use_cases/process_answer_adaptive.py` - Current evaluation (418 lines)
- `src/domain/models/answer.py` - Answer model (146 lines)

## Requirements

### Multi-Dimensional Evaluation

**Theoretical Evaluation (70% weight)**:
- Semantic similarity (LLM)
- Completeness
- Relevance
- Gap detection

**Speaking Evaluation (30% weight)**:
- Intonation score
- Fluency score
- Confidence score
- Speaking rate

**Overall Evaluation**:
- Combined weighted score
- Detailed breakdown
- Improvement suggestions

## Architecture

### CombineEvaluationUseCase

```python
# src/application/use_cases/combine_evaluation.py
class CombineEvaluationUseCase:
    """Combine theoretical and speaking evaluations."""

    def __init__(self):
        self.theoretical_weight = 0.7
        self.speaking_weight = 0.3

    def execute(
        self,
        theoretical_eval: AnswerEvaluation,
        voice_metrics: dict[str, float],
    ) -> dict[str, Any]:
        """Combine evaluations with weighted scoring.

        Returns:
            {
                "overall_score": float,  # 0-100
                "theoretical_score": float,
                "speaking_score": float,
                "breakdown": {...},
                "combined_feedback": str,
            }
        """
        theoretical_score = theoretical_eval.score
        speaking_score = self._calculate_speaking_score(voice_metrics)

        overall_score = (
            theoretical_score * self.theoretical_weight +
            speaking_score * self.speaking_weight
        )

        return {
            "overall_score": overall_score,
            "theoretical_score": theoretical_score,
            "speaking_score": speaking_score,
            "breakdown": {
                "theoretical": {
                    "score": theoretical_score,
                    "weight": self.theoretical_weight,
                    "metrics": {
                        "semantic_similarity": theoretical_eval.semantic_similarity,
                        "completeness": theoretical_eval.completeness,
                        "relevance": theoretical_eval.relevance,
                    }
                },
                "speaking": {
                    "score": speaking_score,
                    "weight": self.speaking_weight,
                    "metrics": voice_metrics,
                }
            },
            "combined_feedback": self._generate_combined_feedback(
                theoretical_eval, voice_metrics
            ),
        }

    def _calculate_speaking_score(
        self,
        voice_metrics: dict[str, float]
    ) -> float:
        """Calculate speaking score from voice metrics."""
        # Average of intonation, fluency, confidence (all 0-1)
        scores = [
            voice_metrics.get("intonation_score", 0.5),
            voice_metrics.get("fluency_score", 0.5),
            voice_metrics.get("confidence_score", 0.5),
        ]
        return sum(scores) / len(scores) * 100  # Convert to 0-100
```

## Implementation Steps

### Day 1: Voice Metrics Integration

**Step 1**: Enhance Answer model
- Add voice_metrics field (dict)
- Add speaking_score field (float)
- Add methods: get_voice_metrics(), has_voice_metrics()

**Step 2**: Update ProcessAnswerAdaptiveUseCase
- Extract voice metrics from STT result
- Store in Answer.voice_metrics
- Add parallel evaluation (asyncio.gather)

### Day 2: Combined Evaluation

**Step 1**: Create CombineEvaluationUseCase
- Implement weighted scoring
- Implement speaking score calculation
- Add combined feedback generation

**Step 2**: Update ProcessAnswerAdaptiveUseCase
- Call CombineEvaluationUseCase after parallel eval
- Store combined scores in Answer
- Update evaluation message format

### Day 3: Testing

**Step 1**: Unit tests
- Test weighted scoring
- Test speaking score calculation
- Test parallel evaluation

**Step 2**: Integration tests
- Test with real voice audio
- Verify score consistency
- Validate feedback quality

## Todo List

**Day 1**:
- [ ] Add voice_metrics and speaking_score to Answer model
- [ ] Update ProcessAnswerAdaptiveUseCase with parallel eval
- [ ] Extract voice metrics from STT result
- [ ] Write unit tests for parallel evaluation

**Day 2**:
- [ ] Create CombineEvaluationUseCase
- [ ] Implement weighted scoring algorithm
- [ ] Implement combined feedback generation
- [ ] Update evaluation message DTO
- [ ] Write unit tests for combined evaluation

**Day 3**:
- [ ] Write integration tests with real audio
- [ ] Validate score consistency across samples
- [ ] Performance test parallel evaluation
- [ ] Update docs with evaluation architecture

## Success Criteria

- ✅ Parallel evaluation completes in <3s
- ✅ Combined score reflects both semantic and voice quality
- ✅ Voice metrics properly extracted and stored
- ✅ Unit test coverage >=80%
- ✅ Integration tests pass with real audio
