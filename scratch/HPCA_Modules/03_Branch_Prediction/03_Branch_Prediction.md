# 03_Branch_Prediction (Synthesized Notes)

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

---

# Module 8: Advanced Branch Prediction and BTB/BHT Interactions

## Introduction and Background Context
In modern pipelined processors, branching introduces a significant challenge: when a branch instruction is fetched, the processor doesn't immediately know the target address or whether the branch will actually be taken. Waiting for this information causes pipeline stalls (bubbles). 

To mitigate this, processors use two key structures:
1. **BHT (Branch History Table)**: Predicts *whether* a conditional branch will be Taken (T) or Not Taken (NT).
2. **BTB (Branch Target Buffer)**: Caches the *destination address* of a taken branch so the processor can immediately begin fetching from the target.

This module explores the nuanced interaction between the BTB and BHT, evaluates the flaws of simple 1-bit predictors, introduces the robust 2-bit predictor, and ultimately dives into history-based prediction for handling complex patterns.

---

## 1. BTB and BHT Interaction

### Mental Model: The Gatekeeper
Think of the BHT as a gatekeeper for the BTB. Accessing the BTB costs time and energy. If the BHT predicts that a branch is **Not Taken**, the processor simply increments the Program Counter (PC = PC + 4) and continues fetching sequentially. In this scenario, the BTB is *never accessed*. The BTB is only queried when the BHT predicts a branch is **Taken**.

### Key Rules of Interaction
* **Non-Branch Instructions**: Never predicted as taken by a perfect BHT, meaning they generate **0 BTB accesses**.
* **Always-Taken Branches (e.g., Unconditional Jumps)**: The BHT always predicts Taken, so the BTB is accessed every time.
* **Conditional Loop Branches**:
  * For a loop that runs 100 times, the branch might be Not Taken for 99 iterations (staying in the loop sequentially if the loop body is laid out linearly, or vice versa) and Taken once (exiting the loop).
  * With a perfect BHT, the BTB is accessed *only* on the iteration where the branch is predicted Taken.

### Indexing the BTB
Similar to the BHT, the BTB is indexed using the **lower bits of the instruction's address (PC)**. 
* Bits that are always the same (e.g., byte offset bits like the lowest 2 bits in a 32-bit architecture) are ignored.
* If a BTB has 4 entries, it requires exactly 2 bits to index. For example, an instruction at address `0xC008` (`1000` in binary) would use bits `[3:2]` to index into entry `2` (`10` in binary).

---

## 2. The Limits of the 1-Bit Predictor

A 1-bit predictor simply remembers the outcome of the last time a branch was executed. 
* `0` = Not Taken
* `1` = Taken

### The "Double Misprediction" Anomaly
While a 1-bit predictor works exceptionally well for long loops (e.g., a loop of 1000 iterations will only mispredict twice: once upon entering and once upon exiting), it fails dramatically when dealing with **anomalies** in heavily biased branches.

**Example Scenario**: A branch is heavily biased to be Taken (T). Occasionally, it is Not Taken (NT). 
**Pattern**: `T, T, T, T, NT, T, T, T`

**What the 1-bit predictor does:**
1. Sees `NT` (Anomaly) → **Mispredicts** (Expected `T`, got `NT`). State updates to `NT`.
2. Next execution is normal `T` → **Mispredicts again!** (Expected `NT`, got `T`). State updates back to `T`.

**Conclusion**: A single anomaly costs the 1-bit predictor **two mispredictions**. It also performs poorly on short loops (e.g., 8 iterations), as the constant switching at loop boundaries constantly pollutes the single bit of history.

---

## 3. The 2-Bit Predictor (2-Bit Counter)

To solve the double misprediction problem, hardware designers introduced the **2-Bit Predictor**, also known as a saturating counter. It adds a concept of *conviction* or *hysteresis*.

### State Machine & Intuition
The 2-bit predictor has 4 states:
* `00` - **Strong Not Taken** (Highly confident)
* `01` - **Weak Not Taken** (Slightly confident)
* `10` - **Weak Taken** (Slightly confident)
* `11` - **Strong Taken** (Highly confident)

*The most significant bit acts as the **Prediction Bit**, while the least significant bit acts as the **Conviction/Hysteresis Bit**.*

It behaves like a counter that saturates at 0 and 3:
* **Taken outcome**: Count UP (moves towards Strong Taken).
* **Not Taken outcome**: Count DOWN (moves towards Strong Not Taken).

### Solving the Anomaly Problem
If the predictor is in **Strong Taken (`11`)**:
1. An anomaly (`NT`) occurs: **Mispredicts**, but only drops to **Weak Taken (`10`)**.
2. Next execution is normal (`T`): **Predicts correctly** (since it was still in a Weak Taken state) and moves back to Strong Taken (`11`).

**Result**: A single anomaly now only costs **one misprediction**, effectively filtering out noise. Switching dominant behavior completely (e.g., from mostly Taken to mostly Not Taken) requires *two* consecutive opposing outcomes, meaning it takes slightly longer to learn a new pattern, but it prevents overreacting.

### Initialization Strategies
Where should the 2-bit predictor start?
* Starting in a **Weak State** (`01` or `10`) is theoretically safer if you guess wrong, as it takes fewer mispredictions to swing to the correct side. `10` (Weak Taken) is mathematically favored since branches are slightly more often Taken than Not Taken.
* However, in reality, initializing to **Strong Not Taken (`00`)** is the industry standard. Why? Because zeroing out memory (`00`) is trivially easy to implement in hardware, and the long-term penalty of starting in the wrong state is negligible over thousands of branch executions.

### Worst-Case Scenarios
Like all predictors, the 2-bit predictor has a sequence that causes a 100% misprediction rate. A malicious sequence can continuously shift the state back and forth across the weak threshold (e.g., `10` -> `01` -> `10`), mispredicting every single time. Fortunately, real-world programs rarely generate this specific adversarial pattern.

### Why not 3-Bit or 4-Bit Predictors?
If 2 bits are better than 1, why not 3?
* **Diminishing Returns**: A 3-bit counter only helps if anomalies consistently come in *streaks* (e.g., two anomalies in a row before returning to normal). In real-world code, this is extremely rare.
* **Hardware Cost**: Moving from 2 bits to 3 bits increases the memory footprint of the predictor by 50% without yielding a proportionate increase in accuracy. 2 bits is the "sweet spot" for balancing cost and performance.

---

## 4. History-Based Predictors

Simple counters (1-bit or 2-bit) fundamentally look for a "majority" behavior. But what if a branch doesn't have a majority behavior, but instead has a **perfectly predictable repeating pattern**?

**Example Pattern**: `Taken, Not Taken, Taken, Not Taken` (T-NT-T-NT)
* A 1-bit predictor will mispredict 100% of the time.
* A 2-bit predictor will constantly oscillate between weak states, mispredicting roughly 50% of the time.

To a human, the pattern is obvious: *If the last one was Taken, the next one is Not Taken.* 
This insight leads to **History-Based Predictors**.

### The 1-Bit History with 2-Bit Counters Predictor
Instead of tracking just the majority, this predictor learns *what to do based on recent history*.

**Architecture:**
1. **History Register**: A global or local bit that remembers the actual outcome of the *previous* branch (0 = NT, 1 = T).
2. **Array of Counters**: Instead of one 2-bit counter, the entry has *two* separate 2-bit counters. 
   * Counter A is used when History = 0.
   * Counter B is used when History = 1.

**How it Learns the T-NT Pattern:**
* When history is `0` (NT), the predictor uses Counter A. Since `NT` is always followed by `T` in our pattern, Counter A will quickly saturate to Strong Taken (`11`).
* When history is `1` (T), the predictor uses Counter B. Since `T` is always followed by `NT`, Counter B will quickly saturate to Strong Not Taken (`00`).

Once warmed up, when the processor sees a history of `0`, it perfectly predicts `T`. When it sees a history of `1`, it perfectly predicts `NT`. 

**The Power of History:**
By extending the history register (e.g., a 2-bit history tracking the last 2 outcomes, leading to 4 separate counters), predictors can learn highly complex, nested loop behaviors (like `NNT NNT NNT`). As long as the pattern repeats, history-based predictors can achieve near 100% accuracy on branches that would completely confuse simple bimodal predictors.

---

# Module 9: Advanced Branch Prediction - History-Based Predictors

## 1. Introduction: The Need for Branch History

In earlier modules, we explored simple 1-bit and 2-bit counters for branch prediction. While these work well for branches that are heavily biased (e.g., mostly taken or mostly not taken), they fail miserably when branches follow repeating patterns. 

**Background Context**: Real-world programs are full of patterns. For instance, a loop that executes exactly 3 times before exiting will have a branch pattern of `Taken, Taken, Not Taken` (`T, T, N`). If our hardware can recognize this pattern, we can achieve near-perfect prediction accuracy!

To do this, we introduce **History-Based Predictors**. These predictors remember the outcomes of recent branches and use that history to inform their next prediction.

---

## 2. 1-Bit vs. 2-Bit History Predictors

Let's evaluate how different history lengths perform on a simple repeating pattern: `N, N, T` (Not Taken, Not Taken, Taken).

### The 1-Bit History Predictor
A 1-bit history predictor only remembers the *last* branch outcome. 
- If the pattern is `N, N, T`, a history of `N` (0) is sometimes followed by `N` and sometimes followed by `T`.
- **Result**: The predictor gets confused. In 100 repetitions of the pattern (300 branches), it will mispredict exactly 100 times (1/3 of the time). It fails because 1 bit of history isn't enough context to distinguish which `N` we are currently at in the sequence.

### The 2-Bit History Predictor
A 2-bit history predictor remembers the last *two* outcomes. It has 4 possible histories (`00`, `01`, `10`, `11`), and a dedicated 2-bit counter for each.
- In the `N, N, T` pattern, the histories we encounter are:
  - `00` (N, N) → always followed by `T`.
  - `01` (N, T) → always followed by `N`.
  - `10` (T, N) → always followed by `N`.
- **Result**: After a brief warm-up period, this predictor will predict the pattern with **100% accuracy**.

**🧠 Mental Model: The $N+1$ Rule**
> An $N$-bit history predictor can perfectly predict any repeating pattern of length up to $N+1$. 
> - A 1-bit history perfectly predicts length 2 (e.g., `N, T, N, T`).
> - A 2-bit history perfectly predicts length 3 (e.g., `N, N, T`).

---

## 3. The Cost of Long History: An Exponential Problem

If longer history gives better accuracy, why not use a 16-bit history for every branch? 

**The Implementation Cost**:
A naive $N$-bit private history predictor stores the history *and* an array of 2-bit counters for *every single branch entry*. 
- Cost per branch = $N \text{ (history bits)} + 2^N \times 2 \text{ (counter bits)}$

If $N = 10$, a single branch entry requires $10 + (1024 \times 2) = 2058$ bits! Storing thousands of branch entries would require megabytes of dedicated SRAM, which is far too expensive for a CPU.

**The Wastefulness Problem**:
Not only is this expensive, but it's also incredibly wasteful. 
- Imagine an 8-iteration nested loop (pattern length 9). It requires an 8-bit history to predict the loop exit perfectly.
- An 8-bit history predictor gives us $2^8 = 256$ counters.
- However, the loop only ever generates 9 unique history patterns. 
- We end up using only 9 counters and **wasting the other 247 counters** (>96% waste).

How do we get the benefits of long history without the exponential cost and waste? Enter **Shared Counters**.

---

## 4. PShare: Private History with Shared Counters

**PShare** solves the exponential cost problem by decoupling the histories from the counters.

### How it Works:
1. **Pattern History Table (PHT)**: An array storing just the $N$-bit histories. Indexed by the Program Counter (PC). Every branch gets its own *private* history.
2. **Branch History Table (BHT)**: A single, global array of 2-bit counters shared by all branches.
3. **The XOR Hash**: To make a prediction, we take the branch's PC and **XOR** it with its private history. The resulting hash is used to index into the global BHT.

**Why this is brilliant**: 
Instead of allocating 256 counters to a branch that only needs 9, the branch simply hashes into the global pool 9 times. Branches that need more counters use more; branches that need fewer use fewer. 

**Cost Reduction**: 
Instead of scaling exponentially per branch, the BHT is a fixed size (e.g., $2^{11}$ counters). The only per-branch cost is the $N$-bit history itself. 

**Best Use Case**: PShare is fantastic for **self-correlated branches**, such as loop bounds, where a branch's future outcome depends heavily on its own past outcomes.

---

## 5. GShare: Global History with Shared Counters

While PShare tracks a private history for *each* branch, **GShare** tracks a single, global history across *all* branches.

### The Concept of Correlated Branches
Sometimes, a branch's outcome isn't tied to its own past, but to the outcomes of *other, recently executed branches*.

**Example**:
```c
if (shape == SQUARE) { ... }  // Branch A
// ... some generic code ...
if (shape != SQUARE) { ... }  // Branch B
```
If Branch A is taken, Branch B is guaranteed to be not taken. They are perfectly correlated. However, if you only look at Branch B in isolation, its behavior might look completely random depending on the data.

### How it Works:
1. **Global History Register (GHR)**: A single register that shifts in the outcome of every branch the CPU executes.
2. **The XOR Hash**: Just like PShare, GShare XORs the PC of the current branch with the Global History Register to index into the shared BHT of 2-bit counters.

**Best Use Case**: GShare excels at predicting **correlated branches** (e.g., dependent if-else statements).

---

## 6. The Tournament Predictor

We now have two powerful predictors:
- **PShare** (Private history) is best for loops and self-similar patterns.
- **GShare** (Global history) is best for correlated branches.

Which one should a CPU use? **Both.**

A **Tournament Predictor** runs multiple predictors in parallel and uses a "Meta Predictor" to decide which one to trust for a given branch.

### How the Meta Predictor Works:
- The Meta Predictor is another array of 2-bit counters, indexed by the PC.
- Instead of predicting "Taken" or "Not Taken", the Meta Predictor predicts **"Trust PShare" or "Trust GShare"**.

### Training the Meta Predictor:
When the actual branch outcome is resolved, the Meta Predictor is updated based on which sub-predictor was correct:
- If **GShare is correct** and PShare is wrong: Decrement the counter (bias towards GShare).
- If **PShare is correct** and GShare is wrong: Increment the counter (bias towards PShare).
- If **both are right** or **both are wrong**: Do nothing (no clear winner).

**Intuition**: The Meta Predictor dynamically learns the "personality" of each branch. If a branch is a loop, the Meta Predictor will quickly learn to route its predictions to PShare. If it's a correlated `if` statement, it will route it to GShare. This hybrid approach gives the CPU the best of both worlds.


---

