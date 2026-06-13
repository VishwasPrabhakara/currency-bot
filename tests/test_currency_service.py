import urllib.error

import pytest

from currency_agent import mcp_server


def test_get_exchange_rate_normalizes_codes(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "_fetch_json",
        lambda path, params=None: {
            "date": "2026-06-13",
            "base": "USD",
            "quote": "INR",
            "rate": 95.36,
        },
    )

    result = mcp_server.get_exchange_rate(" usd ", "inr")

    assert result["status"] == "success"
    assert result["base"] == "USD"
    assert result["target"] == "INR"
    assert result["rate"] == 95.36
    assert result["date"] == "2026-06-13"


def test_same_currency_rate_skips_network(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "_fetch_json",
        lambda *args, **kwargs: pytest.fail("network should not be called"),
    )

    result = mcp_server.get_exchange_rate("EUR", "EUR")

    assert result["rate"] == 1.0
    assert result["source"] == "identity conversion"


def test_conversion_uses_returned_rate(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "_fetch_json",
        lambda path, params=None: {"date": "2026-06-13", "rate": 2.5},
    )

    result = mcp_server.convert_currency(12, "USD", "EUR")

    assert result["converted_amount"] == 30.0
    assert result["rate"] == 2.5


@pytest.mark.parametrize("amount", [-1, float("nan"), float("inf")])
def test_conversion_rejects_invalid_amounts(amount):
    result = mcp_server.convert_currency(amount, "USD", "EUR")

    assert result["status"] == "error"
    assert "amount" in result["message"]


@pytest.mark.parametrize("code", ["US", "US12", "US$", ""])
def test_currency_codes_must_be_three_letters(code):
    result = mcp_server.get_exchange_rate(code, "EUR")

    assert result["status"] == "error"
    assert "three-letter" in result["message"]


def test_historical_rate_rejects_invalid_date():
    result = mcp_server.get_historical_rate("13-06-2024", "USD", "EUR")

    assert result["status"] == "error"
    assert "YYYY-MM-DD" in result["message"]


def test_timeseries_rejects_reversed_dates():
    result = mcp_server.get_rate_timeseries(
        "USD", "EUR", "2024-02-01", "2024-01-01"
    )

    assert result["status"] == "error"
    assert "on or before" in result["message"]


def test_timeseries_rejects_ranges_over_one_year():
    result = mcp_server.get_rate_timeseries(
        "USD", "EUR", "2023-01-01", "2024-02-01"
    )

    assert result["status"] == "error"
    assert "366 days" in result["message"]


def test_timeseries_computes_summary(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "_fetch_json",
        lambda path, params=None: [
            {"date": "2024-01-01", "base": "USD", "quote": "EUR", "rate": 0.8},
            {"date": "2024-01-02", "base": "USD", "quote": "EUR", "rate": 0.9},
            {"date": "2024-01-03", "base": "USD", "quote": "EUR", "rate": 1.0},
        ],
    )

    result = mcp_server.get_rate_timeseries(
        "USD", "EUR", "2024-01-01", "2024-01-03"
    )

    assert result["status"] == "success"
    assert result["data_points"] == 3
    assert result["highest"] == 1.0
    assert result["lowest"] == 0.8
    assert result["average"] == 0.9
    assert result["percentage_change"] == 25.0
    assert result["trend"] == "strengthened"


def test_supported_currencies_are_reduced_to_public_fields(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "_fetch_json",
        lambda path, params=None: [
            {"iso_code": "USD", "name": "United States Dollar", "symbol": "$"},
            {"iso_code": "EUR", "name": "Euro", "symbol": "€"},
        ],
    )

    result = mcp_server.get_supported_currencies()

    assert result["count"] == 2
    assert result["currencies"][0] == {
        "code": "USD",
        "name": "United States Dollar",
        "symbol": "$",
    }


def test_upstream_404_returns_safe_error(monkeypatch):
    error = urllib.error.HTTPError(
        url="https://example.test",
        code=404,
        msg="Not found",
        hdrs=None,
        fp=None,
    )
    monkeypatch.setattr(
        mcp_server.urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    result = mcp_server.get_exchange_rate("USD", "ZZZ")

    assert result == {
        "status": "error",
        "message": "No reference-rate data was found for that request",
    }
