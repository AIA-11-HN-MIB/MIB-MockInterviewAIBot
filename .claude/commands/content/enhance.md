---
description: Analyze the current copy issues and enhance it
argument-hint: [issues]
---

Enhance the copy based on reported issues:
<issues>$ARGUMENTS</issues>

## Workflow

- If the user provides screenshots, use `gemini-vision` skill to analyze and describe the issues in detail, ensuring the copywriter understands the context.
- If the user provides videos, use `gemini-video-understanding` skill to analyze video content and extract relevant copy issues.
- Use multiple `scouter` agents to scout the current codebase or given codebase (if any) to understand the context, then report back to `copywriter` agent.
- Use `copywriter` agent to write the enhanced copy into the code files, then report back to main agent.