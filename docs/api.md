# API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://api.elios-interview.com
```

## API Prefix

All endpoints are prefixed with `/api/v1`

## Authentication

**Note**: Authentication to be implemented. Currently planned:

```http
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### 1. Health Check

#### `GET /health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## CV Management

### 2. Upload CV

#### `POST /api/v1/cv/upload`

Upload a candidate's CV for analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  ```
  cv_file: <file> (PDF, DOC, DOCX)
  candidate_id: <uuid>
  ```

**Response (202 Accepted):**
```json
{
  "cv_analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_id": "650e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "CV analysis started"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file format or missing fields
- `413 Payload Too Large`: File exceeds size limit (10MB)

---

### 3. Get CV Analysis

#### `GET /api/v1/cv/{cv_analysis_id}`

Retrieve CV analysis results.

**Path Parameters:**
- `cv_analysis_id`: UUID of the CV analysis

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_id": "650e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "summary": "Experienced Python developer with 5+ years...",
  "skills": [
    {
      "name": "Python",
      "category": "technical",
      "proficiency_level": "expert",
      "years_of_experience": 5.0,
      "mentioned_count": 12
    },
    {
      "name": "FastAPI",
      "category": "technical",
      "proficiency_level": "intermediate",
      "years_of_experience": 2.0,
      "mentioned_count": 4
    }
  ],
  "work_experience_years": 5.5,
  "education_level": "Bachelor's",
  "suggested_topics": [
    "Python Programming",
    "API Development",
    "Database Design",
    "Testing"
  ],
  "suggested_difficulty": "medium",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: CV analysis not found
- `202 Accepted`: Analysis still in progress

---

## Interview Management

### 4. Create Interview

#### `POST /api/v1/interviews`

Create a new interview session.

**Request Body:**
```json
{
  "candidate_id": "650e8400-e29b-41d4-a716-446655440000",
  "cv_analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "num_questions": 10
}
```

**Response (201 Created):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "candidate_id": "650e8400-e29b-41d4-a716-446655440000",
  "status": "ready",
  "cv_analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_count": 10,
  "current_question_index": 0,
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request body or CV analysis not found
- `404 Not Found`: Candidate not found

---

### 5. Start Interview

#### `POST /api/v1/interviews/{interview_id}/start`

Start an interview session.

**Path Parameters:**
- `interview_id`: UUID of the interview

**Response (200 OK):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "started_at": "2024-01-15T10:40:00Z",
  "first_question": {
    "id": "850e8400-e29b-41d4-a716-446655440000",
    "text": "Can you explain the difference between async and sync programming in Python?",
    "question_type": "technical",
    "difficulty": "medium",
    "audio_url": "/api/v1/audio/questions/850e8400-e29b-41d4-a716-446655440000.mp3"
  }
}
```

**Error Responses:**
- `404 Not Found`: Interview not found
- `400 Bad Request`: Interview not in ready state

---

### 6. Get Current Question

#### `GET /api/v1/interviews/{interview_id}/current-question`

Get the current question for an active interview.

**Path Parameters:**
- `interview_id`: UUID of the interview

**Response (200 OK):**
```json
{
  "id": "850e8400-e29b-41d4-a716-446655440000",
  "text": "Can you explain the difference between async and sync programming in Python?",
  "question_type": "technical",
  "difficulty": "medium",
  "skills": ["Python", "Async Programming"],
  "tags": ["concurrency", "performance"],
  "question_number": 1,
  "total_questions": 10,
  "audio_url": "/api/v1/audio/questions/850e8400-e29b-41d4-a716-446655440000.mp3"
}
```

**Error Responses:**
- `404 Not Found`: Interview not found or no questions remaining
- `400 Bad Request`: Interview not in progress

---

### 7. Submit Answer

#### `POST /api/v1/interviews/{interview_id}/answers`

Submit an answer to the current question.

**Path Parameters:**
- `interview_id`: UUID of the interview

**Request Body (Text Answer):**
```json
{
  "question_id": "850e8400-e29b-41d4-a716-446655440000",
  "text": "Async programming allows concurrent execution without blocking...",
  "is_voice": false
}
```

**Request Body (Voice Answer):**
```json
{
  "question_id": "850e8400-e29b-41d4-a716-446655440000",
  "audio_data": "<base64_encoded_audio>",
  "is_voice": true
}
```

**Response (200 OK):**
```json
{
  "answer_id": "950e8400-e29b-41d4-a716-446655440000",
  "evaluation": {
    "score": 85.0,
    "completeness": 0.9,
    "relevance": 0.95,
    "semantic_similarity": 0.88,
    "sentiment": "confident",
    "reasoning": "Good explanation with clear examples. Covered key concepts.",
    "strengths": [
      "Clear explanation of async/await",
      "Mentioned practical use cases"
    ],
    "weaknesses": [
      "Could elaborate on event loops"
    ],
    "improvement_suggestions": [
      "Add more details about GIL and threading comparison"
    ]
  },
  "next_question": {
    "id": "860e8400-e29b-41d4-a716-446655440000",
    "text": "How would you optimize a slow database query?",
    "question_type": "technical",
    "difficulty": "medium"
  }
}
```

**Error Responses:**
- `404 Not Found`: Interview or question not found
- `400 Bad Request`: Invalid answer format or interview not in progress

---

### 8. Complete Interview

#### `POST /api/v1/interviews/{interview_id}/complete`

Complete the interview and generate feedback.

**Path Parameters:**
- `interview_id`: UUID of the interview

**Response (200 OK):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "completed_at": "2024-01-15T11:00:00Z",
  "overall_score": 78.5,
  "duration_minutes": 25,
  "questions_answered": 10,
  "feedback_url": "/api/v1/interviews/750e8400-e29b-41d4-a716-446655440000/feedback"
}
```

**Error Responses:**
- `404 Not Found`: Interview not found
- `400 Bad Request`: Interview not in progress

---

### 9. Get Interview Feedback

#### `GET /api/v1/interviews/{interview_id}/feedback`

Get comprehensive interview feedback report.

**Path Parameters:**
- `interview_id`: UUID of the interview

**Response (200 OK):**
```json
{
  "interview_id": "750e8400-e29b-41d4-a716-446655440000",
  "overall_score": 78.5,
  "performance_level": "good",
  "summary": "Strong technical knowledge with good communication skills...",
  "skill_scores": {
    "Python": 85.0,
    "API Development": 75.0,
    "Database Design": 72.0,
    "Testing": 80.0
  },
  "strengths": [
    "Clear and articulate explanations",
    "Good understanding of async programming",
    "Practical examples from experience"
  ],
  "areas_for_improvement": [
    "Database optimization techniques",
    "Advanced testing strategies",
    "System design patterns"
  ],
  "recommendations": [
    "Study database indexing and query optimization",
    "Practice with distributed systems design",
    "Review SOLID principles and design patterns"
  ],
  "detailed_report": "## Overall Performance\n\nYou demonstrated strong...",
  "created_at": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Interview not found
- `400 Bad Request`: Interview not completed yet

---

### 10. Get Interview History

#### `GET /api/v1/candidates/{candidate_id}/interviews`

Get interview history for a candidate.

**Path Parameters:**
- `candidate_id`: UUID of the candidate

**Query Parameters:**
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (optional)

**Response (200 OK):**
```json
{
  "candidate_id": "650e8400-e29b-41d4-a716-446655440000",
  "total_interviews": 3,
  "interviews": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "overall_score": 78.5,
      "started_at": "2024-01-15T10:40:00Z",
      "completed_at": "2024-01-15T11:00:00Z"
    },
    {
      "id": "760e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "overall_score": 82.0,
      "started_at": "2024-01-10T14:20:00Z",
      "completed_at": "2024-01-10T14:45:00Z"
    }
  ],
  "performance_trend": "improving"
}
```

**Error Responses:**
- `404 Not Found`: Candidate not found

---

## Question Management

### 11. Create Question

#### `POST /api/v1/questions`

Create a new interview question.

**Request Body:**
```json
{
  "text": "Explain the SOLID principles in software engineering.",
  "question_type": "technical",
  "difficulty": "medium",
  "skills": ["OOP", "Design Patterns"],
  "tags": ["software-engineering", "architecture"],
  "reference_answer": "SOLID is an acronym for five design principles...",
  "evaluation_criteria": "Should mention all 5 principles with examples"
}
```

**Response (201 Created):**
```json
{
  "id": "870e8400-e29b-41d4-a716-446655440000",
  "text": "Explain the SOLID principles in software engineering.",
  "question_type": "technical",
  "difficulty": "medium",
  "skills": ["OOP", "Design Patterns"],
  "tags": ["software-engineering", "architecture"],
  "version": 1,
  "created_at": "2024-01-15T12:00:00Z"
}
```

---

### 12. List Questions

#### `GET /api/v1/questions`

List all questions with filtering and pagination.

**Query Parameters:**
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)
- `question_type`: Filter by type (optional)
- `difficulty`: Filter by difficulty (optional)
- `skill`: Filter by skill (optional)
- `tag`: Filter by tag (optional)

**Response (200 OK):**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "questions": [
    {
      "id": "870e8400-e29b-41d4-a716-446655440000",
      "text": "Explain the SOLID principles...",
      "question_type": "technical",
      "difficulty": "medium",
      "skills": ["OOP", "Design Patterns"],
      "tags": ["software-engineering"],
      "created_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

---

## WebSocket API

### Interview Chat WebSocket

#### `WS /api/v1/ws/interviews/{interview_id}`

Real-time interview chat via WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/interviews/750e8400-e29b-41d4-a716-446655440000');
```

**Client → Server Messages:**

1. **Submit Answer:**
```json
{
  "type": "answer",
  "question_id": "850e8400-e29b-41d4-a716-446655440000",
  "text": "My answer is..."
}
```

2. **Request Next Question:**
```json
{
  "type": "next_question"
}
```

3. **Voice Answer:**
```json
{
  "type": "voice_answer",
  "question_id": "850e8400-e29b-41d4-a716-446655440000",
  "audio_data": "<base64_encoded_audio>"
}
```

**Server → Client Messages:**

1. **Question:**
```json
{
  "type": "question",
  "question": {
    "id": "850e8400-e29b-41d4-a716-446655440000",
    "text": "Can you explain...",
    "question_number": 2,
    "total_questions": 10
  }
}
```

2. **Evaluation:**
```json
{
  "type": "evaluation",
  "answer_id": "950e8400-e29b-41d4-a716-446655440000",
  "score": 85.0,
  "feedback": "Good explanation..."
}
```

3. **Interview Complete:**
```json
{
  "type": "interview_complete",
  "overall_score": 78.5,
  "feedback_url": "/api/v1/interviews/750e8400-e29b-41d4-a716-446655440000/feedback"
}
```

4. **Error:**
```json
{
  "type": "error",
  "code": "INVALID_QUESTION",
  "message": "Question not found"
}
```

---

## Audio Endpoints

### 13. Get Question Audio

#### `GET /api/v1/audio/questions/{question_id}.mp3`

Get text-to-speech audio for a question.

**Path Parameters:**
- `question_id`: UUID of the question

**Query Parameters:**
- `voice`: Voice ID (optional, default: system default)
- `language`: Language code (optional, default: en-US)

**Response (200 OK):**
- Content-Type: `audio/mpeg`
- Body: MP3 audio file

---

### 14. Upload Answer Audio

#### `POST /api/v1/audio/answers`

Upload audio answer for transcription.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  ```
  audio_file: <file> (WAV, MP3)
  interview_id: <uuid>
  question_id: <uuid>
  ```

**Response (200 OK):**
```json
{
  "answer_id": "950e8400-e29b-41d4-a716-446655440000",
  "transcribed_text": "Async programming allows...",
  "audio_url": "/api/v1/audio/answers/950e8400-e29b-41d4-a716-446655440000.mp3",
  "duration_seconds": 45.2
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: External service unavailable

---

## Rate Limiting

**Limits:**
- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute
- Interview session: No limit during active interview

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

---

## Pagination

All list endpoints support pagination:

**Request:**
```
GET /api/v1/questions?limit=20&offset=40
```

**Response:**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 40,
  "has_more": true,
  "next_url": "/api/v1/questions?limit=20&offset=60",
  "prev_url": "/api/v1/questions?limit=20&offset=20",
  "data": [...]
}
```

---

## Versioning

API version is specified in the URL: `/api/v1/`

Breaking changes will increment the version: `/api/v2/`

---

## SDK Examples

### Python

```python
import httpx

client = httpx.AsyncClient(base_url="http://localhost:8000")

# Upload CV
with open("cv.pdf", "rb") as f:
    response = await client.post(
        "/api/v1/cv/upload",
        files={"cv_file": f},
        data={"candidate_id": str(candidate_id)}
    )

cv_analysis_id = response.json()["cv_analysis_id"]

# Create interview
response = await client.post(
    "/api/v1/interviews",
    json={
        "candidate_id": str(candidate_id),
        "cv_analysis_id": str(cv_analysis_id),
        "num_questions": 10
    }
)

interview_id = response.json()["id"]
```

### JavaScript

```javascript
// Upload CV
const formData = new FormData();
formData.append('cv_file', fileInput.files[0]);
formData.append('candidate_id', candidateId);

const cvResponse = await fetch('http://localhost:8000/api/v1/cv/upload', {
  method: 'POST',
  body: formData
});

const { cv_analysis_id } = await cvResponse.json();

// Create interview
const interviewResponse = await fetch('http://localhost:8000/api/v1/interviews', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    candidate_id: candidateId,
    cv_analysis_id: cv_analysis_id,
    num_questions: 10
  })
});

const { id: interviewId } = await interviewResponse.json();
```

---

## Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

These provide interactive API testing and complete schema documentation.
