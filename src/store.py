"""The Chroma collection holding papers: opening it, adding papers, and searching."""

import logging
import re

import chromadb
from chromadb.utils import embedding_functions
from huggingface_hub import try_to_load_from_cache

# PyTorch warns on import that stdout redirection is unsupported on macOS. Nothing here uses it.
logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)

DB_PATH = "./chroma_store"
# BGE vectors have 768 dimensions, so they can't share a collection with the earlier
# 384-dimension default model. Changing the model means using a new collection name.
COLLECTION_NAME = "papers_bge_base"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # downloaded from Hugging Face on first use


def _warn_if_model_not_downloaded() -> None:
    """Tell the user up front that the first run downloads the embedding model."""
    if not isinstance(try_to_load_from_cache(EMBEDDING_MODEL, "modules.json"), str):
        print(f"First run: downloading the embedding model {EMBEDDING_MODEL} (about 440 MB). "
              "This can take a minute; later runs reuse the saved copy.")


def open_collection(path: str = DB_PATH) -> chromadb.Collection:
    # PersistentClient writes to disk. The default in-memory client does NOT.
    client = chromadb.PersistentClient(path=path)
    _warn_if_model_not_downloaded()
    embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
    )
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedder)


def paper_id(arxiv_id: str) -> str:
    """arXiv ID without the version suffix ("2401.01234v2" -> "2401.01234"), so every
    version of a paper is one item and re-runs update it."""
    return re.sub(r"v\d+$", "", arxiv_id.strip())


def _id(paper: dict) -> str:
    return paper_id(paper["id"])


def _document(paper: dict) -> str:
    """The text that gets embedded."""
    return f"{paper['title']}\n\n{paper['abstract']}"


def _metadata(paper: dict) -> dict:
    return {
        "title": paper["title"],
        "authors": ", ".join(paper["authors"]),  # Chroma metadata can't hold lists
        # Older JSONL files were saved before categories were collected, hence .get().
        "primary_category": paper.get("primary_category", ""),
        "categories": ", ".join(paper.get("categories", [])),
        "year": int(paper["published"][:4]),
        "url": paper["url"],
        "pdf_url": paper["pdf_url"],
    }


def add_papers(collection: chromadb.Collection, papers: list[dict]) -> None:
    """Embed and store papers. Safe to repeat: existing IDs are updated, not duplicated.
    The papers within one call must have distinct IDs."""
    collection.upsert(
        ids=[_id(p) for p in papers],
        documents=[_document(p) for p in papers],
        metadatas=[_metadata(p) for p in papers],
    )


def search(collection: chromadb.Collection, text: str, k: int = 5) -> list[tuple[dict, float]]:
    """Return the k closest papers as (metadata, distance) pairs, nearest first.
    Each metadata dict also has the paper's "id"."""
    results = collection.query(query_texts=[text], n_results=k)
    return [
        ({"id": paper_id, **metadata}, distance)
        for paper_id, metadata, distance in zip(results["ids"][0], results["metadatas"][0], results["distances"][0])
    ]


def get_papers(collection: chromadb.Collection, ids: list[str]) -> list[dict]:
    """Return the full stored record of each paper: its metadata plus "id" and "abstract".
    Results follow the order of `ids`; IDs that aren't in the database are left out."""
    if not ids:
        return []
    data = collection.get(ids=ids, include=["metadatas", "documents"])
    found = {i: (meta, doc) for i, meta, doc in zip(data["ids"], data["metadatas"], data["documents"])}
    return [
        {"id": i, **found[i][0], "abstract": found[i][1].removeprefix(found[i][0]["title"]).strip()}
        for i in ids
        if i in found
    ]
