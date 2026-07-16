from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from crypto_intel.domain.enums import EventClassification
from crypto_intel.domain.models import NewsEvent


@dataclass(frozen=True)
class SourceProfile:
    domain: str
    name: str
    source_url: str
    tier: str
    source_type: str
    quality_score: int
    confidence: float
    claim_scope: str
    requires_confirmation: bool = False
    conflict_note: str | None = None

    @property
    def verification_status(self) -> str:
        if self.source_type in {"official_primary", "developer_primary"}:
            return "primary_source"
        if self.source_type == "project_primary":
            return "issuer_statement"
        if self.requires_confirmation:
            return "requires_confirmation"
        return "unknown_source"


DEFAULT_SOURCE_PROFILES = {
    "www.sec.gov": SourceProfile(
        domain="www.sec.gov",
        name="U.S. SEC",
        source_url="https://www.sec.gov/news/pressreleases.rss",
        tier="T1",
        source_type="official_primary",
        quality_score=96,
        confidence=0.90,
        claim_scope="Only confirms official SEC actions, releases, and statements.",
    ),
    "www.cftc.gov": SourceProfile(
        domain="www.cftc.gov",
        name="U.S. CFTC",
        source_url="https://www.cftc.gov/RSS/RSSGP/rssgp.xml",
        tier="T1",
        source_type="official_primary",
        quality_score=96,
        confidence=0.90,
        claim_scope="Only confirms official CFTC actions, releases, and statements.",
    ),
    "blog.chain.link": SourceProfile(
        domain="blog.chain.link",
        name="Chainlink Blog",
        source_url="https://blog.chain.link/rss/",
        tier="T2",
        source_type="project_primary",
        quality_score=78,
        confidence=0.76,
        claim_scope="Only confirms Chainlink's own announcements and stated positions.",
        conflict_note="Project-operated source; not independent market evidence.",
    ),
    "www.coindesk.com": SourceProfile(
        domain="www.coindesk.com",
        name="CoinDesk",
        source_url="https://www.coindesk.com/arc/outboundfeeds/rss/",
        tier="T3",
        source_type="specialist_media",
        quality_score=64,
        confidence=0.58,
        claim_scope="Use for discovery and context; material claims require corroboration.",
        requires_confirmation=True,
        conflict_note="Publisher discloses ownership by Bullish; related coverage requires extra care.",
    ),
    "cointelegraph.com": SourceProfile(
        domain="cointelegraph.com",
        name="Cointelegraph",
        source_url="https://cointelegraph.com/rss",
        tier="T3",
        source_type="specialist_media",
        quality_score=60,
        confidence=0.55,
        claim_scope="Use for discovery and context; material claims require corroboration.",
        requires_confirmation=True,
    ),
    "www.theblock.co": SourceProfile(
        domain="www.theblock.co",
        name="The Block",
        source_url="https://www.theblock.co/rss.xml",
        tier="T3",
        source_type="specialist_media",
        quality_score=63,
        confidence=0.57,
        claim_scope="Use for discovery and context; material claims require corroboration.",
        requires_confirmation=True,
        conflict_note="Crypto specialist media; historical ownership/funding concerns require source cross-checks.",
    ),
    "bitcoinmagazine.com": SourceProfile(
        domain="bitcoinmagazine.com",
        name="Bitcoin Magazine",
        source_url="https://bitcoinmagazine.com/.rss/full/",
        tier="T3",
        source_type="specialist_media",
        quality_score=58,
        confidence=0.53,
        claim_scope="Use for Bitcoin-focused discovery and context; material claims require corroboration.",
        requires_confirmation=True,
        conflict_note="Bitcoin-focused editorial source; broader market claims should be checked against independent sources.",
    ),
    "coinmarketcap.com": SourceProfile(
        domain="coinmarketcap.com",
        name="CoinMarketCap",
        source_url="https://coinmarketcap.com/",
        tier="T3",
        source_type="market_data_media",
        quality_score=62,
        confidence=0.56,
        claim_scope="Use for market-data context and news discovery; material claims require corroboration.",
        requires_confirmation=True,
        conflict_note="Market-data platform owned by Binance; exchange-related or listing-related claims require extra care.",
    ),
    "bitcointalk.org": SourceProfile(
        domain="bitcointalk.org",
        name="Bitcointalk",
        source_url="https://bitcointalk.org/",
        tier="T4",
        source_type="community_forum",
        quality_score=42,
        confidence=0.35,
        claim_scope="Use only as community signal or early lead; never as confirmation of facts or market impact.",
        requires_confirmation=True,
        conflict_note="Open forum with pseudonymous posts; high noise and unverifiable claims are expected.",
    ),
    "github.com": SourceProfile(
        domain="github.com",
        name="Bitcoin Core GitHub",
        source_url="https://github.com/bitcoin/bitcoin/releases.atom",
        tier="T2",
        source_type="developer_primary",
        quality_score=86,
        confidence=0.82,
        claim_scope="Confirms Bitcoin Core repository releases and code activity only; it does not prove market impact.",
        conflict_note="Developer primary source; interpret technical changes separately from market narratives.",
    ),
    "www.reddit.com": SourceProfile(
        domain="www.reddit.com",
        name="Reddit Crypto Communities",
        source_url="https://www.reddit.com/r/CryptoCurrency/.rss",
        tier="T4",
        source_type="community_signal",
        quality_score=40,
        confidence=0.32,
        claim_scope="Use for community attention and sentiment clues only; all claims require independent confirmation.",
        requires_confirmation=True,
        conflict_note="User-generated and moderation-dependent content; susceptible to rumor, promotion, and brigading.",
    ),
    "nostr.com": SourceProfile(
        domain="nostr.com",
        name="Nostr",
        source_url="https://nostr.com/",
        tier="T4",
        source_type="community_protocol",
        quality_score=38,
        confidence=0.30,
        claim_scope="Use as a protocol/community reference point only; individual claims require independent sources.",
        requires_confirmation=True,
        conflict_note="Protocol landing page, not a curated news source; event-level evidence should come from specific relays or authors.",
    ),
}


def profile_for_url(url: str, overrides: dict | None = None) -> SourceProfile:
    domain = (urlparse(url).netloc or "").lower().removeprefix("www.")
    profiles = _profiles_with_overrides(overrides)
    if domain in profiles:
        return profiles[domain]
    return SourceProfile(
        domain=domain or "unknown",
        name=domain or "Unknown source",
        source_url=url,
        tier="T4",
        source_type="unverified",
        quality_score=35,
        confidence=0.30,
        claim_scope="Source is not in the approved registry; do not use as confirmed evidence.",
        requires_confirmation=True,
        conflict_note="Unreviewed source.",
    )


def govern_event(event: NewsEvent, overrides: dict | None = None) -> NewsEvent:
    profile = profile_for_url(event.source_url, overrides)
    classification = event.classification
    if profile.requires_confirmation:
        classification = EventClassification.INFERENCE
    return NewsEvent(
        title=event.title,
        summary=event.summary,
        event_time=event.event_time,
        source_name=profile.name,
        source_url=event.source_url,
        affected_assets=event.affected_assets,
        impact_direction=event.impact_direction,
        short_term_impact=event.short_term_impact,
        medium_term_impact=event.medium_term_impact,
        confidence=min(event.confidence, profile.confidence),
        classification=classification,
        evidence=event.evidence,
        topic=event.topic,
        importance=event.importance,
        quality_score=profile.quality_score,
    )


def event_governance(event: NewsEvent, overrides: dict | None = None) -> dict[str, str | bool | None]:
    profile = profile_for_url(event.source_url, overrides)
    return {
        "tier": profile.tier,
        "source_type": profile.source_type,
        "claim_scope": profile.claim_scope,
        "verification_status": profile.verification_status,
        "requires_confirmation": profile.requires_confirmation,
        "conflict_note": profile.conflict_note,
    }


def approved_source_profiles(overrides: dict | None = None) -> list[SourceProfile]:
    return sorted(_profiles_with_overrides(overrides).values(), key=lambda profile: (profile.tier, profile.name))


def _profiles_with_overrides(overrides: dict | None) -> dict[str, SourceProfile]:
    profiles = {domain.removeprefix("www."): profile for domain, profile in DEFAULT_SOURCE_PROFILES.items()}
    for domain, values in (overrides or {}).items():
        if not isinstance(values, dict):
            continue
        key = str(domain).lower().removeprefix("www.")
        base = profiles.get(key)
        if base is None:
            base = SourceProfile(key, key, f"https://{key}", "T4", "unverified", 35, 0.30, "Unreviewed source.", True)
        profiles[key] = SourceProfile(
            domain=key,
            name=str(values.get("name", base.name)),
            source_url=str(values.get("source_url", base.source_url)),
            tier=str(values.get("tier", base.tier)),
            source_type=str(values.get("source_type", base.source_type)),
            quality_score=int(values.get("quality_score", base.quality_score)),
            confidence=float(values.get("confidence", base.confidence)),
            claim_scope=str(values.get("claim_scope", base.claim_scope)),
            requires_confirmation=bool(values.get("requires_confirmation", base.requires_confirmation)),
            conflict_note=values.get("conflict_note", base.conflict_note),
        )
    return profiles
