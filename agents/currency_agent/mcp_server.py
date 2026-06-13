from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

from mcp.server.fastmcp import FastMCP

API_BASE_URL = "https://api.frankfurter.dev/v2"
MAX_TIMESERIES_DAYS = 366
REQUEST_TIMEOUT_SECONDS = 10
USER_AGENT = "CurrencyBot/2.0"

mcp = FastMCP("currency_server")


class CurrencyServiceError(RuntimeError):
    """A safe, user-facing error raised by the currency service."""


def _currency_code(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise CurrencyServiceError(f"{field_name} must be a string")
    code = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", code):
        raise CurrencyServiceError(
            f"{field_name} must be a three-letter currency code"
        )
    return code


def _iso_date(value: str, field_name: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise CurrencyServiceError(
            f"{field_name} must use YYYY-MM-DD format"
        ) from exc
    if parsed > date.today():
        raise CurrencyServiceError(f"{field_name} cannot be in the future")
    return parsed


def _amount(value: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CurrencyServiceError("amount must be a number") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise CurrencyServiceError("amount must be finite and non-negative")
    return parsed


def _fetch_json(path: str, params: dict[str, str] | None = None) -> Any:
    query = urllib.parse.urlencode(params or {})
    url = f"{API_BASE_URL}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise CurrencyServiceError(
                "No reference-rate data was found for that request"
            ) from exc
        raise CurrencyServiceError(
            f"The exchange-rate provider returned HTTP {exc.code}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CurrencyServiceError(
            "The exchange-rate provider is temporarily unavailable"
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CurrencyServiceError(
            "The exchange-rate provider returned an invalid response"
        ) from exc


def _error_result(exc: CurrencyServiceError) -> dict[str, str]:
    return {"status": "error", "message": str(exc)}


def _rate_result(
    base: str,
    target: str,
    requested_date: date | None = None,
) -> dict[str, Any]:
    if base == target:
        resolved_date = requested_date or date.today()
        return {
            "status": "success",
            "base": base,
            "target": target,
            "rate": 1.0,
            "date": resolved_date.isoformat(),
            "description": f"1 {base} = 1 {target}",
            "source": "identity conversion",
        }

    params = {"date": requested_date.isoformat()} if requested_date else None
    data = _fetch_json(f"rate/{base}/{target}", params)
    rate = data.get("rate") if isinstance(data, dict) else None
    if not isinstance(rate, (int, float)) or not math.isfinite(rate):
        raise CurrencyServiceError(
            "No valid reference rate was returned for that currency pair"
        )
    return {
        "status": "success",
        "base": base,
        "target": target,
        "rate": rate,
        "date": data.get("date"),
        "description": f"1 {base} = {rate} {target}",
        "source": "Frankfurter v2 reference rates",
    }


@mcp.tool()
def get_exchange_rate(base_currency: str, target_currency: str) -> dict[str, Any]:
    """Get the latest daily reference rate between two ISO currency codes."""
    try:
        base = _currency_code(base_currency, "base_currency")
        target = _currency_code(target_currency, "target_currency")
        return _rate_result(base, target)
    except CurrencyServiceError as exc:
        return _error_result(exc)


@mcp.tool()
def convert_currency(
    amount: float,
    base_currency: str,
    target_currency: str,
) -> dict[str, Any]:
    """Convert an amount using the latest available daily reference rate."""
    try:
        normalized_amount = _amount(amount)
        base = _currency_code(base_currency, "base_currency")
        target = _currency_code(target_currency, "target_currency")
        rate_result = _rate_result(base, target)
        converted = round(normalized_amount * rate_result["rate"], 6)
        return {
            "status": "success",
            "original_amount": normalized_amount,
            "base": base,
            "target": target,
            "rate": rate_result["rate"],
            "converted_amount": converted,
            "date": rate_result["date"],
            "description": f"{normalized_amount} {base} = {converted} {target}",
            "source": rate_result["source"],
        }
    except CurrencyServiceError as exc:
        return _error_result(exc)


@mcp.tool()
def get_supported_currencies() -> dict[str, Any]:
    """List currencies available from the Frankfurter v2 API."""
    try:
        data = _fetch_json("currencies")
        if not isinstance(data, list):
            raise CurrencyServiceError(
                "The exchange-rate provider returned an invalid currency list"
            )
        currencies = [
            {
                "code": item.get("iso_code"),
                "name": item.get("name"),
                "symbol": item.get("symbol"),
            }
            for item in data
            if isinstance(item, dict) and item.get("iso_code")
        ]
        return {
            "status": "success",
            "currencies": currencies,
            "count": len(currencies),
            "source": "Frankfurter v2",
        }
    except CurrencyServiceError as exc:
        return _error_result(exc)


@mcp.tool()
def get_historical_rate(
    requested_date: str,
    base_currency: str,
    target_currency: str,
) -> dict[str, Any]:
    """Get a daily reference rate for a past date in YYYY-MM-DD format."""
    try:
        parsed_date = _iso_date(requested_date, "requested_date")
        base = _currency_code(base_currency, "base_currency")
        target = _currency_code(target_currency, "target_currency")
        result = _rate_result(base, target, parsed_date)
        result["description"] = (
            f"On {result['date']}: 1 {base} = {result['rate']} {target}"
        )
        return result
    except CurrencyServiceError as exc:
        return _error_result(exc)


@mcp.tool()
def get_rate_timeseries(
    base_currency: str,
    target_currency: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Get up to one year of daily reference rates for a currency pair."""
    try:
        base = _currency_code(base_currency, "base_currency")
        target = _currency_code(target_currency, "target_currency")
        start = _iso_date(start_date, "start_date")
        end = _iso_date(end_date, "end_date")
        if start > end:
            raise CurrencyServiceError("start_date must be on or before end_date")
        if (end - start).days > MAX_TIMESERIES_DAYS:
            raise CurrencyServiceError(
                f"date range cannot exceed {MAX_TIMESERIES_DAYS} days"
            )
        if base == target:
            rates = {start.isoformat(): 1.0}
            if end != start:
                rates[end.isoformat()] = 1.0
            return {
                "status": "success",
                "base": base,
                "target": target,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "rates": rates,
                "data_points": len(rates),
                "highest": 1.0,
                "lowest": 1.0,
                "average": 1.0,
                "percentage_change": 0.0,
                "trend": "stable",
                "source": "identity conversion",
            }

        data = _fetch_json(
            "rates",
            {
                "base": base,
                "quotes": target,
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
        )
        if not isinstance(data, list):
            raise CurrencyServiceError(
                "The exchange-rate provider returned an invalid time series"
            )
        rates = {
            item["date"]: float(item["rate"])
            for item in data
            if isinstance(item, dict)
            and item.get("date")
            and isinstance(item.get("rate"), (int, float))
        }
        if not rates:
            raise CurrencyServiceError(
                "No reference-rate data was found in that date range"
            )

        values = list(rates.values())
        percentage_change = round(
            (values[-1] - values[0]) / values[0] * 100, 4
        )
        trend = (
            "strengthened"
            if percentage_change > 0
            else "weakened"
            if percentage_change < 0
            else "stable"
        )
        return {
            "status": "success",
            "base": base,
            "target": target,
            "start_date": next(iter(rates)),
            "end_date": next(reversed(rates)),
            "rates": rates,
            "data_points": len(rates),
            "highest": max(values),
            "lowest": min(values),
            "average": round(sum(values) / len(values), 6),
            "percentage_change": percentage_change,
            "trend": trend,
            "source": "Frankfurter v2 reference rates",
        }
    except CurrencyServiceError as exc:
        return _error_result(exc)


if __name__ == "__main__":
    mcp.run(transport="stdio")
