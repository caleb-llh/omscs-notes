# Introduction to High Performance Computing (HPC)

*Background Context: Welcome to the world of High Performance Computing (HPC)! In this domain, we push the limits of software and hardware to solve humanity's most complex problems. From predicting weather patterns to discovering new drugs, HPC (or Supercomputing) is the engine behind modern scientific discovery and large-scale data analysis.*
> **Fact Check:** The Top500 list tracks the world's most powerful supercomputers, which are indeed primarily tasked with these massive-scale scientific simulations. As of recent years, we have entered the "Exascale" era, with systems like Frontier capable of over a quintillion ($10^{18}$) operations per second.
> **Mental Model:** Think of standard computing as a single highly skilled craftsman building a car. HPC is like designing the entire automated factory where thousands of robots (processors) must act in perfect, synchronized orchestration. The challenge isn't just making a faster robot; it's coordinating them so they don't block each other.

## Course Overview and Logistics
- **Instructor:** Rich Vuduc, Professor at the School of Computational Science and Engineering at Georgia Tech.
> **Fact Check:** Richard Vuduc's lab (The HPC Garage) explicitly focuses on performance tuning, emphasizing the practical realities of making code run fast on actual hardware, validating the course's engineering-first philosophy.
> **Background Context:** Professor Vuduc's research often focuses on performance tuning and auto-tuning, which deeply informs the engineering-first approach of this course.
- **Location:** Klaus Advanced Computing Building (a central hub for HPC at GT).
- **Course Focus:** Extracting parallelism and data locality from algorithms and data structures.
  - *Intuition: "Parallelism" is about doing many things at once. "Data locality" is about keeping the data you need close to where you are doing the work, so you don't waste time fetching it.*
> **Tradeoff:** Sometimes, maximizing parallelism can negatively impact data locality, and vice versa. A key challenge in HPC is balancing these two competing goals to achieve the highest overall performance. For example, scattering a dataset across 10,000 cores maximizes parallelism but destroys data locality if those cores constantly need to read each other's data over a slow network.
- **Prerequisites:** Minimum of CS and Math 101.
- **Course Components:**
  - **Videos:** Designed to build intuition.
  - **Quizzes:** Interspersed in videos to introduce and test new concepts.
  - **Readings:** Provide the formal, rigorous details required for projects and exams.
  - **Mini Projects:** Focus on writing real code. Implementing algorithms and data structures is essential for understanding engineering tradeoffs.
> **Common Confusion:** Students often think understanding the algorithm conceptually is enough. In HPC, a theoretically fast algorithm can be incredibly slow in practice if not implemented with the hardware architecture in mind. The implementation *is* the algorithm.

## What is Supercomputing?
- **Terminology:** The term "Supercomputing" is preferred over "High Performance Computing (HPC)" as it better captures the compelling nature of the field.
- **Definition:** Solving complex, large-scale computational problems as efficiently as possible.
  - *Mental Model: Imagine trying to build a highly optimized factory. You don't just want it to work; you want the absolute maximum throughput with the minimum wasted effort.*
> **Hypothetical:** If you have a weather simulation that takes 48 hours to compute tomorrow's weather, it is practically useless. Supercomputing is about taking that 48-hour calculation and completing it in 1 hour so the prediction has actionable value.
- **Applications:** Simulating earth dynamics, studying biomolecular systems, analyzing social networks, and understanding the cosmos.
- **Core Challenge:** Given a computational problem and a machine, how to compute at the absolute limits of scale and speed.
> **Mental Model:** **Amdahl's Law vs. Gustafson's Law.** Amdahl's Law says your maximum speedup is strictly limited by the sequential part of your code (if 5% of code can't be parallelized, max speedup is 20x, no matter how many processors you have). Gustafson's Law offers a more optimistic view: in HPC, we usually scale the *problem size* up as we get more processors, meaning the parallel portion grows while the sequential bottleneck becomes a tiny fraction of the total work.
- **Physical Limits:** Computation is ultimately constrained by physics, including the speed of light, energy consumption, power, and heat dissipation.
  - *Example: Why does a supercomputer get so hot? Because moving billions of electrons to perform calculations and transfer data generates immense heat. At supercomputing scales, cooling the machine and paying the electricity bill are just as critical as the algorithms themselves!*
> **Fact Check:** The breakdown of **Dennard Scaling** in the mid-2000s is the exact reason we shifted to multi-core processors. Previously, as transistors got smaller, their power density stayed constant, allowing clock speeds to increase. When this broke down, increasing clock speeds further would literally melt the chips (the "Power Wall"), forcing the industry to scale *out* (more cores) instead of *up* (faster clocks).
> **Tradeoff:** As we pack more transistors into a smaller space to increase speed (reducing the distance electrons travel), we exponentially increase the heat density. This creates a tradeoff between computational power and the cost/complexity of cooling systems.
- **Future Frontiers:** Quantum computing represents one of the ultimate physical limits of computation, pushing beyond conventional computing boundaries.
> **Mental Model:** If classical computing is like systematically exploring a maze by walking down every path one by one very fast, quantum computing is like filling the entire maze with water simultaneously to find all possible paths to the exit at once.
> **Fact Check:** While the "maze filled with water" is a popular intuition for quantum superposition, a more accurate physics-based mental model is **wave interference**. Quantum algorithms (like Shor's or Grover's) work by designing a system where incorrect answers destructively interfere (cancel each other out) and correct answers constructively interfere (amplify), making the right answer highly probable to be measured.

## Machine Models in HPC
The course is structured around major units reflecting different conceptual models of a computer architecture to understand how algorithms run.

*Background Context: A "machine model" is an abstraction. Just like a physicist models a cow as a sphere to simplify the math, computer scientists use machine models to simplify complex hardware. This allows us to mathematically analyze how fast an algorithm will run without worrying about the exact brand or microscopic wiring of the processor.*
> **Tradeoff:** **Model Accuracy vs. Analytical Tractability.** The more accurately a model reflects real hardware (e.g., accounting for L1/L2/L3 cache sizes, branch prediction, pipeline stalls), the harder it is to mathematically prove the time complexity of an algorithm. We use simplified models because they are "good enough" for big-O analysis.

### 1. The Baseline: Sequential (Serial) RAM Model
- **Architecture:** A single serial processor connected to memory.
- **Operation:** The processor issues instructions that operate on data (operands) residing in memory.
- **Analysis:** 
  - Assumes all instructions have a bounded constant cost.
  - Performance is analyzed using Big O notation based on the input size.
> **Fact Check:** This is technically known as the **von Neumann Architecture** model. Almost all classical programming languages (C, Java, Python) are fundamentally designed around this sequential paradigm, which is why parallel programming feels "unnatural" to many developers.
> **Common Confusion:** In the real world, a division operation takes significantly longer than an addition, and fetching from memory takes much longer than a register operation. The RAM model intentionally ignores these differences to provide a simplified baseline for algorithmic analysis.
- **Context:** The standard model taught in introductory computer science (CS 101).
- **Intuition & Mental Model:** 
  - *Imagine a single chef (the processor) in a kitchen (the computer). The chef has a recipe book (the program) and fetches ingredients one by one from the pantry (memory). The chef can only chop one vegetable or stir one pot at a time. The time it takes to cook the meal depends linearly on the number of steps.*
- **Example:** A simple `for` loop that iterates through an array of numbers and adds them up one by one.

### 2. Parallel RAM (PRAM) Model
- **Architecture:** Multiple processors that all share and can see the same memory (Shared Memory Model).
> **Background Context:** PRAM is a theoretical model that doesn't perfectly exist in reality at a massive scale. As you add more processors, the "shared memory" becomes a physical bottleneck, but PRAM remains a vital conceptual tool for designing parallel algorithms.
> **Fact Check:** True uniform memory access (UMA) across thousands of processors violates the speed of light. In reality, large shared-memory systems use **NUMA (Non-Uniform Memory Access)**, where memory physically closer to a specific processor is faster for that processor to access than memory located near a different processor.
- **Operation:** Processors coordinate and communicate by modifying shared variables.
- **Analysis:** 
  - Assumes a bounded constant cost per operation.
  - Analyzed using Big O notation, aiming to reduce total computational cost by up to a factor of $P$ (the total number of processors).
- **Context:** The simplest model for understanding a shared-user multi-core machine with Uniform Memory Access (UMA).
- **Intuition & Mental Model:**
  - *Imagine a kitchen with multiple chefs (processors) who all share the exact same massive pantry and prep table (shared memory). They can all grab ingredients simultaneously. The challenge is ensuring they don't bump into each other or try to chop the same onion at the same time (a "race condition").*
- **Example:** Splitting a large array of numbers into $P$ chunks. Each processor adds up its chunk simultaneously, and then they combine their subtotals. If you have 4 processors, the work theoretically gets done up to 4 times faster!
> **Tradeoff:** While adding more processors theoretically speeds up the work, you also increase the overhead of coordinating those processors. If the chunks of work are too small, the time spent assigning the work might exceed the time spent actually doing it. This introduces the concept of **granularity**: you need "coarse-grained" work (big chunks) to outweigh the synchronization overhead.

### 3. Distributed Memory Network Model
- **Architecture:** An interconnected network of multiple distinct RAM computers.
- **Operation:** 
  - Each processor has its own private memory.
  - No processor can read or write to the memory of another.
  - Coordination is achieved exclusively by sending and receiving messages over the network.
- **Analysis:** Performance evaluation is based on counting the total number of messages sent and the total volume of communication (data transferred).
> **Fact Check:** The de facto industry standard for this model is **MPI (Message Passing Interface)**. It forces the programmer to explicitly package data, send it over the network, and have the receiving node explicitly catch it.
> **Intuition:** In a distributed system, computing a result locally is almost always faster than asking another computer for it. Therefore, minimizing communication over the network is the primary optimization goal.
- **Intuition & Mental Model:**
  - *Imagine multiple food trucks (computers), each with its own chef and its own small pantry (private memory). They cannot see or reach into each other's pantries. If Food Truck A needs onions from Food Truck B, Chef A must call Chef B on the radio and ask them to send a delivery runner over with the onions (sending a message).*
- **Example:** Modern supercomputing clusters or cloud data centers (like AWS or Azure) where thousands of separate servers are linked via high-speed Ethernet or InfiniBand networks. Frameworks like MPI (Message Passing Interface) operate heavily on this model.
> **Tradeoff:** **Latency vs. Bandwidth.** In distributed models, latency (the time it takes for the *first* byte of a message to arrive) is often a much harsher bottleneck than bandwidth (the volume of data per second). A key optimization is "message coalescing": sending one large 10MB message is vastly faster than sending ten million 1-byte messages because you pay the latency penalty only once.
> **Hypothetical:** Imagine a simulation of the galaxy where each computer simulates a different sector. If a star moves from Sector A to Sector B, Computer A must send a message to Computer B. If too many stars cross borders simultaneously, the network will be overwhelmed.

### 4. Two-Level Input/Output (I/O) Model
- **Architecture:** One or more processors connected to a slower main memory, with at least one level of fast intermediate memory (such as a cache or virtual memory) sitting between them.
- **Operation:** The fast intermediate memory acts as a scratch space.
- **Analysis:** Focuses heavily on data locality. The core metric is determining how much data needs to move back and forth from main memory to the processor through the fast memory layer.
> **Fact Check:** Historically known as the **External Memory (EM)** or **Disk Access Machine (DAM)** model, formalized by Aggarwal and Vitter in 1988. While originally designed for RAM-to-Disk transfers, it perfectly models Cache-to-RAM transfers in modern CPUs.
- **Goal:** Designing algorithms that effectively exploit memory hierarchies to minimize expensive data movement.
> **Common Confusion:** Beginners often assume that the CPU is the bottleneck. In modern systems, the CPU spends most of its time "starving" (waiting) for data to arrive from memory. The true bottleneck is often the "memory wall."
> **Tradeoff:** **Compute-Bound vs. Memory-Bound.** Algorithms fall into two categories. Compute-bound algorithms do a lot of math on a small amount of data (e.g., computing Pi). Memory-bound algorithms do very little math on a massive amount of data (e.g., summing a billion numbers). In HPC, almost all modern challenges are memory-bound. You have plenty of processing power; the trick is feeding it fast enough.
- **Intuition & Mental Model:**
  - *Imagine our chef again. The main memory is a massive warehouse down the street (slow to access, huge capacity). The cache is a small prep table right next to the cutting board (fast to access, tiny capacity). To be efficient, the chef shouldn't walk to the warehouse for every single carrot. Instead, they should bring a whole crate of carrots to the prep table at once, chop them all, and then take the chopped carrots back. This minimizes the "expensive data movement" (the walk to the warehouse).*
- **Example:** Optimizing matrix multiplication. If you multiply large matrices naïvely, the processor constantly waits for data to arrive from main memory. By processing the matrices in small "blocks" or "tiles" that fit perfectly into the L1/L2 cache, the algorithm runs significantly faster because it maximizes *data locality*.
> **Tradeoff:** Optimizing for the I/O model often leads to code that is much longer, more complex, and harder to read than the naive approach. You trade code maintainability for raw performance.
