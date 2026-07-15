from __future__ import annotations

from crypto_intel.domain.models import MarketBundle, MarketSnapshot


def usdt_depeg(price: float) -> float:
    return abs(price - 1.0)


def return_pct(current: float, previous: float) -> float:
    if previous == 0:
        raise ValueError("previous price must not be zero")
    return (current - previous) / previous * 100.0


def exchange_spread_pct(prices: list[float]) -> float:
    if not prices:
        return 0.0
    low = min(prices)
    high = max(prices)
    if low <= 0:
        raise ValueError("prices must be positive")
    return (high - low) / low * 100.0


def snapshots_from_bundle(bundle: MarketBundle) -> list[MarketSnapshot]:
    return [item for item in [bundle.btc_usd, bundle.btc_twd, bundle.usdt_usd] if item is not None]

