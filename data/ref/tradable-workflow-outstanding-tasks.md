# Outstanding Tasks: Tradable Proposal Two-Layer Workflow

Snapshot date: 2026-06-06

Purpose: handoff note for implementing the documented two-layer workflow. Schema, docs, data layout, and Layer 1 import skill are aligned. Notion table migration and portfolio sizing remain deferred.

Canonical references:

- `data/notion/research.md` — Trading Proposals section: Layer 1 + Layer 2 price plan (30 properties)
- `data/notion/portfolio.md` — provisional; sizing + execution history (deferred redesign)
- `data/parallel/output-tradable-tickers.json` — Parallel follow-up output contract
- `AGENTS.md` — Tradable Proposal Layers section
- `README.md` — Tradable Proposal Layers section

## Already Done

- [x] Canonical Trading Proposals schema with two-layer model in `data/notion/research.md`
- [x] Simplified Layer 2: single `Entry Price`, `Stop Price`, `Target Price` (6 price-plan fields)
- [x] Removed Layer 3 fields from trading proposals schema (`Sizing Status`, sizing preconditions)
- [x] Trading Proposals schema merged into `data/notion/research.md` (v2)
- [x] `data/` reorganized: `notion/`, `parallel/`, `prompts/`, `ref/`
- [x] Docs and paths aligned (`AGENTS.md`, `README.md`, cross-links)
- [x] `followup-tradable-tickers-curl` import mapping aligned to `data/notion/research.md`
- [x] Retired `followup-tradable-tickers` (non-curl) skill
- [x] Workflow documented in `AGENTS.md` and `README.md`

## Outstanding Tasks

### 1. Layer 2 — Price Plan Workflow

Documented split:

- Alpha Vantage → `Last Price`, `Quote As Of` only
- External process (out of repo) → `Entry Price`, `Stop Price`, `Target Price`, `Pricing Notes`, `Pricing Status = Ready`

- [ ] Define human gate: `Status = Accepted` → `Pricing Status = Pending`
- [x] Build `refresh-proposal-quotes` skill for AV last-close fetch (`alphavantage-curl` patterns)
- [ ] Symbol normalization: `Ticker` → `Instrument ID` for AV lookups (HK/JP/US)
- [ ] Document or implement external price-plan process
- [ ] Staleness handling: large price move or manual review → `Pricing Status = Stale`

### 2. Operational Views / Rhythm

- [ ] Notion views filtered by `Status`, `Pricing Status`
- [ ] Weekday execution mode: monitor accepted + pricing-ready proposals
- [ ] Weekend research mode: Layer 1 import and qualitative review

## End-to-End Status Flow (Target)

```text
Import        → Status: Proposed,     Pricing: Not Started
Review        → Status: Reviewing
Accept        → Status: Accepted,     Pricing: Pending
AV last close → Last Price + Quote As Of populated
External      → Entry/Stop/Target populated, Pricing: Ready
Archive       → Status: Archived
Stale         → Pricing: Stale
```

## Deferred (Out of Current Scope)

### Notion Structure Migration

Apply documented schemas in Notion (requires explicit confirmation before writes).

**Trading Proposals**

- [ ] Remove obsolete fields if present (`Entry Criteria`, `Core Thesis`, `Schema Version`, etc.)
- [ ] Add Layer 1 fields: `Instrument ID`, `Intent`, consolidated `Invalidation`, `Watchpoints`, `Conviction`
- [ ] Add workflow field: `Pricing Status`
- [ ] Add Layer 2 price-plan fields (6 fields)
- [ ] Configure all select options per `data/notion/research.md`
- [ ] Confirm `Run` and `Idea` relations

**Portfolio track**

- [ ] Create portfolio DBs when `data/notion/portfolio.md` is redesigned
- [ ] `Accounts`, `Trades`, `Cash Movements`, `Position Snapshots`, `Proposal Sizing`

### Portfolio Sizing and Execution

- [ ] Redesign `data/notion/portfolio.md` aligned to `Entry Price` / `Target Price`
- [ ] Implement sizing run (rules, spreadsheet, or future skill)
- [ ] Pre-trade checklist and `Trades` logging workflow
- [ ] Reconciliation via `Position Snapshots`, `Cash Movements`

### Other

- New prompts/JSON schemas for pricing runs
- ~~`refresh-proposal-quotes` skill (AV last-close automation)~~ — skill added at `.agents/skills/refresh-proposal-quotes/SKILL.md`
- Automated staleness monitoring
- Full broker CSV/API portfolio import
- Instruments normalization database
- Simplifying `data/parallel/output-tradable-tickers.json` to match two-layer Notion fields

## Suggested Next Slice

1. Notion `Trading Proposals` table migration (when ready)
2. AV last-close step for accepted proposals
3. External price-plan process documentation
