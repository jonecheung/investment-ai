# Prompt: Follow-up Tradable Focus Markets

## Purpose

Identify tradable opportunities related to a prior deep-research result and convert them into structured, research-ready opportunity hypotheses for the current beginner focus list only.

Use this prompt only as a follow-up task chained to an existing deep-research interaction.

## Inputs

- `previous_interaction_id`: Prior provider interaction ID used to supply deep-research context.
- `prior_research_context`: The thesis, evidence, risks, and conclusions from the previous research interaction.
- `focus_markets`: Current allowed instruments only. Default and hard limit: `XAUUSD`, `EURUSD`, `USDJPY`.
- `analysis_timeframe`: Time horizon for the opportunity scan. Default: `mixed`.

## Current Focus List (Hard Limit)

Only these instruments are allowed in `ticker_opportunities[]`:

| Ticker | Instrument | Asset Class | Market | Primary Role |
| --- | --- | --- | --- | --- |
| `XAUUSD` | Gold / US Dollar | `other` | `OTHER` | Primary opportunity market; USD, real yields, Fed, risk sentiment |
| `EURUSD` | Euro / US Dollar | `fx` | `FX_MAJOR` | FX benchmark / liquidity anchor |
| `USDJPY` | US Dollar / Japanese Yen | `fx` | `FX_MAJOR` | USD, yields, JPY safe-haven expression |

Do **not** output any other ticker, including GBPUSD, GBPJPY, EURJPY, AUDUSD, NZDUSD, USDCAD, USDCHF, EM FX, indices, equities, ETFs, or crypto.

## Task

Follow up on the prior deep-research context and identify whether any of the three allowed instruments have a credible opportunity hypothesis.

For each allowed instrument that has a credible relationship to the research:

1. Explain how it relates to the research thesis through policy divergence, carry, growth/inflation differentials, flow, liquidity, intervention, or cross-asset linkages.
2. Provide a research hypothesis, including trade direction, event or observation-based entry criteria, exit criteria, conviction, and the key invalidation event.
3. Surface assumptions, open questions, and monitoring signals that would help validate or reject the hypothesis.

## Analysis Requirements

- Start from the prior research thesis, not a generic FX screener.
- Include only `XAUUSD`, `EURUSD`, and/or `USDJPY` when they have a clear relationship to the thesis.
- Do not broaden the universe to express the thesis more cleanly. If another pair would express the thesis better, mention that limitation in `output_quality.missing_information` or `output_quality.uncertainty_notes`, but do **not** output it as a proposal.
- Consider pair/instrument convention, quote currency, tick/pip size, primary session, liquidity, policy sensitivity, macro sensitivity, and broker/symbol mapping.
- Treat `XAUUSD` separately from FX majors: state gold quote/tick convention, volatility scale, session liquidity, and macro drivers (USD, real yields, Fed expectations, risk sentiment).
- Clearly separate evidence from assumptions and uncertainty.

## Constraints

- This is research framing only, not personalized investment advice.
- Do not provide trade instructions, position sizing, or portfolio allocation recommendations.
- Keep entry and exit criteria non-quantitative and based on observable events or evidence.
- `relationship_to_research` must be free text, not categorical labels.
- If evidence is limited, include fewer instruments and lower conviction accordingly.
- Output **at most three** `ticker_opportunities[]` records.
- Output **zero** records if none of `XAUUSD`, `EURUSD`, or `USDJPY` has a credible relationship to the prior research.
- Do not invent pair relationships when the prior research context is insufficient.

## Output Format

Return JSON only.

The output must conform to `data/parallel/output-tradable-tickers.json`.

If no credible pair opportunities are found, return:

- `ticker_opportunities`: an empty array
- `output_quality.missing_information`: the information needed to identify credible pairs
- `output_quality.uncertainty_notes`: why the available evidence is insufficient

## Quality Bar

A good output is specific, falsifiable, and explicit about why each pair matters to the thesis.

Each opportunity should make clear:

- the market bucket (`FX_MAJOR` or `OTHER`), venue, quote currency, and asset class
- the causal link to the research thesis
- the core research hypothesis
- what would invalidate the view
- what signals should be monitored next

## Missing Context Handling

If the prior research context is missing, too thin, or points mainly to instruments outside `XAUUSD`, `EURUSD`, and `USDJPY`, do not guess or broaden the universe. Return an empty `ticker_opportunities` array, describe the missing context or out-of-scope instruments in `output_quality.missing_information`, and use the required schema fields to summarize the limitation.
