# Module 5: Pipelining, Dependencies, and Hazards

## 1. Introduction to Pipelining

### 1.1 The Laundry Analogy
**Intuition & Mental Model:**
To understand how pipelining works in a processor, it's incredibly helpful to use a real-world analogy: doing laundry. 
Imagine you have three stations: a Washer, a Dryer, and a Folder. Each station takes exactly 1 hour to process one load of laundry. 

- **Without Pipelining:** 
  You complete a full load (Washer -> Dryer -> Folder) before starting the next one. 
  *Time for 1 load = 3 hours.*
  If you have 10 loads of laundry, doing them sequentially takes $10 \times 3 = 30$ hours.

- **With Pipelining:**
  Instead of waiting for the first load to be fully folded, you put the second load into the washer as soon as the first load moves to the dryer. 
  * Time for the first load to finish = 3 hours.
  * Time for every subsequent load to finish = 1 hour (since one load leaves the pipeline every hour).
  For 10 loads: First load (3 hours) + 9 remaining loads (1 hour each) = **12 hours**.

**Key Takeaway:** Pipelining doesn't make a single task faster (latency remains the same), but it significantly improves the **throughput** of multiple tasks. Since computer programs have billions of instructions, pipelining dramatically reduces overall execution time.

### 1.2 Instruction Pipelining
Applying the laundry concept to a processor:
Consider a **5-stage pipeline** where each stage takes 1 clock cycle to complete. We have 10 instructions to execute, and they can flow perfectly without waiting on each other.

- **Without Pipelining:** 10 instructions $\times$ 5 cycles/instruction = 50 cycles.
- **With Pipelining:** 
  - First instruction takes 5 cycles to complete.
  - The remaining 9 instructions finish at a rate of 1 per cycle.
  - Total time = 5 cycles (initial fill) + 9 cycles = **14 cycles**.

Just like laundry, there is an initial overhead to "fill" the pipeline, but once filled, an instruction finishes every cycle.

---

## 2. Pipeline Performance and CPI (Cycles Per Instruction)

### 2.1 Ideal CPI vs. Actual CPI
In an ideal, perfectly flowing pipeline, the **Cycles Per Instruction (CPI)** approaches **1**. 
Because programs consist of millions or billions of instructions, the few cycles spent filling the pipeline at the start are mathematically negligible. In a "steady state," one instruction completes every single clock cycle.

### 2.2 Pipeline Stalls (Bubbles)
In reality, the steady-state CPI is rarely exactly 1 because the pipeline doesn't always flow smoothly. Disruptions in the flow are called **stalls** or **bubbles**.

**Mental Model: Car Assembly Line**
Imagine an assembly line: Stage 1 (Doors) -> Stage 2 (Front Wheels) -> Stage 3 (Rear Wheels).
If a machine damages the front wheels on a car, that car gets "stuck" in Stage 2 for an extra cycle to fix it.
- The car in Stage 1 cannot move forward (it is stalled).
- The worker in Stage 3 receives no car and sits idle for a cycle (this idle space is a "bubble").

Whenever a stall occurs, the pipeline produces *nothing* during the cycle that the stalled item should have finished. 
If this happens regularly—e.g., 1 stall every 5 cars—it takes 6 cycles to produce 5 cars.
- **Actual CPI** = $6 \text{ cycles} / 5 \text{ cars} = 1.2$. 
Even in steady-state, stalls push the CPI higher than 1.

---

## 3. Data Dependencies and Processor Stalls

### 3.1 What Causes a Processor Stall?
In processors, stalls often happen because an instruction needs information that isn't ready yet.
*Example in a 5-stage pipeline (Fetch -> Decode -> ALU -> Memory -> WriteBack):*
1. **Load Instruction:** `LOAD R1, [Memory]` (Fetching a value from memory into R1)
2. **Add Instruction:** `ADD R2, R1, R3` (Needs the value in R1 to compute)

While the `LOAD` is in the ALU stage (calculating the memory address), the `ADD` is in the Decode stage trying to read `R1`. However, `LOAD` hasn't fetched the value from memory yet, let alone written it to `R1`. 
If `ADD` proceeds, it will read the *wrong, stale* value of `R1`.

**The Solution:** The pipeline must **stall** the `ADD` instruction in the Decode stage until the `LOAD` successfully writes the correct value to `R1`.
- Because `ADD` is stuck, the instruction behind it is also stuck.
- This creates **bubbles** (empty cycles) that flow forward through the pipeline in place of the stalled instruction.
- If it takes 2 extra cycles for the `LOAD` to write the data, we get 2 pipeline bubbles. The sequence of finishing instructions becomes: `LOAD` finishes -> Bubble -> Bubble -> `ADD` finishes.
- This increases the overall CPI.

---

## 4. Control Dependencies and Pipeline Flushes

### 4.1 The Branch Problem
A **control dependence** occurs when the execution of an instruction depends on a previous control instruction, like a branch or jump.
*Example:* 
```assembly
ADD ...
BEQ R1, R3, TargetLabel  // Branch if Equal
SUB ...                  // Should we fetch this?
MUL ...                  // Or should we fetch from TargetLabel?
```
When the processor fetches the `BEQ` (Branch) instruction, it doesn't even know it's a branch until it is decoded. By the time it evaluates the condition (e.g., in the 3rd or 6th stage of a deeper pipeline), the processor has already optimistically fetched subsequent instructions (like `SUB` and `MUL`).

### 4.2 Pipeline Flushes
If the processor guesses wrong (e.g., the branch is taken, but we fetched the sequential instructions), it must discard the wrong instructions.
- Converting these mistakenly fetched instructions into bubbles is called a **Pipeline Flush**.
- Flushes are a major source of stalls, pushing the CPI greater than 1.

### 4.3 Calculating CPI with Control Penalties
- Roughly **20%** of all instructions are branches or jumps.
- Slightly more than **50%** of these are "taken" (meaning we jump to a new address).
- **Penalty Calculation:** If a branch is resolved in the 3rd stage, we fetch 2 wrong instructions. If a branch is taken, we flush 2 instructions (2 idle cycles).
- **Example:** Ideal CPI = 1. If 10% of all instructions cause a 2-cycle penalty:
  *Actual CPI* = $1 + (0.10 \times 2) = 1.2$.

**Impact of Deep Pipelines:**
Modern processors often have much deeper pipelines (e.g., 10 to 20 stages). If a branch is resolved in the 6th stage, the penalty is 5 cycles. 
*Quiz Example:* If 25% of instructions are taken branches, and the penalty is 5 cycles:
*Actual CPI* = $1 + (0.25 \times 5) = 2.25$. 
The processor runs at less than half its ideal speed!
*Solution:* Processors use **Branch Prediction** to guess branch outcomes early and accurately, drastically reducing this penalty percentage.

---

## 5. Types of Data Dependencies

Instructions frequently depend on the registers modified by previous instructions. We categorize data dependencies into three valid types, plus one non-dependence.

### 5.1 True / Flow Dependence (RAW)
**RAW (Read After Write):** A later instruction reads a value that an earlier instruction writes.
```assembly
I1: ADD R1, R2, R3   // Writes R1
I2: SUB R4, R1, R5   // Reads R1
```
*Mental Model:* Data literally "flows" from `I1` to `I2`. You absolutely cannot reorder these. The read must happen *after* the write.

### 5.2 Output Dependence (WAW)
**WAW (Write After Write):** Two instructions write to the same register.
```assembly
I1: ADD R1, R2, R3   // Writes R1
I2: MUL R1, R5, R6   // Writes R1
```
*Mental Model:* The final "output" in `R1` must come from `I2`. If you swap them, the final value in `R1` is wrong.

### 5.3 Anti-Dependence (WAR)
**WAR (Write After Read):** A later instruction overwrites a register that an earlier instruction needs to read.
```assembly
I1: SUB R7, R1, R4   // Reads R1
I2: MUL R1, R5, R6   // Writes R1
```
*Mental Model:* `I1` needs to safely read the old value of `R1` before `I2` destroys it. It's an "anti"-dependence because it flows in the reverse direction of a RAW dependence.

### 5.4 False/Name Dependencies vs. True Dependencies
- **True Dependence:** RAW. The data value itself is passed between instructions.
- **False / Name Dependencies:** WAW and WAR. There is no data flowing between the instructions. They just happen to use the same register "name" (e.g., `R1`). 

*(Note: **Read After Read (RAR)** is NOT a dependence. Multiple instructions can read the same register in any order without affecting the outcome.)*

---

## 6. Dependencies vs. Hazards

It is critical to distinguish between a *Dependence* and a *Hazard*:
- **Dependence:** A property of the **program / code itself**. It dictates the required order of execution.
- **Hazard:** A property of the **pipeline interacting with the program**. A hazard occurs when a dependence would result in incorrect execution *if the pipeline didn't stall or intervene*.

### 6.1 Hazards in a 5-Stage In-Order Pipeline
Let's evaluate which dependencies actually cause hazards in the classic 5-stage pipeline (Fetch, Decode/RegRead, ALU, Memory, WriteBack):

1. **WAW (Output Dependence):** 
   - Not a hazard. Instructions move through the pipeline in order and write to registers in the WriteBack stage in order. `I2` will naturally write after `I1`.
2. **WAR (Anti-Dependence):** 
   - Not a hazard. `I1` reads registers in stage 2 (Decode). `I2` writes registers in stage 5 (WriteBack). Because `I1` enters the pipeline first, it will read the register cycles before `I2` even reaches the write stage.
3. **RAW (True Dependence):**
   - **Potentially a Hazard!** `I2` needs to read in stage 2, but `I1` doesn't write the result until stage 5.
   - **Distance matters:** 
     - If `I2` immediately follows `I1`, it's a hazard (stalls are needed).
     - If there are 3 or more independent instructions between `I1` and `I2`, `I1` will have completed stage 5 and written the data *before* `I2` reaches stage 2. In this case, the true dependence is **not** a hazard.

**Summary of Hazards:** A true dependence (RAW) is only a hazard if the consuming instruction is too close to the producing instruction for the pipeline to resolve it naturally.