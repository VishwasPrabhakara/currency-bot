# CurrencyBot

> A Google ADK agent that uses a local MCP server to retrieve validated daily
> currency reference rates from Frankfurter.

[Live demo](https://currency-agent-381066349460.us-central1.run.app/) |
[Architecture](architecture.svg) |
[Security](SECURITY.md)

CurrencyBot translates natural-language currency questions into MCP tool calls.
Gemini handles intent and response formatting, while a separate stdio MCP
process validates inputs, calls the Frankfurter v2 API, and returns structured
rate data.

Built for the **Google Cloud Gen AI Academy APAC Edition, Track 1**.

## What It Demonstrates

- Google ADK agent orchestration with an MCP toolset
- Process-isolated tools over MCP stdio transport
- Validated external API access with bounded timeouts
- Current, historical, conversion, currency-list, and time-series tools
- Deterministic trend statistics over returned reference rates
- Non-root Docker deployment to Google Cloud Run
- Offline unit tests and GitHub Actions CI

## Architecture

![CurrencyBot architecture](architecture.svg)

```text
User question
    |
    v
ADK web interface
    |
    v
Gemini 2.5 Flash agent
    |
    v
MCPToolset (stdio)
    |
    v
currency MCP server
    |
    +--> validation and date-range limits
    +--> Frankfurter v2 API
    `--> structured rate or error response
```

## MCP Tools

| Tool | Purpose |
|---|---|
| `get_exchange_rate` | Latest available daily reference rate |
| `convert_currency` | Amount conversion using the latest reference rate |
| `get_supported_currencies` | Currency codes, names, and symbols |
| `get_historical_rate` | Reference rate for a past date |
| `get_rate_timeseries` | Up to 366 days of rates with summary statistics |

The time-series response includes the first and last available dates, number of
observations, minimum, maximum, average, percentage change, and direction.

## Example Prompts

```text
What is the latest available USD to INR reference rate?

Convert 250 EUR to JPY.

What was the USD to GBP rate on 2024-01-15?

Show the EUR to INR trend from 2024-01-01 to 2024-06-30.

Which currencies are supported?
```

## Data Semantics

Frankfurter v2 aggregates daily exchange-rate data from central banks and other
official providers. These values are reference rates:

- They are not live, tick-level, bank, card, or broker quotes.
- Weekends and holidays may resolve to the latest available observation.
- Currency conversion results exclude spreads, commissions, taxes, and fees.
- Trend summaries describe historical movement and are not forecasts.

Do not use CurrencyBot as financial advice or as the sole source for executing
a transaction.

## Run Locally

Requirements:

- Python 3.11+
- Gemini API credentials from
  [Google AI Studio](https://aistudio.google.com/apikey)

```powershell
git clone https://github.com/VishwasPrabhakara/currency-bot.git
cd currency-bot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item .env.example .env
# Add GOOGLE_API_KEY to .env

adk web --port 8000 --host 127.0.0.1 agents
```

Open `http://127.0.0.1:8000`. The ADK web UI is a development and demonstration
surface, not an authenticated production frontend.

## Tests

The automated tests mock network responses and do not call Gemini or
Frankfurter:

```powershell
pip install -r requirements-dev.txt
pytest
```

They cover validation, conversion math, date bounds, same-currency requests,
time-series statistics, safe upstream errors, agent registration, and MCP
subprocess configuration.

The suite does not measure Gemini's final-answer quality or tool-selection
accuracy. No model evaluation scores are claimed.

## Docker

```powershell
docker build -t currency-bot .
docker run --rm -p 8080:8080 --env-file .env currency-bot
```

The image does not copy `.env`, runs as a non-root user, and respects Cloud
Run's `PORT` variable.

## Cloud Run

Deploy the agent with ADK:

```powershell
adk deploy cloud_run `
  --project=YOUR_PROJECT_ID `
  --region=us-central1 `
  --service_name=currency-agent `
  --with_ui `
  agents/currency_agent
```

Configure `GOOGLE_API_KEY` and `GOOGLE_GENAI_USE_VERTEXAI=FALSE` through Cloud
Run environment configuration or Secret Manager. Do not pass credentials in a
committed file or bake them into the container image.

Google documents `--with_ui` as a development/testing interface. Add
authentication, rate limiting, monitoring, and a dedicated frontend before
using this service for sensitive or unrestricted public traffic.

## Limitations

- The upstream API can be unavailable or have missing dates.
- Three-letter syntax validation does not prove a currency is supported; the
  provider remains the source of truth.
- Time-series requests are limited to 366 days to bound response size.
- The app has no application-level user authentication or persistent sessions.
- The live demo can have a Cloud Run cold-start delay.

## Project Structure

```text
currency-bot/
|-- .github/workflows/tests.yml
|-- agents/
|   `-- currency_agent/
|       |-- __init__.py
|       |-- agent.py
|       `-- mcp_server.py
|-- tests/
|-- .env.example
|-- architecture.svg
|-- Dockerfile
|-- requirements.txt
|-- requirements-dev.txt
`-- SECURITY.md
```

## Author

**Vishwas Prabhakara**

[GitHub](https://github.com/VishwasPrabhakara) |
[LinkedIn](https://www.linkedin.com/in/vishwas-prabhakara)

## License

[MIT](LICENSE)
