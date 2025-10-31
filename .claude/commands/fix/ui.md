---
description: Analyze and fix UI issues
argument-hint: [issue]
---

Use `ui-ux-designer` subagent to read and analyze `./docs/design-guidelines.md` then fix the following issues:
<issue>$ARGUMENTS</issue>

## Workflow
If the user provides a screenshots or videos, use `gemini-vision` skill to describe as detailed as possible the issue, make sure developers can predict the root causes easily based on the description.

1. Use `ui-ux-designer` subagent to implement the fix step by step.
2. Use screenshot capture tools along with `gemini-vision` skill to take screenshots of the implemented fix (at the exact parent container, don't take screenshot of the whole page) and use the appropriate Gemini analysis skills (`gemini-vision`, `gemini-video-understanding`, or `gemini-document-processing`) to analyze those outputs so the result matches the design guideline and addresses all issues.
  - If the issues are not addressed, repeat the process until all issues are addressed.
3. Use `chrome-devtools` skill to analyze the implemented fix and make sure it matches the design guideline.
4. Use `tester` agent to test the fix and compile the code to make sure it works, then report back to main agent.
  - If there are issues or failed tests, ask main agent to fix all of them and repeat the process until all tests pass.