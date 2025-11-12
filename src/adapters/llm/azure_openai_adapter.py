"""Azure OpenAI LLM adapter implementation."""

import json
import re
from typing import Any
from uuid import UUID

from openai import AsyncAzureOpenAI

from ...domain.models.answer import AnswerEvaluation
from ...domain.models.question import Question
from ...domain.ports.llm_port import LLMPort


class AzureOpenAIAdapter(LLMPort):
    """Azure OpenAI implementation of LLM port.

    This adapter encapsulates all Azure OpenAI-specific logic, making it easy
    to swap for another LLM provider without touching domain logic.
    """

    def __init__(
        self,
        api_key: str,
        azure_endpoint: str,
        api_version: str,
        deployment_name: str,
        temperature: float = 0.7,
    ):
        """Initialize Azure OpenAI adapter.

        Args:
            api_key: Azure OpenAI API key
            azure_endpoint: Azure OpenAI endpoint URL (e.g., "https://your-resource.openai.azure.com/")
            api_version: Azure API version (e.g., "2024-02-15-preview")
            deployment_name: Azure deployment name (not model name)
            temperature: Sampling temperature (default: 0.7)
        """
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
        )
        self.model = deployment_name  # Azure uses deployment names instead of model names
        self.temperature = temperature

    async def generate_question(
        self,
        context: dict[str, Any],
        skill: str,
        difficulty: str,
        exemplars: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate an interview question using Azure OpenAI.

        Args:
            context: Interview context
            skill: Target skill to test
            difficulty: Question difficulty level
            exemplars: Optional list of similar questions for inspiration

        Returns:
            Generated question text
        """
        system_prompt = """You are an expert technical interviewer.
        Generate a clear, relevant interview question based on the context provided."""

        user_prompt = f"""
        Generate a {difficulty} difficulty interview question to test: {skill}

        Context:
        - Candidate's background: {context.get('cv_summary', 'Not provided')}
        - Previous topics covered: {context.get('covered_topics', [])}
        - Interview stage: {context.get('stage', 'early')}
        """

        # Add exemplars if provided
        if exemplars:
            user_prompt += "\n\nSimilar questions for inspiration (do NOT copy exactly):\n"
            for i, ex in enumerate(exemplars[:3], 1):  # Limit to 3 exemplars
                user_prompt += f"{i}. \"{ex.get('text', '')}\" ({ex.get('difficulty', 'UNKNOWN')})\n"
            user_prompt += "\nGenerate a NEW question inspired by the style and structure above.\n"

        user_prompt += "\nReturn only the question text, no additional explanation."

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
        )

        content = response.choices[0].message.content
        return content.strip() if content else ""

    @staticmethod
    def _extract_json_from_markdown(content: str) -> str:
        """Extract JSON from markdown code fences if present.

        Args:
            content: Content that may contain markdown-wrapped JSON

        Returns:
            Clean JSON string
        """
        if not content:
            return "{}"

        # Remove markdown code fences (```json ... ``` or ``` ... ```)
        content = re.sub(r'^```(?:json)?\s*\n', '', content.strip(), flags=re.MULTILINE)
        content = re.sub(r'\n```\s*$', '', content.strip(), flags=re.MULTILINE)

        return content.strip()

    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        context: dict[str, Any], # TODO: update context to be more meaningful
    ) -> AnswerEvaluation:
        """Evaluate an answer using Azure OpenAI.

        Args:
            question: The question that was asked
            answer_text: Candidate's answer
            context: Additional context

        Returns:
            Evaluation results
        """
        system_prompt = """You are an expert technical interviewer evaluating candidate answers.
        Provide objective, constructive feedback with specific scores."""

        user_prompt = f"""
        Question: {question.text}
        Question Type: {question.question_type}
        Difficulty: {question.difficulty}
        Expected Skills: {', '.join(question.skills)}

        Candidate's Answer: {answer_text}

        {"Ideal Answer: " + question.ideal_answer if question.ideal_answer else ""}

        Evaluate this answer and provide:
        1. Overall score (0-100)
        2. Completeness score (0-1)
        3. Relevance score (0-1)
        4. Sentiment (confident/uncertain/nervous)
        5. 2-3 strengths
        6. 2-3 weaknesses
        7. 2-3 improvement suggestions
        8. Brief reasoning for the score

        Return as JSON with keys: score, completeness, relevance, sentiment, strengths, weaknesses, improvements, reasoning
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent evaluation
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        content = self._extract_json_from_markdown(content)
        result = json.loads(content)

        return AnswerEvaluation(
            score=float(result.get("score", 0)),
            semantic_similarity=0.0,  # Will be calculated by vector search
            completeness=float(result.get("completeness", 0)),
            relevance=float(result.get("relevance", 0)),
            sentiment=result.get("sentiment"),
            reasoning=result.get("reasoning"),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            improvement_suggestions=result.get("improvements", []),
        )

    async def generate_feedback_report(
        self,
        interview_id: UUID,
        questions: list[Question],
        answers: list[dict[str, Any]],
    ) -> str:
        """Generate comprehensive feedback report.

        Args:
            interview_id: ID of the interview
            questions: All questions asked
            answers: All answers with evaluations

        Returns:
            Formatted feedback report
        """
        system_prompt = """You are an expert career coach providing comprehensive interview feedback.
        Create a detailed, actionable report that helps candidates improve."""

        # Prepare interview summary
        qa_pairs = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            qa_pairs.append(
                f"Q{i+1}: {q.text}\n"
                f"Answer Score: {a.get('evaluation', {}).get('score', 'N/A')}\n"
                f"Evaluation: {a.get('evaluation', {}).get('reasoning', 'N/A')}\n"
            )

        user_prompt = f"""
        Generate a comprehensive interview feedback report for interview {interview_id}.

        Interview Performance:
        {chr(10).join(qa_pairs)}

        Include:
        1. Overall Performance Summary
        2. Key Strengths (with examples)
        3. Areas for Improvement (with specific guidance)
        4. Skill-by-Skill Breakdown
        5. Actionable Next Steps

        Be encouraging but honest. Provide specific examples and actionable advice.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return content or ""

    async def summarize_cv(self, cv_text: str) -> str:
        """Generate a summary of a CV.

        Args:
            cv_text: Extracted CV text

        Returns:
            Summary of the CV
        """
        system_prompt = """You are an expert recruiter analyzing candidate CVs.
        Create concise, informative summaries."""

        user_prompt = f"""
        Summarize this CV in 3-4 sentences, highlighting:
        - Key technical skills and experience
        - Years of experience and seniority level
        - Notable projects or achievements

        CV:
        {cv_text[:2000]}  # Limit to first 2000 chars
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )

        content = response.choices[0].message.content
        return content.strip() if content else ""

    async def extract_skills_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract skills from CV text using Azure OpenAI.

        Args:
            text: CV text to analyze

        Returns:
            List of extracted skills with metadata
        """
        system_prompt = """You are an expert at extracting structured information from CVs.
        Identify technical skills, soft skills, and tools mentioned."""

        user_prompt = f"""
        Extract all skills from this CV text. For each skill, identify:
        - name: The skill name
        - category: "technical", "soft", or "language"
        - proficiency: "beginner", "intermediate", or "expert" (infer from context)

        Return as JSON array with keys: name, category, proficiency

        CV Text:
        {text[:3000]}  # Limit to first 3000 chars
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        content = self._extract_json_from_markdown(content)
        result = json.loads(content)
        skills: list[dict[str, str]] = result.get("skills", [])
        return skills

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
            Exception: If generation fails
        """
        system_prompt = """You are an expert technical interviewer creating reference answers.
        Generate comprehensive, technically accurate ideal answers."""

        user_prompt = f"""
        Question: {question_text}

        Candidate Background:
        - Summary: {context.get('summary', 'Not provided')}
        - Key Skills: {', '.join(context.get('skills', [])[:5])}
        - Experience: {context.get('experience', 'Not specified')} years

        Generate an ideal answer for this interview question. The answer should:
        - Be 150-300 words
        - Demonstrate expert-level understanding
        - Cover key concepts comprehensively
        - Include practical examples if relevant
        - Be technically accurate

        Output only the ideal answer text.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Low for consistency
            max_tokens=500,
        )

        content = response.choices[0].message.content
        return content.strip() if content else ""

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
            Exception: If generation fails
        """
        system_prompt = """You are an expert technical interviewer explaining evaluation criteria.
        Explain why an answer demonstrates mastery."""

        user_prompt = f"""
        Question: {question_text}
        Ideal Answer: {ideal_answer}

        Explain WHY this is an ideal answer in 50-100 words. Focus on:
        - What key concepts are covered
        - Why this demonstrates mastery
        - What would be missing in a weaker answer

        Output only the rationale text.
        """

        # Note: For rationale, we use the same deployment/model
        # In Azure, you might have separate deployments for different models
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        content = response.choices[0].message.content
        return content.strip() if content else ""

    async def detect_concept_gaps(
        self,
        answer_text: str,
        ideal_answer: str,
        question_text: str,
        keyword_gaps: list[str],
    ) -> dict[str, Any]:
        """Detect concept gaps using Azure OpenAI with JSON mode.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer
            question_text: The question that was asked
            keyword_gaps: Potential missing keywords from keyword analysis

        Returns:
            Dict with concept gap analysis
        """
        prompt = f"""
Question: {question_text}
Ideal Answer: {ideal_answer}
Candidate Answer: {answer_text}
Potential missing keywords: {', '.join(keyword_gaps[:10])}

Analyze and identify:
1. Key concepts in ideal answer missing from candidate answer
2. Whether missing keywords represent real conceptual gaps

Return as JSON:
- "concepts": list of missing concepts
- "confirmed": boolean
- "severity": "minor" | "moderate" | "major"
"""

        system_prompt = """You are an expert technical interviewer analyzing completeness.
Identify real conceptual gaps, not just missing synonyms."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        content = self._extract_json_from_markdown(content)
        result = json.loads(content)

        return {
            "concepts": result.get("concepts", []),
            "keywords": keyword_gaps[:5],
            "confirmed": result.get("confirmed", False),
            "severity": result.get("severity", "minor"),
        }

    async def generate_followup_question(
        self,
        parent_question: str,
        answer_text: str,
        missing_concepts: list[str],
        severity: str,
        order: int,
        cumulative_gaps: list[str] | None = None,
        previous_follow_ups: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate follow-up question using Azure OpenAI with cumulative context.

        Args:
            parent_question: Original question text
            answer_text: Candidate's answer to parent question (or latest follow-up)
            missing_concepts: List of concepts missing from current answer
            severity: Gap severity
            order: Follow-up order in sequence
            cumulative_gaps: All unique gaps accumulated across follow-up cycle
            previous_follow_ups: Previous follow-up questions and answers for context

        Returns:
            Follow-up question text
        """
        # Build cumulative context if available
        cumulative_context = ""
        if cumulative_gaps and len(cumulative_gaps) > 0:
            cumulative_context = f"\nAll Missing Concepts (cumulative): {', '.join(cumulative_gaps)}"

        # Build previous follow-ups context if available
        previous_context = ""
        if previous_follow_ups and len(previous_follow_ups) > 0:
            previous_context = "\n\nPrevious Follow-ups:"
            for i, fu in enumerate(previous_follow_ups, 1):
                previous_context += f"\n  #{i}: {fu.get('question', 'N/A')}"
                previous_context += f"\n      Answer: {fu.get('answer', 'N/A')[:100]}..."

        prompt = f"""
Original Question: {parent_question}
Latest Answer: {answer_text}
Current Missing Concepts: {', '.join(missing_concepts)}
Gap Severity: {severity}{cumulative_context}{previous_context}

Generate focused follow-up question (#{order}) addressing the most critical missing concepts.
The question should:
- Be specific and concise
- Prioritize concepts: {', '.join(missing_concepts[:2])}
- Avoid repeating previous follow-up questions
- Be progressively more targeted (this is follow-up #{order} of max 3)

Return only the question text.
"""

        system_prompt = """You are an expert technical interviewer generating adaptive follow-ups.
Ask questions that probe specific missing concepts while considering the full interview context."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=150,
        )

        content = response.choices[0].message.content
        return content.strip() if content else "Can you elaborate on that?"

    async def generate_interview_recommendations(
        self,
        context: dict[str, Any],
    ) -> dict[str, list[str]]:
        """Generate personalized interview recommendations using Azure OpenAI.

        Args:
            context: Interview context including:
                - interview_id: str
                - total_answers: int
                - gap_progression: dict
                - evaluations: list[dict]

        Returns:
            Dict with strengths, weaknesses, study topics, and technique tips
        """
        evaluations = context.get("evaluations", [])
        gap_progression = context.get("gap_progression", {})

        # Build evaluation summary
        eval_summary = "\n".join(
            [
                f"- Question {i+1}: Score {e['score']:.1f}/100"
                f"\n  Strengths: {', '.join(e.get('strengths', []))}"
                f"\n  Weaknesses: {', '.join(e.get('weaknesses', []))}"
                for i, e in enumerate(evaluations)
            ]
        )

        prompt = f"""
Interview Performance Analysis

Total Questions Answered: {len(evaluations)}
Gap Progression:
- Questions with Follow-ups: {gap_progression.get('questions_with_followups', 0)}
- Gaps Filled: {gap_progression.get('gaps_filled', 0)}
- Gaps Remaining: {gap_progression.get('gaps_remaining', 0)}

Detailed Evaluations:
{eval_summary}

Generate personalized interview feedback in JSON format with these exact keys:
{{
    "strengths": ["strength 1", "strength 2", ...],  // 3-5 specific strengths
    "weaknesses": ["weakness 1", "weakness 2", ...],  // 3-5 specific weaknesses
    "study_topics": ["topic 1", "topic 2", ...],  // 3-7 specific topics to study
    "technique_tips": ["tip 1", "tip 2", ...]  // 2-5 interview technique improvements
}}

Make recommendations:
- Specific and actionable (not generic)
- Based on actual performance data
- Prioritized by impact
- Constructive and encouraging

Return ONLY valid JSON."""

        system_prompt = """You are an expert interview coach analyzing candidate performance.
Provide specific, data-driven recommendations that help candidates improve."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            # Fallback recommendations
            return {
                "strengths": ["Good technical foundation"],
                "weaknesses": ["Could provide more detail in answers"],
                "study_topics": ["Review core concepts"],
                "technique_tips": ["Practice explaining concepts clearly"],
            }

        try:
            content = self._extract_json_from_markdown(content)
            recommendations = json.loads(content)
            return recommendations
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "strengths": ["Good technical foundation"],
                "weaknesses": ["Could provide more detail in answers"],
                "study_topics": ["Review core concepts"],
                "technique_tips": ["Practice explaining concepts clearly"],
            }

