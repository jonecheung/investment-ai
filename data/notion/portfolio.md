# Notion Portfolio Database Schema v1

Snapshot date: 2026-06-06

> **Status notice:** This document is **provisional**. Portfolio sizing and execution schemas are deferred pending a separate redesign. Cross-references to trading proposal price fields may be stale; the canonical Trading Proposals schema is in [`data/notion/research.md`](research.md) (two-layer model, single `Entry Price` / `Target Price`). This file still references legacy proposal fields such as `Entry Reference` and `Target 1`; update when portfolio sizing is redesigned.

This document defines the Notion database schema needed to reconstruct the portfolio and trading history system without copying any data. It includes database names, property names, property types, select options, and relation setup only.

Related research schema:

- `data/notion/research.md` (Trading Proposals section)

## Scope

- Databases covered:
  - Accounts
  - Trades
  - Cash Movements
  - Position Snapshots
  - Proposal Sizing
- Excluded:
  - Page IDs, database IDs, data source IDs, property IDs, URLs, commands, prompts, raw rows, and workspace-specific artifacts.
  - Raw brokerage exports, full statements, tax documents, credentials, and account secrets.

## Design Notes

- Target storage: Notion databases.
- Use Notion `number` for money values, prices, and quantities.
- Use Notion `date` for event timestamps and settlement dates.
- Store `symbol`, `market`, `asset_type`, and `currency` directly on trade and snapshot rows at first.
- Keep `source` and `external_id` fields for future CSV/API import deduplication.
- Keep instrument normalization out of scope for now. Add a separate instruments database only if cross-market normalization becomes difficult to manage inline.
- Pricing fields (entry, stop, target) belong on `Trading Proposals`. Size fields belong on `Proposal Sizing`.
- Do not store credentials, API keys, full account numbers, raw brokerage exports, tax documents, or full statements.
- Do not apply Notion portfolio database structure changes without first summarizing intended changes and receiving explicit confirmation.

## Accounts

Purpose: broker or exchange accounts used for portfolio tracking and trade attribution.

| Property | Type | Notes |
| --- | --- | --- |
| `Account` | title | Display name for the account. |
| `Provider` | rich_text | Broker, exchange, or custodian name. |
| `Base Currency` | select | Account reporting currency. Current options: `HKD`, `USD`, `JPY`, `CNY`, `OTHER`. |
| `Notes` | rich_text | Optional account notes. |

## Trades

Purpose: executed buy and sell records. Instrument details are kept inline for the first version.

| Property | Type | Notes |
| --- | --- | --- |
| `Trade` | title | Human-readable label, typically `<symbol> <side> <traded_at>`. |
| `Account` | relation | Relation to Accounts. |
| `Symbol` | rich_text | Tradable symbol or instrument identifier. |
| `Market` | select | Current options: `HK`, `JP`, `US`, `OTHER`. |
| `Asset Type` | select | Current options: `equity`, `etf`, `bond`, `future`, `option`, `crypto`, `other`. |
| `Side` | select | Current options: `buy`, `sell`. |
| `Quantity` | number | Executed quantity. |
| `Price` | number | Executed price in quote currency. |
| `Currency` | select | Quote or settlement currency. Current options: `HKD`, `USD`, `JPY`, `CNY`, `OTHER`. |
| `Fees` | number | Trading fees. Default to 0 when unknown. |
| `Taxes` | number | Taxes withheld or paid. Default to 0 when unknown. |
| `Net Amount` | number | Net cash impact when available. |
| `Traded At` | date | Execution timestamp. |
| `Settlement Date` | date | Settlement date when applicable. |
| `Source` | rich_text | Import source label, for example `manual`, `broker_csv`, `api`. |
| `External ID` | rich_text | Source-system identifier for deduplication. |
| `Proposal` | relation | Optional relation to Trading Proposals. |
| `Proposal Sizing` | relation | Optional relation to Proposal Sizing row that informed the trade. |
| `Notes` | rich_text | Optional trade notes. |

### Trades Relations

- `Trades.Account`
  - Type: relation
  - Target: Accounts
- `Trades.Proposal`
  - Type: relation
  - Target: Trading Proposals
- `Trades.Proposal Sizing`
  - Type: relation
  - Target: Proposal Sizing

## Cash Movements

Purpose: cash events that are not ordinary executed buy/sell trades.

| Property | Type | Notes |
| --- | --- | --- |
| `Movement` | title | Human-readable label, typically `<movement_type> <amount> <currency>`. |
| `Account` | relation | Relation to Accounts. |
| `Currency` | select | Current options: `HKD`, `USD`, `JPY`, `CNY`, `OTHER`. |
| `Amount` | number | Signed or unsigned amount per workflow convention. |
| `Movement Type` | select | Current options: `deposit`, `withdrawal`, `dividend`, `interest`, `fee`, `tax`, `adjustment`. |
| `Occurred At` | date | Event timestamp. |
| `Settlement Date` | date | Settlement date when applicable. |
| `Related Trade` | relation | Optional relation to Trades. |
| `Source` | rich_text | Import source label. |
| `External ID` | rich_text | Source-system identifier for deduplication. |
| `Notes` | rich_text | Optional movement notes. |

### Cash Movements Relations

- `Cash Movements.Account`
  - Type: relation
  - Target: Accounts
- `Cash Movements.Related Trade`
  - Type: relation
  - Target: Trades

## Position Snapshots

Purpose: periodic portfolio snapshots for reconciliation against broker or API data.

| Property | Type | Notes |
| --- | --- | --- |
| `Snapshot` | title | Human-readable label, typically `<symbol> <snapshot_date>`. |
| `Account` | relation | Relation to Accounts. |
| `Snapshot Date` | date | Snapshot as-of date. |
| `Symbol` | rich_text | Tradable symbol or instrument identifier. |
| `Market` | select | Current options: `HK`, `JP`, `US`, `OTHER`. |
| `Asset Type` | select | Current options: `equity`, `etf`, `bond`, `future`, `option`, `crypto`, `other`. |
| `Currency` | select | Current options: `HKD`, `USD`, `JPY`, `CNY`, `OTHER`. |
| `Quantity` | number | Position quantity at snapshot time. |
| `Avg Cost` | number | Average cost when available. |
| `Market Price` | number | Mark-to-market price at snapshot time. |
| `Market Value` | number | Position market value at snapshot time. |
| `Source` | rich_text | Import source label. |
| `External ID` | rich_text | Source-system identifier for deduplication. |
| `Notes` | rich_text | Optional snapshot notes. |

### Position Snapshots Relations

- `Position Snapshots.Account`
  - Type: relation
  - Target: Accounts

## Proposal Sizing

Purpose: Layer 3 portfolio sizing output. Combines an accepted, price-enriched trading proposal with portfolio state to determine quantity, notional, and risk at stop. This database stores size only; pricing levels remain on `Trading Proposals`.

| Property | Type | Notes |
| --- | --- | --- |
| `Sizing` | title | Human-readable label, typically `<proposal> sizing <sizing_as_of>`. |
| `Proposal` | relation | Relation to Trading Proposals. |
| `Account` | relation | Relation to Accounts. |
| `Sizing As Of` | date | Timestamp when portfolio inputs were captured. |
| `Portfolio NAV` | number | Portfolio net asset value at sizing time. |
| `Cash Available` | number | Available cash at sizing time. |
| `Entry Reference` | number | Copied from proposal pricing for audit at sizing time. |
| `Stop Price` | number | Copied from proposal pricing for audit at sizing time. |
| `Target 1` | number | Copied from proposal pricing for audit at sizing time. |
| `Risk Budget Pct` | number | Portfolio risk budget allocated to this trade, as a percent of NAV. |
| `Risk Budget Amount` | number | Portfolio risk budget allocated to this trade, in currency. |
| `Quantity` | number | Sized quantity to order. |
| `Notional` | number | Sized cash amount at entry reference. |
| `Portfolio Weight Pct` | number | Sized position as a percent of NAV. |
| `Max Loss At Stop` | number | Estimated loss if stop is hit at sized quantity. |
| `Board Lots` | number | Rounded lot count for HK/JP workflows when applicable. |
| `Sizing Status` | select | Current options: `ready`, `rejected`, `stale`. |
| `Rejection Reason` | rich_text | Why sizing was rejected, if applicable. |
| `Notes` | rich_text | Optional sizing notes. |

### Proposal Sizing Relations

- `Proposal Sizing.Proposal`
  - Type: relation
  - Target: Trading Proposals
- `Proposal Sizing.Account`
  - Type: relation
  - Target: Accounts

## Cross-Database Flow

Canonical proposal schema including Layer 2 pricing fields: `data/notion/research.md` (Trading Proposals section).

1. Research outputs create or update `Trading Proposals` (Layer 1 qualitative fields).
2. Alpha Vantage last close updates `Last Price` and `Quote As Of` on the proposal.
3. An external process updates entry/stop/target pricing fields and sets `Pricing Status = Ready`.
4. Portfolio sizing creates one `Proposal Sizing` row per accepted proposal and account when Layer 2 preconditions are met.
5. Manual execution creates one `Trades` row linked to `Proposal Sizing` and optionally `Trading Proposals`.
6. `Position Snapshots` and `Cash Movements` support reconciliation over time.

## Proposal Sizing Preconditions

Layer 3 runs only when the linked `Trading Proposals` row satisfies all of the following:

| Requirement | Proposal field / source |
| --- | --- |
| Human approval | `Status` = `Accepted` |
| Pricing complete | `Pricing Status` = `Ready` |
| Entry reference | `Entry Reference` populated |
| Stop level | `Stop Price` populated |
| Primary target | `Target 1` populated |
| Account selected | Target `Accounts` row for sizing |
| Portfolio inputs | `Portfolio NAV`, `Cash Available` from latest `Position Snapshots`, approved manual inputs, or account-level summary |

At sizing time, copy `Entry Reference`, `Stop Price`, and `Target 1` from the proposal onto the `Proposal Sizing` row as an audit snapshot. Do not re-derive pricing on the sizing row.

After a successful sizing run:

- Create or update the canonical `Proposal Sizing` row with `Sizing Status` = `ready`.
- Mirror summary readiness on the linked proposal: `Sizing Status` = `Ready`.

The proposal-level `Sizing Status` is a summary mirror only. Canonical sizing outputs (`Quantity`, `Notional`, `Max Loss At Stop`, etc.) live on `Proposal Sizing`.

## Reconstruction Order

1. Create a database named `Accounts`.
2. Add the `Accounts` properties listed above.
3. Create a database named `Trades`.
4. Add the non-relation `Trades` properties listed above.
5. Add `Trades.Account`, `Trades.Proposal`, and `Trades.Proposal Sizing` relations.
6. Create a database named `Cash Movements`.
7. Add the non-relation `Cash Movements` properties listed above.
8. Add `Cash Movements.Account` and `Cash Movements.Related Trade` relations.
9. Create a database named `Position Snapshots`.
10. Add the non-relation `Position Snapshots` properties listed above.
11. Add `Position Snapshots.Account` relation.
12. Create a database named `Proposal Sizing`.
13. Add the non-relation `Proposal Sizing` properties listed above.
14. Add `Proposal Sizing.Proposal` and `Proposal Sizing.Account` relations.
