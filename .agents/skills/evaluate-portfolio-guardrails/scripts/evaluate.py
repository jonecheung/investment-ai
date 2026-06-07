#!/usr/bin/env python3
"""Compute portfolio guardrail metrics from Notion and check against guardrails.yaml."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fx_rates import FxError, build_fx_rates, resolve_holding_currency
from guardrails import evaluate_guardrails, load_policy, policy_from_notion
from metrics import compute_metrics
from notion_fetch import NotionError, fetch_active_portfolio_policy, fetch_portfolio_snapshot, load_notion_token


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def build_output(
    portfolio: dict,
    metrics_result: dict,
    guardrail_check: dict | None,
) -> dict:
    snapshot = portfolio["snapshot"]
    output = {
        "schema_version": 1,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": {
            "id": snapshot["id"],
            "date": snapshot.get("snapshot_date"),
            "base_currency": snapshot.get("base_currency"),
            "nav": snapshot.get("nav"),
            "title": snapshot.get("title"),
        },
        "metrics": metrics_result["metrics"],
        "positions": metrics_result["positions"],
    }
    if metrics_result.get("fx_rates"):
        output["fx_rates"] = metrics_result["fx_rates"]
    if metrics_result.get("warnings"):
        output["warnings"] = metrics_result["warnings"]
    if guardrail_check is not None:
        output["guardrail_check"] = guardrail_check
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate portfolio guardrails from Notion Approved Portfolio Snapshot.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="Optional YAML policy file override (default: active Portfolio Policy in Notion)",
    )
    parser.add_argument(
        "--snapshot-date",
        help="Approved snapshot date YYYY-MM-DD (default: latest approved)",
    )
    parser.add_argument(
        "--drawdown-pct",
        type=float,
        help="Optional peak-to-current NAV drawdown percent for regime overrides",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write JSON output to file instead of stdout",
    )
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Skip guardrail_check section",
    )
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="Exit 1 when any hard limit check fails",
    )
    args = parser.parse_args()

    try:
        token = load_notion_token()
        portfolio = fetch_portfolio_snapshot(token, snapshot_date=args.snapshot_date)
        snapshot = portfolio["snapshot"]
        base_currency = snapshot.get("base_currency") or "HKD"
        currencies = {
            resolve_holding_currency(holding)
            for holding in portfolio["holdings"]
            if holding.get("holding_type") != "cash"
            and (holding.get("ticker") or "").upper() != "CASH"
        }
        fx = build_fx_rates({c for c in currencies if c}, base_currency)
        metrics_result = compute_metrics(snapshot, portfolio["holdings"], fx=fx)

        guardrail_check = None
        if not args.metrics_only:
            if args.policy is not None:
                policy = load_policy(args.policy)
                policy_source = {"type": "yaml", "path": str(args.policy.resolve())}
            else:
                notion_policy = fetch_active_portfolio_policy(token)
                policy = policy_from_notion(notion_policy)
                policy_source = {
                    "type": "notion",
                    "id": notion_policy["id"],
                    "title": notion_policy.get("title"),
                    "effective_date": notion_policy.get("effective_date"),
                }
            guardrail_check = evaluate_guardrails(
                policy,
                metrics_result["metrics"],
                policy_source=policy_source,
                drawdown_pct=args.drawdown_pct,
            )

        output = build_output(portfolio, metrics_result, guardrail_check)
        payload = json.dumps(output, indent=2, ensure_ascii=False) + "\n"

        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)

        if (
            args.fail_on_violation
            and guardrail_check is not None
            and not guardrail_check["summary"]["pass"]
        ):
            return 1
        return 0

    except (NotionError, FxError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
