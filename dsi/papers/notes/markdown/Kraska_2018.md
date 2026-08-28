# The Case for Learned Index Structures

**Authors:** Tim Kraska (MIT), Alex Beutel, Ed H. Chi, Jeffrey Dean, Neoklis Polyzotis (Google)  
**Year:** 2018

> **Context:** In 2018, machine learning and hardware accelerators (GPUs, TPUs) were experiencing massive growth, while traditional data structures like B-Trees remained largely unchanged, relying heavily on CPU branching. This paper proposed a radical idea: treat fundamental data structures as machine learning models.

## Abstract
Indexes are models: a B-Tree-Index maps a key to the position of a record within a sorted array, a Hash-Index maps a key to a position within an unsorted array, and a BitMap-Index predicts if a record exists. This exploratory research posits that all existing index structures can be replaced with other types of machine learning (ML) models, including deep-learning models, termed **learned indexes**. A model can learn the sort order or structure of lookup keys and use this signal to effectively predict the position or existence of records. Initial results using neural nets show outperformance over cache-optimized B-Trees by up to 70% in speed while saving an order-of-magnitude in memory on real-world datasets.

---

## 1. Introduction
Traditional indexes (B-Trees, Hash-maps, Bloom filters) are general-purpose data structures. They assume nothing about the data distribution and do not take advantage of common patterns in real-world data. 

> **Intuition:** If you have a sorted array of contiguous integers from 1 to 1,000,000, you don't need a B-Tree to find the value 500,000. You just look at the 500,000th position in the array. Real data isn't perfectly contiguous, but it often follows predictable patterns. A model can "learn" this pattern and calculate the position instead of navigating a tree.

**Core Idea:** Machine learning opens up the opportunity to learn a model that reflects patterns in the data, enabling the automatic synthesis of specialized index structures (learned indexes).

While ML models lack traditional semantic guarantees and neural networks are compute-expensive, these are not insuperable obstacles:
1.  **Semantic Guarantees:** Many data structures can be decomposed into a learned model and an auxiliary structure to provide the same guarantees (e.g., using a local search to fix B-Tree predictions or an overflow filter to fix false negatives).
2.  **Compute Expense:** Modern hardware (CPUs with SIMD, GPUs, TPUs) can execute thousands of neural net operations in a single cycle. Replacing branch-heavy index structures with neural networks allows databases to benefit from hardware trends.

---

## 2. Range Index (Replacing B-Trees)
A B-Tree is essentially a regression tree model: it takes a key as input and predicts the position of a data record in a sorted set, providing a min- and max-error guarantee. 

> **Mental Model:** A B-Tree acts as a "map" that takes a key and navigates down pointers to find the physical location. A Learned Index acts as a "function" that takes a key, performs arithmetic, and estimates the physical location, followed by a short local scan to find the exact spot.

*   Because data is sorted, any prediction error can be easily corrected by a local search (e.g., exponential search) around the prediction. 
*   Therefore, B-Trees can be replaced with any regression model (e.g., linear regression or neural nets). 
*   **Advantage:** This transforms the $O(\log n)$ cost of a B-Tree lookup into a potentially constant operation (e.g., a simple linear model).

### 2.1 Model Complexity
Can we afford ML models? A B-Tree traversal over a page takes ~50 cycles (hard to parallelize). A modern CPU does 8-16 SIMD operations per cycle. A model is faster as long as it has a better precision gain than a B-Tree per ~400 arithmetic operations. Furthermore, ML accelerators (GPUs/TPUs) can perform tens of thousands of operations per cycle, vastly outscaling CPU branch execution.

### 2.2 Range Index Models are CDF Models
Predicting a position in a sorted array effectively approximates the **Cumulative Distribution Function (CDF)** of the data:
$$p = F(Key) \times N$$
Where $p$ is the position estimate, $F(Key)$ is the estimated CDF (likelihood to observe a key $\le$ lookup key), and $N$ is the total number of keys. Thus, indexing literally requires learning a data distribution.

### 2.3 Challenges with a Naïve Learned Index
A naïve implementation of a neural net index in TensorFlow revealed limitations:
1.  TensorFlow has significant invocation overhead for small models.
2.  B-Trees are great at overfitting data for the "last mile" of accuracy, whereas standard ML models are efficient at general CDF shapes but struggle with individual instance-level irregularities.
3.  B-Trees are highly cache-efficient, whereas standard neural nets require many multiplications using all weights.

---

## 3. The Recursive Model Index (RMI)
To overcome the "last mile" accuracy problem, the authors propose a hierarchy of models (inspired by Mixture of Experts). 

### 3.1 Learning Index Framework (LIF)
An index synthesis system that generates, optimizes, and tests index configurations. It extracts weights from trained TensorFlow models and generates efficient, overhead-free C++ code, allowing simple models to execute in ~30 nanoseconds.

### 3.2 RMI Architecture
*   **Hierarchy:** At each stage, a model takes the key as input and picks another model in the next stage, until the final stage predicts the position. 
*   **Benefits:** Separates model size/complexity from execution cost, easily learns the overall CDF shape, divides space into smaller sub-ranges (like a B-Tree), and requires no search process between stages (can be executed as a sparse matrix multiplication).

### 3.3 Hybrid Indexes
RMI allows mixing models. For example, a small Neural Net at the top layer, thousands of simple linear regression models at the bottom, or even falling back to traditional B-Trees for subsets of data that are exceptionally hard to learn. This bounds the worst-case performance of learned indexes to that of B-Trees.

### 3.4 Search Strategies
Since the model predicts an actual position, search strategies can be biased:
*   **Model Biased Search:** Binary search where the first middle point is the predicted position.
*   **Biased Quaternary Search:** Takes three initial points ($pos - \sigma, pos, pos + \sigma$) to leverage hardware pre-fetching, assuming the prediction is highly accurate.

### 3.5 Indexing Strings
Strings are tokenized into feature vectors (e.g., ASCII/Unicode decimal values up to a maximum length $N$). The model architecture scales linearly with input length, using feed-forward neural nets.

### 3.6 & 3.7 Training and Results
*   **Training:** Simple models (linear regression) train in a single pass. Neural nets train in minutes. 
*   **Integer Datasets:** Tested on Weblogs, Maps, and synthetic Lognormal data. The learned index dominated the B-Tree in almost all configurations, being up to **1.5x–3x faster** while being up to **two orders-of-magnitude smaller**.
*   **String Datasets:** Speedups were less prominent due to the high cost of model execution on CPUs and the expense of searching over strings, but still achieved smaller memory footprints. Hybrid models and quaternary search were highly effective here.

---

## 4. Point Index (Replacing Hash-Maps)
Hash-maps use a hash function to map keys to array positions. The key challenge is preventing **conflicts** (collisions). 

### 4.1 The Hash-Model Index
Learning the CDF of the key distribution can yield a better hash function. By scaling the CDF by the targeted Hash-map size $M$: $h(K) = F(K) \times M$. If the model perfectly learns the empirical CDF, there are zero conflicts. This learned hash function is orthogonal to the Hash-map architecture (e.g., separate chaining).

### 4.2 Results
*   Learned models reduced conflicts by up to **77%** over the integer datasets at a reasonable model execution cost (25-40ns).
*   For a separate chaining Hash-map, learned hash functions reduced wasted storage by up to 80% with only a 13ns latency increase.
*   Benefits highly depend on payload size, Hash-map architecture, and workload. High-cost conflict scenarios (e.g., distributed Hash-maps over RDMA) see the largest potential benefits.

---

## 5. Existence Index (Replacing Bloom Filters)
Bloom filters are highly space-efficient probabilistic data structures for set membership (no false negatives, potential false positives). 

### 5.1 Learned Bloom Filters
If there is learnable structure differentiating what is inside vs. outside the set, more efficient representations are possible. 
*   **Classification Problem:** Train a binary classifier (e.g., RNN/CNN for strings) to predict if a query $x$ is a key or non-key. The output $f(x)$ is the probability the key exists.
*   **Threshold & Overflow:** Set a threshold $\tau$. If $f(x) \ge \tau$, predict it exists. To maintain the "zero false negative" guarantee, create a traditional **overflow Bloom filter** for the set of false negatives ($f(x) < \tau$).
*   **Model-Hashes:** Alternatively, use the classifier output to create a hash function $d = \lfloor f(x) \times m \rfloor$ that maps most keys to higher bit positions and non-keys to lower bit positions, using this within a standard Bloom filter setup.

### 5.2 Results
*   Tested on keeping track of blacklisted phishing URLs.
*   A learned Bloom filter (RNN model + overflow Bloom filter) achieved a **36% reduction in memory** over a traditional Bloom filter at a 1% False Positive Rate (FPR), and a 15% reduction at a 0.1% FPR.
*   Learned models can easily incorporate additional features (e.g., WHOIS data) to improve accuracy and further decrease the Bloom filter size.

---

## 6 & 7. Related Work, Conclusion, and Future Work
*   **Related Work:** Orthogonal to cache-conscious B-Trees (FAST, CSB+-tree), index compression, perfect hashing, and succinct data structures.
*   **Future Directions:**
    *   **Inserts/Updates:** Appends might be $O(1)$ if the model generalizes well. Delta-indexes can handle other inserts, periodically merging and retraining.
    *   **Multi-Dimensional Indexes:** Neural nets are excellent at capturing high-dimensional relationships.
    *   **Learned Algorithms:** CDF models could speed up sorting (e.g., roughly sorting data and correcting with insertion sort) and joins.
    *   **GPUs/TPUs:** Will make learned indexes vastly more valuable due to extreme arithmetic scaling.

**Conclusion:** Machine learned models have the potential to provide significant benefits over state-of-the-art indexes, opening an entirely new research direction for a decades-old field by deeply embedding learned models into algorithms and data structures.