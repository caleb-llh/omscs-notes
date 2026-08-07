##### Amdahl’s Law
$$ \text{Speedup} = \frac{1}{S + \frac{P}{N}} $$
Where:
* **P** = Parallelizable fraction of the code
* **S** = Serial (non-parallelizable) fraction of the code ($S = 1 - P$)
* **N** = Number of processors

##### Occupancy

**Example Scenario:**
- **Hardware Limits:** 256 max threads, 64 KB register file, 32 KB shared memory per SM.
- **Kernel Requirements:** 32 threads/block, 2 KB shared memory/block, 64 registers/thread.

Let's calculate the block limits based on each constraint:
- **Threads:** 256 max threads / 32 threads per block = **8 blocks**
- **Registers:** 64 KB (1024 registers of 64 bytes) -> `(64 * 1024) / (64 * 32) = 32` blocks.
- **Shared Memory:** 32 KB / 2 KB per block = **16 blocks**
The final occupancy is the minimum of all constraints: **8 CUDA blocks per SM**.

##### SIMT stack frame
**SIMT Stack Frame:** A hardware structure used to handle SIMT branch divergence inside a warp. Each frame stores:
1. **Re-convergence PC (RPC):** The target instruction address where divergent branch paths merge back.
2. **Alternate Mask:** A 32-bit mask indicating which thread lanes execute the alternate branch path   
3. **Alternate PC:** The starting address of the alternate branch path code

- Upon hitting a divergent branch, the processor pushes the **alternative PC value** and the **reconvergence point** onto the SIMT stack.
- When the processor computes the next PC and finds that it matches the reconvergence point at the top of the stack, it **pops** the stack.
- This process repeats until all alternative paths are executed and the stack is empty for that branch, allowing all threads to finally reconverge.

##### CPI
`Average CPI = CPI_steady_state + sum(Frequency_event * CPI_event)`

_Example_: 5-stage in-order CPU (`CPI_steady` = 1). Branch mispredict penalty is 3 (2% frequency), Cache miss penalty is 5 (5% frequency).  
`Average CPI = 1 + (0.02 * 3) + (0.05 * 5)`

For multithreading, ideal CPI is scaled by `W_depth`:  
`CPI_MT = (CPI_single / W_depth) + Resource_Contentions`  
Resource contentions include MSHRs, busy ALUs, and DRAM bandwidth limits.

##### roofline model
- **X-Axis**: Arithmetic Intensity (FLOPs per byte accessed).
- **Y-Axis**: Performance (FLOPs/sec).

##### Dataflow Analysis

| Feature                    | Reaching Definitions                                                                  | Live Variables                                                                        |
| -------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Domain                     | Sets of definitions                                                                   | Sets of variables                                                                     |
| Direction                  | forward                                                                               | backward                                                                              |
| Transfer function $f_b(x)$ | $gen_B \cup (x - kill_B)$                                                             | $use_B \cup (x - def_B)$                                                              |
| Boundary Condition         | $\text{OUT}[\text{ENTRY}] = \emptyset$                                                | $\text{IN}[\text{EXIT}] = \emptyset$                                                  |
| Meet Operation ($\wedge$)  | $\cup$                                                                                | $\cup$                                                                                |
| Equations                  | $\text{OUT}[B] = f_b(\text{IN}[B])$  <br>$\text{IN}[B] = \wedge \text{ out}[pred(b)]$ | $\text{IN}[B] = f_b(\text{OUT}[B])$  <br>$\text{OUT}[B] = \wedge \text{ in}[succ(b)]$ |
| Initialize                 | $\text{OUT}[B] = \emptyset$                                                           | $\text{IN}[B] = \emptyset$                                                            |
##### GPU Support for Multi-Tenant Computing

| **Mechanisms**       | **Stream** | **MPS**        | **MIG**   |     |
| -------------------- | ---------- | -------------- | --------- | --- |
| **Partition type**   | No         | Logical        | Physical  |     |
| **Max Partition**    | Unlimited  | 48             | 7         |     |
| **SM isolation**     | No         | By percentage  | Yes       |     |
| **Mem BW isolation** | No         | No             | Yes       |     |
| **Performance QoS**  | No         | partial        | Yes       |     |
| **Reconfiguration**  | Dynamic    | Process launch | When idle |     |
