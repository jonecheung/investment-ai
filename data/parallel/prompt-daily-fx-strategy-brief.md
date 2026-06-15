# Prompt: Daily FX Intraday Strategy Brief

## Purpose

Same-day execution brief: classify FX regime per pair and **recommend exactly one strategy template** (or no-trade) from the approved workspace playbook.

- **Notion `Original Idea`:** `Daily FX strategy brief — {YYYY-MM-DD}`
- **Notion settings:** `Run Frequency = Daily`, `Active = true`
- **Processor:** `pro-fast` (not `ultra` — daily brief needs calendar + recent context, not exhaustive research)
- **Schedule:** Weekdays **05:00–06:30 UTC** (before London / NY planning window)
- **Output schema:** `data/parallel/output-daily-fx-strategy-brief.json`

## Workflow

1. Create or activate Notion `Research Ideas` row with today's Original Idea.
2. Run `expand-new-ideas` — auto-fills `Research Input` from **Research Prompt** below when Original Idea matches `Daily FX strategy brief`.
3. Run `run-expanded-ideas-deep-research` — uses `pro-fast` for daily brief ideas.
4. Poll with `poll-deep-research-runs`; read `Executive Summary` + JSON `template_id` per pair.
5. Open recommended Pine strategy on TradingView for the London / NY session.

## Beginner Focus Mode

This prompt is intentionally narrowed for the current execution workflow:

- **Focus markets:** `XAUUSD`, `EURUSD`, `USDJPY`
- **Primary sessions:** London, London/NY overlap, and NY morning
- **Daily capacity:** recommend **at most one primary setup/day** and at most **two watchlist setups/day**
- **Default posture:** prefer `T0_NO_TRADE` when regime, liquidity, calendar, or chart structure is unclear
- **Gold handling:** treat `XAUUSD` separately from FX majors. Always state gold quote convention, tick/pip convention, volatility scale, primary session liquidity, and macro drivers (USD, real yields, Fed expectations, risk sentiment).

## CLI (manual)

```bash
# Substitute trade_date, then:
parallel-cli research run "$(sed -n '/^---$/,/^---$/p' data/parallel/prompt-daily-fx-strategy-brief.md | sed '1d;$d')" \
  --processor pro-fast --no-wait --json
```

Or copy the **Research Prompt** section directly.

---

## Research Prompt

---
You are the daily FX intraday strategy selector for a personal research workspace. Your job is NOT to find new strategies — it is to classify today's market regime for each focus pair and recommend **exactly one approved template** (or explicit no-trade).

**Run mode:** Weekday execution brief (pre-London, 05:00–06:30 UTC).
**Asset scope:** Spot FX plus XAUUSD as a separate gold/FX-adjacent instrument. Default focus is only `XAUUSD`, `EURUSD`, and `USDJPY`.
**Style:** Intraday (flat before rollover unless template says otherwise).
**Cost assumption:** ECN-style majors ~0.8–1.2 pip round-turn. Do not claim guaranteed profitability.

### Runtime inputs (set before each run)

- trade_date: {YYYY-MM-DD}
- focus_pairs: XAUUSD, EURUSD, USDJPY
- session_anchor: UTC (Asian reference 0000-0700, London 0700-1600, NY 1200-2100, overlap 1200-1600)
- session_focus: London session, London/NY overlap, NY morning
- execution_mode: beginner focus mode; max 1 primary setup/day; max 2 watchlist setups/day

### Approved strategy template registry

Recommend ONLY these Template IDs. Map to exact Pine filenames.

| Template ID | Strategy Name | Scenario | Chart TF | Entry Session UTC | Pine Screener | Pine Strategy | Tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1_PULLBACK | D1-Bias EMA Pullback | Strong trend day | H1 | 0700-1400 | d1-bias-ema-pullback-forex.pine | d1-bias-ema-pullback-forex-strategy.pine | PRIMARY |
| T2_FALSE_BREAKOUT | Asian False Breakout Reversion | Range / mean-reversion day | M15 | 0700-1200 | asian-false-breakout-reversion-forex.pine | asian-false-breakout-reversion-forex-strategy.pine | PRIMARY |
| T3_EXPANSION | Volatility-Compression Expansion | Expansion / post-compression | M15 | 0715-1400 | vol-compression-expansion-forex.pine | vol-compression-expansion-forex-strategy.pine | SECONDARY |
| T4_SWING_BACKUP | Supertrend + 200 EMA Long | Swing backup when intraday blocked | 1D | N/A | supertrend-ema-atr-long.pine | (no strategy file) | BACKUP |
| T0_NO_TRADE | No Trade / Cash Mode | Holiday, event, drift, no edge | — | — | — | — | BLOCK |

### Market-specific scope

| Market | Role | Preferred Templates | Notes |
| --- | --- | --- | --- |
| `XAUUSD` | Primary opportunity market | `T1_PULLBACK`, `T3_EXPANSION`, `T0_NO_TRADE` | Treat separately from FX majors. Gold is driven by USD, real yields, Fed expectations, and risk sentiment; avoid forcing T2 fades until separately validated. |
| `EURUSD` | FX benchmark / liquidity anchor | `T1_PULLBACK`, `T2_FALSE_BREAKOUT`, `T3_EXPANSION`, `T0_NO_TRADE` | Lowest-spread benchmark pair; best pair for validating the playbook. |
| `USDJPY` | USD / yield / risk-off expression | `T1_PULLBACK`, `T3_EXPANSION`, `T0_NO_TRADE` | Sensitive to US yields and JPY safe-haven flows; use T2 only if explicitly justified by range conditions. |

**Never recommend (archived — failed backtests after costs):**
- ARCHIVE_ORB — generic 15m Opening Range Breakout (EURUSD PF ~0.5–0.7)
- ARCHIVE_LONDON_BO — plain London/Asian breakout without narrow-range filter (PF ~0.26–0.76)

### Playbook evidence (use for classification, not for hype)

- **T1_PULLBACK:** Highest-confidence intraday template. D1 bias + H1/M15 pullback to 21 EMA, 2× ATR stop, 2:1 R:R. Published EURUSD pullback ~63% WR (small sample ~30 trades). ADX classifies scenario — do NOT use ADX as entry filter (FX PF drops when ADX filters entries). For XAUUSD, explicitly adjust ATR/stop scale and account for real-yield sensitivity.
- **T2_FALSE_BREAKOUT:** Only when D1 ADX < 20 AND Asian range expected 20–35 pips (EURUSD proxy). Without narrow-range filter, London breakout strategies fail (PF ~0.26). Prefer EURUSD first; avoid XAUUSD T2 unless the brief can justify gold-specific range behavior.
- **T3_EXPANSION:** D1 BB inside Keltner squeeze ≥2 bars + London/NY breakout. FX-specific evidence is thin; recommend only when compression is extreme. Marginal edge after costs. For XAUUSD, NY morning / overlap is usually more relevant than early London.
- **T0_NO_TRADE:** Holidays (spreads +30–50%), high-impact events (NFP/CPI/FOMC/ECB ±2h), drift days (ADX 15–25), ambiguous regime. Neely (2002): intraday FX technical rules often have zero excess return after realistic costs.

### Scenario taxonomy (assign one primary scenario 1–8 per pair)

1. Strong trend day — ADX elevated, D1 EMA slope aligned, directional prior day
2. Weak trend / drift day — ADX 15–25, flat EMA
3. Range / mean-reversion day — ADX < 20, low D1 ATR percentile, narrow Asian range expected
4. Expansion / breakout day — D1 volatility compression (BB/Keltner squeeze)
5. High-impact event day — scheduled NFP, CPI, FOMC, ECB, etc.
6. Risk-on / risk-off shock — DXY + VIX co-directional move
7. Low-liquidity / holiday — regional holiday or thin session
8. Cross-pair divergence — EURUSD vs GBPUSD leadership mismatch (filter only, never standalone template)

### Decision tree (apply in order for each pair)

1. Holiday or thin liquidity? → T0_NO_TRADE
2. High-impact event affecting pair within ±2h of release? → T0_NO_TRADE
3. D1 strong trend (ADX > 25, EMA slope aligned, directional prior day)? → T1_PULLBACK
4. D1 range regime (ADX < 20, low ATR pct)? → if Asian range likely 20–35 pips → T2_FALSE_BREAKOUT; else T0_NO_TRADE or wait
5. D1 squeeze (BB inside Keltner ≥ 2 bars, low ATR pct)? → T3_EXPANSION
6. Drift day (ADX 15–25, no squeeze)? → T0_NO_TRADE (default skip)
7. Cross-pair divergence only? → apply as filter on T1/T2; do not assign standalone template
8. Ambiguous or missing data? → T0_NO_TRADE, confidence Low

**Market priority:** choose only the clearest setup. Prefer `XAUUSD` when gold macro + chart structure are aligned, `EURUSD` as the FX benchmark, and `USDJPY` when USD/yield/risk-off signals are clearest. Do not recommend more than one primary setup/day.

### Your task for trade_date

For each market in focus_pairs:

1. Check economic calendar, session liquidity, and market-specific drivers for trade_date (cite sources).
2. Classify primary scenario (1–8) using D1 context knowable before London/NY execution.
3. Apply decision tree → one Template ID.
4. State D1 bias: Long, Short, or Neutral.
5. State confidence: High, Medium, or Low with one-line rationale.
6. List London/NY checklist: key levels, spread check, event windows, and confirmation triggers.
7. List explicit do-not-trade conditions.
8. Rank markets and recommend at most one **Primary Setup** plus at most two **Watchlist Setups**.

Separate FACT vs ASSUMPTION vs OPINION throughout.

### Output format (strict)

Return Markdown with these sections:

## Executive Summary
(≤300 words — whether there is one primary setup today, which template to use, or whether to sit out entirely)

## Today's Market Context
(UTC date, day of week, holidays, high-impact events with times, risk-on/off if relevant)

## Pair Recommendations
(One subsection per market with table: Scenario, Template ID, Strategy Name, D1 Bias, Confidence, Chart TF, Entry Session UTC, Pine Screener, Pine Strategy, Rationale, London/NY checklist, Do NOT trade if)

## Priority Execution Queue
(Numbered max 1 **Primary Setup** plus max 2 **Watchlist Setups**, or "No intraday templates active today")

## Scenario × Template Matrix (Today)
(Table: Pair | Scenario | Template ID | Confidence | Trade? Y/N)

## Structured Output (JSON)
(Fenced JSON block conforming to schema below — required)

## Sources & Uncertainty
(Cite calendar/market sources; list gaps and conflicts)

### Required JSON schema

```json
{
  "schema_version": "v1.0",
  "trade_date": "YYYY-MM-DD",
  "executive_summary": "string ≤300 words",
  "global_context": {
    "liquidity_status": "normal|thin|holiday|mixed",
    "high_impact_events": [{"event_name":"","time_utc":"","affected_pairs":[]}],
    "risk_regime": "risk_on|risk_off|neutral|unknown",
    "risk_regime_notes": "string"
  },
  "pair_recommendations": [{
    "pair": "EURUSD",
    "scenario_id": 1,
    "scenario_name": "string",
    "template_id": "T0_NO_TRADE|T1_PULLBACK|T2_FALSE_BREAKOUT|T3_EXPANSION|T4_SWING_BACKUP",
    "strategy_name": "string",
    "d1_bias": "Long|Short|Neutral",
    "confidence": "High|Medium|Low",
    "chart_timeframe": "H1|M15|1D|N/A",
    "entry_session_utc": "string or N/A",
    "pine_screener": "filename or empty",
    "pine_strategy": "filename or empty",
    "trade_allowed": true,
    "rationale": "string",
    "london_open_checklist": ["string"],
    "do_not_trade_if": ["string"]
  }],
  "priority_execution_queue": [{"rank": 1, "pair": "EURUSD", "template_id": "T1_PULLBACK", "reason": "string"}],
  "output_quality": {
    "fact_assumption_boundary": "string",
    "missing_information": ["string"],
    "uncertainty_notes": ["string"]
  }
}
```

### Constraints

- One primary template per market per day.
- Recommend at most one primary setup/day across all markets.
- Recommend at most two additional watchlist setups/day.
- No position sizing, lot sizes, or personalized investment advice.
- If calendar or prices unavailable → default T0_NO_TRADE, confidence Low, document gaps.
- Optimize for actionable output before London/NY: which Pine file to open, which market to focus on, and which markets to ignore.

Begin analysis for trade_date = {YYYY-MM-DD}.
---

## Expansion rule (expand-new-ideas)

When `Original Idea` matches `Daily FX strategy brief — {YYYY-MM-DD}`:

1. Extract date from title (fallback: today UTC).
2. Set `Research Input` = entire **Research Prompt** block above (between `---` fences).
3. Replace `{YYYY-MM-DD}` in `trade_date` and `Begin analysis` line with extracted date.
4. Set `Status` = `Expanded`.

## Processor rule (run-expanded-ideas-deep-research)

When `Original Idea` starts with `Daily FX strategy brief`:

- Use `--processor pro-fast` (not `ultra`).
- Store `Prompt Used` = first 500 chars of Research Input + `…` if truncated.

## Missing context

If Parallel cannot access live calendar/prices: still output valid JSON with all pairs `trade_allowed: false` and explain gaps in `output_quality.missing_information`.
