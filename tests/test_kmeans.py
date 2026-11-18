from src.topics import kmeans
import numpy as np

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
