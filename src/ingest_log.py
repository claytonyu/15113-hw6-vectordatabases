"""Remember which arXiv categories have already been fetched and embedded into a database.

The log is a JSON file inside the database directory, one per collection, so it travels with
the database and never claims a category is embedded in a collection that doesn't contain it.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from .store import COLLECTION_NAME


def _path(db: str) -> Path:
    return Path(db) / f"ingested_{COLLECTION_NAME}.json"


def read(db: str) -> dict[str, dict]:
    """Return {category: {"limit": ..., "papers": ..., "fetched_at": ...}} for a database."""
    path = _path(db)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def record(db: str, category: str, limit: int, papers: int) -> None:
    """Note that `category` was fetched with this limit and `papers` papers were stored."""
    log = read(db)
    log[category] = {
        "limit": limit,
        "papers": papers,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _path(db).parent.mkdir(parents=True, exist_ok=True)
    _path(db).write_text(json.dumps(log, indent=2), encoding="utf-8")
