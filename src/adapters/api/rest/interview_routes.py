"""Interview REST API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.dto.interview_dto import (
    CreateInterviewRequest,
    FollowUpQuestionResponse,
    InterviewResponse,
    PlanInterviewRequest,
    PlanningStatusResponse,
    QuestionResponse,
)
from ....application.use_cases.get_next_question import GetNextQuestionUseCase
from ....application.use_cases.plan_interview import PlanInterviewUseCase
from ....application.use_cases.start_interview import StartInterviewUseCase
from ....infrastructure.config.settings import get_settings
from ....infrastructure.database.session import get_async_session
from ....infrastructure.dependency_injection.container import get_container

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new interview session",
)
async def create_interview(
    request: CreateInterviewRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Create interview session and prepare questions.

    Args:
        request: Interview creation request with candidate and CV analysis IDs
        session: Database session

    Returns:
        Interview details with WebSocket URL for real-time communication

    Raises:
        HTTPException: If CV analysis not found or validation fails
    """
    try:
        container = get_container()
        settings = get_settings()

        # Get CV analysis
        cv_analysis_repo = container.cv_analysis_repository_port(session)
        cv_analysis = await cv_analysis_repo.get_by_id(request.cv_analysis_id)
        if not cv_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CV analysis {request.cv_analysis_id} not found",
            )

        # Start interview use case
        use_case = StartInterviewUseCase(
            vector_search=container.vector_search_port(),
            question_repository=container.question_repository_port(session),
        )

        interview = await use_case.execute(
            candidate_id=request.candidate_id,
            cv_analysis=cv_analysis,
            num_questions=request.num_questions,
        )

        # Save interview
        interview_repo = container.interview_repository_port(session)
        saved_interview = await interview_repo.save(interview)

        # Return response with WebSocket URL
        base_url = settings.ws_base_url
        return InterviewResponse.from_domain(saved_interview, base_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/{interview_id}",
    response_model=InterviewResponse,
    summary="Get interview details",
)
async def get_interview(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get interview by ID.

    Args:
        interview_id: Interview UUID
        session: Database session

    Returns:
        Interview details

    Raises:
        HTTPException: If interview not found
    """
    container = get_container()
    settings = get_settings()

    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    base_url = settings.ws_base_url
    return InterviewResponse.from_domain(interview, base_url)


@router.put(
    "/{interview_id}/start",
    response_model=InterviewResponse,
    summary="Start interview (move to IN_PROGRESS)",
)
async def start_interview(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Start interview session.

    Args:
        interview_id: Interview UUID
        session: Database session

    Returns:
        Updated interview details

    Raises:
        HTTPException: If interview not found or invalid state
    """
    container = get_container()
    settings = get_settings()

    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    try:
        interview.start()
        updated = await interview_repo.update(interview)

        base_url = settings.ws_base_url
        return InterviewResponse.from_domain(updated, base_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/{interview_id}/questions/current",
    response_model=QuestionResponse,
    summary="Get current question",
)
async def get_current_question(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get current unanswered question.

    Args:
        interview_id: Interview UUID
        session: Database session

    Returns:
        Current question details

    Raises:
        HTTPException: If interview not found or no more questions
    """
    container = get_container()

    use_case = GetNextQuestionUseCase(
        interview_repository=container.interview_repository_port(session),
        question_repository=container.question_repository_port(session),
    )

    try:
        question = await use_case.execute(interview_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No more questions available",
            )

        # Get interview for context
        interview = await container.interview_repository_port(
            session
        ).get_by_id(interview_id)

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview {interview_id} not found",
            )

        return QuestionResponse(
            id=question.id,
            text=question.text,
            question_type=question.question_type.value,
            difficulty=question.difficulty.value,
            index=interview.current_question_index,
            total=len(interview.question_ids),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


# NEW: Adaptive Planning Endpoints
@router.post(
    "/plan",
    response_model=PlanningStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Plan interview with adaptive questions",
)
async def plan_interview(
    request: PlanInterviewRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Plan interview by generating n questions with ideal answers.

    This endpoint triggers the pre-planning phase:
    1. Calculates n based on skill diversity (max 5)
    2. Generates n questions with ideal_answer + rationale
    3. Returns interview with status=PREPARING (async process)

    Args:
        request: Planning request with cv_analysis_id and candidate_id
        session: Database session

    Returns:
        Planning status with interview_id

    Raises:
        HTTPException: If CV analysis not found
    """
    try:
        container = get_container()

        # Validate CV analysis exists
        cv_analysis_repo = container.cv_analysis_repository_port(session)
        cv_analysis = await cv_analysis_repo.get_by_id(request.cv_analysis_id)
        if not cv_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CV analysis {request.cv_analysis_id} not found",
            )

        # Execute planning use case
        use_case = PlanInterviewUseCase(
            llm=container.llm_port(),
            cv_analysis_repo=cv_analysis_repo,
            interview_repo=container.interview_repository_port(session),
            question_repo=container.question_repository_port(session),
        )

        interview = await use_case.execute(
            cv_analysis_id=request.cv_analysis_id,
            candidate_id=request.candidate_id,
        )

        return PlanningStatusResponse(
            interview_id=interview.id,
            status=interview.status.value,
            planned_question_count=interview.planned_question_count,
            plan_metadata=interview.plan_metadata,
            message=f"Interview planned with {interview.planned_question_count} questions",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/{interview_id}/plan",
    response_model=PlanningStatusResponse,
    summary="Get interview planning status",
)
async def get_planning_status(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get interview planning status.

    Args:
        interview_id: Interview UUID
        session: Database session

    Returns:
        Planning status details

    Raises:
        HTTPException: If interview not found
    """
    container = get_container()
    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    # Determine message based on status
    if interview.status.value == "PREPARING":
        message = "Interview planning in progress..."
    elif interview.status.value == "READY":
        message = f"Interview ready with {interview.planned_question_count} questions"
    elif interview.status.value == "IN_PROGRESS":
        message = "Interview started"
    elif interview.status.value == "COMPLETED":
        message = "Interview completed"
    else:
        message = f"Interview status: {interview.status.value}"

    return PlanningStatusResponse(
        interview_id=interview.id,
        status=interview.status.value,
        planned_question_count=interview.planned_question_count,
        plan_metadata=interview.plan_metadata,
        message=message,
    )
