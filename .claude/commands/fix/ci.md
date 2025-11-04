---
description: Analyze Github Actions logs and fix issues
argument-hint: [github-actions-url]
---
## Github Actions URL
<url>$ARGUMENTS</url>

## Workflow
- Use the `planer` subagent to read the github actions logs, analyze and find the root causes of the issues, then provide a detailed plan for implementing the fixes.
- Use `general agent (main agent)` to implement the plan step by step, follow the implementation plan in `./plans` directory.
- Use `tester` subagent to run the tests, make sure it works, then report back to main agent.
- If there are issues or failed tests, ask main agent to fix all of them and repeat the process until all tests pass.

## Notes
- If `gh` command is not available, instruct the user to install and authorize GitHub CLI first.