# 04_Predication (Synthesized Notes)

# HPCA Module 10: Advanced Branch Prediction and Predication

This module explores advanced techniques in computer architecture to handle control hazards, specifically focusing on hierarchical predictors, function return prediction via the Return Address Stack (RAS), and avoiding branches altogether using predication and if-conversion.

---

## 1. Hierarchical Predictors

### Background & Intuition
Standard predictors like the **Tournament Predictor** try to combine two good predictors (e.g., Local and Global) and run them in parallel, updating both to choose the best one. However, high-accuracy predictors are expensive (require large memory for long histories). 
**Intuition (Mental Model):** Imagine a company. You have a cheap frontline worker (Okay Predictor) and a highly-paid specialist (Good Predictor). You don't want the specialist wasting time on trivial tasks. A **Hierarchical Predictor** filters out easy-to-predict branches so the expensive predictor's limited entries are reserved only for the hard-to-predict branches.

### How It Works
- **The "Okay" Predictor:** A cheap, large array of simple 2-bit counters. Most branches (e.g., always-taken, simple loops) are predictable here.
- **The "Good" Predictor:** A smaller, highly accurate predictor (e.g., with long history registers) that costs a lot per entry.
- **The Mechanism:** 
  - Predict using the Okay predictor by default.
  - If the Okay predictor mispredicts, allocate an entry in the Good predictor for that branch.
  - On future executions, if a branch has an entry (tag) in the Good predictor, use it. Otherwise, fall back to the Okay predictor.

### Real-World Example: Intel Pentium M
The Pentium M uses a 3-level hierarchical predictor:
1. **2-bit Counters (Cheap & Large):** Used by default.
2. **Local History Predictor (Medium):** Used if the 2-bit counter fails.
3. **Global History Predictor (Expensive & Small):** Used if the Local predictor fails.
*Result:* Space is saved in the expensive predictors, allowing them to track extremely long histories for the few branches that actually need them.

### Multi-Predictor Combination Example
Suppose you have three predictors:
- 2-bit predictor covers 95% of branches.
- P-share covers the same 95% + an additional 2%.
- G-share covers the same 95% + a *different* 3%.
**Optimal Combination:** Use a **Hierarchical Predictor** that chooses between the 2-bit predictor and a **Tournament Predictor**. The Tournament Predictor, in turn, chooses between P-share and G-share for the remaining 5% of complex branches.

---

## 2. Return Address Stack (RAS)

### The Problem with Function Returns
Function returns (`RET`) are unconditional (always taken), but their **target address is dynamic**. A function like `printf` can be called from hundreds of different places in a program.
If we use a standard Branch Target Buffer (BTB), it only remembers the *last* place the function returned to. If `printf` is called from `Location A` and then `Location B`, the BTB will mispredict the return for `Location B` (it will predict `Location A`).

### The Solution: Return Address Stack (RAS)
**Intuition:** Leave a trail of breadcrumbs. When you enter a maze (function call), drop a breadcrumb (return address). When you exit, pick up the last breadcrumb to know where to go.

The RAS is a small, dedicated hardware stack (typically 4-32 entries) located close to the fetch unit.
- **On a Function Call (e.g., `CALL`):** Push the return address (PC + 4) onto the RAS.
- **On a Function Return (e.g., `RET`):** Pop the top address from the RAS and use it as the predicted target.

### RAS Full Policy: Wraparound vs. Don't Push
What happens when the hardware stack gets full (e.g., calling 5 functions deep on a 4-entry RAS)?
1. **Don't Push:** Stop pushing new addresses. Keep the oldest ones.
2. **Wraparound (The Winner):** Overwrite the oldest entries with the newest ones.

**Why Wraparound is better:** Programs typically have a "main" function that calls functions, which call smaller functions, which call even smaller functions (leaf functions). The smallest functions are called the most frequently. Wraparound sacrifices the prediction of the large, long-running functions (like returning to `main`) to correctly predict the thousands of returns from the small, deeply nested functions. This minimizes the total number of mispredictions.

---

## 3. Pre-decoding: Identifying Instructions Early

### The "Chicken and Egg" Problem
To use the RAS, the processor needs to know the instruction is a `RET` during the **Fetch stage**. But the instruction isn't identified as a `RET` until the **Decode stage**. If we wait until Decode, it's too late—we've already fetched the wrong next instructions.

### Solutions
1. **Branch Predictor for Instruction Types:** Train a simple 1-bit predictor based on the PC to guess "Is this PC a return instruction?" based on past history.
2. **Pre-decoding (Most Popular):** 
   - **Mental Model:** Putting sticky notes on cache lines.
   - When instructions are fetched from main memory (RAM) into the Instruction Cache (L1i), the processor does a quick "pre-decode."
   - It appends extra metadata bits to the cache line. For example, a 32-bit instruction might be stored as 33 bits in the cache, where the 33rd bit flags "Is this a RET instruction?".
   - Pre-decoding is also used to identify instruction length (for variable-length ISAs like x86) and general branch identification, saving power and time during the critical execution pipeline.

---

## 4. Predication & If-Conversion

### Dealing with Control Hazards without Branching
Branch prediction is great, but a misprediction in a modern deep pipeline is devastating (e.g., flushing 50+ instructions). **Predication** offers an alternative: don't predict the branch, just execute *both* paths and throw away the wrong result.

### Predication vs. Branch Prediction
| Scenario | Approach | Reasoning |
| :--- | :--- | :--- |
| **Loops** | Branch Prediction | Predicating a loop means branching work exponentially every iteration. Branch prediction is highly accurate for loops anyway. |
| **Function Calls/Returns** | Branch Prediction | Always taken. No alternative path to predicate. |
| **Large If-Then-Else** | Branch Prediction | Executing both paths wastes too much work (e.g., 100 instructions wasted either way). Better to predict and risk a flush. |
| **Small If-Then-Else** | **Predication** | Executing both paths of a small branch (e.g., 5 instructions) wastes very little. It's cheaper to always waste 5 instructions than to risk a 50-instruction pipeline flush if prediction accuracy isn't near-perfect. |

### If-Conversion
**If-Conversion** is the compiler technique of transforming control dependencies (branches) into data dependencies.

**Example Code:**
```c
if (condition) {
    x = x1;
} else {
    x = x2;
}
```

If converted to standard assembly, this requires a branch. If converted using **Conditional Moves**, it requires no branches:

### Conditional Move Instructions
Modern ISAs provide instructions that only execute if a condition is met.
- **MIPS:** `MOVZ` (Move if Zero), `MOVN` (Move if Not Zero)
- **x86:** `CMOVz`, `CMOVnz`, `CMOVg` (Move based on condition flags)

**If-Converted Assembly (MIPS-style):**
```assembly
# Assume R3 holds the condition (0 = false, non-zero = true)
# R1 holds x1, R2 holds x2
# We want x (R4) to be x1 if true, x2 if false

MOVN R4, R1, R3   # R4 = R1 (x1) if R3 is NOT zero
MOVZ R4, R2, R3   # R4 = R2 (x2) if R3 IS zero
```
By doing this, the processor fetches and executes these instructions sequentially without ever risking a branch misprediction penalty.

---

# Module 11: If-Conversion and Predication

## 1. Introduction: The Problem with Unpredictable Branches

**Background Context:**
Modern CPUs rely heavily on deep pipelines to achieve high performance. When a CPU encounters a conditional branch (like an `if-else` statement), it must guess which path the program will take using a branch predictor. 
- **Good News:** Most branches are highly predictable (e.g., loop conditions).
- **Bad News:** Some branches are data-dependent and essentially random (e.g., ~50% taken, ~50% not taken). When the CPU mispredicts, it must flush the pipeline, discarding all speculative work. This **misprediction penalty** can cost dozens of cycles.

**Intuition for If-Conversion:**
Imagine you are at a fork in the road, and you don't know which path leads to your destination. Instead of guessing, walking miles, and having to run back if you were wrong (branching), you clone yourself, send a clone down each path, and immediately destroy the clone that went the wrong way. 
In hardware, **If-Conversion** means executing the instructions for *both* the `if` and `else` paths simultaneously (or sequentially without branching), and then selectively committing only the correct results. You do more total work, but you completely eliminate the devastating branch misprediction penalty.

---

## 2. Conditional Moves (`MOVZ` / `MOVN`)

One way to implement if-conversion is by adding specific **conditional move** instructions to the Instruction Set Architecture (ISA).
- `MOVZ` (Move if Zero): Moves data only if a specified condition register is zero.
- `MOVN` (Move if Not Zero): Moves data only if a specified condition register is not zero.

### Example: If-Converting a Branch
**Original Code (with a branch):**
```assembly
    BEQ r1, 0, Target  ; Branch if r1 == 0
    ; --- Not Taken Path ---
    ... (modifies r2)
    JMP End
Target:
    ; --- Taken Path ---
    ADD r3, r3, 1      ; modifies r3
End:
```
*Issue:* The original code takes either 3 instructions (Not Taken) or 2 instructions (Taken), plus the branch. If the branch is hard to predict, mispredictions will severely hurt performance.

**If-Converted Code (Branch-Free):**
To make this branch-free, we compute both paths but store the results in **temporary registers** (`r4` and `r5`) so we don't accidentally corrupt `r2` or `r3` before we know which path is correct.
```assembly
    ; Compute both paths unconditionally
    ... (compute Not Taken result into r4 instead of r2)
    ADD r5, r3, 1      ; compute Taken result into r5 instead of r3
    
    ; Select the correct results using conditional moves
    MOVN r2, r4, r1    ; If r1 != 0, move r4 into r2 (Not Taken path)
    MOVZ r3, r5, r1    ; If r1 == 0, move r5 into r3 (Taken path)
```
*Result:* We execute exactly 4 instructions worth of work every time, with zero branches.

### Performance Analysis: Is it worth it?
Let's mathematically model the performance.
- Assume a **40-instruction penalty** for a misprediction.
- **If-Converted Code:** Always executes exactly **4 instructions**.
- **Branched Code:**
  - Path A: 3 instructions.
  - Path B: 2 instructions.
  - If the branch is perfectly predicted, the average cost is ~**2.5 instructions** (assuming a 50/50 split). Branched code wins!
  - If the branch is hard to predict (e.g., only 80% accurate):
    - Base execution: 2.5 instructions.
    - Misprediction cost: 20% misprediction rate * 40 instruction penalty = 8 instructions.
    - Average total cost = 2.5 + 8 = **10.5 instructions**.
    - If-converted code (4 instructions) is vastly superior here.

**Key Takeaway:** If-conversion is highly beneficial for hard-to-predict branches, but actually *degrades* performance for easy-to-predict branches (because you are doing unnecessary work for the path not taken).

### Drawbacks of Conditional Moves
1. **Compiler Support Required:** The compiler must explicitly rewrite the code to use these instructions. Old binaries won't benefit.
2. **Increased Register Pressure:** You need extra registers (`r4`, `r5`) to hold the speculative results from both paths before the final selection.
3. **Extra Instructions:** You must execute explicit `MOVZ`/`MOVN` instructions just to select the correct results.

---

## 3. Full Predication

To solve the drawbacks of conditional moves, architects introduced **Full Predication**.
**Mental Model:** Instead of having a few special `MOVE` instructions that check conditions, what if *every single instruction* in the ISA had an "enable" switch? The instruction computes its result, but at the very end of the pipeline, it only writes the result to the destination register if its enable switch (predicate) is turned on.

### Hardware Support (e.g., Intel Itanium)
- **Predicate Registers:** The CPU has a set of small 1-bit registers (e.g., 64 predicate registers in Itanium).
- **Instruction Encoding:** Every instruction word includes a few extra bits (e.g., 6 bits out of a 41-bit instruction) to specify its **qualifying predicate**.
- **Syntax:** `(p1) ADD r2, r2, 1` means "Execute this ADD, but only commit the result if predicate register `p1` is true."

### Example: Full Predication in Action
Using the same logic as before:
```assembly
    ; 1. Evaluate the condition and set mutually exclusive predicates
    CMP.EQ p1, p2 = r1, 0  ; If r1 == 0: p1 = True, p2 = False
                           ; If r1 != 0: p1 = False, p2 = True
                           
    ; 2. Execute both paths, predicated on the condition
    (p2) ... (modifies r2) ; Only commits if r1 != 0
    (p1) ADD r3, r3, 1     ; Only commits if r1 == 0
```
**Advantages of Full Predication:**
1. **No Temporary Registers Needed:** We can write directly to `r2` and `r3`. If the predicate is false, the write is simply suppressed.
2. **No Selection Overhead:** We don't need extra `MOVZ`/`MOVN` instructions at the end. The work instructions themselves handle the selection.
3. The only overhead is executing the instructions from the wrong path, which are essentially turned into `NOP`s (No-Operations) at the write-back stage.

### Performance Break-Even Quiz
Let's analyze when full predication is better than branching.
**Scenario:**
- Branch Taken path: 2 instructions.
- Branch Not-Taken path: 3 instructions.
- Average base branch execution: 2.5 instructions.
- Predicated execution: 1 (CMP) + 2 (Taken path) = 3 instructions.
- Base CPI = 0.5 cycles per instruction.
- Misprediction Penalty = 10 cycles.

**Calculation:**
- **Predicated Code Cost:** 3 instructions * 0.5 CPI = **1.5 cycles** (constant).
- **Branched Code Base Cost:** 2.5 instructions * 0.5 CPI = **1.25 cycles** (perfect prediction).
- The predicated code is 0.25 cycles slower than perfectly predicted branched code.
- How many mispredictions make the branched code lose that 0.25 cycle advantage?
  - Break-even misprediction rate = (0.25 cycles) / (10 cycles per mispredict) = 0.025 = **2.5%**.
- **Conclusion:** If the branch predictor is less than **97.5% accurate** (100% - 2.5%), Full Predication is faster!

---

## 4. Summary & What's Next

- **If-Conversion** replaces control hazards (hard-to-predict branches) with a slight increase in computational work.
- **Conditional Moves** require temporary registers and selection overhead.
- **Full Predication** elegantly integrates conditionality into every instruction, reducing register pressure and instruction count overhead.
- **Up Next:** Now that we understand how to mitigate **Control Hazards** (via branch prediction and predication), we will explore how to handle **Data Hazards** while maintaining a smooth pipeline flow.

---

