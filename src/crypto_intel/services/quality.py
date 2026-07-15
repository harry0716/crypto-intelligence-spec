from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from crypto_intel.domain.models import MarketBundle, NewsEvent
from crypto_intel.services.source_governance import event_governance


def market_warnings(bundle: MarketBundle) -> list[str]:
    warnings = list(bundle.warnings)
    if bundle.btc_usd is None:
        warnings.append("缺少 BTC/USD 市場資料。")
    elif bundle.btc_usd.price <= 0:
        warnings.append("BTC/USD 價格無效。")
    if bundle.usdt_usd is None:
        warnings.append("缺少 USDT/USD 市場資料。")
    elif abs(bundle.usdt_usd.price - 1.0) > 0.05:
        warnings.append("USDT 偏離 1 美元超過 5%，屬重大風險訊號。")
    return warnings


def single_domain_ratio(events: list[NewsEvent]) -> float:
    if not events:
        return 0.0
    domains = [urlparse(event.source_url).netloc or event.source_name for event in events]
    return Counter(domains).most_common(1)[0][1] / len(events)


def source_diversity(events: list[NewsEvent]) -> dict[str, int | float | str | None]:
    if not events:
        return {
            "independent_sources": 0,
            "largest_source": None,
            "largest_source_share": 0.0,
            "primary_source_events": 0,
            "requires_confirmation_events": 0,
        }
    domains = [urlparse(event.source_url).netloc or event.source_name for event in events]
    counts = Counter(domains)
    largest_source, largest_count = counts.most_common(1)[0]
    return {
        "independent_sources": len(counts),
        "largest_source": largest_source,
        "largest_source_share": round(largest_count / len(events), 4),
        "primary_source_events": sum(
            event_governance(event)["verification_status"] == "primary_source" for event in events
        ),
        "requires_confirmation_events": sum(
            bool(event_governance(event)["requires_confirmation"]) for event in events
        ),
    }
