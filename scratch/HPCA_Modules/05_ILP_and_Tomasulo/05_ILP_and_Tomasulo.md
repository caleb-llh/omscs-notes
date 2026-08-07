# 05_ILP_and_Tomasulo (Synthesized Notes)

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


---

# Module 2: Instruction-Level Parallelism (ILP) & Tomasulo's Algorithm

## 1. Computing ILP
**Instruction-Level Parallelism (ILP)** represents the maximum potential parallelism in a program. It is defined as the Instructions Per Cycle (IPC) on an **ideal processor**.

### The "Ideal Processor" Mental Model
To calculate ILP, we assume a processor with:
- **Infinite resources:** No structural dependencies (e.g., infinite adders and multipliers).
- **Perfect branch prediction:** Control dependencies do not cause any delays.
- **Perfect register renaming:** False dependencies (WAR and WAW) are completely eliminated.
- **Out-of-order execution:** Instructions execute the moment their data is ready.

Because of these assumptions, the *only* thing that restricts ILP is **True Data Dependencies (RAW - Read After Write)**. 

### Trick for Computing ILP on Paper
You do not need to manually rename the program's registers or draw complex hardware diagrams to compute ILP. 
1. Identify only the **true (RAW) dependencies**. Completely ignore anti (WAR) and output (WAW) dependencies, as renaming handles them instantly.
2. Group instructions into execution cycles based on when their inputs are ready.
3. $\text{ILP} = \frac{\text{Total Instructions}}{\text{Total Cycles}}$

> **Example**
> If a program has 5 instructions, and due to true dependencies, they can be grouped into 2 cycles (e.g., 3 instructions in cycle 1, 2 in cycle 2), the ILP is $5 / 2 = 2.5$.

---

## 2. ILP with Control Dependencies
How do branches (control dependencies) affect ILP? **They don't.**

Because our ideal processor has *perfect same-cycle branch prediction*, it "knows" exactly which path the branch will take the moment the program is fetched. 
- The processor sees all the correct instructions after the branch immediately.
- A branch acts like a dummy instruction that produces no result. 
- Independent instructions *after* a branch can actually execute *before* or *in the same cycle* as the branch itself!

---

## 3. ILP vs. IPC
While ILP is a property of the **program**, IPC (Instructions Per Cycle) is a property of the program running on a **specific, real processor**.

### Real Processor Limitations
A real processor cannot achieve ideal ILP because of:
1. **Issue Width:** It might only be able to fetch/issue 1 or 2 instructions per cycle.
2. **Structural Hazards:** It has a limited number of ALUs (e.g., only 1 multiplier).
3. **In-Order Execution:** If an older instruction stalls, all subsequent instructions are blocked, even if they are independent.

**Golden Rule:** $\text{IPC} \le \text{ILP}$
- ILP is the absolute upper bound. 
- A real processor tries to achieve an IPC as close to the ILP as possible, but will often fall short due to the limitations above.

### The Issue Width vs. In-Order Bottleneck
- **Narrow-Issue, In-Order Processor:** Performance is primarily bottlenecked by the narrow issue width (e.g., can only issue 1 instruction per cycle). The in-order penalty doesn't hurt as much because the pipeline is thin anyway.
- **Wide-Issue, In-Order Processor:** Performance is severely bottlenecked by the *in-order* property. Even if it can issue 4 instructions per cycle, a single data dependency stops the entire wide pipeline, leaving execution slots empty. 
- **Takeaway:** If you build a wide-issue processor, it *must* be out-of-order to actually find enough independent instructions to keep those wide execution slots busy.

---

## 4. Improving IPC
To bring a processor's IPC closer to the program's ILP, hardware designers use specific techniques to remove bottlenecks:

| Limitation | Hardware Solution |
| :--- | :--- |
| **Control Dependencies** | **Branch Prediction** (Guess the branch outcome to avoid stalling) |
| **False Dependencies (WAR/WAW)** | **Register Renaming** (Give each written value a unique physical location) |
| **True Dependencies (RAW)** | **Out-of-Order (OoO) Execution** (Execute instructions as soon as inputs are ready) |
| **Structural Dependencies** | **Wider Issue & More Execution Units** (Build a processor that can handle more simultaneous operations) |

---

## 5. Introduction to Tomasulo's Algorithm
Tomasulo's Algorithm is a legendary hardware algorithm developed by Robert Tomasulo for the IBM 360/91 over 40 years ago. It dynamically implements **Register Renaming** and **Out-of-Order Execution** in hardware.

### Tomasulo Then vs. Now
While the core principles remain the same, modern implementations have evolved:
- **Scope:** Originally only for floating-point instructions; today it's used for all instructions.
- **Instruction Window:** Originally looked at a handful of instructions; today processors look at hundreds.
- **Exceptions:** Originally didn't have robust precise exception handling; today, processors use Reorder Buffers (ROB) to handle exceptions cleanly.

---

## 6. The Hardware Picture
To understand Tomasulo's, visualize the following hardware components:

1. **Instruction Queue (IQ):** Holds fetched instructions in program order.
2. **Reservation Stations (RS):** Buffers sitting in front of execution units (ALUs, Multipliers). Instructions wait here until their data operands are ready.
3. **Register File:** Holds the actual committed values of registers.
4. **Register Alias Table (RAT):** A mapping table that tracks which Reservation Station is currently computing the value for a specific architectural register.
5. **Common Data Bus (CDB):** A broadcast bus. When an execution unit finishes, it shouts its result (Value + RS ID) across this bus to all waiting Reservation Stations and the Register File.

### The Three Stages of Execution
1. **Issue:** Move an instruction from the IQ to a Reservation Station. (Done strictly *in-order*).
2. **Dispatch:** Send an instruction from the RS to the Execution Unit. (Done *out-of-order*, whenever operands are ready).
3. **Write Result (Broadcast):** The execution unit finishes and broadcasts the result on the CDB.

---

## 7. Deep Dive: The Issue Stage
The Issue stage is critical because it performs **Register Renaming** and sets up the dependency chain. **It must process instructions in program order.**

**Step-by-Step Process for Issuing an Instruction:**
1. **Fetch:** Take the next instruction from the Instruction Queue.
2. **Check Resources:** Find an available Reservation Station (RS) for the instruction's operation type. *If none are available, the processor stalls (structural hazard).*
3. **Read Operands (The "Listen" Phase):**
   - For each input register, check the RAT.
   - If the RAT is empty for that register, the value is ready! Read it directly from the Register File.
   - If the RAT points to an RS (e.g., "RS1"), the value is not ready. Record the RS tag in the new Reservation Station so it knows to listen on the CDB for "RS1".
4. **Rename Destination (The "Claim" Phase):**
   - Update the RAT entry for the destination register to point to the newly allocated RS. 
   - *Intuition:* You are telling all future instructions, "If you want this register, don't look in the Register File. Wait for me (this RS) to finish!"

### Issue Example
Imagine we are issuing `DIV F1, F2, F3` into Reservation Station 4 (RS4):
- **Inputs:** It needs F2 and F3. 
  - F3's RAT entry is empty, so it grabs the actual value (e.g., 2.72) from the Register File.
  - F2's RAT entry says "RS1". So RS4 records: "Wait for RS1 to broadcast."
- **Output:** It writes to F1.
  - The RAT entry for F1 is updated to point to "RS4". Any older pointer for F1 is overwritten. This completely eliminates WAW hazards!

### Important Caveat on Memory Operations
In the original Tomasulo's algorithm, Loads and Stores were executed strictly in order via Load/Store Queues to prevent memory hazards. Modern processors employ much more complex memory disambiguation to reorder memory operations as well.


---

# High-Performance Computer Architecture: Tomasulo's Algorithm (Module 3)

## Introduction and Background Context
In modern out-of-order processors, Tomasulo's Algorithm is a dynamic scheduling hardware approach that allows instructions to execute as soon as their operands are ready, bypassing the original program order. This module delves into the intricacies of the algorithm, covering edge cases in Issue, Dispatch, and Write Result (Broadcast) stages, as well as handling structural hazards and same-cycle operations.

---

## 1. Issue Stage Mechanics
**Mental Model:** Think of the Issue stage as the "front desk" of the processor. It takes instructions in program order, checks if there is an available Reservation Station (RS), and allocates it.

- **Operation:** 
  - When an instruction issues, it requires an available RS corresponding to its execution unit (e.g., Adder or Multiplier).
  - It reads operands. If the operands are ready, they are copied from the Register File. If they are pending, it records the RS tag of the instruction that will produce them.
  - The Register Alias Table (RAT) is updated to point the destination register to this new RS.
- **Stalls:** 
  - If all Reservation Stations for the required execution unit are full (e.g., all divide/multiply RS are busy), the instruction *cannot issue*. 
  - Because instructions issue in-order, this stalls the entire issue pipeline until a station becomes free.

---

## 2. Dispatch Stage Mechanics
**Mental Model:** The Dispatch stage is the "waiting room to execution." Instructions wait here until they hear their required data announced (broadcast). Once they have everything, they compete to enter the execution room.

- **Two Main Tasks per Cycle:**
  1. **Capture/Latch Results:** Listen to the Common Data Bus (CDB). If a broadcasted tag matches an awaited operand, capture the value.
  2. **Select for Execution:** Identify all RS that have all operands ready, and dispatch them to their respective execution units.
- **Timing Constraint:** Often, these two tasks happen sequentially within a single cycle (e.g., capture at the beginning, dispatch towards the end). 

### What happens when multiple instructions are ready?
If two or more instructions are ready for a single execution unit, a structural hazard occurs. The hardware must choose one using a heuristic:
- **Highest Performance (Ideal but Impossible):** Pick the instruction that unblocks the most future instructions. Hardware lacks perfect future knowledge to do this efficiently.
- **Most Dependencies First:** Check which instruction has the most other RS waiting for it. (Too complex/power-hungry to implement in hardware).
- **Random:** Simple, guarantees correctness (no deadlocks), but yields the worst performance.
- **Oldest First (The Pragmatic Compromise):** Pick the instruction that has been waiting in the RS the longest. 
  - *Intuition:* An older instruction has likely had more subsequent instructions depend on it. This heuristic is simple to track and provides near-optimal performance.

### Dispatch Quiz Insights
Why might a seemingly ready instruction not dispatch immediately?
1. **Issued in the previous cycle:** The processor might not support same-cycle issue-and-dispatch (see "Same-Cycle Operations").
2. **Execution Unit Conflict:** Another ready instruction won the priority heuristic (e.g., it was older) and took the execution unit.
3. *Note on Out-of-Order Execution:* Dispatching is *not* bound by program order. A younger instruction can absolutely dispatch before an older one if its operands are ready and the older one's are not.

---

## 3. Write Result (Broadcast) Stage
**Mental Model:** The "loudspeaker." When an execution unit finishes, it shouts its tag and result to the entire processor.

- **Sequence of Actions:**
  1. Put the tag (e.g., RS1) and the computed result on the broadcast bus.
  2. **Reservation Stations:** Every RS snoops the bus. If it's waiting for RS1, it captures the result.
  3. **RAT & Register File:** Check the RAT. If the RAT entry for the destination register still points to RS1, update the Register File with the new value and clear the RAT entry (marking it valid/empty).
  4. **Free the RS:** The RS that broadcasted the result is marked as empty and can accept a new instruction.

### Multiple Broadcasts in One Cycle
What if an Adder and a Multiplier finish in the same cycle, but there is only one broadcast bus?
- **Hardware Solutions:**
  - **Multiple Buses:** Adds significant complexity (doubles comparators in all RS, doubles write ports in the Register File).
  - **Priority System (Single Bus):** Choose one unit to broadcast and make the other wait.
- **Broadcast Priority Heuristic:** 
  - Give priority to the **slower execution unit** (e.g., Divide/Multiply over Add/Subtract).
  - *Intuition:* An instruction in a slow unit has been executing for a long time. It behaves like an "older" instruction, meaning more pending instructions are likely bottlenecked waiting for its result.

### Broadcasting a "Stale" Result
What happens if an instruction broadcasts, but the RAT no longer points to its RS?
- **Background:** This occurs if a younger instruction has already issued and overwritten the same destination register in the RAT.
- **Action:** 
  - The RS broadcast *still happens* so that any intermediate instructions waiting for this specific result can capture it.
  - However, the **Register File and RAT are NOT updated**. 
  - *Why?* The newer instruction is legally the latest writer to that architectural register. Updating the Register File with the stale result would corrupt the architectural state for future instructions.

---

## 4. Same-Cycle Operations & Timing Nuances
Tomasulo's Algorithm performs many parallel tasks every cycle. Different instructions can be in Issue, Capture, Dispatch, Execute, and Broadcast simultaneously. But can a *single* instruction traverse multiple stages in one cycle?

1. **Same-Cycle Issue and Dispatch?** 
   - **Typically NO.** When issuing, the processor writes to the RS. The dispatch logic usually reads from the RS to determine readiness. Doing both sequentially in one cycle requires a significantly longer clock cycle or complex bypass logic.
2. **Same-Cycle Capture and Dispatch?**
   - **Typically NO.** For the same reason. An instruction capturing its final operand usually transitions its RS to "ready," making it eligible for dispatch in the *next* cycle.
3. **Same-Cycle Issue and Write Result (to the same RAT entry)?**
   - **YES.** Suppose Instruction A (older) broadcasts its result for `R1`, while Instruction B (younger) issues and writes to `R1`.
   - Both want to update the RAT entry for `R1`.
   - **Resolution:** The *issuing* instruction (B) wins. 
   - *Why?* Instruction B is younger in program order. Future instructions must see B's tag in the RAT, not A's result. (A's broadcast still feeds any waiting RS).

### Edge Case: Capturing While Issuing
If an instruction issues in the exact same cycle that its needed operand is broadcasted on the bus, it **must** capture that value directly off the bus during issue. If it just writes the RS tag into its station, it will miss the broadcast (which is happening right now) and wait forever, causing a deadlock.

---

## Summary of the Pipeline Lifecycle
To synthesize, an instruction's lifecycle in Tomasulo's algorithm looks like this:
1. **Issue:** Decode, allocate RS, read ready operands from Register File, update RAT. (Stalls if RS full).
2. **Wait/Capture:** Snoop the CDB. Latch operands as they are broadcasted.
3. **Dispatch:** Once all operands are captured, arbitrate for the execution unit (using "Oldest First").
4. **Execute:** Perform the actual operation.
5. **Write Result:** Broadcast tag and value on CDB. Update dependent RS. Conditionally update RAT and Register File (if not stale). Free the RS.


---

# High Performance Computer Architecture: Tomasulo's Algorithm & Memory Dependencies

This document synthesizes key concepts regarding instruction dispatch rules, the core properties of Tomasulo's Algorithm, and the handling of memory dependencies (loads and stores). 

---

## 1. Instruction Dispatch Dynamics

### Background Context
In an out-of-order (OoO) processor using Tomasulo's Algorithm, the execution of an instruction is broken down into three distinct stages:
1. **Issue:** The instruction is fetched from the instruction buffer and allocated to a Reservation Station.
2. **Execute (Dispatch):** The instruction waits for its operands. Once all operands are available, it is dispatched to a functional (execution) unit.
3. **Write Result:** The computed result is broadcast over the Common Data Bus (CDB).

### 🧠 Mental Model: The Theme Park Ride
Think of the **Issue** stage as buying a ticket for a roller coaster, and the **Dispatch** stage as actually getting on the ride. In Tomasulo's architecture, the ticket booth and the ride entrance are processed by different systems. You cannot buy a ticket and board the ride in the exact same cycle—there is an inherent delay.

### Key Rules of Dispatch in a Single Cycle
When determining which instructions can dispatch to the ALU in a given cycle, keep the following rules in mind:
* **Already Executing:** If an instruction has already dispatched in a previous cycle and is currently executing, it will not dispatch again.
* **Operand Capture:** If an instruction captures its final missing operand during the *current* cycle (via the CDB), it becomes eligible for dispatch.
* **The "No Same-Cycle Issue & Dispatch" Rule:** An instruction **cannot** be issued and dispatched in the same cycle. Even if an instruction is issued and its operands are immediately ready (e.g., already sitting in the register file), it must wait until at least the *next* cycle to dispatch.
* **Structural Hazards (Contention):** If multiple instructions become eligible for dispatch in the same cycle, but there is only one execution unit available, the processor must use a set of arbitration rules (like "oldest instruction first") to pick the winner. If only one instruction is eligible, no arbitration is needed.

---

## 2. Core Properties of Tomasulo's Algorithm

To truly understand Tomasulo's Algorithm, we must evaluate how it handles ordering at each stage of an instruction's lifecycle. 

### 💡 Intuition
The entire goal of Tomasulo's algorithm is to break free from the strict sequential execution of programs while maintaining the illusion that the program was executed sequentially. It achieves this by strictly controlling how instructions enter the system, but letting them run wildly based on data availability once inside.

* **Does it ISSUE instructions in program order?**
  * **Yes.** Instructions are pulled from the instruction buffer and allocated to reservation stations sequentially. You cannot issue instructions out of order.
* **Does it DISPATCH (execute) instructions in program order?**
  * **No.** This is the defining characteristic of an out-of-order processor. Instructions wait in their reservation stations and dispatch as soon as their data dependencies are resolved, regardless of their original program order.
* **Does it WRITE RESULTS in program order?**
  * **No.** Results are written to the Common Data Bus (CDB) in the order they finish execution. A fast instruction (like an integer add) that was issued late might finish and write its result before a slow instruction (like a floating-point divide) that was issued early.

---

## 3. Handling Memory Dependencies (Loads and Stores)

### Background Context
Earlier, we learned how Tomasulo's Algorithm uses **Register Renaming** (via reservation stations) to eliminate false dependencies (WAR and WAW) between registers, allowing true dependencies (RAW) to dictate execution flow. 

However, instructions can also communicate through **Memory**, meaning dependencies exist there as well. Because memory addresses might not be known until execution time, resolving memory dependencies is significantly more complex than resolving register dependencies.

### Types of Memory Dependencies
Just like registers, memory operations face three types of dependencies:
1. **RAW (Read After Write) - True Dependence:**
   * *Example:* `Store R1 -> [Mem A]`, then `Load [Mem A] -> R2`.
   * The Load must wait for the Store to finish so it can read the newly written, correct value.
2. **WAR (Write After Read) - False Dependence:**
   * *Example:* `Load [Mem A] -> R1`, then `Store R2 -> [Mem A]`.
   * If reordered, the Load might incorrectly grab the new value placed by the Store instead of the old value it was supposed to read.
3. **WAW (Write After Write) - False Dependence:**
   * *Example:* `Store R1 -> [Mem A]`, then `Store R2 -> [Mem A]`.
   * If reordered, the final value left in memory will be the stale value from the first store, rather than the correct value from the second store.

### How are Memory Dependencies Handled?

#### 1. The Original Tomasulo Approach (In-Order Memory)
In the classic Tomasulo algorithm, the complexity of calculating addresses and checking for overlaps dynamically was deemed too high.
* **Solution:** Loads and Stores are simply **not reordered**. 
* They are placed into a Load/Store Queue and execute strictly in program order.
* *Example:* If a Load is ready to execute, but there is an older pending Store in the queue (even if it's going to a completely different address), the Load is blocked and cannot bypass the Store. 

#### 2. The Modern Approach (Memory Disambiguation)
*Modern processors* (which build upon Tomasulo's concepts) do not accept the performance penalty of in-order memory operations. 
* **Solution:** They actively identify memory dependencies by computing addresses as early as possible. 
* If the processor can prove that a pending Store and a ready Load target different memory addresses, it will dynamically reorder them, allowing the Load to execute early. (This advanced technique is covered in later modules).


---

# Module 5: Tomasulo's Algorithm - Comprehensive Examples

## 1. Background & Mental Model

Before diving into the complex cycle-by-cycle examples, it's helpful to establish a strong mental model for **Tomasulo's Algorithm**. Tomasulo's enables **dynamic scheduling** and **out-of-order execution** by resolving Data Hazards (RAW) and eliminating Name Hazards (WAR, WAW) through **register renaming**.

**The Restaurant Kitchen Analogy:**
- **Issue (Taking the Order):** An instruction is fetched in-order. If there is space in the "Reservation Station" (RS) — basically a prep station for a specific type of dish — the order is placed. If the required ingredients (operands) are available, they are copied to the RS. If not, the RS records *who* will produce them (register renaming).
- **Dispatch (Cooking):** Once all ingredients (operands) are ready and the execution unit (the chef) is free, the instruction begins execution. 
- **Broadcast / Write Result (Serving):** When execution finishes, the result is broadcast on the Common Data Bus (CDB). Any waiting RS (prep station) listening for this specific result immediately captures it. The destination register is also updated, and the RS is freed for future use.

**Key Rules to Remember for the Examples:**
1. **In-Order Issue:** Instructions must issue in program order.
2. **Out-of-Order Execution & Completion:** Instructions dispatch and write results as soon as they are ready.
3. **Common Timing Constraints:**
   - Often, an instruction cannot issue and dispatch in the same cycle.
   - Capturing a broadcasted operand and dispatching in the same cycle is usually not allowed (must wait for the next cycle).
   - Freeing an RS happens at the end of a write cycle; the RS is only available for a *new* instruction in the *following* cycle.

---

## 2. Detailed Step-by-Step Example

Let's walk through a detailed, cycle-by-cycle execution of a sequence of instructions. 

### Processor Characteristics
- **Latencies:** 
  - Load: 2 cycles
  - Add / Subtract: 2 cycles
  - Multiply: 10 cycles
  - Divide: 40 cycles (uses the multiply unit)
- **Reservation Stations (RS):**
  - 2 Load RS
  - 3 Add/Sub RS
  - 2 Multiply/Divide RS
- **Initial Register Values:** R2 = 100, R3 = 200, R4 = 300

### Instruction Sequence
1. `LD F6, 34(R2)`  *(Load 1)*
2. `LD F2, 45(R3)`  *(Load 2)*
3. `MUL F0, F2, F4` *(Multiply 1)*
4. `SUB F8, F6, F2` *(Subtract 1)*
5. `DIV F10, F0, F6` *(Divide 1)*
6. `ADD F6, F8, F2` *(Add 1)*

### Cycle-by-Cycle Breakdown

#### Cycles 1-2: Issuing the Loads
- **Cycle 1:** `LD F6, 34(R2)` issues. 
  - It takes an available Load RS (Load 1). 
  - It computes the address (34 + R2 = 134). 
  - Register `F6` is renamed to point to `Load 1`. 
  - *Cannot dispatch in the same cycle.*
- **Cycle 2:** `LD F2, 45(R3)` issues.
  - Takes the second Load RS (Load 2). Address is computed (45 + R3 = 245).
  - Register `F2` is renamed to point to `Load 2`.
  - Meanwhile, **Load 1 dispatches** (begins execution) because its operands are ready. It will execute in Cycles 2 and 3, and write its result in Cycle 4.

#### Cycles 3-4: Multiplies and Subtracts
- **Cycle 3:** `MUL F0, F2, F4` issues.
  - It takes a Multiply RS (Mul 1). 
  - `F4` is available (e.g., 2.5), but `F2` is waiting on `Load 2`.
  - Register `F0` is renamed to point to `Mul 1`.
  - *Structural/Pipelining context:* Assuming the Load unit is NOT fully pipelined, `Load 2` cannot dispatch yet because `Load 1` is still executing. 
- **Cycle 4:** `SUB F8, F6, F2` issues.
  - It takes an Add RS (Add 1).
  - It waits for `F6` (from Load 1) and `F2` (from Load 2).
  - Register `F8` is renamed to `Add 1`.
  - **Load 1 finishes and writes back (broadcasts) its result (e.g., 7.1).** 
    - The value is captured by the Subtract instruction waiting in `Add 1`. 
    - Register `F6` is updated to 7.1. 
    - `Load 1` RS is freed.
  - **Load 2 dispatches** (execution begins).

#### Cycles 5-6: Divides and Adds
- **Cycle 5:** `DIV F10, F0, F6` issues.
  - Takes a Multiply RS (Mul 2). 
  - `F6` is ready (7.1 from Load 1), but it waits for `F0` (from Mul 1).
  - Register `F10` renamed to `Mul 2`.
- **Cycle 6:** `ADD F6, F8, F2` issues.
  - Takes an Add RS (Add 2).
  - Waits for `F8` (from Add 1) and `F2` (from Load 2).
  - Register `F6` is renamed to `Add 2`.
  - **Load 2 writes its result (e.g., -2.5).**
    - Broadcasts `-2.5`. 
    - Captured by Multiply 1 (waiting for `F2`), Subtract 1 (waiting for `F2`), and Add 1 (waiting for `F2`).
    - Register `F2` updated. `Load 2` RS freed.

#### Cycles 7-9: Execution Out-of-Order
- **Cycle 7:** 
  - Multiply 1 and Subtract 1 now have all their operands. They both **dispatch**.
  - Subtract takes 2 cycles (executes in 7 and 8).
  - Multiply takes 10 cycles (executes in 7 through 16).
- **Cycle 9:** 
  - **Subtract 1 writes its result (e.g., -9.6).**
  - Captured by Add 1 (waiting for `F8`). 
  - `Add 1` RS is freed.

#### Cycles 10-58: The Long Wait
- **Cycle 10:** Add 1 dispatches (executes 10-11).
- **Cycle 12:** **Add 1 writes its result.** `Add 2` RS freed.
- **Cycle 17:** **Multiply 1 writes its result.** 
  - Broadcasts to `Div 1`. `Mul 1` RS freed.
- **Cycle 18:** Divide 1 dispatches (takes 40 cycles, executes 18-57).
- **Cycle 58:** **Divide 1 writes its result.** `Mul 2` RS freed. *Execution Complete!*

---

## 3. Timing-Only Analysis (Exam Technique)

For exams, you often don't need to draw out the full RS tables every cycle. Instead, you can track just three key milestones for each instruction: **Issue**, **Execute (Dispatch)**, and **Write Result**.

**Heuristics for Timing-Only Analysis:**
1. **Issue:** Look at the previous instruction's issue cycle. Add 1 cycle. Check if an RS of the required type is available. If all RS are full, stall until one is freed (remembering that a freed RS is available in the *next* cycle).
2. **Execute (Dispatch):** Look at the dependencies. When is the *latest* required operand broadcasted? Also check if the execution unit is free (if not pipelined). Add 1 cycle after the last dependency is broadcasted (or the same cycle, depending on strict processor rules). 
3. **Write Result:** `Dispatch Cycle + Latency = Write Cycle` or similar, depending on the exact definition. If an instruction dispatches in cycle 4 and has a latency of 2, it executes in cycles 4 and 5, writing in cycle 6.

---

## 4. Tomasulo Timing Quiz & Solution

Let's apply these rules to a specific quiz scenario.

### Quiz Setup & Constraints
- **Latencies:** Load = 1 cycle, Add = 1 cycle, Mul = 5 cycles.
- **RS Counts:** 1 Load, 2 Add, 2 Multiply.
- **Strict Rules:**
  1. Cannot Issue and Dispatch in the same cycle.
  2. Cannot capture an operand and Dispatch in the same cycle.
  3. RS freed in cycle `X` can only be reallocated in cycle `X+1`.

### Instructions
1. `LD F6, 34(R2)`
2. `MUL F2, F0, F1`
3. `ADD F8, F6, F2`
4. `ADD F10, F8, F2`
5. `ADD F12, F0, F2`
6. `ADD F14, F12, F4`

### Part 1: First Four Instructions (Cycles 1-4 Issue)

| Instruction | Issue | Dispatch | Write Result | Explanation |
| :--- | :---: | :---: | :---: | :--- |
| `1. LD F6, 34(R2)` | 1 | 2 | 3 | No dependencies. Dispatches in cycle 2 (rule 1). Latency 1 (executes cycle 2), writes cycle 3. |
| `2. MUL F2, F0, F1` | 2 | 3 | 8 | No dependencies (`F0`, `F1` are ready). Dispatches in cycle 3. Latency 5 (executes 3-7), writes cycle 8. |
| `3. ADD F8, F6, F2` | 3 | 9 | 10 | Needs `F6` (from LD, ready cycle 3) and `F2` (from MUL, ready cycle 8). Captures last operand in 8, dispatches in 9 (rule 2). Latency 1, writes cycle 10. |
| `4. ADD F10, F8, F2` | 4 | 11 | 12 | Needs `F8` (from ADD 1, ready cycle 10) and `F2` (from MUL, ready cycle 8). Captures last operand in 10, dispatches in 11. Latency 1, writes cycle 12. |

### Part 2: Structural Hazards on Reservation Stations

Now let's trace instructions 5 and 6, paying close attention to **RS availability**. We only have **2 Add RS**. 
- In cycle 3, `ADD 1` took the first RS.
- In cycle 4, `ADD 2` took the second RS.

| Instruction | Issue | Dispatch | Write Result | Explanation |
| :--- | :---: | :---: | :---: | :--- |
| `5. ADD F12, F0, F2` | 11 | 12 | 13 | **Wait for RS:** Both Add RS are full. `ADD 1` frees its RS in cycle 10. The RS is available in cycle 11. So this issues in **11**. Operands are ready (`F0`, `F2`). Dispatches in **12**, writes **13**. |
| `6. ADD F14, F12, F4` | 13 | 14 | 15 | **Wait for RS:** Needs an Add RS. `ADD 2` frees its RS in cycle 12. RS available in cycle 13. Issues in **13**. Needs `F12` (ready since cycle 13). Dispatches in **14**, writes **15**. |

> **Crucial Mental Model for Structural Hazards:** 
> Tomasulo's Algorithm handles True Data Dependencies (RAW) gracefully by renaming and waiting. However, **Structural Hazards** (running out of Reservation Stations) will physically stall the *Issue* stage. In-order issue means if instruction 5 stalls because there are no Add RS, instruction 6 (even if it's a completely independent Load) is also stalled and cannot issue!


---

