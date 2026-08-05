# GPU Architecture and Programming: Course Overview

## Introduction
The breakdown of Dennard Scaling and the onset of the "Power Wall" forced a fundamental shift in computer architecture. As traditional CPUs reached their physical limits for sequential execution frequency, the industry turned to massively parallel architectures to sustain performance scaling. 

This course explores the transition from latency-optimized processors (CPUs) to throughput-optimized processors (GPUs). Rather than relying on deep caches and complex control logic to execute a single thread as quickly as possible, GPUs utilize thousands of simpler cores to execute millions of threads concurrently. By the end of this course, you will understand the hardware realities of modern GPUs, the programming models required to harness them, and the architectural innovations driving the modern artificial intelligence boom.

---

## Core Themes and Conceptual Framework

### 1. The Paradigm of Throughput Computing (Modules 1-4)
Traditional CPU programming is bound by Amdahl's Law, which warns that sequential bottlenecks limit the maximum possible speedup of a program. GPU programming is instead governed by **Gustafson's Law**: as compute capacity grows, we do not simply solve the same problem faster; we solve significantly larger problems. 

You will learn how GPUs achieve this massive throughput by utilizing **zero-overhead context switching**. Unlike a CPU, which relies on Out-of-Order execution and branch prediction to hide memory latency, a GPU hides latency through sheer concurrency. When one group of threads stalls waiting for data, the hardware instantly swaps in another group, keeping the computational engines continuously fed. You will explore how APIs like CUDA map this concurrency directly to physical hardware via the Thread Block and Grid hierarchy.

### 2. Managing the SIMT Execution Model (Modules 5-6)
To maximize silicon area dedicated to pure computation, GPUs group threads into "Warps" that execute in lock-step, following a Single Instruction, Multiple Threads (SIMT) model. 

This architectural choice introduces a unique challenge: **Warp Divergence**. You will explore what happens when threads within a warp take different conditional paths (e.g., an `if-else` statement). The course details how the hardware utilizes a SIMT stack and predicated execution to serialize these diverging paths, and how software engineers must actively design algorithms to avoid these branching penalties. You will also cover **Register Virtualization**, understanding how GPUs manage immense register files to keep thousands of threads active simultaneously.

### 3. Virtual Memory & Performance Modeling (Modules 7-8)
Applying CPU concepts directly to GPUs often fails due to the scale of multithreading. You will explore the unique challenges of **GPU Virtual Memory**, where a single uncoalesced memory access could trigger 32 simultaneous TLB misses per warp, requiring large pages and Unified Virtual Address (UVA) spaces to prevent memory controller collapse.

You will also learn how to diagnose bottlenecks using the **Roofline Model**—a visual framework that plots Performance (GFLOPs) against Arithmetic Intensity (FLOPs/Byte). This tool instantly reveals whether a kernel is Compute-Bound (requiring instruction optimization) or Memory-Bound (requiring caching/coalescing optimization). Additionally, the course contrasts CPU schedulers with GPU **Warp Schedulers** (like Greedy-Then-Oldest) which preserve cache locality.

### 4. The Compiler Pipeline and Data Flow (Modules 10-11)
Writing code for a machine that rapidly evolves across hardware generations requires a unique compilation strategy. You will explore the dual-compilation pipeline, distinguishing between the virtual instruction set (**PTX**) and the physical machine code (**SASS**). 

The course delves into compiler optimization techniques, teaching you how compilers use Intermediate Representations (IR), Static Single-Assignment (SSA) forms, and Control Flow Graphs (CFGs) to analyze code. You will understand how static analysis tools track the lifespan of variables (**Live-Variable Analysis**) to perform aggressive register allocation—a critical necessity in a machine that must recycle physical registers for thousands of concurrent threads.

### 5. Scaling Out: Multi-GPU and Datacenter Architecture (Module 9)
As single monolithic chips reach their manufacturing limits, architecture must scale outward. The course covers the hardware and software mechanisms used to connect multiple GPUs into cohesive supercomputers.

You will explore interconnect technologies like **NVLink** and **GPUDirect RDMA**, which allow GPUs to bypass the host CPU and communicate directly across PCI boundaries and network interfaces. You will also build an intuition for **Non-Uniform Memory Access (NUMA)**, learning how to schedule thread blocks and allocate memory pages to minimize the latency of "far" memory accesses. Finally, the module covers multi-tenant concurrency techniques (Streams, MPS, MIG) used to maximize utilization in modern cloud datacenters.

### 6. The Engine of Machine Learning (Module 12)
The final module connects the fundamental principles of GPU architecture to the specific demands of Deep Learning. 

You will examine the transition from general-purpose SIMD instructions to dedicated machine learning hardware, such as **Tensor Cores** and **Systolic Arrays**, which execute entire matrix multiplications in a single hardware instruction. Finally, the course covers the profound impact of **Quantization**—demonstrating how intentionally reducing floating-point precision (from FP32 down to FP16 or FP8) drastically reduces memory bandwidth bottlenecks, effectively doubling computational throughput for AI workloads without fundamentally altering the underlying compute engines.