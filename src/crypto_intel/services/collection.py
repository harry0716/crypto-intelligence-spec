from __future__ import annotations

import logging
from datetime import datetime, timezone

from crypto_intel.domain.enums import ProviderStatus
from crypto_intel.domain.models import MarketBundle, NewsEvent, ProviderHealth
from crypto_intel.providers.base import MarketProvider, NewsProvider
from crypto_intel.providers.market.static import StaticMarketProvider
from crypto_intel.services.deduplication import deduplicate_events
from crypto_intel.services.ranking import rank_events, select_diverse_events

LOGGER = logging.getLogger(__name__)


class CollectionService:
    def __init__(
        self,
        market_provider: MarketProvider,
        fallback_market_provider: MarketProvider | None,
        news_providers: list[NewsProvider],
    ) -> None:
        self.market_provider = market_provider
        self.fallback_market_provider = fallback_market_provider or StaticMarketProvider()
        self.news_providers = news_providers

    def collect_market(self) -> tuple[MarketBundle, list[ProviderHealth]]:
        started = datetime.now(timezone.utc)
        bundle = self.market_provider.fetch_market_bundle()
        health = [
            ProviderHealth(
                provider=self.market_provider.name,
                status=bundle.provider_status,
                checked_at=started,
                error="; ".join(bundle.warnings) if bundle.provider_status == ProviderStatus.FAILED else None,
            )
        ]
        if bundle.provider_status == ProviderStatus.FAILED:
            LOGGER.warning("Primary market provider failed; using fallback fixture.")
            fallback = self.fallback_market_provider.fetch_market_bundle()
            health.append(
                ProviderHealth(
                    provider=self.fallback_market_provider.name,
                    status=fallback.provider_status,
                    checked_at=datetime.now(timezone.utc),
                    error="; ".join(fallback.warnings),
                )
            )
            return fallback, health
        return bundle, health

    def collect_events(
        self,
        limit: int,
        max_event_age_hours: int | None = None,
        max_per_source: int | None = None,
    ) -> tuple[list[NewsEvent], list[ProviderHealth]]:
        events: list[NewsEvent] = []
        health: list[ProviderHealth] = []
        for provider in self.news_providers:
            checked_at = datetime.now(timezone.utc)
            try:
                provider_events = provider.fetch_events()
                events.extend(provider_events)
                status = ProviderStatus.SUCCESS if provider_events else ProviderStatus.DEGRADED
                error = None if provider_events else "No events returned."
            except Exception as exc:  # noqa: BLE001 - provider boundary records any failure.
                status = ProviderStatus.FAILED
                error = str(exc)
            health.append(ProviderHealth(provider.name, status, checked_at, error=error))
        unique = deduplicate_events(events)
        recent = _recent_events(unique, max_event_age_hours)
        ranked = rank_events(recent, len(recent))
        if max_per_source is not None:
            return select_diverse_events(ranked, limit, max_per_source), health
        return ranked[:limit], health


def _recent_events(events: list[NewsEvent], max_age_hours: int | None) -> list[NewsEvent]:
    if max_age_hours is None:
        return events
    now = datetime.now(timezone.utc)
    return [
        event
        for event in events
        if 0 <= (now - event.event_time.astimezone(timezone.utc)).total_seconds() <= max_age_hours * 3600
    ]
