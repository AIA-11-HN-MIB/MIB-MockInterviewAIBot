"""OpenAI LLM adapter implementation."""

import json
from typing import Dict, Any, List
from uuid import UUID

from openai import AsyncOpenAI

from ...domain.ports.llm_port import LLMPort
from ...domain.models.question import Question
from ...domain.models.answer import AnswerEvaluation


class OpenAIAdapter(LLMPort):
    """OpenAI implementation of LLM port.

    This adapter encapsulates all OpenAI-specific logic, making it easy
    to swap for another LLM provider without touching domain logic.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ):
        """Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
            temperature: Sampling temperature (default: 0.7)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def generate_question(
        self,
        context: Dict[str, Any],
        skill: str,
        difficulty: str,
    ) -> str:
        """Generate an interview question using OpenAI.

        Args:
            context: Interview context
            skill: Target skill to test
            difficulty: Question difficulty level

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

        Return only the question text, no additional explanation.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
        )

        return response.choices[0].message.content.strip()

    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        context: Dict[str, Any],
    ) -> AnswerEvaluation:
        """Evaluate an answer using OpenAI.

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

        {"Reference Answer: " + question.reference_answer if question.reference_answer else ""}

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

        result = json.loads(response.choices[0].message.content)

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
        questions: List[Question],
        answers: List[Dict[str, Any]],
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

        return response.choices[0].message.content

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

        return response.choices[0].message.content.strip()

    async def extract_skills_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract skills from CV text using OpenAI.

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

        result = json.loads(response.choices[0].message.content)
        return result.get("skills", [])
