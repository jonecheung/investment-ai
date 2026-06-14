# Prompt: Daily FX Strategy — Original Idea Stub

## Purpose

Minimal `Original Idea` text for Notion `Research Ideas` when scheduling the daily Parallel strategy brief.

## Notion Row Settings

| Property | Value |
| --- | --- |
| `Original Idea` | See template below |
| `Run Frequency` | `Daily` |
| `Active` | `true` |
| `Market Tags` | `FX_MAJOR`, `FX_CROSS` |
| `Asset Type Tags` | `FX` |
| `Strategy Tags` | `Momentum` (or leave empty) |

## Original Idea Template

```
Daily FX strategy brief — {YYYY-MM-DD}
```

Example: `Daily FX strategy brief — 2026-06-16`

## Research Input Expansion

When expanding to `Research Input`, prepend the trade date and append the full system prompt:

1. Open `data/parallel/prompt-daily-fx-strategy-brief.md`
2. Set `trade_date` and `focus_pairs` at the top of the task section
3. Store the combined text in `Research Input`
4. Run via `parallel-cli research run` with processor `pro-fast`

## Expected Output

Parallel returns which **Template ID** to use per pair (`T1_PULLBACK`, `T2_FALSE_BREAKOUT`, `T3_EXPANSION`, or `T0_NO_TRADE`) plus Pine filenames. See `data/parallel/output-daily-fx-strategy-brief.json`.
