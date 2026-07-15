from __future__ import annotations

import json
import sqlite3
from datetime import date

from crypto_intel.domain.models import ProviderHealth, ReportMetadata


class ReportRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save_report(self, metadata: ReportMetadata) -> None:
        self.conn.execute(
            """
            INSERT INTO reports (
                report_date, generated_at, timezone, html_path, pdf_path,
                json_path, deep_analysis, dry_run, warnings_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.report_date,
                metadata.generated_at.isoformat(),
                metadata.timezone,
                metadata.html_path,
                metadata.pdf_path,
                metadata.json_path,
                int(metadata.deep_analysis),
                int(metadata.dry_run),
                json.dumps(metadata.warnings, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def save_provider_health(self, items: list[ProviderHealth]) -> None:
        self.conn.executemany(
            """
            INSERT INTO provider_health (provider, status, checked_at, latency_ms, error)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    item.provider,
                    item.status.value,
                    item.checked_at.isoformat(),
                    item.latency_ms,
                    item.error,
                )
                for item in items
            ],
        )
        self.conn.commit()

    def last_deep_analysis_date(self) -> date | None:
        row = self.conn.execute(
            "SELECT report_date FROM reports WHERE deep_analysis = 1 ORDER BY report_date DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return date.fromisoformat(row["report_date"])

    def log_delivery(self, report_date: str, channel: str, status: str, dry_run: bool, message: str) -> None:
        from datetime import datetime, timezone

        self.conn.execute(
            """
            INSERT INTO delivery_logs (report_date, channel, status, dry_run, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (report_date, channel, status, int(dry_run), message, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

