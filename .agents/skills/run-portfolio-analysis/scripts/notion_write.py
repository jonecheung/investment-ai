"""Write Layer 3 portfolio analysis results to Notion."""

from __future__ import annotations

import importlib.util
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NOTION_VERSION = "2025-09-03"
BASE_URL = "https://api.notion.com/v1"


def _load_guardrails_notion():
    path = (
        Path(__file__).resolve().parents[2]
        / "evaluate-portfolio-guardrails"
        / "scripts"
        / "notion_fetch.py"
    )
    spec = importlib.util.spec_from_file_location("guardrails_notion_fetch", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gr = _load_guardrails_notion()
NotionError = _gr.NotionError


def _request(token: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise NotionError(f"Notion {method} {path} failed ({exc.code}): {detail}") from exc


def _title_prop(text: str) -> dict:
    return {"title": [{"text": {"content": text[:2000]}}]}


def _rich_text(text: str | None) -> dict | None:
    if not text:
        return None
    return {"rich_text": [{"text": {"content": text[:2000]}}]}


def _select(name: str | None) -> dict | None:
    if not name:
        return None
    return {"select": {"name": name}}


def _number(value: float | int | None) -> dict | None:
    if value is None:
        return None
    return {"number": float(value)}


def _date_start(iso_date: str | None, with_time: bool = False) -> dict | None:
    if not iso_date:
        return None
    if with_time:
        return {"date": {"start": iso_date}}
    return {"date": {"start": iso_date[:10]}}


def _relation(page_id: str | None) -> dict | None:
    if not page_id:
        return None
    return {"relation": [{"id": page_id}]}


def _checkbox(value: bool) -> dict:
    return {"checkbox": bool(value)}


def write_analysis(
    token: str,
    data_sources: dict[str, str],
    output: dict[str, Any],
    snapshot_id: str,
    policy_id: str | None,
) -> dict[str, Any]:
    """Create Portfolio Analysis + child rows. Returns {analysis_page_id, ...}."""
    analysis = output["analysis"]
    title = f"Analysis {analysis.get('analysis_date', '')}"

    props: dict[str, Any] = {
        "Analysis": _title_prop(title),
        "Analysis Date": _date_start(analysis.get("analysis_date")),
        "Status": _select(analysis.get("status", "completed")),
        "Computed At": _date_start(analysis.get("computed_at"), with_time=True),
        "Portfolio Snapshot": _relation(snapshot_id),
        "Base Currency": _select(analysis.get("base_currency")),
        "Input NAV": _number(analysis.get("input_nav")),
        "Input Cash Pct": _number(analysis.get("input_cash_pct")),
        "Input Portfolio Heat Pct": _number(analysis.get("input_portfolio_heat_pct")),
        "Input Holdings Count": _number(analysis.get("input_holdings_count")),
        "Candidate Proposals Count": _number(analysis.get("candidate_proposals_count")),
        "Eligible Proposals Count": _number(analysis.get("eligible_proposals_count")),
        "Max Portfolio Heat Pct": _number(analysis.get("max_portfolio_heat_pct")),
        "Max Single Holding Pct": _number(analysis.get("max_single_holding_pct")),
        "Min Cash Pct": _number(analysis.get("min_cash_pct")),
        "Max Turnover Pct": _number(analysis.get("max_turnover_pct")),
        "Objective": _select(analysis.get("objective")),
        "Sizing Method": _select(analysis.get("sizing_method")),
        "Drawdown Triggered": _checkbox(analysis.get("drawdown_triggered", False)),
        "Target NAV": _number(analysis.get("target_nav")),
        "Target Cash Pct": _number(analysis.get("target_cash_pct")),
        "Target Portfolio Heat Pct": _number(analysis.get("target_portfolio_heat_pct")),
        "Target Holdings Count": _number(analysis.get("target_holdings_count")),
        "Turnover Pct": _number(analysis.get("turnover_pct")),
        "Rebalance Actions Count": _number(analysis.get("rebalance_actions_count")),
        "Executive Summary": _rich_text(output.get("executive_summary")),
        "Rejection Summary": _rich_text(output.get("rejection_summary")),
        "Infeasibility Reason": _rich_text(analysis.get("infeasibility_reason")),
        "Error Message": _rich_text(analysis.get("error_message")),
    }
    if policy_id:
        props["Portfolio Policy"] = _relation(policy_id)

    props = {k: v for k, v in props.items() if v is not None}

    page = _request(
        token,
        "POST",
        "/pages",
        {
            "parent": {"type": "data_source_id", "data_source_id": data_sources["analysis"]},
            "properties": props,
        },
    )
    analysis_id = page["id"]
    time.sleep(0.35)

    target_ds = data_sources["target_holdings"]
    for row in output.get("target_holdings", []):
        tph_props = {
            "Holding": _title_prop(row.get("title") or row.get("ticker", "?")),
            "Portfolio Analysis": _relation(analysis_id),
            "Ticker": _rich_text(row.get("ticker")),
            "Company Name": _rich_text(row.get("company_name")),
            "Holding Type": _select(row.get("holding_type")),
            "Market": _select(row.get("market")),
            "Asset Class": _select(row.get("asset_class")),
            "Currency": _select(row.get("currency")),
            "Trade Type": _select(row.get("trade_type")),
            "Target Weight Pct": _number(row.get("target_weight_pct")),
            "Target Market Value": _number(row.get("target_market_value")),
            "Target Quantity": _number(row.get("target_quantity")),
            "Entry Price": _number(row.get("entry_price")),
            "Stop Price": _number(row.get("stop_price")),
            "Target Price": _number(row.get("target_price")),
            "Risk at Stop": _number(row.get("risk_at_stop")),
            "Risk at Stop Pct": _number(row.get("risk_at_stop_pct")),
            "Line Source": _select(row.get("line_source")),
            "Action Hint": _select(row.get("action_hint")),
            "Notes": _rich_text(row.get("notes")),
        }
        if row.get("source_proposal_id"):
            tph_props["Source Proposal"] = _relation(row["source_proposal_id"])
        if row.get("source_holding_id"):
            tph_props["Source Holding"] = _relation(row["source_holding_id"])
        tph_props = {k: v for k, v in tph_props.items() if v is not None}
        _request(
            token,
            "POST",
            "/pages",
            {"parent": {"type": "data_source_id", "data_source_id": target_ds}, "properties": tph_props},
        )
        time.sleep(0.35)

    rebalance_ds = data_sources["rebalance_actions"]
    for row in output.get("rebalance_actions", []):
        ra_props = {
            "Rebalance Action": _title_prop(row.get("title") or "?"),
            "Portfolio Analysis": _relation(analysis_id),
            "Ticker": _rich_text(row.get("ticker")),
            "Market": _select(row.get("market")),
            "Currency": _select(row.get("currency")),
            "Action Type": _select(row.get("action_type")),
            "Priority": _select(row.get("priority")),
            "Sequence": _number(row.get("sequence")),
            "Current Market Value": _number(row.get("current_market_value")),
            "Target Market Value": _number(row.get("target_market_value")),
            "Delta Market Value": _number(row.get("delta_market_value")),
            "Current Quantity": _number(row.get("current_quantity")),
            "Target Quantity": _number(row.get("target_quantity")),
            "Delta Quantity": _number(row.get("delta_quantity")),
            "Reference Price": _number(row.get("reference_price")),
            "Entry Price": _number(row.get("entry_price")),
            "Stop Price": _number(row.get("stop_price")),
            "Rationale": _rich_text(row.get("rationale")),
            "Constraint Notes": _rich_text(row.get("constraint_notes")),
        }
        if row.get("source_proposal_id"):
            ra_props["Source Proposal"] = _relation(row["source_proposal_id"])
        if row.get("related_holding_id"):
            ra_props["Related Holding"] = _relation(row["related_holding_id"])
        ra_props = {k: v for k, v in ra_props.items() if v is not None}
        _request(
            token,
            "POST",
            "/pages",
            {"parent": {"type": "data_source_id", "data_source_id": rebalance_ds}, "properties": ra_props},
        )
        time.sleep(0.35)

    return {
        "analysis_page_id": analysis_id,
        "analysis_url": page.get("url"),
        "target_holdings_written": len(output.get("target_holdings", [])),
        "rebalance_actions_written": len(output.get("rebalance_actions", [])),
    }
