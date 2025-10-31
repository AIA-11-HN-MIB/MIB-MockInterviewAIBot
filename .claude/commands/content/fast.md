---
description: Write creative & smart copy [FAST]
argument-hint: [user-request]
---

Write creative & smart copy for this user request:
<user_request>$ARGUMENTS</user_request>

## Workflow

- If the user provides screenshots, use `gemini-vision` skill to analyze and describe the context.
- If the user provides videos, use `gemini-video-understanding` skill to analyze video content.
- Use `copywriter` agent to write the copy, then report back to main agent.