# prompts, notes, breadcrumbs for HPCA
> while we can't do anything about latency (memory wall), we can increase the throughput. modern computer architecture does this by turning a sequential control flow into parallel out-of-order execution by isolating and coordinating structural, control, true and false data dependencies, such that other instructions can be independently executed in parallel. modern architecture also optimises for locality (cache hierarchy) to reduce the latency of memory accesses. these two principles (parallelism and locality) are the foundation of modern computer architecture.
> HPC hold similar concepts at a larger scale, also focusing on optimising for power efficiency, as well as network topology to minimise communication latency.


### philosophical
- Paradigm shift from software to hardware logic (sequential, abstract logic to parallel, physical, and state-based logic) What are the mechanisms to bridge the two paradigms? Can every software logic be implemented as hardware logic?
- Is the CPU a state machine? How does it go from continuous, asynchronous, analog to discrete, synchronous and digital? Why must it be digital and synchronous?
- what exactly makes a computer a deterministic state machine? what makes it a turing machine?
- analog, ternary, probabilistic computing? neuromorphic, quantum, biological computing - how do these paradigms differ from traditional von neumann architecture? adcdfcv re they turing machines? fpgas, asics, gpus - how do these architectures differ? what are the tradeoffs?


### hardware paradigm
- transistors -> logic gates -> combinational circuits -> sequential circuits -> registers -> datapath -> control unit -> cpu -> computer. how do these abstractions build on each other? what are the design principles at each layer that enable the next layer of abstraction?
- what actually happens inside transistors and registers during a clock cycle? edge-triggered vs level-triggered? flipflop vs latch? combinational (stateless) vs sequential (stateful) circuits? what resolves analog physical properties into deterministic digital state transitions? how do resistors, capacitors, and inductors that manage signal timing, filter noise, and stabilize the electrical environment so the logic gates can do their job? does the clock signal actually prevent race conditions if the signal propagation delay is longer than a clock cycle? how are metastability and bit flips eliminated? 
- do all cores in a multi-core processor share the same clock signal? how do they synchronize if they don't? how do they maintain cache coherence and memory consistency if they don't?
- what do "in flight" instructions look like at the hardware level? what actually happens when an instruction cannot complete in a single cycle, in terms of the transistor and registers state? what happens to these state if the machine shuts off abruptly - how do we recreate it if nothing is persisted? how does hardware know an instruction is "done"?
- what does hardware interrupts look like at this level? how are complex tasks like broadcast, scheduling, implemented as hardware logic that happens in a clock tick? How does memory access and device io look like at the hardware level? 
- How do computers with different CPU clock cycles synchronize on time? why not just increase clock speed so that all tasks are never CPU-bound? What are the trade-offs between using a high clock speed vs multiple cores for improving performance?
- why does hardware use little-endian and network use big-endian?
- combinatorial logic: how does compare and assign done in a single cycle (e.g. misprediction flush, load/store forwarding)?
- timing violations, setup and hold time, clock skew, clock jitter, metastability - how do these phenomena arise from the physical properties of the hardware? how are they mitigated?
- are combinatorial logic always level-sensitive and sequential logic always edge-triggered - is there something to be done at every level and edge of a clock cycle?

> In computer architecture, addressing is almost universally done in bytes, not bits. This is known as Byte-Addressability.




### introduction and metrics
- what are real world implications of the memory wall, amdahl's law, power wall, and instruction level parallelism wall? how would software design look like if these constraints didn't exist?
- what happens at the hardware level that results in the distinction between static and dynamic power?
- isa, assembly, microarchitecture, compilers, binary, hypervisors, emulators, simulators, uefi, firmware, bios, os, drivers - how do these layers interact with each other? where do they blur?
- anatomy of a superscalar procesor?

Review:
- Amdahl's law quiz



### pipelining
- anatomy of an instruction? instruction bits vs pipeline register bits? what is the role of pipeline registers?
- why are these stages necessary (fetch, decode, execute, memory, writeback)? what exactly happens at the hardware level during each stage of the pipeline? how does fetching instructions from memory fit into a single stage?
- what is the intuition behind breaking down instructions into smaller stages for pipelining - isn't the total computation work the same?
- issue width vs pipeline depth vs clock speed vs multi-core - what are the tradeoffs between these different ways of improving performance?
- does integer and floating point instructions go through the same pipeline/ done in the same stage, considering they have different execution times?


### branch prediction and predication
- what exactly is being predicted? the instruction address or the instruction result? at which stage of the pipeline does branch prediction happen - how does it happen in the same cycle as the stage?
- in the exponential growth of possible branch outcomes, how does hardware manage to store and lookup predictions efficiently?
- what does "bubble" mean in a pipeline? how is it implemented at the hardware level? how are uncommited state changes reverted? how are speculative state and architectural state maintain their separation?
- how does misprediction flush happen in a single cycle (detect, identify, revert, fetch new instruction)?
- are hardware tables accessed in constant time, without concepts like hashmap, binary or linear search?
- what is the significance of XOR that it is chosen to combine the PC and the history - why is XOR considered a “lossless” operation (entropy mixing)?
- difference in essence between the saturating counter and history predictor?
- difference in structure of p-share, g-share, meta-predictor? how are they updated over time?  is the history string for local history table also using a shift register like GHT? when does it get updated? In theory, can Gshare do whatever Pshare can do?
- what information are stored in register file, pipeline registers, L1, L2, L3 cache and mempry stack/heap during runtime? what are the other state stores local to a processor?
- in predication, how does cmov help if it is conditional as well, i.e evaluated only after the execute stage? cmov trades a control hazard for a data hazard - how does that help? what does cmov look like across all the different stages? Atomic MOVZ vs “compare and swap”
- If the "if-condition" (the predicate calculation) takes a long time, how is full predication better than normal predication (MOVx) or branch prediction? what is the intution for why moving to full predication is faster?

> **Prediction** waste depends on number of **stages**, **predication** waste depends on number of **instructions** after the branch

> **The Rule of Thumb:** 
    - If the branch is **predictable** (like a loop): Use **Branch Prediction**.
    - If the branch is **unpredictable** and the paths are **short**: Use **Predication (CMOV)**.


### ILP 
- how does RAT look like?
- are shared data structures like RAT locked to prevent concurrency race conditions? how does hardware handle concurrent access to these structures by multiple instructions in flight?
- is register renaming/ updating the free list (RAT lifecycle) done outside the pipeline since it is not part of the instruction? how does it fit into the pipeline stages? how does it interact with the register file and the reorder buffer? 
- if instructions are executed out of order, how does an instruction know which renamed register value to use if there are multiple instructions that renamed it due to a WaW hazard? how is instruction order tracked in-flight?


> Here is a list of things that can prevent a CPU from moving forward with an instruction.
    > - Issue:
        - Instructions must be issued in order.
        - Only a certain number of instructions can be issued in one cycle.
        - An RS entry of the right type must be available.
        - An ROB entry must be available.  
    > - Dispatch:
        - The RS must have actual values for each operand.
        - An ALU or processing unit must be available.
        - Only a certain number of instructions from each RS can be dispatched in one cycle.
    > - Execution:
        - No limitations.
    > - Broadcast:
        - Only a certain number of instructions may broadcast in the same cycle.
    > - Commit:
        - Instructions must be committed in order.
        - Only a certain number of instructions can be committed in one cycle.



### instruction scheduling (tomasulo)
- Is RaW dependencies the main motivation for OoO execution?
- how are dependencies/hazards detected in a single cycle? at which stage of the pipeline does this happen? how does it interact with the reservation stations and register renaming?

- tomasulo algorihtm vs what we use today? how does branch prediction and predication look like in tomasulo’s algorithm? how does RAS look like in tomasulo’s algorithm? how does register renaming and the RAT look like in tomasulo’s algorithm? how does the ROB look like in tomasulo’s algorithm? how does memory ordering look like in tomasulo’s algorithm?
- how does tomasulo's algorithm handle WaW (broadcast instead of writing to pass values) and WaR (read during issue) hazards?
- map the classic fetch decode execute memory write stages and the pipeline registers to their corresponding replacement in the tomasulo’s algorithm.
- in tomasulo’s algorithm, how does the broadcast-listening mechanism scale if all the reservation stations share the same processor instead of running concurrently? can the maximum ILP exceed the number of reservation stations?  while an instruction is waiting in RS, does it just sit there hogging up space or is there some sort of "context switching" mechanims? how does simultaneous multithreading relate to instruction scheduling?
- what are the invariants in each step of tomasulo's algorithm? 



> RAT (tomasulo): RAT point an architectural register to the name of a reservation station instead of a physical register (implicitly mapped if empty)
    > - Issue/renaming: operands are resolved during issue using the RAT. if RAT entry it is empty, refer to register file. if RAT contains reservation station tag, operand is resolved to that tag, to indicate that it is pending the result of the instruction in that reservation station. After issue, the RAT entry for the destination register is updated to point to the reservation station tag. This is so that if subsequent instructions require the value of that register, they can check the RAT to see if it is pending and which reservation station it is waiting for, and mark the reservation station tag in their own operand to listen for the result on the common data bus. 
    > - Broadcast: When the instruction in the reservation station completes, it broadcasts its result and tag on the common data bus, which updates the RAT and any reservation stations that are listening for that tag. The RAT is a "real-time lookup table" - the entry in RAT can be overwritten because its previous value should have already been used by previous instructions written into the reservation station. This is why instructions have to be issued in order. 
    > - Write: The index of the RAT entry with the reservation tag tells us which register to write to when the instruction completes. 


> Tomasulo’s algorithm relies on having **comparators** everywhere. Every single Reservation Station slot has a circuit that compares the "Tag on the Bus" with the "Tag I'm waiting for." If you have 32 Reservation Stations and a 4-issue processor (4 buses), that’s 32 x 4 = 128 comparisons happening **every single clock cycle.** This is why OoO chips are so power-hungry compared to simple in-order ones.

> The entire execution context (or "Thread State") typically encompasses:
    1. **PC:** The address of the next instruction.
    2. **Architectural Registers:** The values the programmer thinks are in R0–R31.
    3. **Control/Status Registers:** Flags like "Zero," "Negative," or "Overflow."
    4. **Page Table Base Register:** Used by the MMU to translate virtual memory to physical RAM.
    The **Reservation Stations** and **ALUs** are "ephemeral"/ stateless.


### ROB and memory ordering
- what are the key differences to tomasulo's algorithm with the introduction of the ROB? what are the new invariants introduced by the ROB? what are the speculaitve state and architectural state in the algorithm? What is the key essence of the ROB, RAT and reservation stations that enables OoO execution while maintaining precise exceptions and in-order commit? why these 3 data structures, not more or less? how do they interact with each other? 
- do multi-issue pipelines converge at the ROB stage and is this a bottleneck? 
- The ROB commit stage seems to be another independent execution "process" that runs concurrently with the issue, dispatch, execute and broadcast processes. are they done asynchronously with their own clock cycle, or are they interleaved with the other stages in the same cycle? 
- how do the load-store queue, reorder buﬀer, and reservation stations (RS) play together in our out-of-order processor? Are ROB and RAT the key enabler for out of order processing?


### compiler ILP and VLIW
- in theory, can all register renaming be done on the compiler side to remove WaW and WaR hazards? why do we need hardware register renaming?
- what kind of statistics and profiling does the compiler need to do to be able to schedule instructions effectively? how does it get this information? 




---
### caches
- How is the cache address mapped to memory address if the memory address space is significantly larger?
- does the CPU write-through the cache or write-back to the cache? is it part of the instruction or is it done asynchronously? how does it interact with the ROB and LSQ?

### virtual memory
- how do registers, cache, memory, SSDs, HDDs differ physically and logically? what are the patterns as we move down the hierarchy? what does a read or write miss look like under the hood across these layers?
- how do the cache/memory/storage controllers communicate/interact with each other? do they operate asynchronously with their own clock cycles? how do they maintain consistency and coherency across the hierarchy?


---



# Cheatsheet
- 1 word = 32 bits = 4 bytes 
- 1 instruction = 32 bits = 4 bytes 
- if 1 address = 64 bits: usually expressed as 8 hex digits in (byte-addressing) e.g 0x0000ab0c, where the last 2 bits are always 00 because instructions are word-aligned.
- if 1 address = 32 bits: usually expressed as 4 hex digits in (byte-addressing) e.g 0xab0c, where the last 2 bits are always 00 because instructions are word-aligned.

### data structures
**Branch prediction**
- Branch Target Buffer (BTB): maps PC (LSB -2 because instructions are word-aligned) to target address (next PC). A common example is a 1024-entry (2^10) table using 10 bits of the PC as an index, and storing the target address in each entry.

- Direction predictors
    - Local History Table (LHT): maps PC (LSB -2 because instructions are word-aligned) to 2-bit saturating counter (00, 01, 10, 11). For each entry (indexed by PC), costs N bits for the history, another 2^N counters (indexed by history) , where each counter costs 2 bits. i.e. N + 2*2^N bits per entry

    - Shared History Counters - split history and counters.
        - Pshare:
            - Pattern History Table (PHT in Pshare): maps LSB-2 of PC (e.g. L=10) to history string (e.g. N=8 bits) using a shift register. For each entry (2^L entries), costs N bits for the history.
            - Branch History Table (BHR in Pshare): a 2 bit counter, indexed by XOR of PC and PHT entry indexed by PC. Size is 2^N entries with 2 bits each entry.
            - Updating the predictor: after the branch is resolved, the history string in PHT is updated by shifting in the actual outcome (taken/not taken) of the branch, and the counter in BHR is updated based on whether the prediction was correct or not.
        - Gshare:
            - Global History Register (GHR in Gshare): a shift register that stores the history string (e.g. N=8 bits) of the most recent branches.
            - Branch History Table (BHR in Gshare): a 2 bit counter, indexed by XOR of PC (LSB -2) and GHR. Size is 2^N entries with 2 bits each entry.

    - Meta-predictor table: 2BC that chooses between the local and global predictor, indexed by PC (LSB -2). Size is 2^L entries with 2 bits each entry.

- Return Address Stack (RAS): LIFO stack

**Register renaming**
- Register Alias Table (RAT): maps architectural register (Rx) to physical register (Py).

**Instruction scheduling**
- RAT (tomasulo): maps Rx to reservation station tag or empty (indicating the value is in the register file). 

- RAT (tomasulo + ROB): maps Rx to ROB entry or empty (indicating the value is in the register file). The ROB entry contains the destination register and the value (once ready).

- Reservation Station (RS): instruction type, operand values or tags, busy bit.

- Reorder Buffer (ROB): a circular buffer with columns for destination register, value, ready bit. two circular pointers for commit and issue.

- Load-Store Queue (LSQ): ­A bit for indicating a load or store, ­The address of the load or store, ­The data value to be stored in memory, ­A bit indicating completion. Only load and store instructions are placed in the LSQ, and they are issued in order. The LSQ is checked for memory dependencies before issuing a load or store instruction.

### algorithms
**Branch Prediction:**
1. Fetch Stage (The Guess)
    - This is where the hardware makes its prediction using only the current Program Counter (PC).
    - Target Lookup (BTB): The PC indexes into the Branch Target Buffer (ignoring the last 2 bits due to 4-byte word alignment) to retrieve a cached target address.
    - Direction Prediction (BHT/PHT): The PC indexes into the Branch History Table or Pattern History Table to retrieve a 1-bit or 2-bit counter (2BC) that predicts "Taken" or "Not-Taken".
    - History Selection (PShare/GShare):
        - GShare: The Global History Register (GHR) is XORed with the PC to find a specific pattern in the PHT for correlated branches.
        - PShare: A Local History Table (LHT) provides a branch’s private history to index the PHT for self-similar patterns.
    - Predictor Selection (Tournament): The PC indexes a Meta-Predictor table (using 2BCs) to decide whether to believe the GShare or PShare result.
    - Function Returns (RAS): If the instruction is pre-decoded or predicted as a return (ret), the Return Address Stack pops the top address to use as the next PC.
2. Decode Stage (The Confirmation)
    - Instruction ID: The hardware confirms if the fetched instruction is actually a branch.
    - Pre-decoding: The processor may use bits stored in the instruction cache during pre-decoding to identify ret instructions earlier.
3. Execute Stage (The Resolution)
    - Evaluation: The ALU calculates the real branch outcome and the real target address.
    - Comparison: The calculated result is compared against the guess made in the Fetch stage.
4. Update & Recovery Stage
    - This happens immediately after execution or at Commit in out-of-order systems.
    - Table Updates: The BHT, PHT, GHR, and LHT are updated with the actual outcome to "train" the predictors for future encounters.
    - Meta-Predictor Update: The meta-predictor is updated to favor whichever predictor (PShare or GShare) was correct.
    - The Flush: If a misprediction occurred, the pipeline is flushed (clearing all incorrectly fetched instructions), the Reorder Buffer (ROB) resets its pointers, and the Register Allocation Table (RAT) is restored.
    - Redirection: The Fetch stage is restarted at the correct address.


### formulas
- Iron Law of Processor Performance: Execution Time = (Instructions / Program) x (Cycles / Instruction) x (Seconds / Cycle)
- Speedup = (Execution Time of Old) / (Execution Time of New) = (Cycles of Old) / (Cycles of New) = (IPC of New) / (IPC of Old) = (ILP of New) / (ILP of Old)
- Amdahl's Law = 1 / ((1 - P) + (P / S)), where P is the proportion of the program that can be improved and S is the speedup of the improved portion.
- Pipeline Execution Time = (Number of Instructions + Pipeline Depth - 1) * (Clock Cycle Time)
- Overall CPI = Base CPI + (Misprediction Rate % x Misprediction Penalty) = (Base CPI) + (Mispredictions / Instructions) x (Cycles Wasted per Misprediction) = (Base CPI) + (Mispredictions / Branches) x (Branches / Instructions) x (Cycles Wasted per Misprediction)
- Base CPI = 1 (for a perfectly pipelined single-issue processor with no hazards or stalls)
- An N­bit History Predictor will predict all patterns of length <= N+1
- An N­bit History Predictor will cost N+2*2^N per entry, with most of the counters wasted.
- CPI (the lower, the better) = Cycles / Instructions
- IPC (the higher, the better) = Instructions / Cycles
- ILP (like "ideal IPC" - the higher, the better) = Number of instructions / Number of cycles



