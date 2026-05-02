---
name: poll-deep-research-runs
description: Poll Deep Research Runs
disable-model-invocation: true
---

# Poll Deep Research Runs

Poll in-flight deep-research runs from `Research Runs`, then update `Research Runs` and `Research Ideas` with completion metadata and summaries.

## Steps

1. Load guidance and skills:
   - Read `AGENTS.md`.
   - Read `.agents/skills/parallel-deep-research/SKILL.md`.
   - Read `.agents/skills/notion-api/SKILL.md`.
   - Follow workspace safety/change-control rules.

2. Validate auth and resolve target Notion objects (read-only):
   - Check `NOTION_API_TOKEN` from environment first, then `.env` if needed (never print token).
   - Locate `Research Runs` and `Research Ideas` data sources.
   - Retrieve each schema and resolve property IDs by exact name first, then alias fallback.

3. Validate field map before any polling:
   - `Research Runs` **required** fields:
     - `Idea` (relation to `Research Ideas`)
     - `Run ID` (title; parse as the provider `run_id`, not rich text)
     - `Status` (status/select)
   - `Research Runs` **strongly recommended** fields:
     - `Previous Interaction ID`
     - `Started At`
     - `Completed At`
     - `Result URL`
     - `Executive Summary`
     - `Error Message`
     - `Result MD Path`
     - `Result JSON Path`
   - `Research Ideas` **required** fields:
     - `Last Run At`
     - `Last Run ID`
     - `Executive Summary`
   - `Research Ideas` **optional** fields:
     - `Result URL`
     - `Status` (only update if completion status value is explicitly configured)
   - Alias fallback examples (if exact name missing):
     - `Run ID`: `RunID`, `Parallel Run ID`
     - `Previous Interaction ID`: `PreviousInteractionID`, `Previous Parallel Interaction ID`
     - `Started At`: `Triggered At`, `Submitted At`
     - `Result URL`: `Run URL`, `Parallel URL`
     - `Executive Summary`: `Summary`, `Latest Summary`
     - `Completed At`: `Finished At`, `Last Completed At`
     - `Error Message`: `Error`, `Failure Reason`
   - If any required field is missing, stop and report missing fields.

4. Query candidate run records from `Research Runs`:
   - Filter records with all conditions:
     - `Run ID` title is not empty
     - `Status` in in-flight set (default: `queued`, `running`, `in_progress`, `submitted`)
   - Exclude records already terminal:
     - `completed`, `failed`, `cancelled`, `error`
   - If no candidates found, report and stop.

5. Build execution preview (read-only) and ask confirmation:
   - Show:
     - target data source names + IDs
     - number of candidate runs
     - resolved property map (required + optional found)
     - exact write intent per result state (completed vs failed vs still running)
   - Ask for explicit confirmation before polling and database writes.
   - If not confirmed, stop.

6. Poll each candidate run:
   - For each row, run:
     - `parallel-cli research poll "<run_id>" -o "<kebab-case-filename>" --timeout 540`
   - Derive outcome:
     - `completed`: executive summary and output files available
     - `failed`: capture concise error reason
     - `still_running`: timeout/no terminal result; do not mark terminal
   - Capture per run:
     - `run_id`
     - completion status
     - completed timestamp (if terminal)
     - executive summary (if completed)
     - output file paths (`.md`, `.json`) when generated
     - best available result URL pointer (prefer existing stored URL; if unavailable, retain monitoring URL if present)

7. Prepare final write plan (no writes yet):
   - For each polled run record in `Research Runs`:
     - Always update `Status` according to outcome
     - On `completed`: set `Completed At`, `Executive Summary`, `Result URL` (if available), result path fields (if present)
     - On `failed`: set `Completed At`, `Error Message` (or fallback text field)
     - On `still_running`: optionally refresh heartbeat timestamp only if such field exists; otherwise no write
   - For linked `Research Ideas` page:
     - On `completed`:
       - `Last Run At` = completion timestamp
       - `Last Run ID` = run ID
       - `Executive Summary` = latest summary from completed run
       - `Result URL` = same pointer used in runs table (if field exists)
     - On `failed` or `still_running`: do not overwrite `Executive Summary`
   - Conflict rule:
     - If multiple completed runs map to one idea in this batch, keep the newest completion time as canonical update for `Research Ideas`.

8. Confirmation gate before writes:
   - Present concise write preview:
     - total updates to `Research Runs` by outcome (`completed`/`failed`/`still_running`)
     - total updates to `Research Ideas`
     - fields that will be modified
   - Ask explicit confirmation.
   - If not confirmed, stop after showing poll results summary.

9. Execute writes after confirmation:
   - Update `Research Runs` first, then `Research Ideas`.
   - Use property IDs for writes (not names).
   - Process sequentially and continue on per-record error.
   - Never expose secrets/tokens.

10. Final report:
   - Candidate runs found, polled, completed, failed, still running.
   - `Research Runs`: updated/skipped/failed count.
   - `Research Ideas`: updated/skipped/failed count.
   - For failures: include page title/ID, run ID, and concise reason.
   - Include generated output file paths for completed runs.
