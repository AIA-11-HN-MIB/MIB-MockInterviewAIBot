---
description: ⚡⚡⚡ Research, analyze, and create an implementation plan
argument-hint: [task]
---

## Your mission
<task>$ARGUMENTS</task>

## Workflow
Use `planner` subagent to:
1. Create a directory named `plans/YYYYMMDD-HHmm-plan-name` (eg. `plans/20251101-1505-authentication-and-profile-implementation`).
2. Use multiple `researcher` agents in parallel to research for this task, each agent research for a different aspect of the task and perform max 3 researches.
3. Use `/scout <instructions>` slash command to search the codebase for files needed to complete the task.
4. Gathers all research and scout report filepaths, and create an implementation plan of this task.
5. Ask user to review the plan

## Important Notes
- **IMPORTANT:** Ensure token efficiency while maintaining high quality.
- **IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.
- **IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
- **IMPORTANT:** In reports, list any unresolved questions at the end, if any.
- **IMPORTANT**: **Do not** start implementing.
