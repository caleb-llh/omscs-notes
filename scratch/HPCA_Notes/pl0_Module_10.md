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