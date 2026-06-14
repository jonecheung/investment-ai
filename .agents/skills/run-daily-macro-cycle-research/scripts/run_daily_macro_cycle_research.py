#!/usr/bin/env python3
"""Start the scheduled macro-cycle Parallel research run and log it in Notion."""

from __future__ import annotations

import json
import os
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

    def create_page(self, data_source_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/pages", {"parent": {"data_source_id": data_source_id}, "properties": properties})

    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/pages/{page_id}", {"properties": properties})


def extract_json(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            fail(f"Parallel CLI did not return JSON. Output was: {text[:500]}")
        return json.loads(text[start : end + 1])


def find_first_key(data: Any, keys: set[str]) -> Any:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and value:
                return value
        for value in data.values():
            found = find_first_key(value, keys)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_first_key(value, keys)
            if found:
                return found
    return None


def run_parallel(prompt: str, processor: str) -> dict[str, Any]:
    command = [
        "parallel-cli",
        "research",
        "run",
        prompt,
        "--processor",
        processor,
        "--text",
        "--no-wait",
        "--json",
    ]
    try:
        completed = subprocess.run(command, check=True, text=True, capture_output=True)
    except FileNotFoundError:
        fail("parallel-cli is not installed or not on PATH")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        stdout = exc.stdout.strip()
        detail = stderr or stdout or "no output"
        fail(f"Parallel research kickoff failed: {detail}")
    return extract_json(completed.stdout)


def title_property(value: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": value}}]}


def rich_text_property(value: str) -> dict[str, Any]:
    return {"rich_text": split_rich_text(value)}


def select_property(value: str) -> dict[str, Any]:
    return {"select": {"name": value}}


def multi_select_property(values: list[str]) -> dict[str, Any]:
    return {"multi_select": [{"name": value} for value in values]}


def date_property(value: str) -> dict[str, Any]:
    return {"date": {"start": value}}


def ensure_macro_idea(
    notion: NotionClient,
    ideas_data_source_id: str,
    title: str,
    prompt: str,
) -> str:
    matches = notion.query_data_source(
        ideas_data_source_id,
        {
            "filter": {
                "property": "Original Idea",
                "title": {"equals": title},
            },
            "page_size": 5,
        },
    )

    properties = {
        "Original Idea": title_property(title),
        "Research Input": rich_text_property(prompt),
        "Status": select_property("Expanded"),
        "Active": {"checkbox": True},
        "Run Frequency": select_property("Daily"),
        "Market Tags": multi_select_property(["Global Macro", "FX_MAJOR", "FX_CROSS", "FX_EM"]),
        "Asset Type Tags": multi_select_property(["FX"]),
        "Strategy Tags": multi_select_property(["Macro", "Flow", "Event-driven"]),
    }

    if matches:
        page_id = matches[0]["id"]
        notion.update_page(page_id, properties)
        return page_id

    page = notion.create_page(ideas_data_source_id, properties)
    return page["id"]


def main() -> None:
    notion_token = env_required("NOTION_API_TOKEN")

    processor = os.environ.get("PARALLEL_PROCESSOR", "base")
    title = os.environ.get("MACRO_RESEARCH_IDEA_TITLE", "Daily Macro Cycle Regime Scan Before EU Session")
    prompt_path = Path(os.environ.get("MACRO_PROMPT_PATH", "data/prompts/macro-cycle-regime-scan.md"))
    ensure_idea_only = os.environ.get("MACRO_ENSURE_IDEA_ONLY") == "1"

    if not prompt_path.exists():
        fail(f"Prompt template not found: {prompt_path}")
    prompt = prompt_path.read_text(encoding="utf-8")

    notion = NotionClient(notion_token)
    ideas_data_source_id = os.environ.get("NOTION_RESEARCH_IDEAS_DATA_SOURCE_ID") or notion.find_data_source("Research Ideas")
    runs_data_source_id = os.environ.get("NOTION_RESEARCH_RUNS_DATA_SOURCE_ID") or notion.find_data_source("Research Runs")

    idea_page_id = ensure_macro_idea(notion, ideas_data_source_id, title, prompt)
    if ensure_idea_only:
        print(
            json.dumps(
                {
                    "status": "idea_ensured",
                    "idea_page_id": idea_page_id,
                    "title": title,
                },
                indent=2,
            )
        )
        return

    env_required("PARALLEL_API_KEY")

    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    parallel_response = run_parallel(prompt, processor)

    run_id = find_first_key(parallel_response, {"run_id", "id"})
    if not run_id:
        fail(f"Could not extract Parallel run_id from response: {json.dumps(parallel_response)[:500]}")

    interaction_id = find_first_key(parallel_response, {"interaction_id"})
    result_url = find_first_key(parallel_response, {"monitoring_url", "url", "result_url"})

    run_properties: dict[str, Any] = {
        "Run ID": title_property(str(run_id)),
        "Idea": {"relation": [{"id": idea_page_id}]},
        "Status": select_property("Running"),
        "Processor": select_property(processor),
        "Started At": date_property(started_at),
        "Prompt Used": rich_text_property(prompt),
    }
    if result_url:
        run_properties["Result URL"] = {"url": str(result_url)}
    if interaction_id:
        # This field is normally for previous interaction context. We do not store
        # first-pass interaction IDs here to preserve the schema convention.
        pass

    notion.create_page(runs_data_source_id, run_properties)

    notion.update_page(
        idea_page_id,
        {
            "Status": select_property("Running"),
            "Last Run ID": rich_text_property(str(run_id)),
            "Last Run At": date_property(started_at),
        },
    )

    print(
        json.dumps(
            {
                "status": "started",
                "idea_page_id": idea_page_id,
                "run_id": run_id,
                "interaction_id": interaction_id,
                "result_url": result_url,
                "processor": processor,
                "started_at": started_at,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
