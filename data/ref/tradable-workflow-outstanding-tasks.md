# Outstanding Tasks: Tradable Proposal Two-Layer Workflow

Snapshot date: 2026-06-06

Purpose: handoff note for implementing the documented two-layer workflow in a new chat. Trading proposals schema and workspace rules are done; runnable workflow automation is not. Portfolio sizing and execution are deferred.

Canonical references:

- `data/notion/research.md` — Trading Proposals section: Layer 1 + Layer 2 price plan (30 properties)
- `data/notion/portfolio.md` — provisional; sizing + execution history (deferred redesign)
- `AGENTS.md` — Tradable Proposal Layers section
- `README.md` — Tradable Proposal Layers section

## Already Done (Docs / Rules Only)

- [x] Canonical Trading Proposals schema with two-layer model
- [x] Simplified Layer 2: single `Entry Price`, `Stop Price`, `Target Price` (6 price-plan fields)
- [x] Removed Layer 3 fields from trading proposals schema (`Sizing Status`, sizing preconditions)
- [x] Trading Proposals schema in `data/notion/research.md` (v2, two-layer model)
- [x] Workflow documented in `AGENTS.md` and `README.md`
- [x] Neon removed; portfolio target is Notion

## Outstanding Tasks

Adopt in this order where possible.

### 1. Notion Structure Migration (Foundation)

Apply documented schemas in Notion (requires explicit confirmation before writes).

**Trading Proposals**

- [ ] Remove obsolete fields if present (`Entry Criteria`, `Core Thesis`, `Schema Version`, `Sizing Status`, zone/target variants, etc.)
- [ ] Add Layer 1 fields: `Instrument ID`, `Intent`, consolidated `Invalidation`, `Watchpoints`, `Conviction`
- [ ] Add workflow field: `Pricing Status`
- [ ] Add Layer 2 price-plan fields (6 fields): `Quote As Of`, `Last Price`, `Entry Price`, `Stop Price`, `Target Price`, `Pricing Notes`
- [ ] Configure all select options per schema doc
- [ ] Confirm `Run` and `Idea` relations

**Portfolio track** (deferred — create when sizing schema is redesigned)

- [ ] `Accounts`
- [ ] `Trades`
- [ ] `Cash Movements`
- [ ] `Position Snapshots`
- [ ] `Proposal Sizing`
- [ ] Wire relations: proposal ↔ sizing ↔ trades ↔ accounts

### 2. Layer 1 — Research Import Alignment

Current skills still expect the old 35-field Trading Proposals shape.

- [ ] Update `followup-tradable-tickers-curl` import mapping to canonical simple schema (consolidated `Invalidation`, `Watchpoints`, `Conviction`, etc.)
- [ ] Set defaults on import: `Status = Proposed`, `Pricing Status = Not Started`
- [ ] Optionally align `followup-tradable-tickers` (non-curl) or retire it
- [ ] Validate Notion property names exist before import

**Deferred in prior pass:** curl skill update was explicitly out of scope.

### 3. Layer 2 — Price Plan Workflow

Documented split:

- Alpha Vantage → `Last Price`, `Quote As Of` only
- External process (out of repo) → `Entry Price`, `Stop Price`, `Target Price`, `Pricing Notes`, `Pricing Status = Ready`

- [ ] Define human gate: `Status = Accepted` → `Pricing Status = Pending`
- [ ] Build or script AV last-close fetch for accepted proposals (`alphavantage-curl` skill)
- [ ] Symbol normalization: `Ticker` → `Instrument ID` for AV lookups (HK/JP/US)
- [ ] Document or implement external price-plan process
- [ ] Staleness handling: large price move or manual review → `Pricing Status = Stale`

### 4. Portfolio Sizing Workflow (Deferred)

Out of scope until `data/notion/portfolio.md` is redesigned.

- [ ] Redesign `Proposal Sizing` schema aligned to simplified `Entry Price` / `Target Price`
- [ ] Define sizing preconditions and audit snapshot fields
- [ ] Implement sizing run (rules, spreadsheet, or future skill)

### 5. Execution Workflow (Deferred)

- [ ] Pre-trade checklist: pricing ready, not stale, instrument validated
- [ ] Log fills in `Trades` linked to `Trading Proposals`
- [ ] Reconciliation habit: `Position Snapshots`, `Cash Movements`
- [ ] Archive or update proposal `Status` after execution

### 6. Operational Views / Rhythm

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

## Explicitly Deferred (Lower Priority)

- Portfolio sizing and execution schemas (`data/notion/portfolio.md` redesign)
- New prompts/JSON schemas for pricing runs
- New agent skills beyond Layer 1 import alignment
- Automated staleness monitoring
- Full broker CSV/API portfolio import
- Instruments normalization database

## Suggested First Slice for New Chat

1. Notion schema migration (`Trading Proposals` only)
2. Layer 1 import skill alignment (`followup-tradable-tickers-curl`)
3. AV last-close step for accepted proposals
