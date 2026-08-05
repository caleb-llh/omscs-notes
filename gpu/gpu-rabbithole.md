### m1
https://lowyx.com/posts/gt-gpu-M1/
- nuances between SIMD vs SPMD? Is SPMD compiled down into SIMD? What are CPU vector extensions and how does the OS and applications integrate with it?
- relate these concepts - core, SM, lanes, grid, threads, warps, warp scheduler, SP, context, stream. what's the purpose of each abstraction?
- chip vs die vs subcore vs sm vs core vs MIG instance?
- where is global, shared, local and constant memory stored in a GPU?
- how is matrix multiply-accumulate done in a single instruction? how does reducing floating point precision lead to twice as many mathematical operations - what was the bottleneck?
- Is the transformer engine of the hopper architecture a compiler or something run during runtime? What exactly is CUDA?

> the deeper a pipeline, the more it behaves like streaming instead of batch, thus maximising throughput.

### m2
https://lowyx.com/posts/gt-gpu-M2/

### m7
https://lowyx.com/posts/gt-gpu-M7/
- Does the TLB and MMU, page tables, physical pages, all reside in the GPU device or host? What exactly does virtual memory enable in GPUs? Why does both the host and device need the same copy of physical data in unified virtual memory? Where does the source of truth of data reside? How is coherence or consistency ensured?
- synchronisation primitives (implicit and explicit) in CUDA?
- Is there a cache controller or memory controller in GPUs? Who handles the TLB miss? Is it synchronous? Why is it typical for L1 cache to use virtual addresses and L2 cache to use physical address? is page-table walk implemented in hardware inside GPUs or in the CUDA driver?
- How does IOMMU and DMA work? be explicit what happens and which component is on the host or device.
- virtual memory allocation vs writing to page table vs physical frame allocation - are they distinct steps? how does lazy allocation or demand paging work?
- MSHR and memory-level parallelism (MLP) vs memory coalescing? hardware requirements to enable bothj?

> While loading maximum warps onto an SM is crucial for hiding execution latency, letting them all run completely unthrottled destroys data locality. Advanced microarchitectures must use two-level, cache-conscious scheduling to strike a perfect physical equilibrium between massive parallel throughput and local cache preservation.

### m9 - multi-gpus
https://lowyx.com/posts/gt-gpu-M9/
- nvlink vs nvswitch vs infiniband vs pcie? what is a silicon interposer and how does HBM work? How does RDMA come into the picture - at which scale? 
- how does hardware, OS, network all work together to enable RDMA? Trace it out. how is safety/isolation/protection of memory spaces enforced in DMA and RDMA? what is the key insight? does RDMA have a control plane?
- how does memory mapping, allocation and translation work in NUMA why is it hard to marry the memory mapping and scheduling? how does pairing RDMA network cards with NVLink/NVSwitch routing look like? does scheduling happen on the driver running on the CPU for a multi-GPU setup?
- Core Principles of Distributed State Architectures like distributed caches or distributed shared memory? dynamics of Vertical Caching vs. Horizontal Nodes.
- GPUdirect RDMA vs normal rdma? how does GPUDirect RDMA and NVLink and NVSwitch and Infiniband work together?
- what problem does CUDA streams, MPS and MIG solve? How does CUDA streams and CUDA graphs work?  What does a CUDA context contain? How does context switching look like, isn't context switching instantaneous in GPUs?  Which MPS component runs on the host? Why can't CUDA streams solve the same problem as MPS?
- Code examples of CUDA streams, MPS and MIG?

### m10 - compilers i
https://lowyx.com/posts/gt-gpu-M10/
- AST vs LLVM IR vs PTX vs SASS - why so many intermediate representations between code and binary
- statement vs directive vs instruction
- why are there basic blocks in PTX if there is already predication?
- why is global optimization exponentially harder because execution branches loop and split?
- what is the monotonicity and distributiveness of the data flow transfer function and why does it matter?
- how does the control flow graph and the transfer function allow for GPU optimizations?
- 

### m11 - compilers ii
https://lowyx.com/posts/gt-gpu-M11/
- liveness analysis vs reaching definitions - how does each achieve its primary purpose?
- how does divergent analysis, reaching definitions, SSA form, liveness analysis come together, or are they separate concepts?


### m12 - ml acceleration
https://lowyx.com/posts/gt-gpu-M12/
- Give me the gist of how distributed machine learning work and how does multi-GPU setup enable it.
- why does ML statistical computing model a good fit for GPU's underlying execution model e.g. GPUs have weak memory consistency model and do not provide precise exceptions? why do you need different data format like TF32 (TensorFloat-32), BF16 (Bfloat16), and INT4? what is the number of FLOPS in GEMM using FMA and why? how is a big matrix multiplication split among several tensor cores?




****
### cheatsheet
- 
- algorithm and formula for reaching definitions
- algorithm and formula for liveness analysis
- arithmetic intensity formula

|Feature|Reaching Definitions|Live Variables|
|---|---|---|
|Domain|Sets of definitions|Sets of variables|
|Direction|forward|backward|
|Transfer function $f_b(x)$|$gen_B \cup (x - kill_B)$|$use_B \cup (x - def_B)$|
|Boundary Condition|$\text{OUT}[\text{ENTRY}] = \emptyset$|$\text{IN}[\text{EXIT}] = \emptyset$|
|Meet Operation ($\wedge$)|$\cup$|$\cup$|
|Equations|$\text{OUT}[B] = f_b(\text{IN}[B])$  <br>$\text{IN}[B] = \wedge \text{ out}[pred(b)]$|$\text{IN}[B] = f_b(\text{OUT}[B])$  <br>$\text{OUT}[B] = \wedge \text{ in}[succ(b)]$|
|Initialize|$\text{OUT}[B] = \emptyset$|$\text{IN}[B] = \emptyset$|
##### GPU Support for Multi-Tenant Computing

| **Mechanisms**       | **Stream** | **MPS**        | **MIG**   |
| -------------------- | ---------- | -------------- | --------- |
| **Partition type**   | No         | Logical        | Physical  |
| **Max Partition**    | Unlimited  | 48             | 7         |
| **SM isolation**     | No         | By percentage  | Yes       |
| **Mem BW isolation** | No         | No             | Yes       |
| **Performance QoS**  | No         | partial        | Yes       |
| **Reconfiguration**  | Dynamic    | Process launch | When idle |
