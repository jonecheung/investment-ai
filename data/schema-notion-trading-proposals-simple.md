# Notion Trading Proposals Schema

Snapshot date: 2026-06-06

This document is the **canonical** Notion database schema for tradable ticker proposals. It supersedes the `Trading Proposals` section in `data/schema-notion-research.md`.

Layer 1 import source: `data/schema-tradable-tickers-output.json` (`ticker_opportunities[]` items).

Related schema: `data/schema-notion-portfolio.md` (Layer 3 sizing and execution history).

## Ground Rules

- **In scope:** `Trading Proposals` database only.
- **Out of scope:** `Research Ideas`, `Research Runs`, and all other databases. No schema or property changes to those tables as part of this document.
- **Design rule:** Proposal rows store ticker-specific review and pricing-geometry fields. Run-level and thesis-level context is accessed through linked `Run` and `Idea` relations, not duplicated on each proposal row.
- **Import source:** One Notion row represents one `ticker_opportunities[]` item (Layer 1 only).
- **Framing:** Trade-plan framing for human review and monitoring. Not automated trade execution.

## Three-Layer Model

| Layer | Purpose | Where stored |
| --- | --- | --- |
| Layer 1 | Qualitative hypothesis from research import | `Trading Proposals` — identity, rationale, watchpoints, invalidation |
| Layer 2 | Pricing geometry | `Trading Proposals` — last close, entry/stop/target, R:R per unit |
| Layer 3 | Portfolio sizing | `Proposal Sizing` in `data/schema-notion-portfolio.md` — quantity, notional, max loss |

Handoffs:

1. Research follow-up imports Layer 1 fields.
2. Alpha Vantage last close populates `Last Price` and `Quote As Of`.
3. An external process (out of repo scope) populates entry/stop/target levels and sets `Pricing Status`.
4. Portfolio sizing creates a `Proposal Sizing` row when Layer 2 is ready.
5. Manual execution creates a `Trades` row linked to sizing output.

Layer 2 does **not** store quantity, notional, portfolio weight, or max loss in dollars. Those belong in Layer 3.

## Changes From Original Full Schema

The original full schema (`schema-notion-research.md`) defined 35 `Trading Proposals` properties. This target schema removes run/thesis duplication, consolidates related review fields, and keeps high-value per-ticker fields.

### Removed — Run / Thesis Context (Do Not Store On Proposals)

These fields existed on the original full `Trading Proposals` table. They are removed from proposals. Access them through existing linked run/idea pages and external result URLs.

| Removed property | Original JSON / purpose | Where context lives instead |
| --- | --- | --- |
| `Schema Version` | `schema_version` | Linked `Research Runs` row and/or local result files |
| `Previous Interaction ID` | follow-up context | Linked `Research Runs.Previous Interaction ID` (unchanged) |
| `Core Thesis` | `thesis_snapshot.core_thesis` | Linked `Research Ideas` / run summary |
| `Key Drivers` | `thesis_snapshot.key_drivers[]` | Linked `Research Ideas` / run summary |
| `Key Risks` | `thesis_snapshot.key_risks[]` | Linked `Research Ideas` / run summary |
| `Thesis Kill Criteria` | `thesis_snapshot.thesis_kill_criteria[]` | Linked `Research Ideas` / run summary |
| `Fact Assumption Boundary` | `output_quality.fact_assumption_boundary` | Run summary / external result |
| `Missing Information` | `output_quality.missing_information[]` | Run summary / external result |
| `Uncertainty Notes` | `output_quality.uncertainty_notes[]` | Run summary / external result |

### Removed — Consolidated Into Fewer Proposal Fields

| Removed property | Replaced by | Notes |
| --- | --- | --- |
| `Entry Criteria` | `Watchpoints` | Section 1 in sectioned bullet-join |
| `Monitoring Signals` | `Watchpoints` | Section 2 |
| `Open Questions` | `Watchpoints` | Section 3 |
| `Exit Criteria` | `Invalidation` | Bullet list after invalidation event |
| `Key Invalidation Event` | `Invalidation` | Leading text before exit bullets |
| `Conviction Level` | `Conviction` | Renamed; same select options |

### Removed — Low-Value Per-Ticker Duplication

| Removed property | Notes |
| --- | --- |
| `Other Trade Type` | When `Trade Type` is `other`, fold clarification into `Rationale` |
| `Conviction Score` | Optional numeric score; not needed for proposal review queue |
| `Conviction Note` | Fold into `Rationale` or `Review Notes` at import time if needed |

### Kept From Original Full Schema

| Property | Reason |
| --- | --- |
| `Exchange` | Per-ticker venue; not recoverable from run-level fields |
| `Currency` | Per-ticker quote/trading currency |
| `Risk Bucket` | Per-ticker classification; useful for Notion filtering |

## Current Status — Target Trading Proposals Schema

**Property count:** 39 (21 Layer 1 + 4 workflow + 14 Layer 2 pricing)

Purpose: reviewable, price-enriched ticker-level trade plans linked to a research run and source idea.

### Layer 1 — Qualitative

| Property | Type | Notes |
| --- | --- | --- |
| `Proposal` | title | Human-readable label, typically `<ticker> <trade_type>`. |
| `Ticker` | rich_text | Tradable symbol or instrument identifier from research. |
| `Instrument ID` | rich_text | Broker-validated symbol; may be filled during review. |
| `Company Name` | rich_text | Company, ETF, asset, or instrument name. |
| `Market` | select | `HK`, `JP`, `US`, `OTHER`. |
| `Asset Class` | select | `equity`, `etf`, `bond`, `future`, `option`, `crypto`, `other`. |
| `Exchange` | rich_text | Trading venue or exchange. |
| `Currency` | rich_text | Trading or quote currency. |
| `Intent` | select | `Trade`, `Watchlist`, `Hedge`. |
| `Trade Type` | select | `long`, `short`, `other`. |
| `Time Horizon` | select | `near_term`, `medium_term`, `long_term`, `event_driven`, `unspecified`. |
| `Conviction` | select | `low`, `medium`, `high`. |
| `Risk Bucket` | select | `fundamental`, `event_driven`, `macro_sensitive`, `policy_sensitive`, `supply_chain`, `other`. |
| `Relationship To Research` | rich_text | Free-text causal link to the source thesis. |
| `Rationale` | rich_text | Core research hypothesis and reasoning. Include `other_trade_type` text when applicable. |
| `Invalidation` | rich_text | Main thesis-break event and exit or downgrade logic. |
| `Assumptions` | rich_text | Key assumptions behind the proposal. |
| `Watchpoints` | rich_text | Entry triggers, monitoring signals, and open questions. |
| `Status` | select | Human review state. `Proposed`, `Reviewing`, `Accepted`, `Rejected`, `Archived`. |
| `Proposed At` | date | Timestamp when imported or created. |
| `Run` | relation | Relation to Research Runs. |
| `Idea` | relation | Relation to Research Ideas. |
| `Review Notes` | rich_text | User notes during review. |

### Workflow Status Fields

| Property | Type | Notes |
| --- | --- | --- |
| `Pricing Status` | select | Layer 2 readiness. `Not Started`, `Pending`, `Ready`, `Failed`, `Stale`. |
| `Sizing Status` | select | Layer 3 summary mirror. `Not Applicable`, `Pending`, `Ready`, `Skipped`, `Stale`. Canonical sizing row lives in `Proposal Sizing`. |

### Layer 2 — Pricing Geometry

| Property | Type | Source | Notes |
| --- | --- | --- | --- |
| `Quote As Of` | date | Alpha Vantage | Last-close date. |
| `Last Price` | number | Alpha Vantage | Last close in quote currency. |
| `Entry Type` | select | External process | `limit_zone`, `breakout`, `pullback`, `market_plan`. |
| `Entry Low` | number | External process | Lower bound of entry zone. |
| `Entry High` | number | External process | Upper bound; same as low for single limit. |
| `Entry Reference` | number | Derived | Mid of zone or chosen reference for R calculations. |
| `Stop Price` | number | External process | Hard invalidation price. |
| `Target 1` | number | External process | Primary take-profit. |
| `Target 2` | number | External process | Optional secondary target. |
| `Risk Per Unit` | number | Derived | \|entry reference − stop\| in quote currency. |
| `Reward Per Unit` | number | Derived | \|target 1 − entry reference\| in quote currency. |
| `Reward Risk Ratio` | number | Derived | reward per unit / risk per unit. |
| `Plan Valid Until` | date | External process | Staleness cutoff for the price plan. |
| `Pricing Notes` | rich_text | External process | Metadata, liquidity, catalyst notes. |

### Trading Proposals Relations

- `Trading Proposals.Run`
  - Type: relation
  - Target: Research Runs
- `Trading Proposals.Idea`
  - Type: relation
  - Target: Research Ideas

## Status Workflow

Keep human decision workflow (`Status`) separate from machine readiness (`Pricing Status`, `Sizing Status`).

| Stage | Status | Pricing Status | Sizing Status |
| --- | --- | --- | --- |
| Layer 1 import | `Proposed` | `Not Started` | `Not Applicable` |
| Human review | `Reviewing` | unchanged | unchanged |
| Accepted for pricing | `Accepted` | `Pending` | `Not Applicable` |
| Alpha Vantage last close | unchanged | unchanged | unchanged |
| External pricing complete | unchanged | `Ready` | `Pending` |
| Proposal Sizing row created | unchanged | unchanged | `Ready` |
| Sizing skipped or rejected | unchanged | unchanged | `Skipped` |
| Plan expired or large price move | unchanged | `Stale` and/or | `Stale` |

## Layer 2 Data Sources

| Field group | Source | Tool / process |
| --- | --- | --- |
| `Last Price`, `Quote As Of` | Alpha Vantage last close | `alphavantage-curl` skill |
| `Entry Type`, `Entry Low`, `Entry High`, `Stop Price`, `Target 1`, `Target 2`, `Plan Valid Until`, `Pricing Notes` | External process | Out of repo scope; sets `Pricing Status` |
| `Entry Reference`, `Risk Per Unit`, `Reward Per Unit`, `Reward Risk Ratio` | Derived | Computed after external levels are set |

Layer 2 is **not** imported from `schema-tradable-tickers-output.json`.

## Layer 2 to Layer 3 Preconditions

Before creating a `Proposal Sizing` row (see `data/schema-notion-portfolio.md`):

- `Status` = `Accepted`
- `Pricing Status` = `Ready`
- Required pricing fields populated: `Entry Reference`, `Stop Price`, `Target 1`
- Linked `Account` selected for sizing
- Portfolio inputs available: NAV, cash, and position context from `Accounts` / `Position Snapshots` or approved manual inputs

## JSON Import Mapping (Layer 1 Only)

For each `ticker_opportunities[]` item:

| Notion property | JSON path | Transform |
| --- | --- | --- |
| `Proposal` | `ticker`, `trade_hypothesis.trade_type` | `"<ticker> <trade_type>"` |
| `Ticker` | `ticker` | direct |
| `Company Name` | `company_name` | direct |
| `Market` | `market` | direct |
| `Asset Class` | `asset_class` | direct |
| `Exchange` | `exchange` | direct |
| `Currency` | `currency` | direct |
| `Trade Type` | `trade_hypothesis.trade_type` | direct |
| `Time Horizon` | `trade_hypothesis.time_horizon` | direct |
| `Conviction` | `trade_hypothesis.conviction_level` | direct |
| `Risk Bucket` | `trade_hypothesis.risk_bucket` | direct |
| `Relationship To Research` | `relationship_to_research` | direct |
| `Rationale` | `trade_hypothesis.rationale`, `trade_hypothesis.other_trade_type` | rationale first; append other trade type when non-null |
| `Invalidation` | `trade_hypothesis.key_invalidation_event`, `trade_hypothesis.exit_criteria[]` | invalidation first, then bullet exits |
| `Assumptions` | `assumptions[]` | bullet-join |
| `Watchpoints` | `trade_hypothesis.entry_criteria[]`, `monitoring_signals[]`, `open_questions[]` | sectioned bullet-join |
| `Status` | n/a | `Proposed` |
| `Pricing Status` | n/a | `Not Started` |
| `Sizing Status` | n/a | `Not Applicable` |
| `Proposed At` | n/a | current UTC timestamp |
| `Run` | n/a | relation to follow-up run page |
| `Idea` | n/a | relation to source idea page |

Do **not** import these JSON sections onto proposal rows: `schema_version`, `analysis_context.*`, `thesis_snapshot.*`, `output_quality.*`.

If `ticker_opportunities` is empty, create no proposal rows. Record gaps through the linked run workflow using existing `Research Runs` fields and external result files.

## Reconstruction Order

Applies to `Trading Proposals` only:

1. Ensure `Research Ideas` and `Research Runs` already exist (no changes required).
2. Open or create the `Trading Proposals` database.
3. Remove obsolete properties listed in **Removed** sections above, if present.
4. Add or rename Layer 1 qualitative properties listed above.
5. Add workflow properties: `Instrument ID`, `Intent`, `Pricing Status`, `Sizing Status`.
6. Add Layer 2 pricing properties listed above.
7. Configure all select options exactly as listed.
8. Confirm `Trading Proposals.Run` relation to `Research Runs`.
9. Confirm `Trading Proposals.Idea` relation to `Research Ideas`.
