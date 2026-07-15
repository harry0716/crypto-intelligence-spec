from __future__ import annotations

from typing import Protocol

from crypto_intel.domain.models import MarketBundle, NewsEvent


class MarketProvider(Protocol):
    name: str

    def fetch_market_bundle(self) -> MarketBundle:
        ...


class NewsProvider(Protocol):
    name: str

    def fetch_events(self) -> list[NewsEvent]:
        ...

