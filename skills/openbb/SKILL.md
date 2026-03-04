---
name: openbb
description: "Financial market data and research via OpenBB Platform. Use when: (1) checking stock prices, quotes, or watchlists, (2) researching a company (fundamentals, metrics, financials, estimates), (3) getting economic indicators (CPI, GDP, unemployment, interest rates), (4) querying crypto, forex, ETFs, or market indices, (5) fetching FRED data series. NOT for: trade execution, portfolio management, financial advice, or real-time tick data."
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["python3"], "pip": ["openbb"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "pip",
              "package": "openbb",
              "bins": [],
              "label": "Install OpenBB Platform (pip)",
            },
          ],
      },
  }
---

# OpenBB Financial Data Skill

Query financial markets using the [OpenBB Platform](https://github.com/OpenBB-finance/OpenBB) Python SDK.

## When to Use

✅ **USE this skill when:**

- Stock quotes, price history, or watchlists
- Company research (profile, metrics, financials)
- Economic indicators (CPI, GDP, unemployment, rates)
- Crypto, forex, or ETF data
- FRED economic data series
- Market movers (gainers/losers)

## When NOT to Use

❌ **DON'T use this skill when:**

- Trading or order execution → use a broker
- Portfolio tracking → use dedicated tools
- Real-time tick data → use a streaming API
- Financial advice → you're an AI, not an advisor

## Prerequisites

- `pip install openbb` (free, uses yfinance by default)
- Premium providers (FMP, Intrinio, Polygon) need API keys set via config

## Feature 1: Market Dashboard

Quick market overview — watchlist quotes with performance and day ranges.

```bash
python3 SKILL_DIR/scripts/market_dashboard.py [OPTIONS]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--symbols SYM1,SYM2` | Comma-separated watchlist | AAPL,MSFT,GOOGL,AMZN,NVDA |
| `--movers` | Show top gainers/losers | off |
| `--days N` | Lookback for performance | 5 |
| `--provider P` | Data provider | yfinance |

**Example output:**
```
AAPL  $263.75  📉 -0.37%  5d: 📉 -3.08%  Vol: 38.5M
MSFT  $403.93  📈 +1.35%  5d: 📈 +3.84%  Vol: 38.1M
```

## Feature 2: Stock Research Report

Deep-dive on a single company — price, profile, metrics, financials, estimates.

```bash
python3 SKILL_DIR/scripts/stock_research.py SYMBOL [OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--full` | All sections |
| `--financials` | Income/balance/cash flow (last 4 quarters) |
| `--estimates` | Analyst consensus + EPS history |
| `--dividends` | Dividend history |
| `--provider P` | Data provider (default: yfinance) |

**Sections (always shown):** Price summary (multi-timeframe returns, 52W range), company profile, key metrics (P/E, margins, ROE, beta).

## Feature 3: Economic Briefing

Macro economic overview with market context.

```bash
python3 SKILL_DIR/scripts/economic_briefing.py [OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--all` | All indicators (default if none specified) |
| `--cpi` | Consumer Price Index / inflation |
| `--gdp` | GDP data |
| `--rates` | Interest rates |
| `--unemployment` | Unemployment rate |
| `--fred SERIES_ID` | Any FRED series (e.g. DGS10) |
| `--country C` | Country (default: united_states) |
| `--no-market` | Skip market index snapshot |

**Market context** (always shown unless `--no-market`): S&P 500, Dow, NASDAQ, VIX with daily changes.

## Data Provider Notes

| Provider | Free | API Key | Coverage |
|----------|------|---------|----------|
| yfinance | ✅ | No | Equities, ETFs, crypto, indices |
| OECD | ✅ | No | CPI, GDP, unemployment, rates |
| FRED | ✅ | Yes (free) | 800K+ economic series |
| FMP | Partial | Yes | Fundamentals, screeners, movers |
| Intrinio | ❌ | Yes | Deep fundamentals |

Get a free FRED key: https://fred.stlouisfed.org/docs/api/api_key.html

## Output Guidelines

- Use emoji for trends: 📈 up, 📉 down, ➡️ flat
- Keep chat output concise — bullet points over tables
- Include +/- percentage changes
- Note data freshness when relevant
