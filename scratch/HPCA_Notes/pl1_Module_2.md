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
