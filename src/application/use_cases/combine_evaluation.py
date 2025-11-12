"""Combine theoretical and speaking evaluations into overall score."""

import logging
from typing import Any

from ...domain.models.answer import AnswerEvaluation

logger = logging.getLogger(__name__)


class CombineEvaluationUseCase:
    """Combine theoretical (semantic) and speaking (voice) evaluations.

    This use case implements weighted scoring to produce an overall
    interview performance score combining both content quality and
    speaking delivery.

    Weights:
    - Theoretical: 70% (semantic similarity, completeness, relevance)
    - Speaking: 30% (intonation, fluency, confidence)
    """

    def __init__(
        self,
        theoretical_weight: float = 0.7,
        speaking_weight: float = 0.3,
    ):
        """Initialize combine evaluation use case.

        Args:
            theoretical_weight: Weight for theoretical evaluation (default 0.7)
            speaking_weight: Weight for speaking evaluation (default 0.3)
        """
        if abs(theoretical_weight + speaking_weight - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")

        self.theoretical_weight = theoretical_weight
        self.speaking_weight = speaking_weight

    def execute(
        self,
        theoretical_eval: AnswerEvaluation,
        voice_metrics: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Combine theoretical and speaking evaluations.

        Args:
            theoretical_eval: Semantic evaluation from LLM
            voice_metrics: Voice quality metrics from STT (optional)

        Returns:
            Dict with combined evaluation:
            {
                "overall_score": float (0-100),
                "theoretical_score": float (0-100),
                "speaking_score": float | None (0-100),
                "breakdown": {...},
                "combined_feedback": str,
            }
        """
        theoretical_score = theoretical_eval.score

        # Calculate speaking score if voice metrics available
        if voice_metrics:
            speaking_score = self._calculate_speaking_score(voice_metrics)
            overall_score = (
                theoretical_score * self.theoretical_weight
                + speaking_score * self.speaking_weight
            )
        else:
            # Text-only answer: use 100% theoretical weight
            speaking_score = None
            overall_score = theoretical_score

        logger.info(
            f"Combined evaluation: theoretical={theoretical_score:.1f}, "
            f"speaking={speaking_score:.1f if speaking_score else 'N/A'}, "
            f"overall={overall_score:.1f}"
        )

        return {
            "overall_score": round(overall_score, 2),
            "theoretical_score": round(theoretical_score, 2),
            "speaking_score": round(speaking_score, 2) if speaking_score else None,
            "breakdown": self._build_breakdown(
                theoretical_eval, voice_metrics, theoretical_score, speaking_score
            ),
            "combined_feedback": self._generate_combined_feedback(
                theoretical_eval, voice_metrics
            ),
        }

    def _calculate_speaking_score(self, voice_metrics: dict[str, float]) -> float:
        """Calculate speaking score from voice metrics.

        Args:
            voice_metrics: Dict with intonation_score, fluency_score, confidence_score

        Returns:
            Speaking score (0-100)
        """
        # Get metrics with defaults
        intonation = voice_metrics.get("intonation_score", 0.5)
        fluency = voice_metrics.get("fluency_score", 0.5)
        confidence = voice_metrics.get("confidence_score", 0.5)

        # Average and convert to 0-100 scale
        avg_score = (intonation + fluency + confidence) / 3.0
        return avg_score * 100.0

    def _build_breakdown(
        self,
        theoretical_eval: AnswerEvaluation,
        voice_metrics: dict[str, float] | None,
        theoretical_score: float,
        speaking_score: float | None,
    ) -> dict[str, Any]:
        """Build detailed breakdown of evaluation components.

        Args:
            theoretical_eval: Semantic evaluation
            voice_metrics: Voice metrics (optional)
            theoretical_score: Calculated theoretical score
            speaking_score: Calculated speaking score (optional)

        Returns:
            Detailed breakdown dict
        """
        breakdown: dict[str, Any] = {
            "theoretical": {
                "score": round(theoretical_score, 2),
                "weight": self.theoretical_weight,
                "metrics": {
                    "semantic_similarity": round(theoretical_eval.semantic_similarity, 3),
                    "completeness": round(theoretical_eval.completeness, 3),
                    "relevance": round(theoretical_eval.relevance, 3),
                },
            }
        }

        if voice_metrics and speaking_score is not None:
            breakdown["speaking"] = {
                "score": round(speaking_score, 2),
                "weight": self.speaking_weight,
                "metrics": {
                    "intonation_score": round(voice_metrics.get("intonation_score", 0.5), 3),
                    "fluency_score": round(voice_metrics.get("fluency_score", 0.5), 3),
                    "confidence_score": round(voice_metrics.get("confidence_score", 0.5), 3),
                    "speaking_rate_wpm": voice_metrics.get("speaking_rate_wpm", 0),
                },
            }

        return breakdown

    def _generate_combined_feedback(
        self,
        theoretical_eval: AnswerEvaluation,
        voice_metrics: dict[str, float] | None,
    ) -> str:
        """Generate combined feedback message.

        Args:
            theoretical_eval: Semantic evaluation
            voice_metrics: Voice metrics (optional)

        Returns:
            Combined feedback string
        """
        feedback_parts = []

        # Theoretical feedback
        if theoretical_eval.reasoning:
            feedback_parts.append(f"Content: {theoretical_eval.reasoning}")

        # Speaking feedback
        if voice_metrics:
            speaking_feedback = self._generate_speaking_feedback(voice_metrics)
            feedback_parts.append(f"Delivery: {speaking_feedback}")

        return " | ".join(feedback_parts) if feedback_parts else "Evaluation complete."

    def _generate_speaking_feedback(self, voice_metrics: dict[str, float]) -> str:
        """Generate feedback for speaking delivery.

        Args:
            voice_metrics: Voice quality metrics

        Returns:
            Speaking feedback string
        """
        intonation = voice_metrics.get("intonation_score", 0.5)
        fluency = voice_metrics.get("fluency_score", 0.5)
        confidence = voice_metrics.get("confidence_score", 0.5)

        feedback_parts = []

        if intonation >= 0.8:
            feedback_parts.append("excellent voice expression")
        elif intonation >= 0.6:
            feedback_parts.append("good voice modulation")
        else:
            feedback_parts.append("work on voice variety")

        if fluency >= 0.8:
            feedback_parts.append("smooth delivery")
        elif fluency >= 0.6:
            feedback_parts.append("adequate fluency")
        else:
            feedback_parts.append("practice speaking more fluently")

        if confidence >= 0.8:
            feedback_parts.append("confident tone")
        elif confidence >= 0.6:
            feedback_parts.append("moderate confidence")
        else:
            feedback_parts.append("build speaking confidence")

        return ", ".join(feedback_parts)
