"""Papers the user has pinned: a JSON list of arXiv IDs saved inside the database directory.

One file per collection, like ingest_log, so pins always refer to papers in that collection.
"""

import json
from pathlib import Path

from .store import COLLECTION_NAME


def _path(db: str) -> Path:
    return Path(db) / f"pins_{COLLECTION_NAME}.json"


def read(db: str) -> list[str]:
    """Return the pinned paper IDs, oldest pin first."""
    path = _path(db)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _write(db: str, ids: list[str]) -> None:
    _path(db).parent.mkdir(parents=True, exist_ok=True)
    _path(db).write_text(json.dumps(ids, indent=2), encoding="utf-8")


def add(db: str, paper_id: str) -> bool:
    """Pin a paper. Returns False if it was already pinned."""
    ids = read(db)
    if paper_id in ids:
        return False
    _write(db, ids + [paper_id])
    return True


def remove(db: str, paper_id: str) -> bool:
    """Unpin a paper. Returns False if it wasn't pinned."""
    ids = read(db)
    if paper_id not in ids:
        return False
    _write(db, [i for i in ids if i != paper_id])
    return True
