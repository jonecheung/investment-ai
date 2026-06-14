#!/usr/bin/env python3
"""Poll running Parallel research runs and sync summaries back to Notion."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


NOTION_VERSION = "2025-09-03"
NOTION_BASE_URL = "https://api.notion.com/v1"


def fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        fail(f"{name} is required")
    return value


def split_rich_text(text: str, chunk_size: int = 1900) -> list[dict[str, Any]]:
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    return [{"type": "text", "text": {"content": chunk}} for chunk in chunks]


class NotionClient:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{NOTION_BASE_URL}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=45) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            fail(f"Notion API {method} {path} failed: HTTP {exc.code}: {body}")
        except error.URLError as exc:
            fail(f"Notion API {method} {path} failed: {exc}")
        return json.loads(raw) if raw else {}

    def find_data_source(self, title: str) -> str:
        payload = {
            "query": title,
            "filter": {"property": "object", "value": "data_source"},
            "page_size": 10,
        }
        results = self.request("POST", "/search", payload).get("results", [])
        for item in results:
            item_title = "".join(part.get("plain_text", "") for part in item.get("title", []))
            if item_title == title:
                return item["id"]
        fail(f"Could not find Notion data source: {title}")

    def query_data_source(self, data_source_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        next_cursor: str | None = None
        while True:
            request_payload = dict(payload)
            if next_cursor:
                request_payload["start_cursor"] = next_cursor
            response = self.request("POST", f"/data_sources/{data_source_id}/query", request_payload)
            results.extend(response.get("results", []))
            if not response.get("has_more"):
                return results
            next_cursor = response.get("next_cursor")

    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/pages/{page_id}", {"properties": properties})


def title_text(page: dict[str, Any], prop: str) -> str:
    title = page.get("properties", {}).get(prop, {}).get("title", [])
    return "".join(part.get("plain_text", "") for part in title)


def relation_ids(page: dict[str, Any], prop: str) -> list[str]:
    rel = page.get("properties", {}).get(prop, {}).get("relation", [])
    return [item["id"] for item in rel if item.get("id")]


def select_property(value: str) -> dict[str, Any]:
    return {"select": {"name": value}}


def date_property(value: str) -> dict[str, Any]:
    return {"date": {"start": value}}


def rich_text_property(value: str) -> dict[str, Any]:
    return {"rich_text": split_rich_text(value)}


def kebab(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "parallel-research"


def query_running_runs(notion: NotionClient, runs_data_source_id: str, limit: int) -> list[dict[str, Any]]:
    return notion.query_data_source(
        runs_data_source_id,
        {
            "filter": {
                "or": [
                    {"property": "Status", "select": {"equals": "Running"}},
                    {"property": "Status", "select": {"equals": "Queued"}},
                ]
            },
            "sorts": [{"property": "Started At", "direction": "ascending"}],
            "page_size": limit,
        },
    )


def read_summary_from_md(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return ""

    # Prefer the standardized Executive Summary section. Stop at the next H2/H3.
    match = re.search(
        r"(?ims)^#{2,3}\s*1?\.\s*Executive Summary\s*$\n(?P<body>.*?)(?=^#{2,3}\s|\Z)",
        text,
    )
    if match:
        summary = match.group("body").strip()
        if summary:
            return summary[:1900]

    return text[:1900]


def find_first_string(data: Any, keys: set[str]) -> str:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, str) and value.strip():
                return value.strip()
        for value in data.values():
            found = find_first_string(value, keys)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_first_string(value, keys)
            if found:
                return found
    return ""


def read_summary_from_json(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return ""
    summary = find_first_string(data, {"executive_summary", "summary", "answer", "text", "markdown"})
    return summary[:1900] if summary else ""


def poll_parallel(run_id: str, output_base: Path, timeout: int) -> tuple[str, str, Path | None, Path | None]:
    command = [
        "parallel-cli",
        "research",
        "poll",
        run_id,
        "-o",
        str(output_base),
        "--timeout",
        str(timeout),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    combined = "\n".join(part for part in (stdout, stderr) if part)

    if completed.returncode != 0:
        if "still running" in combined.lower() or "timeout" in combined.lower():
            return "still_running", combined, None, None
        return "failed", combined or "Parallel poll failed", None, None

    md_path = output_base.with_suffix(".md")
    json_path = output_base.with_suffix(".json")
    return "completed", combined, md_path if md_path.exists() else None, json_path if json_path.exists() else None


def main() -> None:
    notion_token = env_required("NOTION_API_TOKEN")
    env_required("PARALLEL_API_KEY")

    timeout = int(os.environ.get("PARALLEL_POLL_TIMEOUT", "540"))
    limit = int(os.environ.get("PARALLEL_POLL_LIMIT", "5"))
    output_dir = Path(os.environ.get("PARALLEL_OUTPUT_DIR", "data/parallel/results"))
    output_dir.mkdir(parents=True, exist_ok=True)

    notion = NotionClient(notion_token)
    runs_data_source_id = os.environ.get("NOTION_RESEARCH_RUNS_DATA_SOURCE_ID") or notion.find_data_source("Research Runs")
    ideas_data_source_id = os.environ.get("NOTION_RESEARCH_IDEAS_DATA_SOURCE_ID") or notion.find_data_source("Research Ideas")
    _ = ideas_data_source_id  # Resolved to fail fast if the integration cannot see the data source.

    runs = query_running_runs(notion, runs_data_source_id, limit)
    if not runs:
        print(json.dumps({"status": "no_running_runs"}, indent=2))
        return

    results: list[dict[str, Any]] = []
    for run_page in runs:
        run_page_id = run_page["id"]
        run_id = title_text(run_page, "Run ID")
        if not run_id:
            continue

        output_base = output_dir / f"{kebab(run_id)}"
        status, detail, md_path, json_path = poll_parallel(run_id, output_base, timeout)
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        if status == "completed":
            summary = ""
            if md_path:
                summary = read_summary_from_md(md_path)
            if not summary and json_path:
                summary = read_summary_from_json(json_path)
            if not summary:
                summary = "Parallel research completed. See Result URL for full report."

            run_update: dict[str, Any] = {
                "Status": select_property("Completed"),
                "Completed At": date_property(now),
                "Executive Summary": rich_text_property(summary),
            }
            notion.update_page(run_page_id, run_update)

            for idea_page_id in relation_ids(run_page, "Idea"):
                notion.update_page(
                    idea_page_id,
                    {
                        "Status": select_property("Completed"),
                        "Last Run ID": rich_text_property(run_id),
                        "Last Run At": date_property(now),
                        "Executive Summary": rich_text_property(summary),
                    },
                )

        elif status == "failed":
            notion.update_page(
                run_page_id,
                {
                    "Status": select_property("Failed"),
                    "Completed At": date_property(now),
                    "Error Message": rich_text_property(detail[:1900]),
                },
            )

        results.append(
            {
                "run_id": run_id,
                "status": status,
                "md_path": str(md_path) if md_path else None,
                "json_path": str(json_path) if json_path else None,
            }
        )

    print(json.dumps({"status": "polled", "results": results}, indent=2))


if __name__ == "__main__":
    main()
