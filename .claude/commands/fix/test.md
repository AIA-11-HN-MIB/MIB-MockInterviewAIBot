---
description: Run test suite and fix issues
argument-hint: [issues]
---

## Reported Issues:
<issues>$ARGUMENTS</issues>

## Workflow:
1. First use `tester` subagent to compile the code and fix all syntax errors if any.
2. Then use `tester` subagent to run the tests.
3. If there are issues or failed tests, use `debugger` subagent to find the root cause of the issues.
4. Then use `planner` subagent to create an implementation plan following the progressive disclosure structure:
   - Create a directory `plans/YYYYMMDD-HHmm-plan-name` (example: `plans/20251101-1505-authentication-and-profile-implementation`).
   - Save the overview access point at `plan.md`, keep it generic, under 80 lines, and list each phase with status/progress and links.
   - For each phase, add `phase-XX-phase-name.md` files containing sections (Context links, Overview with date/priority/statuses, Key Insights, Requirements, Architecture, Related code files, Implementation Steps, Todo list, Success Criteria, Risk Assessment, Security Considerations, Next steps).
5. Then implement the plan step by step.
6. Use `tester` subagent to run the tests after implementing the plan, make sure it works, then report back to main agent.
7. After finishing, delegate to `code-reviewer` agent to review code. If there are critical issues, ask main agent to improve the code and test everything again.
8. Repeat this process until all tests pass and no more errors are reported.

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.