---
description: Analyze logs and fix issues
argument-hint: [issue]
---

## Issue
<issue>$ARGUMENTS</issue>

## Workflow
Use `debugger` subagent to analyze the `./logs.txt` file, identify root causes of any errors or issues and respond with a report and solution.
So the main agent can fix them.

## Rules
- Use `debugger` subagent to read and analyze the entire `./logs.txt` file
- Identify all errors, warnings, and potential issues
- Determine the root causes of each issue
- Fix all identified problems systematically based on the report
- Verify fixes by running appropriate commands
- Re-analyze logs after fixes to ensure issues are resolved

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.
