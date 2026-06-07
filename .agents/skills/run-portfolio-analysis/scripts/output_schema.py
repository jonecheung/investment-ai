"""Build JSON output contract for portfolio analysis."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from planner import LineCandidate, PlanResult, compute_turnover_pct, lines_to_holdings
from rebalance import action_hint, build_rebalance_actions


def build_target_holdings(
    lines: list[LineCandidate],
    target_cash_mv: float,
    nav: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.included or line.target_market_value <= 0:
            continue
        weight = line.target_market_value / nav * 100.0 if nav else 0.0
        risk_pct = line.target_risk_at_stop / nav * 100.0 if nav else 0.0
        rows.append(
            {
                "ticker": line.ticker,
                "holding_type": "holding",
                "company_name": line.company_name,
                "market": line.market,
                "asset_class": line.asset_class,
                "currency": line.currency,
                "trade_type": line.trade_type,
                "target_weight_pct": round(weight, 4),
                "target_market_value": round(line.target_market_value, 4),
                "target_quantity": round(line.target_quantity, 6),
                "entry_price": line.entry_price,
                "stop_price": line.stop_price,
                "target_price": line.target_price,
                "risk_at_stop": round(line.target_risk_at_stop, 4),
                "risk_at_stop_pct": round(risk_pct, 4),
                "line_source": line.line_source,
                "action_hint": action_hint(line),
                "source_proposal_id": line.source_proposal_id,
                "source_holding_id": line.source_holding_id,
                "notes": "; ".join(line.notes) if line.notes else None,
                "title": line.ticker,
            }
        )

    if target_cash_mv > 0:
        cash_weight = target_cash_mv / nav * 100.0 if nav else 0.0
        rows.append(
            {
                "ticker": "CASH",
                "holding_type": "cash",
                "company_name": None,
                "market": "OTHER",
                "asset_class": "cash",
                "currency": None,
                "trade_type": "n/a",
                "target_weight_pct": round(cash_weight, 4),
                "target_market_value": round(target_cash_mv, 4),
                "target_quantity": round(target_cash_mv, 4),
                "entry_price": None,
                "stop_price": None,
                "target_price": None,
                "risk_at_stop": 0.0,
                "risk_at_stop_pct": 0.0,
                "line_source": "cash",
                "action_hint": "hold",
                "source_proposal_id": None,
                "source_holding_id": None,
                "notes": None,
                "title": "CASH",
            }
        )
    return rows


def build_executive_summary(
    plan: PlanResult,
    input_metrics: dict[str, Any],
    target_metrics: dict[str, Any],
    guardrail_check: dict[str, Any],
    rejection_count: int,
) -> str:
    lines = [
        f"Status: {plan.status}.",
        f"Input heat {input_metrics.get('portfolio_heat_pct')}% → target {target_metrics.get('portfolio_heat_pct')}%.",
        f"Input cash {input_metrics.get('cash_pct')}% → target {target_metrics.get('cash_pct')}%.",
        f"Holdings {input_metrics.get('holdings_count')} → {target_metrics.get('holdings_count')}.",
        f"Guardrail check: {'PASS' if guardrail_check.get('summary', {}).get('pass') else 'FAIL'}.",
        f"Rejections: {rejection_count} proposal(s) filtered or could not fit.",
    ]
    if plan.infeasibility_reason:
        lines.append(f"Infeasibility: {plan.infeasibility_reason}")
    return " ".join(lines)


def build_output(
    *,
    snapshot: dict[str, Any],
    policy_source: dict[str, Any],
    policy: dict[str, Any],
    input_metrics: dict[str, Any],
    target_metrics: dict[str, Any],
    guardrail_check_input: dict[str, Any],
    guardrail_check_target: dict[str, Any],
    plan: PlanResult,
    filter_rejections: list[dict[str, Any]],
    candidate_proposals_count: int,
    eligible_proposals_count: int,
    rebalance_actions: list[dict[str, Any]],
    fx_rates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nav = float(snapshot["nav"])
    turnover = compute_turnover_pct(plan.lines, nav)
    non_hold_actions = [a for a in rebalance_actions if a.get("action_type") != "hold"]

    effective = guardrail_check_target.get("effective_limits") or {}
    soft = policy.get("soft_preferences") or {}
    regime = guardrail_check_target.get("regime") or {}

    analysis = {
        "status": plan.status,
        "analysis_date": date.today().isoformat(),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": snapshot.get("id"),
        "snapshot_date": snapshot.get("snapshot_date"),
        "snapshot_title": snapshot.get("title"),
        "policy_source": policy_source,
        "policy_id": policy_source.get("id") if policy_source.get("type") == "notion" else None,
        "base_currency": snapshot.get("base_currency") or policy.get("base_currency"),
        "input_nav": nav,
        "input_cash_pct": input_metrics.get("cash_pct"),
        "input_portfolio_heat_pct": input_metrics.get("portfolio_heat_pct"),
        "input_holdings_count": input_metrics.get("holdings_count"),
        "candidate_proposals_count": candidate_proposals_count,
        "eligible_proposals_count": eligible_proposals_count,
        "max_portfolio_heat_pct": effective.get("hard_limits.max_portfolio_heat_pct"),
        "max_single_holding_pct": effective.get("hard_limits.max_single_holding_pct"),
        "min_cash_pct": effective.get("hard_limits.min_cash_pct"),
        "max_turnover_pct": policy.get("hard_limits", {}).get("max_turnover_pct"),
        "objective": soft.get("objective"),
        "sizing_method": (policy.get("planner") or {}).get("sizing_method"),
        "drawdown_triggered": regime.get("drawdown_triggered", False),
        "regime_notes": None,
        "target_nav": nav,
        "target_cash_pct": target_metrics.get("cash_pct"),
        "target_portfolio_heat_pct": target_metrics.get("portfolio_heat_pct"),
        "target_holdings_count": target_metrics.get("holdings_count"),
        "turnover_pct": round(turnover, 4),
        "rebalance_actions_count": len(non_hold_actions),
        "infeasibility_reason": plan.infeasibility_reason,
        "error_message": None,
        "planner_notes": plan.planner_notes,
    }

    all_rejections = filter_rejections + plan.fit_rejections
    rejection_summary = "; ".join(
        f"{r.get('ticker')}: {', '.join(r.get('reasons', []))}"
        for r in all_rejections[:20]
    )

    output = {
        "schema_version": 1,
        "computed_at": analysis["computed_at"],
        "analysis": analysis,
        "target_holdings": build_target_holdings(plan.lines, plan.target_cash_mv, nav),
        "rebalance_actions": rebalance_actions,
        "rejections": all_rejections,
        "guardrail_check_input": guardrail_check_input,
        "guardrail_check": guardrail_check_target,
        "executive_summary": build_executive_summary(
            plan,
            input_metrics,
            target_metrics,
            guardrail_check_target,
            len(all_rejections),
        ),
        "rejection_summary": rejection_summary or None,
    }
    if fx_rates:
        output["fx_rates"] = fx_rates
    return output
