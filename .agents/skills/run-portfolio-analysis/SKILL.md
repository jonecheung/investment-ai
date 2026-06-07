---
name: run-portfolio-analysis
description: Run Layer 3 portfolio analysis from Notion snapshot, policy, and eligible Trading Proposals. Python unified-rank + swap planner outputs target holdings and rebalance actions as JSON (default) or Notion writes with --write.
disable-model-invocation: true
---

# Run Portfolio Analysis

Run **Layer 3 portfolio analysis**: read Approved Portfolio Snapshot + eligible `Trading Proposals` + active `Portfolio Policy`, run deterministic Python planning, emit **Target Portfolio Holdings** and **Rebalance Actions**.

This is planning support only. Do not present output as personalized investment advice. Does not place trades.

## Fixed Defaults

- Input: Notion (`Portfolio Snapshot`, `Portfolio Holdings`, `Portfolio Policy`, `Trading Proposals`)
- Planner: unified rank + risk-budget sizing + swap (incumbents and proposals compete in one pool)
- Objective: from active `Portfolio Policy` (`Objective` field / `soft_preferences.objective`)
- Output: JSON stdout (default); Notion write only with `--write`
- Reuses math from [`evaluate-portfolio-guardrails`](../evaluate-portfolio-guardrails/SKILL.md) via `PYTHONPATH`
- Notion API version: `2025-09-03`

## Python Environment

- Requires system `python3` (3.9+)
- Skill-local venv: `.agents/skills/run-portfolio-analysis/.venv` (gitignored)
- First run of [`scripts/run.sh`](scripts/run.sh) creates venv and installs `pyyaml>=6`
- Guardrails scripts on `PYTHONPATH`: `../evaluate-portfolio-guardrails/scripts`

## Prerequisites

- `NOTION_API_TOKEN` in environment or `.env`
- `FXRATESAPI_API_KEY` optional (FX-adjusted risk-at-stop for JP/US lines)
- Notion: `Portfolio Snapshot`, `Portfolio Holdings`, `Portfolio Policy`, Layer 3 DBs (`Portfolio Analysis`, `Target Portfolio Holdings`, `Rebalance Actions`)
- At least one **Approved Portfolio Snapshot**
- Active **Portfolio Policy** row (unless `--policy` YAML override)
- Eligible proposals optional but recommended (`Accepted`, `Ready`, `Intent = Trade`)

## Inputs

```bash
.agents/skills/run-portfolio-analysis/scripts/run.sh \
  [--snapshot-date YYYY-MM-DD] \
  [--policy data/portfolio/guardrails.yaml] \
  [--drawdown-pct N] \
  [--out path.json] \
  [--write] \
  [--fail-on-infeasible]
```

| Flag | Purpose |
| --- | --- |
| `--snapshot-date` | Approved snapshot date (default: latest approved) |
| `--policy` | YAML policy override (default: active Notion `Portfolio Policy`) |
| `--drawdown-pct` | Apply drawdown regime overrides |
| `--out` | Write JSON to file; default stdout |
| `--write` | Create `Portfolio Analysis` + child rows in Notion (requires feasible plan + passing target guardrails) |
| `--fail-on-infeasible` | Exit code 1 when `analysis.status` = `infeasible` |

Default behavior is **dry-run** (JSON only, no Notion writes).

## Steps

1. Read `AGENTS.md`, [`data/notion/portfolio.md`](../../data/notion/portfolio.md), [`data/portfolio/guardrails.md`](../../data/portfolio/guardrails.md)
2. Confirm `NOTION_API_TOKEN` present (never print value)
3. Run:

```bash
.agents/skills/run-portfolio-analysis/scripts/run.sh --out /tmp/plan.json
```

4. Review JSON: `analysis.status`, `guardrail_check`, `rebalance_actions`, `rejections`
5. If acceptable: re-run with `--write` to persist Layer 3 rows in Notion

## Output JSON Contract

| Key | Content |
| --- | --- |
| `schema_version` | `1` |
| `computed_at` | ISO timestamp |
| `analysis` | Run metadata, input/target aggregates, policy audit fields |
| `target_holdings[]` | Target portfolio lines (+ CASH) |
| `rebalance_actions[]` | Suggested deltas (non-zero only) |
| `rejections[]` | Filtered or could-not-fit proposals |
| `guardrail_check_input` | Input snapshot guardrail evaluation |
| `guardrail_check` | Target portfolio guardrail evaluation |
| `executive_summary` | Template-generated summary |
| `fx_rates` | Optional FXRatesAPI rates used |

## Planner Behavior

1. Filter proposals per policy (`Status`, `Pricing Status`, `Intent`, min R/R, stale/watchlist rules)
2. Merge incumbents + proposals (ticker dedupe → `merged`)
3. **Select** (when input fails guardrails): rank all lines by `effective_score`; keep top `max_holdings_count`; reset selected lines to zero and rebase turnover baseline
4. **Trim** lowest-ranked included lines until guardrails pass (excess cash resolved by sizing, not trimming)
5. **Size**: greedy `risk_at_stop` steps on highest `effective_score` lines within heat, cash, and turnover caps
6. **Swap**: replace lowest-ranked incumbent with highest-ranked excluded proposal when score improves and constraints allow
7. Build rebalance deltas (vs snapshot) and validate target guardrails

`effective_score` = `conviction × R/R × (1 + existing_position_bias)` for incumbents/merged, `× (1 + 0.05)` for new proposals.

## Error Cases

Stop and report when:

- `NOTION_API_TOKEN` missing
- No approved snapshot or active policy
- Layer 3 Notion databases not found
- FXRatesAPI failure for required currencies
- `--write` with `infeasible` status or failing target guardrails

## Tests

```bash
PYTHONPATH=".agents/skills/evaluate-portfolio-guardrails/scripts:.agents/skills/run-portfolio-analysis/scripts" \
  .agents/skills/run-portfolio-analysis/.venv/bin/python \
  .agents/skills/run-portfolio-analysis/tests/test_planner.py -v
```

## Related

- Guardrails evaluation: [`evaluate-portfolio-guardrails`](../evaluate-portfolio-guardrails/SKILL.md)
- Schemas: [`data/notion/portfolio.md`](../../data/notion/portfolio.md)
