"""Run a slow producer in a background thread so the consumer can work in parallel."""

import queue
import threading
from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")

_DONE = object()


def prefetch(items: Iterable[T], buffer: int = 2) -> Iterator[T]:
    """Iterate `items` in a background thread, keeping up to `buffer` items ready.

    The producer blocks when the buffer is full, so memory stays bounded. An exception
    raised by the producer is re-raised in the consuming thread.
    """
    buf: queue.Queue = queue.Queue(maxsize=buffer)

    def produce() -> None:
        try:
            for item in items:
                buf.put(item)
            buf.put(_DONE)
        except Exception as exc:
            buf.put(exc)

    threading.Thread(target=produce, daemon=True).start()

    while (item := buf.get()) is not _DONE:
        if isinstance(item, Exception):
            raise item
        yield item
