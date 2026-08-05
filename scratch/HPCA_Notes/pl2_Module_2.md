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
