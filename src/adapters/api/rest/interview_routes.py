"""Interview REST API endpoints."""

import os
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.dto.interview_dto import (
    InterviewResponse,
    InterviewSummaryResponse,
    PlanInterviewRequest,
    PlanningStatusResponse,
    QuestionResponse,
)
from ....application.use_cases.get_next_question import GetNextQuestionUseCase
from ....application.use_cases.plan_interview import PlanInterviewUseCase
from ....application.use_cases.analyze_cv import AnalyzeCVUseCase
from ....domain.models.interview import InterviewStatus
from ....infrastructure.config.settings import get_settings
from ....infrastructure.database.session import get_async_session
from ....infrastructure.dependency_injection.container import get_container
from ....infrastructure.config.settings import get_settings

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post(
    "/cv/upload",
    summary="Upload CV for further analyze"
)
async def upload_cv(
    file: UploadFile = File(..., description="PDF CV file"),
    session: AsyncSession = Depends(get_async_session),
    ):
    """
    Upload a CV file to the server.

    This endpoint accepts a PDF file and saves it to the server.
    Returns the file path where the CV is stored.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF")

    try:
        # Generate a unique filename
        setting = get_settings()
        UPLOAD_DIR = setting.upload_dir
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        candidate_id = uuid.uuid4()
        container = get_container()
        cv_analyzer = container.cv_analyzer_port()

        cv_analysis_use_case = AnalyzeCVUseCase(
            cv_analyzer=cv_analyzer,
            vector_search=container.vector_search_port(),
            candidate_repository_port=container.contcandidate_repository_port(session),
            cv_analysis_repository_port=container.cv_analysis_repository_port(session),
        )
        cv_analysis = await cv_analysis_use_case.execute(file_path, candidate_id)
        return cv_analysis

    except Exception as e:
        # Clean up the file if there was an error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

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
            # vector_search=container.vector_search_port(),
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
    if interview.status == InterviewStatus.IDLE:
        message = f"Interview ready with {interview.planned_question_count} questions"
    elif interview.status == InterviewStatus.QUESTIONING or interview.status == InterviewStatus.EVALUATING:
        message = "Interview started"
    elif interview.status == InterviewStatus.COMPLETE:
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


@router.get(
    "/{interview_id}/summary",
    response_model=InterviewSummaryResponse,
    summary="Get interview completion summary",
)
async def get_interview_summary(
    interview_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get comprehensive interview summary.

    This endpoint retrieves the cached summary generated during interview completion.
    Use case: Client reconnects after WebSocket disconnect and needs to retrieve summary.

    Args:
        interview_id: Interview UUID
        session: Database session

    Returns:
        Interview summary with all metrics, recommendations, and analysis

    Raises:
        HTTPException:
            - 404: Interview not found
            - 400: Interview not completed
            - 404: Summary not generated
    """
    container = get_container()
    interview_repo = container.interview_repository_port(session)
    interview = await interview_repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    if interview.status != InterviewStatus.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview not completed (status: {interview.status.value})",
        )

    # Extract summary from metadata
    summary = (
        interview.plan_metadata.get("completion_summary")
        if interview.plan_metadata
        else None
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found (interview completed without summary generation)",
        )

    return InterviewSummaryResponse(**summary)
