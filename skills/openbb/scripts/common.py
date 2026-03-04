"""Shared utilities for OpenBB skill scripts."""

import sys


def get_obb():
    """Import and return the OpenBB SDK, or exit with a helpful message."""
    try:
        from openbb import obb
        return obb
    except ImportError:
        print("Error: openbb not installed. Run: pip install openbb", file=sys.stderr)
        sys.exit(1)


def format_change(pct: float) -> str:
    """Format a percentage change with trend emoji."""
    if pct > 0:
        return f"📈 +{pct:.2f}%"
    elif pct < 0:
        return f"📉 {pct:.2f}%"
    return f"➡️ {pct:.2f}%"


def format_number(n) -> str:
    """Format a number with K/M/B/T suffixes."""
    if n is None or (isinstance(n, float) and str(n) == "nan"):
        return "N/A"
    if isinstance(n, str):
        return n
    abs_n = abs(n)
    if abs_n >= 1e12:
        return f"${n / 1e12:.2f}T"
    if abs_n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if abs_n >= 1e6:
        return f"${n / 1e6:.1f}M"
    if abs_n >= 1e3:
        return f"${n / 1e3:.1f}K"
    return f"${n:,.2f}"


def format_volume(n) -> str:
    """Format volume without dollar sign."""
    if n is None:
        return "N/A"
    abs_n = abs(n)
    if abs_n >= 1e9:
        return f"{n / 1e9:.1f}B"
    if abs_n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if abs_n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:,.0f}"


def safe_get(df, col: str, row: int = 0, default="N/A"):
    """Safely extract a value from a DataFrame cell."""
    try:
        if col in df.columns and len(df) > row:
            val = df.iloc[row][col]
            if val is not None and str(val) != "nan":
                return val
    except Exception:
        pass
    return default


def pct_change(current: float, previous: float) -> float:
    """Calculate percentage change, safe against division by zero."""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100
