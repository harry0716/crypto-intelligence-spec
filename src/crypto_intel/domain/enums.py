from __future__ import annotations

from enum import StrEnum


class ImpactDirection(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EventClassification(StrEnum):
    FACT = "fact"
    INFERENCE = "inference"
    RUMOR = "rumor"


class ProviderStatus(StrEnum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILED = "failed"

