"""Group papers into topics by clustering their embeddings."""

import math
import re
from collections import Counter

import numpy as np


def kmeans(vectors: np.ndarray, k: int, iterations: int = 50, seed: int = 0) -> np.ndarray:
    """Cluster vectors by cosine similarity. Returns the cluster number (0..k-1) of each vector."""
    rng = np.random.default_rng(seed)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    # k-means++ start: each new center is likely to be far from the existing ones.
    centers = [vectors[rng.integers(len(vectors))]]
    while len(centers) < k:
        dist = np.clip(2 - 2 * (vectors @ np.array(centers).T).max(axis=1), 0, None)
        probs = dist / dist.sum() if dist.sum() > 0 else None
        centers.append(vectors[rng.choice(len(vectors), p=probs)])
    centers = np.array(centers)

    assignment = None
    for _ in range(iterations):
        new = (vectors @ centers.T).argmax(axis=1)  # most similar center
        if assignment is not None and np.array_equal(new, assignment):
            break
        assignment = new
        for c in range(k):
            members = vectors[assignment == c]
            if len(members):
                mean = members.mean(axis=0)
                centers[c] = mean / np.linalg.norm(mean)
    return assignment


def _label(cluster: list[int], title_words: list[set[str]], word_freq: Counter, n_words: int = 3) -> str:
    """Name a cluster by the title words that are frequent in it but rare overall."""
    in_cluster = Counter(w for i in cluster for w in title_words[i])
    score = {w: n * math.log(len(title_words) / word_freq[w]) for w, n in in_cluster.items()}
    return ", ".join(sorted(score, key=score.get, reverse=True)[:n_words])


def group_by_topic(embeddings: np.ndarray, titles: list[str], k: int) -> dict[str, list[int]]:
    """Cluster into k topics. Returns {topic label: indices of its papers}, largest topic first."""
    assignment = kmeans(np.asarray(embeddings), k)
    clusters = [[i for i, a in enumerate(assignment) if a == c] for c in range(k)]
    clusters = sorted((c for c in clusters if c), key=len, reverse=True)  # drop empty, biggest first

    title_words = [set(re.findall(r"[a-z][a-z-]{3,}", t.lower())) for t in titles]
    word_freq = Counter(w for words in title_words for w in words)
    return {
        f"Topic {n}: {_label(cluster, title_words, word_freq)}": cluster
        for n, cluster in enumerate(clusters, start=1)
    }
