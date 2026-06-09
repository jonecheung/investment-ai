"""Load guardrails.yaml and evaluate metrics against hard limits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SKIPPED_CHECKS = [
    {
        "id": "hard_limits.max_turnover_pct",
        "reason": "requires target portfolio comparison (Layer 3 planner)",
    },
    {
        "id": "hard_limits.min_reward_risk_ratio",
        "reason": "requires Trading Proposals candidate pool",
    },
    {
        "id": "hard_limits.max_risk_per_proposal_pct",
        "reason": "deferred in v1; see positions[].risk_at_stop_pct for per-line values",
    },
    {
        "id": "soft_preferences",
        "reason": "optimization objective, not a pass/fail check",
    },
    {
        "id": "regime_overrides.stale_pricing",
        "reason": "requires Trading Proposals",
    },
    {
        "id": "regime_overrides.watchlist_intent",
        "reason": "requires Trading Proposals",
    },
]


def load_policy(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Policy file must be a YAML mapping: {path}")
    return normalize_policy(data)


def normalize_policy(data: dict[str, Any]) -> dict[str, Any]:
    hard = data.get("hard_limits") or {}
    required_hard = (
        "max_holdings_count",
        "min_cash_pct",
        "max_cash_pct",
        "max_single_holding_pct",
        "max_portfolio_heat_pct",
    )
    missing = [key for key in required_hard if hard.get(key) is None]
    if missing:
        raise ValueError(
            "Policy is missing required hard_limits values: "
            + ", ".join(missing)
        )
    return data


def policy_from_notion(record: dict[str, Any]) -> dict[str, Any]:
    policy = {
        "schema_version": record.get("schema_version"),
        "status": record.get("status"),
        "policy_name": record.get("title"),
        "effective_date": record.get("effective_date"),
        "base_currency": record.get("base_currency"),
        "hard_limits": record.get("hard_limits") or {},
        "market_limits": record.get("market_limits") or {},
        "asset_class_limits": record.get("asset_class_limits") or {},
        "soft_preferences": record.get("soft_preferences") or {},
        "regime_overrides": record.get("regime_overrides") or {},
        "planner": record.get("planner") or {},
    }
    return normalize_policy(policy)


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _compare(metric: float, limit: float, op: str) -> bool:
    if op == "<=":
        return metric <= limit
    if op == ">=":
        return metric >= limit
    raise ValueError(f"Unsupported operator: {op}")


def build_effective_limits(
    policy: dict[str, Any],
    drawdown_pct: float | None,
) -> tuple[dict[str, float], dict[str, Any]]:
    hard = policy.get("hard_limits") or {}
    regime_cfg = _get_nested(policy, "regime_overrides", "drawdown_from_peak") or {}

    effective: dict[str, float] = {
        "hard_limits.max_holdings_count": float(hard["max_holdings_count"]),
        "hard_limits.min_cash_pct": float(hard["min_cash_pct"]),
        "hard_limits.max_cash_pct": float(hard["max_cash_pct"]),
        "hard_limits.max_single_holding_pct": float(hard["max_single_holding_pct"]),
        "hard_limits.max_portfolio_heat_pct": float(hard["max_portfolio_heat_pct"]),
    }

    for market in ("FX_MAJOR", "FX_CROSS", "FX_EM", "OTHER"):
        value = _get_nested(policy, "market_limits", market, "max_exposure_pct")
        if value is not None:
            effective[f"market_limits.{market}.max_exposure_pct"] = float(value)

    for asset_class in ("fx", "equity", "etf", "crypto"):
        value = _get_nested(policy, "asset_class_limits", asset_class, "max_exposure_pct")
        if value is not None:
            effective[f"asset_class_limits.{asset_class}.max_exposure_pct"] = float(value)

    regime_info: dict[str, Any] = {
        "drawdown_pct": drawdown_pct,
        "drawdown_triggered": False,
    }

    trigger = regime_cfg.get("trigger_pct")
    if drawdown_pct is not None and trigger is not None and drawdown_pct >= float(trigger):
        regime_info["drawdown_triggered"] = True
        heat_mult = float(regime_cfg.get("max_portfolio_heat_multiplier", 1.0))
        cash_floor = float(regime_cfg.get("min_cash_pct_floor", hard["min_cash_pct"]))
        effective["hard_limits.max_portfolio_heat_pct"] *= heat_mult
        effective["hard_limits.min_cash_pct"] = max(
            effective["hard_limits.min_cash_pct"],
            cash_floor,
        )

    return effective, regime_info


def evaluate_guardrails(
    policy: dict[str, Any],
    metrics: dict[str, Any],
    policy_source: dict[str, Any],
    drawdown_pct: float | None = None,
) -> dict[str, Any]:
    effective_limits, regime_info = build_effective_limits(policy, drawdown_pct)

    checks: list[dict[str, Any]] = []

    def add_check(check_id: str, metric: float, limit: float, op: str) -> None:
        checks.append(
            {
                "id": check_id,
                "metric": round(metric, 4),
                "limit": round(limit, 4),
                "op": op,
                "pass": _compare(metric, limit, op),
            }
        )

    add_check(
        "hard_limits.max_holdings_count",
        float(metrics["holdings_count"]),
        effective_limits["hard_limits.max_holdings_count"],
        "<=",
    )
    add_check(
        "hard_limits.min_cash_pct",
        float(metrics["cash_pct"]),
        effective_limits["hard_limits.min_cash_pct"],
        ">=",
    )
    add_check(
        "hard_limits.max_cash_pct",
        float(metrics["cash_pct"]),
        effective_limits["hard_limits.max_cash_pct"],
        "<=",
    )
    add_check(
        "hard_limits.max_single_holding_pct",
        float(metrics["max_single_holding_pct"]),
        effective_limits["hard_limits.max_single_holding_pct"],
        "<=",
    )
    add_check(
        "hard_limits.max_portfolio_heat_pct",
        float(metrics["portfolio_heat_pct"]),
        effective_limits["hard_limits.max_portfolio_heat_pct"],
        "<=",
    )

    market_exposure = metrics.get("market_exposure_pct") or {}
    for market in ("FX_MAJOR", "FX_CROSS", "FX_EM", "OTHER"):
        key = f"market_limits.{market}.max_exposure_pct"
        if key in effective_limits:
            add_check(
                key,
                float(market_exposure.get(market, 0.0)),
                effective_limits[key],
                "<=",
            )

    asset_exposure = metrics.get("asset_class_exposure_pct") or {}
    for asset_class in ("fx", "equity", "etf", "crypto"):
        key = f"asset_class_limits.{asset_class}.max_exposure_pct"
        if key in effective_limits:
            add_check(
                key,
                float(asset_exposure.get(asset_class, 0.0)),
                effective_limits[key],
                "<=",
            )

    failed = sum(1 for check in checks if not check["pass"])

    return {
        "policy_source": policy_source,
        "policy_status": policy.get("status"),
        "regime": regime_info,
        "effective_limits": {k: round(v, 4) for k, v in effective_limits.items()},
        "checks": checks,
        "summary": {
            "pass": failed == 0,
            "failed": failed,
            "skipped": SKIPPED_CHECKS,
        },
    }
