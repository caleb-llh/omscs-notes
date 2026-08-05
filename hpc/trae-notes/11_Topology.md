# Network Topology

> **Background Context:** While this chapter focuses on the physical wiring of parallel machines, remember that the software often hides these details. The challenge of HPC (High Performance Computing) is that hiding these details too well can lead to terrible performance when algorithms fight the physical reality of the hardware.

> **Fact Check:** The $\alpha-\beta$ model assumes uniform latency, which is almost never true in modern supercomputers. Network topologies introduce varying latencies based on node distance (NUMA, rack locality, etc.), which makes hiding these details completely impossible if optimal performance is desired.

## 1. Introduction

**Background Context:** When designing parallel algorithms, we often imagine computing nodes magically talking to each other instantly. However, in reality, physical wires (or optical cables) connect these computers. At small scales (e.g., your laptop with 4 cores), the specific layout doesn't matter much. But in parallel and distributed computing at massive scales (supercomputers with millions or billion+ processor systems), the physical layout—the **network topology**—dictates whether an algorithm runs in minutes or days.

> **Fact Check:** As of 2024, the largest supercomputers (like Frontier or Aurora) have millions of compute cores (e.g., Frontier has ~8.7 million CPU/GPU cores), not billions of standalone processors. "Billion+" usually refers to threads, transistors, or future large-scale neuromorphic systems, but the scaling principle for topologies remains exactly the same.

While cost models (like the $\alpha-\beta$ or latency-bandwidth models) abstract away network details, understanding topology helps analyze how an algorithm designed for one network will perform on another. 

**Mental Model:** Think of the computing nodes as cities and the network topology as the highway system connecting them. The $\alpha-\beta$ cost model gives us the "toll fee" and "speed limit" for an average trip, but the topology tells us exactly which roads exist, where the traffic jams (bottlenecks) will happen, and how long a cross-country road trip actually takes.

> **Tradeoff:** Algorithmic Portability vs. Peak Performance. Writing an algorithm for a generalized $\alpha-\beta$ model ensures it runs reasonably well on any cluster. However, tuning it for a specific topology (e.g., a 3D Torus) extracts peak performance but forces a complete rewrite if the code is moved to a Fat Tree cluster.

> **Common Confusion:** It's easy to confuse the $\alpha-\beta$ model with topology. The $\alpha-\beta$ model assumes a uniform cost for communication between *any* two nodes, effectively pretending the network is fully connected. Topology is the study of why that assumption breaks down in practice and how to design algorithms that respect the physical wiring.

## 2. Key Network Properties

Abstractly, a distributed memory machine is modeled as a set of $P$ computing nodes connected by a network.

### 2.1. Links and Diameter

- **Links**: The number of connections (wires) in the network. 
  - *Intuition*: It serves as a proxy for the network's cost. More cables mean higher hardware and maintenance costs, but generally faster communication.
- **Diameter ($\Delta$)**: The longest shortest path between any two nodes. 
  - *Intuition*: It serves as a proxy for the maximum distance any message must travel in the absence of network contention. If the diameter is high, even a single "ping" between the most distant nodes takes a long time.

> **Tradeoff:** There is a fundamental tension between Links and Diameter. Minimizing the diameter requires adding more links, which increases the physical cost, power consumption, and cooling requirements of the supercomputer.

**Examples:**
- **Linear (1D) Network**: $P$ nodes in a line.
  - *Mental Model*: A bucket brigade or a single long hallway of rooms.
  - Links: $P - 1$
  - Diameter: $P - 1$
- **2D Mesh Network**: $P$ nodes in a $\sqrt{P} \times \sqrt{P}$ grid.
  - *Mental Model*: A city grid with avenues and streets.
  - Links: $\approx 2P$
  - Diameter: $2(\sqrt{P} - 1)$ (Manhattan distance between opposite corners)
- **Fully Connected Network**: Every node directly connects to every other node.
  - *Mental Model*: A conference call where everyone can hear everyone directly.
  - Links: $\approx P^2 / 2$
  - Diameter: $1$

> **Fact Check:** The exact number of links in a Fully Connected Network is $P(P - 1) / 2$. The approximation $P^2 / 2$ is accurate for large $P$. Also, the diameter of a 2D mesh is exactly $2(\sqrt{P} - 1)$ assuming it's a perfect square grid without wraparound.

> **Hypothetical:** If you tried to build a fully connected network for a modern supercomputer with 100,000 nodes, you would need nearly 5 billion cables! This is why fully connected networks only exist at very small scales (e.g., inside a single CPU chip) or as logical abstractions.

### 2.2. Bisection Width and Bandwidth

- **Bisection Width ($B$)**: The minimum number of communication links that must be removed to cut the network into two equal parts (measured by node count).
  - *Importance*: Critical for global communication patterns like the all-to-all personalized exchange, where all nodes communicate across the bisection simultaneously.
  - *Intuition*: Imagine a villain wants to split your supercomputer into two disconnected halves by cutting cables. The bisection width is the minimum number of cuts they must make. It represents the ultimate bottleneck of the system during a massive data shuffle.
- **Bisection Bandwidth**: The speed across the bisection. If all links have a speed $\beta$ (words per unit time), it is the bisection width multiplied by $\beta$. If links have unequal speeds, it is the minimum total bandwidth across any cut dividing the network in half.

> **Fact Check:** Bisection width mathematically guarantees a lower bound on communication time for all-to-all exchanges. If $N$ bytes must cross the bisection and the bisection bandwidth is $BW$, the absolute minimum time required is $N / BW$, regardless of how perfectly you route the traffic.

**Examples of Bisection Widths:**
- **Linear Network**: $B = 1$ (cutting the middle link splits the line in half).
- **2D Mesh**: $B = \sqrt{P}$ (cutting across the middle row or column).
- **Fully Connected Network**: $B \approx P^2 / 4$.

> **Mental Model:** Bisection bandwidth is like the maximum number of cars per hour that can cross the bridges between two halves of a city. If everyone wants to drive to the other side at 5 PM, the bisection bandwidth strictly limits how long the traffic jam will last.

## 3. Improving Network Topologies

How do we take a basic network and make it better without rewiring the entire system?

### 3.1. Improving a Linear Network
Adding a single link between the endpoints of a linear network turns it into a **Ring Network**.
- *Intuition*: Instead of a long hallway, the rooms form a circle. If you are at the end, you no longer have to walk all the way back; you just step across the new link.
- The longest path becomes half the perimeter, roughly halving the diameter to $\approx P / 2$.

> **Intuition:** A Ring Network essentially cuts the maximum travel distance in half because you can always choose the shorter direction (clockwise or counter-clockwise) to reach any destination.

> **Fact Check:** The exact diameter of a Ring Network is $\lfloor P/2 \rfloor$. For an even number of nodes, it is exactly $P/2$. For an odd number, it is $(P-1)/2$.

### 3.2. Improving a 2D Mesh
- **Reducing Diameter**: Adding links connecting opposite corners, adding a ring connecting the corners, or adding wraparound links all reduce the diameter by roughly half.
- **Improving Bisection Width**: Only adding **wraparound links** (from left to right and top to bottom) doubles the bisection width (from $\sqrt{P}$ to $2\sqrt{P}$). This transforms the 2D mesh into a **2D Torus**.
  - *Mental Model*: Think of the classic arcade game *Pac-Man* or *Asteroids*. When you go off the right edge of the screen, you instantly appear on the left. A Torus takes a flat 2D grid and glues the edges together, turning a flat sheet into a donut shape! To cut a donut in half, you have to cut through two sides, which is why the bisection width doubles.

> **Tradeoff:** While a 2D Torus doubles the bisection width and halves the diameter compared to a 2D Mesh, the long wraparound cables can be physically difficult to route in a datacenter, often requiring longer wires that might have slightly higher latency or require repeaters.

> **Fact Check:** To solve the long wraparound cable problem, hardware engineers use a "folded torus" layout. Nodes are interleaved so that logically adjacent nodes are placed physically near each other, meaning the "wraparound" cable is exactly the same length as any other cable in the system!

## 4. Other Network Topologies

### 4.1. Tree and Fat Tree Networks
Compute nodes are at the leaves; interior nodes are routers.
- **Complete Binary Tree** (with $P$ leaves):
  - *Intuition*: Like a corporate hierarchy where all communication must go up the chain of command.
  - Links: $\approx P$
  - Diameter: $\log P$ (Excellent scaling, short paths)
  - Bisection Width: $1$ (Terrible scaling. Cutting near the root splits the network, acting as a massive choke point).
- **Fat Tree**: Resolves the bisection bottleneck by increasing bandwidth at higher levels in the tree. Common in medium-scale cluster environments (thousands of nodes).
  - *Mental Model*: To fix the corporate hierarchy bottleneck, you give the CEO and VPs a massive bandwidth pipeline (thicker cables, or multiple parallel links) so the root doesn't choke under pressure. The closer to the root you get, the "fatter" the connections become.

> **Fact Check:** A perfectly scaled Fat Tree maintains a bisection bandwidth that scales linearly with the number of nodes (effectively acting like a Fully Connected network for bisection purposes). It is one of the most popular topologies in modern datacenters (often implemented as Clos networks).

> **Example:** In a typical datacenter Fat Tree, the "leaves" are servers in racks. The "branches" are Top-of-Rack (ToR) switches, and the "root" consists of massive core switches. By using multiple 100Gbps or 400Gbps links near the root, the network avoids becoming a bottleneck even when many racks communicate simultaneously.

### 4.2. Higher-Dimensional Meshes and Torii
A $d$-dimensional mesh or torus is a high-dimensional cube with $P^{1/d}$ nodes per edge.
- **Diameter**: Decreases as $P^{1/d}$ but increases linearly with $d$.
- *Context*: Used in many top supercomputers (like the 3D Torus used in older Cray systems or the 5D/6D Torus in Fujitsu's K computer). It strikes a practical balance between wire cost and routing efficiency.

> **Tradeoff:** Higher dimensional torii significantly reduce diameter and increase bisection width, but the node routing hardware must have more ports (e.g., a 6D torus requires a router with 12 network ports per node, significantly increasing the complexity and cost of the network interface cards).

> **Common Confusion:** A "3D Torus" does not mean the computers are physically stacked in a 3D cube (though they might be). It refers to the logical wiring. You can wire a 3D Torus while all the servers sit in flat rows of racks, though the physical cabling will be very complex!

### 4.3. Hypercube
A hypercube is roughly a $\log P$-dimensional torus. The number of nodes is $P = 2^d$, where $d$ is the dimension. Constructed recursively by connecting corresponding nodes of two $(d-1)$-dimensional hypercubes.
- *Mental Model*: A 0D hypercube is a dot. 1D is a line. 2D is a square. 3D is a cube. 4D is a tesseract. Each time you step up a dimension, you duplicate the shape and connect the matching corners.
- **Links**: $P \log P$
- **Diameter**: $\log P$
- **Bisection Width**: $P / 2$
- *Trade-off*: Highly connected (low diameter, large bisection) but very expensive in terms of wires. It's an engineer's wiring nightmare but a programmer's dream.

> **Fact Check:** The formula $P \log_2 P$ gives the number of directed edges. The number of undirected physical links in a hypercube is exactly $(P \log_2 P) / 2$. Also, the bisection width is exactly $P/2$.

> **Hypothetical:** Imagine an algorithm that relies heavily on a hypercube topology. If a single node or link fails, the perfect symmetry is broken. Hypercube algorithms often need complex fallback mechanisms to handle hardware faults because of this rigid structure.

## 5. Mappings and Congestion

**Background Context:** Imagine you wrote an algorithm assuming the computers were arranged in a 2D Torus (the **logical network**). But the supercomputer you are actually running on is physically wired as a 1D Ring (the **physical network**). When an algorithm designed for a logical network runs on a physical network, its performance depends on the mapping between the two.

- **Congestion**: The maximum number of logical edges that map to a given physical edge. It models how much messages might serialize (overlap) due to network contention.
  - *Intuition*: Think of it as rerouting a 4-lane highway's worth of traffic (logical) onto a 1-lane dirt road (physical). Congestion measures the maximum number of overlapping paths cramming into any single physical cable.
  - If a logical ring maps to a physical 2D torus row-by-row, congestion is $1$ (the torus edges are a superset of the ring).
  - If a logical 2D torus maps to a physical 1D ring row-by-row, congestion is $\sqrt{P} + 2$ (vertical and wraparound edges must traverse many ring links, piling up traffic).

> **Mental Model:** Think of mapping a logical graph to a physical graph as trying to fold a complex origami shape out of a piece of paper. If the shapes don't perfectly align, you end up with crumpled, overlapping layers—that's your congestion.

### 5.1. Lower Bound on Congestion
Estimating congestion by counting edges is tedious. A simpler lower bound relies on bisection widths:
- Let $B_{\text{logical}}$ be the bisection width of the logical network.
- Let $B_{\text{physical}}$ be the bisection width of the physical network.
- **Lower Bound on Congestion**: $\ge \frac{B_{\text{logical}}}{B_{\text{physical}}}$

> **Fact Check:** The actual lower bound involves taking the ceiling of this ratio: $\lceil B_{\text{logical}} / B_{\text{physical}} \rceil$, because congestion must be an integer (you can't have half a message path mapped to a physical wire).

*Example*: Mapping a Logical 2D Torus ($B \approx 2\sqrt{P}$) to a Physical 1D Ring ($B = 2$).
The lower bound is $\sqrt{P}$, which is close to the true congestion ($\sqrt{P} + 2$).

*Implication*: To avoid massive traffic jams (congestion), the physical network must have a bisection width at least as large as the logical network's. You cannot squeeze a high-bandwidth algorithm through a low-bandwidth physical topology without penalty.

> **Tradeoff:** Software engineers love to write algorithms assuming a Fully Connected or Hypercube logical network because it's mathematically elegant. However, running these on physical Torus or Tree networks leads to high congestion. The tradeoff is between developer productivity (using simple logical models) and execution performance (optimizing for the physical layout).

## 6. Exploiting Higher Dimensions

Using networks with higher dimensions (and thus more links) can improve algorithmic performance beyond 1D limits. 

*Intuition*: Why do we care about higher dimensions? Because 1D algorithms hit a mathematical wall. By utilizing a grid or hypercube structure, we can parallelize the communication itself, turning one massive slow step into a few very fast steps.

### 6.1. All-Gather on a 2D Mesh
Instead of a single 1D bucketing all-gather (which takes $\approx \alpha P + \beta N$), a 2D mesh allows a two-step approach:
- *Mental Model*: Instead of 1,000 people in a single line passing notes one by one, arrange them in a grid.
1. **Row All-Gather**: Perform 1D all-gather within each row (using $\sqrt{P}$ processes). Now everyone knows their row's information.
2. **Column All-Gather**: Perform 1D all-gather within each column. Now everyone has everything!
- **Result**: The latency ($\alpha$) term is improved from $O(P)$ to $O(\sqrt{P})$, getting closer to the theoretical lower bound, while keeping the bandwidth ($\beta$) term optimal.

> **Intuition:** By breaking the problem into two orthogonal dimensions (rows, then columns), we change the latency scaling from linear ($O(P)$) to a square root ($O(\sqrt{P})$). This is a classic divide-and-conquer strategy applied to physical space.

> **Fact Check:** The theoretical lower bound for the latency term in an all-gather is $O(\log P)$, which is achievable on a hypercube or fat tree. The 2D mesh brings it down to $O(\sqrt{P})$, which is the diameter of the 2D mesh.

### 6.2. 2D Broadcast
To broadcast on a 2D mesh, a **tree-based broadcast** in each row followed by a tree-based broadcast in each column is highly efficient. 
- *Context*: Rather than one node yelling down a long line, it tells a few row leaders, who tell their column leaders.
- The latency cost is proportional to $\log P$, which is superior to $O(\sqrt{P})$ scaling from a simple scatter-gather bucketing scheme.

> **Fact Check:** The latency for this tree-based broadcast is actually $2 \log_2(\sqrt{P}) = \log_2 P$, which perfectly matches the latency of a broadcast on a hypercube, making it asymptotically optimal for latency!

> **Hypothetical:** What if we used a 3D mesh instead? We would do tree broadcasts in X, then Y, then Z. The latency would scale as $O(P^{1/3})$, showing that higher dimensions progressively compress the communication time.

### 6.3. All-to-All Personalized Exchange
Every node sends a unique message to every other node (e.g., performing a matrix transpose). It is the ultimate stress test for a network, heavily bottlenecked by bisection bandwidth.
- **On a Ring Network** ($P$ nodes, messages of size $m$, total size $n = mP$):
  - Average distance a message travels: $\approx P / 4$.
  - Lower bound on communication time is proportional to the total volume divided by total speed.
  - Algorithm (circular shifts): Nodes continuously pass data to their neighbors. Takes $P-1$ steps, achieving an asymptotic bandwidth cost of $\approx \beta \frac{nP}{2}$, which is within a factor of 2 of the lower bound.
- **Higher Dimensions**: To reduce the all-to-all bandwidth term from linear ($O(P)$) to logarithmic or constant, a network with linear bisection width is required, such as a **Hypercube** or a **Fully Connected Network**. These richer topologies allow multiple data exchanges to bypass each other without colliding.

> **Mental Model:** Think of an all-to-all exchange like every person in a stadium needing to hand a specific, personalized envelope to every other person simultaneously. Without a highly connected network (many wide aisles and tunnels), the resulting collisions make it impossibly slow.

> **Common Confusion:** All-to-All is often confused with All-Gather. In All-Gather, everyone gets the *same* combined message. In All-to-All, node A sends a *different* specific message to node B than it sends to node C. This makes All-to-All much harder to optimize because data cannot simply be combined or duplicated along the way.
