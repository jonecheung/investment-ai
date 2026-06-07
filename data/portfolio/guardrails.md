# Portfolio Guardrails Schema

Snapshot date: 2026-06-07

This document defines how **portfolio guardrails** (hard limits, soft preferences, regime overrides) are stored in Notion and mirrored in the workspace template [`guardrails.yaml`](guardrails.yaml).

Guardrails are inputs to **Portfolio Analysis** (Layer 3). They are not part of the research or Trading Proposals schema.

Related:

- [`guardrails.yaml`](guardrails.yaml) — machine-readable template with initial suggested values
- [`../notion/portfolio.md`](../notion/portfolio.md) — portfolio snapshot, holdings, and analysis outputs
- [`../notion/research.md`](../notion/research.md) — `Trading Proposals` (Layer 1 + Layer 2)

## Purpose

Guardrails answer: **what portfolio shapes are allowed** when combining:

- latest **Approved Portfolio Snapshot** and **Portfolio Holdings**
- eligible `Trading Proposals`

They do **not** store trade execution history, rebalance execution status, or P&L settings.

## Design Notes

- **Single active policy:** one row (or page) marked `Active = true` at a time.
- **Versioning:** each material change creates a new row with `Effective Date`; analysis copies policy fields for audit.
- **Hard vs soft:** hard limits reject or clip allocations; soft preferences rank feasible outcomes.
- **YAML mirror:** `guardrails.yaml` is a draft/template for local skills; Notion is the intended runtime source once confirmed.
- Do not apply Notion structure changes without explicit confirmation.

## Notion: Portfolio Policy

Use either:

- **Option A (recommended):** database named `Portfolio Policy`
- **Option B:** a fixed Notion page with the properties below (singleton)

### Portfolio Policy Properties

#### Identity

| Property | Type | Notes |
| --- | --- | --- |
| `Policy` | title | e.g. `Default`, `2026 Q2 Tactical` |
| `Status` | select | `draft`, `active`, `archived` |
| `Active` | checkbox | Only one row should be checked at a time |
| `Effective Date` | date | When this policy becomes authoritative |
| `Base Currency` | select | `HKD`, `USD`, `JPY`, `CNY`, `OTHER` |
| `Schema Version` | number | Match `guardrails.yaml` `schema_version` |
| `Notes` | rich_text | Human policy context (IPS summary, rationale) |

#### Hard Limits — Concentration

| Property | Type | Suggested starter | Notes |
| --- | --- | --- | --- |
| `Max Single Holding Pct` | number | 12 | Max target weight for one ticker (%) |
| `Max Holdings Count` | number | 10 | Max non-cash positions |

#### Hard Limits — Cash

| Property | Type | Suggested starter | Notes |
| --- | --- | --- | --- |
| `Min Cash Pct` | number | 5 | Minimum cash weight in target portfolio (%) |
| `Max Cash Pct` | number | 35 | Maximum cash weight (%) |

#### Hard Limits — Risk at Stop

| Property | Type | Suggested starter | Notes |
| --- | --- | --- | --- |
| `Max Risk Per Proposal Pct` | number | 1.5 | Max NAV loss at stop for one line (%) |
| `Max Portfolio Heat Pct` | number | 6 | Sum of position risks at stop / NAV (%) |
| `Min Reward Risk Ratio` | number | 2 | Aligns with `Trading Proposals.Reward Risk Ratio` |
| `Max Turnover Pct` | number | 25 | Optional cap on one analysis turnover (%) |

#### Hard Limits — Market Exposure

| Property | Type | Suggested starter | Maps to |
| --- | --- | --- | --- |
| `Max HK Exposure Pct` | number | 50 | `Market` = HK |
| `Max JP Exposure Pct` | number | 30 | `Market` = JP |
| `Max US Exposure Pct` | number | 70 | `Market` = US |
| `Max Other Exposure Pct` | number | 15 | `Market` = OTHER |

#### Hard Limits — Asset Class (optional)

| Property | Type | Suggested starter | Maps to |
| --- | --- | --- | --- |
| `Max Equity Exposure Pct` | number | 90 | `Asset Class` = equity |
| `Max ETF Exposure Pct` | number | 40 | `Asset Class` = etf |
| `Max Crypto Exposure Pct` | number | 10 | `Asset Class` = crypto |

#### Soft Preferences

| Property | Type | Suggested starter | Notes |
| --- | --- | --- | --- |
| `Objective` | select | `maximize_conviction_weighted_reward_risk` | See **Objective options** |
| `Conviction Weight High` | number | 3 | Multiplier for `Conviction` = high |
| `Conviction Weight Medium` | number | 2 | Multiplier for medium |
| `Conviction Weight Low` | number | 1 | Multiplier for low |
| `Existing Position Bias` | number | 0.2 | 0–1; higher = less trimming of incumbents |
| `Max Positions Per Risk Bucket` | number | 4 | Soft cap on `Risk Bucket` count |
| `Max Positions Per Market Risk Bucket` | number | 2 | Soft cap on Market × Risk Bucket |

#### Regime Overrides

| Property | Type | Suggested starter | Notes |
| --- | --- | --- | --- |
| `Drawdown Trigger Pct` | number | 5 | Peak-to-current NAV decline trigger |
| `Drawdown Heat Multiplier` | number | 0.5 | Multiply `Max Portfolio Heat Pct` when triggered |
| `Drawdown Risk Multiplier` | number | 0.5 | Multiply per-proposal risk cap |
| `Drawdown Min Cash Floor Pct` | number | 10 | Raise min cash during drawdown |
| `Exclude Stale Pricing` | checkbox | true | Skip proposals with `Pricing Status` = Stale |
| `Exclude Watchlist Intent` | checkbox | true | Skip `Intent` = Watchlist |

#### Analyzer Inputs

| Property | Type | Suggested starter | Notes |
| --- | --- | --- | --- |
| `Require Proposal Status` | select | `Accepted` | Candidate pool filter |
| `Require Pricing Status` | select | `Ready` | Candidate pool filter |
| `Require Intent` | select | `Trade` | Candidate pool filter |
| `Sizing Method` | select | `risk_at_stop` | Primary sizing algorithm |

### Objective Options

| Value | Behavior |
| --- | --- |
| `maximize_conviction_weighted_reward_risk` | Prefer high conviction × high R/R proposals within guardrails |
| `minimize_turnover` | Prefer target closest to current Approved Portfolio Snapshot |
| `maximize_new_proposals` | Prefer adopting new candidates over trimming incumbents |

## YAML ↔ Notion Mapping

| `guardrails.yaml` path | Notion property |
| --- | --- |
| `base_currency` | `Base Currency` |
| `hard_limits.max_single_holding_pct` | `Max Single Holding Pct` |
| `hard_limits.max_holdings_count` | `Max Holdings Count` |
| `hard_limits.min_cash_pct` | `Min Cash Pct` |
| `hard_limits.max_cash_pct` | `Max Cash Pct` |
| `hard_limits.max_risk_per_proposal_pct` | `Max Risk Per Proposal Pct` |
| `hard_limits.max_portfolio_heat_pct` | `Max Portfolio Heat Pct` |
| `hard_limits.min_reward_risk_ratio` | `Min Reward Risk Ratio` |
| `hard_limits.max_turnover_pct` | `Max Turnover Pct` |
| `market_limits.HK.max_exposure_pct` | `Max HK Exposure Pct` |
| `market_limits.JP.max_exposure_pct` | `Max JP Exposure Pct` |
| `market_limits.US.max_exposure_pct` | `Max US Exposure Pct` |
| `market_limits.OTHER.max_exposure_pct` | `Max Other Exposure Pct` |
| `soft_preferences.objective` | `Objective` |
| `soft_preferences.conviction_weights.*` | `Conviction Weight High/Medium/Low` |
| `regime_overrides.drawdown_from_peak.*` | `Drawdown Trigger Pct`, multipliers, floor |

## Portfolio Analysis Audit (future)

When **Portfolio Analysis** runs, copy active policy fields onto the analysis row (or link + JSON) for audit: which guardrails produced this **Target Portfolio Holdings**.

Minimum audit fields:

- `Policy` relation → `Portfolio Policy` row used
- `Policy Effective Date`
- `Max Portfolio Heat Pct`, `Max Single Holding Pct`, `Min Cash Pct` (at minimum)

## Guardrail Evaluation Order (reference)

1. Filter proposals (`Status`, `Pricing Status`, `Intent`, `min_reward_risk_ratio`)
2. Compute metrics from Approved Portfolio Snapshot (NAV, cash %, market mix, portfolio heat)
3. Apply regime overrides (drawdown, stale pricing)
4. Allocate with `risk_at_stop` sizing under hard limits
5. Rank feasible outcomes with soft preferences
6. Emit **Target Portfolio Holdings** + **Rebalance Actions** + rejection reasons

## Reconstruction Order

1. Create `Portfolio Policy` database (or singleton page) with properties above.
2. Insert one `draft` row with suggested starter values (from `guardrails.yaml`).
3. After user confirmation, set `Status` = `active`, `Active` = true, `Effective Date`.
4. Wire future **Portfolio Analysis** to read active policy and Approved Portfolio Snapshot on each run.

## Initial Suggestions Disclaimer

All numeric defaults are **starting points** from common IPS and portfolio-heat practice. They are not recommendations for your specific situation. Replace before activating policy.
