import json
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("currency_server")

@mcp.tool()
def get_exchange_rate(base_currency: str, target_currency: str) -> str:
    """Get the current exchange rate between two currencies.
    Args:
        base_currency: The source currency code (e.g., USD, EUR, INR, GBP, JPY).
        target_currency: The target currency code (e.g., USD, EUR, INR, GBP, JPY).
    """
    try:
        base = base_currency.upper().strip()
        target = target_currency.upper().strip()
        url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            rate = data.get("rates", {}).get(target)
            return json.dumps({"status": "success", "base": base, "target": target, "rate": rate, "date": data.get("date", "unknown"), "description": f"1 {base} = {rate} {target}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def convert_currency(amount: float, base_currency: str, target_currency: str) -> str:
    """Convert a specific amount from one currency to another using live rates.
    Args:
        amount: The amount of money to convert.
        base_currency: The source currency code.
        target_currency: The target currency code.
    """
    try:
        base = base_currency.upper().strip()
        target = target_currency.upper().strip()
        url = f"https://api.frankfurter.app/latest?amount={amount}&from={base}&to={target}"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            converted = data.get("rates", {}).get(target)
            return json.dumps({"status": "success", "original_amount": amount, "base": base, "target": target, "converted_amount": converted, "date": data.get("date", "unknown"), "description": f"{amount} {base} = {converted} {target}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def get_supported_currencies() -> str:
    """Get the full list of supported currency codes and their names."""
    try:
        url = "https://api.frankfurter.app/currencies"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return json.dumps({"status": "success", "currencies": data, "count": len(data)})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def get_historical_rate(date: str, base_currency: str, target_currency: str) -> str:
    """Get the exchange rate for a specific historical date.
    Args:
        date: The date in YYYY-MM-DD format (e.g., 2024-01-15).
        base_currency: The source currency code.
        target_currency: The target currency code.
    """
    try:
        base = base_currency.upper().strip()
        target = target_currency.upper().strip()
        url = f"https://api.frankfurter.app/{date}?from={base}&to={target}"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            rate = data.get("rates", {}).get(target)
            return json.dumps({"status": "success", "base": base, "target": target, "rate": rate, "date": data.get("date", date), "description": f"On {data.get('date', date)}: 1 {base} = {rate} {target}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def get_rate_timeseries(base_currency: str, target_currency: str, start_date: str, end_date: str) -> str:
    """Get exchange rate history over a date range to see trends.
    Args:
        base_currency: The source currency code.
        target_currency: The target currency code.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
    """
    try:
        base = base_currency.upper().strip()
        target = target_currency.upper().strip()
        url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={target}"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            rates = {}
            for d, r in data.get("rates", {}).items():
                rates[d] = r.get(target)
            vals = list(rates.values())
            return json.dumps({"status": "success", "base": base, "target": target, "start_date": data.get("start_date", start_date), "end_date": data.get("end_date", end_date), "rates": rates, "data_points": len(rates), "highest": max(vals) if vals else None, "lowest": min(vals) if vals else None, "average": round(sum(vals)/len(vals), 4) if vals else None})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    mcp.run(transport="stdio")
