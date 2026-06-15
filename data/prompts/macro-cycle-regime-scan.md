# Prompt: Daily FX Strategy Selection Regime Scan

## Purpose

Run a standardized daily FX market-regime scan before the European trading session.

The report should classify the current macro and FX regime, map likely cross-asset capital flows, and decide which strategy from the approved strategy playbook is suitable today. The goal is strategy selection and regime filtering, not forcing trade ideas.

This is research and scenario analysis only. Do not provide personalized financial advice, position sizing, trade execution instructions, or portfolio allocation.

## Asset Universe

Focus on FX and FX-related instruments:

- G10 majors
- G10 crosses
- EM FX

Do not cover equities, ETFs, or crypto as trade candidates unless explicitly requested. Use equity indices, volatility, commodities, and rates only as cross-asset context for FX regime analysis.

## Task

Analyze the current US and global macro cycle for daily FX strategy selection.

Focus on:

1. Inflation: CPI, core CPI, PCE, core PCE, PPI, inflation expectations
2. Employment: NFP, unemployment rate, jobless claims, JOLTS, wage growth
3. Growth: GDP, retail sales, industrial production
4. Business cycle: ISM manufacturing, ISM services, PMI data
5. Fed policy: current Fed funds rate, latest FOMC statement, dot plot, Fed speakers, market-implied rate path
6. Bond market: 2Y, 10Y, 30Y yields, yield curve, 2s10s, 3m10y, curve steepening/inversion
7. Real yields: 5Y and 10Y real yields, TIPS breakevens
8. Liquidity: Fed balance sheet, QT/QE, Treasury General Account, reverse repo, financial conditions
9. Intermarket confirmation: DXY, gold, S&P 500, Nasdaq, VIX, US bonds, crude oil
10. FX session context: Asia, London, New York, overlap liquidity, and event timing

## Approved Strategy Playbook

Choose only from these strategies. If the evidence does not clearly fit one, choose No-Trade Regime Filter.

### 1. Macro Trend Following

Use when there is a clear macro theme, aligned USD / risk / rates bias, strong trend strength, and confirming price action.

Avoid when signals are mixed, price is overextended, liquidity is poor, or major event risk is imminent.

### 2. Trend Pullback Continuation

Use when the higher-timeframe macro direction is clear but price has pulled back into a valid continuation area.

Avoid when the pullback reflects a macro reversal, key invalidation breaks, or trend structure fails.

### 3. Range Mean Reversion

Use when macro signals are mixed, volatility is controlled, trend strength is low, and price is near a clear range boundary.

Avoid during strong macro trend days, breakout conditions, high-impact event risk, or widening spreads.

### 4. Breakout Confirmation

Use when price is compressed near a key level and macro or event catalysts support volatility expansion and directional follow-through.

Avoid random technical breaks without catalyst, poor liquidity, wide spreads, or repeated false breakouts.

### 5. Post-News Wait-and-Confirm

Use on high-impact event days such as CPI, NFP, FOMC, central bank decisions, major inflation / jobs releases, or geopolitical shocks.

Do not recommend pre-event entries. Wait for post-event direction, liquidity normalization, and confirmation.

### 6. No-Trade Regime Filter

Use when bias is conflicting, confidence is low, liquidity is poor, event risk is too high, or the market does not clearly fit an approved strategy.

No-Trade is a valid primary output. Do not force a trading strategy if the regime is unclear.

## Daily Scoring Model

Score each factor from -2 to +2 and explain the reason:

| Factor | -2 | -1 | 0 | +1 | +2 |
| --- | --- | --- | --- | --- | --- |
| USD Bias | Strong USD bearish | Mild USD bearish | Neutral / mixed | Mild USD bullish | Strong USD bullish |
| Risk Sentiment | Strong risk-off | Mild risk-off | Neutral / mixed | Mild risk-on | Strong risk-on |
| US Rates Bias | Strongly lower yields | Mildly lower yields | Neutral / mixed | Mildly higher yields | Strongly higher yields |
| Equity Sentiment | Strong equity stress | Mild equity stress | Neutral / mixed | Mildly positive | Strongly positive |
| Commodity / Gold Bias | Strong commodity / gold pressure | Mild pressure | Neutral / mixed | Mild support | Strong support |
| Volatility Regime | Very low / compressed | Low | Normal | Elevated | Shock / disorderly |
| Event Risk | No major event risk | Low | Normal | Elevated | Major event imminent / active |
| Trend Strength | Strong anti-trend / reversal | Weak trend | No trend | Moderate trend | Strong trend |
| Range Strength | No reliable range | Weak range | Mixed | Clear range | Strong range |
| Confidence | Very low | Low | Mixed | Medium | High |

## Strategy Selection Rules

Use these rules to translate research into a strategy decision:

- If Confidence <= 0, default to No-Trade Regime Filter.
- If Event Risk >= +2 before a major event, prefer Post-News Wait-and-Confirm or No-Trade Regime Filter.
- If Trend Strength >= +2 and USD / risk / rates are aligned, prefer Macro Trend Following.
- If Trend Strength >= +1, the higher-timeframe direction is intact, and price is pulling back within a valid trend, prefer Trend Pullback Continuation.
- If Trend Strength <= 0 and Range Strength >= +2, prefer Range Mean Reversion.
- If volatility is compressed near a key level and a credible catalyst is present, classify as Breakout Watch and prefer Breakout Confirmation only after confirmation.
- If high volatility is disorderly, spreads are wide, or whipsaw risk is high, prefer reduced activity or No-Trade Regime Filter.
- Do not force a strategy when signals conflict. Explain what evidence would be needed to upgrade from No-Trade.

## Regime Classification

Classify the macro-cycle backdrop into exactly one of these:

- Fed cutting / QE / liquidity increase
- Inflation rising / Fed may hike or stay restrictive
- Recession risk rising
- Recovery after recession
- Mixed / transition regime

Then classify today's FX execution regime into exactly one of these:

- Macro Trend
- Trend Pullback
- Range Market
- Breakout Watch
- Post-News Confirmation
- High Volatility Shock
- No Clear Edge

Use confidence levels:

- High
- Medium
- Low

## Core Capital-Flow Logic

Use this as the baseline framework, then revise it if the latest evidence conflicts:

| Macro environment | Typical capital flow |
| --- | --- |
| Fed cutting / QE / liquidity increase | Stocks up, gold up, USD down |
| Inflation rising / Fed may hike or stay restrictive | Yields up, USD up, gold down or sideways |
| Recession risk rising | Stocks down, bonds up, early USD strength |
| Recovery after recession | Stocks up, gold up, USD down |

## Output Schema

Return the report in Markdown using exactly these sections and headings.

### 1. Executive Summary

- Current regime:
- One-line conclusion:
- Today's primary strategy decision:
- Highest conviction FX / cross-asset flow view:
- Main uncertainty:

### 2. Regime Classification

- Macro-cycle regime:
- FX execution regime:
- Confidence: High / Medium / Low
- Why these regimes fit:
- Why they may be wrong:

### 3. Evidence Table

| Category | Latest Reading | Previous / Trend | Market Interpretation | Source / Date |
| --- | ---: | ---: | --- | --- |
| CPI | | | | |
| Core CPI | | | | |
| PCE | | | | |
| Core PCE | | | | |
| PPI | | | | |
| NFP | | | | |
| Unemployment | | | | |
| Jobless Claims | | | | |
| JOLTS | | | | |
| Wage Growth | | | | |
| GDP | | | | |
| ISM Manufacturing | | | | |
| ISM Services | | | | |
| Fed Funds | | | | |
| 2Y Yield | | | | |
| 10Y Yield | | | | |
| 30Y Yield | | | | |
| 2s10s Curve | | | | |
| 3m10y Curve | | | | |
| 5Y Real Yield | | | | |
| 10Y Real Yield | | | | |
| Fed Balance Sheet | | | | |
| Reverse Repo / TGA / Liquidity | | | | |

### 4. Daily Bias Score Table

| Factor | Score (-2 to +2) | Reason | Source / Date |
| --- | ---: | --- | --- |
| USD Bias | | | |
| Risk Sentiment | | | |
| US Rates Bias | | | |
| Equity Sentiment | | | |
| Commodity / Gold Bias | | | |
| Volatility Regime | | | |
| Event Risk | | | |
| Trend Strength | | | |
| Range Strength | | | |
| Confidence | | | |

### 5. Fed Policy Read-through

- Current Fed stance:
- Market-implied next move:
- Hike / pause / cut probability narrative:
- What would change the Fed path:
- Key Fed communication to monitor:

### 6. Cross-Asset Flow Map

| Asset | Bias | Reason | Confidence |
| --- | --- | --- | --- |
| USD | Bullish / Neutral / Bearish | | |
| Gold | Bullish / Neutral / Bearish | | |
| S&P 500 | Bullish / Neutral / Bearish | | |
| Nasdaq | Bullish / Neutral / Bearish | | |
| US Bonds | Bullish / Neutral / Bearish | | |
| Bond Yields | Higher / Neutral / Lower | | |
| VIX | Bullish / Neutral / Bearish | | |
| Crude Oil | Bullish / Neutral / Bearish | | |

### 7. Today's Strategy Decision

- Primary Strategy:
- Why this is the primary strategy:
- Secondary Strategy:
- Conditions required to activate the secondary strategy:
- Strategies to Avoid:
- Why to avoid them today:
- No-Trade Conditions:
- Confidence Level:
- Research posture: normal watchlist / reduced watchlist / zero prioritized setups

### 8. FX Pair Watchlist

Suggest 3 to 5 FX pairs only if there is sufficient edge. If there is no edge, state that no pair should be prioritized. Consider G10 majors, G10 crosses, and EM FX; prefer the pairs that express the selected strategy most cleanly.

| Pair | Base / Quote Convention | Directional Bias | Strategy Fit | Best Session / Liquidity Window | Confirmation Trigger | Key Invalidation | TradingView / Broker Symbol |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Example: EUR/USD | EUR base, USD quote | Bullish / Neutral / Bearish | | London / New York / overlap / post-event only | | | EURUSD / broker-dependent |

### 9. Execution Guidance

- Trade timing: before event / after event only / Asia / London / New York / no trade
- Best liquidity window:
- Pair types to prioritize:
- Pair types to avoid:
- Spread / liquidity concerns:
- What would invalidate today's strategy choice:
- What timeframe this view applies to:

### 10. Upcoming Catalysts

| Date | Event | Why It Matters | Possible Regime Impact |
| --- | --- | --- | --- |

### 11. Conflicting Evidence

- Bullish USD evidence:
- Bearish USD evidence:
- Bullish gold evidence:
- Bearish gold evidence:
- Risk-on evidence:
- Risk-off evidence:
- Evidence supporting higher yields:
- Evidence supporting lower yields:

### 12. Facts / Assumptions / Opinions

#### Facts

-

#### Assumptions

-

#### Opinions / Interpretations

-

### 13. Regime Kill Criteria

The current regime view should be downgraded or changed if:

-
-
-

### 14. Next Research Step

Define what Step 2 should verify:

- COT positioning to check:
- Volume / value-area confirmation to check:
- Strategy rule to verify:
- Instruments to prioritize:
- Instruments to avoid:
- Data releases that must be reviewed before acting:

## Quality Bar

- Use recent, dated sources.
- Prefer primary or authoritative sources such as BLS, BEA, Federal Reserve, Treasury, FRED, ISM/S&P Global PMI, CME FedWatch, CFTC COT, and major exchange data.
- Separate facts, assumptions, and interpretations.
- Highlight stale data, conflicting signals, and missing context.
- Do not claim certainty when the evidence is mixed.
- Do not output raw JSON.
