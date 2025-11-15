# Question Generation Scout Report
Generated: 2025-11-15

## Executive Summary
Complete audit of question generation system across 3 architectural layers. Found 8 core files implementing LLM-based question generation with exemplar support, adaptive follow-ups, and ideal answer generation.

## File Locations

H:\AI-courseliosAIService\src\domain\ports\llm_port.py
H:\AI-courseliosAIService\srcdapters\llm\openai_adapter.py
H:\AI-courseliosAIService\srcdapters\llmzure_openai_adapter.py
H:\AI-courseliosAIService\srcdapters\mock\mock_llm_adapter.py
H:\AI-courseliosAIService\src\domain\models\question.py
H:\AI-courseliosAIService\srcpplication\use_cases\plan_interview.py
H:\AI-courseliosAIService\srcpplication\use_cases\process_answer_adaptive.py
H:\AI-courseliosAIService\srcpplication\use_casesollow_up_decision.py
H:\AI-courseliosAIService\srcpplication\use_cases\get_next_question.py

## 1. LLM Port Interface (llm_port.py - 217 lines)

Abstract interface defining all LLM operations for question generation.

Key Methods for Question Generation:
- generate_question(context, skill, difficulty, exemplars=None) -> str
- generate_ideal_answer(question_text, context) -> str (150-300 words)
- generate_rationale(question_text, ideal_answer) -> str (50-100 words)
- generate_followup_question(..., cumulative_gaps, previous_follow_ups) -> str
- detect_concept_gaps(answer_text, ideal_answer, question_text, keyword_gaps) -> dict
- generate_interview_recommendations(context) -> dict

Features:
- Exemplar-based generation (list of similar questions)
- Context-aware (CV summary, skills, experience, covered topics, stage)
- Attempt-aware for follow-ups (tracks previous attempts, penalties)
- Structured JSON output for scoring


## 2A. OpenAI Adapter (openai_adapter.py - 625 lines)

Primary LLM implementation using GPT-4 and GPT-3.5-turbo.

Generate Question Prompt:
  System: "You are an expert technical interviewer. Generate a clear, relevant interview question based on the context provided."
  
  User: Generate a {difficulty} difficulty interview question to test: {skill}
        Context: candidate background, previous topics, interview stage
        [If exemplars: Similar questions for inspiration - do NOT copy exactly]
        Return only the question text

  Model: gpt-4 | Temperature: 0.7

Generate Ideal Answer:
  Requirements: 150-300 words, expert-level understanding, key concepts, practical examples
  Model: gpt-4 | Temperature: 0.3 | Max tokens: 500

Generate Rationale:
  Requirements: 50-100 words explaining why answer is ideal, what weaker answers miss
  Model: gpt-3.5-turbo | Temperature: 0.3 | Max tokens: 200

Evaluate Answer:
  JSON output: score, completeness, relevance, sentiment, strengths, weaknesses, improvements, reasoning
  Follow-up context support: attempt number, previous scores, persistent gaps, stricter evaluation
  Model: gpt-4 | Temperature: 0.3 | Format: JSON

Detect Concept Gaps:
  JSON output: concepts, confirmed, severity (minor/moderate/major)
  Model: gpt-3.5-turbo | Temperature: 0.3 | Format: JSON

Generate Follow-up Question:
  Addresses critical missing concepts, progressively targeted (max 3 follow-ups)
  Uses cumulative gaps if available
  Model: gpt-3.5-turbo | Temperature: 0.4 | Max tokens: 150

Generate Interview Recommendations:
  JSON: strengths (3-5), weaknesses (3-5), study_topics (3-7), technique_tips (2-5)
  Based on evaluations and gap progression
  Model: gpt-3.5-turbo | Temperature: 0.7 | Max tokens: 800


## 2B. Azure OpenAI Adapter (azure_openai_adapter.py)

Azure-hosted OpenAI variant with:
- AsyncAzureOpenAI client
- Region-specific endpoint
- Deployment name configuration
- _extract_json_from_markdown() for markdown-wrapped JSON

Same prompts as OpenAI adapter.


## 3. Mock LLM Adapter (mock_llm_adapter.py - 355 lines)

Development/testing adapter with realistic fake responses:

- generate_question: "Mock question about {skill} at {difficulty}?" + exemplar count
- generate_ideal_answer: Template answer demonstrating mastery
- generate_rationale: Template rationale
- generate_followup_question: Different per order (1-3)
- detect_concept_gaps: Heuristic based on word count (<30 = gaps)
- evaluate_answer: Score-based realistic evaluations
- generate_interview_recommendations: Score-based recommendations


## 4. Question Domain Model (question.py - 109 lines)

Value object representing interview questions.

Core fields:
- id: UUID
- text: str
- question_type: QuestionType (TECHNICAL/BEHAVIORAL/SITUATIONAL)
- difficulty: DifficultyLevel (EASY/MEDIUM/HARD)
- skills: list[str]
- tags: list[str]
- embedding: list[float] | None

Pre-planning fields:
- ideal_answer: str | None (150-300 words)
- rationale: str | None (50-100 words)


## 5. Plan Interview Use Case (plan_interview.py - 385 lines)

Pre-planning orchestration to generate n questions with ideal answers.

Question count calculation (skill-based):
- <=2 skills → 2 questions
- <=4 skills → 3 questions
- <=7 skills → 4 questions
- >7 skills → 5 questions (max)

Distribution:
- Type: 60% TECHNICAL, 30% BEHAVIORAL, 10% SITUATIONAL
- Difficulty: 50% EASY, 30% MEDIUM, 20% HARD

Single question generation process:
1. Determine question type/difficulty based on index
2. Select skill from top 5 (use modulo rotation)
3. Find exemplar questions (max 3)
4. Build context: {summary, skills, experience}
5. llm.generate_question(context, skill, difficulty, exemplars)
6. llm.generate_ideal_answer(question_text, context)
7. llm.generate_rationale(question_text, ideal_answer)
8. Create Question entity with all fields

Exemplar retrieval:
- Query by skill and difficulty
- Filter by question_type
- Return max 3: {text, skills, difficulty}
- Currently: Database fallback (vector search commented)

Search query template: "{skill} {difficulty} interview question for {exp_level} developer"


## 6. Process Answer Adaptive (process_answer_adaptive.py)

Evaluates answers, detects gaps, triggers follow-ups.

Key features:
- Detects if follow-up or main question
- Builds follow-up context with previous evaluations
- Attempt-based penalties: 0 (attempt 1), -5 (attempt 2), -15 (attempt 3)
- Resolves gaps if: completeness >= 0.8 OR score >= 80 OR attempt == 3

Workflow:
1. Validate interview state
2. Detect if follow-up question
3. Build follow-up context if applicable
4. Create Answer entity
5. llm.evaluate_answer with followup_context
6. llm.detect_concept_gaps
7. Create Evaluation entity
8. Determine if needs follow-up


## 7. Follow-Up Decision (follow_up_decision.py - 163 lines)

Decides if follow-up should be generated.

Break conditions (return no follow-up):
1. follow_up_count >= 3 (max 3 follow-ups)
2. latest_eval.is_adaptive_complete() (similarity >= 0.8 or no gaps)
3. len(cumulative_gaps) == 0 (no gaps to address)

Gap accumulation:
- Collect gaps from latest_evaluation
- Collect gaps from all previous follow-up evaluations
- Remove resolved gaps
- Return list of unique gap concepts


## 8. Get Next Question (get_next_question.py - 49 lines)

Simple question retrieval during interview.

Workflow:
1. Get interview by ID
2. Check: interview.has_more_questions()
3. Get: interview.get_current_question_id()
4. Fetch question from repository


## Prompt Engineering Summary

Temperature Strategy:
- 0.3: Deterministic (evaluation, gaps)
- 0.4: Focused (follow-ups)
- 0.7: Creative (generation, recommendations)

Model Usage:
- gpt-4: Questions, answers, evaluation
- gpt-3.5-turbo: Rationale, gaps, follow-ups, recommendations

## Unresolved Questions

1. Vector search exemplar retrieval currently commented (using DB fallback)
2. Question embedding storage in vector DB commented
3. Domain-specific prompt expansion needed?
4. Sequential vs parallel question generation performance?
5. Cost optimization: Use gpt-3.5-turbo for all except generation?

