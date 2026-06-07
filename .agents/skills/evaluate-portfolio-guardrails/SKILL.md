---
name: evaluate-portfolio-guardrails
description: Compute portfolio heat, concentration, cash, and exposure metrics from the latest Approved Portfolio Snapshot in Notion and check against guardrails.yaml hard limits. Read-only. Use when evaluating portfolio guardrails, portfolio heat, or snapshot metrics against Portfolio Policy.
disable-model-invocation: true
---

# Evaluate Portfolio Guardrails

Compute portfolio metrics from the **latest Approved Portfolio Snapshot** and its **Portfolio Holdings** in Notion, then check hard limits in [`data/portfolio/guardrails.yaml`](../../data/portfolio/guardrails.yaml).

This skill is **read-only**. It does not write Notion, place trades, or modify policy files. Do not present output as personalized investment advice.

## Fixed Defaults

- Input: Notion only (latest `Status = approved` snapshot, or `--snapshot-date`)
- Policy: [`data/portfolio/guardrails.yaml`](../../data/portfolio/guardrails.yaml) via PyYAML
- Notion API version: `2025-09-03`
- Risk-at-stop: uses `Entry Price` and `Stop Price` on holdings per [`data/notion/portfolio.md`](../../data/notion/portfolio.md), converted to snapshot `Base Currency` via [FXRatesAPI latest rates](https://fxratesapi.com/docs/endpoints/latest-exchange-rates) (`GET /latest?base={BASE}&currencies=...`; optional `FXRATESAPI_API_KEY`)
- Notion writes: **never**

## Python Environment

- Requires system `python3` (3.9+)
- Skill-local venv: `.agents/skills/evaluate-portfolio-guardrails/.venv` (gitignored)
- First run of [`scripts/run.sh`](scripts/run.sh) creates the venv and installs `pyyaml>=6`
- Do not create a repo-root Python project

## Prerequisites

- `NOTION_API_TOKEN` in environment or `.env`
- `FXRATESAPI_API_KEY` in environment or `.env` (optional; API may work without a key on free tier)
- Notion databases: `Portfolio Snapshot`, `Portfolio Holdings` with schema per [`data/notion/portfolio.md`](../../data/notion/portfolio.md)
- At least one **Approved Portfolio Snapshot** row exists

## Inputs

```bash
.agents/skills/evaluate-portfolio-guardrails/scripts/run.sh \
  [--policy data/portfolio/guardrails.yaml] \
  [--snapshot-date YYYY-MM-DD] \
  [--drawdown-pct N] \
  [--out path.json] \
  [--metrics-only] \
  [--fail-on-violation]
```

| Flag | Purpose |
| --- | --- |
| `--policy` | YAML policy path (default: `data/portfolio/guardrails.yaml`) |
| `--snapshot-date` | Pick approved snapshot for a specific date |
| `--drawdown-pct` | Apply drawdown regime overrides when trigger is met |
| `--out` | Write JSON to file; default stdout |
| `--metrics-only` | Omit `guardrail_check` section |
| `--fail-on-violation` | Exit code 1 if any hard limit fails |

## Steps

1. Load guidance:
   - Read `AGENTS.md`
   - Read [`data/notion/portfolio.md`](../../data/notion/portfolio.md) (derived metrics)
   - Read [`data/portfolio/guardrails.yaml`](../../data/portfolio/guardrails.yaml)
   - Read [`.agents/skills/notion-api/SKILL.md`](../notion-api/SKILL.md) for API conventions

2. Validate auth without exposing secrets:
   - Confirm `NOTION_API_TOKEN` is present (env or `.env`)
   - Do not print token values

3. Run evaluation:

```bash
.agents/skills/evaluate-portfolio-guardrails/scripts/run.sh --out /tmp/portfolio-metrics.json
```

4. Summarize results for the user:
   - Snapshot date, NAV, base currency
   - Key metrics: `holdings_count`, `cash_pct`, `max_single_holding_pct`, `portfolio_heat_pct`
   - Failed guardrail checks (if any)
   - Warnings for holdings missing stop/entry data

## Output JSON Contract

Top-level keys:

| Key | Content |
| --- | --- |
| `schema_version` | `1` |
| `computed_at` | ISO 8601 UTC timestamp |
| `snapshot` | `{ id, date, base_currency, nav, title }` |
| `fx_rates` | FXRatesAPI rates used to convert risk-at-stop to base currency |
| `metrics` | Aggregates aligned to guardrails |
| `positions[]` | Per-holding weight, risk-at-stop (base currency), `risk_at_stop_local`, warnings |
| `guardrail_check` | Policy path, effective limits, checks, summary |
| `warnings` | Optional portfolio-level warnings |

### Metrics computed

| Metric | Rule |
| --- | --- |
| `holdings_count` | Non-cash positions |
| `cash_pct` | Cash market value / NAV × 100 |
| `max_single_holding_pct` | Max non-cash weight |
| `portfolio_heat_pct` | Σ risk-at-stop (base currency) / NAV × 100 |
| `market_exposure_pct` | Weights by `Market` (HK/JP/US/OTHER) |
| `asset_class_exposure_pct` | Weights by `Asset Class` (equity/etf/crypto) |

### Guardrail checks (v1)

Hard limits checked against policy:

- `max_holdings_count`, `min_cash_pct`, `max_cash_pct`
- `max_single_holding_pct`, `max_portfolio_heat_pct`
- `market_limits.*.max_exposure_pct`
- `asset_class_limits.*.max_exposure_pct`

Skipped in v1 (listed in `guardrail_check.summary.skipped`):

- Turnover, proposal R/R, per-proposal risk cap, soft preferences, proposal regime filters

## Error Cases

Stop and report clearly when:

- `NOTION_API_TOKEN` is missing
- FXRatesAPI request fails or returns no rate for a required holding currency
- `Portfolio Snapshot` or `Portfolio Holdings` data source not found
- Required Notion properties are missing
- No approved snapshot exists (or no match for `--snapshot-date`)
- NAV is missing or zero
- Policy YAML cannot be loaded

Holdings with missing entry/stop prices produce warnings but do not abort the run.

## Related

- Policy schema: [`data/portfolio/guardrails.md`](../../data/portfolio/guardrails.md)
- Portfolio schema: [`data/notion/portfolio.md`](../../data/notion/portfolio.md)
