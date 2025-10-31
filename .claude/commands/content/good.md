---
description: Write good creative & smart copy [GOOD]
argument-hint: [user-request]
---

Write good creative & smart copy for this user request:
<user_request>$ARGUMENTS</user_request>

## Workflow

- If the user provides screenshots, use `gemini-vision` skill to analyze and describe the context in detail.
- If the user provides videos, use `gemini-video-understanding` skill to analyze video content.
- Use multiple `researcher` agents in parallel to search for relevant information & multiple `scouter` agents to scout the current codebase or given codebase (if any) to understand the project, then report back to `planner` agent.
- Use `planner` agent to plan the copy, make sure it can satisfy the user request.
- Use `copywriter` agent to write the copy based on the plan, then report back to main agent.