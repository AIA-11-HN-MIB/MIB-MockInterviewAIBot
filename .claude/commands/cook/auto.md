---
description: Implement a feature automatically ("trust me bro")
argument-hint: [tasks]
---

**Ultrathink** to plan & start working on these tasks follow the Orchestration Protocol, Core Responsibilities, Subagents Team and Development Rules: 
<tasks>$ARGUMENTS</tasks>

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.

## Workflow:
1. Use `planner` subagent and `researcher` subagent to create an implementation plan following the progressive disclosure structure:
   - Create a directory `plans/YYYYMMDD-HHmm-plan-name` (example: `plans/20251101-1505-authentication-and-profile-implementation`).
   - Save the overview access point at `plan.md`, keep it generic, under 80 lines, and list each phase with status/progress and links.
   - For each phase, add `phase-XX-phase-name.md` files containing sections (Context links, Overview with date/priority/statuses, Key Insights, Requirements, Architecture, Related code files, Implementation Steps, Todo list, Success Criteria, Risk Assessment, Security Considerations, Next steps).
   - Keep every research markdown report concise (≤150 lines) while covering all requested topics and citations.
2. Then use general agent (main agent) to implement the plan step by step.
3. Run type checking and compile the code to make sure there are no syntax errors.
4. Write the tests for the plan, make sure you don't use fake data just to pass the tests, tests should be real and cover all possible cases.
5. Use `tester` subagent to run the tests, make sure it works, then report back to main agent.
6. If there are issues or failed tests, use `debugger` subagent to find the root cause of the issues, then ask main agent to fix all of them and 
7. Repeat the process until all tests pass or no more issues are reported. 
    **Again, do not ignore failed tests or use fake data, mocks, cheats, tricks, temporary solutions, just to pass the build or github actions.**
8. After finishing, delegate to `code-reviewer` subagent to review code. If there are any issues, ask main agent to improve the code and tell `tester` agent to run the tests again. Repeat the process until all tests pass.
9. When all tests pass, code is reviewed, the tasks are completed, report back to user with a summary of the changes and explain everything briefly, ask user to review the changes and approve them.
10. User review process:
  - **If user approves the changes:** use these subagents in parallel: 
    - Give the implementation plan to `project-manage` subagent to update the progress and task status.
    - Use `docs-manager` subagent to update the docs if needed.
    - **IMPORTANT:** Sacrifice grammar for the sake of concision when writing outputs.
  - **If user rejects the changes:** ask user to explain the issues and ask main agent to fix all of them and repeat the process.
11. Finally ask user if he wants to commit to git repository, if yes use `git-manager` subagent to commit to git repository.

**REMEMBER**:
- You can always generate images with `gemini-image-gen` skill on the fly for visual assets.
- You always read and analyze the generated assets with `gemini-vision` skill to verify they meet requirements.
- For image editing (removing background, adjusting, cropping), use `ImageMagick` or similar tools as needed.