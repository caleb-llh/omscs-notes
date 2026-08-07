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
