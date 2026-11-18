from src.topics import kmeans
import numpy as np
import pytest
# This asserts that the labeling is the same (regardless of label values)
def assert_labels_equal(a, b):
    np.testing.assert_array_equal(a[:, None] == a[None, :],
                                  b[:, None] == b[None, :])
def test_kmeans_works_simple():
    # Points should cluster (obviously) into three groups of two points each
    data = np.array([[0, 1], # facing right
                     [0.5, 1],
                     [1, 0], # facing up
                     [1, -0.5],
                     [-1, -1], # facing down-left
                     [-1, -1.1]
                     ])
    _, labels = np.unique(kmeans(data, 3), return_inverse=True)
    print(labels)
    correct_labels = np.array([0, 0, 1, 1, 2, 2])
    assert_labels_equal(labels, correct_labels)
def test_kmeans_works_k_large():
    # When k (num groups) > n (num points), there should be no error
    # Each point should be in a singleton group
    data = np.array([[0, 1],
                     [0.5, 1],
                     [1, 0],
                     [1, -0.5],
                     [-1, -1],
                     [-1, -1.1]
                     ])
    _, labels = np.unique(kmeans(data, 10), return_inverse=True)
    correct_labels = np.array([0, 1, 2, 3, 4, 5])
    assert_labels_equal(labels, correct_labels)


def test_kmeans_returns_one_valid_label_per_vector():
    data = np.random.default_rng(1).normal(size=(30, 6))
    labels = kmeans(data, 10)
    assert labels.shape == (30,)
    assert np.issubdtype(labels.dtype, np.integer)
    assert labels.min() >= 0 and labels.max() < 10


@pytest.mark.parametrize("k", [0, -1])
def test_kmeans_rejects_non_positive_k(k):
    # There is no way to split vectors into zero (or fewer) groups.
    data = np.array([[1.0, 0], [0, 1], [-1, 0], [0, -1]])
    with pytest.raises(ValueError):
        kmeans(data, k)


def test_kmeans_rejects_empty_input():
    with pytest.raises(ValueError):
        kmeans(np.empty((0, 4)), 2)


def test_kmeans_identical_vectors_with_k_larger_than_n():
    # All distances to the existing centers are 0 here, so there is nothing to weight by.
    labels = kmeans(np.ones((5, 3)), 10)
    assert labels.min() >= 0 and labels.max() < 10
    assert len(set(labels)) == 1


def test_kmeans_zero_vector_does_not_corrupt_other_vectors():
    # A zero vector has no direction (normalizing it divides by zero). It should either be
    # rejected, or leave the clustering of all the other vectors intact.
    data = np.array([[0.0, 0.0],
                     [1.0, 0.0],
                     [0.0, 1.0]])
    try:
        labels = kmeans(data, 2)
    except ValueError:
        return
    assert labels[1] != labels[2]
    assert not np.isnan(labels.astype(float)).any()


def test_kmeans_ignores_vector_length():
    # With Euclidean distance, (0, 0.01) would sit next to (1, 0). With cosine it is
    # in the same group as (0, 1).
    data = np.array([[1.0, 0.0],
                     [100.0, 0.0],
                     [0.0, 1.0],
                     [0.0, 0.01]])
    assert_labels_equal(kmeans(data, 2), np.array([0, 0, 1, 1]))


def test_kmeans_recovers_well_separated_groups():
    # Tight groups of 768-dimensional vectors (the size the app uses), with random lengths.
    rng = np.random.default_rng(3)
    directions = rng.normal(size=(6, 768))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    true_labels = np.repeat(np.arange(6), 15)
    data = directions[true_labels] + 0.002 * rng.normal(size=(90, 768))
    data *= rng.uniform(0.1, 50, size=(90, 1))
    assert_labels_equal(kmeans(data.astype(np.float32), 6), true_labels)


def test_kmeans_zero_iterations_does_not_return_none():
    # With no iterations nothing has been assigned yet. It should either raise
    # or still return a label for every vector (not None).
    data = np.array([[1.0, 0], [0, 1], [-1, 0], [0, -1]])
    try:
        labels = kmeans(data, 2, iterations=0)
    except ValueError:
        return
    assert labels is not None
    assert len(labels) == len(data)
