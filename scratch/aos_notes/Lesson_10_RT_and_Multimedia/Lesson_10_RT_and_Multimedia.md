# Lesson_10_RT_and_Multimedia (Synthesized Notes)

# Playlist 3 Module 7: Time-Sensitive Linux

## Introduction
Traditionally, general-purpose operating systems catered to throughput-oriented applications (e.g., databases, scientific apps). However, there is a growing need to support soft real-time guarantees for latency-sensitive applications (e.g., synchronous AV players, video games).

**Time-Sensitive (TS) Linux** is an extension of the commodity general-purpose Linux operating system that addresses two main questions:
1. How to provide guarantees for real-time applications in the presence of background throughput?
2. How to bound the performance loss of throughput-oriented applications in the presence of latency-sensitive applications?

## Sources of Latency
Time-sensitive applications require immediate responses to events. In a typical general-purpose OS, there are three primary sources of latency that increase the distance between **Event Happening** and **Event Activation** (the point where the app is scheduled to react):

1. **Timer Latency:** Inaccuracy of the timing mechanism.
   - The delay between when an event should have triggered an interrupt and when the timer interrupt actually occurs, primarily due to the coarse granularity of periodic timers (e.g., 10ms in standard Linux).
2. **Kernel Preemption Latency:** The delay caused when the kernel cannot be interrupted.
   - Occurs when the kernel is modifying critical shared data structures (interrupts are turned off) or is already handling a higher-priority interrupt.
3. **Scheduler Latency:** The delay in scheduling the required process after the interrupt is delivered.
   - The application waiting for the timer event cannot be scheduled immediately because a higher-priority task is occupying the CPU.

## Types of Timers
An OS typically provides different timer mechanisms, each with pros and cons:

- **Periodic Timers** (Standard in UNIX)
  - **Pro:** Periodicity reduces willy-nilly interruptions.
  - **Con:** High event recognition latency; worst-case latency equals the period length itself.
- **One-Shot Timers**
  - **Pro:** High timeliness and exact accuracy.
  - **Con:** High processing and reprogramming overhead for every single interrupt.
- **Soft Timers**
  - **Pro:** Extremely low interrupt overhead, as they avoid timer interrupts entirely.
  - **Mechanism:** The kernel polls for events at strategic points (e.g., during system calls or external network interrupts).
  - **Con:** Polling latency and the overhead of checking all events to see if any expired.

## Firm Timer Design
**Firm Timer** is a novel mechanism in TS Linux that combines the benefits of Periodic, One-Shot, and Soft timers to provide accurate timing with very low overhead.

### The "Overshoot" Parameter
- **Mechanism:** A one-shot timer is programmed to fire slightly *after* the exact event time. This delay is the "overshoot window."
- **Soft Timer Synergy:** If a system call or external interrupt brings execution into the kernel *during* this overshoot window, the kernel dispatches the expired timer immediately and reprograms it for the next event.
- **Benefit:** It achieves the accuracy of a one-shot timer but frequently avoids the actual hardware interrupt cost (acting like a soft timer).

### Long-Distance Optimization (Periodic Synergy)
- **Mechanism:** If there is a long time distance between two one-shot events, there will likely be several standard periodic timer interrupts occurring in between. 
- **Action:** The kernel dispatches the upcoming one-shot event slightly early, during a preceding periodic interrupt.
- **Benefit:** Eliminates the use of expensive one-shot timers altogether for distant events. Periodic timer data structures ($O(1)$) are much more efficient than one-shot timer structures ($O(\log N)$).

## Firm Timer Implementation
- **Hardware Support:** Relies on the **APIC (Advanced Programmable Interrupt Controller)**, available on modern CPUs (Intel Pentium+).
  - Reprogramming an APIC one-shot timer takes only a few CPU cycles, making overhead negligible.
  - Theoretical accuracy is 10ns (on a 100MHz bus), though limited in practice by interrupt handling time.
- **Data Structure:** Uses a timer queue where tasks are sorted by their expiry time. 
- **Execution:** When the APIC timer expires, the interrupt handler triggers the callback for the expired task, removes it from the queue, and reprograms the timer (either periodic or one-shot) for the next event.

## Reducing Kernel Preemption Latency
To prevent delays when the kernel is busy manipulating shared data, TS Linux employs a **Lock-Breaking Preemptable Kernel** (a technique due to Robert Love).

- **Core Ideas Combined:**
  1. Explicitly inserting preemption points in the kernel.
  2. Allowing preemption anytime the kernel is *not* manipulating shared data structures.
- **Mechanism:** Long critical sections are broken down. The kernel acquires a lock, manipulates shared data, **releases the lock, checks for expired timers/preemptions**, and then reacquires the lock to continue.
- **Benefit:** Safely reduces spin-lock holding times and creates more opportunities for the kernel to respond to latency-sensitive events.

## Reducing Scheduling Latency
Once the timer event is handled, the scheduler must act fast. TS Linux addresses scheduler latency through two mechanisms:

### 1. Proportional Period Scheduling
- **Mechanism:** Applications request a specific proportion of CPU time ($Q$) per time quantum/window ($T$). 
- **Admission Control:** The scheduler only admits a task if the system can accommodate the requested capacity.
- **Benefits:** 
  - Provides temporal protection and highly accurate scheduling for time-sensitive tasks.
  - Allows TS Linux to reserve a fixed proportion of CPU time strictly for throughput-oriented tasks, ensuring they are not starved and can still make forward progress.

### 2. Priority-Based Scheduling (Addressing Priority Inversion)
- **The Problem (Priority Inversion):** A high-priority task ($C_1$) makes a blocking call to a low-priority server. While the server is executing, a medium-priority task ($C_2$) becomes runnable and preempts the server. Now, $C_1$ is indirectly delayed by $C_2$.
- **The Solution (Priority Inheritance):** When $C_1$ makes a request to the server, the server's priority is boosted to match $C_1$'s priority.
- **Benefit:** $C_2$ can no longer preempt the server, completely eliminating priority inversion.

## Conclusion
By fixing the three primary sources of latency, TS Linux successfully provides Quality of Service (QoS) guarantees for real-time applications on commodity operating systems. 

**Summary of TS Linux Innovations:**
1. **Firm Timers:** High timer accuracy without exorbitant overhead.
2. **Lock-Breaking Preemptable Kernel:** Significantly reduced kernel preemption latency.
3. **Proportional & Priority-Based Scheduling:** Minimized scheduler latency, prevention of priority inversion, and protected CPU time for throughput applications.


---

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


---

