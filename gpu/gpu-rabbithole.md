### m1
- nuances between SIMD vs SPMD? Is SPMD compiled down into SIMD? What are CPU vector extensions and how does the OS and applications integrate with it?
- relate these concepts - core, SM, lanes, grid, threads, warps, warp scheduler, SP. what's the purpose of each abstraction?
- how is matrix multiply-accumulate done in a single instruction? how does reducing floating point precision lead to twice as many mathematical operations - what was the bottleneck?
- Is the transformer engine of the hopper architecture a compiler or something run during runtime? What exactly is CUDA?

> the deeper a pipeline, the more it behaves like streaming instead of batch, thus maximising throughput.

### m2

### m7
- Does the TLB and MMU, page tables, physical pages, all reside in the GPU device or host? What exactly does virtual memory enable in GPUs? Why does both the host and device need the same copy of physical data in unified virtual memory? Where does the source of truth of data reside? How is coherence or consistency ensured?
- synchronisation primitives (implicit and explicit) in CUDA?
- Is there a cache controller or memory controller in GPUs? Who handles the TLB miss? Is it synchronous? Why is it typical for L1 cache to use virtual addresses and L2 cache to use physical address? is page-table walk implemented in hardware inside GPUs or in the CUDA driver?

> While loading maximum warps onto an SM is crucial for hiding execution latency, letting them all run completely unthrottled destroys data locality. Advanced microarchitectures must use two-level, cache-conscious scheduling to strike a perfect physical equilibrium between massive parallel throughput and local cache preservation.

### m8
- 