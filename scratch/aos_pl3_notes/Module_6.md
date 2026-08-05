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
