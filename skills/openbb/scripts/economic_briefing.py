#!/usr/bin/env python3
"""Economic Briefing — macro indicators, CPI, GDP, rates, unemployment, FRED."""

import argparse
from datetime import datetime, timedelta

from common import get_obb, format_change, pct_change


# ── Helpers ───────────────────────────────────────────────


def _oecd_value(df, col: str = "value"):
    """Extract the value column from OECD-style DataFrames.

    OECD returns decimals (0.043 = 4.3%) while FRED returns raw percentages.
    Returns (column_name, is_decimal) so callers can display correctly.
    """
    if col in df.columns:
        sample = df[col].dropna().iloc[-1] if len(df) > 0 else 0
        return col, abs(sample) < 1
    # Fallback to first numeric column
    for c in df.columns:
        if df[c].dtype in ("float64", "int64"):
            sample = df[c].dropna().iloc[-1] if len(df) > 0 else 0
            return c, abs(sample) < 1
    return df.columns[0], False


def _try_providers(fn, providers: list[str], **kwargs):
    """Try multiple providers in order, return first non-empty DataFrame."""
    for provider in providers:
        try:
            df = fn(provider=provider, **kwargs).to_dataframe()
            if not df.empty:
                return df
        except Exception:
            continue
    return None


# ── Sections ──────────────────────────────────────────────


def section_market_context(obb):
    """Quick snapshot of major market indices."""
    print("## 🌍 Market Context\n")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    for symbol, name in [("^GSPC", "S&P 500"), ("^DJI", "Dow Jones"), ("^IXIC", "NASDAQ"), ("^VIX", "VIX (Fear Index)")]:
        try:
            df = obb.equity.price.historical(symbol, start_date=start, provider="yfinance").to_dataframe()
            if len(df) >= 2:
                price = df.iloc[-1]["close"]
                change = pct_change(price, df.iloc[-2]["close"])
                arrow = "📈" if change > 0 else "📉"
                print(f"  {name:15s}: {price:>10,.2f} {arrow} {change:+.2f}%")
            else:
                print(f"  {name:15s}: N/A")
        except Exception:
            print(f"  {name:15s}: N/A")
    print()


def section_cpi(obb, country: str):
    """Consumer Price Index / inflation data."""
    print("## 📊 Consumer Price Index (CPI)\n")

    df = _try_providers(obb.economy.cpi, ["fred", "oecd"], country=country, frequency="monthly")
    if df is None:
        print("  CPI data requires FRED API key or OECD access.")
        print("  Get a free key: https://fred.stlouisfed.org/docs/api/api_key.html\n")
        return

    col, is_decimal = _oecd_value(df)
    recent = df.tail(12)

    if is_decimal:
        print(f"  {'Date':12s} {'YoY Inflation':>14s}")
        print(f"  {'-' * 12} {'-' * 14}")
        for idx, row in recent.iterrows():
            val = row[col]
            if isinstance(val, (int, float)):
                pct = val * 100
                arrow = "📈" if pct > 0 else "📉"
                print(f"  {str(idx)[:7]:12s} {arrow} {pct:>6.2f}%")
    else:
        prev = None
        print(f"  {'Date':12s} {'CPI Index':>12s} {'MoM':>10s}")
        print(f"  {'-' * 12} {'-' * 12} {'-' * 10}")
        for idx, row in recent.iterrows():
            val = row[col]
            if isinstance(val, (int, float)):
                mom = format_change(pct_change(val, prev)) if prev else ""
                print(f"  {str(idx)[:7]:12s} {val:12.2f} {mom:>10s}")
                prev = val
    print()


def section_gdp(obb, country: str):
    """GDP growth data."""
    print("## 📊 GDP Growth\n")

    df = _try_providers(obb.economy.gdp.nominal, ["oecd"], country=country)
    if df is None:
        print("  GDP data not available.\n")
        return

    col, is_decimal = _oecd_value(df)
    prev = None
    for idx, row in df.tail(8).iterrows():
        val = row[col]
        if isinstance(val, (int, float)):
            growth = f"  {format_change(pct_change(val, prev))}" if prev else ""
            val_s = f"${val / 1e9:.1f}B" if val > 1e6 else f"${val:,.0f}"
            print(f"  {str(idx)[:10]:12s} {val_s:>15s}{growth}")
            prev = val
    print()


def section_rates(obb, country: str):
    """Interest rates."""
    print("## 🏦 Interest Rates\n")

    df = _try_providers(obb.economy.interest_rates, ["oecd"], country=country)
    if df is not None:
        col, is_decimal = _oecd_value(df)
        for idx, row in df.tail(6).iterrows():
            val = row[col]
            if isinstance(val, (int, float)):
                display = val * 100 if is_decimal else val
                print(f"  {str(idx)[:10]}: {display:.2f}%")
        print()
        return

    # Fallback: FRED series for US rates
    print("  (OECD unavailable, trying FRED...)")
    for series_id, label in [("DFF", "Fed Funds"), ("DGS2", "2Y Treasury"), ("DGS10", "10Y Treasury"), ("DGS30", "30Y Treasury")]:
        try:
            df = obb.economy.fred_series(symbol=series_id, provider="fred").to_dataframe()
            if not df.empty:
                val = df.iloc[-1].iloc[0]
                if isinstance(val, (int, float)):
                    print(f"  {label:15s}: {val:.2f}%")
        except Exception:
            print(f"  {label:15s}: N/A (FRED API key required)")
            break
    print()


def section_unemployment(obb, country: str):
    """Unemployment rate."""
    print("## 👥 Unemployment\n")

    df = _try_providers(obb.economy.unemployment, ["fred", "oecd"], country=country)
    if df is None:
        print("  Requires FRED API key or OECD access.\n")
        return

    col, is_decimal = _oecd_value(df)
    for idx, row in df.tail(12).iterrows():
        val = row[col]
        if isinstance(val, (int, float)):
            display = val * 100 if is_decimal else val
            print(f"  {str(idx)[:7]}: {display:.1f}%")
    print()


def section_fred(obb, series_id: str):
    """Query any FRED series by ID."""
    print(f"## 📊 FRED: {series_id}\n")
    try:
        try:
            sdf = obb.economy.fred_search(query=series_id, provider="fred").to_dataframe()
            if not sdf.empty:
                print(f"  {sdf.iloc[0].get('title', series_id)}\n")
        except Exception:
            pass

        df = obb.economy.fred_series(symbol=series_id, provider="fred").to_dataframe()
        if df.empty:
            print("  No data. Requires FRED API key.\n")
            return
        for idx, row in df.tail(12).iterrows():
            val = row.iloc[0]
            if isinstance(val, (int, float)):
                print(f"  {str(idx)[:10]}: {val:,.4f}")
    except Exception as e:
        print(f"  Error: {e}")
        print("  Get a free FRED key: https://fred.stlouisfed.org/docs/api/api_key.html")
    print()


# ── Main ──────────────────────────────────────────────────


def main():
    p = argparse.ArgumentParser(description="Economic Briefing")
    p.add_argument("--cpi", action="store_true")
    p.add_argument("--gdp", action="store_true")
    p.add_argument("--rates", action="store_true")
    p.add_argument("--unemployment", action="store_true")
    p.add_argument("--fred", type=str, metavar="SERIES_ID")
    p.add_argument("--all", action="store_true")
    p.add_argument("--country", "-c", default="united_states")
    p.add_argument("--no-market", action="store_true")
    args = p.parse_args()

    obb = get_obb()
    show_all = args.all or not any([args.cpi, args.gdp, args.rates, args.unemployment, args.fred])

    print(f"🏛️ Economic Briefing — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"Country: {args.country.replace('_', ' ').title()}\n")

    if not args.no_market:
        section_market_context(obb)
    if show_all or args.cpi:
        section_cpi(obb, args.country)
    if show_all or args.gdp:
        section_gdp(obb, args.country)
    if show_all or args.rates:
        section_rates(obb, args.country)
    if show_all or args.unemployment:
        section_unemployment(obb, args.country)
    if args.fred:
        section_fred(obb, args.fred)

    print("---")
    print("Sources: OECD, FRED, Yahoo Finance (via OpenBB Platform)")


if __name__ == "__main__":
    main()
