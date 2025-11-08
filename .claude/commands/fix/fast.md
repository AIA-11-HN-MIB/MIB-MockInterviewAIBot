---
description: Analyze and fix small issues [FAST]
argument-hint: [issues]
---

Analyze and fix these issues:
<issues>$ARGUMENTS</issues>

## Workflow

- If the user provides a screenshots or videos, use `gemini-vision` skill to describe as detailed as possible the issue, make sure developers can predict the root causes easily based on the description.
- Use `tester` agent to test the fix and make sure it works, then report back to main agent.
- If there are issues or failed tests, ask main agent to fix all of them and repeat the process until all tests pass.

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.