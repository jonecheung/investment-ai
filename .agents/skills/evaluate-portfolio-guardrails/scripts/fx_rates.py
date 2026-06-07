"""Fetch FX rates from FXRatesAPI for currency-adjusted risk-at-stop."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

FXRATESAPI_URL = "https://api.fxratesapi.com/latest"
FXRATESAPI_DOCS = "https://fxratesapi.com/docs/endpoints/latest-exchange-rates"

MARKET_DEFAULT_CURRENCY: dict[str, str] = {
    "HK": "HKD",
    "US": "USD",
    "JP": "JPY",
}


class FxError(Exception):
    pass


def _normalize_currency(code: str | None) -> str | None:
    if not code:
        return None
    normalized = code.strip().upper()
    if normalized in ("CNH", "RMB"):
        return "CNY"
    return normalized


def resolve_holding_currency(holding: dict[str, Any]) -> str | None:
    currency = _normalize_currency(holding.get("currency"))
    if currency:
        return currency
    market = (holding.get("market") or "").upper()
    return MARKET_DEFAULT_CURRENCY.get(market)


def load_fxratesapi_key() -> str | None:
    key = os.environ.get("FXRATESAPI_API_KEY")
    if key:
        return key.strip()

    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        repo_env = Path(__file__).resolve().parents[4] / ".env"
        if repo_env.is_file():
            env_path = repo_env

    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("FXRATESAPI_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    os.environ["FXRATESAPI_API_KEY"] = value
                    return value

    return None


def _fetch_fxratesapi(base_currency: str, currencies: set[str]) -> dict[str, Any]:
    params: dict[str, str] = {
        "base": base_currency,
        "currencies": ",".join(sorted(currencies)),
    }
    api_key = load_fxratesapi_key()
    if api_key:
        params["api_key"] = api_key

    query = urllib.parse.urlencode(params)
    url = f"{FXRATESAPI_URL}?{query}"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "evaluate-portfolio-guardrails/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise FxError(f"Failed to fetch FXRatesAPI latest rates: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FxError("FXRatesAPI returned invalid JSON") from exc

    if not payload.get("success"):
        message = payload.get("error") or payload.get("message") or "unknown error"
        raise FxError(f"FXRatesAPI request failed: {message}")

    api_rates = payload.get("rates")
    if not isinstance(api_rates, dict):
        raise FxError("FXRatesAPI response missing rates object")

    return {
        "url": url,
        "date": payload.get("date"),
        "timestamp": payload.get("timestamp"),
        "rates": api_rates,
    }


def build_fx_rates(
    currencies: set[str],
    base_currency: str,
) -> dict[str, Any]:
    base = _normalize_currency(base_currency) or "HKD"
    needed = {_normalize_currency(code) for code in currencies if code}
    needed.discard(base)
    needed.discard(None)  # type: ignore[arg-type]

    rates: dict[str, float] = {base: 1.0}
    sources: dict[str, str] = {base: "identity"}

    if not needed:
        return {
            "base_currency": base,
            "provider": "fxratesapi.com",
            "rates": rates,
            "sources": sources,
        }

    response = _fetch_fxratesapi(base, needed)
    request_url = response["url"]

    for currency in sorted(needed):
        quote = response["rates"].get(currency)
        if quote is None or float(quote) <= 0:
            raise FxError(
                f"FXRatesAPI did not return a valid rate for {currency} with base {base}"
            )
        # API returns units of `currency` per 1 `base`.
        # Convert local-currency amount to base: amount_base = amount_local / quote.
        rates[currency] = 1.0 / float(quote)
        sources[currency] = request_url

    result: dict[str, Any] = {
        "base_currency": base,
        "provider": "fxratesapi.com",
        "rates": rates,
        "sources": sources,
    }
    if response.get("date"):
        result["as_of"] = response["date"]
    return result


def convert_to_base(
    amount: float,
    from_currency: str | None,
    fx: dict[str, Any],
) -> tuple[float, str | None]:
    base = fx["base_currency"]
    currency = _normalize_currency(from_currency) or base
    rate = fx["rates"].get(currency)
    if rate is None:
        return amount, f"missing FX rate for {currency}->{base}"
    return amount * rate, None
