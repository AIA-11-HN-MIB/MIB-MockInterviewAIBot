---
description: Fix the agent skill based on `logs.txt` file.
argument-hint: [prompt-or-path-to-skill]
---

Ultrathink.
Use `skill-creator` skill.
Fix the agent skill based on the current `logs.txt` file (in the project root directory):
<prompt>$ARGUMENTS</prompt>

## Before Starting:
- Read this skill documentation carefully before starting: https://docs.claude.com/en/docs/claude-code/skills.md
- Read the **Agent Skills Spec** carefully before starting: `.claude/skills/agent_skills_spec.md`
- [Agent Skills Overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview.md)
  - Especially focus on the **How Skills work** section (with **progressive disclosure**)
  - That means try to keep `SKILL.md` short and simple (<200 lines), and provide more details in the reference files & scripts.
- [Best Practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices.md)

## Skill Structure:
- **Skills location:** `./.claude/skills`
- Skill file name (uppercase): `SKILL.md`
- Skill folder name (hyphen-case): `<skill-name>`
- Skill full path: `./.claude/skills/<skill-name>/SKILL.md`
- Script files (if any): `./.claude/skills/<skill-name>/scripts/my-script.py` or `./.claude/skills/<skill-name>/scripts/my-script.sh`
- Reference files (if any): `./.claude/skills/<skill-name>/references/ref-0.md`

## Rules of Skill Fixing:
- If you're given an URL, it's documentation page, use `Explorer` subagent to explore every internal link and report back to main agent, don't skip any link.
- If you receive a lot of URLs, use multiple `Explorer` subagents to explore them in parallel, then report back to main agent.
- If you receive a lot of files, use multiple `Explorer` subagents to explore them in parallel, then report back to main agent.
- If you're given a Github URL, use [`repomix`](https://repomix.com/guide/usage) command to summarize ([install it](https://repomix.com/guide/installation) if needed) and spawn multiple `Explorer` subagents to explore it in parallel, then report back to main agent.