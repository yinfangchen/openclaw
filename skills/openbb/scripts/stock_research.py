#!/usr/bin/env python3
"""Feature 2: Stock Research Report — deep-dive on a single company."""

import argparse
import sys
from datetime import datetime, timedelta


def get_obb():
    try:
        from openbb import obb
        return obb
    except ImportError:
        print("Error: openbb not installed. Run: pip install openbb", file=sys.stderr)
        sys.exit(1)


def format_number(n):
    if n is None:
        return "N/A"
    if isinstance(n, str):
        return n
    if abs(n) >= 1e12:
        return f"${n/1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.1f}K"
    return f"${n:,.2f}"


def safe_get(df, col, row=0, default="N/A"):
    """Safely get a value from a DataFrame."""
    try:
        if col in df.columns and len(df) > row:
            val = df.iloc[row][col]
            if val is not None and str(val) != "nan":
                return val
    except Exception:
        pass
    return default


def section_price_summary(obb, symbol, provider):
    """Price and performance summary."""
    print("## 💰 Price Summary")
    print()
    try:
        start_1y = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        hist = obb.equity.price.historical(symbol, start_date=start_1y, provider=provider)
        df = hist.to_dataframe()

        if df.empty:
            print("  No price data available.")
            return

        latest = df.iloc[-1]
        price = latest["close"]
        volume = latest.get("volume", 0)

        # Calculate various timeframe returns
        periods = {"1d": 1, "5d": 5, "1m": 21, "3m": 63, "6m": 126, "1y": 252}
        returns = {}
        for label, days in periods.items():
            idx = min(days, len(df) - 1)
            if idx > 0:
                old_price = df.iloc[-(idx + 1)]["close"]
                returns[label] = ((price - old_price) / old_price) * 100
            else:
                returns[label] = 0.0

        high_52w = df["high"].max()
        low_52w = df["low"].min()
        pct_from_high = ((price - high_52w) / high_52w) * 100

        print(f"  Current Price: ${price:.2f}")
        print(f"  Volume: {volume:,.0f}")
        print(f"  52-Week Range: ${low_52w:.2f} — ${high_52w:.2f} ({pct_from_high:+.1f}% from high)")
        print()
        print("  Performance:")
        for label, ret in returns.items():
            arrow = "📈" if ret > 0 else "📉" if ret < 0 else "➡️"
            print(f"    {label:4s}: {arrow} {ret:+.2f}%")
    except Exception as e:
        print(f"  Error fetching price: {e}")
    print()


def section_profile(obb, symbol, provider):
    """Company profile."""
    print("## 🏢 Company Profile")
    print()
    try:
        result = obb.equity.profile(symbol, provider=provider)
        df = result.to_dataframe()
        if df.empty:
            print("  Profile not available with this provider.")
            print()
            return

        fields = {
            "name": "Name",
            "sector": "Sector",
            "industry": "Industry",
            "market_cap": "Market Cap",
            "employees": "Employees",
            "country": "Country",
            "website": "Website",
            "description": "Description",
        }
        for key, label in fields.items():
            val = safe_get(df, key)
            if val != "N/A":
                if key == "market_cap" and isinstance(val, (int, float)):
                    val = format_number(val)
                if key == "employees" and isinstance(val, (int, float)):
                    val = f"{int(val):,}"
                if key == "description" and isinstance(val, str) and len(val) > 200:
                    val = val[:200] + "..."
                print(f"  {label}: {val}")
    except Exception as e:
        print(f"  Profile not available: {e}")
    print()


def section_metrics(obb, symbol, provider):
    """Key financial metrics."""
    print("## 📊 Key Metrics")
    print()
    try:
        result = obb.equity.fundamental.metrics(symbol, provider=provider)
        df = result.to_dataframe()
        if df.empty:
            print("  Metrics not available.")
            print()
            return

        metric_fields = {
            "pe_ratio": "P/E Ratio",
            "forward_pe": "Forward P/E",
            "peg_ratio": "PEG Ratio",
            "price_to_book": "P/B Ratio",
            "price_to_sales": "P/S Ratio",
            "eps": "EPS",
            "eps_growth": "EPS Growth",
            "revenue_growth": "Revenue Growth",
            "dividend_yield": "Dividend Yield",
            "return_on_equity": "ROE",
            "return_on_assets": "ROA",
            "debt_to_equity": "Debt/Equity",
            "current_ratio": "Current Ratio",
            "gross_margin": "Gross Margin",
            "operating_margin": "Operating Margin",
            "net_margin": "Net Margin",
            "beta": "Beta",
        }
        for key, label in metric_fields.items():
            val = safe_get(df, key)
            if val != "N/A" and val is not None:
                if isinstance(val, float):
                    if "yield" in key or "margin" in key or "growth" in key or "return" in key:
                        print(f"  {label:20s}: {val*100:.2f}%" if abs(val) < 10 else f"  {label:20s}: {val:.2f}%")
                    else:
                        print(f"  {label:20s}: {val:.2f}")
                else:
                    print(f"  {label:20s}: {val}")
    except Exception as e:
        print(f"  Metrics not available: {e}")
    print()


def section_financials(obb, symbol, provider):
    """Income statement, balance sheet, cash flow."""
    print("## 📋 Financials (Last 4 Quarters)")
    print()

    statements = {
        "Income Statement": obb.equity.fundamental.income,
        "Balance Sheet": obb.equity.fundamental.balance,
        "Cash Flow": obb.equity.fundamental.cash,
    }

    for name, fn in statements.items():
        print(f"  ### {name}")
        try:
            result = fn(symbol, period="quarter", limit=4, provider=provider)
            df = result.to_dataframe()
            if df.empty:
                print(f"    Not available.")
                print()
                continue

            # Pick key columns based on statement type
            if "Income" in name:
                cols = ["revenue", "gross_profit", "operating_income", "net_income", "eps_diluted"]
            elif "Balance" in name:
                cols = ["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents", "total_debt"]
            else:
                cols = ["operating_cash_flow", "capital_expenditure", "free_cash_flow"]

            for col in cols:
                if col in df.columns:
                    vals = df[col].head(4).tolist()
                    formatted = [format_number(v) if isinstance(v, (int, float)) else str(v) for v in vals]
                    label = col.replace("_", " ").title()
                    print(f"    {label:30s}: {' → '.join(formatted)}")
        except Exception as e:
            print(f"    Error: {e}")
        print()


def section_estimates(obb, symbol, provider):
    """Analyst estimates and EPS history."""
    print("## 🎯 Analyst Estimates")
    print()

    try:
        result = obb.equity.estimates.consensus(symbol, provider=provider)
        df = result.to_dataframe()
        if not df.empty:
            for _, row in df.head(4).iterrows():
                period = row.get("fiscal_period", row.get("period", "?"))
                est_rev = row.get("estimated_revenue_avg", row.get("revenue_avg", "N/A"))
                est_eps = row.get("estimated_eps_avg", row.get("eps_avg", "N/A"))
                if isinstance(est_rev, (int, float)):
                    est_rev = format_number(est_rev)
                if isinstance(est_eps, (int, float)):
                    est_eps = f"${est_eps:.2f}"
                print(f"  {period}: Rev {est_rev} | EPS {est_eps}")
    except Exception as e:
        print(f"  Estimates not available: {e}")

    print()

    # EPS history
    try:
        result = obb.equity.fundamental.historical_eps(symbol, provider=provider)
        df = result.to_dataframe()
        if not df.empty:
            print("  EPS History (recent):")
            for _, row in df.head(8).iterrows():
                date = row.get("date", row.get("fiscal_date_ending", "?"))
                actual = row.get("actual_eps", row.get("reported_eps", "N/A"))
                estimated = row.get("estimated_eps", "N/A")
                if isinstance(actual, (int, float)) and isinstance(estimated, (int, float)):
                    surprise = actual - estimated
                    emoji = "✅" if surprise >= 0 else "❌"
                    print(f"    {date}: Actual ${actual:.2f} vs Est ${estimated:.2f} ({emoji} {surprise:+.2f})")
                elif isinstance(actual, (int, float)):
                    print(f"    {date}: ${actual:.2f}")
    except Exception:
        pass
    print()


def section_dividends(obb, symbol, provider):
    """Dividend history."""
    print("## 💵 Dividends")
    print()
    try:
        result = obb.equity.fundamental.dividends(symbol, provider=provider)
        df = result.to_dataframe()
        if df.empty:
            print("  No dividend data available.")
        else:
            recent = df.head(8)
            for _, row in recent.iterrows():
                date = row.get("ex_dividend_date", row.get("date", "?"))
                amount = row.get("amount", row.get("dividend", "N/A"))
                if isinstance(amount, (int, float)):
                    print(f"  {date}: ${amount:.4f}")
                else:
                    print(f"  {date}: {amount}")
    except Exception as e:
        print(f"  Dividend data not available: {e}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Stock Research Report")
    parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    parser.add_argument("--full", action="store_true", help="Full research report")
    parser.add_argument("--financials", action="store_true", help="Include financials")
    parser.add_argument("--estimates", action="store_true", help="Include estimates")
    parser.add_argument("--dividends", action="store_true", help="Include dividends")
    parser.add_argument("--provider", "-p", default="yfinance", help="Data provider")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    obb = get_obb()

    print(f"📈 Stock Research Report: {symbol}")
    print(f"{'=' * 60}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Always show price and profile
    section_price_summary(obb, symbol, args.provider)
    section_profile(obb, symbol, args.provider)
    section_metrics(obb, symbol, args.provider)

    if args.full or args.financials:
        section_financials(obb, symbol, args.provider)

    if args.full or args.estimates:
        section_estimates(obb, symbol, args.provider)

    if args.full or args.dividends:
        section_dividends(obb, symbol, args.provider)


if __name__ == "__main__":
    main()
