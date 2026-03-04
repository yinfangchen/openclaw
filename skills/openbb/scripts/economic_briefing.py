#!/usr/bin/env python3
"""Feature 3: Economic Briefing — macro indicators, CPI, GDP, rates, FRED data."""

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


def format_pct(val):
    if val is None or str(val) == "nan":
        return "N/A"
    arrow = "📈" if val > 0 else "📉" if val < 0 else "➡️"
    return f"{arrow} {val:+.2f}%"


def section_cpi(obb, country):
    """Consumer Price Index data."""
    print("## 📊 Consumer Price Index (CPI)")
    print()

    # Try multiple providers
    providers = ["fred", "oecd"]
    df = None
    for provider in providers:
        try:
            result = obb.economy.cpi(
                country=country,
                frequency="monthly",
                provider=provider,
            )
            df = result.to_dataframe()
            if not df.empty:
                break
        except Exception:
            continue

    if df is None or df.empty:
        # Fallback: use Treasury inflation-indexed securities as proxy
        try:
            result = obb.equity.price.historical("TIP", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"), provider="yfinance")
            tip_df = result.to_dataframe()
            if not tip_df.empty:
                print("  (Using TIP ETF as inflation proxy — FRED API key needed for actual CPI)")
                monthly = tip_df.resample("ME" if hasattr(tip_df.index, 'to_period') else "M").last()
                recent = monthly.tail(6)
                for idx, row in recent.iterrows():
                    date = str(idx)[:7]
                    print(f"  {date}: ${row['close']:.2f}")
                print()
                return
        except Exception:
            pass
        print("  CPI data requires FRED API key or OECD access.")
        print("  Set key: obb.user.credentials['fred_api_key'] = 'YOUR_KEY'")
        print("  Get free key: https://fred.stlouisfed.org/docs/api/api_key.html")
        print()
        return

    # Show last 12 months — handle both index-style and rate-style data
    recent = df.tail(12)

    # Detect if data is YoY rate (small values like 0.02) or index (large values like 300)
    val_col = "value" if "value" in df.columns else df.columns[0]
    sample_val = recent[val_col].dropna().iloc[-1] if len(recent) > 0 else 0
    is_rate = abs(sample_val) < 1  # YoY inflation rate vs CPI index

    if is_rate:
        print(f"  {'Date':12s} {'YoY Inflation':>14s}")
        print(f"  {'-'*12} {'-'*14}")
        for idx, row in recent.iterrows():
            date = str(idx)[:7]
            val = row[val_col] if val_col in row.index else None
            if isinstance(val, (int, float)):
                pct = val * 100
                arrow = "📈" if pct > 0 else "📉"
                print(f"  {date:12s} {arrow} {pct:>6.2f}%")
    else:
        prev_val = None
        print(f"  {'Date':12s} {'CPI Index':>12s} {'MoM Change':>12s}")
        print(f"  {'-'*12} {'-'*12} {'-'*12}")
        for idx, row in recent.iterrows():
            date = str(idx)[:7]
            val = row[val_col] if val_col in row.index else None
            if isinstance(val, (int, float)):
                mom = ""
                if prev_val and isinstance(prev_val, (int, float)) and prev_val != 0:
                    change = ((val - prev_val) / prev_val) * 100
                    mom = format_pct(change)
                print(f"  {date:12s} {val:12.2f} {mom:>12s}")
                prev_val = val
    print()


def section_gdp(obb, country):
    """GDP growth data."""
    print("## 📊 GDP Growth")
    print()
    try:
        result = obb.economy.gdp.nominal(
            country=country,
            provider="oecd",
        )
        df = result.to_dataframe()
        if df.empty:
            print("  No GDP data available.")
            print()
            return

        recent = df.tail(8)
        prev_val = None
        for idx, row in recent.iterrows():
            date = str(idx) if not hasattr(idx, 'strftime') else idx.strftime("%Y-Q%q" if hasattr(idx, 'quarter') else "%Y-%m")
            val = row.iloc[0] if len(row) > 0 else None
            if isinstance(val, (int, float)):
                growth = ""
                if prev_val and isinstance(prev_val, (int, float)) and prev_val != 0:
                    change = ((val - prev_val) / prev_val) * 100
                    growth = format_pct(change)
                val_str = f"${val/1e9:.1f}B" if val > 1e6 else f"${val:,.0f}"
                print(f"  {str(date):12s} {val_str:>15s} {growth}")
                prev_val = val
    except Exception as e:
        print(f"  GDP data error: {e}")
    print()


def section_interest_rates(obb, country):
    """Interest rates overview."""
    print("## 🏦 Interest Rates")
    print()

    # Try to get short and long term rates
    try:
        result = obb.economy.interest_rates(
            country=country,
            provider="oecd",
        )
        df = result.to_dataframe()
        if not df.empty:
            recent = df.tail(6)
            val_col = "value" if "value" in df.columns else None
            for idx, row in recent.iterrows():
                date = str(idx)[:10]
                if val_col:
                    val = row[val_col]
                    if isinstance(val, (int, float)):
                        display = val * 100 if abs(val) < 1 else val
                        print(f"  {date}: {display:.2f}%")
                else:
                    for col in row.index:
                        val = row[col]
                        if isinstance(val, (int, float)):
                            display = val * 100 if abs(val) < 1 else val
                            print(f"  {date} — {col}: {display:.2f}%")
            print()
            return
    except Exception:
        pass

    # Fallback: try FRED series for key rates
    rate_series = {
        "DFF": "Fed Funds Rate",
        "DGS2": "2Y Treasury",
        "DGS10": "10Y Treasury",
        "DGS30": "30Y Treasury",
    }

    for series_id, label in rate_series.items():
        try:
            result = obb.economy.fred_series(
                symbol=series_id,
                provider="fred",
            )
            df = result.to_dataframe()
            if not df.empty:
                latest = df.iloc[-1]
                val = latest.iloc[0] if len(latest) > 0 else "N/A"
                if isinstance(val, (int, float)):
                    print(f"  {label:20s}: {val:.3f}%")
        except Exception:
            print(f"  {label:20s}: N/A (requires FRED API key)")
            break
    print()


def section_unemployment(obb, country):
    """Unemployment rate."""
    print("## 👥 Unemployment")
    print()

    providers = ["fred", "oecd"]
    df = None
    for provider in providers:
        try:
            result = obb.economy.unemployment(
                country=country,
                provider=provider,
            )
            df = result.to_dataframe()
            if not df.empty:
                break
        except Exception:
            continue

    if df is None or df.empty:
        print("  Unemployment data requires FRED API key or OECD access.")
        print("  Set key: obb.user.credentials['fred_api_key'] = 'YOUR_KEY'")
        print()
        return

    recent = df.tail(12)
    val_col = "value" if "value" in df.columns else df.columns[0]
    for idx, row in recent.iterrows():
        date = str(idx)[:7]
        val = row[val_col] if val_col in row.index else None
        if isinstance(val, (int, float)):
            # OECD returns as decimal (0.043 = 4.3%), FRED returns as percentage
            display_val = val * 100 if abs(val) < 1 else val
            print(f"  {date}: {display_val:.1f}%")
    print()


def section_fred(obb, series_id):
    """Query a specific FRED series."""
    print(f"## 📊 FRED Series: {series_id}")
    print()
    try:
        # First search for the series name
        try:
            search = obb.economy.fred_search(query=series_id, provider="fred")
            sdf = search.to_dataframe()
            if not sdf.empty:
                title = sdf.iloc[0].get("title", series_id)
                print(f"  {title}")
                print()
        except Exception:
            pass

        result = obb.economy.fred_series(
            symbol=series_id,
            provider="fred",
        )
        df = result.to_dataframe()
        if df.empty:
            print("  No data available. Requires FRED API key.")
            print()
            return

        recent = df.tail(12)
        for idx, row in recent.iterrows():
            date = str(idx)[:10]
            val = row.iloc[0] if len(row) > 0 else None
            if isinstance(val, (int, float)):
                print(f"  {date}: {val:,.4f}")
    except Exception as e:
        print(f"  FRED error: {e}")
        print("  Note: FRED data requires an API key. Set it via:")
        print('  obb.user.credentials["fred_api_key"] = "YOUR_KEY"')
    print()


def section_market_summary(obb):
    """Quick market index summary as context."""
    print("## 🌍 Market Context")
    print()
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^VIX": "VIX (Fear Index)",
    }

    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    for symbol, name in indices.items():
        try:
            result = obb.equity.price.historical(symbol, start_date=start, provider="yfinance")
            df = result.to_dataframe()
            if not df.empty and len(df) >= 2:
                price = df.iloc[-1]["close"]
                prev = df.iloc[-2]["close"]
                change = ((price - prev) / prev) * 100
                arrow = "📈" if change > 0 else "📉"
                print(f"  {name:15s}: {price:>10,.2f}  {arrow} {change:+.2f}%")
        except Exception:
            print(f"  {name:15s}: N/A")
    print()


def main():
    parser = argparse.ArgumentParser(description="Economic Briefing")
    parser.add_argument("--cpi", action="store_true", help="CPI data")
    parser.add_argument("--gdp", action="store_true", help="GDP data")
    parser.add_argument("--rates", action="store_true", help="Interest rates")
    parser.add_argument("--unemployment", action="store_true", help="Unemployment")
    parser.add_argument("--fred", type=str, help="FRED series ID")
    parser.add_argument("--all", action="store_true", help="All indicators")
    parser.add_argument("--country", "-c", default="united_states", help="Country")
    parser.add_argument("--no-market", action="store_true", help="Skip market context")
    args = parser.parse_args()

    obb = get_obb()

    print(f"🏛️ Economic Briefing — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 60}")
    print(f"Country: {args.country.replace('_', ' ').title()}")
    print()

    # Default to --all if nothing specified
    show_all = args.all or not (args.cpi or args.gdp or args.rates or args.unemployment or args.fred)

    if not args.no_market:
        section_market_summary(obb)

    if show_all or args.cpi:
        section_cpi(obb, args.country)

    if show_all or args.gdp:
        section_gdp(obb, args.country)

    if show_all or args.rates:
        section_interest_rates(obb, args.country)

    if show_all or args.unemployment:
        section_unemployment(obb, args.country)

    if args.fred:
        section_fred(obb, args.fred)

    print("---")
    print("Data sources: OECD, FRED, Yahoo Finance (via OpenBB)")
    print("Note: Some data requires API keys for premium providers.")


if __name__ == "__main__":
    main()
