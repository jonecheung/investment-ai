# BTC / ETH Intraday Crypto Playbook

## Purpose

This playbook extends the workspace into a separate, small-size crypto workflow for `BTC` and `ETH`.

It is for research, observation, and manual decision support only. It does not place trades, size positions, or replace the existing FX / XAUUSD daily workflow.

## Scope

| Item | Setting |
| --- | --- |
| Markets | `BTCUSD`, `BTCUSDT`, `ETHUSD`, `ETHUSDT` depending on broker / exchange |
| Mode | Observation first; small manual trades only after user review |
| Primary timeframes | H1 for context, M15 for execution |
| Main sessions | London open, NY morning, London/NY overlap |
| Avoid | Weekend thin liquidity, major macro releases, major crypto-specific news shocks |
| Default posture | No trade when flow, liquidity, or volatility regime is unclear |

## Why This Is Separate From FX

Crypto trades 24/7 and is heavily affected by exchange-specific liquidity, perpetual futures funding, open interest, liquidation cascades, ETF flows, and weekend liquidity gaps.

Do not directly copy FX / XAUUSD rules into BTC or ETH without adjustment.

Key differences:

| Area | FX / XAUUSD | BTC / ETH |
| --- | --- | --- |
| Trading week | Weekdays, session-driven | 24/7, but session activity still matters |
| Volume | Spot FX volume is usually a proxy | Exchange / futures volume can be more informative |
| Order flow | Broker-dependent proxy | CVD, funding, OI, liquidation levels are more useful |
| Weekend behavior | Mostly closed | Open but often thinner and easier to manipulate |
| News drivers | Central banks, macro data, yields | Macro + ETF flows + funding + exchange liquidation |

## Required Pre-Trade Filters

Before considering any crypto setup:

1. Check whether a major US macro event is scheduled within +/- 2 hours.
2. Check whether price is near a major higher-timeframe level.
3. Check whether volatility is abnormal relative to recent ATR.
4. Check whether spread / slippage is acceptable on the broker or exchange.
5. Check whether BTC and ETH agree or diverge:
   - BTC leading up + ETH confirming = cleaner long environment.
   - BTC leading down + ETH confirming = cleaner short environment.
   - BTC/ETH divergence = reduce confidence or skip.
6. For perpetual futures context, if available, check:
   - Funding rate.
   - Open interest.
   - Liquidation clusters.
   - Futures CVD versus spot price.

If these checks are unavailable, treat all CVD / order-flow conclusions as proxy-only and reduce confidence.

## Approved Crypto Templates

Use crypto-specific IDs so they do not conflict with FX templates.

| Template ID | Name | Scenario | Chart TF | Main Confirmation |
| --- | --- | --- | --- | --- |
| `C1_VWAP_TREND` | Crypto VWAP Trend Pullback | Trend continuation | H1 + M15 | VWAP/EMA alignment + CVD support |
| `C2_SWEEP_REVERSAL` | Crypto Liquidity Sweep Reversal | Stop-run reversal | M15 | Sweep + MSS + absorption / exhaustion |
| `C3_COMPRESSION_BREAKOUT` | Crypto Compression Breakout Retest | Expansion after compression | H1 + M15 | Compression + breakout + retest + volume |
| `C0_NO_TRADE` | No Trade | Thin, choppy, news-driven, unclear | N/A | Capital preservation |

## C1: Crypto VWAP Trend Pullback

Use when BTC or ETH is trending and repeatedly respecting VWAP / anchored VWAP.

### Conditions

- H1 structure is making higher highs / higher lows for longs, or lower highs / lower lows for shorts.
- M15 price is on the correct side of VWAP.
- EMA 20 is aligned with EMA 200, or price is clearly trending relative to both.
- Pullback reaches VWAP, anchored VWAP, EMA 20, or a prior fair-value zone.
- CVD supports the direction:
  - Long: CVD rising or bearish pullback absorbed.
  - Short: CVD falling or bullish pullback absorbed.

### Entry Confirmation

- Rejection candle at VWAP / EMA / prior order block.
- CVD turns back in trend direction.
- No immediate high-impact macro event.
- BTC and ETH are not strongly diverging against the trade.

### Exit Logic

- If no follow-through within 3-6 M15 candles, reduce or exit.
- Take profit near prior high/low, liquidity pool, or fixed reward/risk target.
- Do not hold purely because the market is 24/7.

## C2: Crypto Liquidity Sweep Reversal

Use when price sweeps a clear high/low and order flow shows exhaustion or absorption.

### Conditions

- Price sweeps:
  - Asian range high/low.
  - Prior day high/low.
  - NY session high/low.
  - Obvious equal highs/lows.
- Sweep candle has large wick or displacement failure.
- Market structure shift appears after the sweep.
- CVD diverges or shows absorption:
  - Long: price makes lower low, CVD does not make lower low, or heavy sell volume fails to push lower.
  - Short: price makes higher high, CVD does not make higher high, or heavy buy volume fails to push higher.

### Entry Confirmation

- Wait for MSS, then retest of the breaker / order block / swept level.
- Avoid entering directly into the first wick.
- Prefer confirmation from both price action and CVD / absorption.

### Exit Logic

- First target: range midpoint or nearest internal liquidity.
- Second target: opposite side of the local range only if momentum remains strong.
- If price returns to entry and CVD flips against the trade, exit.

## C3: Crypto Compression Breakout Retest

Use when volatility compresses and a real expansion move begins.

### Conditions

- H1 or M15 Bollinger width / ATR compresses relative to recent history.
- Range is clear and not too wide.
- Breakout candle has displacement and volume expansion.
- Avoid chasing the first candle if liquidation wick is extreme.

### Entry Confirmation

- Wait for retest of breakout level, VWAP, or new order block.
- CVD should confirm the breakout direction.
- OI/funding context, if available, should not show an overcrowded trap.

### Exit Logic

- If breakout does not continue within 1-4 M15 candles after retest, exit.
- Avoid holding through uncertain weekend liquidity.
- Reduce risk if price stalls before prior daily high/low.

## C0: No Trade Conditions

Use `C0_NO_TRADE` when:

- Weekend liquidity is thin or price is grinding without clean structure.
- Funding / OI suggests overcrowding but direction is unclear.
- BTC and ETH strongly diverge.
- High-impact macro event is imminent.
- Exchange or broker spread/slippage is abnormal.
- Price is between major levels with no CVD or absorption edge.
- The setup requires guessing rather than waiting for confirmation.

## Session Guide

Crypto is open 24/7, but not every hour is worth trading.

| Window UTC | Use |
| --- | --- |
| 0000-0700 | Asian range reference; observe but be selective |
| 0700-1000 | London open; good for sweep / range formation |
| 1200-1600 | London/NY overlap; often best liquidity |
| 1330-1600 | NY morning; strong macro / ETF / futures flow possible |
| Weekend | Observation only unless liquidity and structure are exceptional |

## Small-Trade Risk Rules

These are guardrails for manual review, not position sizing advice:

- Use smaller size than FX until the crypto workflow has a tested sample.
- One crypto trade at a time.
- Do not trade both BTC and ETH in the same direction unless they are clearly confirming each other.
- Stop after one full stop-loss in a session.
- Avoid revenge trades after liquidation wicks.
- Record screenshots for every setup: before entry, entry, exit, and post-trade review.

## BTC Versus ETH Selection

Prefer BTC when:

- Macro / ETF / broad risk flow is the main driver.
- BTC is leading the move and ETH is confirming.
- Liquidity is uncertain and you want the cleaner benchmark.

Prefer ETH when:

- ETH has a cleaner technical level.
- ETH/BTC relative strength supports the direction.
- ETH-specific catalyst exists and liquidity is normal.

If BTC and ETH conflict, default to no trade.

## Minimum Execution Checklist

Before a trade:

1. Market: BTC or ETH.
2. Template: `C1`, `C2`, `C3`, or `C0`.
3. Bias: long, short, or no trade.
4. Key level: VWAP, range high/low, order block, or breakout level.
5. Order-flow confirmation: CVD, absorption, or exhaustion.
6. Invalidation: exact price level where the idea is wrong.
7. Target: nearest liquidity / range midpoint / prior high-low / fixed RR.
8. Time stop: what time or how many M15 candles before exit if no follow-through.

If any item is missing, skip the trade.

## Research Follow-Up Needed

Before adding BTC / ETH into the daily automated workflow, run a separate crypto research prompt to evaluate:

- Best data sources for BTC / ETH CVD, funding, OI, and liquidation levels.
- Whether TradingView symbols can expose useful exchange volume for the user's broker.
- Whether a dedicated crypto selector should be separate from `daily-strategy-selector.pine`.
- Whether weekend and US macro-day filters should be hard blocks.

