---
description: Create an immersive design
argument-hint: [tasks]
---

Think hard to plan & start working on these tasks follow the Orchestration Protocol, Core Responsibilities, Subagents Team and Development Rules: 
<tasks>$ARGUMENTS</tasks>

## Workflow:
1. Use `ui-ux-designer` subagent and multiple `researcher` subagents in parallel to create a design plan with TODO tasks in `./plans` directory.
   - Research about design style, trends, fonts, colors, border, spacing, elements' positions, etc.
   - **IMPORTANT:** Try to predict the font name (Google Fonts) and font size in the given screenshot, don't just use Inter or Poppins.
2. Then use `ui-ux-designer` subagent to implement the plan step by step.
3. If user doesn't specify, create the design in pure HTML/CSS/JS.
4. Report back to user with a summary of the changes and explain everything briefly, ask user to review the changes and approve them.
5. If user approves the changes, update the `./docs/design-guidelines.md` docs if needed.

## Important Notes:
- **ALWAYS REMEBER that you have the skills of a top-tier UI/UX Designer who won a lot of awards on Dribbble, Behance, Awwwards, Mobbin, TheFWA.**
- Remember that you have the capability to generate images, videos, edit images, etc. with gemini-image-gen skill for image generation. Use them to create the design with real assets.
- Always review, analyze and double check the generated assets with gemini-vision skill to verify quality.
- Use removal background tools to remove background from generated assets if needed.
- Create storytelling designs, immersive 3D experiences, micro-interactions, and interactive interfaces.
- Maintain and update `./docs/design-guidelines.md` docs if needed.