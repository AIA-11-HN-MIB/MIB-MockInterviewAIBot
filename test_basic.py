"""Quick test script to verify setup."""

import asyncio
from src.domain.models import Candidate, Interview, Question, DifficultyLevel, QuestionType
from src.infrastructure.config import get_settings


async def main():
    print("=== Testing Elios AI Service Setup ===\n")

    # Test 1: Configuration
    print("1. Testing Configuration...")
    settings = get_settings()
    print(f"   ✓ App Name: {settings.app_name}")
    print(f"   ✓ Environment: {settings.environment}")
    print(f"   ✓ API Port: {settings.api_port}\n")

    # Test 2: Domain Models
    print("2. Testing Domain Models...")
    candidate = Candidate(name="Test User", email="test@example.com")
    print(f"   ✓ Created Candidate: {candidate.name} ({candidate.id})")

    interview = Interview(candidate_id=candidate.id)
    print(f"   ✓ Created Interview: {interview.id}")
    print(f"   ✓ Interview Status: {interview.status}\n")

    question = Question(
        text="What is dependency injection?",
        question_type=QuestionType.TECHNICAL,
        difficulty=DifficultyLevel.MEDIUM,
        skills=["Software Architecture"]
    )
    print(f"   ✓ Created Question: {question.text[:40]}...")
    print(f"   ✓ Question Difficulty: {question.difficulty}\n")

    # Test 3: Interview Flow
    print("3. Testing Interview Flow...")
    interview.mark_ready(candidate.id)
    print(f"   ✓ Interview marked ready")

    interview.start()
    print(f"   ✓ Interview started: {interview.status}")

    interview.add_question(question.id)
    print(f"   ✓ Added question to interview")
    print(f"   ✓ Progress: {interview.get_progress_percentage()}%\n")

    print("=== All Tests Passed! ===")
    print("\nYou can now start the server:")
    print("  python src/main.py")
    print("\nThen visit:")
    print("  http://localhost:8000")
    print("  http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
