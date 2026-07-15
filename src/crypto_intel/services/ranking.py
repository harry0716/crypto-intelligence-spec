from __future__ import annotations

from dataclasses import replace

from crypto_intel.domain.enums import EventClassification
from crypto_intel.domain.models import NewsEvent


TOPIC_WEIGHTS = {
    "Regulation": 0.90,
    "Security": 0.88,
    "ETF": 0.82,
    "Stablecoin": 0.80,
    "Exchange": 0.74,
    "RWA": 0.66,
    "Derivatives": 0.62,
    "Macro": 0.60,
    "BTC": 0.58,
    "GitHub": 0.42,
    "Market": 0.50,
}


def rank_events(events: list[NewsEvent], limit: int = 10) -> list[NewsEvent]:
    scored = [replace(event, importance=_score(event)) for event in events]
    return sorted(scored, key=lambda item: (item.importance, item.confidence, item.quality_score), reverse=True)[:limit]


def _score(event: NewsEvent) -> float:
    source_credibility = event.quality_score / 100
    market_relevance = 0.9 if {"BTC", "USDT"} & set(event.affected_assets) else 0.4
    regulatory_impact = 1.0 if event.topic == "Regulation" else 0.2
    security_impact = 1.0 if event.topic == "Security" else 0.2
    novelty = TOPIC_WEIGHTS.get(event.topic, 0.5)
    social_velocity = 0.3
    classification_penalty = 0.85 if event.classification == EventClassification.RUMOR else 1.0
    score = (
        source_credibility * 0.25
        + market_relevance * 0.25
        + regulatory_impact * 0.15
        + security_impact * 0.15
        + novelty * 0.10
        + social_velocity * 0.10
    )
    return round(score * classification_penalty, 4)

