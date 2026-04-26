# Project Agent Skills

Project-level skills live in `.agents/skills/` so Cursor can auto-discover them for this workspace.

Use skills for repeatable assistant workflows, not general preferences. Keep sensitive skills explicit by setting `disable-model-invocation: true` in `SKILL.md` so they only run when manually invoked.

Recommended conventions:

- Keep each skill focused on one workflow.
- Prefer read-only analysis unless the user explicitly approves a write action.
- Do not store credentials, tokens, account numbers, or raw financial exports in skill files.
- Put long references in a `references/` folder inside the skill if needed.
- Put scripts in a `scripts/` folder only when the workflow genuinely needs executable automation.
