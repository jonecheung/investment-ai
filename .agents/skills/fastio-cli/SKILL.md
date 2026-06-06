---
name: fastio-cli
description: Perform basic Fast.io cloud file operations with the fastio CLI (list, create folders, upload, download, search, rename, delete). Use when uploading Trading Proposals session files, reading screener exports from Fast.io, or managing files in the configured Fast.io workspace.
disable-model-invocation: true
---

# Fast.io CLI — Basic File Operations

Use the [`fastio`](https://github.com/MediaFire/fastio_cli) CLI for cloud storage in this workspace. Prefer CLI over MCP for file tasks unless the user requests MCP.

## Environment

Copy `env.sample` → `.env`. Required Fast.io variables:

| Variable | Purpose |
| --- | --- |
| `FASTIO_API_KEY` | API authentication |
| `FASTIO_WORKSPACE_NAME` | Workspace display name (e.g. `ai-trading`) |

Load before commands:

```bash
set -a && [ -f .env ] && . ./.env && set +a
```

Never print raw `FASTIO_API_KEY` values.

## Prerequisites

1. CLI: `npm install -g @vividengine/fastio-cli`
2. `FASTIO_API_KEY` and `FASTIO_WORKSPACE_NAME` set in `.env`
3. Confirm CLI: `fastio --version`

### Auth precedence

1. `--token` → 2. `FASTIO_TOKEN` → 3. `FASTIO_API_KEY` → 4. stored profile

Agents: use `FASTIO_API_KEY` via env or `--token "$FASTIO_API_KEY"`.

### Verify auth (read-only)

```bash
set -a && [ -f .env ] && . ./.env && set +a
fastio org list --format json
fastio workspace list --format json
```

## Name-based resolution

Do not store workspace or folder node IDs in `.env`. Resolve at runtime from `FASTIO_WORKSPACE_NAME` and folder **names**:

1. **Workspace ID** — match `FASTIO_WORKSPACE_NAME` in `workspace list`
2. **Folder ID** — `files list` in parent, match child by `name` where `type == folder`

Session path under workspace:

```text
trading-proposals/sessions/<YYYY-MM-DD>-<run_id>-<script-slug>/
```

`trading-proposals` and `sessions` are fixed folder names in this workflow (not env vars). Create them if absent.

### Resolve workspace + sessions folder (Python)

```python
import json, os, subprocess

def fastio(*args):
    token = os.environ["FASTIO_API_KEY"]
    r = subprocess.run(
        ["fastio", *args, "--token", token, "--format", "json"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)

def folder_id_by_name(ws_id, parent_id, name):
    args = ["files", "list", "--workspace", ws_id]
    if parent_id:
        args += ["--folder", parent_id]
    items = fastio(*args).get("nodes", {}).get("items", [])
    match = next((n for n in items if n.get("type") == "folder" and n.get("name") == name), None)
    return match["id"] if match else None

ws_name = os.environ["FASTIO_WORKSPACE_NAME"]
workspaces = fastio("workspace", "list").get("workspaces", [])
ws_id = next(w["id"] for w in workspaces if w["name"] == ws_name)

tp_id = folder_id_by_name(ws_id, None, "trading-proposals")
sessions_id = folder_id_by_name(ws_id, tp_id, "sessions")
```

Create missing folders:

```bash
fastio files create-folder --workspace "$WS_ID" "trading-proposals" --format json
fastio files create-folder --workspace "$WS_ID" --parent "$TP_ID" "sessions" --format json
```

## Output format

- Scripts: `--format json`
- `files list` → `nodes.items[]`
- `upload text` → `{status, filename, new_file_id}`

## Basic operations

After resolving `WS_ID` and target `FOLDER_ID`:

### List

```bash
fastio files list --workspace "$WS_ID" --folder "$FOLDER_ID" --format json
```

### Create folder

```bash
fastio files create-folder --workspace "$WS_ID" \
  --parent "$SESSIONS_ID" \
  "2026-06-06-trun_abc123-supertrend-ema-atr-long" \
  --format json
```

### Upload file

```bash
fastio upload file --workspace "$WS_ID" \
  --folder "$SESSION_FOLDER_ID" \
  ./watchlist.txt --format json
```

### Upload text

```bash
fastio upload text --workspace "$WS_ID" \
  --folder "$SESSION_FOLDER_ID" \
  --name manifest.json \
  '{"session_id":"...","status":"pending_review"}' \
  --format json
```

### Download

```bash
fastio download file --workspace "$WS_ID" "<file_node_id>" \
  --output ./downloads/ --format json

fastio download folder --workspace "$WS_ID" "<folder_node_id>" \
  --output ./downloads/
```

### Info / search

```bash
fastio files info --workspace "$WS_ID" "<node_id>" --format json
fastio files search --workspace "$WS_ID" "screener.csv" --format json
```

### Rename / delete

Confirm with user first.

```bash
fastio files rename --workspace "$WS_ID" "<node_id>" "new-name.txt" --format json
fastio files delete --workspace "$WS_ID" "<node_id>" --format json
```

## Trading Proposals session workflow

1. Resolve workspace from `FASTIO_WORKSPACE_NAME`.
2. Resolve or create `trading-proposals/sessions/` by name.
3. Create session folder: `YYYY-MM-DD-<run_id>-<script-slug>`.
4. Upload `manifest.json` (`status: pending_review`), then `watchlist.txt`.
5. After Pine Screener export, upload `screener.csv`; update manifest.

### manifest.json minimum fields

```json
{
  "session_id": "2026-06-06-trun_abc123-supertrend-ema-atr-long",
  "run_id": "trun_abc123",
  "pine_script": "supertrend-ema-atr-long.pine",
  "trade_type": "long",
  "screener_timeframe": "1D",
  "filter": { "Setup Active": 1 },
  "created_at": "2026-06-06",
  "status": "pending_review",
  "files": { "watchlist": "watchlist.txt", "screener": "screener.csv" }
}
```

Status: `pending_review` → `approved` → `imported` → `archived`.

## Safety

- Read-only by default for discovery.
- Confirm before upload/rename/delete/purge.
- No secrets in skill files or committed data.

## Errors

| Symptom | Check |
| --- | --- |
| Workspace not found | `FASTIO_WORKSPACE_NAME` in `.env`; `workspace list` |
| Folder not found | List parent; create `trading-proposals` / `sessions` |
| Auth failure | `FASTIO_API_KEY` in `.env`; try `--token "$FASTIO_API_KEY"` |

## Related skills

- `export-tv-watchlist` — `watchlist.txt`
- `create-tv-pine-screener` — Pine Screener scripts
- `refresh-proposal-quotes` — Notion `Last Price` only

## Reference

- CLI: https://github.com/MediaFire/fastio_cli
