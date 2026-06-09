#!/usr/bin/env python3
"""Run portfolio analysis: repair + greedy plan from Notion inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fx_rates import FxError, build_fx_rates, resolve_holding_currency
from guardrails import evaluate_guardrails, load_policy, policy_from_notion
from metrics import compute_metrics

from notion_fetch import (
    NotionError,
    fetch_active_portfolio_policy,
    fetch_layer3_data_sources,
    fetch_portfolio_snapshot,
    fetch_trading_proposals,
    load_notion_token,
)
from notion_write import write_analysis
from output_schema import build_output
from planner import run_planner
from rebalance import build_rebalance_actions
from universe import build_universe, get_cash_holding


def _load_policy(token: str, policy_path: Path | None) -> tuple[dict, dict]:
    if policy_path is not None:
        policy = load_policy(policy_path)
        source = {"type": "yaml", "path": str(policy_path.resolve())}
        return policy, source
    record = fetch_active_portfolio_policy(token)
    policy = policy_from_notion(record)
    source = {
        "type": "notion",
        "id": record["id"],
        "title": record.get("title"),
        "effective_date": record.get("effective_date"),
    }
    return policy, source


def main() -> int:
    parser = argparse.ArgumentParser(description="Run portfolio analysis (Layer 3 planner).")
    parser.add_argument("--snapshot-date", help="Approved snapshot YYYY-MM-DD")
    parser.add_argument("--policy", type=Path, help="YAML policy override")
    parser.add_argument("--drawdown-pct", type=float, help="Drawdown %% for regime overrides")
    parser.add_argument("--out", type=Path, help="Write JSON to file")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write Portfolio Analysis + child rows to Notion (default: JSON dry-run only)",
    )
    parser.add_argument(
        "--fail-on-infeasible",
        action="store_true",
        help="Exit 1 when plan status is infeasible",
    )
    args = parser.parse_args()

    try:
        token = load_notion_token()
        portfolio = fetch_portfolio_snapshot(token, snapshot_date=args.snapshot_date)
        snapshot = portfolio["snapshot"]
        holdings = portfolio["holdings"]
        nav = float(snapshot["nav"])

        policy, policy_source = _load_policy(token, args.policy)
        eligible, filter_rejections, candidate_count = fetch_trading_proposals(token, policy)

        base_currency = snapshot.get("base_currency") or policy.get("base_currency") or "USD"
        currencies = {
            resolve_holding_currency(h)
            for h in holdings
            if (h.get("ticker") or "").upper() != "CASH"
        }
        for prop in eligible:
            c = prop.get("currency")
            if c:
                currencies.add(c.upper())
        fx = build_fx_rates({c for c in currencies if c}, base_currency)

        input_metrics_result = compute_metrics(snapshot, holdings, fx=fx)
        input_metrics = input_metrics_result["metrics"]

        guardrail_input = evaluate_guardrails(
            policy,
            input_metrics,
            policy_source=policy_source,
            drawdown_pct=args.drawdown_pct,
        )

        soft = policy.get("soft_preferences") or {}
        conviction_weights = soft.get("conviction_weights") or {"high": 3, "medium": 2, "low": 1}

        universe = build_universe(
            holdings,
            eligible,
            input_metrics_result["positions"],
            conviction_weights,
        )

        cash_h = get_cash_holding(holdings)
        initial_cash = float(cash_h.get("market_value") or 0.0) if cash_h else 0.0

        plan = run_planner(
            universe,
            nav,
            initial_cash,
            policy,
            input_metrics,
            guardrail_input,
            compute_metrics,
            fx,
        )

        rebalance_actions = build_rebalance_actions(
            plan.lines,
            initial_cash,
            plan.target_cash_mv,
            nav,
        )

        target_snapshot = {"nav": nav, "base_currency": base_currency}
        from planner import lines_to_holdings

        target_holdings = lines_to_holdings(
            [line for line in plan.lines if line.included],
            plan.target_cash_mv,
        )
        target_metrics_result = compute_metrics(target_snapshot, target_holdings, fx=fx)
        target_metrics = target_metrics_result["metrics"]

        guardrail_target = evaluate_guardrails(
            policy,
            target_metrics,
            policy_source=policy_source,
            drawdown_pct=args.drawdown_pct,
        )

        output = build_output(
            snapshot=snapshot,
            policy_source=policy_source,
            policy=policy,
            input_metrics=input_metrics,
            target_metrics=target_metrics,
            guardrail_check_input=guardrail_input,
            guardrail_check_target=guardrail_target,
            plan=plan,
            filter_rejections=filter_rejections,
            candidate_proposals_count=candidate_count,
            eligible_proposals_count=len(eligible),
            rebalance_actions=rebalance_actions,
            fx_rates=target_metrics_result.get("fx_rates"),
            target_positions=target_metrics_result.get("positions"),
        )

        payload = json.dumps(output, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)

        if args.write:
            if plan.status == "infeasible":
                raise NotionError(
                    "Refusing --write: plan status is infeasible. Review JSON output first."
                )
            if not guardrail_target.get("summary", {}).get("pass"):
                raise NotionError(
                    "Refusing --write: target portfolio fails guardrail checks."
                )
            ds = fetch_layer3_data_sources(token)
            policy_id = policy_source.get("id") if policy_source.get("type") == "notion" else None
            write_result = write_analysis(
                token,
                ds,
                output,
                snapshot_id=snapshot["id"],
                policy_id=policy_id,
            )
            print(json.dumps({"notion_write": write_result}, indent=2), file=sys.stderr)

        if args.fail_on_infeasible and plan.status == "infeasible":
            return 1
        return 0

    except (NotionError, FxError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
