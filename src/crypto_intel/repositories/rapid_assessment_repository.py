from __future__ import annotations

import json
import sqlite3
from datetime import datetime


class RapidAssessmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, assessment: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO rapid_assessments (
                assessment_id, created_at, title, observation, stated_direction,
                urgency, source_urls_json, market_provider_status, json_path,
                html_path, warnings_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment["assessment_id"],
                assessment["created_at"],
                assessment["manual_input"]["title"],
                assessment["manual_input"]["observation"],
                assessment["manual_input"]["stated_direction"],
                assessment["manual_input"]["urgency"],
                json.dumps(assessment["manual_input"]["source_urls"], ensure_ascii=False),
                assessment["market"]["provider_status"],
                assessment["artifacts"]["json_path"],
                assessment["artifacts"]["html_path"],
                json.dumps(assessment["warnings"], ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def recent(self, limit: int = 12) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT assessment_id, created_at, title, stated_direction, urgency,
                   market_provider_status, json_path, html_path, warnings_json
            FROM rapid_assessments
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "assessment_id": row["assessment_id"],
                "created_at": row["created_at"],
                "title": row["title"],
                "stated_direction": row["stated_direction"],
                "urgency": row["urgency"],
                "market_provider_status": row["market_provider_status"],
                "json_path": row["json_path"],
                "html_path": row["html_path"],
                "html_url": f"/artifacts/{row['assessment_id']}.html",
                "warnings": json.loads(row["warnings_json"]),
            }
            for row in rows
        ]


def utc_now_iso() -> str:
    return datetime.now().astimezone().isoformat()
