# High-Performance Computer Architecture - Module 4: Advanced Out-of-Order Execution & Memory Ordering

## 1. Timing and Commit in the ROB (Quiz Solution Context)
*(Context: In a Reorder Buffer (ROB) based Out-of-Order (OoO) processor, instructions must issue in order, execute out of order, and commit in order. A processor often has a bandwidth limit on how many instructions it can process per cycle.)*

**Key Takeaways:**
* **Resource Contention at Issue:** An instruction cannot issue if the required Reservation Station (RS) is full. For example, if all Add/Sub reservation stations are occupied, the next Add/Sub instruction must wait, stalling the issue stage.
* **Parallel Execution & Broadcast:** Instructions utilizing different execution units (e.g., a Multiplier and an Adder) can begin execution in the exact same cycle. They can also broadcast their results in the same cycle, provided there are enough broadcast buses (Common Data Buses) available.
* **Commit Rate:** The commit stage processes instructions strictly in program order. If a processor has a commit limit (e.g., up to two instructions per cycle), it will retire the oldest completed instructions first. If the oldest instruction is not yet finished, the commit stage stalls. If multiple are finished, they commit together up to the hardware bandwidth limit.

## 2. Unified vs. Separate Reservation Stations
**Background:** Reservation Stations hold instructions that have been issued but are waiting for their data operands to arrive before they can execute.

* **Separate Reservation Stations:** Each execution unit (e.g., Adder, Multiplier) has its own dedicated RS array. 
  * *The Bottleneck:* If a program has a burst of Add instructions, the Add RS fills up. Because the issue stage operates strictly in-order, a full Add RS will stall the entire pipeline from issuing further, even if the Multiply RS is completely empty and idle.
* **Unified Reservation Stations:** All execution units share a single, large pool of reservation stations.
  * *The Advantage:* Vastly improved resource utilization. We can continue to issue instructions as long as *any* RS entry is available in the unified pool, eliminating artificial stalls.
  * *The Drawback:* Hardware complexity. The dispatch logic must look across the entire unified pool every single cycle to find ready instructions, match them to their specific execution units (e.g., route an Add to the Adder, a Mul to the Multiplier), and handle contention if multiple instructions are ready for the same unit simultaneously.
  * *Industry Reality:* True unified reservation stations are extremely expensive to build in hardware. Modern processors typically use a hybrid approach—clustering groups of functional units together to share a local pool of reservation stations, rather than being fully separate or entirely unified.

*Intuition / Mental Model:* Think of separate reservation stations as dedicated checkout queues at a grocery store (e.g., cash only, card only). If the cash queue is full, cash buyers block the entrance, even if the card queue is empty. A Unified RS is like a single "bank queue" where everyone waits in one line and the person at the front goes to the next available teller of the correct type.

## 3. Superscalar Processors
**Background:** A scalar processor handles one instruction per cycle (IPC $\le$ 1). A true superscalar processor attempts to handle multiple instructions per cycle (IPC > 1).

To achieve superscalar performance, the processor must widen *every* stage of its pipeline. The weakest link dictates the overall throughput.
* **Fetch:** Must fetch multiple instructions (bytes) from memory per cycle.
* **Decode:** Requires multiple parallel decoders to handle the fetched stream.
* **Issue:** Must check and allocate RS/ROB entries for multiple instructions simultaneously. Because issue is in-order, if the 1st instruction stalls, the 2nd and 3rd must also stall.
* **Dispatch:** Requires an adequate ratio of execution units (e.g., 2 Adders, 1 Multiplier) so multiple instructions can begin execution simultaneously.
* **Broadcast:** Needs multiple Result Buses. **Note:** This drastically increases RS complexity because every single RS must monitor *all* buses simultaneously to capture matching tags. The hardware cost of an RS scales heavily with the number of broadcast buses.
* **Commit:** Must be able to check and retire multiple instructions from the ROB per cycle, strictly in order.

*Mental Model:* A superscalar pipeline is like a pipe system with varying widths. If fetch is 4-wide, decode is 4-wide, but issue is only 1-wide, the maximum sustained throughput of the entire processor is severely bottlenecked to 1 instruction per cycle. The narrowest point dictates the flow.

## 4. Terminology Confusion (Industry vs. Academia)
Computer architecture nomenclature varies heavily between the original Tomasulo academic papers, subsequent research, and industry documentation (like Intel or ARM manuals).

| Logical Stage | Academic / Tomasulo Term | Alternative Terms Used in Industry/Papers |
| :--- | :--- | :--- |
| **Stage 1 (Allocation)** | Issue | Allocate, Dispatch |
| **Stage 2 (Execution Prep)** | Dispatch | Execute, Issue, Dispatch |
| **Stage 3 (Finalization)** | Commit | Complete, Retire, Graduate |

*(Note: The term "Complete" is particularly confusing. An instruction physically "completes" execution and broadcasts its result long before it is officially "committed" to architectural state. However, some literature uses Complete to mean Commit.)*

## 5. What is *Actually* "Out of Order"?
Despite the umbrella term "Out-of-Order Execution," an OoO processor executes many of its stages strictly in program order to maintain program correctness and precise state (for exceptions).

* **In Order:** Fetch, Decode, Issue. (Instructions enter the processor strictly as written in the code).
* **Out of Order:** Dispatch, Execute, Broadcast / Write-Result. (Instructions execute dynamically whenever their data dependencies are met).
* **In Order:** Commit. (Instructions leave the processor and update the permanent architectural state in program order, creating the illusion that everything happened sequentially).

## 6. Memory Access Ordering (Loads and Stores)
**The Problem:** Register dependencies are explicitly tracked via renaming and the ROB. However, memory dependencies are implicit—they are determined by the actual memory addresses computed at runtime. 
* *When does a memory write happen?* Stores **must** write to memory at **Commit**. Writing to memory prematurely is unsafe because a branch misprediction or an exception would require "undoing" the memory write, which is nearly impossible.

### The Load-Store Queue (LSQ)
Since stores are delayed until commit, loads would theoretically have to wait a long time to read updated data from memory. To prevent loads from stalling, processors use a Load-Store Queue (LSQ).
* The LSQ holds Load and Store instructions in program order.
* **Store-to-Load Forwarding:** When a Load computes its memory address, it checks the LSQ for any older Stores targeting that same address. If a match is found, the Load grabs the value directly from the Store inside the LSQ instead of going to memory.

### Handling Unresolved Store Addresses
What happens if a Load computes its address, but an older Store in the LSQ *hasn't computed its address yet*? (We don't know if they will collide).

1. **In-Order Load/Store (Safe but Slow):** Loads wait until ALL previous instructions complete. This stalls the pipeline terribly, especially on cache misses.
2. **Wait for Store Addresses (Moderate):** The Load waits only until all older Stores compute their addresses. Once the addresses are known, the Load checks for collisions and proceeds.
3. **Go Anyway / Speculative Execution (Aggressive, Modern Standard):** The processor boldly assumes there is no collision and sends the Load to memory immediately. 
   * *Success Scenario:* If the older Store eventually computes a different address, we saved a massive amount of time by not waiting.
   * *Failure Scenario (Memory Ordering Violation):* If the older Store eventually computes the *same* address, our Load fetched stale data from memory. The processor must flush the pipeline and re-execute the Load and all subsequent instructions. Modern processors use sophisticated prediction schemes to guess if a collision is likely, avoiding costly flushes.

*Mental Model:* The LSQ is the processor's "scratchpad" for memory. We don't publish writes to the official ledger (RAM) until we are 100% sure the instruction isn't going to be squashed (Commit). But if we need to read what we *just* wrote to our scratchpad, we read it from there directly (Store-to-Load Forwarding) without waiting for the official ledger. If someone is writing something to the scratchpad but we don't know the exact address yet, we can either wait for them to finish, or aggressively guess they aren't writing over our data and read the official ledger anyway.
