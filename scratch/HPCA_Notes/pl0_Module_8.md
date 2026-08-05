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