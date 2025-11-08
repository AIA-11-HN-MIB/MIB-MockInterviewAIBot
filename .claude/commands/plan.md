---
description: Research, analyze, and create an implementation plan
argument-hint: [task]
---

Use the `planner` subagent to plan for this task:
<task>$ARGUMENTS</task>

**Research Output Requirements**
- Ensure every research markdown report remains concise (≤150 lines) while covering all requested topics and citations.

**Plan File Specification**
- Create a directory named `plans/YYYYMMDD-HHmm-plan-name` (example: `plans/20251101-1505-authentication-and-profile-implementation`).
- Save the overview access point at `plans/YYYYMMDD-HHmm-plan-name/plan.md`. Keep it generic, under 80 lines, and list each implementation phase with status and progress plus links to phase files.
- For each phase, create `plans/YYYYMMDD-HHmm-plan-name/phase-XX-phase-name-here.md` containing the following sections in order: Context links (reference parent plan, dependencies, docs), Overview (date, description, priority, implementation status, review status), Key Insights, Requirements, Architecture, Related code files, Implementation Steps, Todo list, Success Criteria, Risk Assessment, Security Considerations, Next steps.

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.
**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.
**IMPORTANT**: **Do not** start implementing.
