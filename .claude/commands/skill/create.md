---
description: Create a new agent skill
argument-hint: [prompt-or-llms-or-github-url]
---

Ultrathink.
Use `skill-creator` skill.
Create a new **Agent Skill** for Claude Code based on the given prompt:
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
  `SKILL.md` must be under 500 lines, if you need more, plit it to multiple files in `references` folder.
- Skill folder name (hyphen-case): `<skill-name>`
- Skill full path: `./.claude/skills/<skill-name>/SKILL.md`
- Script files (if any): `./.claude/skills/<skill-name>/scripts/my-script.py` or `./.claude/skills/<skill-name>/scripts/my-script.sh`
- Reference files (if any): `./.claude/skills/<skill-name>/references/ref-0.md`

## Rules of Skill Creation:
- If you're given an URL, it's documentation page, use `Explorer` subagent to explore every internal link and report back to main agent, don't skip any link.
- If you receive a lot of URLs, use multiple `Explorer` subagents to explore them in parallel, then report back to main agent.
- If you receive a lot of files, use multiple `Explorer` subagents to explore them in parallel, then report back to main agent.
- If you're given a Github URL, use [`repomix`](https://repomix.com/guide/usage) command to summarize ([install it](https://repomix.com/guide/installation) if needed) and spawn multiple `Explorer` subagents to explore it in parallel, then report back to main agent.