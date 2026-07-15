from __future__ import annotations

from datetime import timezone, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_timezone(name: str) -> tzinfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "Asia/Taipei":
            return timezone(timedelta(hours=8), name="Asia/Taipei")
        return timezone.utc

