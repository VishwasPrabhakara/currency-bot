import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MCP_SERVER_PATH = str(Path(__file__).parent / "mcp_server.py")

root_agent = Agent(
    name="currency_agent",
    model="gemini-2.5-flash",
    description="A currency reference-rate agent with conversion, historical data, and trend analysis via MCP.",
    instruction="""You are CurrencyBot, a currency reference-rate assistant powered by MCP tools.

## YOUR MCP TOOLS:
1. get_exchange_rate(base_currency, target_currency) - Current rate
2. convert_currency(amount, base_currency, target_currency) - Convert amount
3. get_supported_currencies() - List all supported currencies
4. get_historical_rate(requested_date, base_currency, target_currency) - Past rate
5. get_rate_timeseries(base_currency, target_currency, start_date, end_date) - Trends

## RULES:
- ALWAYS use tools to get reference-rate data. Never guess rates.
- Present numbers clearly (e.g., 1 USD = 83.45 INR).
- Always show the data date.
- Explain that rates are daily reference data, not live tradable quotes.
- For trends, describe the change in target currency per unit of base currency.
- If unknown currency code, call get_supported_currencies first.""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[MCP_SERVER_PATH],
                ),
            ),
        )
    ],
)
