"""Fetch paper metadata from the arXiv query API (https://info.arxiv.org/help/api/user-manual.html)."""

import time
import xml.etree.ElementTree as ET
from collections.abc import Iterator

import requests

API_URL = "https://export.arxiv.org/api/query"
PAGE_SIZE = 100     # papers per request; arXiv allows up to 2000
DELAY_SECONDS = 3   # arXiv asks for ~3s between consecutive calls
MAX_RETRIES = 3

# Atom and OpenSearch use XML namespaces; every tag lookup needs them.
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _text(entry: ET.Element, tag: str) -> str:
    """Text of a child element with whitespace collapsed (arXiv wraps titles and abstracts)."""
    el = entry.find(tag, NS)
    return " ".join(el.text.split()) if el is not None and el.text else ""


def parse_entry(entry: ET.Element) -> dict:
    """Turn one Atom <entry> into a flat paper dict."""
    abs_url = _text(entry, "atom:id")  # e.g. http://arxiv.org/abs/2401.01234v2
    pdf_url = next(
        (link.get("href") for link in entry.findall("atom:link", NS) if link.get("title") == "pdf"),
        abs_url.replace("/abs/", "/pdf/"),
    )
    primary = entry.find("arxiv:primary_category", NS)
    return {
        "id": abs_url.rsplit("/abs/", 1)[-1],
        "title": _text(entry, "atom:title"),
        "abstract": _text(entry, "atom:summary"),
        "authors": [_text(a, "atom:name") for a in entry.findall("atom:author", NS)],
        "primary_category": primary.get("term") if primary is not None else "",  # e.g. "cs.CL"
        "categories": [c.get("term") for c in entry.findall("atom:category", NS)],  # includes cross-lists
        "published": _text(entry, "atom:published"),  # ISO 8601, e.g. 2024-01-02T18:59:59Z
        "url": abs_url,
        "pdf_url": pdf_url,
    }


def _get(session: requests.Session, params: dict) -> bytes:
    """GET with retries and increasing backoff on transient errors.
    Client errors (4xx, except 429 rate limiting) are raised at once, since retrying can't fix them."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(API_URL, params=params, timeout=60)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            status = exc.response.status_code if exc.response is not None else None
            client_error = status is not None and 400 <= status < 500 and status != 429
            if attempt == MAX_RETRIES or client_error:
                raise
            wait = DELAY_SECONDS * attempt * 2
            print(f"arXiv request failed ({exc}); retrying in {wait}s")
            time.sleep(wait)


def fetch_page(session: requests.Session, query: str, start: int, count: int) -> tuple[list[dict], int]:
    """Fetch one page of results. Returns (papers, total number of matches)."""
    params = {
        "search_query": query,
        "start": start,
        "max_results": count,
        # A fixed sort keeps paging stable while new papers are being submitted.
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    root = ET.fromstring(_get(session, params))
    total = int(root.findtext("os:totalResults", "0", NS))
    return [parse_entry(e) for e in root.findall("atom:entry", NS)], total


def _new_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "15113-hw6-vectordb (student project)"
    return session


def fetch_paper(arxiv_id: str) -> dict:
    """Return the paper with this arXiv ID, e.g. "1706.03762" (latest version) or
    "1706.03762v1" (that version). Raises ValueError if the ID is malformed or not found."""
    with _new_session() as session:
        try:
            content = _get(session, {"id_list": arxiv_id})
        except requests.HTTPError as exc:
            if exc.response.status_code == 400:  # arXiv's response to a malformed ID
                raise ValueError(f"Invalid arXiv ID {arxiv_id!r}") from exc
            raise
    entries = ET.fromstring(content).findall("atom:entry", NS)
    if not entries:  # well-formed ID, but no such paper
        raise ValueError(f"No arXiv paper found for ID {arxiv_id!r}")
    return parse_entry(entries[0])


def iter_batches(query: str, limit: int) -> Iterator[list[dict]]:
    """Yield pages of papers until `limit` papers are produced or results run out."""
    fetched = 0
    with _new_session() as session:
        while fetched < limit:
            if fetched:
                time.sleep(DELAY_SECONDS)
            batch, total = fetch_page(session, query, fetched, min(PAGE_SIZE, limit - fetched))
            if not batch:
                return
            yield batch
            fetched += len(batch)
            print(f"Fetched {fetched}/{limit} papers")
            if fetched >= total:
                return
