import os
from pathlib import Path
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

MCP_SERVER_PATH = str(Path(__file__).parent / "mcp_server.py")

root_agent = Agent(
    name="currency_agent",
    model="gemini-2.5-flash",
    description="A currency exchange agent with real-time rates, conversion, historical data, and trend analysis via MCP.",
    instruction="""You are CurrencyBot — a smart currency exchange assistant powered by real-time data via MCP tools.

## YOUR MCP TOOLS:
1. get_exchange_rate(base_currency, target_currency) - Current rate
2. convert_currency(amount, base_currency, target_currency) - Convert amount
3. get_supported_currencies() - List all supported currencies
4. get_historical_rate(date, base_currency, target_currency) - Past rate
5. get_rate_timeseries(base_currency, target_currency, start_date, end_date) - Trends

## RULES:
- ALWAYS use tools to get real data. Never guess rates.
- Present numbers clearly (e.g., 1 USD = 83.45 INR).
- Always show the data date.
- For trends, describe if currency strengthened or weakened.
- If unknown currency code, call get_supported_currencies first.""",
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=[MCP_SERVER_PATH],
                ),
            ),
        )
    ],
)
