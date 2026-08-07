# Module 6: Pipeline Hazards, Branching, and Branch Prediction

## 1. Dependencies vs. Hazards

**Background Context & Mental Model:**
Imagine a kitchen where multiple chefs are preparing a complex meal. 
- A **dependence** is a rule in the recipe: "You must chop the onions before you can fry them." It is a fundamental property of the recipe (the program) itself.
- A **hazard** occurs when the kitchen's workflow (the pipeline) risks breaking that rule. For example, if Chef A is chopping onions and Chef B tries to grab them to fry before Chef A is finished, a hazard occurs. 

**Key Definitions:**
- **Dependencies:** A property of the **program alone**. They dictate the logical order of operations (e.g., an `ADD` instruction produces a result in register `R1`, and a subsequent `SUB` instruction needs to read `R1`).
- **Hazards:** A property of the **pipeline implementation**. A dependence only becomes a hazard if the pipeline design allows a dependent instruction to read a register *before* the preceding instruction has finished writing to it.

**Example:**
```assembly
ADD R1, R2, R3   ; Writes to R1
SUB R4, R1, R5   ; Reads from R1
DIV R6, R1, R7   ; Reads from R1
```
In a 5-stage pipeline, `SUB` might attempt to read `R1` in the Decode stage while `ADD` is still in the Execute/ALU stage (not yet written to `R1`). This dependence is a **hazard**. However, by the time `DIV` reads `R1`, `ADD` might have already finished and left the pipeline. In that case, the dependence between `ADD` and `DIV` is **not a hazard**.

---

## 2. Handling Hazards: Flushes, Stalls, and Forwarding

When a hazard is detected, the pipeline cannot simply produce incorrect results. It must resolve the hazard to ensure correct execution. There are three primary mechanisms to do this:

### A. Flushing (For Control Hazards)
- **When to use:** Control hazards (e.g., Branches).
- **Intuition:** If a branch condition evaluates differently than we expected, we have fetched the wrong instructions into the pipeline. Trying to delay them won't help because they are simply the *wrong* instructions.
- **Action:** Delete (flush) the incorrectly fetched instructions from the pipeline and start fetching the correct ones from scratch.

### B. Stalling (For Data Hazards)
- **When to use:** Data hazards where forwarding isn't enough (e.g., Load-Use hazards).
- **Intuition:** Sometimes the required data simply hasn't been computed or fetched from memory yet.
- **Action:** Pause (stall) the dependent instruction in its current stage (e.g., the Decode stage) until the required value is finally written to the register.

### C. Forwarding / Bypassing (For Data Hazards)
- **When to use:** Data hazards where the value has been computed in the pipeline but hasn't reached the final Register Write stage.
- **Intuition:** Instead of waiting for a worker to put a finished part into the storage bin (register file) just for the next worker to take it out, hand the part directly to the next worker.
- **Action:** Route the output of an earlier pipeline stage (e.g., ALU output) directly back to the input of a previous stage (e.g., ALU input) so the dependent instruction can compute with the correct value without stalling.
- **Preference:** We **prefer forwarding** over stalling because forwarding does not introduce wasted cycles (bubbles) into the pipeline.

### Load-Use Hazard Example (Stall + Forward)
If a `LOAD` instruction reads memory into `R1`, and the very next instruction `ADD` needs `R1`, forwarding alone isn't enough. The `LOAD` doesn't get the data until the end of the Memory stage, but the `ADD` needs it at the beginning of the ALU stage (which happens simultaneously). 
- **Solution:** We must **stall** the `ADD` instruction for one cycle. After that one cycle stall, the data is available from the `LOAD`, and we can then **forward** it to the `ADD`.

---

## 3. How Many Pipeline Stages? (Pipeline Depth)

**Intuition:** If pipelining increases throughput, why not have a 100-stage or 1000-stage pipeline to achieve incredibly high clock speeds?

The Iron Law of Performance dictates:
`Execution Time = Instructions × CPI × Cycle Time`

**The Trade-off of Adding More Stages:**
1. **Cycle Time Decreases (Pros):** Less work is done per stage, meaning the clock frequency can be much faster. This reduces execution time.
2. **CPI Increases (Cons):** A deeper pipeline means more instructions are in flight simultaneously. When a hazard occurs (like a branch misprediction), the penalty is much larger. For example, a branch resolved in stage 3 causes 2 flushed instructions, but a branch resolved in stage 15 causes 14 flushed instructions. These penalties increase the average CPI.

**Optimal Pipeline Depth:**
- **For Performance Only:** If we only cared about maximum performance, the optimal depth is typically around **30 to 40 stages**. This is where the cycle time improvements perfectly balance out the CPI degradation from hazard penalties.
- **For Power Efficiency (Reality):** Every pipeline stage requires hardware latches to hold intermediate values. More stages = more latches = exponentially more power consumption and heat. 
- **Conclusion:** Modern processors typically use **10 to 15 stages** to balance good performance with manageable power consumption.

---

## 4. Branching in a Pipeline

**Background:** 
A branch instruction (e.g., `BEQ R1, R2, Label`) compares two registers. 
- If the condition is **met (Taken)**, it adds an immediate offset to the Program Counter (PC) to jump to the `Label`.
- If the condition is **not met (Not Taken)**, the PC simply increments (e.g., PC + 4) to the next sequential instruction.

**The Pipeline Problem:**
In a pipeline, the processor fetches a new instruction every single cycle. However, a branch instruction might not resolve its condition and target address until the 3rd or 4th stage (e.g., the ALU stage). 

**What do we fetch in the meantime?**
1. **Wait and Fetch Nothing (Stall):** If we refuse to guess and fetch nothing until the branch is fully resolved, we guarantee pipeline bubbles (wasted cycles) for *every* branch, taken or not.
2. **Make a Prediction:** If we guess what the branch will do:
   - **Correct Guess:** 0 penalty. The pipeline flows seamlessly.
   - **Incorrect Guess (Misprediction):** We must flush the incorrectly fetched instructions, resulting in a multi-cycle penalty.

**Conclusion:** It is always better to make a prediction (even a simple one) than to stall and wait. A two-cycle penalty *some* of the time is better than a two-cycle penalty *all* of the time.

---

## 5. Branch Prediction Requirements and Accuracy

To successfully keep the pipeline full, a branch predictor must look at the current PC being fetched and instantly predict:
1. Is this instruction a branch?
2. If so, is it Taken or Not Taken?
3. If Taken, what is the Target PC?

In practice, this boils down to one primary question: **Is this a Taken Branch?** (If not, we just fetch the next sequential instruction, PC + 4).

### Impact of Predictor Accuracy on CPI
The performance of a pipeline with branching can be calculated as:
`CPI = Ideal CPI + (Mispredictions per instruction × Misprediction Penalty)`

Where:
- `Mispredictions per instruction = (Branch frequency) × (Predictor misprediction rate)`
- `Misprediction Penalty = Pipeline stages between Fetch and Branch Resolution`

**Key Insight:** A better branch predictor improves performance for any processor. However, **deeper pipelines have much higher misprediction penalties** (e.g., a 9-cycle penalty vs. a 2-cycle penalty). Therefore, deeper pipelines are far more dependent on highly accurate branch predictors to maintain good performance. This is why research into advanced branch prediction is still highly active today.

---

## 6. Static Prediction: Predict "Not Taken"

The simplest form of branch prediction is the **"Not Taken" prediction**. 

- **How it works:** The processor assumes every instruction (branch or not) will simply fall through to the next sequential instruction (PC + 4). 
- **Why it's beneficial:** It is incredibly cheap to implement in hardware. You don't need to know anything about the instruction being fetched; you just increment the PC.
- **Performance:** 
  - For non-branch instructions: Always correct (1 cycle cost).
  - For Not-Taken branches: Correct prediction (1 cycle cost).
  - For Taken branches: Misprediction (incurs the flush penalty).
- **Takeaway:** Even this rudimentary prediction strategy significantly outperforms a policy of "wait until we are sure."

---

## 7. Multiple Mispredictions (Shadow of a Misprediction)

**Mental Model:** What happens if you take a wrong turn while driving, and while on that wrong road, you make *another* wrong turn based on a bad map? Once you realize your *first* mistake and teleport back to the original intersection, the second mistake no longer matters—it was erased from reality.

**Scenario:** 
Imagine the processor fetches `Branch 1`, mispredicts it, and starts fetching instructions down the wrong path. One of those incorrectly fetched instructions is `Branch 2`. The processor also mispredicts `Branch 2` and fetches even more wrong instructions.

**The Cost:** 
How many penalties do we pay? **Only one.**

**Reasoning:**
When `Branch 1` finally resolves in the ALU stage, the processor realizes the first mistake. It immediately **flushes the entire pipeline**. 
Because `Branch 2` was fetched *after* `Branch 1`, it is still sitting in an earlier pipeline stage (e.g., Decode) when the flush occurs. `Branch 2` is destroyed before it ever reaches the ALU stage to trigger its own flush. Therefore, you only pay the penalty for the earliest mispredicted branch. The subsequent mispredicted branches in its "shadow" are canceled for free.