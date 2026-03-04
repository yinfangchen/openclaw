---
name: openbb
description: Financial market data and research via OpenBB Platform. Use when the user asks about stock prices, market movers, company fundamentals, earnings, economic indicators (CPI, GDP, rates, FRED), crypto, forex, or wants a research report on a stock. Provides 3 tools — market dashboard (quotes + movers), stock research reports (financials + metrics + estimates), and economic briefings (macro data). NOT for: trading execution, portfolio management, or financial advice.
metadata:
  {
    "openclaw":
      { "emoji": "📈", "requires": { "anyBins": ["python3"], "pip": ["openbb"] } },
  }
---

# OpenBB Financial Data Skill

Query financial markets using the OpenBB Platform SDK. Requires `pip install openbb`.

Free data via `yfinance` provider works without API keys. Premium providers (FMP, Intrinio, Polygon, etc.) need keys set via `obb.user.credentials`.

## Feature 1: Market Dashboard

Quick market overview — watchlist quotes, top gainers/losers, and price snapshots.

```bash
python3 SKILL_DIR/scripts/market_dashboard.py [OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--symbols SYM1,SYM2` | Comma-separated watchlist (default: AAPL,MSFT,GOOGL,AMZN,NVDA) |
| `--movers` | Show top gainers and losers |
| `--days N` | Lookback for performance calc (default: 5) |
| `--provider P` | Data provider (default: yfinance) |

**Examples:**
```bash
# Default tech watchlist
python3 SKILL_DIR/scripts/market_dashboard.py

# Custom watchlist with movers
python3 SKILL_DIR/scripts/market_dashboard.py --symbols TSLA,META,NFLX --movers

# Crypto watchlist
python3 SKILL_DIR/scripts/market_dashboard.py --symbols BTC-USD,ETH-USD,SOL-USD
```

## Feature 2: Stock Research Report

Deep-dive on a single company — profile, key metrics, financials, and analyst estimates.

```bash
python3 SKILL_DIR/scripts/stock_research.py SYMBOL [OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--full` | Include all sections (default: summary only) |
| `--financials` | Income statement, balance sheet, cash flow |
| `--estimates` | Analyst estimates and EPS history |
| `--dividends` | Dividend history |
| `--provider P` | Data provider (default: yfinance) |

**Examples:**
```bash
# Quick summary
python3 SKILL_DIR/scripts/stock_research.py AAPL

# Full research report
python3 SKILL_DIR/scripts/stock_research.py AAPL --full

# Just financials
python3 SKILL_DIR/scripts/stock_research.py MSFT --financials
```

## Feature 3: Economic Briefing

Macro economic overview — CPI, GDP, interest rates, unemployment, FRED series.

```bash
python3 SKILL_DIR/scripts/economic_briefing.py [OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--cpi` | Consumer Price Index data |
| `--gdp` | GDP growth data |
| `--rates` | Interest rates (Fed Funds, Treasury yields) |
| `--unemployment` | Unemployment rate |
| `--fred SERIES_ID` | Query any FRED series by ID |
| `--all` | All major indicators |
| `--country C` | Country (default: united_states) |

**Examples:**
```bash
# Full macro briefing
python3 SKILL_DIR/scripts/economic_briefing.py --all

# Just inflation data
python3 SKILL_DIR/scripts/economic_briefing.py --cpi

# Custom FRED series (e.g., 10Y Treasury)
python3 SKILL_DIR/scripts/economic_briefing.py --fred DGS10
```

## Output Guidelines

- Use emoji for direction: 📈 up, 📉 down, ➡️ flat
- Keep chat output concise — bullet points over tables
- For research reports, use structured sections with headers
- Include percentage changes with +/- signs
- Note data freshness (market hours, last update)
