from __future__ import annotations

import hashlib
import re

from crypto_intel.domain.models import NewsEvent


def deduplicate_events(events: list[NewsEvent]) -> list[NewsEvent]:
    seen: set[str] = set()
    unique: list[NewsEvent] = []
    for event in events:
        key = _canonical_key(event)
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return unique


def _canonical_key(event: NewsEvent) -> str:
    if event.source_url and not event.source_url.startswith("fixture://"):
        return event.source_url.rstrip("/")
    normalized = re.sub(r"\W+", " ", event.title.lower()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

