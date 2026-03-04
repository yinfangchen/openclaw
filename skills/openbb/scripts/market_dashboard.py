#!/usr/bin/env python3
"""Market Dashboard — watchlist quotes, day ranges, and top movers."""

import argparse
from datetime import datetime, timedelta

from common import get_obb, format_change, format_volume, pct_change


def fetch_watchlist(obb, symbols: list[str], provider: str, days: int) -> list[dict]:
    """Fetch historical data and compute daily + N-day performance for each symbol."""
    start = (datetime.now() - timedelta(days=max(days + 5, 10))).strftime("%Y-%m-%d")
    results = []

    for symbol in symbols:
        try:
            df = obb.equity.price.historical(symbol, start_date=start, provider=provider).to_dataframe()
            if df.empty:
                results.append({"symbol": symbol, "error": "No data"})
                continue

            latest = df.iloc[-1]
            price = latest["close"]

            daily = pct_change(price, df.iloc[-2]["close"]) if len(df) >= 2 else 0.0
            lookback = min(days, len(df) - 1)
            period = pct_change(price, df.iloc[-(lookback + 1)]["close"]) if lookback > 0 else 0.0

            results.append({
                "symbol": symbol,
                "price": price,
                "daily_change": daily,
                "period_change": period,
                "volume": latest.get("volume", 0),
                "high": latest.get("high", price),
                "low": latest.get("low", price),
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    return results


def fetch_movers(obb, provider: str) -> tuple[list[dict], list[dict]]:
    """Fetch top gainers and losers (requires providers like FMP)."""
    def extract(fn):
        try:
            df = fn(provider=provider).to_dataframe()
            return [
                {
                    "symbol": row.get("symbol", "?"),
                    "price": row.get("price", row.get("last_price", 0)),
                    "change": row.get("change_percent", row.get("percent_change", 0)),
                }
                for _, row in df.head(5).iterrows()
            ] if not df.empty else []
        except Exception:
            return []

    return extract(obb.equity.discovery.gainers), extract(obb.equity.discovery.losers)


def render(results: list[dict], days: int, movers: tuple | None = None):
    """Print the formatted dashboard."""
    print(f"📊 Market Dashboard — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # — Watchlist
    print("\n## Watchlist\n")
    for r in results:
        if "error" in r:
            print(f"  ⚠️  {r['symbol']}: {r['error']}")
            continue
        print(
            f"  {r['symbol']:8s}"
            f"  $ {r['price']:>9.2f}"
            f"  {format_change(r['daily_change']):16s}"
            f"  {days}d: {format_change(r['period_change']):16s}"
            f"  Vol: {format_volume(r['volume'])}"
        )

    # — Day ranges
    print("\n## Day Ranges\n")
    for r in results:
        if "error" in r:
            continue
        lo, hi, price = r["low"], r["high"], r["price"]
        if hi > lo:
            pos = int((price - lo) / (hi - lo) * 20)
            bar = "░" * pos + "█" + "░" * (19 - pos)
            print(f"  {r['symbol']:8s}  ${lo:.2f} [{bar}] ${hi:.2f}")
        else:
            print(f"  {r['symbol']:8s}  ${lo:.2f} — ${hi:.2f}")

    # — Movers
    if movers:
        gainers, losers = movers
        if gainers:
            print("\n## 🟢 Top Gainers\n")
            for g in gainers:
                print(f"  {g['symbol']:8s}  ${g['price']:>8.2f}  📈 +{abs(g['change']):.2f}%")
        if losers:
            print("\n## 🔴 Top Losers\n")
            for l in losers:
                print(f"  {l['symbol']:8s}  ${l['price']:>8.2f}  📉 -{abs(l['change']):.2f}%")
        if not gainers and not losers:
            print("\n## Movers: requires premium provider (e.g. FMP)")

    print()


def main():
    p = argparse.ArgumentParser(description="Market Dashboard")
    p.add_argument("--symbols", "-s", default="AAPL,MSFT,GOOGL,AMZN,NVDA")
    p.add_argument("--movers", "-m", action="store_true")
    p.add_argument("--days", "-d", type=int, default=5)
    p.add_argument("--provider", "-p", default="yfinance")
    args = p.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",")]
    obb = get_obb()

    results = fetch_watchlist(obb, symbols, args.provider, args.days)
    movers = fetch_movers(obb, args.provider) if args.movers else None
    render(results, args.days, movers)


if __name__ == "__main__":
    main()
