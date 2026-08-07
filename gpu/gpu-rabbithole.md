### m1
- nuances between SIMD vs SPMD? Is SPMD compiled down into SIMD? What are CPU vector extensions and how does the OS and applications integrate with it?
- What exactly is CUDA?
- relate these concepts - core, SM, lanes, grid, threads, warps, warp scheduler, SP, context, stream, graph, grid, cluster. what's the purpose of each abstraction?
- chip vs die vs subcore vs sm vs core vs MIG instance?
- where is global, shared, local and constant memory stored in a GPU?
- how is matrix multiply-accumulate done in a single instruction? how does reducing floating point precision lead to twice as many mathematical operations - what was the bottleneck?

> the deeper a pipeline, the more it behaves like streaming instead of batch, thus maximising throughput.

### m2 - parallel programming
- categorise and put these on a table: master/worker pattern, loop parallelism pattern, SPMD pattern, fork/join pattern, pipeline pattern. what else?
- omp single vs omp critical? how is the ratio split in in omp parallel sections?
- What is the intuition/philosophy for synchronization in shared vs distributed memory models? what exactly is synchronisation? how is it related to distributed synchronisation?

> Three purposes of synchronisation: 
> 1. preventing collision (mutual exclusion) - local: mutex. distributed: distributed locks
> 2. waiting for dependencies (sequence control) - local: condition variable. distributed: message queues
> 3. gathering the team (barriers) 

> Distributed memory synchronization ensures that **isolated data moves safely across space** (the network), while shared memory synchronization ensures that **shared data changes safely across time** (ordered execution).

### m3 - cuda fundamentals
- what is the responsibility of the OS, device driver, and device controller when it comes to CUDA programs? what other controllers/processors are involved?
- `__syncthreads()` vs `__syncwarp()` vs `cuda:barrier`?
- synchronisation primitives (implicit and explicit) in CUDA?

### m4 - gpu microarchitecture & multithreading
- can occupancy and thread block scheduling only be determined during runtime? how is dynamic shared memory size handled? why do registers per block vary? how does register allocation work in GPUs, why is there padding involved? how does the lifecycle of a variable and register differ between CPUs and GPUs? are operand buffers different from the register files?
- how does padding or stride resolve shared memory bank conflicts?
- does memory coalescing happen before the actual memory request, where is it done? is the MSHR involved in the process? MSHR and memory-level parallelism (MLP) vs memory coalescing? hardware requirements to enable both?

### m5 - gpu performance optimisation
- code example for pipeline data transfers and async data transfers? cudaMemcpyAsync vs CUDA streams?
- what problem does UVA solve? is it developer convenience or performance or others?
- why does using lower precision arithmetic improve computation overhead if the ALU is bounded in size? how does ALU, multipliers and tensor cores benefit from increased throughput with lower precision - how does this multiplexing happen?
- how does Warp Shuffle, Vote, and Ballot work?

### m6 - gpu architecture - divergence & memory optimisation
- are predicated execution and active masks mutually exclusive when handling divergent execution? what is the structure of a SIMT stack frame and how does it handle a conditional branch? how does Independent Thread Scheduling replace SIMT stack to handle divergent paths? is Independent Thread Scheduling and Dynamic Warp Formation related?
- operand collector/register file cache vs operand buffer? is there a Register Alias Table in GPUs for register file virtualization?
- why is GPU shared memory regarded as a software-managed cache? how does unified SRAM support the different access patterns of register files vs shared memory?

### m7 - virtual memory & warp scheduling
- Does the TLB and MMU, page tables, physical pages, all reside in the GPU device or host? What exactly does virtual memory enable in GPUs? Why is it that older GPUs can use physical addresses directly without translation? Why does both the host and device need the same copy of physical data in unified virtual memory? Where does the source of truth of data reside? How is coherence or consistency ensured?
- Is there a cache controller or memory controller in GPUs? Who handles the TLB miss? is TLB miss handler and a Page Table Walker (PTW) the same thing? is page-table walk implemented in hardware inside GPUs or in the CUDA driver? when does coalescing and MSHR come in? are these translations and access synchronous? 
- Why is it typical for L1 cache to use virtual addresses and L2 cache to use physical address? 
- How does IOMMU and DMA work? what about with RDMA? be explicit what happens and which component is on the host or device.
- virtual memory allocation vs writing to page table vs physical frame allocation - are they distinct steps? how does lazy allocation or demand paging work?

> While loading maximum warps onto an SM is crucial for hiding execution latency, letting them all run completely unthrottled destroys data locality. Advanced microarchitectures must use two-level, cache-conscious scheduling to strike a perfect physical equilibrium between massive parallel throughput and local cache preservation.

### m8 - gpu modeling & simulation
- what do events refer to when talking about event-driven simulation? execution-driven simulation vs cycle-level simulation? modeling vs simulation?
- how do sectored caches work?
- what is the point of a sub-core abstraction?
- explain: `CPI_MT = (CPI_single / W_depth) + Resource_Contentions`

### m9 - multi-gpus
- nvlink vs nvswitch vs infiniband vs pcie? what is a silicon interposer and how does HBM work? How does RDMA come into the picture - at which scale? 
- how does hardware, OS, network all work together to enable RDMA? Trace it out. how is safety/isolation/protection of memory spaces enforced in DMA and RDMA? what is the key insight? does RDMA have a control plane?
- how does memory mapping, allocation and translation work in NUMA why is it hard to marry the memory mapping and scheduling? how does pairing RDMA network cards with NVLink/NVSwitch routing look like? does scheduling happen on the driver running on the CPU for a multi-GPU setup?
- Core Principles of Distributed State Architectures like distributed caches or distributed shared memory? dynamics of Vertical Caching vs. Horizontal Nodes.
- GPUdirect RDMA vs normal rdma? how does GPUDirect RDMA and NVLink and NVSwitch and Infiniband work together?
- what problem does CUDA streams, MPS and MIG solve? How does CUDA streams and CUDA graphs work?  What does a CUDA context contain? How does context switching look like, isn't context switching instantaneous in GPUs?  Which MPS component runs on the host? Why can't CUDA streams solve the same problem as MPS?
- Code examples of CUDA streams, MPS and MIG?

### m10 - compilers i
- AST vs LLVM IR vs PTX vs SASS - why so many intermediate representations between code and binary
- statement vs directive vs instruction
- why are there basic blocks in PTX if there is already predication?
- why is global optimization exponentially harder because execution branches loop and split?
- what is the monotonicity and distributiveness of the data flow transfer function and why does it matter?
- how does the control flow graph and the transfer function allow for GPU optimizations?

### m11 - compilers ii
- liveness analysis vs reaching definitions - how does each achieve its primary purpose?
- how does divergent analysis, reaching definitions, SSA form, liveness analysis come together, or are they separate concepts?


### m12 - ml acceleration
- Give me the gist of how distributed machine learning work and how does multi-GPU setup enable it.
- why does ML statistical computing model a good fit for GPU's underlying execution model e.g. GPUs have weak memory consistency model and do not provide precise exceptions? Why are there out-of-order memory writes in GPU? Isn't it sequentially executed in lock step? 
- what is the number of FLOPS in GEMM using FMA and why? how is a big matrix multiplication split among several tensor cores?
-  walk me through how the bits work in floating point format. why do you need different data format like TF32 (TensorFloat-32), BF16 (Bfloat16), and INT4? how does compute density (power and area) and memory bandwidth scale with bit width? how does dynamic range scaling work in the Transformer Engine?
- what are non-uniform quantization techniques and how does it allocate more representational states near zero, and why is it used for ML workloads.
- TMA async copy and async barrier vs cudamemcpyAsync and cudaStreamSynchronize?
- why is SpMV relevant to deep learning? how does structured sparsity work? how does SpMV look different from normal GEMM using FMA? if memory bound, why does pruning help to improve performance?


****
### cheatsheet
- amdahl's law
- openmp and openmpi abstractions
- occupancy
- SIMT stack
- CPI
- Roofline model
- algorithm and formula for reaching definitions
- algorithm and formula for liveness analysis
- arithmetic intensity formula
