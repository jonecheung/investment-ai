#!/usr/bin/env python3
"""Unit tests for portfolio planner (stdlib unittest, no Notion)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
GUARDRAILS = Path(__file__).resolve().parents[2] / "evaluate-portfolio-guardrails" / "scripts"
sys.path.insert(0, str(GUARDRAILS))
sys.path.insert(0, str(SCRIPTS))

from output_schema import build_target_holdings  # noqa: E402
from planner import (  # noqa: E402
    LineCandidate,
    compute_turnover_pct,
    effective_score,
    market_value_from_quantity,
    quantity_from_risk,
    risk_per_unit,
    run_planner,
    sync_line_from_risk,
)
from rebalance import action_type, build_rebalance_actions  # noqa: E402
from universe import build_universe  # noqa: E402


class TestSizing(unittest.TestCase):
    def test_quantity_from_risk_long(self):
        self.assertAlmostEqual(quantity_from_risk(1000, 100, 90, "long"), 100.0)

    def test_reward_at_target_equals_risk_times_rr(self):
        entry, stop, target = 100.0, 90.0, 120.0
        risk = 1000.0
        qty = quantity_from_risk(risk, entry, stop, "long")
        rr = (target - entry) / (entry - stop)
        self.assertAlmostEqual(qty * (target - entry), risk * rr)


class TestEffectiveScore(unittest.TestCase):
    def test_incumbent_bias(self):
        inc = LineCandidate(
            ticker="A",
            line_source="incumbent",
            reward_risk_ratio=2.0,
            conviction_weight=2.0,
        )
        prop = LineCandidate(
            ticker="B",
            line_source="proposal",
            reward_risk_ratio=2.0,
            conviction_weight=2.0,
        )
        self.assertGreater(effective_score(inc, 0.2), effective_score(prop, 0.2))

    def test_strong_proposal_beats_weak_incumbent(self):
        weak = LineCandidate(
            ticker="WEAK",
            line_source="incumbent",
            reward_risk_ratio=1.0,
            conviction_weight=2.0,
        )
        strong = LineCandidate(
            ticker="STRONG",
            line_source="proposal",
            reward_risk_ratio=2.5,
            conviction_weight=3.0,
        )
        self.assertGreater(effective_score(strong, 0.2), effective_score(weak, 0.2))


class TestUniverseMerge(unittest.TestCase):
    def test_merge_overlapping_ticker(self):
        holdings = [
            {
                "page_id": "h1",
                "ticker": "NVDA",
                "holding_type": "holding",
                "market_value": 100000,
                "quantity": 100,
                "market": "US",
                "asset_class": "equity",
                "trade_type": "long",
                "entry_price": 200,
                "stop_price": 180,
            }
        ]
        proposals = [
            {
                "page_id": "p1",
                "ticker": "NVDA",
                "market": "US",
                "asset_class": "equity",
                "conviction": "high",
                "entry_price": 205,
                "stop_price": 184,
                "target_price": 250,
                "reward_risk_ratio": 2.5,
            }
        ]
        positions = [{"ticker": "NVDA", "risk_at_stop": 2000}]
        universe = build_universe(holdings, proposals, positions, {"high": 3, "medium": 2, "low": 1})
        self.assertEqual(len(universe), 1)
        self.assertEqual(universe[0].line_source, "merged")
        self.assertEqual(universe[0].source_holding_id, "h1")
        self.assertEqual(universe[0].source_proposal_id, "p1")


class TestRebalance(unittest.TestCase):
    def test_trim_action(self):
        line = LineCandidate(
            ticker="A",
            line_source="incumbent",
            initial_market_value=100,
            initial_quantity=10,
            target_market_value=80,
            target_quantity=8,
            included=True,
        )
        self.assertEqual(action_type(line), "trim")

    def test_add_action(self):
        line = LineCandidate(
            ticker="B",
            line_source="proposal",
            initial_market_value=0,
            initial_quantity=0,
            target_market_value=5000,
            target_quantity=50,
            included=True,
        )
        self.assertEqual(action_type(line), "add")


class TestCurrencyAlignment(unittest.TestCase):
    def test_sync_line_from_risk_converts_usd_risk_to_base(self):
        line = LineCandidate(
            ticker="TSM",
            line_source="proposal",
            market="US",
            currency="USD",
            entry_price=100.0,
            stop_price=90.0,
            reference_price=100.0,
            trade_type="long",
            target_risk_at_stop=10_000.0,
        )
        fx = {"base_currency": "HKD", "rates": {"HKD": 1.0, "USD": 7.8}}
        sync_line_from_risk(line, 1_000_000.0, fx, "HKD")
        risk_local = 10_000.0 / 7.8
        expected_qty = risk_local / 10.0
        expected_mv_base = expected_qty * 100.0 * 7.8
        self.assertAlmostEqual(line.target_quantity, expected_qty)
        self.assertAlmostEqual(line.target_market_value, expected_mv_base)

    def test_target_holdings_risk_matches_compute_metrics(self):
        from metrics import compute_metrics

        nav = 1_000_000.0
        line = LineCandidate(
            ticker="TSM",
            line_source="proposal",
            market="US",
            currency="USD",
            entry_price=100.0,
            stop_price=90.0,
            reference_price=100.0,
            trade_type="long",
            included=True,
            target_risk_at_stop=10_000.0,
        )
        fx = {
            "base_currency": "HKD",
            "rates": {"HKD": 1.0, "USD": 7.8},
            "sources": {"HKD": "identity", "USD": "test"},
        }
        sync_line_from_risk(line, nav, fx, "HKD")
        metrics = compute_metrics(
            {"nav": nav, "base_currency": "HKD"},
            [
                {
                    "ticker": "TSM",
                    "holding_type": "holding",
                    "market": "US",
                    "currency": "USD",
                    "asset_class": "equity",
                    "trade_type": "long",
                    "quantity": line.target_quantity,
                    "market_value": line.target_market_value,
                    "entry_price": 100.0,
                    "stop_price": 90.0,
                }
            ],
            fx=fx,
        )["positions"][0]
        rows = build_target_holdings([line], 0.0, nav, positions=[metrics])
        self.assertAlmostEqual(rows[0]["risk_at_stop"], metrics["risk_at_stop"])
        self.assertAlmostEqual(rows[0]["risk_at_stop_pct"], metrics["risk_at_stop_pct"])
        self.assertAlmostEqual(rows[0]["target_weight_pct"], metrics["weight_pct"])


class TestRepairHelpers(unittest.TestCase):
    def test_trim_risk_step(self):
        line = LineCandidate(
            ticker="X",
            line_source="incumbent",
            entry_price=100,
            stop_price=90,
            reference_price=100,
            trade_type="long",
            target_risk_at_stop=32_000,
            target_quantity=3200,
            target_market_value=320_000,
            included=True,
        )
        from planner import _trim_line_risk

        _trim_line_risk(line, 0.1, 1_000_000.0)
        self.assertAlmostEqual(line.target_risk_at_stop, 31_000.0)
        self.assertAlmostEqual(line.target_market_value, 310_000.0)

    def test_weight_cap_trim(self):
        line = LineCandidate(
            ticker="X",
            line_source="incumbent",
            target_market_value=500_000,
            target_quantity=5000,
            target_risk_at_stop=50_000,
            included=True,
        )
        from planner import _trim_line_to_weight_cap

        _trim_line_to_weight_cap(line, 1_000_000.0, 40.0)
        self.assertAlmostEqual(line.target_market_value, 400_000.0)
        self.assertAlmostEqual(line.target_risk_at_stop, 40_000.0)


class TestTurnover(unittest.TestCase):
    def test_turnover_pct(self):
        lines = [
            LineCandidate(
                ticker="A",
                line_source="incumbent",
                initial_market_value=100,
                target_market_value=80,
                included=True,
            )
        ]
        self.assertAlmostEqual(compute_turnover_pct(lines, 1000), 2.0)


class TestPlannerIntegration(unittest.TestCase):
    def _sample_policy(self, **overrides) -> dict:
        policy = {
            "base_currency": "HKD",
            "hard_limits": {
                "max_holdings_count": 10,
                "min_cash_pct": 3,
                "max_cash_pct": 50,
                "max_single_holding_pct": 55,
                "max_portfolio_heat_pct": 6,
                "max_risk_per_proposal_pct": 2,
                "max_turnover_pct": 50,
                "min_reward_risk_ratio": 2,
            },
            "market_limits": {
                "HK": {"max_exposure_pct": 50},
                "JP": {"max_exposure_pct": 30},
                "US": {"max_exposure_pct": 70},
                "OTHER": {"max_exposure_pct": 15},
            },
            "asset_class_limits": {"equity": {"max_exposure_pct": 95}},
            "soft_preferences": {
                "objective": "maximize_conviction_weighted_reward_risk",
                "conviction_weights": {"high": 3, "medium": 2, "low": 1},
                "existing_position_bias": 0.2,
            },
            "regime_overrides": {"drawdown_from_peak": {}},
            "planner": {"sizing_method": "risk_at_stop"},
        }
        policy.update(overrides)
        return policy

    def test_infeasible_input_trims_to_feasible(self):
        nav = 1_000_000.0
        lines = [
            LineCandidate(
                ticker="LOW",
                line_source="incumbent",
                market="US",
                asset_class="equity",
                entry_price=100,
                stop_price=90,
                reference_price=100,
                reward_risk_ratio=1.0,
                conviction_weight=1,
                initial_market_value=200_000,
                initial_quantity=2000,
                initial_risk_at_stop=20_000,
                target_market_value=200_000,
                target_quantity=2000,
                target_risk_at_stop=20_000,
                included=True,
            ),
            LineCandidate(
                ticker="HIGH",
                line_source="incumbent",
                market="US",
                asset_class="equity",
                entry_price=100,
                stop_price=90,
                reference_price=100,
                reward_risk_ratio=3.0,
                conviction_weight=3,
                initial_market_value=750_000,
                initial_quantity=7500,
                initial_risk_at_stop=75_000,
                target_market_value=750_000,
                target_quantity=7500,
                target_risk_at_stop=75_000,
                included=True,
            ),
        ]
        input_metrics = {
            "holdings_count": 2,
            "cash_pct": 5.0,
            "portfolio_heat_pct": 9.5,
            "max_single_holding_pct": 75,
            "market_exposure_pct": {"US": 95, "HK": 0, "JP": 0, "OTHER": 0},
            "asset_class_exposure_pct": {"equity": 95, "etf": 0, "crypto": 0},
        }
        guardrail_input = {"summary": {"pass": False}, "regime": {"drawdown_pct": None}}
        from metrics import compute_metrics

        policy = self._sample_policy(
            soft_preferences={
                "objective": "minimize_turnover",
                "conviction_weights": {"high": 3, "medium": 2, "low": 1},
                "existing_position_bias": 0.2,
            }
        )
        plan = run_planner(
            lines,
            nav,
            50_000,
            policy,
            input_metrics,
            guardrail_input,
            compute_metrics,
            None,
        )
        self.assertEqual(plan.status, "completed")
        target_holdings = [
            {
                "ticker": line.ticker,
                "holding_type": "holding",
                "market": line.market,
                "asset_class": line.asset_class,
                "trade_type": "long",
                "quantity": line.target_quantity,
                "market_value": line.target_market_value,
                "entry_price": line.entry_price,
                "stop_price": line.stop_price,
            }
            for line in plan.lines
            if line.included and line.target_market_value > 0
        ]
        target_holdings.append(
            {
                "ticker": "CASH",
                "holding_type": "cash",
                "market": "OTHER",
                "asset_class": "cash",
                "trade_type": "n/a",
                "quantity": plan.target_cash_mv,
                "market_value": plan.target_cash_mv,
                "entry_price": None,
                "stop_price": None,
            }
        )
        metrics = compute_metrics({"nav": nav}, target_holdings)["metrics"]
        self.assertLessEqual(metrics["portfolio_heat_pct"], 6.0)

    def test_proposal_replaces_weak_incumbent_when_input_infeasible(self):
        nav = 1_000_000.0
        lines = [
            LineCandidate(
                ticker="WEAK",
                line_source="incumbent",
                market="HK",
                asset_class="equity",
                currency="HKD",
                entry_price=100,
                stop_price=90,
                reference_price=100,
                reward_risk_ratio=1.0,
                conviction_weight=2,
                initial_market_value=200_000,
                initial_quantity=2000,
                initial_risk_at_stop=20_000,
                target_market_value=200_000,
                target_quantity=2000,
                target_risk_at_stop=20_000,
                included=True,
            ),
            LineCandidate(
                ticker="STRONG",
                line_source="incumbent",
                market="US",
                asset_class="equity",
                currency="USD",
                entry_price=100,
                stop_price=90,
                reference_price=100,
                reward_risk_ratio=3.0,
                conviction_weight=3,
                initial_market_value=700_000,
                initial_quantity=7000,
                initial_risk_at_stop=70_000,
                target_market_value=700_000,
                target_quantity=7000,
                target_risk_at_stop=70_000,
                included=True,
            ),
            LineCandidate(
                ticker="TSM",
                line_source="proposal",
                market="US",
                asset_class="equity",
                currency="USD",
                entry_price=400,
                stop_price=380,
                reference_price=400,
                reward_risk_ratio=2.5,
                conviction_weight=3,
                initial_market_value=0,
                initial_quantity=0,
                initial_risk_at_stop=0,
                target_market_value=0,
                target_quantity=0,
                target_risk_at_stop=0,
                included=False,
            ),
        ]
        input_metrics = {
            "holdings_count": 2,
            "cash_pct": 10.0,
            "portfolio_heat_pct": 9.0,
            "max_single_holding_pct": 70,
            "market_exposure_pct": {"US": 70, "HK": 20, "JP": 0, "OTHER": 0},
            "asset_class_exposure_pct": {"equity": 90, "etf": 0, "crypto": 0},
        }
        guardrail_input = {"summary": {"pass": False}, "regime": {"drawdown_pct": None}}
        from metrics import compute_metrics

        plan = run_planner(
            lines,
            nav,
            100_000,
            self._sample_policy(),
            input_metrics,
            guardrail_input,
            compute_metrics,
            None,
        )
        self.assertEqual(plan.status, "completed")
        by_ticker = {line.ticker: line for line in plan.lines}
        self.assertLess(by_ticker["WEAK"].target_market_value, 200_000)
        self.assertGreater(by_ticker["TSM"].target_market_value, 0)

    def test_swap_adds_proposal_when_input_feasible(self):
        nav = 1_000_000.0
        lines = [
            LineCandidate(
                ticker="WEAK",
                line_source="incumbent",
                market="HK",
                asset_class="equity",
                entry_price=100,
                stop_price=90,
                reference_price=100,
                reward_risk_ratio=1.0,
                conviction_weight=1,
                initial_market_value=60_000,
                initial_quantity=600,
                initial_risk_at_stop=6_000,
                target_market_value=60_000,
                target_quantity=600,
                target_risk_at_stop=6_000,
                included=True,
            ),
            LineCandidate(
                ticker="CORE",
                line_source="incumbent",
                market="US",
                asset_class="equity",
                entry_price=100,
                stop_price=90,
                reference_price=100,
                reward_risk_ratio=2.0,
                conviction_weight=3,
                initial_market_value=540_000,
                initial_quantity=5400,
                initial_risk_at_stop=54_000,
                target_market_value=540_000,
                target_quantity=5400,
                target_risk_at_stop=54_000,
                included=True,
            ),
            LineCandidate(
                ticker="NEW",
                line_source="proposal",
                market="US",
                asset_class="equity",
                entry_price=200,
                stop_price=190,
                reference_price=200,
                reward_risk_ratio=2.5,
                conviction_weight=3,
                initial_market_value=0,
                initial_quantity=0,
                initial_risk_at_stop=0,
                target_market_value=0,
                target_quantity=0,
                target_risk_at_stop=0,
                included=False,
            ),
        ]
        input_metrics = {
            "holdings_count": 2,
            "cash_pct": 10.0,
            "portfolio_heat_pct": 5.0,
            "max_single_holding_pct": 80,
            "market_exposure_pct": {"US": 80, "HK": 10, "JP": 0, "OTHER": 0},
            "asset_class_exposure_pct": {"equity": 90, "etf": 0, "crypto": 0},
        }
        guardrail_input = {"summary": {"pass": True}, "regime": {"drawdown_pct": None}}
        from metrics import compute_metrics

        plan = run_planner(
            lines,
            nav,
            400_000,
            self._sample_policy(
                hard_limits={
                    "max_holdings_count": 10,
                    "min_cash_pct": 3,
                    "max_cash_pct": 50,
                    "max_single_holding_pct": 85,
                    "max_portfolio_heat_pct": 6,
                    "max_risk_per_proposal_pct": 2,
                    "max_turnover_pct": 50,
                    "min_reward_risk_ratio": 2,
                }
            ),
            input_metrics,
            guardrail_input,
            compute_metrics,
            None,
        )
        self.assertEqual(plan.status, "completed")
        by_ticker = {line.ticker: line for line in plan.lines}
        self.assertGreater(by_ticker["NEW"].target_market_value, 0)
        self.assertEqual(by_ticker["WEAK"].target_market_value, 0)


if __name__ == "__main__":
    unittest.main()
