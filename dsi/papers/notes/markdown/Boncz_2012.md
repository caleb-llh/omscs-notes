# Vectorwise: Beyond Column Stores

**Authors:** Marcin Zukowski (Actian, Amsterdam, The Netherlands), Peter Boncz (CWI, Amsterdam, The Netherlands)  
**Year:** 2012

> **Context:** While C-Store popularized column stores, it relied on traditional tuple-at-a-time processing. Vectorwise (originating from the MonetDB/X100 project) argued that high performance is not just about storage layout, but also about vectorized execution to fully utilize modern CPU architectures (like SIMD and deep caches).

## Abstract
This paper tells the story of Vectorwise, a high-performance analytical database system, from multiple perspectives: its history from academic project to commercial product, the evolution of its technical architecture, customer reactions to the product and its future research and development roadmap.

One take-away from this story is that the novelty in Vectorwise is much more than just column-storage: it boasts many query processing innovations in its vectorized execution model, and an adaptive mixed row/column data storage model with indexing support tailored to analytical workloads. Another take-away is that there is a long road from research prototype to commercial product, though database research continues to achieve a strong innovative influence on product development.

---

## 1. Introduction
The history of Vectorwise goes back to 2003 when a group of researchers from CWI in Amsterdam, known for the MonetDB project, invented a new query processing model. This **vectorized query processing** approach became the foundation of the **X100 project**. In the following years, the project served as a platform for further improvements in query processing and storage. 

> **Intuition:** Traditional databases process one row (tuple) at a time, resulting in massive function call overhead and poor CPU cache utilization. Vectorwise processes data in small vectors (e.g., arrays of 1000 values for a single column), which allows the CPU to process them in a tight loop without branching, keeping the instruction pipeline full and leveraging SIMD instructions.

Initial results showed impressive performance improvements in decision support workloads and other application areas like information retrieval. Recognizing the commercial potential, CWI spun-out this project and founded **Vectorwise BV** as a company in 2008. Vectorwise BV combined the X100 processing and storage components with the mature higher-layer database components and APIs of the **Ingres DBMS** (a product of Actian Corp). After two years of cooperation and the delivery of the first versions of the integrated product aimed at the analytical database market, Vectorwise was acquired and became a part of Actian Corp.

---

## 2. Vectorwise Architecture
The architecture consists of two main layers:
*   **Upper layers (from Ingres):** Provides database administration tools, connectivity APIs, SQL parsing, and a cost-based query optimizer based on histogram statistics.
*   **Lower layers (from X100 project):** Delivers cutting-edge query execution and data storage.

The most important feature of Vectorwise—dazzling query execution speed—was carefully preserved and improved from its inception as an academic prototype into a full-fledged database product.

### Data Storage
While Vectorwise provides great performance for memory-resident data sets, when deployed on a high-bandwidth I/O subsystem, it allows efficient analysis of much larger datasets, often achieving performance close to that of buffered data for disk-resident data.

#### Storage Model (PAX-based)
Vectorwise stores data using a generalized row/column storage based on **PAX** (Partition Attributes Across). A table is stored in multiple PAX partitions, each containing a group of columns.

> **Mental Model:** Pure DSM (column store) is like storing each column in its own separate file. Pure NSM (row store) is like storing the whole table in one file. PAX is a hybrid: the disk is divided into large blocks, and within each block, data is stored column by column. This provides the cache-friendly benefits of column stores while keeping related attributes of a row somewhat close together on disk.

*   **DSM/PAX:** Each column in a separate PAX group (similar to pure column store).
*   **NSM/PAX:** All columns in one PAX group (similar to pure row store).

The grouping of a table in PAX partitions can be controlled by explicit DDL or is **self-tuned**:
*   **Nullable Columns:** Represented internally as a column containing values and a boolean column indicating whether the value is NULL. This separation improves query processing efficiency (avoiding hard-to-predict branching and allowing SIMD instructions). Both are stored in the same PAX partition.
*   **Composite Primary Keys:** Automatically stored in the same partition.
*   **Small Tables:** Stored using NSM/PAX to avoid wasting space with empty disk blocks, as Vectorwise uses relatively large block-sizes (e.g., 512KB on magnetic disks, 32KB for SSDs).
*   **Very Wide Tables:** A more advanced PAX grouping algorithm clusters certain columns to limit the number of PAX groups, reducing the buffer memory needed for table scans.

#### Compression
Data on disk is stored in compressed form, using automatically selected compression schemes and tuned parameters. Vectorwise uses schemes that allow **very high decompression ratios with a cost of only a few cycles per tuple**. 
*   Because of this low overhead, data can be stored compressed in the buffer pool and decompressed immediately before query processing, effectively increasing the buffer pool size and reducing I/O.
*   While initially avoiding compressed execution to keep the query executor simple, Vectorwise recently introduced forms of **compressed execution** for high-benefit cases (e.g., aggregation on Run-Length Encoding (RLE) or operations on dictionary-compressed strings).

#### Indexing
*   **Clustered Index:** Users can declare one index per table. The physical tuple order is determined by the index keys, allowing push-down of range-predicates on the index keys. For foreign keys, tuple order is derived from the referenced table, accelerating foreign key joins.
*   **MinMax Indices:** Automatically kept on all columns (based on small materialized aggregates). They store metadata (e.g., Min and Max values) about values in a range of records, allowing quick elimination of ranges during scan operations. They are highly effective when there are correlations between attribute values and tuple position (e.g., date-time columns in fact tables).

#### I/O and Buffer Pool
Focused on providing optimal performance for concurrent scan-intensive queries typical of analytical workloads. The product uses a highly effective variant of intelligent data buffering that optimizes average query latency and throughput by determining the order to fetch tuples at runtime based on the interest of all concurrent queries.

#### High-Performance Updates
Uses a differential update mechanism based on **Positional Delta Trees (PDT)**. A three-level design (small private PDT, shared CPU-cache resident PDT, and potentially large RAM-resident PDT) offers snapshot isolation without slowing down read-only queries. PDTs organize differences by position rather than by key value, making the task of merging differences during a table scan virtually cost-free.

> **Tradeoff:** Organizing updates by physical position (PDT) makes merging updates during a full column scan extremely fast (avoiding expensive key joins). However, this means if the base data shifts physically (e.g., during reorganization or vacuuming), all these positional references must be carefully translated and managed.

### Query Execution
The core technology behind Vectorwise's high processing speed is its **vectorized processing model**.

> **Common Confusion:** Vectorized execution is often confused with column-oriented storage. They are orthogonal. You can have a row store with vectorized execution, or a column store with tuple-at-a-time execution (like early C-Store). Vectorwise combines both for maximum analytical performance.

*   **Reduced Overhead:** Dramatically reduces the interpretation overhead typical of tuple-at-a-time processing systems.
*   **Modern CPU Exploitation:** Exposes possibilities to exploit super-scalar execution and SIMD instructions.
*   **Cache Efficiency:** Focuses on storing data in the CPU cache, reducing main-memory traffic.

**Improvements to the vectorized execution model:**
1.  Lazy vectorized expression evaluation.
2.  Choosing different function implementations depending on the environment.
3.  Pushing up selections to enable more SIMD predicate evaluation.
4.  NULL-processing optimizations.
5.  **NSM Record Layout during Execution:** Strict adherence to vertical (columnar) layout was dropped in favor of NSM layout for parts of tuples where access patterns make it more beneficial (mostly in hash tables).
6.  **Volcano-based Parallelism:** Based on exchange operators, allowing efficient scaling to multiple cores.
7.  **Bloom-filters:** Highly efficient Bloom-filters applied to speed-up join processing.
8.  **Hardware Cooperation:** Exploited new CPU features (e.g., large TLB pages, SSE4.2 instructions for text data) through cooperation with Intel.

**Future roadmap for query execution:** Execution on compressed data, intelligent use of just-in-time (JIT) compilation of complex predicates, and MPP cluster capabilities for scale-out architectures.

---

## 3. Vectorwise Experiences
Vectorwise 1.0 was released in June 2010. While its unparalleled processing performance was praised, it faced challenges typical for young software (missing features, update expectations, stability issues). Vectorwise 2.0 (November 2011) addressed these, adding optimized loading, full transactional support, better storage management, parallel execution, temporary tables, analytical SQL 1999, disk-spilling operations, and a Windows version.

### Customer Reactions
Performance improvements led customers to adopt previously impossible approaches:
*   **Removing indices:** Efficient in-memory and on-disk scan performance combined with optimized filtering outperformed indexed systems.
*   **Normalizing tables:** Quick data transformations made large-volume data normalizations possible.
*   **De-normalizing tables:** Alternatively, performance was sufficient even with de-normalized tables, simplifying schemas.
*   **Running on raw data:** Avoided expensive data precomputations.
*   **Full data reloads:** Faster loading made full data reloads feasible.

The technical and organizational contributions of the mature Ingres product (connectivity options, solid SQL support, tools, worldwide 24/7 support) were also crucial to its success.

### Adoption Challenges
*   **Migrations:** Online data transfer from transactional systems and migrating complex application logic (e.g., PL/SQL) proved labor-intensive.
*   **Data Freshness:** Users demanded sub-second data loading latency, prompting improvements in incremental loads, data-update capabilities (ACID properties), and the introduction of Vectorstream.
*   **Complex Schemas:** Scenarios with hundreds of databases and thousands of tables/attributes stressed system capabilities, requiring schema reorganizations and system improvements.

---

## 4. Vectorwise Research Program
Vectorwise maintains strong academic roots and a continued research track. Licensees include various universities, and multiple MSc/PhD projects have been pursued.
*   **Completed topics:** Volcano-style multi-core parallelism, JIT compilation of predicates, non-intrusive compressed execution, materialization/caching of intermediate query results (Recycler idea), cooperative scans for buffer management, and XML storage/processing.
*   **Ongoing projects:** Improving vectorized execution performance, accelerating processing with multi-dimensional data organization, and improving MPP architecture scalability.

---

## 5. Conclusion
Achieving truly high performance requires much more than just "column storage." Vectorwise's success is attributed to its vectorized execution, adaptive storage, and the functionality, usability, and support capabilities provided by its integration with Ingres. A solid innovation pipeline continues to bolster the product's performance and capabilities for the future.