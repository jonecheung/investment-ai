---
name: followup-tradable-tickers-curl
description: Run a Parallel Task API follow-up via curl with JSON schema constrained output, validate ticker JSON with ajv-cli, create a linked Research Runs row, and import validated opportunities into Trading Proposals after confirmation.
disable-model-invocation: true
---

# Follow-up Tradable Tickers Curl

Run a follow-up research task against an existing Parallel `interaction_id` or `run_id`, generate structured tradable ticker proposals with Parallel Task API `task_spec.output_schema`, save local result files, validate output with `ajv-cli`, populate Notion `Research Runs`, and import validated rows into Notion `Trading Proposals`.

Use this skill instead of `followup-tradable-tickers` when schema-constrained output is required. The older skill uses `parallel-cli research run --json`, which only makes CLI metadata JSON and does not enforce the research output schema.

This workflow has fixed defaults so it can run without design questions:

- Treat a supplied `trun_...` as both a possible run ID and interaction ID. Resolve it with `parallel-cli research status <id> --json` when available; if the returned `interaction_id` exists, use it, otherwise use the supplied ID.
- Use Parallel Task API directly with `curl`:
  - Create run: `POST https://api.parallel.ai/v1/tasks/runs`
  - Retrieve result: `GET https://api.parallel.ai/v1/tasks/runs/<run_id>/result?timeout=600`
- Use processor `core` by default.
- Enforce output shape at task creation by sending:
  - `task_spec.output_schema.type = "json"`
  - `task_spec.output_schema.json_schema = data/schema-tradable-tickers-output.json`
- Remove schema metadata keys unsupported or unnecessary for Task API before sending the schema, at minimum `"$schema"` and `title`.
- Save:
  - raw create response as `<filename>.create.json`
  - raw result response as `<filename>.result.json`
  - extracted JSON payload as `<filename>.payload.json`
  - readable summary as `<filename>.md`
- Validate `<filename>.payload.json` with `npx --yes ajv-cli validate --spec=draft2020 --all-errors --errors=text`.
- Import validated `ticker_opportunities[]` into `Trading Proposals` only after the `Research Runs` row is created and after a separate confirmation gate.
- Never infer confirmation from Cloud Agent, background execution, or non-interactive execution alone. Only skip a confirmation gate when the original user request includes the matching explicit flag below.

## Inputs

- `interaction_id` or `run_id`: Required. The user may provide a `trun_...`; resolve it with `parallel-cli research status` if possible.
- Optional auto-confirm flags:
  - `--yes-start-research`: Treat as explicit confirmation for starting the external Parallel Task API follow-up run.
  - `--yes-create-research-run`: Treat as explicit confirmation for creating the linked Notion `Research Runs` row.
  - `--yes-create-trade-proposals`: Treat as explicit confirmation for creating Notion `Trading Proposals` rows from validated output.
- Optional source context if needed:
  - source `Research Runs` page ID
  - source `Research Ideas` page ID
  - idea title or enough information to identify the related idea

## Auto-Confirm Rules

- Auto-confirm flags must be present in the user's original skill invocation or latest explicit instruction for this run. Do not assume them from context, Cloud Agent mode, background execution, or prior unrelated approvals.
- Each flag only applies to its matching gate:
  - `--yes-start-research` applies only to external Parallel Task API kickoff.
  - `--yes-create-research-run` applies only to creating the Notion `Research Runs` row.
  - `--yes-create-trade-proposals` applies only to creating Notion `Trading Proposals` rows.
- If a flag is absent and interactive confirmation is unavailable, stop at that gate and report the prepared preview.
- Even with flags, stop instead of writing if validation fails, required Notion schema fields are missing, select values are unavailable, the related idea cannot be resolved, or duplicate proposal rows require a user choice.
- Do not use a blanket `--yes`; this skill intentionally requires scoped approvals.

## Steps

1. Load guidance and prompt sources:
   - Read `AGENTS.md`.
   - Read `.agents/skills/notion-api/SKILL.md`.
   - Read `data/prompt-followup-tradable-tickers.md`.
   - Read `data/schema-tradable-tickers-output.json`.
   - Follow workspace safety and confirmation rules.

2. Validate auth and tools without exposing secrets:
   - Check `PARALLEL_API_KEY` from environment first, then `.env` if needed.
   - Check `NOTION_API_TOKEN` from environment first, then `.env` if needed.
   - Confirm `curl`, `jq`, and `npx` are available.
   - Confirm `parallel-cli` is available only for optional prior-run status resolution; do not use it to create the follow-up run.
   - Use `npx --yes ajv-cli ...` for validation; no project dependency is required.
   - Do not print raw token values.

3. Resolve the supplied Parallel ID:
   - Prefer:

```bash
parallel-cli research status "$INPUT_ID" --json
```

   - Extract:
     - `run_id`
     - `interaction_id`
     - `status`
     - result or monitoring URL if present
   - If `interaction_id` is present, use it as `INTERACTION_ID`.
   - If `interaction_id` is absent but the input is a `trun_...`, use the input as `INTERACTION_ID`.
   - If status lookup fails, continue only if the supplied ID is clearly intended as a prior Parallel interaction ID and Notion can resolve a matching source run.

4. Resolve the related Notion idea before writing:
   - Locate `Research Runs` and `Research Ideas` data sources.
   - Resolve schemas and property IDs.
   - Required `Research Runs` fields:
     - `Run ID` title
     - `Idea` relation to `Research Ideas`
     - `Status`
     - `Previous Interaction ID`
     - `Started At`
     - `Prompt Used`
   - Strongly recommended `Research Runs` fields:
     - `Completed At`
     - `Result URL`
     - `Executive Summary`
     - `Error Message`
     - `Result MD Path`
     - `Result JSON Path`
   - If `Processor` exists, validate that the `core` select option is available before writing. If it is missing, do not alter schema automatically; ask whether to add the option or omit the `Processor` property from the write.
   - If a source run or idea is supplied, use it to resolve the `Idea` relation.
   - If only the Parallel ID is supplied, search `Research Runs` in this order:
     1. `Run ID` title equals the supplied ID.
     2. `Previous Interaction ID` equals the supplied ID.
     3. Any known stored interaction reference field, if present.
   - If the related idea cannot be resolved, stop and ask the user for the source `Research Runs` page or `Research Ideas` page. Do not create an unlinked run row.

5. Resolve `Trading Proposals` before running external research:
   - Locate the `Trading Proposals` data source. If exact search fails, also try `Trade Proposals` and `Proposals`.
   - Resolve property IDs by exact name.
   - Required `Trading Proposals` fields:
     - `Proposal` title
     - `Ticker` rich_text
     - `Company Name` rich_text
     - `Asset Class` select
     - `Market` select
     - `Exchange` rich_text
     - `Currency` rich_text
     - `Relationship To Research` rich_text
     - `Trade Type` select
     - `Time Horizon` select
     - `Rationale` rich_text
     - `Entry Criteria` rich_text
     - `Exit Criteria` rich_text
     - `Key Invalidation Event` rich_text
     - `Conviction Level` select
     - `Risk Bucket` select
     - `Assumptions` rich_text
     - `Open Questions` rich_text
     - `Monitoring Signals` rich_text
     - `Status` select
     - `Proposed At` date
     - `Run` relation
     - `Idea` relation
   - Optional but preferred `Trading Proposals` fields:
     - `Schema Version`
     - `Previous Interaction ID`
     - `Core Thesis`
     - `Key Drivers`
     - `Key Risks`
     - `Thesis Kill Criteria`
     - `Fact Assumption Boundary`
     - `Missing Information`
     - `Uncertainty Notes`
     - `Conviction Score`
     - `Conviction Note`
     - `Other Trade Type`
     - `Review Notes`
   - Do not alter the Notion schema inside this skill unless separately confirmed.

6. Build the follow-up prompt and schema:
   - Use `data/prompt-followup-tradable-tickers.md` as the instruction source.
   - Include the resolved `INTERACTION_ID`.
   - Default `focus_markets` to `HK`, `JP`, and `US`.
   - Default `analysis_timeframe` to `mixed`.
   - Keep the input focused on the research task; schema enforcement belongs in `task_spec.output_schema`, not only in prompt text.
   - Do not provide personalized investment advice, position sizing, or trade execution instructions.
   - Prepare the Task API JSON schema with:

```bash
SCHEMA_JSON="$(jq 'del(."$schema", .title)' data/schema-tradable-tickers-output.json)"
```

7. Confirmation gate before external research:
   - Summarize:
     - input ID and resolved `INTERACTION_ID`
     - resolved source idea/page
     - processor choice, default `core`
     - that `previous_interaction_id` will be sent to the Task API
     - that `task_spec.output_schema` will use `data/schema-tradable-tickers-output.json`
     - intended output filenames
     - that `ajv-cli` will validate the extracted `output.content` before Notion proposal imports
   - If `--yes-start-research` was supplied, record that the gate was auto-confirmed by flag and continue.
   - Otherwise, ask for explicit confirmation before starting the Parallel Task API follow-up run.

8. Start the follow-up run with Task API:
   - Use `core` by default.
   - Build request JSON with `jq`; never interpolate secrets into visible logs.

```bash
REQUEST_JSON="$(jq -n \
  --arg input "$FOLLOWUP_PROMPT" \
  --arg prev "$INTERACTION_ID" \
  --argjson schema "$SCHEMA_JSON" \
  '{
    input: $input,
    processor: "core",
    previous_interaction_id: $prev,
    task_spec: {
      output_schema: {
        type: "json",
        json_schema: $schema
      }
    }
  }')"

curl -sS "https://api.parallel.ai/v1/tasks/runs" \
  -H "x-api-key: ${PARALLEL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_JSON" > "$FILENAME.create.json"
```

   - Capture:
     - new `run_id`
     - new `interaction_id`
     - status
     - created timestamp if returned
   - If the create response contains `error`, stop and report the concise error message.
   - Immediately report kickoff metadata to the user.

9. Retrieve and save the structured result:
   - Poll by repeatedly calling the blocking result endpoint with short enough timeouts to stay responsive:

```bash
curl -sS "https://api.parallel.ai/v1/tasks/runs/${RUN_ID}/result?timeout=600" \
  -H "x-api-key: ${PARALLEL_API_KEY}" \
  -H "Content-Type: application/json" > "$FILENAME.result.json"
```

   - If the endpoint returns HTTP 408 or an error indicating the run is still active, report that it is still running and do not write terminal Notion status.
   - On completion, expect:
     - `.output.type` equals `json`
     - `.output.content` is the schema-constrained JSON object
   - Save the payload:

```bash
jq '.output.content' "$FILENAME.result.json" > "$FILENAME.payload.json"
```

   - Create a concise readable summary file:

```bash
jq -r '
  "# Follow-up Tradable Tickers\n\n" +
  "- Run ID: " + (.run.run_id // "") + "\n" +
  "- Interaction ID: " + (.run.interaction_id // "") + "\n" +
  "- Output type: " + (.output.type // "") + "\n" +
  "- Ticker count: " + ((.output.content.ticker_opportunities // []) | length | tostring) + "\n"
' "$FILENAME.result.json" > "$FILENAME.md"
```

10. Validate ticker JSON:
   - Validate the extracted payload:

```bash
npx --yes ajv-cli validate \
  --spec=draft2020 \
  --all-errors \
  --errors=text \
  -s data/schema-tradable-tickers-output.json \
  -d "$FILENAME.payload.json"
```

   - If validation fails, stop. Do not write `Research Runs` or `Trading Proposals`.
   - If validation passes, summarize:
     - schema version
     - ticker count
     - ticker list
     - markets
     - asset classes
     - `output_quality.fact_assumption_boundary`
     - missing information count
     - uncertainty notes count

11. Summarize output for Notion:
   - Create a concise `Executive Summary` for Notion:
     - number of ticker opportunities
     - markets and asset classes covered
     - highest-level uncertainty notes
     - location of local result files
   - Do not paste raw JSON payloads into Notion.

12. Prepare `Research Runs` write plan:
   - Create a new `Research Runs` row linked to the resolved `Research Ideas` page.
   - Populate fields when present:
     - `Run ID` = new follow-up `run_id`
     - `Idea` = resolved idea relation
     - `Status` = `Completed`, `Failed`, or `Running`
     - `Processor` = `core` only if the field exists and the option is available
     - `Started At` = kickoff timestamp or create response timestamp
     - `Completed At` = completion timestamp if terminal
     - `Result URL` = result URL when available, otherwise omit
     - `Prompt Used` = follow-up prompt submitted
     - `Executive Summary` = concise summary only
     - `Previous Interaction ID` = input `interaction_id`
     - `Error Message` = concise failure reason if failed
     - `Result MD Path` = local `.md` path if field exists
     - `Result JSON Path` = local `.result.json` path if field exists
   - Do not update the original source run row unless the user explicitly asks.
   - Do not alter Notion schema inside this skill unless separately confirmed.

13. Confirmation gate before `Research Runs` write:
   - Show target data source name and ID.
   - Show target idea page and ID.
   - Show the exact new row fields that will be created.
   - If `--yes-create-research-run` was supplied, record that the gate was auto-confirmed by flag and continue.
   - Otherwise, ask for explicit confirmation before creating the `Research Runs` row.

14. Execute `Research Runs` write after confirmation:
   - Use Notion REST API via `curl`.
   - Use property IDs for writes when available.
   - Handle errors gracefully and do not expose secrets.
   - Capture the created follow-up `Research Runs` page ID. This page ID is required for `Trading Proposals.Run` relations.

15. Prepare `Trading Proposals` import plan:
   - Query `Trading Proposals` for rows where `Run` relation contains the newly created follow-up `Research Runs` page ID.
   - If existing rows are found for this run, do not blindly duplicate them. Report existing count/tickers and ask whether to skip, append only missing tickers, or stop.
   - Default import mapping for each `ticker_opportunities[]` item:
     - `Proposal` title: `<ticker> <trade_type> - follow-up tradable tickers`
     - `Ticker`: `ticker`
     - `Company Name`: `company_name`
     - `Asset Class`: `asset_class`
     - `Market`: `market`
     - `Exchange`: `exchange`
     - `Currency`: `currency`
     - `Relationship To Research`: `relationship_to_research`
     - `Trade Type`: `trade_hypothesis.trade_type`
     - `Other Trade Type`: `trade_hypothesis.other_trade_type`
     - `Time Horizon`: `trade_hypothesis.time_horizon`
     - `Rationale`: `trade_hypothesis.rationale`
     - `Entry Criteria`: bullet-joined `trade_hypothesis.entry_criteria`
     - `Exit Criteria`: bullet-joined `trade_hypothesis.exit_criteria`
     - `Key Invalidation Event`: `trade_hypothesis.key_invalidation_event`
     - `Conviction Level`: `trade_hypothesis.conviction_level`
     - `Conviction Score`: `trade_hypothesis.conviction_score`
     - `Conviction Note`: `trade_hypothesis.conviction_note`
     - `Risk Bucket`: `trade_hypothesis.risk_bucket`
     - `Assumptions`: bullet-joined `assumptions`
     - `Open Questions`: bullet-joined `open_questions`
     - `Monitoring Signals`: bullet-joined `monitoring_signals`
     - `Schema Version`: `schema_version`
     - `Previous Interaction ID`: input/resolved previous `INTERACTION_ID`
     - `Core Thesis`: `thesis_snapshot.core_thesis`
     - `Key Drivers`: bullet-joined `thesis_snapshot.key_drivers`
     - `Key Risks`: bullet-joined `thesis_snapshot.key_risks`
     - `Thesis Kill Criteria`: bullet-joined `thesis_snapshot.thesis_kill_criteria`
     - `Fact Assumption Boundary`: `output_quality.fact_assumption_boundary`
     - `Missing Information`: bullet-joined `output_quality.missing_information`
     - `Uncertainty Notes`: bullet-joined `output_quality.uncertainty_notes`
     - `Status`: `Proposed`
     - `Proposed At`: current UTC timestamp
     - `Run`: relation to the newly created follow-up `Research Runs` page
     - `Idea`: relation to the resolved `Research Ideas` page
     - `Review Notes`: `Imported from ajv-cli-validated Parallel Task API schema-constrained output. Research framing only, not personalized investment advice.`
   - Use Notion rich_text chunks below 2000 characters.
   - Validate that select values exist in the target schema before writing. If a select value is missing, stop and ask before changing schema or writing partial data.

16. Confirmation gate before `Trading Proposals` writes:
   - Show:
     - target `Trading Proposals` data source name and ID
     - follow-up `Research Runs` page ID
     - linked `Research Ideas` page ID
     - number of rows to create
     - ticker list
     - status value (`Proposed`)
     - exact high-level field mapping
   - If `--yes-create-trade-proposals` was supplied, record that the gate was auto-confirmed by flag and continue.
   - Otherwise, ask for explicit confirmation before creating `Trading Proposals` rows.

17. Execute `Trading Proposals` writes after confirmation:
   - Create one Notion page per ticker opportunity.
   - Process sequentially.
   - Continue on per-row errors and collect failures.
   - Do not update, archive, or delete existing proposal rows unless the user explicitly confirms that separate action.
   - After writes, query `Trading Proposals` by `Run` relation to verify created count and ticker list.

18. Final report:
   - Input ID and resolved previous `INTERACTION_ID`
   - New follow-up `run_id`
   - New follow-up `interaction_id`
   - Task API schema-constrained output status
   - `ajv-cli` validation result
   - `Research Runs` row created/skipped/failed
   - `Trading Proposals` rows created/skipped/failed and ticker list
   - Which confirmation gates were interactive versus auto-confirmed by flags
   - Local result file paths
   - Concise error details for any failures
