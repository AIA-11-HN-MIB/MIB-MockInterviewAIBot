# Phase 4: Unified CV Upload API Endpoint

**Date**: 2025-11-11
**Status**: Pending
**Priority**: Medium
**Implementation Status**: Not Started
**Review Status**: Pending

## Context

**Parent Plan**: [Refactor Plan Interview Flow](./plan.md)
**Previous Phase**: [Phase 3: Vector Search Integration](./phase-03-vector-search-integration.md)
**Next Phase**: Phase 5: Testing & Documentation
**Related Docs**:
- [Interview Routes](../../src/adapters/api/rest/interview_routes.py)
- [Sequence Diagram Requirements](../README.md)

## Overview

Create unified API endpoint for CV upload + analysis + interview planning. Align with sequence diagram requirement: single POST /interview/cv endpoint that handles full flow from CV file to READY interview.

**Duration**: 2 days
**Estimated Completion**: 2025-11-18

## Key Insights

### Current API Design

**Existing Endpoints**:
```
POST /api/interviews/plan
- Input: cv_analysis_id, candidate_id
- Output: Interview (status=READY)
- Assumes CV already analyzed

GET /api/interviews/{id}
- Get interview details

PUT /api/interviews/{id}/start
- Start interview (READY → IN_PROGRESS)

GET /api/interviews/{id}/questions/current
- Get current question
```

**Gap**: No single endpoint for CV upload → analysis → planning flow.

### New Unified Endpoint Design

**POST /api/interview/cv**

**Request** (multipart/form-data):
```json
{
  "file": <cv_file>,  // PDF, DOC, DOCX
  "candidate_id": "uuid",
  "options": {
    "auto_start": false,  // Optional: auto-start interview
    "question_count": null  // Optional: override n calculation
  }
}
```

**Response** (202 Accepted):
```json
{
  "interview_id": "uuid",
  "status": "READY",
  "cv_analysis_id": "uuid",
  "planned_question_count": 5,
  "plan_metadata": {
    "n": 5,
    "generated_at": "2025-11-11T10:30:00Z",
    "strategy": "adaptive_planning_v1",
    "cv_summary": "3 years Python experience..."
  },
  "message": "Interview planned with 5 questions",
  "ws_url": "ws://localhost:8000/ws/interviews/{interview_id}"
}
```

**Workflow**:
1. Validate CV file format (PDF/DOC/DOCX)
2. Save CV file to storage
3. Analyze CV (CVAnalyzerPort)
4. Plan interview (PlanInterviewUseCase with vector search)
5. Return interview details

### Alternative: Keep Existing Endpoint

**Option**: Enhance existing `/api/interviews/plan` to accept CV file.

**Pros**: Less disruption, incremental change
**Cons**: Deviates from sequence diagram requirement

**Recommendation**: Create new `/interview/cv` endpoint (matches diagram).

## Requirements

### Functional Requirements

1. **File Upload Handling**
   - Accept multipart/form-data
   - Validate file format (PDF, DOC, DOCX)
   - Validate file size (max 10MB)
   - Save file to storage directory

2. **CV Analysis Integration**
   - Call CVAnalyzerPort.analyze_cv()
   - Handle analysis failures gracefully
   - Store CVAnalysis in repository

3. **Interview Planning Integration**
   - Call PlanInterviewUseCase.execute()
   - Pass cv_analysis_id and candidate_id
   - Handle planning failures with rollback

4. **Response Format**
   - Return 202 Accepted (async processing complete)
   - Include interview_id, status, metadata
   - Include WebSocket URL for real-time interview

5. **Error Handling**
   - 400 Bad Request: Invalid file format
   - 413 Payload Too Large: File exceeds size limit
   - 500 Internal Server Error: CV analysis or planning failure
   - Cleanup: Delete uploaded file on error

### Non-Functional Requirements

1. **Performance**
   - File upload: <5 seconds for 5MB file
   - CV analysis: <30 seconds
   - Interview planning: <30 seconds
   - Total: <90 seconds end-to-end

2. **Security**
   - Validate file content type (not just extension)
   - Scan for malware (future)
   - Store files outside web root
   - Generate unique filenames (prevent overwrite)

3. **Testability**
   - Unit tests with mock file uploads
   - Integration tests with real CV files
   - Test error scenarios

## Architecture

### Endpoint Implementation

**File**: `src/adapters/api/rest/interview_routes.py`

```python
from fastapi import File, UploadFile, Form
from typing import Optional
import uuid
import shutil
from pathlib import Path

@router.post(
    "/cv",
    response_model=UnifiedPlanningResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload CV and plan interview",
)
async def upload_cv_and_plan_interview(
    file: UploadFile = File(...),
    candidate_id: UUID = Form(...),
    auto_start: bool = Form(False),
    question_count: Optional[int] = Form(None),
    session: AsyncSession = Depends(get_async_session),
):
    """Upload CV, analyze, and plan interview in one request.

    This endpoint combines:
    1. CV file upload and validation
    2. CV analysis (skill extraction, summary)
    3. Interview planning (question generation with exemplars)

    Args:
        file: CV file (PDF, DOC, DOCX)
        candidate_id: Candidate UUID
        auto_start: If true, start interview immediately (status=IN_PROGRESS)
        question_count: Optional override for n questions (default: calculated from CV)
        session: Database session

    Returns:
        Interview details with status=READY (or IN_PROGRESS if auto_start=true)

    Raises:
        HTTPException: 400 (invalid file), 413 (too large), 500 (processing error)
    """
    container = get_container()
    settings = get_settings()

    # Step 1: Validate file
    if file.content_type not in ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Must be PDF, DOC, or DOCX."
        )

    # Check file size (10MB limit)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size: 10MB."
        )

    # Step 2: Save file
    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved CV file: {file_path}")

        # Step 3: Analyze CV
        cv_analyzer = container.cv_analyzer_port()
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path=str(file_path),
            candidate_id=str(candidate_id),
        )

        # Store CV analysis
        cv_analysis_repo = container.cv_analysis_repository_port(session)
        await cv_analysis_repo.save(cv_analysis)

        logger.info(f"CV analyzed: {cv_analysis.id}")

        # Step 4: Plan interview with vector search
        use_case = PlanInterviewUseCase(
            llm=container.llm_port(),
            vector_search=container.vector_search_port(),
            cv_analysis_repo=cv_analysis_repo,
            interview_repo=container.interview_repository_port(session),
            question_repo=container.question_repository_port(session),
        )

        interview = await use_case.execute(
            cv_analysis_id=cv_analysis.id,
            candidate_id=candidate_id,
        )

        logger.info(f"Interview planned: {interview.id}")

        # Step 5: Auto-start if requested
        if auto_start:
            interview.start()
            await container.interview_repository_port(session).update(interview)
            logger.info(f"Interview auto-started: {interview.id}")

        # Step 6: Build response
        ws_url = f"{settings.ws_base_url}/interviews/{interview.id}"

        return UnifiedPlanningResponse(
            interview_id=interview.id,
            status=interview.status.value,
            cv_analysis_id=cv_analysis.id,
            planned_question_count=interview.planned_question_count,
            plan_metadata=interview.plan_metadata,
            message=f"Interview {'started' if auto_start else 'ready'} with {interview.planned_question_count} questions",
            ws_url=ws_url,
        )

    except Exception as e:
        # Cleanup on error
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Failed to process CV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CV: {str(e)}"
        ) from e
```

### Response DTO

**File**: `src/application/dto/interview_dto.py`

```python
class UnifiedPlanningResponse(BaseModel):
    """Response for unified CV upload + planning endpoint."""

    interview_id: UUID
    status: str  # READY or IN_PROGRESS
    cv_analysis_id: UUID
    planned_question_count: int
    plan_metadata: dict[str, Any]
    message: str
    ws_url: str  # WebSocket URL for real-time interview

    class Config:
        json_schema_extra = {
            "example": {
                "interview_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "READY",
                "cv_analysis_id": "660e8400-e29b-41d4-a716-446655440001",
                "planned_question_count": 5,
                "plan_metadata": {
                    "n": 5,
                    "generated_at": "2025-11-11T10:30:00Z",
                    "strategy": "adaptive_planning_v1",
                    "cv_summary": "3 years Python experience..."
                },
                "message": "Interview ready with 5 questions",
                "ws_url": "ws://localhost:8000/ws/interviews/550e8400-e29b-41d4-a716-446655440000"
            }
        }
```

### File Storage Configuration

**File**: `src/infrastructure/config/settings.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # File Storage
    upload_directory: str = "./uploads"  # CV file storage
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
```

## Related Code Files

**API Layer**:
- `src/adapters/api/rest/interview_routes.py` (MODIFY - add new endpoint)

**DTOs**:
- `src/application/dto/interview_dto.py` (MODIFY - add UnifiedPlanningResponse)

**Use Cases** (USE):
- `src/application/use_cases/plan_interview.py` (USE from Phase 3)

**Adapters** (USE):
- `src/adapters/cv_processing/cv_processing_adapter.py` (USE)
- `src/adapters/mock/mock_cv_analyzer.py` (USE for tests)

**Infrastructure**:
- `src/infrastructure/config/settings.py` (MODIFY - add upload settings)

**Tests** (CREATE):
- `tests/unit/api/test_interview_routes.py` (MODIFY)
- `tests/integration/test_cv_upload_flow.py` (NEW)

## Implementation Steps

### Step 1: Update Settings
**File**: `src/infrastructure/config/settings.py`

- [ ] Add `upload_directory: str = "./uploads"`
- [ ] Add `max_upload_size: int = 10 * 1024 * 1024`
- [ ] Update docstring
- [ ] Commit: `feat(config): add file upload settings`

### Step 2: Create Response DTO
**File**: `src/application/dto/interview_dto.py`

- [ ] Create `UnifiedPlanningResponse` class
- [ ] Add all required fields
- [ ] Add example in Config
- [ ] Commit: `feat(dto): add UnifiedPlanningResponse`

### Step 3: Implement Endpoint
**File**: `src/adapters/api/rest/interview_routes.py`

- [ ] Create `upload_cv_and_plan_interview()` function
- [ ] Add file upload parameter (UploadFile)
- [ ] Add form parameters (candidate_id, auto_start, question_count)
- [ ] Validate file type and size
- [ ] Save file to upload directory
- [ ] Call CVAnalyzerPort
- [ ] Call PlanInterviewUseCase
- [ ] Handle auto_start option
- [ ] Build response
- [ ] Add error handling with cleanup
- [ ] Add logging
- [ ] Commit: `feat(api): add unified CV upload and planning endpoint`

### Step 4: Create Upload Directory
- [ ] Create `./uploads` directory (gitignored)
- [ ] Add to .gitignore: `uploads/`
- [ ] Document in README
- [ ] Commit: `chore: add uploads directory to gitignore`

### Step 5: Update API Documentation
- [ ] Add endpoint to OpenAPI docs (automatic via FastAPI)
- [ ] Test with Swagger UI: http://localhost:8000/docs
- [ ] Verify request/response schemas
- [ ] Test file upload in Swagger
- [ ] Commit: `docs: document unified CV upload endpoint`

### Step 6: Unit Tests
**File**: `tests/unit/api/test_interview_routes.py`

**Test Cases**:
- [ ] Test successful CV upload + planning
- [ ] Test invalid file type (400)
- [ ] Test file too large (413)
- [ ] Test missing candidate_id (422)
- [ ] Test auto_start option
- [ ] Test CV analysis failure (500)
- [ ] Test planning failure with rollback
- [ ] Mock file upload (use TestClient)
- [ ] Mock CVAnalyzer and PlanInterviewUseCase
- [ ] Verify file cleanup on error
- [ ] Run tests: `pytest tests/unit/api/ -v`
- [ ] Commit: `test(api): add unit tests for CV upload endpoint`

### Step 7: Integration Tests
**File**: `tests/integration/test_cv_upload_flow.py`

- [ ] Test with real CV file (sample PDF)
- [ ] Test with MockCVAnalyzer and MockLLM
- [ ] Test end-to-end flow
- [ ] Verify interview created in database
- [ ] Verify CV analysis stored
- [ ] Verify questions generated
- [ ] Verify embeddings stored (if vector DB available)
- [ ] Measure end-to-end latency
- [ ] Commit: `test(api): add integration tests for CV upload flow`

### Step 8: Error Handling & Cleanup
- [ ] Ensure file deleted on any error
- [ ] Test rollback scenarios
- [ ] Add detailed error messages
- [ ] Add request ID for tracing
- [ ] Commit: `feat(api): enhance error handling for CV upload`

### Step 9: Documentation
- [ ] Update README with new endpoint
- [ ] Add example curl command
- [ ] Document request/response format
- [ ] Add troubleshooting section
- [ ] Commit: `docs: document unified CV upload endpoint usage`

## Todo List

- [ ] Update settings with upload configuration
- [ ] Create UnifiedPlanningResponse DTO
- [ ] Implement unified endpoint
- [ ] Create upload directory and gitignore
- [ ] Update API documentation
- [ ] Create comprehensive unit tests
- [ ] Run integration tests
- [ ] Enhance error handling and cleanup
- [ ] Update documentation
- [ ] Code review and approval
- [ ] Merge to main branch

## Success Criteria

- [ ] Unified endpoint accepts CV file upload
- [ ] CV analyzed and stored successfully
- [ ] Interview planned with vector search
- [ ] Response includes all required fields
- [ ] All unit tests pass
- [ ] Integration tests verify end-to-end flow
- [ ] Error handling and cleanup working
- [ ] API documentation complete
- [ ] Code review approved

## Risk Assessment

### Technical Risks

**Risk**: Large CV files cause timeout
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: 10MB file size limit, async processing
- **Target**: <90 seconds end-to-end

**Risk**: File upload consumes excessive disk space
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: Implement file cleanup job (future)
- **Monitoring**: Track upload directory size

**Risk**: Malicious file upload (security)
- **Likelihood**: Medium
- **Impact**: High
- **Mitigation**: File type validation, future malware scanning
- **Protection**: Store outside web root

### Implementation Risks

**Risk**: Complex endpoint difficult to test
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**: Comprehensive unit tests with mocks
- **Strategy**: Test each step independently

**Risk**: Breaking existing API contracts
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: New endpoint (no changes to existing)
- **Validation**: Run full API test suite

## Security Considerations

### File Upload Security
- Validate content type (not just extension)
- **Action**: Check file magic bytes
- **Protection**: Reject non-PDF/DOC/DOCX files

### Path Traversal
- User-provided filenames may contain "../"
- **Action**: Generate unique filenames (UUID)
- **Protection**: Never use user-provided paths directly

### Disk Space Exhaustion
- Unlimited uploads may fill disk
- **Action**: File size limits (10MB)
- **Future**: Implement cleanup job, storage quotas

### Data Privacy
- CV files contain PII
- **Action**: Encrypt at rest (future)
- **Compliance**: GDPR right to deletion

## Next Steps

1. **Begin Implementation**: Update settings and create DTO
2. **Parallel Work**: Endpoint implementation and tests
3. **Testing**: Comprehensive unit and integration tests
4. **Security Review**: File upload security audit
5. **Code Review**: Team review of API endpoint
6. **Merge**: Merge after approval
7. **Phase 5**: Begin comprehensive testing and documentation

## Unresolved Questions

1. **File Retention**: How long to keep uploaded CV files?
2. **Cleanup Strategy**: Periodic cleanup job or delete after analysis?
3. **Storage Backend**: Local filesystem or cloud storage (S3, GCS)?
4. **Async Processing**: Should CV analysis be async with polling endpoint?
5. **Rate Limiting**: Limit CV uploads per user/IP?
6. **Virus Scanning**: Integrate malware scanner (ClamAV)?

---

**Document Status**: Draft
**Next Review**: Before implementation
**Dependencies**: Phase 3 complete (Vector Search Integration)
**Blocks**: Phase 5 (Testing & Documentation)
