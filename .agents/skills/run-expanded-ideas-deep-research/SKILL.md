---
name: run-expanded-ideas-deep-research
description: Run Expanded Ideas Deep Research
disable-model-invocation: true
---

# Run Expanded Ideas Deep Research

Find eligible `Research Ideas` records (`Status = Expanded`, `Active = true`, and `Research Input` is not empty), create deep-research runs, then immediately record run metadata in Notion (`Research Ideas` + `Research Runs`) without polling.

## Steps

1. Load guidance and skills:
   - Read `AGENTS.md`.
   - Read `.agents/skills/parallel-deep-research/SKILL.md`.
   - Read `.agents/skills/notion-api/SKILL.md`.
   - Follow workspace safety/change-control rules.

2. Validate auth and resolve target Notion objects (read-only):
   - Check `NOTION_API_TOKEN` from environment first, then `.env` if needed (never print token).
   - Locate `Research Ideas` and `Research Runs` data sources.
   - Confirm required `Research Ideas` properties exist:
     - `Status`
     - `Active`
     - `Research Input`
     - `Original Idea` (optional fallback title context)
     - `Last Run At`
     - `Last Run ID`
   - Confirm `Research Runs` has properties needed to log kickoff metadata (at minimum: `Idea` relation, `Run ID` title, `Result URL`, `Status`, and `Started At`).

3. Query eligible ideas from `Research Ideas`:
   - Filter:
     - `Status` equals `Expanded`
     - `Active` equals `true`
     - `Research Input` is not empty
   - If no records match, report "no eligible ideas" and stop.

4. Prepare execution preview (no writes yet):
   - For each matched idea, collect:
     - page title and page ID
     - `Research Input` text that will be used
   - Summarize:
     - target data source names + IDs (`Research Ideas`, `Research Runs`)
     - number of ideas to process
     - exact operations that will happen:
       - run deep research using `Research Input`
       - create/update kickoff records in `Research Runs`
       - update run pointer fields in `Research Ideas`

5. **Confirmation gate #1 (required):**
   - Ask user: confirm whether to proceed with deep research runs for the matched ideas.
   - If user does not explicitly confirm, stop with no writes and no research run.

6. Run deep research for each matched idea (one-by-one):
   - Use `.agents/skills/parallel-deep-research` procedure.
   - Use each idea's `Research Input` as the deep-research input.
   - Use `parallel-cli research run "<Research Input>" --processor ultra --no-wait --json`.
   - `--no-wait` is required so the command returns immediately and can be polled separately.
   - Capture and retain:
     - `run_id`
     - `interaction_id` for possible future follow-up context, but do not store it in `Research Runs` unless it was supplied as a previous interaction for this run.
     - monitoring URL
   - Do not poll in this command. Stop at successful kickoff for each idea.

7. Prepare Notion write plan (still no writes):
   - For each processed idea, map updates:
     - `Research Runs`: create a run record linked to the idea (or update existing run record if workflow requires), using `run_id` as the `Run ID` title and including monitoring URL, kickoff status, and `Started At`. Leave `Previous Interaction ID` blank for first-pass runs; populate it only when this run was created with `--previous-interaction-id`.
     - `Research Ideas`: update `Last Run At` and `Last Run ID` (plus any kickoff status/link field available in your schema).
   - Include which records will be created vs updated.

8. **Confirmation gate #2 (required before Notion writes):**
   - Present concise write preview:
     - target objects (IDs)
     - count of creates/updates in each database
     - fields to be changed
   - Ask user to explicitly confirm writes.
   - If not confirmed, stop after reporting kickoff metadata; do not write to Notion.

9. Execute Notion writes after confirmation:
   - Apply writes to `Research Runs` and `Research Ideas`.
   - Handle errors per record; continue processing remaining records.
   - Never expose secrets in logs/output.

10. Final report:
   - Eligible ideas found, research runs kicked off/failed.
   - Notion records created/updated/failed in `Research Runs` and `Research Ideas`.
   - For failures: include idea title/page ID and concise reason.
   - Return `run_id`, `interaction_id`, and monitoring URL for each kicked-off run. Note that `interaction_id` is retained for future follow-ups rather than stored as a normal run field.
   - Explicitly note that polling/result ingestion is handled by `poll-deep-research-runs`.
