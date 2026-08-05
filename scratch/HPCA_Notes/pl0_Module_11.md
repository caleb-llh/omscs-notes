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