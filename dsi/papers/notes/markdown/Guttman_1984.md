# R-Trees: A Dynamic Index Structure for Spatial Searching

## Abstract
Traditional indexing methods are not well-suited to data objects of non-zero size in multi-dimensional spaces. The R-tree is a dynamic index structure for spatial searching. It performs well and is useful for database systems handling spatial applications like computer-aided design (CAD) and geo-data.

> **Intuition:** A B-Tree organizes 1D data by splitting numbers into ranges. An R-Tree organizes 2D/3D data by splitting space into hierarchical, overlapping bounding boxes (rectangles).

## 1. Introduction
Spatial data often occupy regions of non-zero size in multiple dimensions (e.g., counties on a map). A common operation is a range search.
Classical 1D structures (hash tables, B-trees) do not work for multi-dimensional range searches.
Other structures have drawbacks:
- Cell methods: cell boundaries must be decided in advance.
- Quad trees / k-d trees: do not consider secondary memory paging.
- K-D-B trees: useful only for point data.
- Corner stitching: assumes homogeneous primary memory.
- Grid files: map objects to points in higher-dimensional space.
The R-tree represents data objects by intervals in several dimensions.

## 2. R-Tree Index Structure
An R-tree is a height-balanced tree similar to a B-tree. It is completely dynamic: inserts and deletes can be intermixed with searches, and no periodic reorganization is needed.
- **Leaf nodes** contain entries: `(I, tuple-identifier)` where `I` is an n-dimensional bounding box.
- **Non-leaf nodes** contain entries: `(I, child-pointer)` where `I` covers all rectangles in the child node.

> **Mental Model:** Picture nested Tupperware boxes. The outermost box is the root node. Inside it are a few smaller boxes (child nodes), which may overlap. Inside those are even smaller boxes, until you reach the actual objects at the leaves.

Properties (where M is max entries per node, m <= M/2 is min entries):
1. Every leaf node has between `m` and `M` records (unless root).
2. `I` in a leaf is the smallest bounding rectangle for the object.
3. Every non-leaf node has between `m` and `M` children (unless root).
4. `I` in a non-leaf is the smallest bounding rectangle for all its child's rectangles.
5. Root has at least 2 children (unless leaf).
6. All leaves are on the same level.
Height of R-tree is at most `log_m(N) - 1`. Worst-case space utilization is `m/M`.

## 3. Searching and Updating

### 3.1 Searching
Descends the tree from the root. More than one subtree under a node may need to be searched because bounding boxes can overlap.
Algorithm: Check each entry in a node. If its bounding box overlaps the search area, recursively search that child. At leaves, return matching tuples.

> **Common Confusion:** Unlike B-trees where a search goes down exactly one path, R-tree searches might traverse *multiple* paths because sibling bounding boxes can overlap. The worse the overlap, the slower the search!

### 3.2 Insertion
Similar to B-tree. New records added to leaves. Overflowing nodes split, and splits propagate up.
- **ChooseLeaf:** Descend the tree to find the best leaf. At each step, choose the subtree whose covering rectangle needs the *least enlargement* to include the new entry. Resolve ties by smallest area.
- **AdjustTree:** Ascend to root, adjusting covering rectangles and propagating splits.

### 3.3 Deletion
- **FindLeaf:** Locate leaf containing the entry.
- Remove entry.
- **CondenseTree:** If a node becomes under-full (fewer than `m` entries), it is eliminated. Its remaining entries are added to a set Q and re-inserted.
Re-insertion is preferred over B-tree-like merging because it incrementally refines the spatial structure of the tree.

> **Tradeoff:** Re-inserting orphaned entries during deletion is slightly more expensive upfront than just merging adjacent nodes (like a B-tree), but it continually self-optimizes the tree, preventing performance decay over time.

### 3.5 Node Splitting
When adding to a full node, M+1 entries must be divided into two nodes. Goal: Minimize the total area of the two covering rectangles after the split.
1. **Exhaustive Algorithm:** Generates all possible groupings. Too slow (exponential).
2. **Quadratic-Cost Algorithm:** Cost is O(M^2). Picks two "seeds" that would waste the most area if put together. Then assigns remaining entries one by one, picking the entry showing the greatest difference in area expansion between the two groups.
3. **Linear-Cost Algorithm:** Cost is O(M). Picks seeds by finding the entries that are furthest apart along any dimension (normalized). Then simply assigns remaining entries in arbitrary order to the group needing least enlargement.

## 4. Performance Tests
Implemented in C under Unix. Tested with varying page sizes (128 to 2048 bytes), `m` values, and the three split algorithms.
- **Insertion Cost:** Linear algorithm is fastest. CPU time hardly increased with page size. Quadratic is slower but reasonable.
- **Deletion Cost:** Strongly affected by the minimum node fill requirement (`m`). Stricter fill requirements cause more frequent under-full nodes and splits during re-insertion.
- **Search Performance:** Very insensitive to the node split algorithm and fill requirements. Exhaustive is slightly better structurally, but Linear and Quadratic provide excellent search performance.
- **Space Efficiency:** Stricter node fill criteria produce smaller indexes.
- **Scalability:** Insert/delete cost is independent of tree width but affected by tree height. Search cost per qualifying record drops as more data is retrieved.

## 5. Conclusions
The R-tree is highly useful for indexing non-zero size spatial data objects. Nodes corresponding to disk pages (e.g., 1024 bytes) give good performance.
The Linear node-split algorithm proved to be as good as more expensive techniques in terms of search performance, while being very fast.
R-trees would be easy to add to any relational database system.