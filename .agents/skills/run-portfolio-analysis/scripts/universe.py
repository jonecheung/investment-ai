"""Build planner universe from snapshot holdings and eligible proposals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LineCandidate:
    ticker: str
    line_source: str  # incumbent, proposal, merged
    market: str | None = None
    asset_class: str | None = None
    currency: str | None = None
    trade_type: str = "long"
    company_name: str | None = None
    risk_bucket: str | None = None
    entry_price: float | None = None
    stop_price: float | None = None
    target_price: float | None = None
    reward_risk_ratio: float | None = None
    conviction: str = "medium"
    reference_price: float | None = None
    # Current state (incumbent / merged)
    initial_market_value: float = 0.0
    initial_quantity: float = 0.0
    initial_risk_at_stop: float = 0.0
    # Planned state (mutated by planner)
    target_market_value: float = 0.0
    target_quantity: float = 0.0
    target_risk_at_stop: float = 0.0
    source_holding_id: str | None = None
    source_proposal_id: str | None = None
    included: bool = True
    conviction_weight: float = 1.0
    turnover_baseline_market_value: float | None = None
    notes: list[str] = field(default_factory=list)


def _norm_ticker(ticker: str | None) -> str:
    return (ticker or "").strip().upper()


def _conviction_weight(conviction: str, weights: dict[str, float]) -> float:
    key = (conviction or "medium").lower()
    return float(weights.get(key) or weights.get("medium") or 1.0)


def _compute_rr(
    entry: float | None,
    stop: float | None,
    target: float | None,
    trade_type: str,
) -> float | None:
    if entry is None or stop is None or target is None:
        return None
    if trade_type == "short":
        risk = stop - entry
        reward = entry - target
    else:
        risk = entry - stop
        reward = target - entry
    if risk <= 0:
        return None
    return reward / risk


def build_universe(
    holdings: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    positions_metrics: list[dict[str, Any]],
    conviction_weights: dict[str, float],
) -> list[LineCandidate]:
    """Merge incumbents and proposals into LineCandidate rows."""
    risk_by_ticker = {
        _norm_ticker(p.get("ticker")): float(p.get("risk_at_stop") or 0.0)
        for p in positions_metrics
        if p.get("ticker")
    }

    incumbents: dict[str, LineCandidate] = {}
    for h in holdings:
        ticker = _norm_ticker(h.get("ticker"))
        if not ticker or ticker == "CASH":
            continue
        htype = (h.get("holding_type") or "").lower()
        if htype == "cash":
            continue

        mv = float(h.get("market_value") or 0.0)
        qty = float(h.get("quantity") or 0.0)
        risk = risk_by_ticker.get(ticker, 0.0)

        line = LineCandidate(
            ticker=ticker,
            line_source="incumbent",
            market=h.get("market"),
            asset_class=(h.get("asset_class") or "equity").lower(),
            currency=h.get("currency"),
            trade_type=(h.get("trade_type") or "long").lower(),
            entry_price=h.get("entry_price"),
            stop_price=h.get("stop_price"),
            target_price=h.get("target_price"),
            reference_price=h.get("entry_price") or h.get("market_price"),
            initial_market_value=mv,
            initial_quantity=qty,
            initial_risk_at_stop=risk,
            target_market_value=mv,
            target_quantity=qty,
            target_risk_at_stop=risk,
            source_holding_id=h.get("page_id"),
        )
        incumbents[ticker] = line

    for line in incumbents.values():
        if line.reward_risk_ratio is None:
            line.reward_risk_ratio = _compute_rr(
                line.entry_price, line.stop_price, line.target_price, line.trade_type
            ) or 1.0

    proposal_by_ticker: dict[str, dict[str, Any]] = {}
    for prop in proposals:
        ticker = _norm_ticker(prop.get("ticker"))
        if ticker:
            proposal_by_ticker[ticker] = prop

    universe: list[LineCandidate] = []

    for ticker, inc in incumbents.items():
        if ticker in proposal_by_ticker:
            prop = proposal_by_ticker[ticker]
            inc.line_source = "merged"
            inc.source_proposal_id = prop.get("page_id")
            inc.entry_price = prop.get("entry_price") or inc.entry_price
            inc.stop_price = prop.get("stop_price") or inc.stop_price
            inc.target_price = prop.get("target_price")
            inc.reward_risk_ratio = prop.get("reward_risk_ratio")
            inc.conviction = (prop.get("conviction") or "medium").lower()
            inc.company_name = prop.get("company_name") or inc.company_name
            inc.risk_bucket = prop.get("risk_bucket") or inc.risk_bucket
            inc.reference_price = prop.get("last_price") or prop.get("entry_price") or inc.reference_price
            if prop.get("market"):
                inc.market = prop.get("market")
            if prop.get("asset_class"):
                inc.asset_class = prop.get("asset_class")
            if prop.get("currency"):
                inc.currency = prop.get("currency")
            del proposal_by_ticker[ticker]
        universe.append(inc)

    for ticker, prop in proposal_by_ticker.items():
        line = LineCandidate(
            ticker=ticker,
            line_source="proposal",
            market=prop.get("market"),
            asset_class=prop.get("asset_class") or "equity",
            currency=prop.get("currency"),
            trade_type=(prop.get("trade_type") or "long").lower(),
            company_name=prop.get("company_name"),
            risk_bucket=prop.get("risk_bucket"),
            entry_price=prop.get("entry_price"),
            stop_price=prop.get("stop_price"),
            target_price=prop.get("target_price"),
            reward_risk_ratio=prop.get("reward_risk_ratio"),
            conviction=(prop.get("conviction") or "medium").lower(),
            reference_price=prop.get("last_price") or prop.get("entry_price"),
            source_proposal_id=prop.get("page_id"),
            included=False,
        )
        universe.append(line)

    for line in universe:
        line.conviction_weight = _conviction_weight(line.conviction, conviction_weights)

    return universe


def get_cash_holding(holdings: list[dict[str, Any]]) -> dict[str, Any] | None:
    for h in holdings:
        ticker = _norm_ticker(h.get("ticker"))
        htype = (h.get("holding_type") or "").lower()
        if ticker == "CASH" or htype == "cash":
            return h
    return None
