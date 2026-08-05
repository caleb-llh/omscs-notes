# Network Topology

## 1. Introduction

**Background Context:** When designing parallel algorithms, we often imagine computing nodes magically talking to each other instantly. However, in reality, physical wires (or optical cables) connect these computers. At small scales (e.g., your laptop with 4 cores), the specific layout doesn't matter much. But in parallel and distributed computing at massive scales (supercomputers with millions or billion+ processor systems), the physical layout—the **network topology**—dictates whether an algorithm runs in minutes or days.

While cost models (like the $\alpha-\beta$ or latency-bandwidth models) abstract away network details, understanding topology helps analyze how an algorithm designed for one network will perform on another. 

**Mental Model:** Think of the computing nodes as cities and the network topology as the highway system connecting them. The $\alpha-\beta$ cost model gives us the "toll fee" and "speed limit" for an average trip, but the topology tells us exactly which roads exist, where the traffic jams (bottlenecks) will happen, and how long a cross-country road trip actually takes.

## 2. Key Network Properties

Abstractly, a distributed memory machine is modeled as a set of $P$ computing nodes connected by a network.

### 2.1. Links and Diameter

- **Links**: The number of connections (wires) in the network. 
  - *Intuition*: It serves as a proxy for the network's cost. More cables mean higher hardware and maintenance costs, but generally faster communication.
- **Diameter ($\Delta$)**: The longest shortest path between any two nodes. 
  - *Intuition*: It serves as a proxy for the maximum distance any message must travel in the absence of network contention. If the diameter is high, even a single "ping" between the most distant nodes takes a long time.

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

### 2.2. Bisection Width and Bandwidth

- **Bisection Width ($B$)**: The minimum number of communication links that must be removed to cut the network into two equal parts (measured by node count).
  - *Importance*: Critical for global communication patterns like the all-to-all personalized exchange, where all nodes communicate across the bisection simultaneously.
  - *Intuition*: Imagine a villain wants to split your supercomputer into two disconnected halves by cutting cables. The bisection width is the minimum number of cuts they must make. It represents the ultimate bottleneck of the system during a massive data shuffle.
- **Bisection Bandwidth**: The speed across the bisection. If all links have a speed $\beta$ (words per unit time), it is the bisection width multiplied by $\beta$. If links have unequal speeds, it is the minimum total bandwidth across any cut dividing the network in half.

**Examples of Bisection Widths:**
- **Linear Network**: $B = 1$ (cutting the middle link splits the line in half).
- **2D Mesh**: $B = \sqrt{P}$ (cutting across the middle row or column).
- **Fully Connected Network**: $B \approx P^2 / 4$.

## 3. Improving Network Topologies

How do we take a basic network and make it better without rewiring the entire system?

### 3.1. Improving a Linear Network
Adding a single link between the endpoints of a linear network turns it into a **Ring Network**.
- *Intuition*: Instead of a long hallway, the rooms form a circle. If you are at the end, you no longer have to walk all the way back; you just step across the new link.
- The longest path becomes half the perimeter, roughly halving the diameter to $\approx P / 2$.

### 3.2. Improving a 2D Mesh
- **Reducing Diameter**: Adding links connecting opposite corners, adding a ring connecting the corners, or adding wraparound links all reduce the diameter by roughly half.
- **Improving Bisection Width**: Only adding **wraparound links** (from left to right and top to bottom) doubles the bisection width (from $\sqrt{P}$ to $2\sqrt{P}$). This transforms the 2D mesh into a **2D Torus**.
  - *Mental Model*: Think of the classic arcade game *Pac-Man* or *Asteroids*. When you go off the right edge of the screen, you instantly appear on the left. A Torus takes a flat 2D grid and glues the edges together, turning a flat sheet into a donut shape! To cut a donut in half, you have to cut through two sides, which is why the bisection width doubles.

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

### 4.2. Higher-Dimensional Meshes and Torii
A $d$-dimensional mesh or torus is a high-dimensional cube with $P^{1/d}$ nodes per edge.
- **Diameter**: Decreases as $P^{1/d}$ but increases linearly with $d$.
- *Context*: Used in many top supercomputers (like the 3D Torus used in older Cray systems or the 5D/6D Torus in Fujitsu's K computer). It strikes a practical balance between wire cost and routing efficiency.

### 4.3. Hypercube
A hypercube is roughly a $\log P$-dimensional torus. The number of nodes is $P = 2^d$, where $d$ is the dimension. Constructed recursively by connecting corresponding nodes of two $(d-1)$-dimensional hypercubes.
- *Mental Model*: A 0D hypercube is a dot. 1D is a line. 2D is a square. 3D is a cube. 4D is a tesseract. Each time you step up a dimension, you duplicate the shape and connect the matching corners.
- **Links**: $P \log P$
- **Diameter**: $\log P$
- **Bisection Width**: $P / 2$
- *Trade-off*: Highly connected (low diameter, large bisection) but very expensive in terms of wires. It's an engineer's wiring nightmare but a programmer's dream.

## 5. Mappings and Congestion

**Background Context:** Imagine you wrote an algorithm assuming the computers were arranged in a 2D Torus (the **logical network**). But the supercomputer you are actually running on is physically wired as a 1D Ring (the **physical network**). When an algorithm designed for a logical network runs on a physical network, its performance depends on the mapping between the two.

- **Congestion**: The maximum number of logical edges that map to a given physical edge. It models how much messages might serialize (overlap) due to network contention.
  - *Intuition*: Think of it as rerouting a 4-lane highway's worth of traffic (logical) onto a 1-lane dirt road (physical). Congestion measures the maximum number of overlapping paths cramming into any single physical cable.
  - If a logical ring maps to a physical 2D torus row-by-row, congestion is $1$ (the torus edges are a superset of the ring).
  - If a logical 2D torus maps to a physical 1D ring row-by-row, congestion is $\sqrt{P} + 2$ (vertical and wraparound edges must traverse many ring links, piling up traffic).

### 5.1. Lower Bound on Congestion
Estimating congestion by counting edges is tedious. A simpler lower bound relies on bisection widths:
- Let $B_{\text{logical}}$ be the bisection width of the logical network.
- Let $B_{\text{physical}}$ be the bisection width of the physical network.
- **Lower Bound on Congestion**: $\ge \frac{B_{\text{logical}}}{B_{\text{physical}}}$

*Example*: Mapping a Logical 2D Torus ($B \approx 2\sqrt{P}$) to a Physical 1D Ring ($B = 2$).
The lower bound is $\sqrt{P}$, which is close to the true congestion ($\sqrt{P} + 2$).

*Implication*: To avoid massive traffic jams (congestion), the physical network must have a bisection width at least as large as the logical network's. You cannot squeeze a high-bandwidth algorithm through a low-bandwidth physical topology without penalty.

## 6. Exploiting Higher Dimensions

Using networks with higher dimensions (and thus more links) can improve algorithmic performance beyond 1D limits. 

*Intuition*: Why do we care about higher dimensions? Because 1D algorithms hit a mathematical wall. By utilizing a grid or hypercube structure, we can parallelize the communication itself, turning one massive slow step into a few very fast steps.

### 6.1. All-Gather on a 2D Mesh
Instead of a single 1D bucketing all-gather (which takes $\approx \alpha P + \beta N$), a 2D mesh allows a two-step approach:
- *Mental Model*: Instead of 1,000 people in a single line passing notes one by one, arrange them in a grid.
1. **Row All-Gather**: Perform 1D all-gather within each row (using $\sqrt{P}$ processes). Now everyone knows their row's information.
2. **Column All-Gather**: Perform 1D all-gather within each column. Now everyone has everything!
- **Result**: The latency ($\alpha$) term is improved from $O(P)$ to $O(\sqrt{P})$, getting closer to the theoretical lower bound, while keeping the bandwidth ($\beta$) term optimal.

### 6.2. 2D Broadcast
To broadcast on a 2D mesh, a **tree-based broadcast** in each row followed by a tree-based broadcast in each column is highly efficient. 
- *Context*: Rather than one node yelling down a long line, it tells a few row leaders, who tell their column leaders.
- The latency cost is proportional to $\log P$, which is superior to $O(\sqrt{P})$ scaling from a simple scatter-gather bucketing scheme.

### 6.3. All-to-All Personalized Exchange
Every node sends a unique message to every other node (e.g., performing a matrix transpose). It is the ultimate stress test for a network, heavily bottlenecked by bisection bandwidth.
- **On a Ring Network** ($P$ nodes, messages of size $m$, total size $n = mP$):
  - Average distance a message travels: $\approx P / 4$.
  - Lower bound on communication time is proportional to the total volume divided by total speed.
  - Algorithm (circular shifts): Nodes continuously pass data to their neighbors. Takes $P-1$ steps, achieving an asymptotic bandwidth cost of $\approx \beta \frac{nP}{2}$, which is within a factor of 2 of the lower bound.
- **Higher Dimensions**: To reduce the all-to-all bandwidth term from linear ($O(P)$) to logarithmic or constant, a network with linear bisection width is required, such as a **Hypercube** or a **Fully Connected Network**. These richer topologies allow multiple data exchanges to bypass each other without colliding.
