#!/usr/bin/env python3
"""Stock Research Report — deep-dive on a single company."""

import argparse
from datetime import datetime, timedelta

from common import get_obb, format_number, safe_get, pct_change


# ── Sections ──────────────────────────────────────────────


def section_price(obb, symbol: str, provider: str):
    """Price summary with multi-timeframe returns."""
    print("## 💰 Price Summary\n")
    try:
        start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        df = obb.equity.price.historical(symbol, start_date=start, provider=provider).to_dataframe()
        if df.empty:
            print("  No price data available.\n")
            return

        price = df.iloc[-1]["close"]
        volume = df.iloc[-1].get("volume", 0)
        high_52w, low_52w = df["high"].max(), df["low"].min()
        pct_high = pct_change(price, high_52w)

        print(f"  Current Price: ${price:.2f}")
        print(f"  Volume: {volume:,.0f}")
        print(f"  52-Week Range: ${low_52w:.2f} — ${high_52w:.2f} ({pct_high:+.1f}% from high)\n")
        print("  Performance:")

        for label, days in [("1d", 1), ("5d", 5), ("1m", 21), ("3m", 63), ("6m", 126), ("1y", 252)]:
            idx = min(days, len(df) - 1)
            if idx > 0:
                ret = pct_change(price, df.iloc[-(idx + 1)]["close"])
                arrow = "📈" if ret > 0 else "📉" if ret < 0 else "➡️"
                print(f"    {label:4s}: {arrow} {ret:+.2f}%")
    except Exception as e:
        print(f"  Error: {e}")
    print()


def section_profile(obb, symbol: str, provider: str):
    """Company profile."""
    print("## 🏢 Company Profile\n")
    try:
        df = obb.equity.profile(symbol, provider=provider).to_dataframe()
        if df.empty:
            print("  Not available.\n")
            return

        for key, label in [
            ("name", "Name"), ("sector", "Sector"), ("industry", "Industry"),
            ("market_cap", "Market Cap"), ("employees", "Employees"),
        ]:
            val = safe_get(df, key)
            if val == "N/A":
                continue
            if key == "market_cap" and isinstance(val, (int, float)):
                val = format_number(val)
            elif key == "employees" and isinstance(val, (int, float)):
                val = f"{int(val):,}"
            print(f"  {label}: {val}")
    except Exception as e:
        print(f"  Not available: {e}")
    print()


def section_metrics(obb, symbol: str, provider: str):
    """Key financial metrics and ratios."""
    print("## 📊 Key Metrics\n")
    try:
        df = obb.equity.fundamental.metrics(symbol, provider=provider).to_dataframe()
        if df.empty:
            print("  Not available.\n")
            return

        # Fields grouped: (column, display label, is_percentage)
        fields = [
            ("pe_ratio", "P/E Ratio", False),
            ("forward_pe", "Forward P/E", False),
            ("price_to_book", "P/B Ratio", False),
            ("revenue_growth", "Revenue Growth", True),
            ("dividend_yield", "Dividend Yield", True),
            ("return_on_equity", "ROE", True),
            ("return_on_assets", "ROA", True),
            ("debt_to_equity", "Debt/Equity", False),
            ("current_ratio", "Current Ratio", False),
            ("gross_margin", "Gross Margin", True),
            ("operating_margin", "Operating Margin", True),
            ("beta", "Beta", False),
        ]
        for col, label, is_pct in fields:
            val = safe_get(df, col)
            if val == "N/A" or val is None:
                continue
            if isinstance(val, float):
                if is_pct:
                    display = f"{val * 100:.2f}%" if abs(val) < 10 else f"{val:.2f}%"
                else:
                    display = f"{val:.2f}"
                print(f"  {label:20s}: {display}")
    except Exception as e:
        print(f"  Not available: {e}")
    print()


def section_financials(obb, symbol: str, provider: str):
    """Income statement, balance sheet, and cash flow (last 4 quarters)."""
    print("## 📋 Financials (Last 4 Quarters)\n")

    statement_config = {
        "Income Statement": {
            "fn": obb.equity.fundamental.income,
            "cols": ["revenue", "gross_profit", "operating_income", "net_income"],
        },
        "Balance Sheet": {
            "fn": obb.equity.fundamental.balance,
            "cols": ["total_assets", "total_liabilities", "total_equity", "total_debt"],
        },
        "Cash Flow": {
            "fn": obb.equity.fundamental.cash,
            "cols": ["operating_cash_flow", "capital_expenditure", "free_cash_flow"],
        },
    }

    for name, cfg in statement_config.items():
        print(f"  ### {name}")
        try:
            df = cfg["fn"](symbol, period="quarter", limit=4, provider=provider).to_dataframe()
            if df.empty:
                print("    Not available.\n")
                continue
            for col in cfg["cols"]:
                if col not in df.columns:
                    continue
                vals = [format_number(v) if isinstance(v, (int, float)) else str(v) for v in df[col].head(4)]
                label = col.replace("_", " ").title()
                print(f"    {label:30s}: {' → '.join(vals)}")
        except Exception as e:
            print(f"    Error: {e}")
        print()


def section_estimates(obb, symbol: str, provider: str):
    """Analyst estimates and EPS beat/miss history."""
    print("## 🎯 Analyst Estimates\n")

    try:
        df = obb.equity.estimates.consensus(symbol, provider=provider).to_dataframe()
        if not df.empty:
            for _, row in df.head(4).iterrows():
                period = row.get("fiscal_period", row.get("period", "?"))
                rev = row.get("estimated_revenue_avg", row.get("revenue_avg", None))
                eps = row.get("estimated_eps_avg", row.get("eps_avg", None))
                rev_s = format_number(rev) if isinstance(rev, (int, float)) else "N/A"
                eps_s = f"${eps:.2f}" if isinstance(eps, (int, float)) else "N/A"
                print(f"  {period}: Rev {rev_s} | EPS {eps_s}")
    except Exception as e:
        print(f"  Estimates not available: {e}")
    print()

    try:
        df = obb.equity.fundamental.historical_eps(symbol, provider=provider).to_dataframe()
        if not df.empty:
            print("  EPS History:")
            for _, row in df.head(8).iterrows():
                date = row.get("date", row.get("fiscal_date_ending", "?"))
                actual = row.get("actual_eps", row.get("reported_eps", None))
                est = row.get("estimated_eps", None)
                if isinstance(actual, (int, float)) and isinstance(est, (int, float)):
                    diff = actual - est
                    icon = "✅" if diff >= 0 else "❌"
                    print(f"    {date}: ${actual:.2f} vs Est ${est:.2f} ({icon} {diff:+.2f})")
                elif isinstance(actual, (int, float)):
                    print(f"    {date}: ${actual:.2f}")
    except Exception:
        pass
    print()


def section_dividends(obb, symbol: str, provider: str):
    """Recent dividend history."""
    print("## 💵 Dividends\n")
    try:
        df = obb.equity.fundamental.dividends(symbol, provider=provider).to_dataframe()
        if df.empty:
            print("  No dividend data.\n")
            return
        for _, row in df.tail(8).iterrows():
            date = row.get("ex_dividend_date", row.get("date", "?"))
            amt = row.get("amount", row.get("dividend", None))
            print(f"  {date}: ${amt:.4f}" if isinstance(amt, (int, float)) else f"  {date}: {amt}")
    except Exception as e:
        print(f"  Not available: {e}")
    print()


# ── Main ──────────────────────────────────────────────────


def main():
    p = argparse.ArgumentParser(description="Stock Research Report")
    p.add_argument("symbol", help="Ticker symbol (e.g. AAPL)")
    p.add_argument("--full", action="store_true", help="All sections")
    p.add_argument("--financials", action="store_true")
    p.add_argument("--estimates", action="store_true")
    p.add_argument("--dividends", action="store_true")
    p.add_argument("--provider", "-p", default="yfinance")
    args = p.parse_args()

    symbol = args.symbol.upper()
    obb = get_obb()

    print(f"📈 Stock Research Report: {symbol}")
    print(f"{'=' * 60}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    section_price(obb, symbol, args.provider)
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
