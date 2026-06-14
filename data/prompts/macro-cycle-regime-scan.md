# Prompt: Macro Cycle Regime Scan

## Purpose

Run a standardized macro-cycle scan for swing trading research before the European trading session.

The report should classify the current macro regime, map likely cross-asset capital flows, and define what the next research step should verify through COT positioning, volume profile, and auction-market context.

This is research and scenario analysis only. Do not provide personalized financial advice, position sizing, trade execution instructions, or portfolio allocation.

## Task

Analyze the current US and global macro cycle for swing trading strategy selection.

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

## Regime Classification

Classify the current regime into exactly one of these:

- Fed cutting / QE / liquidity increase
- Inflation rising / Fed may hike or stay restrictive
- Recession risk rising
- Recovery after recession
- Mixed / transition regime

Use confidence levels:

- High
- Medium
- Low

## Core Capital-Flow Logic

Use this as the baseline framework, then revise it if the latest evidence conflicts:

| Macro environment | Typical capital flow |
| --- | --- |
| Fed cutting / QE / liquidity increase | Stocks up, gold up, USD down, crypto up |
| Inflation rising / Fed may hike or stay restrictive | Yields up, USD up, gold down or sideways |
| Recession risk rising | Stocks down, bonds up, early USD strength |
| Recovery after recession | Stocks up, gold up, USD down |

## Output Schema

Return the report in Markdown using exactly these sections and headings.

### 1. Executive Summary

- Current regime:
- One-line conclusion:
- Highest conviction asset-flow view:
- Main uncertainty:

### 2. Regime Classification

- Selected regime:
- Confidence: High / Medium / Low
- Why this regime fits:
- Why it may be wrong:

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

### 4. Fed Policy Read-through

- Current Fed stance:
- Market-implied next move:
- Hike / pause / cut probability narrative:
- What would change the Fed path:
- Key Fed communication to monitor:

### 5. Cross-Asset Flow Map

| Asset | Bias | Reason | Confidence |
| --- | --- | --- | --- |
| USD | Bullish / Neutral / Bearish | | |
| Gold | Bullish / Neutral / Bearish | | |
| S&P 500 | Bullish / Neutral / Bearish | | |
| Nasdaq | Bullish / Neutral / Bearish | | |
| US Bonds | Bullish / Neutral / Bearish | | |
| Bond Yields | Higher / Neutral / Lower | | |
| VIX | Bullish / Neutral / Bearish | | |
| Crypto | Bullish / Neutral / Bearish | | |
| Crude Oil | Bullish / Neutral / Bearish | | |

### 6. FX Bias Table

| Pair | Bias | Macro Driver | Key Invalidation |
| --- | --- | --- | --- |
| EUR/USD | Bullish / Neutral / Bearish | | |
| GBP/USD | Bullish / Neutral / Bearish | | |
| USD/JPY | Bullish / Neutral / Bearish | | |
| AUD/USD | Bullish / Neutral / Bearish | | |
| USD/CAD | Bullish / Neutral / Bearish | | |
| AUD/CAD | Bullish / Neutral / Bearish | | |
| EUR/CHF | Bullish / Neutral / Bearish | | |

### 7. Strategy Implications

- Best regime-fit strategy:
  - Trend following
  - Failed auction reversal
  - Range mean reversion
  - No-trade / wait
- Best candidate markets:
- Avoided markets:
- Why:
- What timeframe this view applies to:

### 8. Upcoming Catalysts

| Date | Event | Why It Matters | Possible Regime Impact |
| --- | --- | --- | --- |

### 9. Conflicting Evidence

- Bullish USD evidence:
- Bearish USD evidence:
- Bullish gold evidence:
- Bearish gold evidence:
- Risk-on evidence:
- Risk-off evidence:
- Evidence supporting higher yields:
- Evidence supporting lower yields:

### 10. Facts / Assumptions / Opinions

#### Facts

-

#### Assumptions

-

#### Opinions / Interpretations

-

### 11. Regime Kill Criteria

The current regime view should be downgraded or changed if:

-
-
-

### 12. Next Research Step

Define what Step 2 should verify:

- COT positioning to check:
- Volume / value-area confirmation to check:
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
