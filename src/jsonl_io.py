"""Read and write papers as JSON Lines (one paper per line)."""

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

BATCH_SIZE = 500


def read_batches(path: str, size: int = BATCH_SIZE) -> Iterator[list[dict]]:
    """Yield papers from a JSONL file in lists of up to `size`."""
    batch = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                batch.append(json.loads(line))
            if len(batch) == size:
                yield batch
                batch = []
    if batch:
        yield batch


def save_batches(batches: Iterable[list[dict]], path: str) -> Iterator[list[dict]]:
    """Write each batch to `path` as it passes through, then yield it unchanged."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for batch in batches:
            for paper in batch:
                f.write(json.dumps(paper, ensure_ascii=False) + "\n")
            yield batch
