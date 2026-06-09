"""Read-only Notion fetch for Portfolio Snapshot and Portfolio Holdings."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

NOTION_VERSION = "2025-09-03"
BASE_URL = "https://api.notion.com/v1"

SNAPSHOT_TITLES = ("Portfolio Snapshot", "Portfolio Snapshots")
HOLDINGS_TITLES = ("Portfolio Holdings", "Holdings")
POLICY_TITLES = ("Portfolio Policy",)

SNAPSHOT_REQUIRED = (
    "Snapshot",
    "Snapshot Date",
    "Status",
    "Base Currency",
    "Portfolio NAV",
)

HOLDINGS_REQUIRED = (
    "Holding",
    "Portfolio Snapshot",
    "Holding Type",
    "Ticker",
    "Market",
    "Asset Class",
    "Trade Type",
    "Quantity",
    "Market Value",
)

POLICY_REQUIRED = (
    "Policy",
    "Status",
    "Active",
    "Base Currency",
    "Max Single Holding Pct",
    "Max Holdings Count",
    "Min Cash Pct",
    "Max Cash Pct",
    "Max Portfolio Heat Pct",
)


class NotionError(Exception):
    pass


def load_notion_token() -> str:
    token = os.environ.get("NOTION_API_TOKEN")
    if token:
        return token.strip()

    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        repo_env = Path(__file__).resolve().parents[4] / ".env"
        if repo_env.is_file():
            env_path = repo_env

    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("NOTION_API_TOKEN="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    os.environ["NOTION_API_TOKEN"] = value
                    return value

    raise NotionError(
        "NOTION_API_TOKEN is missing. Set it in the environment or .env file."
    )


def _request(
    method: str,
    path: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
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
        raise NotionError(f"Notion API {method} {path} failed ({exc.code}): {detail}") from exc


def _paginate_query(
    token: str,
    data_source_id: str,
    body: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    start_cursor: str | None = None
    while True:
        payload = dict(body)
        if start_cursor:
            payload["start_cursor"] = start_cursor
        data = _request(
            "POST",
            f"/data_sources/{data_source_id}/query",
            token,
            payload,
        )
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
        if not start_cursor:
            break
        time.sleep(0.35)
    return results


def _search_data_source(token: str, titles: tuple[str, ...]) -> dict[str, Any]:
    for title in titles:
        data = _request(
            "POST",
            "/search",
            token,
            {
                "query": title,
                "filter": {"property": "object", "value": "data_source"},
                "page_size": 20,
            },
        )
        for item in data.get("results", []):
            if item.get("object") != "data_source":
                continue
            item_title = item.get("title", [])
            plain = "".join(part.get("plain_text", "") for part in item_title)
            if plain == title:
                return item
        time.sleep(0.35)
    raise NotionError(
        f"Could not find Notion data source. Tried: {', '.join(titles)}"
    )


def _validate_schema(data_source: dict[str, Any], required: tuple[str, ...]) -> None:
    props = data_source.get("properties", {})
    missing = [name for name in required if name not in props]
    if missing:
        title = "".join(part.get("plain_text", "") for part in data_source.get("title", []))
        raise NotionError(
            f"Data source '{title}' is missing required properties: {', '.join(missing)}"
        )


def _plain_text(prop: dict[str, Any] | None) -> str | None:
    if not prop:
        return None
    if prop.get("type") == "title":
        parts = prop.get("title") or []
    elif prop.get("type") == "rich_text":
        parts = prop.get("rich_text") or []
    else:
        return None
    text = "".join(part.get("plain_text", "") for part in parts).strip()
    return text or None


def _number(prop: dict[str, Any] | None) -> float | None:
    if not prop or prop.get("type") != "number":
        return None
    value = prop.get("number")
    return float(value) if value is not None else None


def _select(prop: dict[str, Any] | None) -> str | None:
    if not prop or prop.get("type") != "select":
        return None
    selected = prop.get("select")
    if not selected:
        return None
    return selected.get("name")


def _date_start(prop: dict[str, Any] | None) -> str | None:
    if not prop or prop.get("type") != "date":
        return None
    date_obj = prop.get("date")
    if not date_obj:
        return None
    return date_obj.get("start")


def _relation_ids(prop: dict[str, Any] | None) -> list[str]:
    if not prop or prop.get("type") != "relation":
        return []
    return [item["id"] for item in prop.get("relation", []) if item.get("id")]


def _checkbox(prop: dict[str, Any] | None) -> bool:
    if not prop or prop.get("type") != "checkbox":
        return False
    return bool(prop.get("checkbox"))


def fetch_portfolio_snapshot(
    token: str,
    snapshot_date: str | None = None,
) -> dict[str, Any]:
    snapshot_ds = _search_data_source(token, SNAPSHOT_TITLES)
    snapshot_id = snapshot_ds["id"]
    _validate_schema(snapshot_ds, SNAPSHOT_REQUIRED)

    rows = _paginate_query(
        token,
        snapshot_id,
        {
            "filter": {
                "property": "Status",
                "select": {"equals": "approved"},
            },
            "sorts": [
                {"property": "Snapshot Date", "direction": "descending"},
            ],
        },
    )
    if not rows:
        raise NotionError("No approved Portfolio Snapshot found in Notion.")

    if snapshot_date:
        matched = None
        for row in rows:
            props = row.get("properties", {})
            row_date = _date_start(props.get("Snapshot Date"))
            if row_date and row_date[:10] == snapshot_date:
                matched = row
                break
        if not matched:
            raise NotionError(
                f"No approved Portfolio Snapshot found for date {snapshot_date}."
            )
        row = matched
    else:
        row = rows[0]

    props = row.get("properties", {})
    nav = _number(props.get("Portfolio NAV"))
    snapshot = {
        "id": row["id"],
        "title": _plain_text(props.get("Snapshot")) or "",
        "snapshot_date": _date_start(props.get("Snapshot Date")),
        "base_currency": _select(props.get("Base Currency")),
        "nav": nav,
        "status": _select(props.get("Status")),
    }

    holdings_ds = _search_data_source(token, HOLDINGS_TITLES)
    holdings_id = holdings_ds["id"]
    _validate_schema(holdings_ds, HOLDINGS_REQUIRED)

    holding_rows = _paginate_query(
        token,
        holdings_id,
        {
            "filter": {
                "property": "Portfolio Snapshot",
                "relation": {"contains": snapshot["id"]},
            },
        },
    )

    holdings: list[dict[str, Any]] = []
    for hrow in holding_rows:
        hprops = hrow.get("properties", {})
        holding_type = (_select(hprops.get("Holding Type")) or "").lower()
        ticker = _plain_text(hprops.get("Ticker")) or _plain_text(hprops.get("Holding"))
        market_value = _number(hprops.get("Market Value"))
        holdings.append(
            {
                "page_id": hrow["id"],
                "ticker": ticker,
                "holding_type": holding_type or None,
                "market": _select(hprops.get("Market")),
                "currency": _select(hprops.get("Currency")),
                "asset_class": (_select(hprops.get("Asset Class")) or "").lower() or None,
                "trade_type": (_select(hprops.get("Trade Type")) or "").lower() or None,
                "quantity": _number(hprops.get("Quantity")),
                "market_value": market_value,
                "entry_price": _number(hprops.get("Entry Price")),
                "stop_price": _number(hprops.get("Stop Price")),
            }
        )

    if snapshot["nav"] is None:
        values = [h["market_value"] for h in holdings if h["market_value"] is not None]
        if values:
            snapshot["nav"] = sum(values)

    if snapshot["nav"] is None or snapshot["nav"] <= 0:
        raise NotionError("Portfolio NAV is missing or zero; cannot compute metrics.")

    return {"snapshot": snapshot, "holdings": holdings}


def fetch_active_portfolio_policy(token: str) -> dict[str, Any]:
    policy_ds = _search_data_source(token, POLICY_TITLES)
    policy_ds_id = policy_ds["id"]
    _validate_schema(policy_ds, POLICY_REQUIRED)

    rows = _paginate_query(
        token,
        policy_ds_id,
        {
            "filter": {
                "property": "Active",
                "checkbox": {"equals": True},
            },
            "sorts": [
                {"property": "Effective Date", "direction": "descending"},
            ],
        },
    )
    if not rows:
        rows = _paginate_query(
            token,
            policy_ds_id,
            {
                "filter": {
                    "property": "Status",
                    "select": {"equals": "active"},
                },
                "sorts": [
                    {"property": "Effective Date", "direction": "descending"},
                ],
            },
        )
    if not rows:
        raise NotionError(
            "No active Portfolio Policy found in Notion "
            "(Active=true or Status=active)."
        )

    row = rows[0]
    props = row.get("properties", {})
    return {
        "id": row["id"],
        "title": _plain_text(props.get("Policy")) or "",
        "status": _select(props.get("Status")),
        "active": _checkbox(props.get("Active")),
        "effective_date": _date_start(props.get("Effective Date")),
        "base_currency": _select(props.get("Base Currency")),
        "schema_version": _number(props.get("Schema Version")),
        "hard_limits": {
            "max_single_holding_pct": _number(props.get("Max Single Holding Pct")),
            "max_holdings_count": _number(props.get("Max Holdings Count")),
            "min_cash_pct": _number(props.get("Min Cash Pct")),
            "max_cash_pct": _number(props.get("Max Cash Pct")),
            "max_risk_per_proposal_pct": _number(
                props.get("Max Risk Per Proposal Pct")
            ),
            "max_portfolio_heat_pct": _number(props.get("Max Portfolio Heat Pct")),
            "min_reward_risk_ratio": _number(props.get("Min Reward Risk Ratio")),
            "max_turnover_pct": _number(props.get("Max Turnover Pct")),
        },
        "market_limits": {
            "FX_MAJOR": {
                "max_exposure_pct": _number(props.get("Max FX Major Exposure Pct"))
            },
            "FX_CROSS": {
                "max_exposure_pct": _number(props.get("Max FX Cross Exposure Pct"))
            },
            "FX_EM": {
                "max_exposure_pct": _number(props.get("Max FX EM Exposure Pct"))
            },
            "OTHER": {
                "max_exposure_pct": _number(props.get("Max Other Exposure Pct"))
            },
        },
        "asset_class_limits": {
            "fx": {"max_exposure_pct": _number(props.get("Max FX Exposure Pct"))},
            "equity": {
                "max_exposure_pct": _number(props.get("Max Equity Exposure Pct"))
            },
            "etf": {"max_exposure_pct": _number(props.get("Max ETF Exposure Pct"))},
            "crypto": {
                "max_exposure_pct": _number(props.get("Max Crypto Exposure Pct"))
            },
        },
        "soft_preferences": {
            "objective": _select(props.get("Objective")),
            "conviction_weights": {
                "high": _number(props.get("Conviction Weight High")),
                "medium": _number(props.get("Conviction Weight Medium")),
                "low": _number(props.get("Conviction Weight Low")),
            },
            "existing_position_bias": _number(props.get("Existing Position Bias")),
            "max_positions_per_risk_bucket": _number(
                props.get("Max Positions Per Risk Bucket")
            ),
            "max_positions_per_market_risk_bucket": _number(
                props.get("Max Positions Per Market Risk Bucket")
            ),
        },
        "regime_overrides": {
            "drawdown_from_peak": {
                "trigger_pct": _number(props.get("Drawdown Trigger Pct")),
                "max_portfolio_heat_multiplier": _number(
                    props.get("Drawdown Heat Multiplier")
                ),
                "max_risk_per_proposal_multiplier": _number(
                    props.get("Drawdown Risk Multiplier")
                ),
                "min_cash_pct_floor": _number(
                    props.get("Drawdown Min Cash Floor Pct")
                ),
            },
            "stale_pricing": {
                "exclude_proposal_when_pricing_status": "Stale"
                if _checkbox(props.get("Exclude Stale Pricing"))
                else None,
            },
            "watchlist_intent": {
                "exclude_intent": "Watchlist"
                if _checkbox(props.get("Exclude Watchlist Intent"))
                else None,
            },
        },
        "planner": {
            "require_proposal_status": _select(props.get("Require Proposal Status")),
            "require_pricing_status": _select(props.get("Require Pricing Status")),
            "require_intent": _select(props.get("Require Intent")),
            "sizing_method": _select(props.get("Sizing Method")),
            "emit_rejection_reasons": True,
        },
    }
