# Module 7: Branch Prediction - Foundations

## Introduction to Branch Prediction

**Background Context:** In modern pipelined processors, instructions are fetched continuously to keep the pipeline full and maximize throughput. However, when a branch instruction is fetched, the processor doesn't immediately know two critical things:
1. **Direction:** Will the branch be taken or not taken?
2. **Target:** If taken, what is the destination address?

These properties are only resolved later in the pipeline (e.g., the execution stage). If the processor pauses fetching to wait for the branch to resolve, it introduces "pipeline bubbles" (wasted cycles). To avoid this, the processor must *guess* (predict) the outcome and continue fetching.

---

## 1. The "Predict Not-Taken" Predictor

**Mental Model:** This is the most optimistic and simplest approach. The processor essentially assumes every instruction is just a normal, sequential instruction and that branches simply won't be taken.

- **How it works:** Simply increment the Program Counter (`PC = PC + 4`). No special memory, tables, or complex logic is needed because the hardware already has to compute `PC + 4` anyway.
- **Accuracy Analysis:**
  - A general rule of thumb is that **~20%** of all instructions are branches.
  - Therefore, **80%** of the time, the instruction isn't even a branch, and `PC + 4` is 100% correct.
  - Of the 20% that are branches, slightly more than half are taken. Let's assume **60% are taken** and **40% are not taken**.
  - **Total Accuracy:** $80\% \text{ (non-branches)} + (40\% \times 20\%) \text{ (not-taken branches)} = 80\% + 8\% = \textbf{88\%}$.
  - **Misprediction Rate:** $60\% \times 20\% = \textbf{12\%}$.

**Impact on CPI (Cycles Per Instruction):**
We can calculate the impact of branch mispredictions on the CPI using the following formula:
$$ \text{CPI} = \text{Ideal CPI} + (\text{Misprediction Rate} \times \text{Misprediction Penalty}) $$

*Example:* In a 5-stage pipeline where branches are resolved in the 3rd stage, the penalty is 2 cycles.
$$ \text{CPI} = 1 + (0.12 \times 2) = \textbf{1.24} $$

---

## 2. Why We Need Better Prediction

**Intuition:** While 88% accuracy sounds like an A grade on an exam, in computer architecture, it leaves a lot of performance on the table. This becomes significantly more pronounced as processors become more advanced.

Let's compare the 88% Not-Taken predictor against a theoretical **99% accurate Better Predictor** across two modern architectural features:

### A. Deeper Pipelines
Imagine a 14-stage pipeline that resolves branches in the 11th stage, resulting in a **10-cycle penalty**.
- **Not-Taken (12% error):** $\text{CPI} = 1 + (0.12 \times 10) = \textbf{2.2}$
- **Better Predictor (1% error):** $\text{CPI} = 1 + (0.01 \times 10) = \textbf{1.1}$
- **Speedup:** $2.2 / 1.1 = \textbf{2.0x}$ (The better predictor makes the CPU twice as fast!)

### B. Superscalar Processors (Multiple Issue)
Imagine a processor that executes 4 instructions per cycle (IPC) with a 10-cycle penalty. The ideal CPI is $1/4 = 0.25$.
- **Not-Taken (12% error):** $\text{CPI} = 0.25 + (0.12 \times 10) = \textbf{1.45}$
- **Better Predictor (1% error):** $\text{CPI} = 0.25 + (0.01 \times 10) = \textbf{0.35}$
- **Speedup:** $1.45 / 0.35 \approx \textbf{4.14x}$

> **Takeaway:** The deeper the pipeline and the wider the issue width (more instructions executed per cycle), the more devastating a branch misprediction penalty becomes. A single misprediction in a 4-wide, 10-cycle penalty processor flushes **40 instructions** worth of work!

---

### Real-World Example: Pentium 4 Prescott (Quiz & Solution)
**Context:** The Intel Pentium 4 "Prescott" architecture featured an incredibly deep 31-stage pipeline, resulting in a massive **30-cycle misprediction penalty**.

**Scenario:**
- 20% of instructions are branches.
- Initial State: 1% of *branches* are mispredicted. Overall CPI = 0.5.
- Question: What is the new CPI if 2% of *branches* are mispredicted?

**Solution Breakdown:**
1. **Find the Ideal CPI:**
   - Misprediction rate across *all* instructions = $1\% \times 20\% = 0.002$.
   - Current Penalty Cost = $0.002 \times 30 = 0.06$ CPI.
   - Ideal CPI = Actual CPI - Penalty Cost = $0.5 - 0.06 = \textbf{0.44}$.
2. **Calculate New CPI:**
   - New misprediction rate across *all* instructions = $2\% \times 20\% = 0.004$.
   - New Penalty Cost = $0.004 \times 30 = 0.12$ CPI.
   - New Actual CPI = Ideal CPI + New Penalty Cost = $0.44 + 0.12 = \textbf{0.56}$.

---

## 3. How Do We Make Better Predictions?

**The Challenge:** When the processor is in the Fetch stage, all it knows is the current Program Counter (PC). It hasn't decoded the instruction yet, so it doesn't even know *if* the instruction is a branch, let alone what its target offset is or whether it evaluates to true.

**The Solution:** Use historical data. Branches exhibit high temporal locality. For example, the branch at the end of a `for` loop that runs 100 times will be "Taken" 99 times in a row, and "Not Taken" once. If the processor remembers what a branch did the last time it was executed, it can make a highly educated guess about what it will do this time.

---

## 4. Branch Target Buffer (BTB)

**Concept:** The BTB is a small, fast hardware cache that maps a branch's PC to its predicted target address. 

**How it works:**
1. During the Fetch stage, the processor uses the current PC to index the BTB.
2. If there is a hit, the BTB outputs the predicted "Next PC".
3. The processor fetches from this predicted address on the very next cycle.
4. Later, when the branch is actually evaluated, if the prediction was wrong, the processor updates the BTB with the correct target address so it gets it right next time.

### Realistic BTB Indexing
A perfect BTB would have an entry for every possible 64-bit instruction address, but memory limits require the BTB to be small (e.g., 1024 entries) to maintain a 1-cycle access latency.

**How do we map a 64-bit PC into a 1024-entry ($2^{10}$) BTB?**
We must extract 10 bits from the PC to use as the index.
- ❌ **Do NOT use the most significant bits:** Sequential instructions in the same loop/function share the same upper bits. They would all map to the exact same BTB entry, causing constant eviction conflicts.
- ❌ **Do NOT use the absolute least significant bits:** In architectures where instructions are 4 bytes long and word-aligned, addresses always end in `00` (e.g., 0, 4, 8, 12). Using the lowest 2 bits wastes entries because they never change.
- ✅ **Use the lowest *variable* bits:** Ignore the lowest 2 bits (which are always 00), and take the next 10 bits (`PC[11:2]`). This evenly distributes sequential instructions across the BTB, perfectly mapping loops and functions without conflicts.

---

## 5. Direction Predictor: Branch History Table (BHT)

**Concept:** Storing a full 64-bit target address in the BTB is expensive. To save space and increase tracking capacity, we can split the prediction task. The BHT is a dense table dedicated solely to predicting *direction* (Taken vs. Not Taken).

**How it works:**
- It is indexed exactly like the BTB (using the lowest variable bits of the PC).
- Each entry is extremely small—just **1 bit** (0 = Not Taken, 1 = Taken).
- **Synergy with BTB:** 
  1. The processor checks the BHT.
  2. If BHT says `0` (Not Taken), the processor simply increments the PC (`PC + 4`). The BTB is ignored.
  3. If BHT says `1` (Taken), the processor looks up the target address in the BTB.
- **Optimization:** Because of the BHT, the BTB only needs to store entries for branches that are actually *taken*. This drastically reduces conflicts in the small, expensive BTB, while the large, cheap BHT can track the history of thousands of instructions.

---

## 6. Accessing Predictors in Loops (Mental Model Exercise)

When analyzing code to see how often predictors are accessed, keep this crucial rule in mind:
> **The BHT is accessed *every single time* an instruction is fetched.** 

Because the fetch stage doesn't know what the instruction is yet, it must query the BHT for *every* instruction just in case it turns out to be a branch.

**Example Scenario:** A loop initializes a counter, runs a loop body, and branches back to the top until a condition is met (e.g., 100 iterations).
- **Initialization instructions (before the loop):** Fetched 1 time. BHT accessed 1 time.
- **Loop body instructions:** Fetched 100 times. BHT accessed 100 times.
- **Loop conditional branch (at the bottom):** 
  - Evaluates to "Taken" 100 times to jump back up.
  - Evaluates to "Not Taken" 1 time to fall through and exit the loop.
  - Total fetches: 101 times. BHT accessed 101 times.

**Indexing the BHT for these instructions:**
If the BHT has 16 entries ($2^4$), it requires a 4-bit index. Assuming 4-byte aligned instructions, we ignore the lowest 2 bits and use `PC[5:2]`.
- Instruction at `0x...C000`: Index `0000` (Entry 0)
- Instruction at `0x...C004`: Index `0001` (Entry 1)
- Instruction at `0x...C008`: Index `0010` (Entry 2)
- This sequential mapping ensures that consecutive instructions in the loop do not collide in the predictor tables.