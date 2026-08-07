# Module 1: Instruction-Level Parallelism (ILP) - Part 2

## 1. Introduction to Instruction-Level Parallelism (ILP)
**Background Context**: In previous discussions on pipelining, we saw how branch prediction and if-conversion help us eliminate most of the pipeline problems caused by control hazards. However, **data hazards (dependencies)** can still prevent us from finishing one instruction every single cycle.

This leads us to ask: *What can we do about data dependencies? And why stop at only one instruction per cycle?*

**Instruction-Level Parallelism (ILP)** tells us the theoretical maximum number of instructions that could possibly execute in any given cycle, bounded only by the intrinsic data dependencies within the program itself.

---

## 2. The Ideal Execution Scenario (And Why It Fails)
**Mental Model: The "Infinite" Pipeline**
Imagine an ideal processor that is infinitely wide. What if all the instructions we need to execute could just go through the pipeline in the exact same stage at the exact same time?
If we could execute a massive number of instructions in just 5 cycles (for a 5-stage pipeline), our Cycles Per Instruction (CPI) would approach 0. 

**The Catch: No Time Travel**
Let's look at an example:
1. `ADD R1, R2, R3`  *(Writes to R1)*
2. `SUB R4, R1, R5`  *(Reads from R1)*

If both instructions are decoded and read their registers in the exact same cycle, the `SUB` instruction will read the *old* value of `R1`—the value that existed before the `ADD` instruction wrote to it. 

*But what about data forwarding?*
Forwarding can take a result produced at the end of the Execute stage and feed it into the *next* cycle's Execute stage. However, it cannot feed the result into the *same* cycle. Doing so would require producing a result and sending it backward in time (e.g., 1 nanosecond into the past). Since time travel is impossible, we cannot execute these two dependent instructions simultaneously.

**The Reality**
Dependent instructions must be delayed (stalled). The `SUB` must wait for the `ADD` to produce its result. Because of these necessary stalls, CPI will always be greater than 0, even on a theoretical infinite-width processor.

---

## 3. Types of Data Dependencies

To understand how to maximize ILP, we must categorize dependencies into two distinct groups: True Dependencies and False (Name) Dependencies.

### A. True Dependencies: RAW (Read-After-Write)
- **Definition**: An instruction needs a value that is produced by an earlier instruction.
- **Nature**: Fundamental to the program's logic. You cannot compute a result without its inputs.
- **Impact**: Forces serialization. If you have a chain of 5 instructions where each depends on the previous one, it will take exactly 5 cycles to execute them, giving a CPI of 1.

### B. False Dependencies (Name Dependencies)
These occur not because data actually flows between the instructions, but simply because the instructions happen to use the *same register name*.

1. **WAW (Write-After-Write) / Output Dependence**
   - **Scenario**: Two instructions write to the same register (e.g., R4).
   - **The Problem**: If the second instruction executes faster than the first (due to the first instruction being stalled by an earlier dependency), the second instruction might write its result to R4 *before* the first instruction writes to R4. 
   - **Result**: The final value left in R4 will be the older value (from the first instruction), which breaks the program's logic for any subsequent instructions reading R4.

2. **WAR (Write-After-Read) / Anti-Dependence**
   - **Scenario**: A later instruction writes to a register that an earlier instruction needs to read.
   - **The Problem**: If the later instruction executes early, it might overwrite the register before the earlier instruction has had a chance to read it.

---

## 4. Resolving False Dependencies
Since False Dependencies are an artifact of limited register names rather than actual data flow, we can eliminate them to extract more parallel performance.

### Attempt 1: Duplicating Register Values (The Hard Way)
- **Concept**: Instead of storing just one value for R4, the hardware stores a complete history of every value R4 has ever held.
- **Execution**: When an instruction reads R4, it must search through the history to find the specific version of R4 that was produced immediately prior to it.
- **Verdict**: Extremely complicated and inefficient to build in hardware.

### Attempt 2: Register Renaming (The Elegant Solution)
Register Renaming is the industry-standard technique used in modern superscalar processors to eliminate WAW and WAR dependencies on the fly.

**Intuition**: Think of **Architectural Registers** (like R1, R2) as pointers or variable names in a high-level language, and **Physical Registers** (like P1, P2) as the actual memory addresses where data lives. 

- **Architectural Registers (AR)**: The small set of registers visible to the programmer and compiler (e.g., 32 registers in MIPS/ARM).
- **Physical Registers (PR)**: A much larger set of hidden registers built into the CPU hardware.
- **Register Allocation Table (RAT)**: A dynamic mapping table that tracks which Physical Register currently holds the value for each Architectural Register.

#### How Register Renaming Works (Step-by-Step)
When the processor fetches an instruction, it consults and updates the RAT:
1. **Reads**: For every architectural register the instruction needs to read, look up its current mapping in the RAT and rewrite the instruction to use that physical register.
2. **Writes**: For every architectural register the instruction writes to, **allocate a brand new, unused physical register**. Update the RAT so that future instructions reading this architectural register will be pointed to this new physical register.

**Example Walkthrough**:
*Initial RAT State: R1->P1, R2->P2, R3->P3*

1. `ADD R1, R2, R3`
   - **Reads**: R2 (P2), R3 (P3)
   - **Writes**: R1. Allocate a new PR (e.g., P7). Update RAT: R1->P7.
   - **Renamed Instruction**: `ADD P7, P2, P3`

2. `SUB R4, R1, R5`
   - **Reads**: R1 (now P7!), R5 (P5)
   - **Writes**: R4. Allocate a new PR (e.g., P8). Update RAT: R4->P8.
   - **Renamed Instruction**: `SUB P8, P7, P5`

**Why this is magical**: 
Because every single write operation allocates a *new* physical register, no instruction ever overwrites a physical register that an older instruction is still trying to read. WAW and WAR dependencies instantly vanish! Only the true RAW data dependencies remain.

---

## 5. Defining and Calculating ILP

Now that we understand renaming and true dependencies, we can formally define ILP.

**Definition**: ILP is the Instructions Per Cycle (IPC) that a program would achieve if executed on an **ideal processor**.

**Characteristics of the "Ideal Processor"**:
- It can fetch, decode, execute, and write back in exactly 1 cycle.
- It can process an infinite number of instructions simultaneously.
- It is constrained **only** by true (RAW) data dependencies. (No time travel!)

**Crucial Mental Model**: 
ILP is a fundamental property of the **program itself**, NOT the processor. It makes no sense to ask "What is the ILP on an Intel Core i7?" because ILP measures the theoretical limit of the code's dependencies, independent of hardware constraints like pipeline width or cache misses.

### How to Calculate the ILP of a Program
1. **Rename the Registers**: Perform Register Renaming on the entire sequence of instructions to eliminate all WAW and WAR dependencies.
2. **Schedule by Data Flow**: Look at the true dependencies (RAW). 
   - **Cycle 1**: Group all instructions that do not depend on any other instructions in the sequence. These all execute in Cycle 1.
   - **Cycle 2**: Group instructions that only depend on the outputs of Cycle 1 instructions.
   - **Cycle N**: Continue this process until all instructions are scheduled.
3. **Calculate IPC**: Divide the total number of instructions by the total number of cycles it took to schedule them. 

*Example*: If a renamed 6-instruction program can be scheduled such that 3 instructions execute in Cycle 1, and 3 instructions execute in Cycle 2, the ILP is `6 instructions / 2 cycles = 3 IPC`.
