from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class JsonCache:
    def __init__(self, root: Path = Path("data/cache")) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, ttl: timedelta) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        created = datetime.fromisoformat(payload["created_at"])
        if datetime.now(timezone.utc) - created > ttl:
            return None
        return payload["value"]

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        payload = {"created_at": datetime.now(timezone.utc).isoformat(), "value": value}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"

