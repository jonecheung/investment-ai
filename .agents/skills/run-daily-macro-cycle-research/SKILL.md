---
name: run-daily-macro-cycle-research
description: Start the scheduled daily macro-cycle Parallel deep research run before the European trading session and log kickoff metadata in Notion.
disable-model-invocation: true
---

# Run Daily Macro Cycle Research

Start the standardized macro-cycle regime scan from `Research Ideas`, submit it to Parallel research, and log kickoff metadata in `Research Runs`.

This skill is intended for scheduled automation. Kickoff and polling are separate:

- `scripts/run.sh` starts a run and logs kickoff metadata.
- `scripts/poll.sh` polls running Notion records and syncs completed summaries.

## Safety

- Research only. No trade execution, order placement, or money movement.
- Do not print or persist `NOTION_API_TOKEN` or `PARALLEL_API_KEY`.
- Do not store raw research JSON in Notion.
- The prompt template is stored in `data/prompts/macro-cycle-regime-scan.md`.

## Required Environment

- `NOTION_API_TOKEN`
- `PARALLEL_API_KEY`

Optional:

- `PARALLEL_PROCESSOR` defaults to `base`
- `MACRO_RESEARCH_IDEA_TITLE` defaults to `Daily Macro Cycle Regime Scan Before EU Session`
- `MACRO_PROMPT_PATH` defaults to `data/prompts/macro-cycle-regime-scan.md`

## Manual Run

```bash
bash .agents/skills/run-daily-macro-cycle-research/scripts/run.sh
```

## What It Does

1. Resolves Notion data sources:
   - `Research Ideas`
   - `Research Runs`
2. Ensures the macro-cycle research idea exists in `Research Ideas`.
3. Stores the standardized prompt in `Research Ideas.Research Input`.
4. Starts a Parallel deep research run with `--no-wait`.
5. Creates a linked `Research Runs` row with:
   - `Run ID`
   - `Idea`
   - `Status = Running`
   - `Processor`
   - `Started At`
   - `Result URL`
   - `Prompt Used`
6. Updates the source `Research Ideas` row with:
   - `Status = Running`
   - `Last Run ID`
   - `Last Run At`

## Manual Poll

```bash
bash .agents/skills/run-daily-macro-cycle-research/scripts/poll.sh
```

Polling updates completed runs in `Research Runs` and their linked `Research Ideas` with:

- `Status = Completed`
- `Completed At`
- `Executive Summary`

## Scheduling

The paired GitHub Actions workflow runs Monday-Friday at 06:30 UTC, before the European trading session. It performs both parts in one run:

1. Start the new macro-cycle research run.
2. Poll running research records and sync any completed summaries back to Notion.

If a research run takes longer than the poll timeout, it remains `Running` in Notion and will be picked up by the next scheduled/manual workflow run. This approximates trading days by weekday; market holidays are not filtered unless the workflow is extended with a holiday calendar.
