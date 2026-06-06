---
name: refresh-proposal-quotes
description: Fetch Alpha Vantage last daily close for Trading Proposals and update Notion Last Price and Quote As Of via curl. Use when refreshing proposal quotes, last close prices, or Layer 2 AV quote fields.
disable-model-invocation: true
---

# Refresh Proposal Quotes

Fetch the latest **daily close** from Alpha Vantage for one or more `Trading Proposals` rows, then update Notion `Last Price` and `Quote As Of` only.

This skill covers the **Alpha Vantage portion of Layer 2** per `data/notion/research.md`. It does **not** set `Entry Price`, `Stop Price`, `Target Price`, or `Pricing Notes`, and does **not** require qualitative review gates (`Status = Accepted`, `Pricing Status = Pending`).

This is market-data support only. Do not present retrieved prices as personalized investment advice.

## Fixed Defaults

- Alpha Vantage function: `TIME_SERIES_DAILY` with `outputsize=compact`
- Price field: latest bar `"4. close"` (unadjusted daily close)
- Notion fields written: `Last Price`, `Quote As Of` only
- Optional write-back: `Instrument ID` when AV lookup used a derived symbol and the field was empty
- Lookup symbol priority: `Instrument ID` → normalized symbol from `Ticker` + `Market`
- Notion writes: **on by default** after a successful AV fetch and update plan
- Batch rate limit: sleep **13 seconds** between Alpha Vantage requests (free-tier safe default)
- Notion API version: `2025-09-03`
- Data source discovery: search for `Trading Proposals` (fallback `Trade Proposals`)

## Inputs

Provide at least one selector:

- `--page-id <uuid>` — one proposal page ID
- `--ticker <symbol>` — match proposals where `Ticker` equals the value (case-sensitive trim)
- `--all` — every row in `Trading Proposals`
- `--missing-only` — only rows where `Last Price` is empty (default when using `--all` without `--force`)

Modifiers:

- `--force` — refresh even when `Last Price` is already populated
- `--dry-run` — fetch and preview AV results only; never write Notion
- `--confirm` — require explicit user confirmation before Notion writes (default is write without asking)

Deprecated (no longer required; default already writes):

- `--yes-update-notion` — accepted as a no-op alias for backward compatibility

If multiple selectors are supplied, process the union of matched rows and deduplicate by page ID.

## Write Defaults

- **Default:** after a successful fetch and update plan, write `Last Price` and `Quote As Of` to Notion without an extra confirmation gate.
- **`--dry-run`:** preview only; never write Notion.
- **`--confirm`:** show the preview and wait for explicit user confirmation before writing.
- Stop instead of writing when:
  - `--dry-run` is set
  - `--confirm` is set and interactive confirmation is unavailable
  - required Notion properties are missing
  - Alpha Vantage returned an error, rate-limit note, or empty series for a row
  - duplicate ticker matches require a user choice

## Steps

1. Load guidance:
   - Read `AGENTS.md`.
   - Read `.agents/skills/notion-api/SKILL.md`.
   - Read `.agents/skills/alphavantage-curl/SKILL.md`.
   - Read `data/notion/research.md` (Trading Proposals Layer 2 section).
   - Follow workspace safety and confirmation rules.

2. Validate auth and tools without exposing secrets:
   - Check `NOTION_API_TOKEN` from environment first, then `.env` if needed.
   - Check `ALPHAVANTAGE_API_KEY` from environment first, then `.env` if needed.
   - Confirm `curl` and `jq` are available.
   - Do not print raw token or API key values.

3. Resolve `Trading Proposals` data source (read-only):
   - Search Notion for data source titled `Trading Proposals`.
   - Fallback search: `Trade Proposals`, `Proposals`.
   - Retrieve schema with `GET /v1/data_sources/{data_source_id}`.
   - Required properties:
     - `Proposal` (title)
     - `Ticker` (rich_text)
     - `Market` (select)
     - `Last Price` (number)
     - `Quote As Of` (date)
   - Optional properties:
     - `Instrument ID` (rich_text)
     - `Pricing Status` (select) — read only; do not change unless user explicitly asks in the same request
   - If required properties are missing, stop and report gaps. Do not alter schema automatically.

4. Select proposal rows:
   - Query the data source with `POST /v1/data_sources/{data_source_id}/query`.
   - Paginate until all matches are collected when batching.
   - Apply selector filters from inputs.
   - For each row extract:
     - page ID
     - `Proposal` title
     - `Ticker`
     - `Market`
     - `Instrument ID` if present
     - current `Last Price`
     - current `Quote As Of`
   - If no rows match, report and stop.

5. Resolve Alpha Vantage symbol per row:
   - If `Instrument ID` is non-empty, use it as `AV_SYMBOL`.
   - Otherwise derive from `Ticker` and `Market`:

| Market | Rule | Example |
| --- | --- | --- |
| `US` | use `Ticker` as-is | `NVDA` → `NVDA` |
| `HK` | zero-pad numeric tickers to 4 digits, append `.HK` | `700` → `0700.HK`, `0700` → `0700.HK` |
| `JP` | append `.T` | `7203` → `7203.T` |
| `OTHER` | use `Ticker` as-is; report ambiguity | — |

   - Trim whitespace from tickers before normalization.
   - Record `lookup_source` as `instrument_id` or `normalized`.

6. Fetch last daily close from Alpha Vantage:
   - For each row, call:

```bash
curl -sG "https://www.alphavantage.co/query" \
  --data-urlencode "function=TIME_SERIES_DAILY" \
  --data-urlencode "symbol=${AV_SYMBOL}" \
  --data-urlencode "outputsize=compact" \
  --data-urlencode "datatype=json" \
  --data-urlencode "apikey=${ALPHAVANTAGE_API_KEY}"
```

   - Inspect the JSON before use:
     - `Error Message`
     - `Information`
     - `Note` (rate limit)
     - missing `"Time Series (Daily)"`
   - Extract latest bar:

```bash
echo "$response" | jq -r '
  ."Time Series (Daily)" // empty
  | if . == {} or . == null then empty else
      to_entries | sort_by(.key) | reverse | .[0]
      | {quote_date: .key, last_close: (.value."4. close" | tonumber?)}
    end
'
```

   - If extraction fails:
     - mark row as `failed`
     - include AV response summary (non-secret fields only)
     - continue to next row unless only one row was requested
   - Sleep 13 seconds before the next AV request when processing multiple rows.

7. Build Notion update plan:
   - For each successful fetch, prepare:
     - page ID
     - `Last Price` = `last_close`
     - `Quote As Of` = `quote_date` (ISO date `YYYY-MM-DD`)
     - optional `Instrument ID` write-back when lookup used normalization and field was empty
   - Do **not** modify `Entry Price`, `Stop Price`, `Target Price`, `Pricing Notes`, `Status`, or `Pricing Status`.
   - Present a preview table:
     - proposal title
     - market
     - ticker
     - AV symbol used
     - quote date
     - last close
     - previous last price
     - page ID
     - planned write action (`update` / `skip` / `failed`)

8. Notion write gate:
   - Show target data source name and ID.
   - Show exact rows and property values to update.
   - If `--dry-run`, stop here with the preview report.
   - If `--confirm`, ask for explicit confirmation before updating Notion.
   - Otherwise proceed to write Notion using the update plan (default).

9. Execute Notion updates:
   - Update each page sequentially with `PATCH /v1/pages/{page_id}`.
   - Example property payload:

```json
{
  "properties": {
    "Last Price": {"number": 123.45},
    "Quote As Of": {"date": {"start": "2026-06-05"}},
    "Instrument ID": {"rich_text": [{"text": {"content": "NVDA"}}]}
  }
}
```

   - Include `Instrument ID` only when step 7 planned a write-back.
   - Continue on per-row errors; collect failures.
   - Handle HTTP 429 with `Retry-After` backoff for Notion.

10. Final report:
    - data source name and ID
    - selector used
    - rows matched / updated / skipped / failed
    - per-row: ticker, AV symbol, quote date, last close, previous values, page ID
    - AV failures and Notion write failures (concise)
    - whether writes used default auto-write, `--confirm`, or `--dry-run`
    - reminder: daily close is end-of-day data; state market, currency context, and retrieval time

## Example Invocations

Refresh all proposals missing `Last Price` (writes to Notion by default):

```text
refresh-proposal-quotes --all --missing-only
```

Refresh one ticker:

```text
refresh-proposal-quotes --ticker NVDA
```

Preview without writes:

```text
refresh-proposal-quotes --all --dry-run
```

Force refresh every proposal:

```text
refresh-proposal-quotes --all --force
```

Require confirmation before writes:

```text
refresh-proposal-quotes --all --confirm
```

## Out of Scope

- Setting `Pricing Status`, `Status`, or external price-plan fields
- Requiring `Accepted` / `Pending` gates
- Staleness detection or scheduled automation
- Options, futures, crypto, or non-equity AV endpoints unless explicitly requested
- Portfolio sizing or trade execution
