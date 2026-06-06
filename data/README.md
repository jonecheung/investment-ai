# Data Directory

Use this directory only for sanitized examples, schemas, derived summaries, or pointers to approved external data sources.

## Layout

Organize files by how they are used:

```
data/
├── README.md
├── notion/          # Notion database specs
├── parallel/        # Parallel API output contracts and paired prompts
├── prompts/         # Other reusable prompt assets
└── tradingview/     # TV watchlist exports + Pine Screener scripts for Layer 2 pricing
```

| Folder | Purpose | Examples |
| --- | --- | --- |
| `notion/` | Notion database structure only | `research.md`, `portfolio.md` |
| `parallel/` | Parallel Task API `output_schema` JSON and follow-up prompts used with it | `output-tradable-tickers.json`, `prompt-followup-tradable-tickers.md` |
| `prompts/` | Reusable prompts for other workflows | `research-idea-brief.md` |
| `tradingview/` | TradingView watchlist `.txt` exports (local/gitignored) and Pine Screener `.pine` scripts (tracked) | `2026-06-06-trun_abc123.txt`, `supertrend-ema-atr-long.pine` |

## File Naming

Use lowercase, kebab-case filenames **without** redundant type prefixes inside each folder:

- `notion/research.md` — not `schema-notion-research.md`
- `parallel/output-tradable-tickers.json` — Parallel output contract, not a Notion schema
- `prompts/research-idea-brief.md`

Guidelines:

- Keep filenames concise and descriptive
- Prefer `.md` for text documentation and prompt assets
- Do not include version numbers in filenames; use git history to track revisions

## Prompt Asset Convention

Use a consistent section order for reusable prompt files:

1. `# Prompt: <name>`
2. `## Purpose`
3. `## Inputs`
4. `## Task`
5. `## Analysis Requirements`
6. `## Constraints`
7. `## Output Format`
8. `## Quality Bar`
9. `## Missing Context Handling`
10. `## Examples` when useful

Keep prompt files focused on instructions. Store large Parallel output contracts in `parallel/` as `.json` and reference them from the paired prompt.

Do not store:

- Credentials, API keys, access tokens, or seed phrases
- Account numbers, SSNs, tax identifiers, or personal identity documents
- Full brokerage, bank, credit card, or retirement account statements
- Raw CSV, PDF, Excel, or database exports from financial institutions
- Tax forms or tax preparation files
- TradingView watchlist `.txt` exports under `data/tradingview/` (gitignored local run outputs from `export-tv-watchlist`; use Fast.io session storage as the durable copy)

If a workflow needs sensitive source data, keep it outside this workspace and explicitly approve the specific file or service access for that task.
