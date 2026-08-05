# Module 8: Introduction to Distributed Systems

## Overview
- **Parallel vs. Distributed Systems:**
  - **Similarities:** Both involve multiple processing units working together to solve problems.
  - **Differences:**
    - Distributed system nodes possess **individual autonomy**.
    - Interconnection networks in distributed systems are **wide open** to the world (unlike parallel systems, which are typically confined to a single rack, room, or box).
- **Modern Context:** As transistor feature sizes continue to shrink (advances in VLSI technology), issues traditionally considered within the domain of distributed systems are now surfacing even within a single chip.

## What is a Distributed System?
A distributed system is defined by three core properties:
1. **Network Interconnection:** A collection of nodes connected via a Local Area Network (LAN - e.g., twisted pair, coaxial cable, optical fiber, Ethernet) or a Wide Area Network (WAN - e.g., satellite, microwave, ATM).
2. **No Shared Physical Memory:** Nodes do not share physical memory. The *only* way nodes can communicate is by sending messages over the network.
3. **Communication Time vs. Computation Time:** 
   - **$T_E$ (Event Computation Time):** The time it takes a single node to perform meaningful processing.
   - **$T_M$ (Message Transmission Time):** The time it takes to communicate a message between nodes.
   - In a distributed system, **$T_M \gg T_E$** (communication time is significantly larger than event computation time).

### Leslie Lamport's Definition
> *"A system is distributed if the message transmission time ($T_M$) is not negligible compared to the time between events in a single process."*

- **Implication for Clusters:** By this definition, even a **cluster** (the workhorses of modern data centers, often contained in a single rack) is a distributed system. Processors have become blazingly fast ($T_E$ has shrunk significantly), and while networks have improved, they haven't kept pace with processor speeds, making $T_M$ significantly larger than $T_E$.
- **Algorithm Design Rule:** When designing distributed algorithms spanning network nodes, computation time must be structured to be significantly more than communication time. Otherwise, the system will not reap the benefits of parallelism.

## Event Ordering and System Beliefs
In a distributed system, understanding the ordering of events is crucial. We rely on two core beliefs (illustrated by multi-party communications, e.g., User $\rightarrow$ Expedia $\rightarrow$ Delta):

### 1. Sequential Processes
- Events happening within a **single process** are expected to be **totally ordered** in their textual execution sequence.
- The apparent effect of the process execution to the user is sequential.

### 2. Communication Events
- The **receipt** of a message must happen *after* the **send** of that message. 
- A message cannot be received before it has been completely sent by the sender.

## The "Happened Before" Relationship ($\rightarrow$)
The "happened before" relationship (denoted as $A \rightarrow B$) defines the causal ordering of events. $A \rightarrow B$ implies one of two possibilities:
1. **Same Process:** $A$ and $B$ are events in the same process, and $A$ textually occurred before $B$ (sequential process condition).
2. **Across Processes (Communication):** $A$ is the act of sending a message on one node, and $B$ is the act of receiving that *same* message on a different node.

**Key Property: Transitivity**
- If event $A$ happened before event $B$ ($A \rightarrow B$), and event $B$ happened before event $C$ ($B \rightarrow C$), then it logically follows that $A$ happened before $C$ ($A \rightarrow C$).

## Concurrent Events
- **Definition:** Two events ($A$ and $B$) are considered **concurrent** if there is no apparent causal relationship between them (neither $A \rightarrow B$ nor $B \rightarrow A$).
- **Characteristics:**
  - They are not sequential events on the same process.
  - They are not connected by communication (neither directly nor transitively).
  - It is impossible to assert a definitive order. In one execution, $A$ might happen before $B$ in wall-clock time; in another execution, $B$ might happen before $A$.
- **Partial Order:** The "happened before" relationship only provides a **partial order** of events in a distributed system. It is impossible to establish a total order for all events due to asynchronous execution and concurrency.
- **Design Implications:** Assuming an ordering between unconnected concurrent events leads to timing and synchronization bugs. Robust distributed algorithms must accurately recognize which events are causally connected and which are concurrent.
