# Prompt: Daily FX Strategy — Original Idea Stub

## Purpose

Minimal Notion input for the **daily Parallel strategy selector**. The agent expands this into full `Research Input` automatically.

This workflow currently runs in **Beginner Focus Mode**:

- Focus markets: `XAUUSD`, `EURUSD`, `USDJPY`
- Session focus: London, London/NY overlap, NY morning
- Daily capacity: max **one primary setup/day** and max **two watchlist setups/day**
- Default posture: prefer `T0_NO_TRADE` when unclear

## Notion row template

| Property | Value |
| --- | --- |
| `Original Idea` | `Daily FX strategy brief — {YYYY-MM-DD}` |
| `Run Frequency` | `Daily` |
| `Active` | ✅ true |
| `Status` | `New` (until expanded) |
| `Market Tags` | `FX_MAJOR`, `FX_CROSS` |
| `Asset Type Tags` | `FX` |

Example title: `Daily FX strategy brief — 2026-06-16`

## What expand-new-ideas does

When `Original Idea` matches `Daily FX strategy brief — {date}`:

1. Reads **Research Prompt** from `data/parallel/prompt-daily-fx-strategy-brief.md` (content between `---` fences under `## Research Prompt`).
2. Substitutes `{YYYY-MM-DD}` with the date from the title.
3. Writes result to `Research Input` and sets `Status` = `Expanded`.

No manual prompt paste required after expansion.

## What run-expanded-ideas does

For daily brief ideas: kicks off Parallel with `--processor pro-fast` (not `ultra`).

## Expected output

- Markdown sections including **Executive Summary** and **Priority Execution Queue**
- JSON with per-pair `template_id`: `T1_PULLBACK`, `T2_FALSE_BREAKOUT`, `T3_EXPANSION`, or `T0_NO_TRADE`
- Pine filenames under `data/tradingview/`
- XAUUSD treated separately from FX majors, including gold tick/pip convention, volatility scale, session liquidity, and macro drivers

Schema: `data/parallel/output-daily-fx-strategy-brief.json`
