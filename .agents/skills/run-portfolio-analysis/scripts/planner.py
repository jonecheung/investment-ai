"""Portfolio planner: unified rank, risk-budget sizing, and swap."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from universe import LineCandidate

RISK_STEP_PCT = 0.1  # increment per greedy step as % of NAV
NEW_PROPOSAL_BOOST = 0.05


def local_to_base_rate(
    line: LineCandidate,
    fx: dict[str, Any] | None,
    base_currency: str,
) -> float:
    """Multiplier: amount_base = amount_local * rate."""
    from fx_rates import resolve_holding_currency

    base = (fx or {}).get("base_currency") or base_currency
    holding = {"currency": line.currency, "market": line.market}
    currency = resolve_holding_currency(holding) or base
    if currency == base:
        return 1.0
    if fx is None:
        return 1.0
    rate = fx.get("rates", {}).get(currency)
    if rate is None or rate <= 0:
        return 1.0
    return float(rate)


def risk_per_unit(entry: float, stop: float, trade_type: str) -> float:
    if trade_type == "short":
        return max(0.0, stop - entry)
    return max(0.0, entry - stop)


def quantity_from_risk(risk: float, entry: float, stop: float, trade_type: str) -> float:
    per_unit = risk_per_unit(entry, stop, trade_type)
    if per_unit <= 0:
        return 0.0
    return risk / per_unit


def market_value_from_quantity(qty: float, price: float | None) -> float:
    if price is None or price <= 0:
        return 0.0
    return qty * price


def base_score(line: LineCandidate) -> float:
    rr = float(line.reward_risk_ratio or 0.0)
    return line.conviction_weight * rr


def effective_score(line: LineCandidate, existing_position_bias: float) -> float:
    score = base_score(line)
    if line.line_source in ("incumbent", "merged"):
        return score * (1.0 + existing_position_bias)
    if line.line_source == "proposal":
        return score * (1.0 + NEW_PROPOSAL_BOOST)
    return score


def line_score(line: LineCandidate) -> float:
    """Backward-compatible alias for base_score."""
    return base_score(line)


def objective_value(line: LineCandidate) -> float:
    if not line.included or line.target_risk_at_stop <= 0:
        return 0.0
    return base_score(line) * line.target_risk_at_stop


def sync_line_from_risk(
    line: LineCandidate,
    nav: float,
    fx: dict[str, Any] | None = None,
    base_currency: str = "HKD",
) -> None:
    """Update quantity and MV from target_risk_at_stop (base currency)."""
    entry = line.entry_price
    stop = line.stop_price
    if entry is None or stop is None:
        return
    rate = local_to_base_rate(line, fx, base_currency)
    risk_local = line.target_risk_at_stop / rate if rate > 0 else line.target_risk_at_stop
    qty = quantity_from_risk(risk_local, entry, stop, line.trade_type)
    price = line.reference_price or entry
    line.target_quantity = qty
    line.target_market_value = market_value_from_quantity(qty, price) * rate


def zero_line_targets(line: LineCandidate) -> None:
    line.included = False
    line.target_risk_at_stop = 0.0
    line.target_quantity = 0.0
    line.target_market_value = 0.0


def lines_to_holdings(lines: list[LineCandidate], cash_mv: float) -> list[dict[str, Any]]:
    holdings: list[dict[str, Any]] = []
    for line in lines:
        if not line.included or line.target_market_value <= 0:
            continue
        holdings.append(
            {
                "ticker": line.ticker,
                "holding_type": "holding",
                "market": line.market,
                "currency": line.currency,
                "asset_class": line.asset_class,
                "trade_type": line.trade_type,
                "quantity": line.target_quantity,
                "market_value": line.target_market_value,
                "entry_price": line.entry_price,
                "stop_price": line.stop_price,
            }
        )
    if cash_mv > 0:
        holdings.append(
            {
                "ticker": "CASH",
                "holding_type": "cash",
                "market": "OTHER",
                "currency": None,
                "asset_class": "cash",
                "trade_type": "n/a",
                "quantity": cash_mv,
                "market_value": cash_mv,
                "entry_price": None,
                "stop_price": None,
            }
        )
    return holdings


def compute_turnover_pct(lines: list[LineCandidate], nav: float) -> float:
    if nav <= 0:
        return 0.0
    delta = 0.0
    for line in lines:
        baseline = line.turnover_baseline_market_value
        if baseline is None:
            baseline = line.initial_market_value
        delta += abs(line.target_market_value - baseline)
    return delta / nav * 100.0


def _rebase_turnover_baseline(lines: list[LineCandidate]) -> None:
    for line in lines:
        line.turnover_baseline_market_value = line.target_market_value


def max_risk_per_line_nav_pct(policy: dict[str, Any], regime_info: dict[str, Any]) -> float:
    hard = policy.get("hard_limits") or {}
    base = float(hard.get("max_risk_per_proposal_pct") or 1.5)
    if regime_info.get("drawdown_triggered"):
        mult = float(
            (policy.get("regime_overrides") or {})
            .get("drawdown_from_peak", {})
            .get("max_risk_per_proposal_multiplier", 1.0)
        )
        return base * mult
    return base


@dataclass
class PlanResult:
    lines: list[LineCandidate]
    target_cash_mv: float
    initial_cash_mv: float
    status: str  # completed, infeasible
    infeasibility_reason: str | None = None
    planner_notes: list[str] = field(default_factory=list)
    fit_rejections: list[dict[str, Any]] = field(default_factory=list)


def _count_included(lines: list[LineCandidate]) -> int:
    return sum(1 for line in lines if line.included and line.target_market_value > 0)


def _can_add_line(lines: list[LineCandidate], max_holdings: int) -> bool:
    return _count_included(lines) < max_holdings


def _has_pricing(line: LineCandidate) -> bool:
    return line.entry_price is not None and line.stop_price is not None


def _trim_line_risk(
    line: LineCandidate,
    step_nav_pct: float,
    nav: float,
    fx: dict[str, Any] | None = None,
    base_currency: str = "HKD",
) -> None:
    step = nav * step_nav_pct / 100.0
    reducible = max(0.0, line.target_risk_at_stop - step)
    if reducible <= 0:
        zero_line_targets(line)
        return
    line.target_risk_at_stop = reducible
    sync_line_from_risk(line, nav, fx, base_currency)


def _trim_line_to_weight_cap(line: LineCandidate, nav: float, max_single_pct: float) -> None:
    max_mv = nav * max_single_pct / 100.0
    if line.target_market_value <= max_mv or max_mv <= 0:
        return
    scale = max_mv / line.target_market_value
    line.target_market_value = max_mv
    line.target_quantity *= scale
    line.target_risk_at_stop *= scale


def _restore_line_state(line: LineCandidate, snapshot: dict[str, float]) -> None:
    line.included = snapshot["included"]
    line.target_risk_at_stop = snapshot["target_risk_at_stop"]
    line.target_quantity = snapshot["target_quantity"]
    line.target_market_value = snapshot["target_market_value"]


def _snapshot_line_state(line: LineCandidate) -> dict[str, float | bool]:
    return {
        "included": line.included,
        "target_risk_at_stop": line.target_risk_at_stop,
        "target_quantity": line.target_quantity,
        "target_market_value": line.target_market_value,
    }


def _select_by_rank(
    working: list[LineCandidate],
    max_holdings: int,
    position_bias: float,
    fit_rejections: list[dict[str, Any]],
    *,
    rebuild: bool = True,
) -> None:
    """Keep top-ranked lines up to max_holdings; close the rest."""
    ranked = sorted(
        [line for line in working if _has_pricing(line)],
        key=lambda line: effective_score(line, position_bias),
        reverse=True,
    )
    selected = ranked[:max_holdings]
    selected_tickers = {line.ticker for line in selected}

    for line in working:
        if line.ticker in selected_tickers:
            line.included = True
            if rebuild:
                line.target_risk_at_stop = 0.0
                line.target_quantity = 0.0
                line.target_market_value = 0.0
            elif line.line_source == "proposal":
                line.target_risk_at_stop = 0.0
                line.target_quantity = 0.0
                line.target_market_value = 0.0
            continue

        if line.line_source == "proposal":
            if line.included:
                fit_rejections.append(
                    {
                        "ticker": line.ticker,
                        "reasons": ["not ranked in target set"],
                    }
                )
            zero_line_targets(line)
            continue

        if line.included:
            line.notes.append("closed: not ranked in target set")
        zero_line_targets(line)


def _trim_until_feasible(
    working: list[LineCandidate],
    nav: float,
    position_bias: float,
    effective_limits: dict[str, float],
    max_single_pct: float,
    target_state_fn: Any,
    current_cash_mv_fn: Any,
    notes: list[str],
    fx: dict[str, Any] | None = None,
    base_currency: str = "HKD",
    max_iters: int = 500,
) -> bool:
    for _ in range(max_iters):
        cash_mv = current_cash_mv_fn()
        metrics, _ = target_state_fn(cash_mv)
        failed = _failed_checks(metrics, effective_limits, cash_mv, nav)
        if not failed:
            return True
        if failed == ["max_cash_pct"]:
            # Excess cash is resolved by sizing/deployment, not trimming.
            return True

        if failed[0] == "max_cash_pct":
            # Trim increases cash; skip to other failing constraints if any.
            failed = [item for item in failed if item != "max_cash_pct"]
            if not failed:
                return True

        candidates = [
            line
            for line in working
            if line.included and (line.target_risk_at_stop > 0 or line.target_market_value > 0)
        ]
        if not candidates:
            return False

        if failed[0] == "max_single_holding_pct":
            over = [
                line
                for line in candidates
                if line.target_market_value > nav * max_single_pct / 100.0
            ]
            line = min(
                over or candidates,
                key=lambda item: effective_score(item, position_bias),
            )
            _trim_line_to_weight_cap(line, nav, max_single_pct)
            line.notes.append(f"trimmed for feasibility: {failed[0]}")
            continue

        line = min(candidates, key=lambda item: effective_score(item, position_bias))
        _trim_line_risk(line, RISK_STEP_PCT, nav, fx, base_currency)
        line.notes.append(f"trimmed for feasibility: {failed[0]}")
        notes.append(f"trimmed {line.ticker} for {failed[0]}")
    return False


def _try_risk_step(
    line: LineCandidate,
    nav: float,
    max_risk_line: float,
    heat_step: float,
    fx: dict[str, Any] | None,
    base_currency: str,
    *,
    is_new: bool,
) -> bool:
    if not _has_pricing(line):
        return False

    if is_new:
        if line.included and line.target_risk_at_stop > 0:
            return False
        line.included = True
        line.target_risk_at_stop = min(heat_step, max_risk_line)
    elif line.target_risk_at_stop < max_risk_line:
        line.target_risk_at_stop = min(line.target_risk_at_stop + heat_step, max_risk_line)
    else:
        return False

    sync_line_from_risk(line, nav, fx, base_currency)
    return True


def _revert_risk_step(
    line: LineCandidate,
    nav: float,
    heat_step: float,
    fx: dict[str, Any] | None,
    base_currency: str,
    *,
    is_new: bool,
) -> None:
    if is_new:
        zero_line_targets(line)
        return
    line.target_risk_at_stop = max(0.0, line.target_risk_at_stop - heat_step)
    if line.target_risk_at_stop <= 0:
        zero_line_targets(line)
    else:
        sync_line_from_risk(line, nav, fx, base_currency)


def _blocking_failures(
    failed: list[str],
    cash_mv: float,
    nav: float,
    effective_limits: dict[str, float],
) -> list[str]:
    """Failures that should block the current move (cash deploy/raise handled separately)."""
    if not failed:
        return []
    cash_pct = cash_mv / nav * 100.0 if nav else 0.0
    blocking = list(failed)
    if cash_pct > effective_limits["hard_limits.max_cash_pct"]:
        blocking = [item for item in blocking if item != "max_cash_pct"]
    if cash_pct < effective_limits["hard_limits.min_cash_pct"]:
        blocking = [item for item in blocking if item != "min_cash_pct"]
    return blocking


def _greedy_size(
    working: list[LineCandidate],
    nav: float,
    position_bias: float,
    effective_limits: dict[str, float],
    max_risk_line: float,
    heat_step: float,
    max_turnover: float,
    max_holdings: int,
    target_state_fn: Any,
    current_cash_mv_fn: Any,
    fit_rejections: list[dict[str, Any]],
    fx: dict[str, Any] | None = None,
    base_currency: str = "HKD",
    max_iters: int = 1000,
) -> None:
    for _ in range(max_iters):
        improved = False
        candidates = sorted(
            working,
            key=lambda line: effective_score(line, position_bias),
            reverse=True,
        )
        for line in candidates:
            is_new = line.target_market_value <= 0 and line.initial_market_value <= 0
            reopen = line.target_market_value <= 0 and line.initial_market_value > 0
            if is_new and not _can_add_line(working, max_holdings):
                continue

            before = _snapshot_line_state(line)
            if not _try_risk_step(
                line,
                nav,
                max_risk_line,
                heat_step,
                fx,
                base_currency,
                is_new=is_new or reopen,
            ):
                continue

            cash_mv = current_cash_mv_fn()
            min_cash_pct = effective_limits["hard_limits.min_cash_pct"]
            if cash_mv / nav * 100.0 < min_cash_pct:
                _restore_line_state(line, before)
                continue

            metrics, _ = target_state_fn(cash_mv)
            failed = _failed_checks(metrics, effective_limits, cash_mv, nav)
            blocking = _blocking_failures(failed, cash_mv, nav, effective_limits)
            turnover = compute_turnover_pct(working, nav)
            if blocking or turnover > max_turnover:
                _restore_line_state(line, before)
                if (is_new or reopen) and not line.included:
                    fit_rejections.append(
                        {
                            "ticker": line.ticker,
                            "reasons": [
                                f"cannot fit: {blocking[0] if blocking else 'turnover cap'}"
                            ],
                        }
                    )
                continue

            improved = True
            break

        if not improved:
            break


def _try_swap(
    working: list[LineCandidate],
    nav: float,
    position_bias: float,
    effective_limits: dict[str, float],
    max_risk_line: float,
    heat_step: float,
    max_turnover: float,
    max_holdings: int,
    target_state_fn: Any,
    current_cash_mv_fn: Any,
    fx: dict[str, Any] | None = None,
    base_currency: str = "HKD",
) -> bool:
    included = [
        line
        for line in working
        if line.included and line.target_market_value > 0 and line.line_source != "proposal"
    ]
    excluded = [
        line
        for line in working
        if line.line_source == "proposal"
        and (not line.included or line.target_market_value <= 0)
        and _has_pricing(line)
    ]
    if not included or not excluded:
        return False

    worst = min(included, key=lambda line: effective_score(line, position_bias))
    best = max(excluded, key=lambda line: effective_score(line, position_bias))
    if effective_score(best, position_bias) <= effective_score(worst, position_bias):
        return False

    if not _can_add_line(working, max_holdings) and worst.target_market_value <= 0:
        return False

    snapshots = {line.ticker: _snapshot_line_state(line) for line in (worst, best)}

    zero_line_targets(worst)
    worst.notes.append(f"closed for swap: {best.ticker}")

    best.included = True
    best.target_risk_at_stop = min(heat_step, max_risk_line)
    sync_line_from_risk(best, nav, fx, base_currency)

    cash_mv = current_cash_mv_fn()
    metrics, _ = target_state_fn(cash_mv)
    failed = _failed_checks(metrics, effective_limits, cash_mv, nav)
    blocking = _blocking_failures(failed, cash_mv, nav, effective_limits)
    turnover = compute_turnover_pct(working, nav)

    if blocking or turnover > max_turnover:
        _restore_line_state(worst, snapshots[worst.ticker])  # type: ignore[arg-type]
        _restore_line_state(best, snapshots[best.ticker])  # type: ignore[arg-type]
        return False

    best.notes.append(f"added via swap from {worst.ticker}")
    return True


def run_planner(
    lines: list[LineCandidate],
    nav: float,
    initial_cash_mv: float,
    policy: dict[str, Any],
    input_metrics: dict[str, Any],
    guardrail_check_input: dict[str, Any],
    compute_target_metrics_fn: Any,
    fx: dict[str, Any] | None,
) -> PlanResult:
    """
    Unified rank + risk-budget sizing + swap within guardrails.
    compute_target_metrics_fn(snapshot, holdings, fx) -> metrics_result dict
    """
    from guardrails import build_effective_limits

    working = deepcopy(lines)
    hard = policy.get("hard_limits") or {}
    soft = policy.get("soft_preferences") or {}
    objective = (soft.get("objective") or "maximize_conviction_weighted_reward_risk").lower()
    position_bias = float(soft.get("existing_position_bias") or 0.0)
    max_turnover = float(hard.get("max_turnover_pct") or 100.0)
    max_holdings = int(hard.get("max_holdings_count") or 10)

    drawdown_pct = guardrail_check_input.get("regime", {}).get("drawdown_pct")
    effective_limits, regime_info = build_effective_limits(policy, drawdown_pct)
    max_single_pct = effective_limits["hard_limits.max_single_holding_pct"]
    max_risk_line_pct = max_risk_per_line_nav_pct(policy, regime_info)
    max_risk_line = nav * max_risk_line_pct / 100.0
    heat_step = nav * RISK_STEP_PCT / 100.0
    base_currency = policy.get("base_currency") or "HKD"

    notes: list[str] = []
    fit_rejections: list[dict[str, Any]] = []

    for line in working:
        if line.line_source == "proposal":
            line.included = False
            line.target_risk_at_stop = 0.0
            line.target_quantity = 0.0
            line.target_market_value = 0.0

    def target_state(cash_mv: float) -> tuple[dict[str, Any], dict[str, Any]]:
        snapshot = {"nav": nav, "base_currency": policy.get("base_currency")}
        holdings = lines_to_holdings(working, cash_mv)
        result = compute_target_metrics_fn(snapshot, holdings, fx=fx)
        return result["metrics"], holdings

    def current_cash_mv() -> float:
        invested = sum(line.target_market_value for line in working if line.included)
        return max(0.0, nav - invested)

    input_pass = guardrail_check_input.get("summary", {}).get("pass", False)

    if not input_pass:
        notes.append("Select: rank all lines and rebuild target set from zero")
        _select_by_rank(working, max_holdings, position_bias, fit_rejections, rebuild=True)
        _rebase_turnover_baseline(working)
        notes.append("Rebased turnover baseline after rank rebuild")
    elif objective == "minimize_turnover":
        notes.append("Input feasible: retain incumbents (minimize turnover)")
    else:
        notes.append("Input feasible: retain incumbents, compete with proposals")

    cash_mv = current_cash_mv()
    metrics, _ = target_state(cash_mv)
    failed = _failed_checks(metrics, effective_limits, cash_mv, nav)

    if failed:
        if not input_pass and objective == "minimize_turnover":
            # Trim-only path when minimizing turnover on an infeasible snapshot.
            for line in working:
                if line.included and line.initial_market_value > 0:
                    line.target_market_value = line.initial_market_value
                    line.target_quantity = line.initial_quantity
                    line.target_risk_at_stop = line.initial_risk_at_stop
            _select_by_rank(
                working, max_holdings, position_bias, fit_rejections, rebuild=False
            )
            cash_mv = current_cash_mv()
            metrics, _ = target_state(cash_mv)
            failed = _failed_checks(metrics, effective_limits, cash_mv, nav)

        if failed and not _trim_until_feasible(
            working,
            nav,
            position_bias,
            effective_limits,
            max_single_pct,
            target_state,
            current_cash_mv,
            notes,
            fx,
            base_currency,
        ):
            return PlanResult(
                lines=working,
                target_cash_mv=current_cash_mv(),
                initial_cash_mv=initial_cash_mv,
                status="infeasible",
                infeasibility_reason="Cannot satisfy guardrails after rank/trim",
                planner_notes=notes,
                fit_rejections=fit_rejections,
            )

    if objective != "minimize_turnover":
        notes.append("Size: greedy risk-budget allocation by effective score")
        _greedy_size(
            working,
            nav,
            position_bias,
            effective_limits,
            max_risk_line,
            heat_step,
            max_turnover,
            max_holdings,
            target_state,
            current_cash_mv,
            fit_rejections,
            fx,
            base_currency,
        )

        notes.append("Swap: replace lower-ranked incumbents with higher-ranked proposals")
        for _ in range(max_holdings * 2):
            if not _try_swap(
                working,
                nav,
                position_bias,
                effective_limits,
                max_risk_line,
                heat_step,
                max_turnover,
                max_holdings,
                target_state,
                current_cash_mv,
                fx,
                base_currency,
            ):
                break
            _greedy_size(
                working,
                nav,
                position_bias,
                effective_limits,
                max_risk_line,
                heat_step,
                max_turnover,
                max_holdings,
                target_state,
                current_cash_mv,
                fit_rejections,
                fx,
                base_currency,
                max_iters=200,
            )

        if not _trim_until_feasible(
            working,
            nav,
            position_bias,
            effective_limits,
            max_single_pct,
            target_state,
            current_cash_mv,
            notes,
            fx,
            base_currency,
        ):
            return PlanResult(
                lines=working,
                target_cash_mv=current_cash_mv(),
                initial_cash_mv=initial_cash_mv,
                status="infeasible",
                infeasibility_reason="Cannot satisfy guardrails after sizing/swap",
                planner_notes=notes,
                fit_rejections=fit_rejections,
            )

    target_cash = current_cash_mv()
    metrics, _ = target_state(target_cash)
    failed = _failed_checks(metrics, effective_limits, target_cash, nav)
    status = "completed" if not failed else "infeasible"
    reason = None if not failed else f"Target fails: {failed[0]}"

    return PlanResult(
        lines=working,
        target_cash_mv=target_cash,
        initial_cash_mv=initial_cash_mv,
        status=status,
        infeasibility_reason=reason,
        planner_notes=notes,
        fit_rejections=fit_rejections,
    )


def _failed_checks(
    metrics: dict[str, Any],
    effective_limits: dict[str, float],
    cash_mv: float,
    nav: float,
) -> list[str]:
    failures: list[str] = []
    cash_pct = cash_mv / nav * 100.0 if nav else 0.0

    if metrics.get("portfolio_heat_pct", 0) > effective_limits["hard_limits.max_portfolio_heat_pct"]:
        failures.append("max_portfolio_heat_pct")
    if metrics.get("max_single_holding_pct", 0) > effective_limits["hard_limits.max_single_holding_pct"]:
        failures.append("max_single_holding_pct")
    if cash_pct < effective_limits["hard_limits.min_cash_pct"]:
        failures.append("min_cash_pct")
    if cash_pct > effective_limits["hard_limits.max_cash_pct"]:
        failures.append("max_cash_pct")
    if metrics.get("holdings_count", 0) > effective_limits["hard_limits.max_holdings_count"]:
        failures.append("max_holdings_count")

    for market in ("HK", "JP", "US", "OTHER"):
        key = f"market_limits.{market}.max_exposure_pct"
        if key in effective_limits:
            exp = (metrics.get("market_exposure_pct") or {}).get(market, 0.0)
            if exp > effective_limits[key]:
                failures.append(key)

    for ac in ("equity", "etf", "crypto"):
        key = f"asset_class_limits.{ac}.max_exposure_pct"
        if key in effective_limits:
            exp = (metrics.get("asset_class_exposure_pct") or {}).get(ac, 0.0)
            if exp > effective_limits[key]:
                failures.append(key)

    return failures
