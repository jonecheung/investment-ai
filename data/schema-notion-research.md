# Notion Research Database Schema v1

Snapshot date: 2026-05-02

This document defines the database schema needed to reconstruct the Notion research system without copying any data. It includes database names, property names, property types, select options, relation setup, and rollup setup only.

## Scope

- Databases covered:
  - Research Ideas
  - Research Runs
- Excluded:
  - Page IDs, database IDs, data source IDs, property IDs, URLs, commands, prompts, raw rows, and workspace-specific artifacts.

## Research Ideas

Purpose: planning backlog and opportunity pipeline.

| Property | Type | Notes |
| --- | --- | --- |
| `Original Idea` | title | User-entered raw idea. Minimal input field. |
| `Idea ID` | unique_id | Stable generated identifier. Prefix: `RI`. |
| `Research Input` | rich_text | Expanded, research-ready prompt/input for execution. |
| `Status` | select | Lifecycle state. Current options: `New`, `Expanded`, `Queued`, `Running`, `Completed`. |
| `Active` | checkbox | Controls scheduler eligibility. |
| `Run Frequency` | select | Recurrence cadence. Current options: `Once`, `Daily`, `Weekly`, `Biweekly`, `Monthly`, `Quarterly`. |
| `Market Tags` | multi_select | Market scope labels. Current options: `HK`, `JP`, `US`, `CN`, `Global`. |
| `Asset Type Tags` | multi_select | Asset class labels. Current options: `Equity`, `ETF`, `Derivatives`, `Crypto`, `FX`. |
| `Strategy Tags` | multi_select | Strategy/theme labels. Current options: `Momentum`, `Contrarian`, `Macro`, `Flow`, `Event-driven`. |
| `Last Run ID` | rich_text | Most recent provider run ID linked to this idea. |
| `Last Run At` | date | Timestamp of latest completed run for this idea. |
| `Executive Summary` | rich_text | Latest summary synced back from the most recent completed run. |
| `Last Updated` | date | Workflow-maintained update timestamp, if used. |

## Research Runs

Purpose: execution log and audit trail for research runs. Each row represents one provider run event.

| Property | Type | Notes |
| --- | --- | --- |
| `Run ID` | title | Primary row identifier. Store the provider run ID, for example `trun_...`. |
| `Idea` | relation | Relation to Research Ideas. Each run should link to its source idea. |
| `Idea ID` | rollup | Rolls up Research Ideas `Idea ID` through the `Idea` relation. Function: `show_original`. |
| `Status` | select | Execution state. Current options: `Queued`, `Running`, `Completed`, `Failed`, `Cancelled`. |
| `Processor` | select | Provider processor tier. Current options: `lite`, `pro-fast`, `ultra-fast`, `ultra`. |
| `Started At` | date | Timestamp when run was submitted or started. |
| `Completed At` | date | Timestamp when run reached a terminal state. |
| `Result URL` | url | External result or monitoring URL for the provider run. |
| `Prompt Used` | rich_text | Exact prompt submitted for this run. |
| `Executive Summary` | rich_text | Run-level executive summary. |
| `Previous Interaction ID` | rich_text | Prior provider interaction ID supplied only for follow-up runs. Blank for first-pass runs. |
| `Error Message` | rich_text | Failure or cancellation details. |

### Research Runs Relation And Rollup

- `Research Runs.Idea`
  - Type: relation
  - Target: Research Ideas
- `Research Runs.Idea ID`
  - Type: rollup
  - Relation property: `Idea`
  - Related property: `Idea ID`
  - Function: `show_original`

## Reconstruction Order

1. Create a database named `Research Ideas`.
2. Add the `Research Ideas` properties listed above.
3. Configure `Research Ideas.Idea ID` as a unique ID with prefix `RI`.
4. Create a database named `Research Runs`.
5. Add the non-relation `Research Runs` properties listed above.
6. Add `Research Runs.Idea` as a relation to `Research Ideas`.
7. Add `Research Runs.Idea ID` as a rollup:
   - Relation property: `Idea`
   - Related property: `Idea ID`
   - Function: `show_original`

