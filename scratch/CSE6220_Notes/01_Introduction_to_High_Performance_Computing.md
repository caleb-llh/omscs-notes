# Introduction to High Performance Computing (HPC)

*Background Context: Welcome to the world of High Performance Computing (HPC)! In this domain, we push the limits of software and hardware to solve humanity's most complex problems. From predicting weather patterns to discovering new drugs, HPC (or Supercomputing) is the engine behind modern scientific discovery and large-scale data analysis.*

## Course Overview and Logistics
- **Instructor:** Rich Vuduc, Professor at the School of Computational Science and Engineering at Georgia Tech.
- **Location:** Klaus Advanced Computing Building (a central hub for HPC at GT).
- **Course Focus:** Extracting parallelism and data locality from algorithms and data structures.
  - *Intuition: "Parallelism" is about doing many things at once. "Data locality" is about keeping the data you need close to where you are doing the work, so you don't waste time fetching it.*
- **Prerequisites:** Minimum of CS and Math 101.
- **Course Components:**
  - **Videos:** Designed to build intuition.
  - **Quizzes:** Interspersed in videos to introduce and test new concepts.
  - **Readings:** Provide the formal, rigorous details required for projects and exams.
  - **Mini Projects:** Focus on writing real code. Implementing algorithms and data structures is essential for understanding engineering tradeoffs.

## What is Supercomputing?
- **Terminology:** The term "Supercomputing" is preferred over "High Performance Computing (HPC)" as it better captures the compelling nature of the field.
- **Definition:** Solving complex, large-scale computational problems as efficiently as possible.
  - *Mental Model: Imagine trying to build a highly optimized factory. You don't just want it to work; you want the absolute maximum throughput with the minimum wasted effort.*
- **Applications:** Simulating earth dynamics, studying biomolecular systems, analyzing social networks, and understanding the cosmos.
- **Core Challenge:** Given a computational problem and a machine, how to compute at the absolute limits of scale and speed.
- **Physical Limits:** Computation is ultimately constrained by physics, including the speed of light, energy consumption, power, and heat dissipation.
  - *Example: Why does a supercomputer get so hot? Because moving billions of electrons to perform calculations and transfer data generates immense heat. At supercomputing scales, cooling the machine and paying the electricity bill are just as critical as the algorithms themselves!*
- **Future Frontiers:** Quantum computing represents one of the ultimate physical limits of computation, pushing beyond conventional computing boundaries.

## Machine Models in HPC
The course is structured around major units reflecting different conceptual models of a computer architecture to understand how algorithms run.

*Background Context: A "machine model" is an abstraction. Just like a physicist models a cow as a sphere to simplify the math, computer scientists use machine models to simplify complex hardware. This allows us to mathematically analyze how fast an algorithm will run without worrying about the exact brand or microscopic wiring of the processor.*

### 1. The Baseline: Sequential (Serial) RAM Model
- **Architecture:** A single serial processor connected to memory.
- **Operation:** The processor issues instructions that operate on data (operands) residing in memory.
- **Analysis:** 
  - Assumes all instructions have a bounded constant cost.
  - Performance is analyzed using Big O notation based on the input size.
- **Context:** The standard model taught in introductory computer science (CS 101).
- **Intuition & Mental Model:** 
  - *Imagine a single chef (the processor) in a kitchen (the computer). The chef has a recipe book (the program) and fetches ingredients one by one from the pantry (memory). The chef can only chop one vegetable or stir one pot at a time. The time it takes to cook the meal depends linearly on the number of steps.*
- **Example:** A simple `for` loop that iterates through an array of numbers and adds them up one by one.

### 2. Parallel RAM (PRAM) Model
- **Architecture:** Multiple processors that all share and can see the same memory (Shared Memory Model).
- **Operation:** Processors coordinate and communicate by modifying shared variables.
- **Analysis:** 
  - Assumes a bounded constant cost per operation.
  - Analyzed using Big O notation, aiming to reduce total computational cost by up to a factor of $P$ (the total number of processors).
- **Context:** The simplest model for understanding a shared-user multi-core machine with Uniform Memory Access (UMA).
- **Intuition & Mental Model:**
  - *Imagine a kitchen with multiple chefs (processors) who all share the exact same massive pantry and prep table (shared memory). They can all grab ingredients simultaneously. The challenge is ensuring they don't bump into each other or try to chop the same onion at the same time (a "race condition").*
- **Example:** Splitting a large array of numbers into $P$ chunks. Each processor adds up its chunk simultaneously, and then they combine their subtotals. If you have 4 processors, the work theoretically gets done up to 4 times faster!

### 3. Distributed Memory Network Model
- **Architecture:** An interconnected network of multiple distinct RAM computers.
- **Operation:** 
  - Each processor has its own private memory.
  - No processor can read or write to the memory of another.
  - Coordination is achieved exclusively by sending and receiving messages over the network.
- **Analysis:** Performance evaluation is based on counting the total number of messages sent and the total volume of communication (data transferred).
- **Intuition & Mental Model:**
  - *Imagine multiple food trucks (computers), each with its own chef and its own small pantry (private memory). They cannot see or reach into each other's pantries. If Food Truck A needs onions from Food Truck B, Chef A must call Chef B on the radio and ask them to send a delivery runner over with the onions (sending a message).*
- **Example:** Modern supercomputing clusters or cloud data centers (like AWS or Azure) where thousands of separate servers are linked via high-speed Ethernet or InfiniBand networks. Frameworks like MPI (Message Passing Interface) operate heavily on this model.

### 4. Two-Level Input/Output (I/O) Model
- **Architecture:** One or more processors connected to a slower main memory, with at least one level of fast intermediate memory (such as a cache or virtual memory) sitting between them.
- **Operation:** The fast intermediate memory acts as a scratch space.
- **Analysis:** Focuses heavily on data locality. The core metric is determining how much data needs to move back and forth from main memory to the processor through the fast memory layer.
- **Goal:** Designing algorithms that effectively exploit memory hierarchies to minimize expensive data movement.
- **Intuition & Mental Model:**
  - *Imagine our chef again. The main memory is a massive warehouse down the street (slow to access, huge capacity). The cache is a small prep table right next to the cutting board (fast to access, tiny capacity). To be efficient, the chef shouldn't walk to the warehouse for every single carrot. Instead, they should bring a whole crate of carrots to the prep table at once, chop them all, and then take the chopped carrots back. This minimizes the "expensive data movement" (the walk to the warehouse).*
- **Example:** Optimizing matrix multiplication. If you multiply large matrices naïvely, the processor constantly waits for data to arrive from main memory. By processing the matrices in small "blocks" or "tiles" that fit perfectly into the L1/L2 cache, the algorithm runs significantly faster because it maximizes *data locality*.
