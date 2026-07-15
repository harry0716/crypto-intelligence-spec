from __future__ import annotations

from datetime import date


def should_run_deep_analysis(today: date, last_run: date | None, interval_days: int = 3) -> bool:
    if last_run is None:
        return False
    return (today - last_run).days >= interval_days

