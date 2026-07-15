from __future__ import annotations

import json
import sqlite3

from crypto_intel.domain.models import NewsEvent


class EventRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save_many(self, events: list[NewsEvent]) -> None:
        self.conn.executemany(
            """
            INSERT INTO news_events (
                title, summary, event_time, source_name, source_url,
                affected_assets_json, impact_direction, short_term_impact,
                medium_term_impact, confidence, classification, evidence_json,
                topic, importance, quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.title,
                    item.summary,
                    item.event_time.isoformat(),
                    item.source_name,
                    item.source_url,
                    json.dumps(item.affected_assets, ensure_ascii=False),
                    item.impact_direction.value,
                    item.short_term_impact,
                    item.medium_term_impact,
                    item.confidence,
                    item.classification.value,
                    json.dumps(item.evidence, ensure_ascii=False),
                    item.topic,
                    item.importance,
                    item.quality_score,
                )
                for item in events
            ],
        )
        self.conn.commit()

