# Outstanding Tasks: Tradable Proposal Three-Layer Workflow

Snapshot date: 2026-06-06

Purpose: handoff note for implementing the documented three-layer workflow in a new chat. Schemas and workspace rules are done; runnable workflow automation is not.

Canonical references:

- `data/schema-notion-trading-proposals-simple.md` — Layer 1 + Layer 2 pricing (39 fields)
- `data/schema-notion-portfolio.md` — Layer 3 sizing + execution history
- `AGENTS.md` — Tradable Proposal Layers section
- `README.md` — Tradable Proposal Layers section

## Already Done (Docs / Rules Only)

- [x] Canonical Trading Proposals schema with three-layer model
- [x] Portfolio schema with `Proposal Sizing`, `Trades`, etc.
- [x] Deprecation notice on historical Trading Proposals in `schema-notion-research.md`
- [x] Workflow documented in `AGENTS.md` and `README.md`
- [x] Neon removed; portfolio target is Notion

## Outstanding Tasks

Adopt in this order where possible.

### 1. Notion Structure Migration (Foundation)

Apply documented schemas in Notion (requires explicit confirmation before writes).

**Trading Proposals**

- [ ] Remove obsolete fields if present (`Entry Criteria`, `Core Thesis`, `Schema Version`, etc.)
- [ ] Add Layer 1 workflow fields: `Instrument ID`, `Intent`, `Pricing Status`, `Sizing Status`
- [ ] Add Layer 2 pricing fields (14 fields): `Quote As Of`, `Last Price`, `Entry Type`, `Entry Low`, `Entry High`, `Entry Reference`, `Stop Price`, `Target 1`, `Target 2`, `Risk Per Unit`, `Reward Per Unit`, `Reward Risk Ratio`, `Plan Valid Until`, `Pricing Notes`
- [ ] Configure all select options per schema doc
- [ ] Confirm `Run` and `Idea` relations

**Portfolio track** (create if missing)

- [ ] `Accounts`
- [ ] `Trades`
- [ ] `Cash Movements`
- [ ] `Position Snapshots`
- [ ] `Proposal Sizing`
- [ ] Wire relations: proposal ↔ sizing ↔ trades ↔ accounts

### 2. Layer 1 — Research Import Alignment

Current skills still expect the old 35-field Trading Proposals shape.

- [ ] Update `followup-tradable-tickers-curl` import mapping to canonical simple schema (consolidated `Invalidation`, `Watchpoints`, `Conviction`, etc.)
- [ ] Set defaults on import: `Status = Proposed`, `Pricing Status = Not Started`, `Sizing Status = Not Applicable`
- [ ] Optionally align `followup-tradable-tickers` (non-curl) or retire it
- [ ] Validate Notion property names exist before import

**Deferred in prior pass:** curl skill update was explicitly out of scope.

### 3. Layer 2 — Pricing Workflow

Documented split:

- Alpha Vantage → `Last Price`, `Quote As Of` only
- External process (out of repo) → entry/stop/target levels, `Pricing Status = Ready`

- [ ] Define human gate: `Status = Accepted` → `Pricing Status = Pending`
- [ ] Build or script AV last-close fetch for accepted proposals (`alphavantage-curl` skill)
- [ ] Symbol normalization: `Ticker` → `Instrument ID` for AV lookups (HK/JP/US)
- [ ] Document or implement external pricing process (entry/stop/target, `Plan Valid Until`, `Pricing Notes`)
- [ ] Compute derived fields after levels set: `Entry Reference`, `Risk Per Unit`, `Reward Per Unit`, `Reward Risk Ratio`
- [ ] Staleness handling: past `Plan Valid Until` or large price move → `Pricing Status = Stale` (and/or `Sizing Status = Stale`)

### 4. Layer 3 — Portfolio Sizing Workflow

Preconditions (see `schema-notion-portfolio.md`):

- `Status = Accepted`, `Pricing Status = Ready`
- `Entry Reference`, `Stop Price`, `Target 1` populated
- Account selected; NAV/cash available

- [ ] Seed portfolio data: at least one `Accounts` row
- [ ] Establish NAV/cash input source (`Position Snapshots` or approved manual input)
- [ ] Define risk policy (max % per name, max loss per trade, concentration limits)
- [ ] Implement sizing run (rules, spreadsheet, or future skill) → create `Proposal Sizing` row
- [ ] Copy audit snapshot from proposal: `Entry Reference`, `Stop Price`, `Target 1`
- [ ] Mirror readiness on proposal: `Sizing Status = Ready` (canonical outputs stay on `Proposal Sizing`)

### 5. Execution Workflow (Manual Bridge)

- [ ] Pre-trade checklist: pricing ready, sizing ready, not stale, instrument validated
- [ ] Log fills in `Trades` with links to `Proposal Sizing` and `Trading Proposals`
- [ ] Reconciliation habit: `Position Snapshots`, `Cash Movements`
- [ ] Archive or update proposal `Status` after execution

### 6. Operational Views / Rhythm

- [ ] Notion views filtered by `Status`, `Pricing Status`, `Sizing Status`
- [ ] Weekday execution mode: monitor accepted + pricing-ready + sizing-ready proposals
- [ ] Weekend research mode: Layer 1 import and qualitative review

## End-to-End Status Flow (Target)

```text
Import        → Status: Proposed,     Pricing: Not Started, Sizing: Not Applicable
Review        → Status: Reviewing
Accept        → Status: Accepted,     Pricing: Pending
AV last close → Last Price + Quote As Of populated
External      → Entry/Stop/Target populated, Pricing: Ready, Sizing: Pending
Sizing run    → Proposal Sizing row created, Sizing: Ready
Execute       → Manual broker order → Trades row
Archive       → Status: Archived
Stale         → Pricing and/or Sizing: Stale
```

## Explicitly Deferred (Lower Priority)

- New prompts/JSON schemas for pricing or sizing runs
- New agent skills beyond Layer 1 import alignment
- Automated staleness monitoring
- Full broker CSV/API portfolio import
- Instruments normalization database

## Suggested First Slice for New Chat

1. Notion schema migration (Trading Proposals + portfolio DBs)
2. Layer 1 import skill alignment (`followup-tradable-tickers-curl`)
3. AV last-close step for accepted proposals
