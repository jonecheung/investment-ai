# Prompt: Research Idea Brief

## Purpose

Convert a raw investment `Original Idea` into a concise, deep-research-ready brief.

The brief should help a buy-side style research workflow test whether the idea is valid, mispriced, and worthy of further diligence.

## Inputs

- `original_idea`: Raw investment idea entered by the user.
- `analysis_window`: Time range for the research brief. Default: last 7 days.
- `focus_markets`: Target FX buckets when specified. Default: G10 majors, G10 crosses, and EM FX (`FX_MAJOR`, `FX_CROSS`, `FX_EM`).
- `asset_focus`: Target asset classes when specified. Default: forex (spot FX) and FX-related derivatives.

## Task

Transform `original_idea` into a high-signal research brief for deep research.

Keep the brief specific, falsifiable, and evidence-seeking. Prioritize the questions and facts that would most efficiently validate, reject, or refine the thesis.

## Analysis Requirements

Focus strictly on these five sections:

1. Thesis clarity and variant view
2. Macro regime and cross-asset transmission
3. Policy, central banks, and positioning
4. Catalysts and timing
5. Risk and downside

Apply these cross-cutting checks in every section:

- central bank reaction functions, forward guidance, and policy divergence
- rates, inflation, real yields, carry, and term-premium shifts
- FX liquidity, intervention risk, and volatility regime changes
- positioning, crowding, CTA/systematic flows, and dealer gamma where relevant
- geopolitical, sanctions, and cross-border capital-flow scenarios

## Constraints

- Keep the final brief within 15,000 characters.
- Target 1,500-4,000 characters when possible.
- Prioritize high-signal content and remove low-value detail.
- Clearly separate facts, assumptions, and uncertainties.
- State what consensus likely believes versus the variant view.
- Include evidence that would invalidate the thesis.
- Prefer primary or authoritative sources to investigate first.
- Do not provide trade instructions, position sizing, portfolio allocation, or personalized investment advice.

## Output Format

Return a Markdown brief using exactly these sections:

1. `## Thesis Clarity And Variant View`
2. `## Macro Regime And Cross-Asset Transmission`
3. `## Policy, Central Banks, And Positioning`
4. `## Catalysts And Timing`
5. `## Risk And Downside`
6. `## Source Priorities`
7. `## Missing Context`

For `## Thesis Clarity And Variant View`, include:

- the core claim in 1-2 lines
- why it may be mispriced now
- consensus view versus variant view
- decisive disconfirming evidence

For `## Macro Regime And Cross-Asset Transmission`, include:

- growth, inflation, and liquidity regime
- key macro drivers and transmission channels into FX
- base regime versus adverse regime implications for the relevant pairs

For `## Policy, Central Banks, And Positioning`, include:

- central bank stance, credibility, and reaction-function asymmetry
- rate-path and balance-sheet implications
- positioning, flow, and positioning-risk context that reduces or supports conviction

For `## Catalysts And Timing`, include:

- concrete catalysts (data releases, central bank meetings, fiscal events, geopolitical windows) and impact mechanisms
- expected timing windows and dependency chain
- whether the thesis is near-term catalyst-driven or longer-duration carry/structural

For `## Risk And Downside`, include:

- downside paths and trigger conditions
- bear-case severity and major uncertainty nodes
- explicit kill criteria or thesis-break conditions

## Quality Bar

A good brief is concise, operational, and useful as direct input for deep research.

It should read like a checklist of what a research analyst needs to verify next, not like generic market commentary.

## Missing Context Handling

If crucial context is missing, state the gap in `## Missing Context` and list the minimum additional inputs needed to produce a sharper brief.
