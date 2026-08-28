# C-Store: A Column-oriented DBMS

**Authors:** Mike Stonebraker et al. (MIT CSAIL, Brandeis University, UMass Boston, Brown University)  
**Year:** 2005

> **Context:** In the early 2000s, OLTP (Online Transaction Processing) and OLAP (Online Analytical Processing) workloads were diverging, yet most commercial systems used a one-size-fits-all row-store architecture. C-Store was the foundational paper that sparked the column-store revolution for analytics.

## Abstract
This paper presents the design of a read-optimized relational DBMS (C-Store) that contrasts sharply with most current systems, which are write-optimized. Key design differences include:
*   Storage of data by column rather than by row.
*   Careful coding and packing of objects into storage (including main memory) during query processing.
*   Storing an overlapping collection of column-oriented projections, rather than the current fare of tables and indexes.
*   A non-traditional implementation of transactions which includes high availability and snapshot isolation for read-only transactions.
*   Extensive use of bitmap indexes to complement B-tree structures.

Preliminary performance data on a subset of TPC-H shows that C-Store is substantially faster than popular commercial products.

---

## 1. Introduction
Most major DBMS vendors implement **write-optimized** row-store architectures (placing record attributes contiguously), which are effective for OLTP-style applications. In contrast, systems oriented toward ad-hoc querying of large amounts of data (e.g., data warehouses, CRM, electronic library catalogs) should be **read-optimized**. 

A **column store architecture** (where values for a single column are stored contiguously) is more efficient for read-mostly environments. It avoids bringing irrelevant attributes into memory, which is highly advantageous for warehouse environments where queries involve aggregates over large numbers of data items.

> **Intuition:** If you have a table with 100 columns but your query only aggregates on one or two (e.g., `SUM(salary)` grouped by `department`), a row store forces you to read all 100 columns from disk into memory. A column store only reads the required columns, saving massive amounts of disk I/O.

**Read-Optimized vs. Write-Optimized Distinctions:**
1.  **CPU-to-Disk Tradeoff:** CPUs are getting faster much quicker than disk bandwidth. It makes sense to trade abundant CPU cycles to save disk bandwidth by:
    *   **Coding:** Encoding data elements into a more compact form (e.g., coding states into 6 bits instead of strings).
    *   **Dense-packing:** Packing N values (K bits each) into N * K bits in storage. Query executors should operate on this compressed representation whenever possible.

> **Tradeoff:** By keeping data heavily compressed on disk and in memory, C-Store spends more CPU cycles decompressing it, but drastically reduces disk I/O. Since disk I/O is typically the bottleneck for analytical workloads, this tradeoff is highly favorable.
2.  **Indexing and Storage:** Commercial DBMSs use auxiliary B-tree indexes, which perform poorly in read-optimized worlds. C-Store stores collections of columns sorted on some attribute(s), called **"projections."** Multiple projections can exist, each sorted on different attributes, opening optimization opportunities.
3.  **Grid Computing:** C-Store is designed for a "shared nothing" grid environment, automatically horizontally partitioning data across disks of various nodes, facilitating intra-query parallelism.
4.  **High Availability (K-safety):** C-Store allows redundant objects to be stored in different sort orders on different nodes, providing both higher retrieval performance and high availability (tolerating K site failures).
5.  **Handling Updates:** To resolve the tension between providing updates and optimizing read structures, C-Store combines a read-optimized column store (**RS**) and an update/insert-oriented writeable store (**WS**), connected by a **Tuple Mover**.

> **Mental Model:** Think of the WS as a fast, uncompressed, temporary cache for incoming changes (inserts/updates), and the RS as the massive, highly compressed archive. The Tuple Mover acts as a background garbage collector that merges the WS into the RS.
6.  **Snapshot Isolation:** To avoid dynamic locking overhead, read-only queries run in historical mode (Snapshot Isolation) using a timestamp T, ignoring elements inserted after T.
7.  **Column-Oriented Optimizer and Executor:** C-Store builds software specifically for column-oriented operations.

---

## 2. Data Model
C-Store supports the standard relational logical data model (tables, attributes, primary/foreign keys, SQL semantics). However, data is physically stored as **projections**.

> **Common Confusion:** A "projection" in C-Store is not just the mathematical projection from relational algebra (selecting columns). In C-Store, a projection is a materialized, physical copy of a subset of columns from one or more tables, sorted by a specific key. This replaces traditional indexes.

*   **Projections:** Anchored on a logical table *T*, containing one or more attributes from *T* and possibly attributes from other tables (via n:1 foreign key relationships). Projections retain duplicate rows and have the same number of rows as the anchor table.
*   **Column-wise Storage:** Tuples in a projection are stored column-wise and are sorted by a **sort key** (one or more columns in the projection).
*   **Segments:** Every projection is horizontally partitioned into one or more segments (value-based partitioning on the sort key), associated with a segment identifier (Sid).
*   **Storage Keys (SK):** Values from different columns in the same segment belonging to the same logical row have matching storage keys. In RS, SKs are inferred from physical position (1, 2, 3...). In WS, SKs are explicitly stored as integers larger than the largest RS SK.
*   **Join Indexes:** Used to reconstruct complete rows from different projections. A join index from projection T1 to T2 maps the segments of T1 to the segment ID and SK of the corresponding tuple in T2. Join indexes are expensive to maintain during updates, so C-Store relies on overlapping projections to keep their number small.

---

## 3. RS (Read-optimized Store)
RS breaks any segment into its constituent columns, stored in order of the sort key. SKs are inferred from the ordinal number of the record.

### 3.1 Encoding Schemes
Columns in RS are compressed using one of 4 encodings, depending on their ordering (self-order vs. foreign-order) and the proportion of distinct values.
*   **Type 1 (Self-order, few distinct values):** Represented by a sequence of triples `(v, f, n)` (value, first position, number of appearances). Uses a densepack clustered B-tree index.
*   **Type 2 (Foreign-order, few distinct values):** Represented by a sequence of tuples `(v, b)` (value, bitmap of positions). Bitmaps are run-length encoded. Uses B-tree "offset indexes".
*   **Type 3 (Self-order, many distinct values):** Values are represented as deltas from the previous value. Block-oriented: first entry is a value and SK, subsequent values are deltas. Uses a densepack B-tree index.
*   **Type 4 (Foreign-order, many distinct values):** Values are left unencoded (with a densepack B-tree index).

### 3.2 Join Indexes
Join indexes are special columns containing `(sid, storage_key)` pairs, used to connect projections and integrate RS and WS.

---

## 4. WS (Writeable Store)
WS is a column store implementing the identical physical DBMS design as RS but is optimized for efficient transactional updates.
*   **Storage Key:** SK is explicitly stored in each WS segment.
*   **Partitioning:** Horizontally partitioned exactly like RS (1:1 mapping between RS and WS segments).
*   **Data Representation:** Uncompressed. Columns are pairs `(v, sk)` represented in a conventional B-tree on the `sk`. The sort key is represented by pairs `(s, sk)` in a B-tree on `s`.
*   **Join Indexes:** Pointers to records that can be in either RS or WS, partitioned and co-located with the "sending" segment.

---

## 5. Storage Management
C-Store automatically allocates segments to nodes in a grid.
*   Columns in a single segment of a projection are co-located.
*   Join indexes are co-located with their "sender" segments.
*   WS segments are co-located with corresponding RS segments.
*   Big columns are stored in individual files in the underlying OS (raw devices offer little benefit over modern file systems).

---

## 6. Updates and Transactions
*   **Inserts:** Assigned a globally unique SK (locally unique counter + site id) larger than any RS key. Handled via B-tree structures in WS.
*   **Deletes/Updates:** Read-only queries use **snapshot isolation** to avoid locking. Updates are turned into an insert and a delete.
    *   **Insertion Vector (IV):** WS maintains the epoch in which a record was inserted.
    *   **Deleted Record Vector (DRV):** WS maintains a sparse, Type 2-encoded vector of the epoch a tuple was deleted (0 if not deleted).

### 6.1 Providing Snapshot Isolation
Transactions run at an Effective Time (ET). A record is visible if inserted before ET and deleted after ET. 
*   **High Water Mark (HWM):** The most recent time with no uncommitted transactions. Read-only queries run as of the HWM.
*   **Low Water Mark (LWM):** The earliest effective time a read-only transaction can run. The Tuple Mover ensures no RS records were inserted after LWM.
*   **Epochs:** Used as coarse granularity timestamps. A Timestamp Authority (TA) manages epoch transitions and tracks when all sites complete transactions for an epoch.

### 6.2 Locking-based Concurrency Control
Read-write transactions use strict two-phase locking. C-Store uses a NO-FORCE, STEAL policy, logs only UNDO records (logical logging), and avoids the PREPARE phase of two-phase commit (2PC).

### 6.3 Recovery
Leverages K-safety. 
*   **No data loss:** Roll forward queued updates.
*   **Catastrophic failure (RS & WS destroyed):** Reconstruct from other projections/join indexes on remote sites.
*   **WS damaged, RS intact (Common case):** Reconstruct WS by querying remote projections for records inserted after the local RS's last merge time (`t_lastmove`). If necessary, use a Tuple Mover log from remote sites.

---

## 7. Tuple Mover
The Tuple Mover is a background task that moves blocks of tuples from a WS segment to the corresponding RS segment.
*   **Merge-Out Process (MOP):** Finds all WS records inserted at/before LWM. Discards those deleted at/before LWM. Moves the rest to RS.
*   Creates a new RS segment (`RS'`), merges data from old RS and WS, assigns new SKs, updates join indexes and DRV, and then cuts over to `RS'`.

---

## 8. C-Store Query Execution

### 8.1 Query Operators and Plan Format
Operators accept/produce projections, columns, bitstrings, predicates, join indexes, attribute names, or expressions.
1.  **Decompress:** Converts compressed to Type 4 (uncompressed).
2.  **Select:** Produces a bitstring representation of the result.
3.  **Mask:** Restricts a projection using a bitstring.
4.  **Project:** Standard relational projection.
5.  **Sort:** Sorts columns by a subset of columns.
6.  **Aggregation:** Computes SQL-like aggregates.
7.  **Concat:** Combines projections sorted in the same order.
8.  **Permute:** Permutes a projection according to a join index.
9.  **Join:** Joins projections according to a predicate.
10. **Bitstring Operators:** BAnd, BOr, BNot.

Uses a modified iterator interface returning 64K blocks from a single column (coupling data flow with control flow while matching the column-based model).

### 8.2 Query Optimization
Uses a Selinger-style cost-based optimizer (likely two-phase). It differs from traditional optimizers by:
1.  Accounting for compressed representations (execution cost depends on compression type).
2.  Deciding which set of projections to use.
3.  Deciding when/where in the plan to mask a projection using a bitstring.

---

## 9. Performance Comparison
Evaluated on a subset of TPC-H (scale 10) comparing C-Store against a commercial Row Store and a commercial Column Store.
*   **Storage Budget:** C-Store used ~2 GB, Row Store needed ~4.5 GB, Column Store needed ~2.65 GB. C-Store's smaller size is due to superior compression and absence of padding, despite redundancy.
*   **Speed:** On average, C-Store was **164x faster** than the Row Store and **21x faster** than the Column Store in space-constrained cases. 
*   **Reasons for Performance:** Column representation (avoids reading unused attributes), overlapping projections (multiple orderings), better compression, and operating directly on compressed data.

---

## 10. Related Work
*   **Data Cubes/Materialized Views:** Effective for anticipated queries, but C-Store targets ad-hoc workloads.
*   **Data Mirrors:** Achieves better query performance, but C-Store uniquely targets both update workloads and ad-hoc queries simultaneously.
*   **Column Stores (Sybase IQ, Monet, etc.):** Typically store data in entry sequence; lack C-Store's hybrid WS/RS architecture and overlapping projections.
*   **Compressed Databases:** Operating on compressed data is a known concept, but C-Store combines it uniquely with its architecture.

---

## 11. Conclusions
C-Store represents a radical departure from current DBMS architectures, specifically targeting the "read-mostly" market. Innovative contributions include:
*   A column store representation and query engine.
*   A hybrid architecture allowing transactions on a column store.
*   Economized storage through coding and dense-packing.
*   A data model based on overlapping projections instead of tables/indexes.
*   Optimized for shared-nothing architectures.
*   Distributed transactions without redo logs or 2PC.
*   Efficient snapshot isolation.