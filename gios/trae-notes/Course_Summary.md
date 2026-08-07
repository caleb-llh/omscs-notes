# Graduate Introduction to Operating Systems (GIOS): Course Overview

## Introduction
An Operating System (OS) is the foundational layer of systems software that sits between raw physical hardware and high-level applications. Its primary mandate is to manage complex hardware resources securely and efficiently while providing simple, robust abstractions for applications. 

This course explores the continuous tension between **software abstraction** and **hardware reality**. We want the abstraction of seamless, infinite concurrency and memory, but hardware imposes strict limits: context switches consume CPU cycles, caches pollute, and memory buses clog. By the end of this course, you will understand how modern operating systems balance these tradeoffs—from local thread scheduling and memory management, all the way up to distributed cloud datacenters. A recurring design principle throughout these topics is the strict separation of **Mechanism** (the "how", such as context switching) from **Policy** (the "what", such as the scheduling algorithm) to build flexible, modular systems.

---

## Core Themes and Conceptual Framework

### 1. Execution Abstractions: Processes and Threads
The OS acts as both an *illusionist* and a *referee*. It provides each application with the illusion of endless memory and a dedicated CPU, while strictly isolating them to ensure security and fairness.
* **OS Protection Boundaries:** To enforce isolation, the OS relies on hardware support for dual-mode execution (User vs. Kernel mode). Applications run in unprivileged User mode and must use **System Calls** or hardware **Traps** to safely transition to Kernel mode when they require privileged OS services.
* **Processes:** A process is an isolated execution environment—the actual act of running a program. The OS manages this isolation via Process Control Blocks (PCBs) and virtual memory address spaces. However, switching between processes is expensive due to the overhead of saving registers and flushing CPU caches.
* **Threads:** To achieve high concurrency without the massive overhead of process switching, OSes use threads. Threads are independent execution contexts (each with its own stack) that live within the *same* process address space. You will study the tradeoff between User-Level Threads (fast, managed by libraries) and Kernel-Level Threads (OS-aware, true parallelism), and how they are mapped together using structures like Lightweight Processes (LWPs).
* **Concurrency Models:** You will explore how highly concurrent, I/O-bound applications (like Web Servers) are designed. You will contrast multi-threaded patterns (Boss/Worker, Pipeline) with the highly efficient **Event-Driven Architecture** (using `epoll`/`select`), which multiplexes requests within a single thread to completely avoid context-switch overhead.

### 2. Concurrency Control and Scheduling
When multiple threads share memory, the OS must provide hardware-backed synchronization constructs to prevent data corruption.
* **Synchronization Constructs:** You will learn how Mutexes, Condition Variables, and Semaphores are used to protect critical sections. Crucially, you will look under the hood to see how these rely on hardware atomic instructions (like `test_and_set`), and how naive Spinlocks can crush multiprocessor performance by generating massive cache-coherence bus traffic. You will also learn about **Deadlocks**, how to avoid them using strict lock ordering, and the challenges of hardware interrupts.
* **CPU Scheduling:** The OS must decide which thread runs next. You will explore the evolution of schedulers, from simple FCFS algorithms to Linux's **Completely Fair Scheduler (CFS)**. You will also learn how modern schedulers prioritize **Cache Affinity** and **NUMA-awareness** to keep data close to the executing CPU on multi-core architectures.

### 3. Resource Management: Memory and I/O
The OS decouples physical hardware from the software interface, providing a unified, virtualized environment.
* **Memory Management:** The OS uses Virtual Memory to give processes the illusion of contiguous memory. You will learn how the OS and hardware collaborate using **Hierarchical Page Tables** and the **Translation Lookaside Buffer (TLB)** to map virtual addresses to physical RAM on the fly. You will also explore lazy allocation strategies like Demand Paging and Copy-on-Write.
* **Inter-Process Communication (IPC):** Because processes are isolated, they must communicate intentionally. You will contrast **Message Passing** (safe but slow due to OS data copying) with **Shared Memory** (incredibly fast, but requires developers to manually manage synchronization).
* **I/O Management:** The OS translates the myriad of hardware devices into a unified abstraction via the **Virtual File System (VFS)**. You will explore how the OS aggressively masks the agonizing slowness of physical disks using buffer caches, I/O scheduling, and prefetching. Furthermore, you will contrast how the CPU physically interacts with these devices using **Interrupts** vs. **Polling**, how **Direct Memory Access (DMA)** frees the CPU from manually copying bytes (PIO), and how **OS Bypass** maps device registers directly into user space for extreme performance.

### 4. Scaling Out: Distributed Systems
When problems exceed the capacity of a single machine, the OS principles extend to distributed clusters over a network.
* **Remote Procedure Calls (RPC):** RPC abstracts the complexity of network transmission, allowing developers to execute functions on remote servers as if they were local calls. You will understand how stubs marshal and unmarshal data across machine boundaries.
* **Distributed File Systems (DFS) & Shared Memory (DSM):** You will explore how the OS creates the illusion of local storage and shared RAM across isolated nodes. Designing these systems is a delicate compromise between performance and consistency, heavily relying on caching, relaxed consistency models, and OS-level memory traps.

### 5. The Cloud Era: Datacenters and Virtualization
The course concludes by examining how these OS concepts enable the modern cloud computing era.
* **Virtualization:** Instead of multiplexing hardware for applications, the Hypervisor (Virtual Machine Monitor) multiplexes hardware for *entire operating systems*. You will explore Type 1 and Type 2 hypervisors, and how hardware-assisted virtualization (Intel VT-x) allows Guest OSes to run natively on the CPU, only trapping to the hypervisor for privileged operations.
* **Datacenter Technologies:** You will understand how virtualization enables the economic viability of the cloud, transforming raw physical servers into elastic, fungible utilities that can be dynamically provisioned to handle multi-tier internet services and Big Data analytics frameworks.

### Conclusion
Graduate Introduction to Operating Systems provides the structural vocabulary required to understand everything from a single smartphone processor to a global AWS datacenter. By studying the intricate dance between software abstractions and hardware limits, you will emerge with the architectural intuition necessary to design robust, high-performance systems.