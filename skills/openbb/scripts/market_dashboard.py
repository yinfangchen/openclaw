#!/usr/bin/env python3
"""Feature 1: Market Dashboard — watchlist quotes, movers, and price snapshots."""

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


def format_change(change_pct):
    """Format a percentage change with emoji."""
    if change_pct > 0:
        return f"📈 +{change_pct:.2f}%"
    elif change_pct < 0:
        return f"📉 {change_pct:.2f}%"
    else:
        return f"➡️ {change_pct:.2f}%"


def format_number(n):
    """Format large numbers with K/M/B suffixes."""
    if n is None:
        return "N/A"
    if abs(n) >= 1e9:
        return f"{n/1e9:.1f}B"
    elif abs(n) >= 1e6:
        return f"{n/1e6:.1f}M"
    elif abs(n) >= 1e3:
        return f"{n/1e3:.1f}K"
    return f"{n:,.0f}"


def get_watchlist(obb, symbols, provider, days):
    """Get quotes and performance for a watchlist."""
    start = (datetime.now() - timedelta(days=max(days + 5, 10))).strftime("%Y-%m-%d")
    results = []

    for symbol in symbols:
        try:
            hist = obb.equity.price.historical(
                symbol, start_date=start, provider=provider
            )
            df = hist.to_dataframe()
            if df.empty:
                results.append({"symbol": symbol, "error": "No data"})
                continue

            latest = df.iloc[-1]
            price = latest["close"]
            volume = latest.get("volume", 0)

            # Calculate changes
            if len(df) >= 2:
                prev = df.iloc[-2]
                daily_change = ((price - prev["close"]) / prev["close"]) * 100
            else:
                daily_change = 0.0

            # N-day performance
            lookback_idx = min(days, len(df) - 1)
            if lookback_idx > 0:
                period_start_price = df.iloc[-(lookback_idx + 1)]["close"]
                period_change = ((price - period_start_price) / period_start_price) * 100
            else:
                period_change = 0.0

            # 52-week high/low approximation from available data
            high_52w = df["high"].max()
            low_52w = df["low"].min()

            results.append({
                "symbol": symbol,
                "price": price,
                "daily_change": daily_change,
                "period_change": period_change,
                "volume": volume,
                "high": latest.get("high", price),
                "low": latest.get("low", price),
                "high_period": high_52w,
                "low_period": low_52w,
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    return results


def get_movers(obb, provider):
    """Get top gainers and losers."""
    gainers = []
    losers = []

    try:
        g = obb.equity.discovery.gainers(provider=provider)
        df = g.to_dataframe()
        if not df.empty:
            for _, row in df.head(5).iterrows():
                gainers.append({
                    "symbol": row.get("symbol", "?"),
                    "price": row.get("price", row.get("last_price", 0)),
                    "change": row.get("change_percent", row.get("percent_change", 0)),
                })
    except Exception:
        pass

    try:
        l = obb.equity.discovery.losers(provider=provider)
        df = l.to_dataframe()
        if not df.empty:
            for _, row in df.head(5).iterrows():
                losers.append({
                    "symbol": row.get("symbol", "?"),
                    "price": row.get("price", row.get("last_price", 0)),
                    "change": row.get("change_percent", row.get("percent_change", 0)),
                })
    except Exception:
        pass

    return gainers, losers


def print_dashboard(results, days, show_movers=False, gainers=None, losers=None):
    """Print formatted market dashboard."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"📊 Market Dashboard — {now}")
    print(f"{'=' * 60}")
    print()

    # Watchlist
    print("## Watchlist")
    print()
    for r in results:
        if "error" in r:
            print(f"  ⚠️  {r['symbol']}: {r['error']}")
            continue

        sym = r["symbol"]
        price = r["price"]
        daily = format_change(r["daily_change"])
        period = format_change(r["period_change"])
        vol = format_number(r["volume"])

        print(f"  {sym:8s}  ${price:>10.2f}  {daily:16s}  {days}d: {period:16s}  Vol: {vol}")

    print()

    # Day range summary
    print("## Day Ranges")
    print()
    for r in results:
        if "error" in r:
            continue
        sym = r["symbol"]
        lo = r["low"]
        hi = r["high"]
        price = r["price"]
        # Visual position in range
        if hi > lo:
            pos = (price - lo) / (hi - lo)
            bar_len = 20
            filled = int(pos * bar_len)
            bar = "░" * filled + "█" + "░" * (bar_len - filled - 1)
            print(f"  {sym:8s}  ${lo:.2f} [{bar}] ${hi:.2f}")
        else:
            print(f"  {sym:8s}  ${lo:.2f} — ${hi:.2f}")
    print()

    # Movers
    if show_movers:
        if gainers:
            print("## 🟢 Top Gainers")
            print()
            for g in gainers:
                print(f"  {g['symbol']:8s}  ${g['price']:>8.2f}  📈 +{abs(g['change']):.2f}%")
            print()

        if losers:
            print("## 🔴 Top Losers")
            print()
            for l in losers:
                print(f"  {l['symbol']:8s}  ${l['price']:>8.2f}  📉 -{abs(l['change']):.2f}%")
            print()

        if not gainers and not losers:
            print("## Movers: Data unavailable (may require premium provider like FMP)")
            print()


def main():
    parser = argparse.ArgumentParser(description="Market Dashboard")
    parser.add_argument("--symbols", "-s", default="AAPL,MSFT,GOOGL,AMZN,NVDA",
                        help="Comma-separated symbols")
    parser.add_argument("--movers", "-m", action="store_true", help="Show top gainers/losers")
    parser.add_argument("--days", "-d", type=int, default=5, help="Lookback days for performance")
    parser.add_argument("--provider", "-p", default="yfinance", help="Data provider")
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",")]
    obb = get_obb()

    results = get_watchlist(obb, symbols, args.provider, args.days)

    gainers, losers = None, None
    if args.movers:
        gainers, losers = get_movers(obb, args.provider)

    print_dashboard(results, args.days, args.movers, gainers, losers)


if __name__ == "__main__":
    main()
