# HPCA Module 3: Performance Comparison and Benchmarks

Welcome to Module 3! In this module, we explore how to measure, compare, and summarize computer performance. We also introduce the foundational "Iron Law of Performance," which will guide our understanding of processor design throughout the course.

---

## 1. Performance Comparison and Speedup

**Background Context**  
When building or buying a new computer, we want to know: *How much better is it?* To quantify improvements, we compare the performance of a new system against a baseline (the old system). 

The primary metric for this is **Speedup**.

### Calculating Speedup
Performance is inversely proportional to execution time (latency) and directly proportional to throughput. Therefore, speedup can be calculated in two ways:
- **Using Latency (Execution Time):** `Speedup = Old Latency / New Latency`
- **Using Throughput:** `Speedup = New Throughput / Old Throughput`

### Interpreting Speedup (Mental Model)
Think of speedup as answering: *"How many times faster is the new system?"*
- **Speedup > 1**: The new system is faster (improved performance).
  - *Example*: An old laptop takes 4 hours (240 mins) to compress a video. A new laptop takes 10 mins.  
    `Speedup = 240 / 10 = 24`. The new laptop is 24x faster.
- **Speedup < 1**: The new system is slower (performance degradation).
  - *Example*: If we accidentally use the old laptop instead of the new one.  
    `Speedup = 10 / 240 = 0.04`. This is an actual slowdown.
- **Sanity Check**: If you expect the new system to be faster but calculate a number lower than 1, you likely divided the numbers backwards! Always divide *Old Latency* by *New Latency*.

---

## 2. Measuring Performance & Benchmarks

**The Problem**  
To compare two machines, what software should we run? Ideally, we'd run a user's exact daily workload. However, collecting this data is difficult, and one user's workload rarely represents everyone else's.

**The Solution: Benchmarks**  
Benchmarks are agreed-upon programs and input data used specifically for performance measurements. They act as a standardized measuring stick.

### Types of Benchmarks
1. **Real Applications**
   - **What it is**: Full, real-world software (e.g., a web browser, a database).
   - **Pros**: The most representative of actual real-world usage.
   - **Cons**: Extremely difficult to set up on a new, unreleased machine that might not yet have a full operating system or drivers.
2. **Application Kernels**
   - **What it is**: The most time-consuming core part of a real application (often an isolated mathematical loop).
   - **Pros**: Uses actual code from real applications but is much easier to run than the full software.
   - **Cons**: Misses some system-level interactions that the full application would have.
3. **Synthetic Benchmarks**
   - **What it is**: Abstract code specifically designed from scratch to mimic the behavior of real kernels.
   - **Pros**: Very simple to compile and run. Excellent for early design studies and prototyping.
   - **Cons**: Not representative enough for reporting final performance to customers.
4. **Peak Performance**
   - **What it is**: Theoretical maximum instructions per second based purely on hardware specs.
   - **Pros**: Easy to calculate.
   - **Cons**: Rarely achieved in practice. Mostly used for marketing rather than representing true performance.

### Benchmark Standards and Suites
A **benchmark suite** groups multiple programs to represent a variety of applications. Consortiums of companies and academics standardize these suites:
- **TPC**: Used for databases, web servers, and transaction processing.
- **EEMBC**: Used for embedded systems (cars, phones, printers).
- **SPEC**: Used for engineering workstations and raw processors. SPEC is highly processor-oriented (CPU-intensive) and includes applications like GCC (compilers), fluid dynamics, physics simulations, and AI.

---

## 3. Summarizing Performance

**The Problem**  
If a benchmark suite has 26 different applications, how do we combine their results into a single number to say "Machine X is overall N times faster than Machine Y"?

### Arithmetic vs. Geometric Mean
- **Arithmetic Mean** is used for averaging raw execution times.
  - *Example*: `(Time A + Time B + Time C) / 3`
- **Geometric Mean** must be used for averaging **Speedups (ratios)**.
  - *Rule of Thumb*: NEVER use an arithmetic mean on ratios. Because speedups are relative fractions, an arithmetic average mathematically skews the result. 
  - *Formula*: Multiply the individual speedups and take the N-th root: `Geometric_Mean = (S1 * S2 * ... * Sn)^(1/n)`
  - *Example*: 
    - App 1 Speedup = 2x
    - App 2 Speedup = 8x
    - Incorrect (Arithmetic): `(2 + 8) / 2 = 5`
    - Correct (Geometric): `sqrt(2 * 8) = 4`. The overall average speedup is 4x.
  - *Insight*: The geometric mean of individual speedups equals the speedup calculated from the geometric means of the raw execution times.

---

## 4. The Iron Law of Performance

**Mental Model**  
To make a processor faster, we need to know exactly where the time goes. The Iron Law breaks down total CPU execution time into three fundamental, actionable components.

### The Formula
`CPU Time = (Instructions / Program) × (Cycles / Instruction) × (Seconds / Cycle)`

Let's break down the three components and see what influences them:

1. **Instructions per Program**
   - *What it is*: The total number of machine instructions executed to finish the program.
   - *Influenced by*: The algorithm, the compiler, and the Instruction Set Architecture (ISA).
   - *Trade-off*: A complex instruction set (CISC) might do more work per instruction, requiring *fewer* total instructions than a simple instruction set (RISC).
2. **Cycles per Instruction (CPI)**
   - *What it is*: The average number of clock cycles it takes to execute one instruction.
   - *Influenced by*: The ISA and the Processor Design (Microarchitecture).
   - *Trade-off*: Complex instructions often take many cycles to complete. Simple instructions can often be done in 1 cycle (or less, using advanced pipelining).
3. **Clock Cycle Time (Seconds per Cycle)**
   - *What it is*: The physical duration of one clock tick (inversely related to Clock Rate, e.g., 3 GHz).
   - *Influenced by*: Processor Design, Circuit Design, and Transistor Physics.
   - *Trade-off*: If a processor tries to do too much work in a single cycle, the cycle time must be stretched out (slower clock rate). 

### Balancing the Iron Law
A good computer architecture balances these three factors. For example, you can build a processor with an incredibly high clock rate (low Seconds/Cycle), but if it requires spending many more cycles per instruction (high CPI), the overall CPU Time might not improve. 

**Example Calculation:**
- **Instructions**: 3 Billion
- **CPI**: 2 cycles per instruction
- **Clock Rate**: 3 GHz (which means 3 Billion cycles per second, so Cycle Time = `1 / (3 × 10^9)` seconds)
- **CPU Time** = `3×10^9` * `2` * `1 / (3×10^9)` = **2 seconds**.
