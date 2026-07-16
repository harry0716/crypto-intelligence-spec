from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from crypto_intel.domain.enums import EventClassification, ImpactDirection
from crypto_intel.domain.models import NewsEvent
from crypto_intel.services.source_governance import govern_event


DEFAULT_FEEDS = [
    "https://www.sec.gov/news/pressreleases.rss",
    "https://www.cftc.gov/RSS/RSSGP/rssgp.xml",
    "https://blog.chain.link/rss/",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.theblock.co/rss.xml",
    "https://bitcoinmagazine.com/.rss/full/",
    "https://github.com/bitcoin/bitcoin/releases.atom",
    "https://www.reddit.com/r/CryptoCurrency/.rss",
    "https://www.reddit.com/r/Bitcoin/.rss",
]


class RssNewsProvider:
    name = "rss"

    def __init__(self, feeds: list[str] | None = None, source_registry: dict | None = None) -> None:
        self.feeds = feeds or DEFAULT_FEEDS
        self.source_registry = source_registry or {}

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
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")[:20]
        events: list[NewsEvent] = []
        for item in items:
            title = _entry_text(item, "title")
            link = _entry_link(item) or feed
            summary = html.unescape(_entry_text(item, "description") or _entry_text(item, "summary") or _entry_text(item, "content"))[:500]
            event_time = _parse_time(_entry_text(item, "pubDate") or _entry_text(item, "published") or _entry_text(item, "updated"))
            events.append(
                govern_event(
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
                    confidence=0.95,
                    classification=EventClassification.FACT,
                    evidence=[link],
                    topic=_topic_for(title + " " + summary),
                    importance=0.5,
                    quality_score=75,
                    ),
                    self.source_registry,
                )
            )
        return events


def _text(item: ET.Element, tag: str) -> str:
    found = item.find(tag)
    return (found.text or "").strip() if found is not None else ""


def _entry_text(item: ET.Element, tag: str) -> str:
    return _text(item, tag) or _text(item, f"{{http://www.w3.org/2005/Atom}}{tag}")


def _entry_link(item: ET.Element) -> str:
    direct = _entry_text(item, "link")
    if direct:
        return direct
    atom_link = item.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None:
        return (atom_link.attrib.get("href") or "").strip()
    return ""


def _parse_time(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
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
    return assets


def _topic_for(text: str) -> str:
    lowered = text.lower()
    if "sec" in lowered or "cftc" in lowered or "regulat" in lowered:
        return "Regulation"
    if "stablecoin" in lowered or "usdt" in lowered:
        return "Stablecoin"
    if "security" in lowered or "hack" in lowered:
        return "Security"
    if "etf" in lowered:
        return "ETF"
    return "Market"
