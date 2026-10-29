"""Build and search a vector database of arXiv papers.

Run  python main.py  to open the text interface (search, view, pin, add papers).

The operations behind it can also be used from Python:
    from main import fetch, fetch_category, load, add_paper, search
The code lives in the src/ package; this file is only the entry point.
"""

from src import tui
from src.library import (  # noqa: F401  (re-exported so `from main import ...` keeps working)
    add_paper,
    fetch,
    fetch_category,
    ingest,
    ingested_categories,
    load,
    search,
)


def print_results(results: list[tuple[dict, float]]) -> None:
    for meta, distance in results:
        print(f"\n{meta['title']} ({meta['year']})")
        print(f"\t{meta['authors']}\n\t{meta['url']}")
        print(f"\t[distance {distance:.3f}]")


if __name__ == "__main__":
    tui.run()
