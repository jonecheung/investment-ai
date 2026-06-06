# Personal Investment Assistant Workspace

This repository is a Cursor workspace for personal investment research, planning, and assistant workflows.

It is not a coding workspace. The assistant should avoid adding code, scripts, applications, notebooks, or software project scaffolding. If code is genuinely required by the user, the assistant must explain why, describe the files that would be created or changed, and ask for confirmation twice before proceeding.

## Purpose

This workspace is for:

- Investment research and analysis support
- Research idea intake, scheduling, and execution tracking
- Structured tradable ticker proposal research
- Portfolio review support
- Notion portfolio and trading history schema planning
- Market and product research
- Safe integration with external services through Cursor MCP
- Reusable assistant workflows through Agent Skills

This workspace is not for:

- Placing trades
- Moving money
- Storing credentials or account secrets
- Storing raw financial statements, tax files, or brokerage exports
- Producing financial, legal, or tax advice
- Building software projects or storing code by default

## Language And Scope

Default communication language is English unless otherwise requested.

Covered product types:

- Equities
- Derivatives
- ETFs
- Crypto assets

Covered markets:

- Hong Kong
- Japan
- United States

## High-Level Data Flow

The workspace separates research workflow data from portfolio and trading history data. Research outputs may support human review and monitoring, but they do not directly execute trades or move money.

```mermaid
flowchart TD
  subgraph IR[Idea Research Data Track]
    A[Original Idea]
    B[Research Ideas<br/>idea backlog and schedule]
    C[Research Brief<br/>expanded research input]
    D[Deep Research Run]
    E[Research Runs<br/>execution log]
    F[Research Results<br/>summary and result files]
    G[Updated Research Idea<br/>latest run, summary, recency]
  end

  subgraph TP[Tradable Proposal Track]
    H[Completed Research Context]
    I[Follow-up Opportunity Scan]
    J[Structured Ticker Opportunities]
    K[Trading Proposals<br/>Layer 1 qualitative + Layer 2 price plan]
  end

  subgraph PF[Portfolio Data Track]
    L[Approved Sanitized Portfolio Inputs]
    M[Notion Portfolio]
    N[Accounts]
    O[Trades]
    P[Cash Movements]
    Q[Position Snapshots]
    Sizing[Proposal Sizing]
  end

  A --> B --> C --> D --> E --> F --> G

  G --> H --> I --> J --> K

  K --> R[Human Review / Decision Support]
  R --> S[Watchlist / Monitoring / Possible Trade Framing]
  S -. only approved sanitized records .-> L

  L --> M
  M --> N
  M --> O
  M --> P
  M --> Q
  M --> Sizing
  N --> O
  N --> P
  N --> Q
  Sizing --> O

  Z[Safety Boundary<br/>Research only<br/>No trade execution or money movement<br/>No raw sensitive exports stored<br/>External writes require confirmation]
  Z --- R
  Z --- L
```

## Tradable Proposal Layers

Trading proposals follow a two-layer model documented in [`data/notion/research.md`](data/notion/research.md) (Trading Proposals section):

| Layer | What | Where |
| --- | --- | --- |
| Layer 1 | Qualitative hypothesis from research import | `Trading Proposals` |
| Layer 2 | Alpha Vantage last close + external single entry/stop/target prices | `Trading Proposals` price-plan fields |

Layer 2 uses Alpha Vantage for `Last Price` only; `Entry Price`, `Stop Price`, and `Target Price` come from an external process. Portfolio sizing and execution history are defined separately. No automated order placement.

## Workspace Structure

- `AGENTS.md`: Instructions for Cursor Agent behavior, safety boundaries, language preference, and workspace rules.
- `data/`: Sanitized examples, schemas, derived summaries, or pointers to approved external data sources.
- `.agents/skills/`: Project-level Agent Skills for repeatable assistant workflows.
- `.cursor/rules/`: Cursor project rules for safety and research workflows.
- `.cursor/mcp.json`: Project-level MCP configuration. It currently contains no live services or credentials.
- `.cursorignore`: Excludes sensitive or bulky files from Cursor context and indexing.

## Data Policy

Keep sensitive financial data outside this workspace by default.

Do not store credentials, API keys, access tokens, seed phrases, account numbers, tax identifiers, identity documents, full statements, raw exports, or tax forms.

Before saving any data into the workspace, the assistant should summarize what will be saved, where it will be saved, and whether it may contain sensitive financial or personal information.

## Notion Portfolio Schema Plan

Portfolio and trading history live in Notion. The first version should stay small and avoid a separate instruments database.

The saved schema is available at `data/notion/portfolio.md` for later reference before applying changes to Notion.

Recommended starting databases:

- `Accounts`: broker or exchange accounts, with a display name, provider, and base currency.
- `Trades`: executed buys and sells, storing symbol, market, asset type, side, quantity, price, currency, fees, taxes, timestamps, source, and external import ID.
- `Cash Movements`: deposits, withdrawals, dividends, interest, fees, taxes, and adjustments, with currency, amount, type, timestamps, source, and optional related trade.
- `Position Snapshots`: periodic position snapshots for reconciliation against broker or API data, including quantity, average cost, market price, and market value.
- `Proposal Sizing`: sized quantity and notional after combining an accepted trading proposal with portfolio state.

Implementation notes:

- Use Notion `number` for quantities and money values.
- Use Notion `date` for trade and cash movement timestamps.
- Use Notion relations for cross-database links such as trades to accounts, proposal sizing, and trading proposals.
- Keep `source` and `external_id` fields for import deduplication.
- Do not store credentials, account numbers, raw exports, tax documents, or full statements.
- Make Notion portfolio database structure changes only after explicit confirmation.

## Safety

The assistant must not place trades, move money, submit forms, open accounts, close accounts, change beneficiaries, or take irreversible financial actions.

All outputs should be treated as research and analysis support, not financial advice.