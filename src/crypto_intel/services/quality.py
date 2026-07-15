from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from crypto_intel.domain.models import MarketBundle, NewsEvent


def market_warnings(bundle: MarketBundle) -> list[str]:
    warnings = list(bundle.warnings)
    if bundle.btc_usd is None:
        warnings.append("Missing BTC/USD.")
    elif bundle.btc_usd.price <= 0:
        warnings.append("Invalid BTC/USD price.")
    if bundle.usdt_usd is None:
        warnings.append("Missing USDT/USD.")
    elif abs(bundle.usdt_usd.price - 1.0) > 0.05:
        warnings.append("Critical USDT depeg greater than 5%.")
    return warnings


def single_domain_ratio(events: list[NewsEvent]) -> float:
    if not events:
        return 0.0
    domains = [urlparse(event.source_url).netloc or event.source_name for event in events]
    return Counter(domains).most_common(1)[0][1] / len(events)

