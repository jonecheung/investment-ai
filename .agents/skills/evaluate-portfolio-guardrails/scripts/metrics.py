"""Portfolio metric computation from normalized snapshot data."""

from __future__ import annotations

from typing import Any

from fx_rates import convert_to_base, resolve_holding_currency

MARKET_KEYS = ("FX_MAJOR", "FX_CROSS", "FX_EM", "OTHER")
ASSET_CLASS_KEYS = ("fx", "equity", "etf", "crypto")


def _is_cash(holding: dict[str, Any]) -> bool:
    holding_type = (holding.get("holding_type") or "").lower()
    ticker = (holding.get("ticker") or "").upper()
    asset_class = (holding.get("asset_class") or "").lower()
    return holding_type == "cash" or ticker == "CASH" or asset_class == "cash"


def _risk_at_stop_local(holding: dict[str, Any]) -> tuple[float | None, list[str]]:
    warnings: list[str] = []
    if _is_cash(holding):
        return 0.0, warnings

    quantity = holding.get("quantity")
    entry = holding.get("entry_price")
    stop = holding.get("stop_price")
    trade_type = (holding.get("trade_type") or "long").lower()

    if quantity is None or entry is None or stop is None:
        ticker = holding.get("ticker") or "?"
        warnings.append(f"{ticker}: missing quantity, entry_price, or stop_price for risk-at-stop")
        return None, warnings

    if trade_type == "short":
        per_unit = max(0.0, stop - entry)
    else:
        per_unit = max(0.0, entry - stop)

    return quantity * per_unit, warnings


def compute_metrics(
    snapshot: dict[str, Any],
    holdings: list[dict[str, Any]],
    fx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nav = float(snapshot["nav"])
    positions: list[dict[str, Any]] = []
    all_warnings: list[str] = []

    market_exposure: dict[str, float] = {k: 0.0 for k in MARKET_KEYS}
    asset_class_exposure: dict[str, float] = {k: 0.0 for k in ASSET_CLASS_KEYS}

    cash_value = 0.0
    holdings_count = 0
    max_single_holding_pct = 0.0
    total_risk_at_stop = 0.0

    for holding in holdings:
        market_value = holding.get("market_value")
        if market_value is None:
            ticker = holding.get("ticker") or "?"
            all_warnings.append(f"{ticker}: missing market_value; skipped in aggregates")
            continue

        weight_pct = market_value / nav * 100.0
        is_cash = _is_cash(holding)

        risk_local, warnings = _risk_at_stop_local(holding)
        currency = resolve_holding_currency(holding)
        risk = risk_local
        fx_warning = None

        if risk is not None and fx is not None:
            risk, fx_warning = convert_to_base(risk, currency, fx)
            if fx_warning:
                ticker = holding.get("ticker") or "?"
                warnings.append(f"{ticker}: {fx_warning}")

        all_warnings.extend(warnings)

        risk_at_stop_pct = None
        if risk is not None:
            total_risk_at_stop += risk
            risk_at_stop_pct = risk / nav * 100.0

        if is_cash:
            cash_value += market_value
        else:
            holdings_count += 1
            if weight_pct > max_single_holding_pct:
                max_single_holding_pct = weight_pct

            market = holding.get("market") or "OTHER"
            if market not in market_exposure:
                market = "OTHER"
            market_exposure[market] += weight_pct

            asset_class = (holding.get("asset_class") or "other").lower()
            if asset_class in asset_class_exposure:
                asset_class_exposure[asset_class] += weight_pct

        positions.append(
            {
                "ticker": holding.get("ticker"),
                "holding_type": holding.get("holding_type"),
                "currency": currency,
                "weight_pct": round(weight_pct, 4),
                "risk_at_stop_local": round(risk_local, 4) if risk_local is not None else None,
                "risk_at_stop": round(risk, 4) if risk is not None else None,
                "risk_at_stop_pct": round(risk_at_stop_pct, 4) if risk_at_stop_pct is not None else None,
                "market": holding.get("market"),
                "asset_class": holding.get("asset_class"),
                "trade_type": holding.get("trade_type"),
                "warnings": warnings,
            }
        )

    cash_pct = cash_value / nav * 100.0
    portfolio_heat_pct = total_risk_at_stop / nav * 100.0

    result: dict[str, Any] = {
        "metrics": {
            "holdings_count": holdings_count,
            "cash_pct": round(cash_pct, 4),
            "max_single_holding_pct": round(max_single_holding_pct, 4),
            "portfolio_heat_pct": round(portfolio_heat_pct, 4),
            "market_exposure_pct": {k: round(v, 4) for k, v in market_exposure.items()},
            "asset_class_exposure_pct": {k: round(v, 4) for k, v in asset_class_exposure.items()},
        },
        "positions": positions,
        "warnings": all_warnings,
    }
    if fx is not None:
        result["fx_rates"] = {
            "base_currency": fx["base_currency"],
            "provider": fx.get("provider"),
            "as_of": fx.get("as_of"),
            "rates": fx["rates"],
            "sources": fx["sources"],
        }
    return result
