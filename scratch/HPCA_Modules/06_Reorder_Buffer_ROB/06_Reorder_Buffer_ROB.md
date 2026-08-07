# 06_Reorder_Buffer_ROB (Synthesized Notes)

# Reorder Buffer (ROB) and Out-of-Order Execution

## Background Context: The Limits of Basic Out-of-Order Execution
While Out-of-Order (OoO) execution (like Tomasulo's Algorithm) dramatically improves processor performance by executing instructions as soon as their data is ready, it introduces significant challenges when things go wrong. In real-world programs, execution isn't always a smooth, predictable flow. 

There are three major problems with basic OoO execution that need to be addressed:

1. **Imprecise Exceptions:**
   - *The Problem:* Imagine an older instruction (like a slow division) causes a divide-by-zero exception. However, a younger, faster instruction (like an addition) has already finished and permanently written its result to the register file.
   - *Why it's bad:* When the operating system's exception handler takes over, the processor's state is "messy." It contains results from instructions that logically appear *after* the exception. For the OS to recover cleanly, it needs a **precise exception**—a state where all instructions before the faulting instruction have completed, and zero instructions after it have modified the state.

2. **Branch Misprediction Recovery:**
   - *The Problem:* Processors guess which way a branch will go to keep the pipeline full. If the guess is wrong, the processor might have executed dozens of instructions from the wrong path, permanently modifying registers.
   - *Why it's bad:* We need a way to "undo" or roll back these permanent changes so the processor behaves as if the wrong instructions were never fetched.

3. **Phantom Exceptions:**
   - *The Problem:* What if we guess a branch incorrectly, and an instruction on that *wrong* path divides by zero?
   - *Why it's bad:* The processor will trigger a divide-by-zero exception for an instruction that, according to the actual program logic, should never have been executed in the first place.

## The Solution: Execute Out-of-Order, Commit In-Order
To clean up the "reordering mess," modern processors enforce a golden rule: **Execute out of order, but deposit values to registers in order.**

* **Mental Model:** Think of a restaurant kitchen. The chefs might cook dishes out of order depending on how long they take (a salad is ready before a well-done steak). However, the waiter (the processor) holds onto the dishes and only serves them to the customer (the register file) in the exact order they were ordered.

To implement this, processors introduce a hardware structure called the **Reorder Buffer (ROB)**.

### What is the Reorder Buffer (ROB)?
The ROB is a circular buffer (a table of entries) that acts as a temporary holding pen for instruction results. It remembers the original program order. Instructions place their results in the ROB when they finish computing, but these results are only permanently written to the architectural registers when it is absolutely safe to do so.

Each ROB entry typically contains:
- **Destination Register:** Which architectural register this instruction is supposed to update (e.g., `R1`).
- **Value:** The actual computed result (e.g., `15`).
- **Done/Valid Bit:** A flag indicating whether the instruction has finished executing and the value is ready.

The ROB uses two main pointers:
- **Issue Pointer (Tail):** Where the next fetched instruction will be placed.
- **Commit Pointer (Head):** The oldest instruction in the processor, which is next in line to be permanently saved ("committed").

## Instruction Lifecycle with a ROB
Adding a ROB changes how Tomasulo's Algorithm operates. Here is the new step-by-step lifecycle of an instruction:

### 1. Issue
When an instruction is issued, the processor allocates:
1. A free Reservation Station (RS).
2. The next available ROB entry (at the Issue Pointer).
*Crucially, the Register Alias Table (RAT) is updated to point to the **ROB entry**, NOT the Reservation Station.* The ROB entry now serves as the unique "name" or tag for this instruction's result.

### 2. Dispatch and Execute
The instruction waits in the Reservation Station until its operands are ready. Once ready, it is dispatched to the execution unit.
* **Optimization:** Because the ROB entry acts as the name for the result, the **Reservation Station can be freed immediately upon dispatch**. In basic Tomasulo, the RS had to be held until the result was broadcast. Freeing it early prevents RS bottlenecks.

### 3. Broadcast (Complete)
When the execution unit finishes computing the result:
- The result is broadcast on the Common Data Bus with its **ROB tag**.
- Reservation stations waiting for this tag capture the value.
- **Key Difference:** The result is written to the **ROB entry**, *not* the register file. The instruction's "Done" bit in the ROB is set to 1. The RAT is *not* updated here.

### 4. Commit
This is a new stage. Every cycle, the processor looks at the instruction at the **Commit Pointer**.
- If the instruction is *not done*, the processor waits.
- If the instruction *is done*, the processor "commits" it:
  1. The value in the ROB is permanently written to the architectural register file.
  2. The RAT is updated. (If the RAT is still pointing to this ROB entry, it is changed to point directly to the architectural register).
  3. The Commit Pointer moves to the next instruction, freeing the ROB entry.

## Handling Branch Mispredictions with the ROB
With the ROB, recovering from a branch misprediction becomes elegant and straightforward.

* **Intuition:** Don't panic when the execution unit discovers a branch was mispredicted. Just wait. Let the branch instruction reach the commit stage.

1. **Execution on the wrong path:** Instructions on the mispredicted path execute, but their results only go into the ROB. The register file remains completely untouched by these wrong instructions.
2. **Reaching Commit:** When the mispredicted branch finally reaches the Commit Pointer, we know for a fact that every instruction *before* the branch has safely committed, and no instruction *after* the branch has modified the register file. The registers are in the exact, perfect state they should be in at the moment the branch occurred.
3. **Recovery:**
   - We **Flush the ROB**: We move the Issue Pointer to equal the Commit Pointer, effectively deleting all younger, incorrect instructions from the ROB.
   - We **Reset the RAT**: Since the register file holds the absolute truth, we rewrite the RAT so every entry points directly to its corresponding architectural register (ignoring any leftover renaming).
   - We start fetching instructions from the correct branch target.

## Handling Exceptions with the ROB
The ROB solves both imprecise exceptions and phantom exceptions using a brilliant conceptual shift: **Treat an exception as just another type of data result.**

1. **Detecting the Exception:** If an instruction (e.g., a division) causes a divide-by-zero, the execution unit does *not* immediately trigger the OS handler. Instead, it writes "Exception: Divide by Zero" into the instruction's ROB entry and marks it as "Done".
2. **Waiting for Commit:** The instruction sits in the ROB until it becomes the oldest instruction in the machine (reaches the Commit Pointer).
3. **Triggering the Handler:** When an instruction with an "Exception" result tries to commit, the processor stops.
   - Because it's at the Commit Pointer, all older instructions have successfully finished and updated the registers.
   - Because we stop right here, no younger instructions have updated the registers.
   - We have achieved a **precise exception state**. The processor flushes the ROB (discarding younger instructions) and safely jumps to the OS exception handler.
4. **Solving Phantom Exceptions:** What if that divide-by-zero happened on a mispredicted branch path? 
   - The divide instruction will be marked with an exception in the ROB.
   - However, the mispredicted branch is older, so it will reach the Commit Pointer *first*.
   - When the branch commits, it flushes the ROB, erasing the divide instruction before it ever has a chance to commit. The phantom exception is cleanly ignored, exactly as it should be.

---

# Reorder Buffer (ROB) and Exceptions - Part 3

## 1. Background Context: The Need for ROB
In modern out-of-order (OoO) processors, instructions are fetched and executed as soon as their operands are ready, often out of their original program order. While this maximizes performance, it introduces two major challenges:
1. **Branch Mispredictions**: What if we execute instructions along a guessed branch path, and the guess is wrong?
2. **Precise Exceptions**: What if an instruction (like a divide) causes an exception (e.g., divide-by-zero), but we have already executed instructions that logically appear *after* it in the program?

To solve this, processors introduce the **Reorder Buffer (ROB)**. The ROB ensures that while instructions can *execute* out of order, they must **commit** (update the architectural state visible to the programmer) strictly **in order**. 

---

## 2. The "Outside View" of Execution
**Intuition**: Think of the processor as a kitchen and the programmer as a customer in a restaurant. The chefs (execution units) might prepare the dessert before the appetizer to save time, but the waiter (the ROB commit logic) will only serve the dishes to the customer in the correct order. The customer never sees the messy, out-of-order kitchen operations.

### Programmer's View vs. Processor's View
- **Internal State (Execution)**: The processor may execute an instruction (like a multiply) that comes *after* a mispredicted branch or an instruction that will eventually cause an exception. These instructions finish executing internally and sit in the ROB.
- **Architectural State (Commit)**: The programmer only sees instructions that have successfully committed. 
  - If a branch is mispredicted, the wrong-path instructions (even if fully executed internally) are simply flushed from the ROB before they commit.
  - The programmer *never* sees the results of wrong-path instructions or instructions following an exception. 
- **The Golden Rule**: An instruction is only "officially executed" when it commits. Before commit, its result is just an internal processor state waiting for final approval.

---

## 3. Handling Exceptions with the ROB
Let's consider a scenario where an instruction (e.g., a Divide) causes a divide-by-zero exception while executing out-of-order.

### The Problem
When the exception is detected during the divide's execution:
- Earlier instructions might still be executing.
- Later instructions might have already finished executing and are waiting in the ROB.

### The Solution (Step-by-Step)
1. **Detect and Mark**: The divide unit detects the divide-by-zero. Instead of stopping the processor immediately, it simply writes the exception status into the divide instruction's ROB entry, just like writing a normal result.
2. **Wait for Commit**: The processor continues running. It waits until the divide instruction becomes the *oldest* instruction in the machine (i.e., it reaches the head of the ROB).
   - Why? We must ensure that all instructions *before* the divide have successfully committed, so the processor state matches exactly what the programmer expects right before the exception.
3. **Trigger the Exception**: When the divide instruction tries to commit, the commit logic sees the exception flag.
4. **Flush the Pipeline**: The processor stops committing. It flushes the divide instruction and **all** subsequent instructions from the ROB and the pipeline. These instructions become "unexecuted" (as if they were never fetched).
5. **Jump to Handler**: Control is transferred to the OS exception handler.

**Mental Model**: Exception handling acts very much like a branch misprediction. We realize we went down the wrong path (normal execution instead of exception handling), so we roll back everything that happened after the offending instruction.

---

## 4. RAT Updates on Commit
The **Register Alias Table (RAT)** maps architectural registers (like `R1`, `R2`) to physical locations (like ROB entries). 

### How State is Updated
When an instruction commits, it takes its result from the ROB and deposits it into the architectural **Register File**. 
- **Rule 1: Always update the Register File**. The committing instruction writes to the Register File *regardless* of what the RAT says.
- **Rule 2: Conditionally update the RAT**. After writing to the register file, we check the RAT. Does the RAT currently point to the ROB entry that is committing?
  - **Yes (We are the latest rename)**: Update the RAT to point directly to the Register File. This means the latest value for this register is now safely in the architectural register.
  - **No (A newer instruction renamed this register)**: Leave the RAT alone. It must continue pointing to the newer ROB entry.

### Why do we deposit values into the Register File even if they are overwritten?
**Crucial Insight**: We do this to maintain a perfect, up-to-date architectural state for precise exceptions. 
If an exception occurs (or a branch mispredicts), we can instantly recover the processor state by simply:
1. Flushing the ROB.
2. Making the entire RAT point back to the Register File.
Because every committing instruction updated the Register File in program order, the Register File holds the exact, correct state of the program up to the last committed instruction.

---

## 5. Comprehensive Cycle-by-Cycle ROB Example
Let's walk through an execution timeline to see how Dispatch, Issue, Execute, Write Result, and Commit work together.

**Instruction Latencies for this Example**: 
- Add/Subtract: 1 cycle
- Multiply: 10 cycles
- Divide: 40 cycles

**Assumptions**:
- Issue: In-order. Takes 1 cycle.
- Execute: Can begin the cycle after operands are ready.
- Dispatch/Broadcast: Happens in the same cycle if an instruction captures a broadcasted result it was waiting for.

### Cycle 1 - 4: Issuing Instructions
- **Cycle 1**: Issue a Divide (`R2 = R3 / R4`). It takes `ROB1`. Operands are ready in the register file.
- **Cycle 2**: The Divide begins execution (will take until cycle 42 to broadcast its result, as it's a 40-cycle operation). Meanwhile, Issue a Multiply (`R1 = R5 * R6`). It takes `ROB2`. Operands ready.
- **Cycle 3**: The Multiply begins execution. Issue an Add (`R3 = R7 + R8`). It takes `ROB3`. Operands ready.
- **Cycle 4**: The Add begins execution. Issue a second Multiply (`R1 = R1 * R3`). It takes `ROB4`. 
  - **Dependency**: It needs `R1` (from `ROB2`) and `R3` (from `ROB3`). It must wait in the reservation station.

### Cycle 5 - 6: Execution and Broadcasts
- **Cycle 5**: 
  - `ROB3` (the Add) finishes execution and broadcasts its result.
  - Issue a Subtract (`R4 = R1 - R5`). It takes `ROB5`. It needs `R1` (from `ROB4`).
  - Because `ROB3` broadcasted, `ROB4` captures the value for `R3`. However, `ROB4` still waits for `R1` from `ROB2`.
- **Cycle 6**: Issue another Add (`R1 = R4 + R2`). It takes `ROB6`. It needs `R4` (from `ROB5`) and `R2` (from `ROB1`).

### Cycle 13 - 24: Resolving Dependencies
- **Cycle 13**: `ROB2` (first Multiply) finishes and broadcasts its result. `ROB4` captures this value. Now `ROB4` has both operands! It dispatches in this cycle.
- **Cycle 14**: `ROB4` (second Multiply) begins executing. 
- **Cycle 24**: `ROB4` finishes and broadcasts its result. `ROB5` (Subtract) captures this result and dispatches.

### Cycle 25 - 43: The Commit Phase
- **Cycle 25**: `ROB5` begins executing.
- **Cycle 26**: `ROB5` finishes and broadcasts its result. `ROB6` captures it, but still waits for `ROB1` (the very first Divide!).
- **Cycle 42**: The long Divide (`ROB1`) finally finishes and broadcasts its result! `ROB6` captures it and dispatches.
- **Cycle 43**: 
  - `ROB6` begins executing.
  - **COMMIT TIME**: Since `ROB1` is finally marked as 'done', the commit logic can start working. In cycle 43, `ROB1` commits. It writes its result to `R2` in the register file. The RAT entry for `R2` is updated to point to the register file (since no newer instruction renamed `R2`).
  - Once `ROB1` commits, `ROB2`, `ROB3`, `ROB4`, etc., can rapidly commit in subsequent cycles, as they have been finished for a long time.

---

## 6. Self-Test Quizzes (Mental Checkpoints)

*(Note: In the quiz section, the latencies are slightly different: Add/Sub = 1 cycle, Multiply = 3 cycles, Divide = 10 cycles)*

### Quiz 1: Initial RAT Update
**Scenario**: In Cycle 1, we issue `DIV R2, R3, R4` into `ROB1`. 
**Question**: What is the content of the RAT entry for `R2` immediately after issuing?
**Answer**: The RAT entry for `R2` will point to `ROB1`. 
*Explanation*: The RAT tracks the latest producer for a register. Since this divide will produce the latest value for `R2`, any subsequent instruction needing `R2` must look at `ROB1`.

### Quiz 2: Reading the RAT
**Scenario**: In Cycle 4, we issue `MUL R1, R1, R2` into a reservation station. The RAT says `R1` is mapped to `ROB2` and `R2` is mapped to `ROB1`.
**Question**: What goes into the reservation station tags for this multiplication, and which RAT entry is modified?
**Answer**: 
- The reservation station will hold tags `ROB2` (for the first operand) and `ROB1` (for the second operand). It holds no actual values yet because `ROB2` and `ROB1` haven't finished.
- The RAT entry for `R1` will be updated to point to the ROB entry assigned to this new multiplication (e.g., `ROB4`).
*Explanation*: We always read the RAT *before* updating it for the destination register to avoid an instruction waiting for its own output.

### Quiz 3: Dispatching and Writing Results
**Scenario**: In Cycle 5, `ROB3` (an Add instruction) finishes its 1-cycle execution. `ROB5` (a Subtract) is waiting for `ROB3`'s result.
**Question**: Does any instruction write a result in cycle 5? Does any instruction dispatch?
**Answer**: 
- **Writes result**: Yes, `ROB3` writes and broadcasts its result in Cycle 5.
- **Dispatches**: Yes, `ROB5` captures the broadcasted result in the same cycle (Cycle 5) and dispatches, meaning it will begin execution in Cycle 6.
*Explanation*: Modern pipelines are designed with bypassing/forwarding. The broadcasted result is immediately grabbed by waiting reservation stations, allowing dependent instructions to dispatch in the exact same cycle the result is broadcast.


---

# Playlist 2, Module 3: Advanced Reorder Buffer (ROB) Mechanics and Timing

## 1. Background Context & Intuition

To deeply understand the mechanics of a Reorder Buffer (ROB) based processor (often using Tomasulo's Algorithm with a ROB), it helps to recall its primary goal: **to enable out-of-order execution while preserving in-order commit.** This guarantees precise exceptions and correct architectural state, presenting an illusion of sequential execution to the software.

### The Four Stages of Instruction Execution
1. **Issue**: The instruction is decoded. The processor allocates a ROB entry and a Reservation Station (RS). It reads available operands from the Architectural Register File (ARF) or the Register Alias Table (RAT). **Crucial rule: Instructions must issue strictly in order.**
2. **Execute (Dispatch)**: The instruction waits in the RS until all its operands are ready. Once the final missing operand is captured from the Common Data Bus (CDB), the instruction is dispatched and execution begins in the functional unit (typically in the following cycle).
3. **Write Result (Broadcast)**: The functional unit finishes its computation and broadcasts the result on the CDB. Any dependent instructions waiting in their RS capture this value.
4. **Commit (Retire)**: The instruction reaches the head of the ROB. Its result is safely written to the ARF, and its ROB entry is freed. **Crucial rule: Instructions must commit strictly in order.**

---

## 2. Capturing Results, Dispatch, and Commit Timing (Quizzes 4 & 5)

### Dispatch Timing
When an instruction is waiting for a result (e.g., waiting for `ROB 1` to produce a value), it continuously monitors the Common Data Bus. 
- **Broadcast**: Suppose `ROB 1` broadcasts its result in Cycle 12.
- **Capture and Dispatch**: The dependent instruction captures this value in Cycle 12. Because this is the final value it needs, the instruction is **dispatched** in that exact same cycle (Cycle 12).
- **Execution Start**: The dispatched instruction begins actual execution in the functional unit in the **following cycle** (Cycle 13).

### Concurrent Cycle Actions
In a superscalar, out-of-order processor, many things happen concurrently. For instance, in Cycle 13:
- One instruction begins execution.
- Another instruction might capture a value and dispatch.
- **Commit**: If the oldest instruction in the ROB has already written its result (e.g., in Cycle 12), it will **commit** in Cycle 13.

---

## 3. Register Alias Table (RAT) Updates (Quiz 6)

A common pitfall is misunderstanding when the Register Alias Table (RAT) is updated. 

**Q: Does the RAT change when an instruction writes its result (broadcasts)?**
**A: No. Absolutely nothing changes in the RAT during the Write Result stage.**

### The Lifecycle of a RAT Entry
- **At Issue**: The RAT is updated to point to the newly allocated ROB entry (e.g., register `R1` now points to `ROB 6`).
- **At Write Result (Broadcast)**: The result is placed in the ROB entry and broadcasted on the CDB. The RAT is completely untouched.
- **At Commit**: The processor checks if the RAT *still* points to the committing ROB entry. 
  - **If Yes**: It means no subsequent instruction has overwritten this architectural register. The RAT entry is cleared (or pointed back to the ARF), and the ROB entry is freed.
  - **If No**: It means a newer instruction has already issued and renamed this register. The RAT is left alone, and the processor simply frees the committing ROB entry.

---

## 4. Committing Results to the Architectural Register File (Quizzes 7 & 8)

When an instruction commits, its result permanently updates the architectural state.

- **ARF Update**: Suppose `ROB 2` finishes its multiplication (result = 8) and commits. The value `8` is deposited into architectural register `R1`.
- **RAT Cleanup**: As discussed, the processor checks the RAT for `R1`. If it points to `ROB 2`, it clears the mapping. If it points to a newer instruction (e.g., `ROB 6`), it ignores the RAT. Finally, the reservation station (if not freed earlier) and `ROB 2` entry are freed.

**In-Order Commit Enforcement**:
An instruction cannot commit until **all previous instructions have committed**. If an instruction finishes execution early (e.g., a fast addition following a slow division), it simply waits in the ROB until it becomes the oldest instruction. 

*Example from Quiz 8*: If `ROB 5` broadcasts in Cycle 16, it can commit in Cycle 17. The next instruction, `ROB 6`, if already finished, will commit in Cycle 18, and `ROB 7` will commit in Cycle 19.

---

## 5. ROB Timing Examples & Structural Hazards

Timing analysis requires tracking data dependencies (RAW hazards) and structural hazards (limited processor resources).

### Key Rules for Timing Analysis
1. **In-Order Issue Stalls**: If an instruction cannot issue due to a lack of Reservation Stations, **all subsequent instructions are stalled**. Even if a later instruction needs a different, available RS, it cannot bypass the stalled instruction during issue.
2. **Execution Start**: Begins one cycle after all operands are ready (dispatch).
3. **Write Result**: Occurs when the functional unit finishes its specific latency (e.g., Add = 1 cycle, Mul = 10 cycles, Div = 40 cycles).
4. **Commit**: Occurs earliest in the cycle *after* the instruction writes its result, provided it is the head of the ROB.

### Handling Reservation Station Constraints (Detailed Walkthrough)
Consider a processor that frees a Reservation Station when the result is **broadcast**, not when dispatched. *(Note: Holding the RS until broadcast aids in speculative execution recovery).*
- **Scenario**: 2 Multiply/Divide RS and 3 Add/Sub RS.
  - `DIV` issues and takes the first Multiply/Divide RS.
  - `MUL` issues and takes the second Multiply/Divide RS.
  - A second `MUL` wants to issue, but there are no Multiply/Divide RS available. It must **stall at the issue stage**.
  - A subsequent `ADD` instruction is also stalled because issue must remain strictly in-order, even though all 3 Add/Sub RS are empty!
- The stalled `MUL` can only issue the cycle *after* one of the previous instructions broadcasts its result and frees up a Multiply/Divide RS.

### Superscalar Timing Constraints (Timing Quizzes 1 & 2)
Real processors often feature superscalar capabilities:
- **Multiple Broadcasts**: A processor might have separate buses for different functional units, allowing it to broadcast one Add/Sub result and one Multiply/Divide result in the **same cycle**.
- **Multiple Commits**: A processor might commit up to 2 instructions per cycle.
  - *Example*: A long `DIV` instruction finally commits in Cycle 8. A subsequent `ADD` instruction finished way back in Cycle 5 and has been waiting in the ROB. Because the processor can commit 2 instructions per cycle, both the `DIV` and the `ADD` can commit together in Cycle 8. 
  - A third instruction, `MUL`, which finishes in Cycle 9, will commit in Cycle 10 (one cycle after it writes its result, since it is now the oldest instruction).


---

