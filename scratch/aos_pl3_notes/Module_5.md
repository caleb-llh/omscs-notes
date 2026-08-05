# Module 5: Big Data and MapReduce

## 1. Introduction to Big Data Systems
* **Big Data**: Computations in giant-scale services are usually simple but operate over extremely large datasets, taking significant time to compute (e.g., searching for specific photographs across all web documents, online reservations, shopping).
* **Embarrassingly Parallel Computations**: Computations that require minimal synchronization or coordination among parallel threads running on different nodes.
* **Challenges of Programming at Scale**:
  * **Parallelization**: Distributing an application across thousands of machines (e.g., 10,000 nodes).
  * **Data Distribution and Plumbing**: Managing the flow of intermediate data between producers (early phases of the app) and consumers (later phases).
  * **Failure Handling**: In data centers with thousands of components, failure is inevitable ("when", not "if"). Programming models must expect and handle failures gracefully.

## 2. MapReduce Programming Paradigm
MapReduce is a programming framework designed for big data applications running on large computational clusters.

### Core Concepts
* **Key-Value Pairs**: Both input and output for the application, as well as intermediate data, are structured as key-value pairs.
* **User-Defined Functions**: The developer only needs to supply two functions: `map` and `reduce`.
  * **Map**: Takes a user-defined key-value pair as input and produces intermediate key-value pairs.
  * **Reduce**: Takes the intermediate key-value pairs as input and produces final key-value pairs.

### Example: Word Count (Finding Unique Names)
* **Goal**: Find specific unique names (e.g., Kishore, Arun, Drew) in a large document corpus.
* **Input**: Key = File Name, Value = File Content.
* **Map Phase**:
  * Looks for the specific names in the input file.
  * Emits an intermediate key-value pair: `(Name, 1)` or `(Name, Count in File)`.
  * *Embarrassingly Parallel*: Multiple mappers can run independently on different files.
* **Reduce Phase**:
  * Receives all intermediate values for a specific key (Name).
  * Aggregates (sums) the values.
  * Output: `(Name, Total Occurrences)`.
* **Plumbing**: The framework ensures that all values for "Kishore" from all mappers are routed to the specific reducer assigned to "Kishore".

## 3. Why MapReduce?
Many processing steps in giant-scale services can be expressed as MapReduce computations:
* Determining seat availability for flights.
* Accessing URL frequencies on a website.
* Creating word indexes for web document searches.
* **Page Ranking Example**:
  * **Input**: Key = Source URL, Value = Webpage Content.
  * **Mapper**: Finds target URLs within the source page. Emits `(Target URL, Source URL)`.
  * **Reducer**: Aggregates all source URLs that link to a specific target URL. Output: `(Target URL, List of Source URLs)`.
  * **Result**: Ranks target pages based on the number of source pages linking to them.

## 4. Heavy Lifting Done by the Runtime
The MapReduce framework handles all the complex underlying operations (instantiation, data movement, coordination) so the developer only focuses on the domain logic (`map` and `reduce`).

### Execution Workflow
1. **Splitting**: The input key-value space is divided into `M` splits (automatically or user-specified).
2. **Spawning**: The runtime spawns a **Master** process and multiple **Worker** threads.
   * **Master**: Oversees the operation, tracks worker status, and orchestrates tasks.
3. **Assigning Mappers**: The Master assigns `M` map tasks to available workers.
4. **Assigning Reducers**: The Master assigns `R` reduce tasks to workers (where `R` is often determined by the application, e.g., number of unique names).
5. **Map Phase Execution**:
   * A worker reads its assigned split from the local disk.
   * Parses the input and executes the user-defined `map` function.
   * Buffers intermediate key-value pairs in memory.
   * Periodically writes intermediate results to `R` separate files on its local disk (one for each reducer).
   * Notifies the Master upon completion. The Master waits for all `M` mappers to finish.
6. **Plumbing (Data Transfer)**: The Master orchestrates the communication paths between mappers and reducers.
7. **Reduce Phase Execution**:
   * A reducer worker pulls its required intermediate data from the local disks of all `M` mappers via Remote Procedure Calls (RPC).
   * The framework **sorts** the gathered data so all identical keys are grouped together.
   * The framework calls the user-supplied `reduce` function for each key and its corresponding list of values.
   * The reducer writes the final output to a file for its specific partition.
   * Notifies the Master upon completion.
8. **Completion**: Once all reducers finish, the Master finalizes the output and the user program is woken up.

### Resource Management
* If the number of available nodes `N` is less than `M + R`, the Master dynamically assigns new splits to workers as they complete their current tasks, ensuring load balancing.

## 5. Issues Handled by the Runtime
The MapReduce runtime manages complex distributed system challenges behind the scenes:

### Master Data Structures
* Tracks the locations and namespaces of intermediate files created by completed mappers.
* Maintains a **scoreboard** of which workers are assigned to which splits, tracking progress and reassigning tasks as needed.

### Fault Tolerance
* **Straggler Handling**: If a mapper node is dead, disconnected, or unusually slow (a "straggler"), the Master will not receive a timely response.
* **Redundant Execution**: The Master will assume the node is dead and restart the map task on a different node.
* **Idempotency**: Map and reduce functions *must* be idempotent. This ensures that if the original slow node eventually finishes, the Master can safely ignore its redundant completion message without affecting semantics.
* **Reducer Output Commits**: Reducers write to local files. The Master relies on the **atomicity of the rename system call** to commit the final output file, safely ignoring redundant reducer stragglers.

### Data Management & Locality
* **Locality Management**: Uses underlying file systems (like Google File System) to ensure computations happen as close to the data as possible, minimizing network transfer.
* **Task Granularity**: The framework manages the granularity of tasks to maintain a good load balance across the cluster.

### Refinements & Optimizations
* **Partitioning**: Data is routed to reducers using a default hash function, which users can override with custom partitioning logic.
* **Partial Merging (Combiners)**: Users can implement combining functions within the mapper (e.g., locally summing word counts before emitting) to reduce the volume of intermediate data sent over the network.
* **Extras**: The framework provides built-in tools for status monitoring and logging.

## 6. Conclusion
The true power of MapReduce lies in its **simplicity**. Domain experts only need to define the `map` and `reduce` functions specific to their application, while the runtime framework seamlessly handles the immense complexity ("heavy lifting") of distributed parallel execution, fault tolerance, and data plumbing.