"""Algorithm catalog — strongly-typed entries with hashtag annotation.

Each algorithm is tagged with a subset of the Tag vocabulary.
The matcher uses these tags to surface candidates via set intersection.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════
# Tag vocabulary
# ═══════════════════════════════════════════════════════════════════

class Tag(str, Enum):
    """Hashtag vocabulary for algorithm pattern matching.

    Organised by category — each tag is also a plain ``str``
    so ``Tag.GRAPH == "graph"`` is ``True``.
    """

    # ── Input Structure ─────────────────────────
    ARRAY = "array"
    SEQUENCE = "sequence"
    STRING = "string"
    GRAPH = "graph"
    TREE = "tree"
    MATRIX = "matrix"
    SET = "set"
    STREAM = "stream"
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    TIME_SERIES = "time-series"
    GRID = "grid"
    INTERVAL = "interval"
    POINT_CLOUD = "point-cloud"
    NUMERIC = "numeric"
    KEY_VALUE = "key-value"

    # ── Output Goal ─────────────────────────────
    SORTING = "sorting"
    SEARCH = "search"
    SHORTEST_PATH = "shortest-path"
    SPANNING_TREE = "spanning-tree"
    MAX_FLOW = "max-flow"
    TRAVERSAL = "traversal"
    CONNECTIVITY = "connectivity"
    MATCHING = "matching"
    PATTERN_MATCHING = "pattern-matching"
    OPTIMIZATION = "optimization"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    RANKING = "ranking"
    ANOMALY_DETECTION = "anomaly-detection"
    GENERATION = "generation"
    EMBEDDING = "embedding"
    RECOMMENDATION = "recommendation"
    PREDICTION = "prediction"
    SAMPLING = "sampling"
    PARTITION = "partition"
    FEATURE_SELECTION = "feature-selection"
    DIMENSIONALITY_REDUCTION = "dimensionality-reduction"
    RANGE_QUERY = "range-query"
    DECOMPOSITION = "decomposition"
    DENSITY_ESTIMATION = "density-estimation"
    SIMILARITY = "similarity"
    TRANSFORM = "transform"
    ENCODING = "encoding"
    FREQUENCY = "frequency"
    AGGREGATION = "aggregation"
    SCHEDULING = "scheduling"

    # ── Problem Property ────────────────────────
    OVERLAPPING_SUBPROBLEMS = "overlapping-subproblems"
    OPTIMAL_SUBSTRUCTURE = "optimal-substructure"
    HIGH_DIMENSIONALITY = "high-dimensionality"
    SPARSE = "sparse"
    ONLINE = "online"
    WEIGHTED = "weighted"
    DIRECTED = "directed"
    PROBABILISTIC = "probabilistic"
    LINEAR = "linear"
    NONLINEAR = "nonlinear"
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    NP_HARD = "np-hard"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    MONOTONIC = "monotonic"

    # ── Paradigm ────────────────────────────────
    DIVIDE_AND_CONQUER = "divide-and-conquer"
    DYNAMIC_PROGRAMMING = "dynamic-programming"
    GREEDY = "greedy"
    HEURISTIC = "heuristic"
    RANDOMIZED = "randomized"
    APPROXIMATION = "approximation"
    ITERATIVE = "iterative"
    ENSEMBLE = "ensemble"
    KERNEL = "kernel"
    GRADIENT_BASED = "gradient-based"
    BAYESIAN = "bayesian"
    NEURAL_NETWORK = "neural-network"
    SPECTRAL = "spectral"
    INFORMATION_THEORETIC = "information-theoretic"
    HASHING = "hashing"
    BACKTRACKING = "backtracking"

    # ── Scale ───────────────────────────────────
    LARGE_SCALE = "large-scale"
    REAL_TIME = "real-time"


# Category mapping — used by the matcher to present tags in groups.
TAG_CATEGORIES: dict[str, tuple[Tag, ...]] = {
    "Input Structure": (
        Tag.ARRAY, Tag.SEQUENCE, Tag.STRING, Tag.GRAPH, Tag.TREE,
        Tag.MATRIX, Tag.SET, Tag.STREAM, Tag.TEXT, Tag.IMAGE,
        Tag.TABLE, Tag.TIME_SERIES, Tag.GRID, Tag.INTERVAL,
        Tag.POINT_CLOUD, Tag.NUMERIC, Tag.KEY_VALUE,
    ),
    "Output Goal": (
        Tag.SORTING, Tag.SEARCH, Tag.SHORTEST_PATH, Tag.SPANNING_TREE,
        Tag.MAX_FLOW, Tag.TRAVERSAL, Tag.CONNECTIVITY, Tag.MATCHING,
        Tag.PATTERN_MATCHING, Tag.OPTIMIZATION, Tag.CLUSTERING,
        Tag.CLASSIFICATION, Tag.REGRESSION, Tag.RANKING,
        Tag.ANOMALY_DETECTION, Tag.GENERATION, Tag.EMBEDDING,
        Tag.RECOMMENDATION, Tag.PREDICTION, Tag.SAMPLING,
        Tag.PARTITION, Tag.FEATURE_SELECTION,
        Tag.DIMENSIONALITY_REDUCTION, Tag.RANGE_QUERY,
        Tag.DECOMPOSITION, Tag.DENSITY_ESTIMATION, Tag.SIMILARITY,
        Tag.TRANSFORM, Tag.ENCODING, Tag.FREQUENCY, Tag.AGGREGATION,
        Tag.SCHEDULING,
    ),
    "Problem Property": (
        Tag.OVERLAPPING_SUBPROBLEMS, Tag.OPTIMAL_SUBSTRUCTURE,
        Tag.HIGH_DIMENSIONALITY, Tag.SPARSE, Tag.ONLINE, Tag.WEIGHTED,
        Tag.DIRECTED, Tag.PROBABILISTIC, Tag.LINEAR, Tag.NONLINEAR,
        Tag.DISCRETE, Tag.CONTINUOUS, Tag.NP_HARD, Tag.TEMPORAL,
        Tag.SPATIAL, Tag.LABELED, Tag.UNLABELED, Tag.MONOTONIC,
    ),
    "Paradigm": (
        Tag.DIVIDE_AND_CONQUER, Tag.DYNAMIC_PROGRAMMING, Tag.GREEDY,
        Tag.HEURISTIC, Tag.RANDOMIZED, Tag.APPROXIMATION,
        Tag.ITERATIVE, Tag.ENSEMBLE, Tag.KERNEL, Tag.GRADIENT_BASED,
        Tag.BAYESIAN, Tag.NEURAL_NETWORK, Tag.SPECTRAL,
        Tag.INFORMATION_THEORETIC, Tag.HASHING, Tag.BACKTRACKING,
    ),
    "Scale": (
        Tag.LARGE_SCALE, Tag.REAL_TIME,
    ),
}


# ═══════════════════════════════════════════════════════════════════
# Algorithm entry
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class Algorithm:
    """A single algorithm / technique with its hashtag set."""

    name: str
    tags: frozenset[Tag]


def _a(name: str, *tags: Tag) -> Algorithm:
    """Compact factory for catalog entries."""
    return Algorithm(name, frozenset(tags))


T = Tag  # short alias for catalog readability


# ═══════════════════════════════════════════════════════════════════
# Catalog
# ═══════════════════════════════════════════════════════════════════

CATALOG: tuple[Algorithm, ...] = (

    # ── Sorting & Ordering ──────────────────────────────────────
    _a("QuickSort",               T.ARRAY, T.SORTING, T.DIVIDE_AND_CONQUER, T.RANDOMIZED),
    _a("MergeSort",               T.ARRAY, T.SORTING, T.DIVIDE_AND_CONQUER, T.SEQUENCE),
    _a("HeapSort",                T.ARRAY, T.SORTING),
    _a("RadixSort",               T.ARRAY, T.SORTING, T.DISCRETE, T.LINEAR),
    _a("CountingSort",            T.ARRAY, T.SORTING, T.DISCRETE, T.LINEAR),
    _a("BucketSort",              T.ARRAY, T.SORTING),
    _a("TimSort",                 T.ARRAY, T.SORTING, T.SEQUENCE),

    # ── Searching ───────────────────────────────────────────────
    _a("BinarySearch",            T.ARRAY, T.SEARCH, T.DIVIDE_AND_CONQUER),
    _a("InterpolationSearch",     T.ARRAY, T.SEARCH, T.NUMERIC),
    _a("HashTableLookup",         T.KEY_VALUE, T.SEARCH, T.HASHING),

    # ── Graph: Traversal & Shortest Path ────────────────────────
    _a("BFS",                     T.GRAPH, T.TRAVERSAL, T.SEARCH, T.SHORTEST_PATH),
    _a("DFS",                     T.GRAPH, T.TRAVERSAL, T.SEARCH, T.BACKTRACKING, T.CONNECTIVITY),
    _a("Dijkstra",                T.GRAPH, T.WEIGHTED, T.SHORTEST_PATH, T.GREEDY),
    _a("Bellman-Ford",            T.GRAPH, T.WEIGHTED, T.SHORTEST_PATH, T.DYNAMIC_PROGRAMMING),
    _a("Floyd-Warshall",          T.GRAPH, T.WEIGHTED, T.SHORTEST_PATH, T.DYNAMIC_PROGRAMMING),
    _a("A*",                      T.GRAPH, T.WEIGHTED, T.SHORTEST_PATH, T.HEURISTIC),
    _a("Bidirectional BFS",       T.GRAPH, T.SEARCH, T.SHORTEST_PATH, T.TRAVERSAL),

    # ── Graph: MST, Flow, Matching ──────────────────────────────
    _a("Kruskal",                 T.GRAPH, T.SPANNING_TREE, T.GREEDY, T.WEIGHTED),
    _a("Prim",                    T.GRAPH, T.SPANNING_TREE, T.GREEDY, T.WEIGHTED),
    _a("Topological Sort",        T.GRAPH, T.DIRECTED, T.SORTING, T.SCHEDULING),
    _a("Tarjan SCC",              T.GRAPH, T.DIRECTED, T.CONNECTIVITY),
    _a("Ford-Fulkerson",          T.GRAPH, T.DIRECTED, T.MAX_FLOW, T.WEIGHTED),
    _a("Edmonds-Karp",            T.GRAPH, T.DIRECTED, T.MAX_FLOW, T.WEIGHTED),
    _a("Hungarian Algorithm",     T.MATRIX, T.MATCHING, T.OPTIMIZATION, T.WEIGHTED),
    _a("Hopcroft-Karp",           T.GRAPH, T.MATCHING),

    # ── Tree Structures ─────────────────────────────────────────
    _a("Binary Search Tree",      T.TREE, T.SEARCH, T.KEY_VALUE),
    _a("AVL Tree",                T.TREE, T.SEARCH, T.KEY_VALUE),
    _a("B-Tree",                  T.TREE, T.SEARCH, T.KEY_VALUE, T.LARGE_SCALE),
    _a("Trie",                    T.TREE, T.TEXT, T.STRING, T.SEARCH, T.PATTERN_MATCHING),
    _a("Segment Tree",            T.TREE, T.ARRAY, T.RANGE_QUERY, T.AGGREGATION),
    _a("Fenwick Tree (BIT)",      T.TREE, T.ARRAY, T.RANGE_QUERY, T.AGGREGATION),
    _a("Suffix Tree",             T.TREE, T.STRING, T.PATTERN_MATCHING),
    _a("Suffix Array",            T.ARRAY, T.STRING, T.PATTERN_MATCHING, T.SORTING),

    # ── Dynamic Programming ─────────────────────────────────────
    _a("LCS",                     T.SEQUENCE, T.DYNAMIC_PROGRAMMING, T.OVERLAPPING_SUBPROBLEMS, T.MATCHING, T.SIMILARITY),
    _a("LIS",                     T.SEQUENCE, T.DYNAMIC_PROGRAMMING, T.MONOTONIC, T.OPTIMAL_SUBSTRUCTURE),
    _a("Edit Distance",           T.STRING, T.SEQUENCE, T.DYNAMIC_PROGRAMMING, T.OVERLAPPING_SUBPROBLEMS, T.SIMILARITY),
    _a("0/1 Knapsack",            T.SET, T.OPTIMIZATION, T.DYNAMIC_PROGRAMMING, T.DISCRETE, T.OVERLAPPING_SUBPROBLEMS),
    _a("Matrix Chain Multiply",   T.SEQUENCE, T.OPTIMIZATION, T.DYNAMIC_PROGRAMMING, T.OVERLAPPING_SUBPROBLEMS),
    _a("Coin Change",             T.SET, T.OPTIMIZATION, T.DYNAMIC_PROGRAMMING, T.DISCRETE),
    _a("TSP (DP Bitmask)",        T.GRAPH, T.OPTIMIZATION, T.DYNAMIC_PROGRAMMING, T.NP_HARD, T.DISCRETE),
    _a("Viterbi",                 T.SEQUENCE, T.DYNAMIC_PROGRAMMING, T.PROBABILISTIC, T.OPTIMAL_SUBSTRUCTURE, T.ENCODING),

    # ── String Algorithms ───────────────────────────────────────
    _a("KMP",                     T.STRING, T.PATTERN_MATCHING, T.LINEAR),
    _a("Rabin-Karp",              T.STRING, T.PATTERN_MATCHING, T.HASHING, T.RANDOMIZED),
    _a("Aho-Corasick",            T.STRING, T.PATTERN_MATCHING, T.TEXT, T.TREE),
    _a("Boyer-Moore",             T.STRING, T.PATTERN_MATCHING, T.HEURISTIC),
    _a("Z-Algorithm",             T.STRING, T.PATTERN_MATCHING, T.LINEAR),

    # ── Probabilistic Data Structures ───────────────────────────
    _a("Bloom Filter",            T.SET, T.SEARCH, T.HASHING, T.PROBABILISTIC, T.SPARSE),
    _a("Count-Min Sketch",        T.STREAM, T.FREQUENCY, T.HASHING, T.PROBABILISTIC),
    _a("HyperLogLog",             T.STREAM, T.FREQUENCY, T.HASHING, T.PROBABILISTIC, T.LARGE_SCALE),
    _a("Consistent Hashing",      T.KEY_VALUE, T.HASHING, T.PARTITION, T.LARGE_SCALE),
    _a("Cuckoo Filter",           T.SET, T.SEARCH, T.HASHING, T.PROBABILISTIC),

    # ── Computational Geometry ──────────────────────────────────
    _a("Convex Hull",             T.POINT_CLOUD, T.SPATIAL, T.SORTING),
    _a("Line Sweep",              T.INTERVAL, T.SPATIAL, T.SORTING),
    _a("k-d Tree",                T.POINT_CLOUD, T.TREE, T.SPATIAL, T.SEARCH),
    _a("Voronoi Diagram",         T.POINT_CLOUD, T.SPATIAL, T.PARTITION),

    # ── Miscellaneous CS ────────────────────────────────────────
    _a("Union-Find",              T.SET, T.CONNECTIVITY, T.GRAPH, T.PARTITION),
    _a("LRU Cache",               T.KEY_VALUE, T.SEARCH, T.REAL_TIME),
    _a("Skip List",               T.SEQUENCE, T.SEARCH, T.PROBABILISTIC),
    _a("Reservoir Sampling",      T.STREAM, T.SAMPLING, T.RANDOMIZED, T.ONLINE),
    _a("Fisher-Yates Shuffle",    T.ARRAY, T.RANDOMIZED),
    _a("Monotone Stack",          T.ARRAY, T.SEQUENCE, T.MONOTONIC),
    _a("Sliding Window",          T.SEQUENCE, T.STREAM, T.AGGREGATION, T.ONLINE, T.INTERVAL),
    _a("Two Pointers",            T.ARRAY, T.SEQUENCE, T.SEARCH, T.LINEAR),
    _a("FFT",                     T.SEQUENCE, T.TRANSFORM, T.DIVIDE_AND_CONQUER, T.FREQUENCY),

    # ── Regression ──────────────────────────────────────────────
    _a("Linear Regression (OLS)", T.NUMERIC, T.TABLE, T.REGRESSION, T.LINEAR, T.CONTINUOUS),
    _a("Logistic Regression",     T.NUMERIC, T.TABLE, T.CLASSIFICATION, T.LINEAR, T.PROBABILISTIC),
    _a("Ridge Regression (L2)",   T.NUMERIC, T.TABLE, T.REGRESSION, T.LINEAR),
    _a("Lasso Regression (L1)",   T.NUMERIC, T.TABLE, T.REGRESSION, T.LINEAR, T.FEATURE_SELECTION, T.SPARSE),
    _a("Elastic Net",             T.NUMERIC, T.TABLE, T.REGRESSION, T.LINEAR, T.FEATURE_SELECTION),

    # ── Classification ──────────────────────────────────────────
    _a("SVM",                     T.NUMERIC, T.CLASSIFICATION, T.KERNEL, T.HIGH_DIMENSIONALITY),
    _a("Decision Tree",           T.TABLE, T.CLASSIFICATION, T.REGRESSION, T.TREE),
    _a("Random Forest",           T.TABLE, T.CLASSIFICATION, T.REGRESSION, T.ENSEMBLE),
    _a("XGBoost",                 T.TABLE, T.CLASSIFICATION, T.REGRESSION, T.ENSEMBLE, T.GRADIENT_BASED, T.LARGE_SCALE),
    _a("k-NN",                    T.NUMERIC, T.CLASSIFICATION, T.REGRESSION, T.SEARCH, T.SPATIAL),
    _a("Naive Bayes",             T.TABLE, T.CLASSIFICATION, T.PROBABILISTIC, T.BAYESIAN, T.TEXT),
    _a("AdaBoost",                T.TABLE, T.CLASSIFICATION, T.ENSEMBLE),

    # ── Clustering ──────────────────────────────────────────────
    _a("K-Means",                 T.NUMERIC, T.CLUSTERING, T.ITERATIVE, T.UNLABELED),
    _a("DBSCAN",                  T.NUMERIC, T.CLUSTERING, T.DENSITY_ESTIMATION, T.SPATIAL, T.UNLABELED),
    _a("Hierarchical Clustering", T.NUMERIC, T.CLUSTERING, T.TREE, T.UNLABELED),
    _a("GMM (EM)",                T.NUMERIC, T.CLUSTERING, T.PROBABILISTIC, T.ITERATIVE, T.UNLABELED),
    _a("Spectral Clustering",     T.NUMERIC, T.CLUSTERING, T.SPECTRAL, T.GRAPH, T.UNLABELED),
    _a("Mean Shift",              T.NUMERIC, T.CLUSTERING, T.DENSITY_ESTIMATION, T.KERNEL, T.UNLABELED),

    # ── Dimensionality Reduction ────────────────────────────────
    _a("PCA",                     T.NUMERIC, T.DIMENSIONALITY_REDUCTION, T.LINEAR, T.UNLABELED, T.DECOMPOSITION),
    _a("t-SNE",                   T.NUMERIC, T.DIMENSIONALITY_REDUCTION, T.NONLINEAR, T.EMBEDDING),
    _a("UMAP",                    T.NUMERIC, T.DIMENSIONALITY_REDUCTION, T.NONLINEAR, T.EMBEDDING, T.LARGE_SCALE),
    _a("LDA (Linear Discriminant)", T.NUMERIC, T.DIMENSIONALITY_REDUCTION, T.LINEAR, T.CLASSIFICATION, T.LABELED),
    _a("SVD",                     T.MATRIX, T.DECOMPOSITION, T.DIMENSIONALITY_REDUCTION, T.LINEAR),
    _a("NMF",                     T.MATRIX, T.DECOMPOSITION, T.ENCODING, T.TEXT),
    _a("Autoencoder",             T.NUMERIC, T.DIMENSIONALITY_REDUCTION, T.NONLINEAR, T.NEURAL_NETWORK, T.ENCODING),

    # ── Neural Networks ─────────────────────────────────────────
    _a("MLP",                     T.NUMERIC, T.CLASSIFICATION, T.REGRESSION, T.NEURAL_NETWORK, T.GRADIENT_BASED),
    _a("CNN",                     T.IMAGE, T.GRID, T.CLASSIFICATION, T.NEURAL_NETWORK, T.SPATIAL),
    _a("RNN / LSTM / GRU",       T.SEQUENCE, T.TIME_SERIES, T.NEURAL_NETWORK, T.TEMPORAL, T.PREDICTION),
    _a("Transformer",             T.SEQUENCE, T.TEXT, T.NEURAL_NETWORK, T.GENERATION, T.LARGE_SCALE),
    _a("GAN",                     T.IMAGE, T.GENERATION, T.NEURAL_NETWORK),
    _a("VAE",                     T.GENERATION, T.NEURAL_NETWORK, T.PROBABILISTIC, T.ENCODING),
    _a("Diffusion Model",         T.IMAGE, T.GENERATION, T.NEURAL_NETWORK, T.ITERATIVE, T.PROBABILISTIC),
    _a("GNN",                     T.GRAPH, T.NEURAL_NETWORK, T.CLASSIFICATION, T.EMBEDDING),

    # ── Feature Selection ───────────────────────────────────────
    _a("Mutual Information",      T.FEATURE_SELECTION, T.INFORMATION_THEORETIC, T.NONLINEAR),
    _a("Chi-Square Test",         T.FEATURE_SELECTION, T.DISCRETE, T.TABLE),
    _a("L1 Regularization Path",  T.FEATURE_SELECTION, T.LINEAR, T.SPARSE),
    _a("RFE",                     T.FEATURE_SELECTION, T.ITERATIVE, T.ENSEMBLE),

    # ── Time Series ─────────────────────────────────────────────
    _a("ARIMA",                   T.TIME_SERIES, T.PREDICTION, T.LINEAR, T.TEMPORAL),
    _a("Exponential Smoothing",   T.TIME_SERIES, T.PREDICTION, T.TEMPORAL),
    _a("Prophet",                 T.TIME_SERIES, T.PREDICTION, T.TEMPORAL, T.LARGE_SCALE),
    _a("Kalman Filter",           T.TIME_SERIES, T.PREDICTION, T.PROBABILISTIC, T.LINEAR, T.ONLINE),
    _a("HMM",                     T.SEQUENCE, T.TIME_SERIES, T.PROBABILISTIC, T.TEMPORAL, T.ENCODING),

    # ── Recommendation ──────────────────────────────────────────
    _a("Collaborative Filtering", T.TABLE, T.RECOMMENDATION, T.SIMILARITY, T.SPARSE),
    _a("Matrix Factorization",    T.MATRIX, T.RECOMMENDATION, T.DECOMPOSITION, T.SPARSE, T.LARGE_SCALE),
    _a("Content-Based Filtering", T.TABLE, T.TEXT, T.RECOMMENDATION, T.SIMILARITY),

    # ── Anomaly Detection ───────────────────────────────────────
    _a("Isolation Forest",        T.TABLE, T.ANOMALY_DETECTION, T.TREE, T.ENSEMBLE, T.UNLABELED),
    _a("One-Class SVM",           T.NUMERIC, T.ANOMALY_DETECTION, T.KERNEL, T.UNLABELED),
    _a("LOF",                     T.NUMERIC, T.ANOMALY_DETECTION, T.DENSITY_ESTIMATION, T.SPATIAL),
    _a("ADWIN",                   T.STREAM, T.ANOMALY_DETECTION, T.ONLINE, T.TEMPORAL),

    # ── Information Retrieval & NLP ─────────────────────────────
    _a("TF-IDF",                  T.TEXT, T.RANKING, T.FREQUENCY, T.SPARSE),
    _a("BM25",                    T.TEXT, T.RANKING, T.FREQUENCY, T.PROBABILISTIC),
    _a("PageRank",                T.GRAPH, T.RANKING, T.ITERATIVE),
    _a("Word2Vec",                T.TEXT, T.EMBEDDING, T.NEURAL_NETWORK, T.SIMILARITY),
    _a("BERT Embedding",          T.TEXT, T.EMBEDDING, T.NEURAL_NETWORK, T.LARGE_SCALE),

    # ── Optimization ────────────────────────────────────────────
    _a("Gradient Descent",        T.OPTIMIZATION, T.GRADIENT_BASED, T.ITERATIVE, T.CONTINUOUS),
    _a("SGD",                     T.OPTIMIZATION, T.GRADIENT_BASED, T.ITERATIVE, T.LARGE_SCALE, T.ONLINE),
    _a("Adam",                    T.OPTIMIZATION, T.GRADIENT_BASED, T.ITERATIVE, T.CONTINUOUS),
    _a("Simulated Annealing",     T.OPTIMIZATION, T.HEURISTIC, T.RANDOMIZED, T.DISCRETE, T.CONTINUOUS),
    _a("Genetic Algorithm",       T.OPTIMIZATION, T.HEURISTIC, T.RANDOMIZED, T.DISCRETE, T.NP_HARD),
    _a("Bayesian Optimization",   T.OPTIMIZATION, T.BAYESIAN, T.CONTINUOUS, T.APPROXIMATION),
    _a("Simplex (LP)",            T.OPTIMIZATION, T.LINEAR, T.CONTINUOUS),
    _a("Interior Point",          T.OPTIMIZATION, T.CONTINUOUS, T.LINEAR),

    # ── Probabilistic & Bayesian ────────────────────────────────
    _a("Bayesian Network",        T.GRAPH, T.PROBABILISTIC, T.BAYESIAN, T.DIRECTED),
    _a("MCMC",                    T.SAMPLING, T.PROBABILISTIC, T.BAYESIAN, T.HIGH_DIMENSIONALITY, T.ITERATIVE),
    _a("EM (Expectation-Max)",    T.ITERATIVE, T.PROBABILISTIC, T.OPTIMIZATION, T.UNLABELED),
    _a("Variational Inference",   T.PROBABILISTIC, T.BAYESIAN, T.OPTIMIZATION, T.APPROXIMATION, T.LARGE_SCALE),

    # ── Reinforcement Learning ──────────────────────────────────
    _a("Q-Learning",              T.OPTIMIZATION, T.TEMPORAL, T.DISCRETE),
    _a("Policy Gradient",         T.OPTIMIZATION, T.GRADIENT_BASED, T.NEURAL_NETWORK, T.CONTINUOUS),
    _a("MCTS",                    T.TREE, T.SEARCH, T.RANDOMIZED, T.HEURISTIC),
    _a("PPO",                     T.OPTIMIZATION, T.GRADIENT_BASED, T.NEURAL_NETWORK, T.LARGE_SCALE),

    # ── Additional ──────────────────────────────────────────────
    _a("LSH",                     T.HIGH_DIMENSIONALITY, T.SEARCH, T.HASHING, T.APPROXIMATION, T.SIMILARITY, T.LARGE_SCALE),
    _a("MinHash",                 T.SET, T.SIMILARITY, T.HASHING, T.APPROXIMATION),
    _a("SimHash",                 T.TEXT, T.SIMILARITY, T.HASHING, T.APPROXIMATION),
    _a("Apriori / FP-Growth",     T.TABLE, T.SET, T.PATTERN_MATCHING, T.FREQUENCY, T.DISCRETE),
)
