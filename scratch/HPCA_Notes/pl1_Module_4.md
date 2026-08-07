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
