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
