# High Performance Computer Architecture (HPCA)
## Playlist 2, Module 6: Compiler Instruction Scheduling, Loop Unrolling, and Function Inlining

---

## 1. Compiler Instruction Scheduling

### Background Context & Intuition
While hardware techniques like Tomasulo's algorithm dynamically reorder instructions at runtime (out-of-order execution), **compiler instruction scheduling** is a *static* approach. The compiler analyzes the code before it runs and explicitly reorders instructions in the binary to minimize pipeline stalls. This is especially critical for simpler in-order processors that cannot look ahead dynamically.

**Mental Model:** Think of the processor's pipeline as an assembly line. When one station has to wait for parts (a stall due to data dependence), the whole line pauses. The compiler acts as the factory planner, finding other independent tasks that can be done during that wait time so the workers (execution units) are never idle.

### The Mechanism
The core idea is to find independent instructions and move them into the stall slots caused by long-latency operations (like memory loads).

**Example Scenario:**
Consider a single loop iteration processing an array:
1. `LD R2, 0(R1)`  *(Load array element)*
2. `ADD R2, R2, R0` *(Modify element)*
3. `ST R2, 0(R1)`  *(Store element)*
4. `ADDI R1, R1, 4` *(Advance pointer)*
5. `BNE R1, R_END, Loop` *(Branch if not end)*

If a load takes 2 cycles (requiring a 1-cycle stall if used immediately), the processor must stall before the `ADD`. 

**Compiler Solution:**
The compiler can move the pointer update (`ADDI`) into the stall slot between `LD` and `ADD`, because `ADDI` doesn't depend on the loaded value in `R2`.
*Crucial Adjustment:* If we advance the pointer `R1` *before* the store instruction uses it, the store will write to the wrong address (it would write to the next element). The compiler compensates by adjusting the store's offset. 

**New Schedule:**
1. `LD R2, 0(R1)`
2. `ADDI R1, R1, 4` *(Executes during the load stall!)*
3. `ADD R2, R2, R0`
4. `ST R2, -4(R1)` *(Compensated offset by -4 to match original address)*
5. `BNE R1, R_END, Loop`

This simple reordering eliminates stall cycles and significantly speeds up the loop without changing the program's logic.

---

## 2. Scheduling and If-Conversion

### The Branching Bottleneck
The compiler's ability to schedule is limited by branches. A compiler cannot easily move an instruction past a branch because it doesn't know which execution path will be taken at runtime. These small branch-delimited chunks of code are called "basic blocks," and small blocks mean fewer opportunities to find independent instructions to fill stalls.

### Synergy with Predication
**If-Conversion** transforms control dependencies (branches) into data dependencies (predicated instructions). 
- Instead of an `if-then-else` block with branches, all instructions from both paths are included sequentially, but they only commit their results if their condition (predicate) is true.

**The Scheduling Benefit:**
By eliminating branches, if-conversion merges small basic blocks into one large, branch-free block. The compiler now has a much larger "window" of instructions to analyze. It can take a predicated instruction from the `else` path and use it to fill a stall cycle in the code that precedes the `if` statement. Thus, if-conversion not only avoids branch misprediction penalties but also supercharges the compiler's instruction scheduling capabilities.

---

## 3. Loop Unrolling

### Background Context & Intuition
If-conversion is great for `if` statements, but it doesn't work for loops. A loop has a dynamic number of iterations; if-converting a loop would require a massive, impractical number of predicates, and executing thousands of false-predicated instructions would be incredibly slow. Instead, compilers use **Loop Unrolling** to enlarge the scheduling window for loops.

**Mental Model:** Instead of fetching one item, processing it, and checking your list, you grab two or four items at once, process them all, and then check your list. You spend less time walking back and forth (loop overhead).

### The Mechanism
Loop unrolling combines multiple iterations of a loop into a single, larger iteration.
- **Unrolling *Once*:** Doing the work of **2** iterations per loop. (You add 1 extra iteration to the original body).
- **Unrolling *Twice*:** Doing the work of **3** iterations per loop.

**Adjustments Required:**
When unrolling, the compiler must carefully adjust the code so it doesn't just compute the exact same thing twice:
1. **Memory Offsets:** If iteration 1 accesses `0(R1)`, iteration 2 must access `4(R1)`.
2. **Loop Counter/Pointer:** The pointer must be advanced by the total amount processed per unrolled loop. If unrolling once (2 elements), a 4-byte pointer advances by 8 bytes at the end of the loop.
3. **Register Renaming:** To prevent data hazards (like overwriting the first load's value before using it), the compiler uses different registers for the independent calculations of the second iteration.

### The Benefits
1. **Reduced Loop Overhead:** The branch instruction and the loop counter update are executed less frequently. If a loop originally executed 1000 times, unrolling once drops it to 500 times, eliminating 500 branch and 500 pointer update instructions.
2. **Increased ILP (Instruction-Level Parallelism) and Lower CPI:** By fusing loop bodies, the compiler creates a huge, branch-free block of code. 
   * *Example:* On a 4-issue processor, an unrolled loop allows the compiler to schedule the load for iteration 1 and the load for iteration 2 to execute in the *exact same cycle*. This drastically lowers the Cycles Per Instruction (CPI). Combining fewer total instructions with a lower CPI results in a massive performance boost.

### The Downsides
1. **Code Bloat:** The compiled binary size grows linearly with the unroll factor. Excessive unrolling increases the instruction footprint, potentially causing instruction cache misses that negate the performance gains.
2. **Fringe Iterations:** If a loop needs to run 7 times, and you unroll it to process 4 items per loop, the final 3 iterations must be handled separately by a "cleanup" or "fringe" loop, complicating the generated code.

---

## 4. Function Call Inlining

### Background Context & Intuition
Similar to how loop unrolling removes loop overhead by expanding the loop body, **Function Call Inlining** removes function call overhead by expanding the function call.

**Mental Model:** Instead of calling a specialist to your desk (which takes time to explain the problem and get their result), you simply learn their 3-step process and do it yourself directly in your workflow.

### The Mechanism
The compiler replaces the `CALL` instruction with the actual body of the target function. It maps the caller's arguments directly to the registers used in the function body, bypassing the standard calling convention.

### The Benefits
1. **Elimination of Call/Return Overheads:** We completely remove the `CALL` and `RETURN` instructions. We also eliminate the overhead of pushing/popping arguments to the stack or shuffling them into specific argument registers (like `A0`, `A1`).
2. **Enhanced Scheduling:** Inlining merges distinct code blocks (caller and callee) into one continuous block. The compiler can now interleave the caller's surrounding code with the callee's internal instructions. 

**Example Walkthrough:**
* **Without Inlining:** 
  1. `LD A0` (Load arg) 
  2. `CALL func` (2 cycles)
  3. `MUL` (Inside func, 3 cycles) 
  4. `ADD` (Inside func, 1 cycle) 
  5. `RET` (2 cycles)
  6. `ST` (Store result). 
  *Total: ~10 cycles (due to call/return overhead and strict execution boundaries).*
* **With Inlining:** The `CALL` and `RET` disappear. The `MUL` and `ADD` are placed directly after the `LD`. The compiler can schedule the `MUL` immediately once the `LD` finishes.
  *Total: ~7 cycles.*

### The Downsides
1. **Code Bloat:** If a function is called from 100 different places, inlining it copies its body 100 times into the binary. 
*Rule of Thumb:* Compilers are very judicious with inlining, restricting it to small, frequently called functions (like getters/setters or simple math helpers) where the call overhead is high relative to the actual work, and the resulting code bloat is minimal. As functions get larger, the cost of replication outweighs the benefits of removing the call overhead.

---

## 5. Summary & Key Takeaways
- **Static Scheduling:** Compilers move independent instructions into stall slots to keep the pipeline busy. Offset compensation is often required when moving pointer updates.
- **Enlarging the Scheduling Window:** Compilers need large blocks of branch-free code to schedule effectively. 
  - **If-Conversion** eliminates branches inside `if-else` blocks.
  - **Loop Unrolling** eliminates loop-back branches, fusing multiple iterations.
  - **Function Inlining** eliminates function calls, fusing caller and callee.
- **The Core Trade-off:** All these techniques trade binary size (code bloat) for execution speed (ILP and reduced overhead).
