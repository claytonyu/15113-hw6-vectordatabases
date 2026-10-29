"""Operations on the paper library: fetching from arXiv, embedding into the database, searching."""

import re
from collections.abc import Iterable

from . import arxiv_client, categories, ingest_log, jsonl_io, store
from .pipeline import prefetch

# arXiv category names look like "cs.CL", "stat.ML", "hep-th" or "q-bio.CB".
CATEGORY_PATTERN = re.compile(r"^[a-z-]+(\.[A-Za-z-]+)?$")


def normalize_category(text: str) -> str:
    """Clean up a category typed by a user: drop an optional "cat:" prefix and fix the letter
    case of known codes ("STAT.th" -> "stat.TH"). Aliases are kept; see canonical_category().
    Raises ValueError if the result is not a category name."""
    name = re.sub(r"^cat:", "", text.strip(), flags=re.IGNORECASE)
    name = categories.CODES.get(name.lower(), name)
    # Codes missing from our list may still be valid, so only the shape is checked. This also
    # keeps extra search syntax (e.g. "cs.CL OR all:foo") out of the query we build.
    if not CATEGORY_PATTERN.match(name):
        raise ValueError(f"{text!r} is not an arXiv category name like 'cs.CL' or 'q-bio.CB'")
    return name


def canonical_category(text: str) -> str:
    """The code arXiv files papers under: normalize_category() plus alias resolution,
    so "stat.TH" becomes "math.ST". This is the form to search for and to record."""
    name = normalize_category(text)
    return categories.ALIASES.get(name, name)


def ingest(collection, batches: Iterable[list[dict]]) -> int:
    """Store batches as they arrive and return how many papers were stored.
    Producing the next batch (e.g. an arXiv request) runs in a background thread
    while the current batch is being embedded."""
    total = 0
    for batch in prefetch(batches):
        store.add_papers(collection, batch)
        total += len(batch)
        print(f"Embedded {total} papers")
    print(f"collection now holds {collection.count()} papers")
    return total


def fetch(query: str = "cat:cs.LG", limit: int = 1000, save: str | None = None, db: str = store.DB_PATH) -> int:
    """Fetch papers from arXiv and store them; returns how many were stored. `query` is an
    arXiv search_query, e.g. "cat:cs.CL". If `save` is a path, the papers are also written
    there as JSONL. This does not track what has been fetched; see fetch_category()."""
    batches = arxiv_client.iter_batches(query, limit)
    if save:
        batches = jsonl_io.save_batches(batches, save)
    return ingest(store.open_collection(db), batches)


def fetch_category(category: str, limit: int = 1000, refresh: bool = False, db: str = store.DB_PATH) -> int:
    """Fetch and embed the newest `limit` papers of one arXiv category (e.g. "cs.CL"),
    including papers cross-listed into it. Returns how many papers were stored.

    A category that was already fetched with the same or a larger `limit` is skipped (and 0
    is returned), so it is safe to call repeatedly. Pass refresh=True to fetch it again, e.g.
    to pick up papers submitted since. Asking for a larger `limit` than before also fetches again.
    """
    category = canonical_category(category)  # "cat:stat.TH" and "stat.TH" both mean "math.ST"
    done = ingest_log.read(db).get(category)
    if done and done["limit"] >= limit and not refresh:
        print(f"Skipping {category}: already fetched {done['papers']} papers on {done['fetched_at']} "
              f"(limit {done['limit']}).")
        return 0

    stored = fetch(f"cat:{category}", limit, db=db)
    if stored:  # no results usually means a misspelled category; don't remember it as fetched
        ingest_log.record(db, category, limit, stored)  # only reached if the fetch completed
    return stored


def ingested_categories(db: str = store.DB_PATH) -> dict[str, dict]:
    """Return the categories fetched so far: {category: {"limit", "papers", "fetched_at"}}."""
    return ingest_log.read(db)


def load(path: str, db: str = store.DB_PATH, category: str | None = None) -> int:
    """Store the papers from a JSONL file (as written by fetch(..., save=path)) and return
    how many were stored. If the file holds one arXiv category, pass it as `category` so
    fetch_category() knows that category is already in the database."""
    if category:
        category = canonical_category(category)
    stored = ingest(store.open_collection(db), jsonl_io.read_batches(path))
    if category:
        ingest_log.record(db, category, limit=stored, papers=stored)
    return stored


def add_paper(arxiv_id: str, db: str = store.DB_PATH) -> dict:
    """Fetch one paper by arXiv ID (e.g. "1706.03762"), store it, and return it.
    Raises ValueError if the ID is invalid or no such paper exists."""
    paper = arxiv_client.fetch_paper(arxiv_id)
    store.add_papers(store.open_collection(db), [paper])
    print(f"stored {paper['id']}: {paper['title']}")
    return paper


def search(text: str, k: int = 5, db: str = store.DB_PATH) -> list[tuple[dict, float]]:
    """Return the k papers closest to `text` as (metadata, distance) pairs, nearest first."""
    return store.search(store.open_collection(db), text, k)
