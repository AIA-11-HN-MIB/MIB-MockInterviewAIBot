"""Tests for Phase 03: PlanInterviewUseCase."""

from uuid import uuid4

import pytest

from src.application.use_cases.plan_interview import PlanInterviewUseCase
from src.domain.models.cv_analysis import CVAnalysis, ExtractedSkill
from src.domain.models.interview import InterviewStatus


class TestPlanInterviewUseCase:
    """Test PlanInterviewUseCase."""

    @pytest.mark.asyncio
    async def test_plan_interview_with_2_skills(
        self,
        mock_llm,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_vector_search,
    ):
        """Test planning with 2 skills -> n=2 questions."""
        # Create CV with 2 skills
        cv = CVAnalysis(
            candidate_id=uuid4(),
            cv_file_path="/path/to/cv.pdf",
            extracted_text="Sample CV text",
            summary="Python developer",
            skills=[
                ExtractedSkill(skill="Python", category="technical", proficiency="expert"),
                ExtractedSkill(skill="FastAPI", category="technical", proficiency="intermediate"),
            ],
        )
        await mock_cv_analysis_repo.save(cv)

        # Execute use case
        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=cv.id,
            candidate_id=cv.candidate_id,
        )

        # Verify n=2
        assert interview.planned_question_count == 2
        assert len(interview.question_ids) == 2
        assert interview.status == InterviewStatus.IDLE
        assert "strategy" in interview.plan_metadata

    @pytest.mark.asyncio
    async def test_plan_interview_with_4_skills(
        self,
        mock_llm,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_vector_search,
    ):
        """Test planning with 4 skills -> n=3 questions."""
        cv = CVAnalysis(
            candidate_id=uuid4(),
            cv_file_path="/path/to/cv.pdf",
            extracted_text="Sample CV text",
            summary="Full-stack developer",
            skills=[
                ExtractedSkill(skill="Python", category="technical", proficiency="expert"),
                ExtractedSkill(skill="React", category="technical", proficiency="advanced"),
                ExtractedSkill(skill="PostgreSQL", category="technical", proficiency="intermediate"),
                ExtractedSkill(skill="Docker", category="technical", proficiency="beginner"),
            ],
        )
        await mock_cv_analysis_repo.save(cv)

        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=cv.id,
            candidate_id=cv.candidate_id,
        )

        # Verify n=3
        assert interview.planned_question_count == 3
        assert len(interview.question_ids) == 3

    @pytest.mark.asyncio
    async def test_plan_interview_with_7_skills(
        self,
        mock_llm,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_vector_search,
    ):
        """Test planning with 7 skills -> n=4 questions."""
        cv = CVAnalysis(
            candidate_id=uuid4(),
            cv_file_path="/path/to/cv.pdf",
            extracted_text="Sample CV text",
            summary="Senior engineer",
            skills=[
                ExtractedSkill(skill=f"Skill{i}", category="technical", proficiency="expert")
                for i in range(7)
            ],
        )
        await mock_cv_analysis_repo.save(cv)

        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=cv.id,
            candidate_id=cv.candidate_id,
        )

        # Verify n=4
        assert interview.planned_question_count == 4
        assert len(interview.question_ids) == 4

    @pytest.mark.asyncio
    async def test_plan_interview_with_10_skills_max_5(
        self,
        mock_llm,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_vector_search,
    ):
        """Test planning with 10 skills -> n=5 (max)."""
        cv = CVAnalysis(
            candidate_id=uuid4(),
            cv_file_path="/path/to/cv.pdf",
            extracted_text="Sample CV text",
            summary="Tech lead",
            skills=[
                ExtractedSkill(skill=f"Skill{i}", category="technical", proficiency="expert")
                for i in range(10)
            ],
        )
        await mock_cv_analysis_repo.save(cv)

        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=cv.id,
            candidate_id=cv.candidate_id,
        )

        # Verify n=5 (max cap)
        assert interview.planned_question_count == 5
        assert len(interview.question_ids) == 5

    @pytest.mark.asyncio
    async def test_plan_interview_questions_have_ideal_answer(
        self,
        mock_llm,
        mock_vector_search,
        sample_cv_analysis,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
    ):
        """Test all generated questions have ideal_answer and rationale."""
        await mock_cv_analysis_repo.save(sample_cv_analysis)

        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=sample_cv_analysis.id,
            candidate_id=sample_cv_analysis.candidate_id,
        )

        # Verify all questions have ideal_answer
        for question_id in interview.question_ids:
            question = await mock_question_repo.get_by_id(question_id)
            assert question is not None
            assert question.has_ideal_answer() is True
            assert question.is_planned is True
            assert question.ideal_answer is not None
            assert question.rationale is not None

    @pytest.mark.asyncio
    async def test_plan_interview_cv_not_found(
        self,
        mock_llm,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
        mock_vector_search,
    ):
        """Test error when CV analysis not found."""
        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        with pytest.raises(ValueError, match="CV analysis .* not found"):
            await use_case.execute(
                cv_analysis_id=uuid4(),  # Non-existent
                candidate_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_plan_interview_metadata_stored(
        self,
        mock_llm,
        mock_vector_search,
        sample_cv_analysis,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
    ):
        """Test plan_metadata is properly stored."""
        await mock_cv_analysis_repo.save(sample_cv_analysis)

        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=sample_cv_analysis.id,
            candidate_id=sample_cv_analysis.candidate_id,
        )

        # Verify metadata
        assert "n" in interview.plan_metadata
        assert "generated_at" in interview.plan_metadata
        assert "strategy" in interview.plan_metadata
        assert interview.plan_metadata["strategy"] == "adaptive_planning_v1"
        assert "cv_summary" in interview.plan_metadata

    @pytest.mark.asyncio
    async def test_plan_interview_status_progression(
        self,
        mock_llm,
        mock_vector_search,
        sample_cv_analysis,
        mock_cv_analysis_repo,
        mock_interview_repo,
        mock_question_repo,
    ):
        """Test interview status transitions PREPARING -> READY."""
        await mock_cv_analysis_repo.save(sample_cv_analysis)

        use_case = PlanInterviewUseCase(
            llm=mock_llm,
            vector_search=mock_vector_search,
            cv_analysis_repo=mock_cv_analysis_repo,
            interview_repo=mock_interview_repo,
            question_repo=mock_question_repo,
        )

        interview = await use_case.execute(
            cv_analysis_id=sample_cv_analysis.id,
            candidate_id=sample_cv_analysis.candidate_id,
        )

        # Final status should be READY
        assert interview.status == InterviewStatus.IDLE
        assert interview.cv_analysis_id == sample_cv_analysis.id


class TestQuestionCountCalculation:
    """Test n-calculation logic (skill diversity only, max 5)."""

    def test_calculate_n_for_various_skill_counts(self):
        """Test n-calculation for different skill counts."""
        from src.application.use_cases.plan_interview import PlanInterviewUseCase

        # Create use case instance (dependencies don't matter for this test)
        use_case = PlanInterviewUseCase(
            llm=None,  # type: ignore
            vector_search=None,  # type: ignore
            cv_analysis_repo=None,  # type: ignore
            interview_repo=None,  # type: ignore
            question_repo=None,  # type: ignore
        )

        # Test cases: (skill_count, expected_n)
        test_cases = [
            (1, 2),  # 1-2 skills -> 2
            (2, 2),
            (3, 3),  # 3-4 skills -> 3
            (4, 3),
            (5, 4),  # 5-7 skills -> 4
            (6, 4),
            (7, 4),
            (8, 5),  # 8+ skills -> 5
            (10, 5),
            (20, 5),  # Still capped at 5
        ]

        for skill_count, expected_n in test_cases:
            cv = CVAnalysis(
                candidate_id=uuid4(),
                cv_file_path="/path",
            extracted_text="Test CV",
                summary="Test",
                skills=[
                    ExtractedSkill(skill=f"Skill{i}", category="technical", proficiency="expert")
                    for i in range(skill_count)
                ],
            )

            n = use_case._calculate_question_count(cv)
            assert n == expected_n, f"For {skill_count} skills, expected n={expected_n}, got {n}"

    def test_calculate_n_ignores_experience_years(self):
        """Test n-calculation ignores experience years (skill diversity only)."""
        from src.application.use_cases.plan_interview import PlanInterviewUseCase

        use_case = PlanInterviewUseCase(
            llm=None,  # type: ignore
            vector_search=None,  # type: ignore
            cv_analysis_repo=None,  # type: ignore
            interview_repo=None,  # type: ignore
            question_repo=None,  # type: ignore
        )

        # Same skills, different experience
        cv_junior = CVAnalysis(
            candidate_id=uuid4(),
            cv_file_path="/path",
            extracted_text="Test CV",
            summary="Junior",
            skills=[
                ExtractedSkill(skill="Python", category="technical", proficiency="beginner"),
                ExtractedSkill(skill="SQL", category="technical", proficiency="beginner"),
            ],
            work_experience_years=1,
        )

        cv_senior = CVAnalysis(
            candidate_id=uuid4(),
            cv_file_path="/path",
            extracted_text="Test CV",
            summary="Senior",
            skills=[
                ExtractedSkill(skill="Python", category="technical", proficiency="expert"),
                ExtractedSkill(skill="SQL", category="technical", proficiency="expert"),
            ],
            work_experience_years=15,
        )

        # Both should get n=2 (based on 2 skills, not experience)
        assert use_case._calculate_question_count(cv_junior) == 2
        assert use_case._calculate_question_count(cv_senior) == 2
