import sys

file_path = '/Users/bytedance/Documents/repos/github/omscs-notes/hpca/trae-notes/04_Predication/04_Predication.md'

with open(file_path, 'r') as f:
    content = f.read()

replacements = [
    (
        "**Optimal Combination:** Use a **Hierarchical Predictor** that chooses between the 2-bit predictor and a **Tournament Predictor**. The Tournament Predictor, in turn, chooses between P-share and G-share for the remaining 5% of complex branches.\n\n---",
        "**Optimal Combination:** Use a **Hierarchical Predictor** that chooses between the 2-bit predictor and a **Tournament Predictor**. The Tournament Predictor, in turn, chooses between P-share and G-share for the remaining 5% of complex branches.\n\n### 🧠 Dense Enrichments: Hierarchical Predictors\n- **Mental Model (Triage):** Think of a hospital emergency room. The Okay Predictor is the triage nurse handling 95% of standard cases (colds, minor cuts). The Good Predictor is the specialized trauma surgeon. You don't waste the surgeon's time (limited expensive predictor entries) on a cold (a highly predictable branch).\n- **Tradeoff (Latency/Power vs. Accuracy):** Why not just make the Good Predictor massive? *Cycle time.* A massive global history table cannot be indexed and read in a single cycle at 4+ GHz. Hierarchical design buys time and saves power.\n- **Confusion (Warmup Time):** A highly complex predictor takes longer to \"learn\" a pattern (warmup) than a simple 2-bit counter. If a branch executes infrequently, the Good Predictor might actually perform *worse* because it never fully warms up.\n\n---"
    ),
    (
        "**Why Wraparound is better:** Programs typically have a \"main\" function that calls functions, which call smaller functions, which call even smaller functions (leaf functions). The smallest functions are called the most frequently. Wraparound sacrifices the prediction of the large, long-running functions (like returning to `main`) to correctly predict the thousands of returns from the small, deeply nested functions. This minimizes the total number of mispredictions.\n\n---",
        "**Why Wraparound is better:** Programs typically have a \"main\" function that calls functions, which call smaller functions, which call even smaller functions (leaf functions). The smallest functions are called the most frequently. Wraparound sacrifices the prediction of the large, long-running functions (like returning to `main`) to correctly predict the thousands of returns from the small, deeply nested functions. This minimizes the total number of mispredictions.\n\n### 🧠 Dense Enrichments: Return Address Stack (RAS)\n- **Mental Model (Theseus and the Minotaur):** The RAS is the ball of string Theseus unspools to navigate the maze. Every `CALL` drops string; every `RET` rewinds it exactly to the last intersection.\n- **Tradeoff (Context Switches):** What happens to the RAS during a thread context switch? Saving and restoring the RAS to memory is slow. OSes often just clear/ignore it, leading to transient return mispredictions right after a context switch.\n- **Confusion (BTB vs. RAS):** \"Why doesn't the Branch Target Buffer (BTB) handle returns?\" The BTB maps a single instruction address (PC) to a *single* target. But a `RET` instruction's target changes dynamically based on who called it (1-to-N mapping). The RAS handles temporal 1-to-N mappings perfectly.\n\n---"
    ),
    (
        "   - Pre-decoding is also used to identify instruction length (for variable-length ISAs like x86) and general branch identification, saving power and time during the critical execution pipeline.\n\n---",
        "   - Pre-decoding is also used to identify instruction length (for variable-length ISAs like x86) and general branch identification, saving power and time during the critical execution pipeline.\n\n### 🧠 Dense Enrichments: Pre-decoding\n- **Mental Model (Mail Sorting):** Pre-decoding is like a mailroom clerk stamping \"URGENT\" or \"INTERNATIONAL\" on an envelope before handing it to the actual department. The pipeline (department) instantly knows how to route it without reading the whole letter.\n- **Tradeoff (Cache Bloat vs. Pipeline Speed):** Adding pre-decode bits (e.g., expanding 32-bit instructions to 33 or 36 bits) physically inflates the L1 Instruction Cache by ~3-10%, costing valuable silicon area. The payoff is a shorter critical path in the decode stage, allowing higher clock speeds.\n- **Confusion (Pre-decode vs. Decode):** Pre-decoding happens *outside* the main pipeline, typically during the cache fill from L2 to L1i. Normal decoding happens *inside* the pipeline. Pre-decoding doesn't execute anything; it just annotates.\n\n---"
    ),
    (
        "3. **Extra Instructions:** You must execute explicit `MOVZ`/`MOVN` instructions just to select the correct results.\n\n---",
        "3. **Extra Instructions:** You must execute explicit `MOVZ`/`MOVN` instructions just to select the correct results.\n\n### 🧠 Dense Enrichments: Conditional Moves\n- **Mental Model (The Eager Chef):** You don't know if a customer wants a burger or a hotdog. Instead of waiting to ask (branching), you cook *both* (execute both paths). When they order, you hand them the right one and throw the other in the trash.\n- **Tradeoff (Fetch Bandwidth vs. Flush Penalty):** Conditional moves waste ALU cycles and fetch bandwidth on the wrong path. If the branch is 99% predictable, branching is far superior because you don't waste resources cooking the meal that gets thrown away.\n- **Confusion (Sequential vs. Parallel):** \"Does the CPU execute both paths simultaneously?\" Not necessarily. In a scalar processor, it executes them sequentially. The key benefit isn't parallelism; it's the *guarantee of no pipeline flushes*.\n\n---"
    ),
    (
        "- **Conclusion:** If the branch predictor is less than **97.5% accurate** (100% - 2.5%), Full Predication is faster!\n\n---",
        "- **Conclusion:** If the branch predictor is less than **97.5% accurate** (100% - 2.5%), Full Predication is faster!\n\n### 🧠 Dense Enrichments: Full Predication\n- **Mental Model (The Master Switchboard):** Imagine a factory assembly line where every worker has a red/green light above their station (Predicate Register). The worker still builds the part, but if their light is red, the final inspector throws the part in the bin instead of attaching it.\n- **Tradeoff (ISA Bloat vs. Register Pressure):** Conditional moves (CMOV) cause high register pressure because you need temporary registers to hold both path results. Full predication avoids this, but suffers from ISA bloat: *every* instruction must permanently sacrifice 3-4 bits of its encoding space just to specify a predicate register (e.g., Intel Itanium).\n- **Confusion (Power Consumption):** Predicated instructions whose predicates are false still consume power! They are fetched, decoded, and often sent to ALUs. They just don't write back to architectural state. Predication saves *time* (no flushes) but often burns more *power*.\n\n---"
    )
]

new_content = content
for old, new in replacements:
    if old not in new_content:
        print(f"Failed to find target for replacement: {old[:50]}...")
        sys.exit(1)
    new_content = new_content.replace(old, new)

with open(file_path, 'w') as f:
    f.write(new_content)

print("Successfully injected enrichments.")
