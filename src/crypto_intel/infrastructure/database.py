from __future__ import annotations

import sqlite3
from pathlib import Path

from crypto_intel.config import sqlite_path_from_url


SCHEMA = """
CREATE TABLE IF NOT EXISTS market_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    price REAL NOT NULL,
    market_cap REAL,
    volume_24h REAL,
    change_24h_pct REAL,
    change_7d_pct REAL,
    observed_at TEXT NOT NULL,
    provider TEXT NOT NULL,
    source_url TEXT NOT NULL,
    inferred INTEGER NOT NULL DEFAULT 0,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    event_time TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    affected_assets_json TEXT NOT NULL,
    impact_direction TEXT NOT NULL,
    short_term_impact TEXT NOT NULL,
    medium_term_impact TEXT NOT NULL,
    confidence REAL NOT NULL,
    classification TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    topic TEXT NOT NULL,
    importance REAL NOT NULL,
    quality_score INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    timezone TEXT NOT NULL,
    html_path TEXT NOT NULL,
    pdf_path TEXT,
    json_path TEXT NOT NULL,
    deep_analysis INTEGER NOT NULL,
    dry_run INTEGER NOT NULL,
    warnings_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    dry_run INTEGER NOT NULL,
    message TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS provider_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    latency_ms INTEGER,
    error TEXT
);

CREATE TABLE IF NOT EXISTS rapid_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL,
    observation TEXT NOT NULL,
    stated_direction TEXT NOT NULL,
    urgency TEXT NOT NULL,
    source_urls_json TEXT NOT NULL,
    market_provider_status TEXT NOT NULL,
    json_path TEXT NOT NULL,
    html_path TEXT NOT NULL,
    warnings_json TEXT NOT NULL
);
"""


def connect(database_url: str) -> sqlite3.Connection:
    db_path = sqlite_path_from_url(database_url)
    ensure_parent(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
