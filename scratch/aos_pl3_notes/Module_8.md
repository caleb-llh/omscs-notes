# Module 8: Middleware for Distributed Multimedia Applications

## Introduction & Programming Paradigms
* **Context**: Moving up the stack from operating system scheduler adaptations (for real-time multimedia) to **middleware**. This middleware sits between commodity operating systems and novel distributed, real-time multimedia applications.
* **Conventional Programming APIs**:
  * **`pthreads`**: API for parallel program development.
  * **Sockets**: API for distributed application development (e.g., NFS servers, RPC packages).
* **Limitations of Sockets**: The socket API is too low-level and lacks the semantic richness required for emerging novel multimedia distributed applications.

## Novel Multimedia Applications
* **Characteristics**:
  * **Sensor-based**: Utilize simple sensors (temperature, humidity) and complex sensors (cameras, microphones, radars).
  * **Distributed**: Accessed via the internet.
  * **Real-time**: High computational intensity requiring clusters/clouds, with a strict need to shrink the latency from sensing to actuation.
* **Situation Awareness Applications**: Applications that gather live sensor data to analyze real-time environments and make timely decisions (e.g., traffic analysis, emergency response, disaster recovery, robotics, asset tracking).
* **The Control Loop**:
  1. **Sensing**: Gathering continuous streams of data.
  2. **Prioritizing**: Determining which sensors/data are most interesting (e.g., focusing on cameras with movement).
  3. **Analyzing**: Devoting computational resources to process the prioritized streams.
  4. **Actuating**: Taking action (triggering alarms, notifying humans) or providing feedback to sensors (e.g., retargeting pan-tilt-zoom cameras).

## The Developer's Challenge
* **Domain Experts**: Developers of these systems are often vision researchers or domain experts who write sophisticated detection, tracking, and recognition algorithms.
* **The Problem**: Scaling these algorithms to thousands of distributed sensors involves significant distributed systems complexity (e.g., tracking an object across multiple cameras).
* **The Solution**: Systems need to provide a programming model that abstracts away distributed resource management, reducing pain points for domain experts. 

## Persistent Temporal Streams (PTS) Programming Model
* **Overview**: PTS is an exemplar distributed programming system designed to cater to the needs of situation awareness applications.
* **Core Abstractions**:
  * **Threads**: Computational entities.
  * **Channels**: Conduits for data between threads.
* **Graph Structure**: The computation graph resembles a Unix process-socket graph, easing the transition for socket programmers. However, channels allow **many-to-many connections** (multiple producers and consumers).
* **Time-Sequenced Data**: Unlike standard sockets, PTS channels hold data objects that are explicitly sequenced by time.

### Key Primitives
* **`put_item(item, timestamp)`**: A thread produces data (e.g., a camera frame), associates it with a wall-clock timestamp, and places it into a channel.
* **`get(lower_bound, upper_bound)`**: A thread retrieves data from a channel within a specific time window. 
  * Allows querying by explicit timestamps (e.g., 1:05 PM to 1:06 PM) or abstract variables (e.g., "oldest item", "newest item").

### Correlating and Bundling Streams
* **Temporal Causality**: When a thread processes an input (e.g., a camera frame) and produces an output (e.g., a data digest), it assigns the output the *same timestamp* as the input. This propagates temporal causality throughout the distributed computation graph.
* **Bundling Streams (Stream Groups)**:
  * Applications often need to process multiple modalities simultaneously (e.g., video, audio, text).
  * PTS allows grouping streams into a bundle with an **anchor stream** (e.g., video) and **dependent streams** (e.g., audio).
  * **`group_get`**: A primitive that fetches correspondingly time-stamped items from all streams in a bundle, automatically handling the temporal synchronization.

## PTS Design Principles & Architecture
* **Ubiquity & Simplicity**: Channels are network-wide unique named entities that can exist anywhere in the distributed system, much like Unix sockets. All the heavy lifting is handled under the covers by the PTS runtime.
* **Time as a First-Class Entity**: Time is recognized and manipulated by the programming system. Applications query and index channels fundamentally based on time.
* **Stream Persistence Under Application Control**:
  * Sensors produce data 24/7, which exceeds CPU memory limits. 
  * PTS allows streams to be persisted to archival storage (e.g., disk, HDFS) based on application-defined policies (e.g., condensing data or dropping frames before saving).
* **Seamless Live and Historical Data**:
  * The `get` primitive handles queries seamlessly regardless of whether the data is currently in memory (live) or on disk (historical). A single query can span from yesterday (historical) to right now (live).

## Conclusion
* Just as **MapReduce** provides a simple programming model for batch Big Data applications, **PTS** provides a simple, intuitive model for **live stream analysis**.
* By offering time-based distributed data structures, transparent stream persistence, and automatic data management, PTS significantly reduces the complexity for domain experts building large-scale situation awareness applications.
