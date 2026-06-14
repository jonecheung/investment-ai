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

    def find_data_source_any(self, titles: list[str]) -> str:
        for title in titles:
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
        fail(f"Could not find Notion data source: {', '.join(titles)}")

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

    def create_page(self, data_source_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/pages", {"parent": {"data_source_id": data_source_id}, "properties": properties})


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


def title_property(value: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": value[:1900]}}]}


def relation_property(page_ids: list[str]) -> dict[str, Any]:
    return {"relation": [{"id": page_id} for page_id in page_ids if page_id]}


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


def query_completed_macro_runs_without_followup(
    notion: NotionClient,
    runs_data_source_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = notion.query_data_source(
        runs_data_source_id,
        {
            "filter": {
                "and": [
                    {"property": "Status", "select": {"equals": "Completed"}},
                    {"property": "Previous Interaction ID", "rich_text": {"is_empty": True}},
                ]
            },
            "sorts": [{"property": "Completed At", "direction": "descending"}],
            "page_size": limit,
        },
    )
    result: list[dict[str, Any]] = []
    for page in candidates:
        run_id = title_text(page, "Run ID")
        if run_id.startswith("trun_"):
            existing = notion.query_data_source(
                runs_data_source_id,
                {
                    "filter": {"property": "Previous Interaction ID", "rich_text": {"equals": run_id}},
                    "page_size": 1,
                },
            )
            if not existing:
                result.append(page)
    return result


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


def strip_schema_metadata(schema: Any) -> Any:
    if isinstance(schema, dict):
        return {
            key: strip_schema_metadata(value)
            for key, value in schema.items()
            if key not in {"$schema", "title"}
        }
    if isinstance(schema, list):
        return [strip_schema_metadata(value) for value in schema]
    return schema


def parallel_api_request(api_key: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"https://api.parallel.ai{path}",
        data=data,
        method=method,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=700) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Parallel API {method} {path} failed: HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Parallel API {method} {path} failed: {exc}") from exc
    return json.loads(raw) if raw else {}


def extract_task_payload(result: dict[str, Any]) -> dict[str, Any]:
    output = result.get("output") or {}
    content = output.get("content")
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(result.get("content"), dict):
        return result["content"]
    raise ValueError("Task result did not contain JSON output.content")


def validate_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    required_top = {"analysis_context", "thesis_snapshot", "ticker_opportunities", "output_quality"}
    missing = sorted(required_top - set(payload))
    if missing:
        raise ValueError(f"Follow-up payload missing top-level fields: {missing}")
    opportunities = payload.get("ticker_opportunities")
    if not isinstance(opportunities, list):
        raise ValueError("ticker_opportunities must be an array")

    markets = {"FX_MAJOR", "FX_CROSS", "FX_EM", "OTHER"}
    asset_classes = {"fx", "future", "option", "equity", "etf", "bond", "crypto", "other"}
    trade_types = {"long", "short", "other"}
    horizons = {"near_term", "medium_term", "long_term", "event_driven", "unspecified"}
    convictions = {"low", "medium", "high"}
    risk_buckets = {"fundamental", "event_driven", "macro_sensitive", "policy_sensitive", "supply_chain", "other"}

    valid: list[dict[str, Any]] = []
    for idx, opp in enumerate(opportunities):
        if not isinstance(opp, dict):
            raise ValueError(f"Opportunity {idx} must be an object")
        hypothesis = opp.get("trade_hypothesis") or {}
        checks = [
            ("ticker", opp.get("ticker"), None),
            ("company_name", opp.get("company_name"), None),
            ("asset_class", opp.get("asset_class"), asset_classes),
            ("market", opp.get("market"), markets),
            ("trade_type", hypothesis.get("trade_type"), trade_types),
            ("time_horizon", hypothesis.get("time_horizon"), horizons),
            ("conviction_level", hypothesis.get("conviction_level"), convictions),
            ("risk_bucket", hypothesis.get("risk_bucket"), risk_buckets),
        ]
        for field, value, allowed in checks:
            if value is None or value == "":
                raise ValueError(f"Opportunity {idx} missing {field}")
            if allowed is not None and value not in allowed:
                raise ValueError(f"Opportunity {idx} invalid {field}: {value}")
        valid.append(opp)
    return valid


def text_list(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    return "\n".join(f"- {value}" for value in values if isinstance(value, str) and value.strip())


def sectioned_watchpoints(opp: dict[str, Any]) -> str:
    hypothesis = opp.get("trade_hypothesis") or {}
    parts = [
        "Entry criteria:",
        text_list(hypothesis.get("entry_criteria")),
        "",
        "Monitoring signals:",
        text_list(opp.get("monitoring_signals")),
        "",
        "Open questions:",
        text_list(opp.get("open_questions")),
    ]
    return "\n".join(part for part in parts if part is not None).strip()


def invalidation_text(opp: dict[str, Any]) -> str:
    hypothesis = opp.get("trade_hypothesis") or {}
    exit_criteria = text_list(hypothesis.get("exit_criteria"))
    main = hypothesis.get("key_invalidation_event") or ""
    if exit_criteria:
        return f"{main}\n\nExit / downgrade criteria:\n{exit_criteria}".strip()
    return main


def proposal_title(opp: dict[str, Any]) -> str:
    hypothesis = opp.get("trade_hypothesis") or {}
    trade_type = hypothesis.get("trade_type", "other")
    return f"{opp.get('ticker', 'UNKNOWN')} {trade_type}"


def query_duplicate_proposal(notion: NotionClient, proposals_data_source_id: str, ticker: str, run_page_id: str) -> bool:
    matches = notion.query_data_source(
        proposals_data_source_id,
        {
            "filter": {
                "and": [
                    {"property": "Ticker", "rich_text": {"equals": ticker}},
                    {"property": "Run", "relation": {"contains": run_page_id}},
                ]
            },
            "page_size": 1,
        },
    )
    return bool(matches)


def create_research_run(
    notion: NotionClient,
    runs_data_source_id: str,
    run_id: str,
    idea_ids: list[str],
    previous_interaction_id: str,
    prompt: str,
    summary: str,
    status: str = "Completed",
) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    props: dict[str, Any] = {
        "Run ID": title_property(run_id),
        "Idea": relation_property(idea_ids),
        "Status": select_property(status),
        "Started At": date_property(now),
        "Completed At": date_property(now),
        "Previous Interaction ID": rich_text_property(previous_interaction_id),
        "Prompt Used": rich_text_property(prompt),
        "Executive Summary": rich_text_property(summary),
    }
    page = notion.create_page(runs_data_source_id, props)
    return page["id"]


def create_trading_proposals(
    notion: NotionClient,
    proposals_data_source_id: str,
    followup_run_page_id: str,
    idea_ids: list[str],
    opportunities: list[dict[str, Any]],
) -> dict[str, int]:
    created = 0
    skipped_duplicates = 0
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for opp in opportunities:
        ticker = str(opp["ticker"]).strip().upper()
        if query_duplicate_proposal(notion, proposals_data_source_id, ticker, followup_run_page_id):
            skipped_duplicates += 1
            continue
        hypothesis = opp.get("trade_hypothesis") or {}
        trade_type = hypothesis.get("trade_type", "other")
        rationale = hypothesis.get("rationale", "")
        other_trade_type = hypothesis.get("other_trade_type")
        if trade_type == "other" and other_trade_type:
            rationale = f"{rationale}\n\nOther trade type: {other_trade_type}".strip()
        conviction_note = hypothesis.get("conviction_note")
        if conviction_note:
            rationale = f"{rationale}\n\nConviction note: {conviction_note}".strip()

        properties: dict[str, Any] = {
            "Proposal": title_property(proposal_title({"ticker": ticker, "trade_hypothesis": hypothesis})),
            "Ticker": rich_text_property(ticker),
            "Instrument ID": rich_text_property(f"FX:{ticker}" if opp.get("asset_class") == "fx" else ticker),
            "Company Name": rich_text_property(str(opp.get("company_name") or ticker)),
            "Market": select_property(str(opp.get("market") or "OTHER")),
            "Asset Class": select_property(str(opp.get("asset_class") or "fx")),
            "Exchange": rich_text_property(str(opp.get("exchange") or "FX")),
            "Currency": rich_text_property(str(opp.get("currency") or ticker[-3:])),
            "Intent": select_property("Trade" if trade_type in {"long", "short"} else "Watchlist"),
            "Trade Type": select_property(trade_type),
            "Time Horizon": select_property(str(hypothesis.get("time_horizon") or "unspecified")),
            "Conviction": select_property(str(hypothesis.get("conviction_level") or "low")),
            "Risk Bucket": select_property(str(hypothesis.get("risk_bucket") or "macro_sensitive")),
            "Relationship To Research": rich_text_property(str(opp.get("relationship_to_research") or "")),
            "Rationale": rich_text_property(rationale),
            "Invalidation": rich_text_property(invalidation_text(opp)),
            "Assumptions": rich_text_property(text_list(opp.get("assumptions"))),
            "Watchpoints": rich_text_property(sectioned_watchpoints(opp)),
            "Status": select_property("Proposed"),
            "Pricing Status": select_property("Not Started"),
            "Proposed At": date_property(now),
            "Run": relation_property([followup_run_page_id]),
            "Idea": relation_property(idea_ids),
        }
        notion.create_page(proposals_data_source_id, properties)
        created += 1
    return {"created": created, "skipped_duplicates": skipped_duplicates}


def run_followup_and_import(
    notion: NotionClient,
    api_key: str,
    runs_data_source_id: str,
    proposals_data_source_id: str,
    source_run_page: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    source_run_id = title_text(source_run_page, "Run ID")
    idea_ids = relation_ids(source_run_page, "Idea")
    if not source_run_id or not idea_ids:
        return {"source_run_id": source_run_id, "status": "skipped", "reason": "missing source run id or idea relation"}

    # Skip if we already created a follow-up run for this source run.
    existing = notion.query_data_source(
        runs_data_source_id,
        {
            "filter": {"property": "Previous Interaction ID", "rich_text": {"equals": source_run_id}},
            "page_size": 1,
        },
    )
    if existing:
        return {"source_run_id": source_run_id, "status": "skipped", "reason": "follow-up already exists"}

    schema_path = Path("data/parallel/output-tradable-tickers.json")
    prompt_path = Path("data/parallel/prompt-followup-tradable-tickers.md")
    schema = strip_schema_metadata(json.loads(schema_path.read_text(encoding="utf-8")))
    base_prompt = prompt_path.read_text(encoding="utf-8")
    followup_prompt = (
        f"{base_prompt}\n\n"
        f"previous_interaction_id: {source_run_id}\n"
        "focus_markets: FX_MAJOR, FX_CROSS, FX_EM\n"
        "analysis_timeframe: mixed\n"
        "Return only schema-valid JSON with tradable FX pair opportunities."
    )

    request_payload = {
        "input": followup_prompt,
        "processor": os.environ.get("FOLLOWUP_PROCESSOR", "core"),
        "previous_interaction_id": source_run_id,
        "task_spec": {
            "output_schema": {
                "type": "json",
                "json_schema": schema,
            }
        },
    }
    create_response = parallel_api_request(api_key, "POST", "/v1/tasks/runs", request_payload)
    task_run_id = find_first_string(create_response, {"run_id", "id"})
    if not task_run_id:
        raise RuntimeError(f"Could not extract follow-up run ID: {json.dumps(create_response)[:500]}")

    output_base = output_dir / f"followup-{kebab(source_run_id)}"
    output_base.with_suffix(".create.json").write_text(json.dumps(create_response, indent=2), encoding="utf-8")

    result = parallel_api_request(api_key, "GET", f"/v1/tasks/runs/{task_run_id}/result?timeout=600")
    output_base.with_suffix(".result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    payload = extract_task_payload(result)
    output_base.with_suffix(".payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    opportunities = validate_payload(payload)

    thesis = payload.get("thesis_snapshot") or {}
    summary = str(thesis.get("core_thesis") or f"Generated {len(opportunities)} FX pair opportunities.")
    followup_run_page_id = create_research_run(
        notion,
        runs_data_source_id,
        task_run_id,
        idea_ids,
        source_run_id,
        followup_prompt,
        summary,
    )
    import_counts = create_trading_proposals(notion, proposals_data_source_id, followup_run_page_id, idea_ids, opportunities)
    return {
        "source_run_id": source_run_id,
        "followup_run_id": task_run_id,
        "status": "imported",
        "opportunities": len(opportunities),
        **import_counts,
    }


def main() -> None:
    notion_token = env_required("NOTION_API_TOKEN")
    parallel_api_key = env_required("PARALLEL_API_KEY")

    timeout = int(os.environ.get("PARALLEL_POLL_TIMEOUT", "540"))
    limit = int(os.environ.get("PARALLEL_POLL_LIMIT", "5"))
    auto_create_proposals = os.environ.get("AUTO_CREATE_TRADING_PROPOSALS", "1") == "1"
    output_dir = Path(os.environ.get("PARALLEL_OUTPUT_DIR", "data/parallel/results"))
    output_dir.mkdir(parents=True, exist_ok=True)

    notion = NotionClient(notion_token)
    runs_data_source_id = os.environ.get("NOTION_RESEARCH_RUNS_DATA_SOURCE_ID") or notion.find_data_source("Research Runs")
    ideas_data_source_id = os.environ.get("NOTION_RESEARCH_IDEAS_DATA_SOURCE_ID") or notion.find_data_source("Research Ideas")
    _ = ideas_data_source_id  # Resolved to fail fast if the integration cannot see the data source.

    runs = query_running_runs(notion, runs_data_source_id, limit)
    results: list[dict[str, Any]] = []
    if runs:
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

    proposal_results: list[dict[str, Any]] = []
    if auto_create_proposals:
        proposals_data_source_id = os.environ.get("NOTION_TRADING_PROPOSALS_DATA_SOURCE_ID") or notion.find_data_source_any(
            ["Trading Proposals", "Trade Proposals", "Proposals"]
        )
        completed_sources = query_completed_macro_runs_without_followup(notion, runs_data_source_id, limit)
        for source_run_page in completed_sources:
            try:
                proposal_results.append(
                    run_followup_and_import(
                        notion,
                        parallel_api_key,
                        runs_data_source_id,
                        proposals_data_source_id,
                        source_run_page,
                        output_dir,
                    )
                )
            except Exception as exc:  # Keep workflow diagnostics concise while avoiding partial hard failure.
                proposal_results.append(
                    {
                        "source_run_id": title_text(source_run_page, "Run ID"),
                        "status": "failed",
                        "error": str(exc)[:500],
                    }
                )

    print(json.dumps({"status": "polled", "results": results, "proposal_results": proposal_results}, indent=2))


if __name__ == "__main__":
    main()
