from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from crypto_intel.domain.enums import EventClassification, ImpactDirection
from crypto_intel.domain.models import NewsEvent


DEFAULT_FEEDS = [
    "https://www.sec.gov/news/pressreleases.rss",
    "https://blog.chain.link/rss/",
]


class RssNewsProvider:
    name = "rss"

    def __init__(self, feeds: list[str] | None = None) -> None:
        self.feeds = feeds or DEFAULT_FEEDS

    def fetch_events(self) -> list[NewsEvent]:
        events: list[NewsEvent] = []
        for feed in self.feeds:
            try:
                events.extend(self._fetch_feed(feed))
            except Exception:
                continue
        return events

    def _fetch_feed(self, feed: str) -> list[NewsEvent]:
        req = Request(feed, headers={"User-Agent": "crypto-intelligence-daily/0.1"})
        with urlopen(req, timeout=15) as response:  # noqa: S310 - configured public RSS endpoints.
            xml = response.read()
        root = ET.fromstring(xml)
        source_name = urlparse(feed).netloc or feed
        items = root.findall(".//item")[:20]
        events: list[NewsEvent] = []
        for item in items:
            title = _text(item, "title")
            link = _text(item, "link") or feed
            summary = html.unescape(_text(item, "description"))[:500]
            event_time = _parse_time(_text(item, "pubDate"))
            events.append(
                NewsEvent(
                    title=html.unescape(title),
                    summary=summary,
                    event_time=event_time,
                    source_name=source_name,
                    source_url=link,
                    affected_assets=_assets_for(title + " " + summary),
                    impact_direction=ImpactDirection.NEUTRAL,
                    short_term_impact="需與價格、成交量及官方資料交叉驗證。",
                    medium_term_impact="若事件延續，可能改變風險偏好或合規成本。",
                    confidence=0.65,
                    classification=EventClassification.FACT,
                    evidence=[link],
                    topic=_topic_for(title + " " + summary),
                    importance=0.5,
                    quality_score=75,
                )
            )
        return events


def _text(item: ET.Element, tag: str) -> str:
    found = item.find(tag)
    return (found.text or "").strip() if found is not None else ""


def _parse_time(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _assets_for(text: str) -> list[str]:
    lowered = text.lower()
    assets = []
    if "bitcoin" in lowered or "btc" in lowered:
        assets.append("BTC")
    if "tether" in lowered or "usdt" in lowered or "stablecoin" in lowered:
        assets.append("USDT")
    return assets or ["BTC", "USDT"]


def _topic_for(text: str) -> str:
    lowered = text.lower()
    if "sec" in lowered or "regulat" in lowered:
        return "Regulation"
    if "stablecoin" in lowered or "usdt" in lowered:
        return "Stablecoin"
    if "security" in lowered or "hack" in lowered:
        return "Security"
    if "etf" in lowered:
        return "ETF"
    return "Market"

