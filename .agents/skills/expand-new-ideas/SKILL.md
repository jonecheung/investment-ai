---
name: expand-new-ideas
description: Expand New Ideas
disable-model-invocation: true
---

# Expand New Ideas

Convert eligible Notion `Research Ideas` entries from `Original Idea` into `Research Input`, then move status to `expanded`.

## Steps

1. Load guidance and prompt sources:
   - Read `AGENTS.md`.
   - Read `data/prompts/research-idea-brief.md`.
   - Read `data/parallel/prompt-daily-fx-strategy-brief.md` (daily FX strategy selector).
   - Follow workspace safety rules and the `notion-api` skill.

2. Validate auth and target objects (read-only):
   - Check `NOTION_API_TOKEN` from environment first, then `.env` if needed.
   - Locate the `Research Ideas` data source.
   - Confirm required properties exist: `Original Idea`, `Research Input`, `Status`, `Active`.

3. Query eligible ideas:
   - Filter for records where all are true:
     - `Status` equals `New`
     - `Active` equals `true`
     - `Research Input` is empty
   - If no records match, report and stop.

4. Before writing, provide a change preview and ask for confirmation:
   - Summarize target object (Notion data source name + ID).
   - Summarize count of matched records.
   - Summarize exact updates to be applied per record:
     - Set `Research Input` (generated from `Original Idea` using `data/prompts/research-idea-brief.md`)
     - Set `Status` to `expanded`
   - Wait for explicit confirmation before any write.

5. Generate research input:
   - For each matched record, inspect `Original Idea`:
     - **Daily FX strategy brief:** If title matches `Daily FX strategy brief — {YYYY-MM-DD}` (case-insensitive):
       - Extract date from title; fallback to today UTC if missing.
       - Load the **Research Prompt** block from `data/parallel/prompt-daily-fx-strategy-brief.md` (content between the first pair of `---` fences under `## Research Prompt`).
       - Replace all `{YYYY-MM-DD}` placeholders with the extracted date.
       - Use the result as `Research Input` verbatim (do not summarize or shorten).
     - **All other ideas:** Use `data/prompts/research-idea-brief.md` guidance + `Original Idea` to produce concise, high-signal `Research Input`.

6. Update Notion pages:
   - Update each matched page in `Research Ideas`:
     - `Research Input` = generated text
     - `Status` = `expanded`
   - Process sequentially and handle errors per record (do not abort all on first failure).

7. Final report:
   - Total matched, updated, skipped, failed.
   - For failures, include page title/ID and concise error reason.
   - Do not expose secrets or raw tokens.
