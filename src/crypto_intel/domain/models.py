from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from crypto_intel.domain.enums import EventClassification, ImpactDirection, ProviderStatus


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class SourceRef:
    name: str
    url: str
    fetched_at: datetime
    provider: str

    def to_dict(self) -> JsonObject:
        item = asdict(self)
        item["fetched_at"] = self.fetched_at.isoformat()
        return item


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    quote_currency: str
    price: float
    market_cap: float | None
    volume_24h: float | None
    change_24h_pct: float | None
    change_7d_pct: float | None
    observed_at: datetime
    provider: str
    source_url: str
    raw: JsonObject = field(default_factory=dict)
    inferred: bool = False

    def to_dict(self) -> JsonObject:
        item = asdict(self)
        item["observed_at"] = self.observed_at.isoformat()
        return item


@dataclass(frozen=True)
class MarketBundle:
    btc_usd: MarketSnapshot | None
    btc_twd: MarketSnapshot | None
    usdt_usd: MarketSnapshot | None
    btc_dominance: float | None
    usdt_depeg: float | None
    provider_status: ProviderStatus
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonObject:
        return {
            "btc_usd": self.btc_usd.to_dict() if self.btc_usd else None,
            "btc_twd": self.btc_twd.to_dict() if self.btc_twd else None,
            "usdt_usd": self.usdt_usd.to_dict() if self.usdt_usd else None,
            "btc_dominance": self.btc_dominance,
            "usdt_depeg": self.usdt_depeg,
            "provider_status": self.provider_status.value,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class NewsEvent:
    title: str
    summary: str
    event_time: datetime
    source_name: str
    source_url: str
    affected_assets: list[str]
    impact_direction: ImpactDirection
    short_term_impact: str
    medium_term_impact: str
    confidence: float
    classification: EventClassification
    evidence: list[str]
    topic: str
    importance: float
    quality_score: int

    def to_dict(self) -> JsonObject:
        item = asdict(self)
        item["event_time"] = self.event_time.isoformat()
        item["impact_direction"] = self.impact_direction.value
        item["classification"] = self.classification.value
        return item


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    status: ProviderStatus
    checked_at: datetime
    latency_ms: int | None = None
    error: str | None = None

    def to_dict(self) -> JsonObject:
        item = asdict(self)
        item["status"] = self.status.value
        item["checked_at"] = self.checked_at.isoformat()
        return item


@dataclass(frozen=True)
class ReportMetadata:
    report_date: str
    timezone: str
    generated_at: datetime
    html_path: str
    pdf_path: str | None
    json_path: str
    deep_analysis: bool
    dry_run: bool
    warnings: list[str]

    def to_dict(self) -> JsonObject:
        item = asdict(self)
        item["generated_at"] = self.generated_at.isoformat()
        return item

