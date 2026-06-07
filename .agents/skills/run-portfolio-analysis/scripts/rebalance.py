"""Build rebalance action rows from plan result."""

from __future__ import annotations

from typing import Any

from planner import LineCandidate


def action_hint(line: LineCandidate) -> str:
    delta = line.target_market_value - line.initial_market_value
    if abs(delta) < 1e-6:
        return "hold"
    if line.initial_market_value <= 0 and line.target_market_value > 0:
        return "add"
    if line.target_market_value <= 0 and line.initial_market_value > 0:
        return "remove"
    if delta > 0:
        return "increase"
    return "decrease"


def action_type(line: LineCandidate) -> str:
    delta_mv = line.target_market_value - line.initial_market_value
    if abs(delta_mv) < 1e-6:
        return "hold"
    if line.initial_market_value <= 0 and line.target_market_value > 0:
        return "add"
    if line.target_market_value <= 0 and line.initial_market_value > 0:
        return "close"
    if delta_mv < 0:
        return "trim" if line.target_market_value > 0 else "close"
    return "buy"


def build_rebalance_actions(
    lines: list[LineCandidate],
    initial_cash_mv: float,
    target_cash_mv: float,
    nav: float,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    seq = 1

    for line in lines:
        if not line.included and line.initial_market_value <= 0:
            continue
        delta_mv = line.target_market_value - line.initial_market_value
        delta_qty = line.target_quantity - line.initial_quantity
        if abs(delta_mv) < 1e-6 and abs(delta_qty) < 1e-6:
            continue

        atype = action_type(line)
        actions.append(
            {
                "ticker": line.ticker,
                "market": line.market,
                "currency": line.currency,
                "action_type": atype,
                "priority": "high" if abs(delta_mv) / nav * 100 > 5 else "medium",
                "sequence": seq,
                "current_market_value": round(line.initial_market_value, 4),
                "target_market_value": round(line.target_market_value, 4),
                "delta_market_value": round(delta_mv, 4),
                "current_quantity": round(line.initial_quantity, 6),
                "target_quantity": round(line.target_quantity, 6),
                "delta_quantity": round(delta_qty, 6),
                "reference_price": line.reference_price,
                "entry_price": line.entry_price,
                "stop_price": line.stop_price,
                "rationale": "; ".join(line.notes) if line.notes else None,
                "constraint_notes": None,
                "source_proposal_id": line.source_proposal_id,
                "related_holding_id": line.source_holding_id,
                "title": f"{line.ticker} {atype}",
            }
        )
        seq += 1

    cash_delta = target_cash_mv - initial_cash_mv
    if abs(cash_delta) >= 1e-6:
        actions.append(
            {
                "ticker": "CASH",
                "market": "OTHER",
                "currency": None,
                "action_type": "buy" if cash_delta > 0 else "sell",
                "priority": "medium",
                "sequence": seq,
                "current_market_value": round(initial_cash_mv, 4),
                "target_market_value": round(target_cash_mv, 4),
                "delta_market_value": round(cash_delta, 4),
                "current_quantity": round(initial_cash_mv, 4),
                "target_quantity": round(target_cash_mv, 4),
                "delta_quantity": round(cash_delta, 4),
                "reference_price": None,
                "entry_price": None,
                "stop_price": None,
                "rationale": "Cash adjustment to match target allocation",
                "constraint_notes": None,
                "source_proposal_id": None,
                "related_holding_id": None,
                "title": f"CASH {'buy' if cash_delta > 0 else 'sell'}",
            }
        )

    return actions
