from __future__ import annotations

import json
import sqlite3

from crypto_intel.domain.models import MarketSnapshot


class MarketRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save_many(self, snapshots: list[MarketSnapshot]) -> None:
        self.conn.executemany(
            """
            INSERT INTO market_snapshots (
                symbol, quote_currency, price, market_cap, volume_24h,
                change_24h_pct, change_7d_pct, observed_at, provider,
                source_url, inferred, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.symbol,
                    item.quote_currency,
                    item.price,
                    item.market_cap,
                    item.volume_24h,
                    item.change_24h_pct,
                    item.change_7d_pct,
                    item.observed_at.isoformat(),
                    item.provider,
                    item.source_url,
                    int(item.inferred),
                    json.dumps(item.raw, ensure_ascii=False),
                )
                for item in snapshots
            ],
        )
        self.conn.commit()

