# Lesson_9_Internet_Computing (Synthesized Notes)

# Module 4: Systems Issues in Giant Scale Services

## 1. Introduction to Internet-Scale Computing
Giant scale services address the systems issues involved in managing massive data centers, programming big data applications (e.g., search engines), and disseminating content scalably across the web. 

**Examples of Giant Scale Services:**
- Online airline reservation systems
- E-commerce platforms
- Webmail (e.g., Gmail)
- Internet search engines (e.g., Google)
- Video streaming services (e.g., Netflix)

**Key Themes of the Module:**
1. **Systems Issues:** Providing giant scale services on the internet.
2. **Programming Models:** Big data applications delivering everyday services.
3. **Content Distribution Networks (CDNs):** Disseminating content scalably.

*Note on Scale:* When dealing with thousands of processes and nodes, failures are inevitable. It is not a question of *if* a failure will occur, but *when*.

---

## 2. Generic Service Model
A typical architecture for a giant scale service involves a client reaching a web portal via the IP network. 
- **Site Architecture:** Thousands (e.g., 10,000+) of servers interconnected via a high-bandwidth communication backplane, all connected to data stores.
- **Embarrassingly Parallel:** Client requests are typically independent of one another. They can be handled in parallel as long as there is sufficient server capacity.

### The Role of the Load Manager
A Load Manager sits between the servers and the IP network. Its responsibilities include:
- **Traffic Balancing:** Redirecting incoming client requests to servers to ensure no single server is overloaded, keeping utilization equal.
- **Hiding Partial Failures:** Observing the state of the servers and shielding incoming client requests from internal node failures.

---

## 3. Clusters as Workhorses
Computational clusters are the backbone of giant scale services. Data centers employ thousands of computational nodes (often Symmetric Multiprocessors - SMPs) connected by high-performance networks.

**Advantages of Computational Clusters:**
- **Absolute Scalability:** Resources can be added without re-architecting the data center.
- **Incremental Scalability:** Adding more nodes directly increases performance and capacity.
- **Cost and Performance Control:** Standardized, identical nodes allow administrators to control costs and performance efficiently.
- **Flexibility:** Independent components make it easy to mix and match generational hardware changes.

---

## 4. Load Management Strategies
Load management can operate at different levels of the 7-layer OSI Reference Model. Higher layers provide more functionality and intelligence.

### Network Level (Layer 3)
- **Mechanism:** Round-Robin Domain Name Server (DNS).
- **How it works:** Assigns different IP addresses (corresponding to different servers) to incoming requests for the same domain name.
- **Pros:** Good load balancing, assumes all servers are identical and data is fully replicated.
- **Cons:** Cannot hide down/failed server nodes from the external world.

### Transport Level and Higher (Layer 4+)
- **Mechanism:** Layer 4 switches or higher-level switches (often architected as switch pairs for hot failover).
- **Pros:** 
  - Dynamic isolation of failures.
  - **Service-Specific Front-End Nodes:** Can route requests based on the specific application (e.g., Gmail vs. Google Search vs. Picasa).
  - **Client-Aware:** Can make routing decisions based on client device characteristics (e.g., smartphones).

---

## 5. The DQ Principle
The DQ principle defines the system capacity for handling giant scale services, primarily based on the insight that giant scale services are **network-bound**, not disk I/O-bound.

### Definitions
- **Offered Load ($Q_0$):** The rate of incoming requests hitting the server per unit time.
- **Completed Requests ($Q_c$):** The portion of incoming requests successfully served.
- **Yield ($Q$):** The ratio of completed requests to offered load ($Q_c / Q_0$). Ranges from 0 to 1. (Ideally 1).
- **Full Data Set ($D_f$):** The complete corpus of data required to handle queries.
- **Available Data ($D_v$):** The portion of data actually used to process a query (due to failures or load).
- **Harvest ($D$):** The ratio of available data to the full data set ($D_v / D_f$). Ranges from 0 to 1. (Ideally 1).

### The DQ Constant
- **$D \times Q = \text{Constant}$**: For a given server capacity, the product of data served per query ($D$) and the rate of query processing ($Q$) is a system limit.
- **Trade-offs:** A system administrator can increase Yield ($Q$) by decreasing Harvest ($D$), or vice versa. Both cannot be increased simultaneously without adding hardware capacity.
- **Alternative Metrics:** While traditional servers use IOPS (I/O Operations Per Second) or Uptime (MTBF - MTTR / MTBF), $DQ$ is much more intuitive for network-bound giant scale services.

---

## 6. Data Management: Replication vs. Partitioning
Administrators must choose how to distribute data across servers.

- **Replication:** Every server has the full corpus of data.
  - *Impact of Failure:* Harvest remains 100% (requests can be redirected to other replicas), but Yield decreases due to reduced total capacity. Ideal for services where users expect complete data (e.g., Email).
- **Partitioning:** The data corpus is divided into $N$ partitions across servers.
  - *Impact of Failure:* Yield remains unchanged (computational capacity is the same), but Harvest decreases because some partitions become unavailable. Acceptable for services where partial results are okay (e.g., Web Search).
- *Note:* Beyond a certain scale, systems often use both partitioning and partial/full replication to balance Harvest and Yield.

---

## 7. Graceful Degradation
When a server reaches saturation (its DQ limit), the system must degrade gracefully.
- **Option 1:** Maintain Harvest (fidelity) but decrease Yield (serve fewer clients).
- **Option 2:** Maintain Yield (serve all clients) but decrease Harvest (lower fidelity/quality).

**Saturation Management Strategies:**
- **Cost-based / Priority-based Admission Control:** "Pay more, get more" or prioritize higher-value requests.
- **Reduced Data Freshness/Fidelity:** e.g., Serving video streams at a lower bitrate to accommodate all users.

---

## 8. Online Evolution and Growth
Services must be continuously upgraded (hardware or software) with minimal disruption. Upgrades result in a planned DQ loss.

### Upgrade Strategies
1. **Fast Reboot:**
   - *Method:* Bring down all servers simultaneously, upgrade, and turn back on.
   - *Impact:* 100% loss of service during the upgrade time.
   - *Best for:* Services with predictable off-peak hours (using the diurnal server property).
2. **Rolling Upgrade (Wave Upgrade):**
   - *Method:* Upgrade one server (or a small batch) at a time.
   - *Impact:* Service remains fully available, but the upgrade process takes a long time ($N \times \text{Upgrade Time}$). Continuous, minor DQ loss.
3. **Big Flip:**
   - *Method:* Bring down 50% of the nodes, upgrade, turn back on, then do the other 50%.
   - *Impact:* Service runs at 50% capacity for twice the individual upgrade time.

*Key Insight:* The total DQ loss (Area = $N \times \text{Upgrade Time} \times \text{DQ loss per node}$) is mathematically the same across all three strategies. The choice depends on how the administrator wants the user community to experience the downtime.

---

## Conclusion
- Giant scale services are fundamentally **network-bound**, not disk I/O-bound.
- The **DQ Principle** is a powerful tool for system designers to optimize between Yield and Harvest, manage graceful degradation, and plan online evolution via controlled failures.

---

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

---

# Module 6: Content Distribution Networks (CDNs) and DHTs

## Introduction
- **Internet and WWW**: Provide ubiquitous access to information created by both individuals and large businesses (e.g., CNN, BBC).
- **Previous Modules**: Focused on server-side architecture (data centers, cluster organization, programming models for big data).
- **Current Module**: Focuses on **Content Distribution Networks (CDNs)**—how information is organized, located, and distributed globally at scale.

## Distributed Hash Tables (DHT)
- **Content Naming**: Textual names cause collisions. Instead, a unique **Content Hash** (e.g., using SHA-1 to create a 160-bit string) is generated. This serves as the **Key**.
- **Value**: The **Node ID** (e.g., an IP address or virtual ID) where the content is stored.
- **Key-Value Pair**: Links the content's unique hash to its location (e.g., `(149, 80)` where 149 is the key, 80 is the node ID).
- **Storage Problem**: A central name server does not scale for user-generated content.
- **DHT Solution**: 
  - A distributed approach where the key-value pair is stored on a node whose ID matches (or is very close to) the key.
  - To find content, a user looks for the node with an ID matching the content's key.

### DHT Namespaces
1. **Key Space Namespace**: Created by hashing the content (e.g., using SHA-1 to generate a 160-bit key) to ensure unique signatures without collisions.
2. **Node Space Namespace**: Created by hashing the IP addresses of the nodes in the network (also generating a 160-bit ID).
- **Objective**: Store a key in a node `n` such that the key is very close to `n`.
- **API**: 
  - `put(key, value)`: Stores the location of the content.
  - `get(key)`: Retrieves the value (node ID) associated with the key.

## CDNs as Overlay Networks
- **Overlay Network Definition**: A virtual network built on top of a physical network. 
- **Examples**:
  - **IP Network**: An overlay on top of a Local Area Network (MAC addresses).
  - **CDN**: An overlay on top of the TCP/IP network.
- **Routing at User Level**: 
  - Nodes use virtual addresses (Node IDs).
  - A user-level routing table maps these virtual Node IDs to physical IP addresses.
  - Nodes exchange routing information with peers.
  - Sending a message may take a few hops at the virtual overlay level, but many more hops at the underlying physical network level.

## Traditional (Greedy) Approach to DHTs
- **Algorithm**:
  - **Placement (`put`)**: Place the key-value pair at a node `n` where `n` is equal to or closest to key `K`.
  - **Retrieval (`get`)**: Route requests to the known node closest to key `K`.
- **Goal**: Reach the destination with the fewest number of overlay hops (optimizing individual lookup time).

### Problems with the Greedy Approach
- **Metadata Server Overload**: If many keys hash to similar IDs, they all get stored on the same node, congesting it.
- **Origin Server Overload**: If content becomes highly popular, the metadata server is overwhelmed with `get` requests, and the origin server is overwhelmed with download requests.
- **Tree Saturation**: The congestion at a target node propagates outward to adjacent nodes in the overlay network (which act as gateways), creating a saturated tree rooted at the congested node.

## Coral's Sloppy DHT and Key-Based Routing
- **Philosophy**: Optimize for the common good by avoiding tree saturation, even if it slightly increases individual lookup latency.
- **Sloppy DHT**: `put` and `get` operations are often satisfied by intermediate nodes rather than the exact destination node `n`.

### Distance Metric
- **XOR Distance**: The distance between two nodes is calculated using the bitwise Exclusive-OR (XOR) of their Node IDs.
- **Why XOR?**: It is computationally much faster than subtraction and provides a symmetrical distance metric.

### Coral Key-Based Routing
- **Routing Strategy**: Instead of jumping to the closest known node (greedy approach), Coral reduces the XOR distance to the destination by **half** at each hop.
  - e.g., If distance is 10, the next hop targets a node with distance 5, then 2, then 1, until reaching the destination.
- **Mechanism**: 
  - A node queries a peer: "Do you know nodes that are half the distance to my target?"
  - The peer responds with the best matching nodes it knows.
  - The querying node updates its routing table and proceeds.

### Handling Overload in Coral
Coral defines two states to determine if a node is overloaded:
1. **Full State (Space Metric)**: The node is already storing a maximum of `L` values for a specific key.
2. **Loaded State (Time Metric)**: The node is receiving a maximum of `beta` requests per unit time for a specific key.

### Put and Get Operations in Coral
- **`put(key, value)`**:
  - **Forward Phase**: The node routes towards the destination (halving distance each step). At each step, it asks, "Are you full or loaded for this key?"
  - **Reverse Phase**: If an intermediate node says it is full or loaded, Coral infers that the path ahead is congested (tree saturation). It retracts its step and places the key-value pair at the previous node that was neither full nor loaded.
- **`get(key)`**:
  - Routes towards the destination (halving distance). 
  - Because metadata might have been dropped at intermediate nodes (due to full/loaded states), the `get` request will often hit an intermediate metadata server and resolve early without reaching the original exact destination.

## Coral in Action (Example)
1. **Initial Publication**: Naomi puts her video (key 100). The `put` traverses the network and stores the metadata at David's computer (node 100), which is neither full nor loaded.
2. **First Retrieval**: Jacques does a `get` for key 100, reaches David, finds Naomi's node ID, and downloads the video.
3. **Proxying**: Jacques acts as a good samaritan and becomes a proxy. He tries to `put` (key 100, his node ID). David's node might now be "full" for key 100, so the `put` retracts and stores the metadata on an intermediate node.
4. **Subsequent Retrievals**: Kamal searches for key 100. His `get` request hits the intermediate node first. He is directed to Jacques instead of Naomi.
- **Result**: Metadata server load is distributed across intermediate nodes. Origin server load is distributed across proxies. The system scales dynamically.

## Conclusion
- **Coral's Impact**: Democratizes content generation, storage, and distribution using a participatory, sloppy DHT approach that prevents server overload.
- **Commercial CDNs**: CDNs like Akamai do not use this participatory model; they contractually mirror content for customers and dynamically deploy proprietary mirrors to handle request volume.


---

