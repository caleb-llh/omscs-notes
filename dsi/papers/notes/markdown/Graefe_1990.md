# Encapsulation of Parallelism in the Volcano Query Processing System

## Abstract
Volcano is a dataflow query processing system designed for database systems research and education. Its uniform interface makes it extensible by new operators, which are coded as if meant for a single-process system. To parallelize Volcano, the authors chose an "operator model" over the traditional "bracket model". They introduce the `exchange` operator, which parallelizes all other operators, allows intra-operator parallelism on partitioned datasets, and both vertical and horizontal inter-operator parallelism. The `exchange` operator encapsulates all parallelism issues, translating between demand-driven dataflow (within processes) and data-driven dataflow (between processes).

> **Intuition:** Instead of baking parallelism into every database operator (like join or sort), wrap the parallelism itself into a single, specialized operator. Other operators don't even know they are running in parallel!

## 1. Introduction
The goal of Volcano was to provide a flexible, extensible testbed without sacrificing efficiency. It is a small system (less than two dozen core modules). All existing query processing algorithms can be parallelized without modifying their implementations.
The bracket model uses template processes that encompass specific operators, whereas the operator model (used in Volcano) uses the `exchange` operator.
Volcano's mechanism to synchronize multiple operators in complex query trees within a single process and to exchange data is similar to commercial systems (Ingres, System R). 

> **Mental Model:** Think of the query plan as a pipeline of Lego blocks. In the bracket model, every Lego block is wrapped in a thick layer of parallel-processing logic. In the operator model, the parallel-processing logic is just another Lego block (`exchange`) that you snap into the pipeline wherever you want.

## 2. Previous Work
Previous systems (WISS, GAMMA) heavily influenced Volcano. The data exchange mechanism is a radical departure from GAMMA.
Other influences include EXODUS, E language, GENESIS, and conventional systems like Bubba, Starburst, Postgres, XPRS.

### 2.1 The Bracket Model of Parallelization
Used in GAMMA and Bubba. There is a generic process template that receives/sends data and executes exactly one operator at a time.
Problems with the bracket model:
- Each locus of control must be created, often by a separate scheduler process, complicating development.
- Network I/O is the only means of obtaining input and delivering output.
- Passing data between operators always involves expensive inter-process communication (IPC) system calls, even if evaluated on a single machine or when data doesn't need repartitioning.
In a single-process engine, operators schedule each other efficiently via procedure calls.

> **Tradeoff:** The bracket model forces IPC everywhere, providing uniform isolation but paying a massive overhead penalty even when components reside on the same machine and could just use simple function calls.

## 3. Volcano System Design
Volcano uses a conventional file system. Queries are expressed as complex algebra expressions (query processing algorithms).
All operators are implemented as **iterators** supporting an open-next-close protocol.
- **State Record:** Arguments for algorithms are kept here.
- **Support Functions:** Operations like comparisons and hashing are passed as arguments.
- **Anonymous Inputs/Streams:** An operator doesn't need to know what kind of operator produces its input.
Calling `open` for the top-most operator recursively instantiates state records and opens all inputs. `next` is called repeatedly until end-of-stream. `close` shuts down iterators.
This uses **demand-driven dataflow**. Records are pinned in the buffer and owned by exactly one operator at a time. Virtual devices are used for intermediate results.

> **Common Confusion:** Demand-driven (pull) vs Data-driven (push). Within a single process, Volcano uses demand-driven dataflow (the consumer calls `next()` to pull data). Between processes, it switches to data-driven dataflow (the producer pushes data into a port).

## 4. The Operator Model of Parallelization
The single-process code is used without change. The module responsible for parallel execution and synchronization is the **`exchange` iterator**. It can be inserted anywhere in a query tree.

### 4.1 Vertical Parallelism
Also known as pipelining between processes.
- The `open` procedure creates a new child process and a shared memory port.
- The parent acts as the consumer, the child as the producer.
- Consumer: `exchange` receives input via IPC. `next` waits for data via the port.
- Producer: `exchange` becomes the driver for the subtree below it. Output is collected in packets.
When input is exhausted, an end-of-stream tag is passed. 
Notice: `exchange` uses **data-driven dataflow** (eager evaluation) between processes, unlike the demand-driven flow within processes. This removes the need for request messages and is easier to combine with horizontal parallelism.
A run-time switch enables **flow control (back pressure)** using an additional semaphore to prevent producers from overrunning consumers.

> **Tradeoff:** Eager evaluation across processes eliminates the overhead of sending "request" messages for every record, but risks memory exhaustion if the producer outpaces the consumer. Back-pressure semaphores perfectly balance this.

### 4.2 Horizontal Parallelism
Two forms:
1. **Bushy parallelism:** Different CPUs execute different subtrees (e.g., sorting two inputs concurrently).
2. **Intra-operator parallelism:** Several CPUs perform the same operator on different subsets of data. Requires data partitioning (round-robin, key-range, or hash-partitioning) via a support function.
When a producer operation runs in parallel, a master process forks the slave processes (optimized using a propagation tree scheme). Once forked, producers run without further synchronization except for short-term locks when accessing shared structures.
Closing is orderly: close request propagates down, and semaphores coordinate process shutdown.

### 4.3 An Example
Describes a complex pipeline with groups of processes. `exchange` manages the cross-process communication seamlessly. End-of-stream tags are counted so consumers know when all producers are finished.

### 4.4 Variants of the Exchange Operator
- **Replication/Broadcast:** Send all records to all consumers (e.g., for hash-division or parallel join algorithms).
- **Merge Network:** Multiple sorted streams merged concurrently. `exchange` keeps input records separated by producer.
- **Reduced Process Count:** The `exchange` operator can live in the middle of a process's operator tree. It doesn't fork new processes but establishes a port, requesting records from its input tree and sending them to other processes. This avoids the OS scheduling overhead of too many processes.

> **Mental Model:** The `exchange` operator is like a shape-shifter. It can act as a pipeline buffer, a data partitioner/router, a broadcaster, or a merger, all while maintaining the exact same `open-next-close` interface to the rest of the system.

## 5. Overhead and Performance
Performance measurements on a Sequent Symmetry (shared-memory) showed:
- Overhead of the `exchange` operator (without new processes) was negligible (~25.73 µsec per record).
- Data transfer via `exchange` across processes is very fast.
- Packet size affects performance: penalty for very small packets is significant. For larger packets (e.g., 250 records), the overhead is minimal (estimated ~992 µsec per packet and process boundary).

## 6. Summary and Conclusions
Volcano encapsulates parallel query evaluation into a single module (`exchange`).
Advantages over the bracket model:
1. Hides parallelism from other operators.
2. Can be placed anywhere in a tree.
3. No separate scheduler process required (uses standard open-next-close).
4. Does not require IPC for every operator.
5. A single process can have any number of inputs.
6. Can multiplex a single process between producer and consumer.