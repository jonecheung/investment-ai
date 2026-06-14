# Prompt: Daily FX Intraday Strategy Brief

## Purpose

Produce a **same-day execution brief** that classifies the current FX market regime for each focus pair and **recommends exactly one strategy template** (or explicit no-trade) from the approved workspace playbook.

This prompt is designed for **weekday execution mode** (Mon–Fri, pre-London). Output feeds `Research Ideas` → `Research Runs` → human review → Pine Screener / manual execution. It is research framing only, not trade instructions or personalized investment advice.

## When To Run

- **Schedule:** Daily, **05:00–06:30 UTC** (before Asian range locks at 07:00 UTC).
- **Notion:** `Research Ideas` row with `Run Frequency = Daily`, `Active = true`.
- **Processor:** `pro-fast` (needs current calendar + recent market context). Use `lite` only as a follow-up with `--previous-interaction-id` from the same morning run.
- **Original Idea (minimal user input):** `Daily FX strategy brief — {YYYY-MM-DD}`

## Inputs

- `trade_date`: Today's date in UTC (YYYY-MM-DD).
- `focus_pairs`: Default `EURUSD`, `GBPUSD`, `USDJPY`, `EURJPY`.
- `session_anchor`: UTC. Default primary sessions: Asian `0000-0700`, London `0700-1600`, NY `1200-2100`, overlap `1200-1600`.
- `cost_assumption`: ECN-style majors, ~0.8–1.2 pip round-turn equivalent.
- `prior_playbook_interaction_id`: Optional. Prior deep-research interaction ID for scenario playbook context (intraday FX scenario × strategy matrix).

## Approved Strategy Template Registry

Recommend **only** templates from this registry. Do not invent new strategy names.

| Template ID | Strategy Name | Scenario | Chart TF | Entry Session (UTC) | Pine Screener | Pine Strategy | Tier | Default Pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `T1_PULLBACK` | D1-Bias EMA Pullback | Strong trend day | H1 | 0700-1400 | `d1-bias-ema-pullback-forex.pine` | `d1-bias-ema-pullback-forex-strategy.pine` | PRIMARY | EURUSD, GBPUSD, USDJPY |
| `T2_FALSE_BREAKOUT` | Asian False Breakout Reversion | Range / mean-reversion day | M15 | 0700-1200 | `asian-false-breakout-reversion-forex.pine` | `asian-false-breakout-reversion-forex-strategy.pine` | PRIMARY | EURUSD, GBPUSD |
| `T3_EXPANSION` | Volatility-Compression Expansion | Expansion / post-compression day | M15 | 0715-1400 | `vol-compression-expansion-forex.pine` | `vol-compression-expansion-forex-strategy.pine` | SECONDARY | EURUSD, USDJPY, EURJPY |
| `T4_SWING_BACKUP` | Supertrend + 200 EMA Long | Multi-day swing (not intraday primary) | 1D | N/A | `supertrend-ema-atr-long.pine` | — | BACKUP | majors when intraday blocked |
| `T0_NO_TRADE` | No Trade / Cash Mode | Holiday, event, drift, insufficient edge | — | — | — | — | BLOCK | all |

**Deprioritized — do not recommend unless user explicitly revalidated:**

| Template ID | Reason |
| --- | --- |
| `ARCHIVE_ORB` | Generic 15m ORB underperformed after costs (PF ~0.5–0.7) |
| `ARCHIVE_LONDON_BO` | Plain London/Asian breakout PF ~0.26–0.76 without narrow-range filters |

## Scenario Taxonomy (classify before recommending)

For each focus pair, assign **one primary scenario** (1–8):

1. **Strong trend day** — ADX elevated, D1 EMA slope aligned, directional prior day
2. **Weak trend / drift day** — ADX 15–25, flat EMA, indecisive D1
3. **Range / mean-reversion day** — ADX < 20, low D1 ATR percentile, narrow expected Asian range
4. **Expansion / breakout day** — D1 volatility compression (BB/Keltner squeeze), coiling at range edge
5. **High-impact event day** — NFP, CPI, FOMC, ECB, etc. on calendar today
6. **Risk-on / risk-off shock** — DXY + VIX co-directional spike (if detectable from recent data)
7. **Low-liquidity / holiday** — regional holiday or thin session expected
8. **Cross-pair divergence** — EURUSD vs GBPUSD leadership mismatch (filter only, not standalone entry)

## Task

For `trade_date` and each pair in `focus_pairs`:

1. **Check calendar and liquidity:** flag holidays, high-impact events, and pairs affected.
2. **Classify scenario** using D1 context (trend, volatility, compression, event risk) and what is knowable pre-07:00 UTC.
3. **Apply decision tree** (below) to select **one** `Template ID`.
4. **State D1 bias:** `Long`, `Short`, or `Neutral` (intraday direction constraint for T1).
5. **State confidence:** `High`, `Medium`, or `Low` with one-line rationale.
6. **List watch conditions** for London open (07:00 UTC): e.g. Asian range width target, ADX confirmation, spread check.
7. **Explicit do-not-trade rules** when recommending `T0_NO_TRADE`.

## Decision Tree (mandatory logic)

Apply in order for each pair:

1. Holiday or thin liquidity expected? → `T0_NO_TRADE`
2. High-impact event today affecting this pair (±2h of release)? → `T0_NO_TRADE` (or note post-event fade as observation only — still default `T0_NO_TRADE` for retail)
3. D1 strong trend signals (ADX > 25, EMA slope aligned, directional prior day)? → `T1_PULLBACK`
4. D1 range regime (ADX < 20, low ATR percentile)? → if Asian range likely **20–35 pips** (EURUSD proxy) → `T2_FALSE_BREAKOUT`; else if range too wide/narrow → `T0_NO_TRADE` or wait
5. D1 squeeze / compression (BB inside Keltner ≥ 2 bars, low ATR pct)? → `T3_EXPANSION`
6. Drift day (ADX 15–25, no squeeze)? → `T0_NO_TRADE` (default skip)
7. Cross-pair divergence only? → use as **filter** on T1/T2; do not assign standalone template
8. If ambiguous → `T0_NO_TRADE` and explain missing data

**Pair priority when templates conflict:** EURUSD first for T1/T2; USDJPY for risk-off context; EURJPY only for T3 when expansion expected.

## Analysis Requirements

- Use **current** economic calendar for `trade_date` ( cite source ).
- Separate **FACT** (calendar, prior close, published ranges) from **ASSUMPTION** (expected Asian range, scenario persistence) from **OPINION** (confidence).
- ADX is for **scenario classification only** — do not recommend ADX threshold as entry filter (FX evidence: ADX filter can reduce PF).
- Include spread/cost awareness: deprioritize intraday on wide-spread crosses unless T3 with large expected range.
- Do not claim guaranteed profitability. Frame as conditional playbook selection.
- If live prices unavailable, state gaps and recommend conservative `T0_NO_TRADE`.

## Constraints

- Recommend only registry `Template ID` values.
- At most **one primary template per pair** per day.
- Do not recommend `ARCHIVE_*` templates.
- Do not provide position sizing, lot size, or account-specific advice.
- Do not output raw JSON in the markdown body unless Output Format requests a fenced JSON block.
- Keep `Executive Summary` ≤ 300 words.

## Output Format

Return Markdown with **exactly** these sections:

### 1. `## Executive Summary`

≤ 300 words. Answer: **What should we trade today, with which template, or should we sit out?**

### 2. `## Today's Market Context`

- UTC date and day of week
- Global liquidity / holiday flags
- Scheduled high-impact events (time UTC, affected pairs)
- Risk-on/off snapshot if relevant (DXY, VIX direction — cite source)

### 3. `## Pair Recommendations`

One subsection per focus pair:

```markdown
### {PAIR} (e.g. EURUSD)

| Field | Value |
| --- | --- |
| Scenario | {1–8 name} |
| Template ID | {T0_NO_TRADE \| T1_PULLBACK \| T2_FALSE_BREAKOUT \| T3_EXPANSION \| T4_SWING_BACKUP} |
| Strategy Name | {from registry} |
| D1 Bias | Long / Short / Neutral |
| Confidence | High / Medium / Low |
| Chart TF | {H1 / M15 / 1D} |
| Entry Session UTC | {from registry or N/A} |
| Pine Screener | {filename or —} |
| Pine Strategy | {filename or —} |

**Rationale:** {2–4 sentences}

**London open checklist (07:00 UTC):**
- {bullet}
- {bullet}

**Do NOT trade if:**
- {bullet}
```

### 4. `## Priority Execution Queue`

Numbered list (max 3 trades/day suggestion for retail focus):

1. {PAIR} — {Template ID} — {one-line why first}
2. ...

If all pairs `T0_NO_TRADE`, state: **No intraday templates active today.**

### 5. `## Scenario × Template Matrix (Today)`

| Pair | Scenario | Template ID | Confidence | Trade? (Y/N) |
| --- | --- | --- | --- | --- |

### 6. `## Structured Output (JSON)`

Return a fenced JSON block conforming to `data/parallel/output-daily-fx-strategy-brief.json` for downstream parsing.

### 7. `## Sources & Uncertainty`

- Cite calendar and market data sources with dates.
- List conflicts, stale data, and missing inputs.

## Quality Bar

A good daily brief lets the user at **06:30 UTC** know:

- which Pine script to open on TradingView,
- which pairs are in play,
- and which pairs to **ignore today**.

It must be **actionable in one screen** — not a generic FX commentary.

## Missing Context Handling

If calendar or price context is unavailable:

- Default affected pairs to `T0_NO_TRADE`
- Set all confidence to `Low`
- Document gaps in `## Sources & Uncertainty`
- Still produce valid JSON with `trade_allowed: false` per pair

## Notion Handoff

After Parallel run completes:

- Store full result URL in `Research Runs.Result URL`
- Copy `## Executive Summary` to `Research Runs.Executive Summary` and `Research Ideas.Executive Summary`
- Use JSON `pair_recommendations[]` for optional Trading Proposals prep (manual review; no auto-import without confirmation)

## Example Original Idea → Research Input

**Original Idea:** `Daily FX strategy brief — 2026-06-16`

**Research Input:** Paste this entire prompt, replacing:

```
trade_date: 2026-06-16
focus_pairs: EURUSD, GBPUSD, USDJPY, EURJPY
```
