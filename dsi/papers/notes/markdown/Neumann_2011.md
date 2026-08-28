# Efficiently Compiling Efficient Query Plans for Modern Hardware

**Author:** Thomas Neumann (Technische Universität München)
**Conference:** VLDB 2011

## 1. Introduction
As database systems increasingly fit data into main memory, disk I/O ceases to be the bottleneck, and query performance becomes heavily bounded by raw CPU costs. 

**The Problem with Existing Models:**
- **Iterator Model (Volcano-style):** The standard query execution model where operators pull data via a `next()` function call. This is highly flexible but CPU-inefficient due to millions of virtual function calls, poor code/data locality, and frequent branch mispredictions.
- **Block-oriented/Vectorized Processing:** Passes batches of tuples to amortize function call costs. However, this forces materialization (breaking pure pipelining), increasing memory bandwidth consumption. Hand-written C++ code routinely outperforms even the fastest vectorized systems.

> **Common Confusion:** One might think that vectorized processing (processing batches of tuples) is always the fastest approach. While it is better than Volcano, it still writes intermediate batches to memory/cache. The fastest approach is keeping the tuple in CPU registers for as long as possible.

**The Solution:**
Compile queries directly into highly optimized machine code using the **LLVM compiler framework**. 
- Processing becomes **data-centric** rather than operator-centric.
- Data is **pushed** rather than pulled, maximizing code/data locality.
- Values are kept in CPU registers as long as possible.

> **Intuition:** Instead of having a generic engine that reads a query plan and interprets it step-by-step, we generate a custom, hardcoded C++ program for that exact query, compile it on the fly, and run it.

## 2. The Query Compiler Architecture

### 2.1 Push-Based Data-Centric Processing
To maximize performance, data must stay in CPU registers. 
- **Pipeline Breaker:** Defined as an algebraic operator that takes an incoming tuple out of CPU registers (i.e., forcing materialization, such as a hash join build phase or a sort).
- Instead of pulling tuples up the tree (which breaks pipelines), the query compiler **pushes** tuples from one pipeline-breaker to the next.
- Operations between pipeline breakers (like selections or projections) simply act on the registers without touching memory.
- The resulting code has tight loops operating on large amounts of data, yielding excellent locality.

> **Mental Model:** Think of the traditional iterator model like passing a bucket of water down a line of people, where everyone has to grab it and hand it off (function calls). The data-centric push model is like laying down a continuous pipe where the water flows uninterrupted until it hits a reservoir (a pipeline breaker like a sort).

### 2.2 Compiling Algebraic Expressions
To abstract the translation from algebraic plans to imperative code, the compiler conceptually uses two functions during the generation phase:
- `produce()`: Asks the operator to generate result tuples.
- `consume(attributes, source)`: Pushes generated tuples to the parent operator.

These functions only exist during the compilation phase to emit the imperative code. The final generated code blurs operator boundaries, fusing multiple pipelined algebraic operations into a single tight loop.

## 3. Code Generation

### 3.1 LLVM Machine Code
Initially, generating C++ code was considered, but it proved to have unacceptable compilation times (seconds per query) and lacked low-level control (like overflow flags). Instead, the system uses **LLVM**:
- Generates portable assembly code that LLVM's JIT compiler translates to native machine code in milliseconds.
- Provides an unbounded number of virtual registers (SSA form), abstracting away register allocation.
- **Mixed Execution Model:** Complex, query-independent logic (e.g., buffer management, spilling to disk, hash table allocation) is implemented in pre-compiled C++. The dynamically generated LLVM code handles the "hot path" (tuple processing) and calls the C++ functions only when necessary (e.g., when out of memory).

> **Tradeoff:** Using LLVM provides fast JIT compilation and excellent performance, but it introduces a heavy dependency into the DBMS and makes debugging generated query code much harder than stepping through standard C++ operators.

### 3.2 Complex Operators
Complex operators (like Hash Joins or Outer Joins) cannot be compiled into a single massive function, as this could cause exponential code growth.
- Pipelined fragments are separated into distinct LLVM functions.
- Materialization in memory requires explicit tracking of which attributes are in registers versus memory.

### 3.3 Performance Tuning
The tight loops in the generated LLVM code are so fast that previously negligible overheads (like hashing a single integer or branch mispredictions) become the bottleneck.
- **Branch Prediction:** The compiler structures branches to be highly predictable. For example, hash table collision chain traversals are structured as `if (entry) do { ... } while(entry)` rather than a simple `while`, because the initial check is almost always true, and the collision check is almost always false. 

## 4. Advanced Parallelization
The data-centric compilation framework naturally supports modern CPU parallelism:
- **SIMD (Inter-tuple parallelism):** Processing blocks of tuples within wide vector registers is easily supported because data is passed in registers.
- **Multi-core (Intra-query parallelism):** Since data is processed in fragments within tight loops, partitioning data fragments across threads requires minimal changes to the generated code.

## 5. Evaluation (HyPer System)
The techniques were integrated into the HyPer main-memory DBMS and evaluated using the TPC-CH benchmark.

- **OLTP Performance:** The LLVM backend matched the raw transaction throughput of the highly optimized C++ backend but reduced query compilation time from 16.53 seconds down to 0.81 seconds.
- **OLAP Performance:** The LLVM generated code was significantly faster than both the C++ backend and competing systems (VectorWise, MonetDB), often executing queries 2x–4x faster.
- **Micro-architectural Analysis (Callgrind):** Compared to MonetDB, the LLVM compiled queries executed far fewer branches, suffered drastically fewer branch mispredictions, and exhibited significantly fewer L1/L2 cache misses.

## 6. Conclusion
Data-centric query compilation via LLVM effectively matches or exceeds the performance of hand-written C++ code. By pushing tuples between pipeline breakers and keeping data in CPU registers, modern DBMSs can overcome the CPU bottlenecks of the traditional iterator model while keeping compilation times in the sub-second range.