from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    timezone: str = "Asia/Taipei"
    language: str = "zh-TW"
    database_url: str = "sqlite:///data/crypto_intelligence.db"
    report_output_dir: Path = Path("artifacts")
    email_enabled: bool = False
    dry_run: bool = True
    top_event_count: int = 10
    deep_analysis_interval_days: int = 3
    minimum_event_count: int = 5
    minimum_provider_success_rate: float = 0.70
    max_single_domain_ratio: float = 0.50
    raw: dict[str, Any] = field(default_factory=dict)


def load_config(path: str | Path = "config/default.yaml") -> AppConfig:
    raw = _parse_simple_yaml(Path(path))
    env = os.environ
    app = raw.get("app", {})
    report = raw.get("report", {})
    quality = raw.get("quality", {})
    delivery = raw.get("delivery", {})
    return AppConfig(
        timezone=env.get("APP_TIMEZONE", app.get("timezone", "Asia/Taipei")),
        language=app.get("language", "zh-TW"),
        database_url=env.get("DATABASE_URL", "sqlite:///data/crypto_intelligence.db"),
        report_output_dir=Path(env.get("REPORT_OUTPUT_DIR", "artifacts")),
        email_enabled=_as_bool(env.get("EMAIL_ENABLED", delivery.get("email_enabled", False))),
        dry_run=_as_bool(env.get("DRY_RUN", True)),
        top_event_count=int(report.get("top_event_count", 10)),
        deep_analysis_interval_days=int(report.get("deep_analysis_interval_days", 3)),
        minimum_event_count=int(quality.get("minimum_event_count", 5)),
        minimum_provider_success_rate=float(quality.get("minimum_provider_success_rate", 0.70)),
        max_single_domain_ratio=float(quality.get("max_single_domain_ratio", 0.50)),
        raw=raw,
    )


def sqlite_path_from_url(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// DATABASE_URL is supported in the MVP.")
    return Path(database_url[len(prefix) :])


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    pending_list_key: tuple[int, dict[str, Any], str] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line.startswith("- ") and pending_list_key:
            _, parent, key = pending_list_key
            if not isinstance(parent.get(key), list):
                parent[key] = []
            parent[key].append(_parse_scalar(line[2:]))
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        key, _, value = line.partition(":")
        key = key.strip()
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
            pending_list_key = (indent, parent, key)
        else:
            parent[key] = _parse_scalar(value.strip())
            pending_list_key = None
    return root


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")
