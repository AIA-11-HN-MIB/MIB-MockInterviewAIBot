"""Pytest configuration and fixtures."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.domain.models.answer import Answer, AnswerEvaluation
from src.domain.models.cv_analysis import CVAnalysis, ExtractedSkill
from src.domain.models.follow_up_question import FollowUpQuestion
from src.domain.models.interview import Interview, InterviewStatus
from src.domain.models.question import DifficultyLevel, Question, QuestionType


@pytest.fixture
def sample_cv_analysis() -> CVAnalysis:
    """Sample CV analysis for testing."""
    return CVAnalysis(
        candidate_id=uuid4(),
        cv_file_path="/path/to/cv.pdf",
        extracted_text="Sample CV text with Python, FastAPI, PostgreSQL, and Docker experience",
        summary="Experienced Python developer with 5 years of experience",
        skills=[
            ExtractedSkill(skill="Python", category="technical", proficiency="expert"),
            ExtractedSkill(skill="FastAPI", category="technical", proficiency="intermediate"),
            ExtractedSkill(skill="PostgreSQL", category="technical", proficiency="intermediate"),
            ExtractedSkill(skill="Docker", category="technical", proficiency="beginner"),
        ],
        work_experience_years=5,
        education_level="Bachelor's Degree",
    )


@pytest.fixture
def sample_question_with_ideal_answer() -> Question:
    """Sample question with ideal answer for adaptive testing."""
    return Question(
        text="Explain the concept of recursion in programming",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.MEDIUM,
        skills=["Python", "Algorithms"],
        ideal_answer="""Recursion is a programming technique where a function calls itself
        to solve a problem by breaking it down into smaller subproblems. Key concepts include:
        1) Base case: A condition that stops the recursion
        2) Recursive case: The function calling itself with modified parameters
        3) Stack management: Each call is added to the call stack
        Example: Fibonacci sequence, factorial calculation, tree traversal""",
        rationale="""This answer demonstrates mastery by covering the fundamental concepts
        (base case, recursive case), explaining the mechanism (call stack), and providing
        concrete examples. A weaker answer would miss these comprehensive details.""",
    )


@pytest.fixture
def sample_question_without_ideal_answer() -> Question:
    """Sample question without ideal answer (legacy mode)."""
    return Question(
        text="Tell me about a challenging project you worked on",
        question_type=QuestionType.BEHAVIORAL,
        difficulty=DifficultyLevel.EASY,
        skills=["Communication"],
    )


@pytest.fixture
def sample_interview_adaptive(sample_cv_analysis: CVAnalysis) -> Interview:
    """Sample adaptive interview with plan_metadata."""
    interview = Interview(
        candidate_id=sample_cv_analysis.candidate_id,
        status=InterviewStatus.READY,
        cv_analysis_id=sample_cv_analysis.id,
    )
    interview.plan_metadata = {
        "n": 3,
        "generated_at": datetime.utcnow().isoformat(),
        "strategy": "adaptive_planning_v1",
        "cv_summary": sample_cv_analysis.summary,
    }
    interview.question_ids = [uuid4(), uuid4(), uuid4()]
    # Start interview to set status to IN_PROGRESS
    interview.start()
    return interview


@pytest.fixture
def sample_interview_legacy() -> Interview:
    """Sample legacy interview without plan_metadata."""
    return Interview(
        candidate_id=uuid4(),
        status=InterviewStatus.IN_PROGRESS,
    )


@pytest.fixture
def sample_answer_high_similarity(sample_question_with_ideal_answer: Question) -> Answer:
    """Sample answer with high similarity (>= 80%)."""
    answer = Answer(
        interview_id=uuid4(),
        question_id=sample_question_with_ideal_answer.id,
        candidate_id=uuid4(),
        text="""Recursion is when a function calls itself to solve problems.
        It needs a base case to stop and a recursive case to continue.
        The call stack tracks each call. Examples include factorial and Fibonacci.""",
        is_voice=False,
        similarity_score=0.85,
        gaps={"concepts": [], "keywords": [], "confirmed": False},
    )
    answer.evaluate(
        AnswerEvaluation(
            score=85.0,
            semantic_similarity=0.85,
            completeness=0.9,
            relevance=0.95,
            sentiment="confident",
            reasoning="Strong answer covering key concepts",
            strengths=["Clear explanation", "Good examples"],
            weaknesses=["Could add more detail on stack management"],
            improvement_suggestions=["Explain stack overflow scenarios"],
        )
    )
    return answer


@pytest.fixture
def sample_answer_low_similarity(sample_question_with_ideal_answer: Question) -> Answer:
    """Sample answer with low similarity (< 80%) - should trigger follow-up."""
    answer = Answer(
        interview_id=uuid4(),
        question_id=sample_question_with_ideal_answer.id,
        candidate_id=uuid4(),
        text="Recursion is a function that calls itself.",
        is_voice=False,
        similarity_score=0.45,
        gaps={
            "concepts": ["base case", "recursive case", "call stack"],
            "keywords": ["base", "stack", "parameters"],
            "confirmed": True,
            "severity": "major",
        },
    )
    answer.evaluate(
        AnswerEvaluation(
            score=55.0,
            semantic_similarity=0.45,
            completeness=0.4,
            relevance=0.8,
            sentiment="uncertain",
            reasoning="Answer is too brief and missing key concepts",
            strengths=["Correct basic definition"],
            weaknesses=["Missing base case", "No examples", "Lacks depth"],
            improvement_suggestions=[
                "Explain base case and recursive case",
                "Provide examples",
                "Discuss call stack",
            ],
        )
    )
    return answer


@pytest.fixture
def sample_follow_up_question(sample_question_with_ideal_answer: Question) -> FollowUpQuestion:
    """Sample follow-up question."""
    return FollowUpQuestion(
        parent_question_id=sample_question_with_ideal_answer.id,
        interview_id=uuid4(),
        text="Can you explain what a base case is in recursion and why it's important?",
        generated_reason="Missing concepts: base case, termination condition",
        order_in_sequence=1,
    )


# Mock repository fixtures
class MockQuestionRepository:
    """Mock question repository for testing."""

    def __init__(self) -> None:
        self.questions: dict[UUID, Question] = {}

    async def save(self, question: Question | FollowUpQuestion) -> Question | FollowUpQuestion:
        self.questions[question.id] = question  # type: ignore
        return question

    async def get_by_id(self, question_id: UUID) -> Question | None:
        return self.questions.get(question_id)  # type: ignore


class MockInterviewRepository:
    """Mock interview repository for testing."""

    def __init__(self) -> None:
        self.interviews: dict[UUID, Interview] = {}

    async def save(self, interview: Interview) -> Interview:
        self.interviews[interview.id] = interview
        return interview

    async def update(self, interview: Interview) -> Interview:
        self.interviews[interview.id] = interview
        return interview

    async def get_by_id(self, interview_id: UUID) -> Interview | None:
        return self.interviews.get(interview_id)


class MockAnswerRepository:
    """Mock answer repository for testing."""

    def __init__(self) -> None:
        self.answers: dict[UUID, Answer] = {}

    async def save(self, answer: Answer) -> Answer:
        self.answers[answer.id] = answer
        return answer

    async def get_by_interview_id(self, interview_id: UUID) -> list[Answer]:
        return [a for a in self.answers.values() if a.interview_id == interview_id]


class MockCVAnalysisRepository:
    """Mock CV analysis repository for testing."""

    def __init__(self) -> None:
        self.analyses: dict[UUID, CVAnalysis] = {}

    async def save(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        self.analyses[cv_analysis.id] = cv_analysis
        return cv_analysis

    async def get_by_id(self, cv_analysis_id: UUID) -> CVAnalysis | None:
        return self.analyses.get(cv_analysis_id)


class MockVectorSearch:
    """Mock vector search for testing."""

    async def get_embedding(self, text: str) -> list[float]:
        """Return mock embedding."""
        # Simple hash-based mock embedding
        hash_val = hash(text.lower()[:50])
        return [float((hash_val >> i) & 1) for i in range(128)]

    async def find_similar_questions(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return mock similar questions."""
        # Return empty list by default (simulating empty vector DB)
        # Tests can override this behavior
        return []

    async def store_question_embedding(
        self,
        question_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Mock embedding storage (no-op)."""
        pass

    async def find_similar_answers(
        self,
        answer_embedding: list[float],
        reference_embeddings: list[list[float]],
    ) -> float:
        """Return mock similarity score based on text length."""
        # Simple mock: longer answers get higher similarity
        return 0.85 if len(answer_embedding) > 100 else 0.45


class MockLLM:
    """Mock LLM for testing."""

    async def evaluate_answer(
        self, question: Question, answer_text: str, context: dict[str, Any]
    ) -> AnswerEvaluation:
        """Return mock evaluation."""
        score = 85.0 if len(answer_text) > 50 else 55.0
        return AnswerEvaluation(
            score=score,
            semantic_similarity=score / 100,
            completeness=score / 100,
            relevance=0.9,
            sentiment="confident" if score > 70 else "uncertain",
            reasoning="Mock evaluation",
            strengths=["Good understanding"],
            weaknesses=["Could be more detailed"],
            improvement_suggestions=["Add examples"],
        )

    async def generate_question(
        self, context: dict[str, Any], skill: str, difficulty: str, exemplars: list[dict[str, Any]] | None = None
    ) -> str:
        """Return mock question."""
        base = f"Mock question about {skill} at {difficulty} level"
        if exemplars:
            base += f" [with {len(exemplars)} exemplars]"
        return base

    async def generate_ideal_answer(
        self, question_text: str, context: dict[str, Any]
    ) -> str:
        """Return mock ideal answer."""
        return f"Mock ideal answer for: {question_text[:50]}..."

    async def generate_rationale(
        self, question_text: str, ideal_answer: str
    ) -> str:
        """Return mock rationale."""
        return "Mock rationale explaining why this is an ideal answer"

    async def detect_concept_gaps(
        self,
        answer_text: str,
        ideal_answer: str,
        question_text: str,
        keyword_gaps: list[str],
    ) -> dict[str, Any]:
        """Mock gap detection based on answer length."""
        # Simple heuristic: short answers have gaps
        word_count = len(answer_text.split())

        if word_count < 30:
            # Simulate gaps for short answers
            return {
                "concepts": keyword_gaps[:2] if keyword_gaps else ["depth", "examples"],
                "keywords": keyword_gaps[:5],
                "confirmed": True,
                "severity": "moderate",
            }
        else:
            # Good answer, no gaps
            return {
                "concepts": [],
                "keywords": [],
                "confirmed": False,
                "severity": "minor",
            }

    async def generate_followup_question(
        self,
        parent_question: str,
        answer_text: str,
        missing_concepts: list[str],
        severity: str,
        order: int,
    ) -> str:
        """Mock follow-up question generation."""
        concepts_str = ', '.join(missing_concepts[:2]) if missing_concepts else "that concept"
        return f"Can you elaborate more on {concepts_str}? Please provide specific examples."


@pytest.fixture
def mock_question_repo() -> MockQuestionRepository:
    """Mock question repository fixture."""
    return MockQuestionRepository()


@pytest.fixture
def mock_interview_repo() -> MockInterviewRepository:
    """Mock interview repository fixture."""
    return MockInterviewRepository()


@pytest.fixture
def mock_answer_repo() -> MockAnswerRepository:
    """Mock answer repository fixture."""
    return MockAnswerRepository()


@pytest.fixture
def mock_cv_analysis_repo() -> MockCVAnalysisRepository:
    """Mock CV analysis repository fixture."""
    return MockCVAnalysisRepository()


@pytest.fixture
def mock_vector_search() -> MockVectorSearch:
    """Mock vector search fixture."""
    return MockVectorSearch()


@pytest.fixture
def mock_llm() -> MockLLM:
    """Mock LLM fixture."""
    return MockLLM()
