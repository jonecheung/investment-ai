"""Notion fetch for portfolio analysis (proposals + Layer 3 data source lookup)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

# Load guardrails notion_fetch without shadowing this module name.
_guardrails_path = (
    Path(__file__).resolve().parents[2]
    / "evaluate-portfolio-guardrails"
    / "scripts"
    / "notion_fetch.py"
)
_spec = importlib.util.spec_from_file_location("guardrails_notion_fetch", _guardrails_path)
assert _spec and _spec.loader
_gr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gr)

NotionError = _gr.NotionError
fetch_active_portfolio_policy = _gr.fetch_active_portfolio_policy
fetch_portfolio_snapshot = _gr.fetch_portfolio_snapshot
load_notion_token = _gr.load_notion_token
_paginate_query = _gr._paginate_query
_search_data_source = _gr._search_data_source
_plain_text = _gr._plain_text
_number = _gr._number
_select = _gr._select

PROPOSALS_TITLES = ("Trading Proposals",)


def _rich_text_currency(prop: dict[str, Any] | None) -> str | None:
    text = _plain_text(prop)
    return text.strip().upper() if text else None


def _parse_proposal_row(row: dict[str, Any]) -> dict[str, Any]:
    props = row.get("properties", {})
    return {
        "page_id": row["id"],
        "ticker": _plain_text(props.get("Ticker")),
        "company_name": _plain_text(props.get("Company Name")),
        "market": _select(props.get("Market")),
        "asset_class": (_select(props.get("Asset Class")) or "").lower() or None,
        "currency": _rich_text_currency(props.get("Currency")),
        "trade_type": (_select(props.get("Trade Type")) or "long").lower(),
        "conviction": (_select(props.get("Conviction")) or "medium").lower(),
        "risk_bucket": _select(props.get("Risk Bucket")),
        "status": _select(props.get("Status")),
        "pricing_status": _select(props.get("Pricing Status")),
        "intent": _select(props.get("Intent")),
        "entry_price": _number(props.get("Entry Price")),
        "stop_price": _number(props.get("Stop Price")),
        "target_price": _number(props.get("Target Price")),
        "last_price": _number(props.get("Last Price")),
        "reward_risk_ratio": _number(props.get("Reward Risk Ratio")),
    }


def fetch_all_trading_proposals(token: str) -> list[dict[str, Any]]:
    ds = _search_data_source(token, PROPOSALS_TITLES)
    rows = _paginate_query(token, ds["id"], {"page_size": 100})
    return [_parse_proposal_row(row) for row in rows]


def filter_proposals(
    proposals: list[dict[str, Any]],
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (eligible, rejections) per policy planner filters."""
    planner = policy.get("planner") or {}
    hard = policy.get("hard_limits") or {}
    regime = policy.get("regime_overrides") or {}

    req_status = planner.get("require_proposal_status")
    req_pricing = planner.get("require_pricing_status")
    req_intent = planner.get("require_intent")
    min_rr = hard.get("min_reward_risk_ratio")

    stale_status = (regime.get("stale_pricing") or {}).get(
        "exclude_proposal_when_pricing_status"
    )
    exclude_intent = (regime.get("watchlist_intent") or {}).get("exclude_intent")

    eligible: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    for prop in proposals:
        ticker = prop.get("ticker") or "?"
        reasons: list[str] = []

        if req_status and prop.get("status") != req_status:
            reasons.append(f"status={prop.get('status')!r}, required={req_status!r}")
        if req_pricing and prop.get("pricing_status") != req_pricing:
            reasons.append(
                f"pricing_status={prop.get('pricing_status')!r}, required={req_pricing!r}"
            )
        if req_intent and prop.get("intent") != req_intent:
            reasons.append(f"intent={prop.get('intent')!r}, required={req_intent!r}")
        if stale_status and prop.get("pricing_status") == stale_status:
            reasons.append(f"pricing_status={stale_status} excluded by policy")
        if exclude_intent and prop.get("intent") == exclude_intent:
            reasons.append(f"intent={exclude_intent} excluded by policy")
        if min_rr is not None:
            rr = prop.get("reward_risk_ratio")
            if rr is None or rr < float(min_rr):
                reasons.append(f"reward_risk_ratio={rr} below min {min_rr}")
        if prop.get("entry_price") is None or prop.get("stop_price") is None:
            reasons.append("missing entry_price or stop_price")

        if reasons:
            rejections.append({"ticker": ticker, "reasons": reasons})
        else:
            eligible.append(prop)

    return eligible, rejections


def fetch_trading_proposals(
    token: str,
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    all_rows = fetch_all_trading_proposals(token)
    eligible, rejections = filter_proposals(all_rows, policy)
    return eligible, rejections, len(all_rows)


LAYER3_TITLES = {
    "analysis": ("Portfolio Analysis",),
    "target_holdings": ("Target Portfolio Holdings",),
    "rebalance_actions": ("Rebalance Actions",),
}


def fetch_layer3_data_sources(token: str) -> dict[str, str]:
    """Return data_source_id map for Layer 3 databases."""
    result: dict[str, str] = {}
    for key, titles in LAYER3_TITLES.items():
        ds = _search_data_source(token, titles)
        result[key] = ds["id"]
    return result
