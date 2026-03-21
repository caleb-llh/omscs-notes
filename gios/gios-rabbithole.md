# Notes and prompts for CS6200 - GIOS
> Aim is to understand which level of abstraction are the concepts being applied to (hardware, kernel, process, kernel-level thread, user-level thread), and how mechanisms works across the levels, the design patterns built on top, and the tradeoffs involved, and metrics to measure them.

### Computer architecture and kernel
- Paradigm shift from software to hardware logic (sequential, abstract logic to parallel, physical, and state-based logic) What are the mechanisms to bridge the two paradigms?
- Explain the CPU as a state machine? How does it go from continuous, asynchronous, analog to discrete, synchronous and digital? Why must it be digital and synchronous?
- How many percent of CPU time is allocated for kernel? 
  > - Without a hardware timer, a process could run forever and never give up the CPU and context switch would never occur. What's running in parallel to a CPU core is another CPU core, I/O devices, and hardware timers, and they can generate interrupts to the CPU core.
  > - CPU switches to kernel mode primarily via interrupts(async) and traps(sync).
- How is the cache address mapped to memory address if the memory address space is significantly larger?
- How do computers with different CPU clock cycles synchronize on time? why not just increase clock speed so that all tasks are never CPU-bound?
- How are these hardware involved during context switch: TLB, MMU, Cache, CR3, GPRs, RIP, RSP? Why is TLB involved in the biggest cost? Why is the Stack Pointer (RSP) essential, and is its necessity related to referencing local variables using offsets?
  > - RSP is crucial because local variables and function arguments are almost always referenced by offsets relative to the stack frame base or the RSP.
- Difference between hardware/software interrupts, traps, system calls, faults, signals? Is the interrupt handler part of the kernel logic or is it hardware logic? 
    > - Trap: Synchronous, from software processes.
    > - Interrupts: Asynchronous, from hardware devices. Handled by interrupt handlers in the kernel. Interrupt number (hardware defined) is used to find the right handler (specific to OS) in the Interrupt Descriptor Table (IDT).
    > - Signals: Asynchronous, from software processes. Handled by signal handlers in user space. Signal numbers (OS defined) are used to identify the signal type, to find the right handler (specific to process) in the process's signal handler table. Threads within the same process share the same signal handler table, but each thread can have its own signal mask.
- How do computers with different CPU clock cycles synchronize on time? why not just increase clock speed so that all tasks are never CPU-bound? What are the trade-offs between using a high clock speed vs multiple cores for improving performance?



### Processes and threads
> Process: Resource ownership. Threads: Execution context.
- When I run `ps aux` or `lsof`, does the shell program make a system call to the kernel to scrape all the PCBs? `fork` vs `exec` under the hood? 
- For multi-core architecture, are there task "stickiness" implemented? Why not just make time slice as large as possible - what's the tradeoff here? Are schedulers and the dynamic calculation run only during context switch or in the background? Are ready queues specific to each CPU core, or is there a global ready queue shared among all cores? How does this design choice impact load balancing and context switching?
-  Why are Page Tables typically structured like a tree, and does each process have its own independent tree? Why is the list of PCBs stored using a doubly-linked list rather than a contiguous array? Are page tables stored in PCB or in a separate structure?
-  Cost (creation, context switch, blocking, communication) and complexity(synchronization, multi-processor) tradeoffs between processes, KLTs and ULTs? What use cases are best suited for each?
- do threads share heap but not stack? Why is one of the most costly parts of context switching between processes is remapping the VA space?
- Why is context switching faster for ULT compared to KLT? shouldn't KLT context switch be faster since it's lower level? Can a ULT be mapped to a different KLT each time it runs, considering typically threads are stateful -  or are all of the state encapsulated in the thread data structure?
- What do ULTs, KLTs, processes and kernel share and not share? Why context switch speed of ULT > KLT > Process?
Where do these data structures live: PCB, TCB, Page tables? What's the impact of PCB/TCB Design on User-Level Libraries? What does context switch look like for many-to-many model?
    > - The PCB/TCB is read and written only during a context switch, and at that moment, it receives and holds the most current execution state of the outgoing thread, ready for the next time it runs. 
    > - The M:N model aims to keep the frequent switches on the Fast Path (ULT-to-ULT) while using the Slow Path (KLT-to-KLT) only when necessary to achieve parallelism or handle blocking I/O.
    > - KLT is a scheduled entity running in user mode. ULT is just a passive logical construct managed by a user-level library.
-  SunOS: How does LWP fit into the whole picture of the kernel, process, KLT, ULT, CPU? Why LWP Visibility is Necessary for Kernel Decisions?
-  Why does I/O block the KLT, not just the ULT? If a ULT is blocked on I/O, can the KLT switch to another ULT in the same process?
-  Do ULTs have TCBs associated? (Yes, but in user space. Kernel only has TCB of associated KLT) Does ULT stack and registers actually live in the heap of the process, as compared to KLT?
-  why are mode switches/traps and kernel data structure manipulation expensive? Why is M:N considered more memory-efficient when both ULTs and KLTs require stacks? Why would we revisit custom threading policies (like M:N) for super large-scale processing today, given 1:1 works well? What are the kernel's inherent limitations in extreme concurrency?
- Why is IPC cheaper between threads? buffer vs channels vs pipes vs message queue? are inter-thread communication almost always using shared memory? do mutex and condition variables use shared memory (user space)?

### Concurrency and synchronization
> - **Mutexes** enforces ownership of a resource. **Semaphores** enforces capacity of a resource. **Condition variables** enforces ordering like a wait list.
All rely on atomic operations.
> - Principles to maximize concurrency and minimize contention: 
>   - Keep synchronization critical sections as short as possible. 
>   - Keep locks fine-grained. Shard data structures and use separate locks for each shard where possible.
>   - Keep global lock ordering.
> - Isolation and synchronization are fundamentally at odds with each other. The more isolated an execution context is (higher overhead), the less it needs to synchronize with other threads (lower complexity), and vice versa.

> - Modern operating systems use Symmetric Multiprocessing (SMP), meaning any CPU core can run any part of the kernel or any thread of any process. This means that all kernel data structures must be protected by synchronization mechanisms.
> - i.e. Conceptually, a single multi-core machine is a distributed system. While they share a single physical memory unit, the cores are autonomous units that operate with their own private caches and instruction pipelines. This creates a need for explicit coordination that mirrors challenges in a network of computers:
>   - **Communication**: Cores must communicate via shared memory and the bus interface.
>   - **Coordination**: Synchronization primitives are required to maintain consistency (like distributed consensus algorithms).
>   - **Coherence**: The Cache Coherence Protocol (MESI, MOESI) is the built-in hardware protocol that enforces consistency, essentially solving the "shared state" problem that is difficult in true distributed systems.

> - Classic synchronization problems: Producer-Consumer, Readers-Writers, Dining Philosophers, Sleeping Barber, Cigarette Smokers.

> In writer-readers pattern, you have two different critical sections: 
    > - **Synchronization** critical section - Protects the shared metadata used for decision-making (resource_counter, conditional variables). Mutex is locked. Concurrency is Exclusive: Only one thread can be modifying the counters at a time
    > - **Data Access** critical section - The actual data being protected. Mutex is unlocked. Concurrency is Shared: Shared (Readers) or Exclusive (Writers), managed by the counter logic.

- Illustrate the Lost wakeup problem, spurious wakeup problem, deadlock, livelock, starvation - how do you avoid them?
- Do synchronisation primitives live in user or kernel space or in hardware - how do you synchronise across the different levels of concurrency/parallelism? How are atomic operations guaranteed in multiprocessor systems?

### Concurrency/parallelism models
> - Event-driven model: the processing of multiple requests are interleaved within a single execution context.

> - IO-bound workloads: Multithreading - If the amount of time a thread will spend idle is greater than the time it takes to context switch twice, it makes sense to context switch and let some other thread do some work. Event-driven - a request will be processed exactly until a wait is necessary, at which point the execution context will switch to servicing another request.
> - CPU-bound workloads: Multithreading/multiprocessing for true parallelism. Multi-processing for fault isolation.

- Data vs task parallelism, and its tradeoffs in relation to latency vs throughput?
- Where do they fit in Flynn's taxonomy - boss-worker, pipeline, event-driven, map-reduce?
- event dispatcher vs kernel scheduler - preemptive vs cooperative multitasking? how does epoll enable event-driven model?
- What are the classes of workloads that benefit from each model and complexities that arise from multi-CPU systems? SPED vs AMPED vs MT/MP boss-worker vs pipeline models for cache-bound vs disk-bound vs CPU-bound workloads?
- How is the right level of granularity determined for tasks in task parallelism - effects of management/synchronisation overhead and data locality?
- Thread scaling: If you ran your server from the class project for two different traces: (i) many requests for a single file, and (ii) many random requests across a very large pool of very large files, what do you think would happen as you add more threads to your server? Can you sketch a hypothetical graph?
  > - Cached / Single File (CPU-Bound):	If a thread is always running, adding more threads than cores means the CPU must interrupt (switch) threads just to share time. Overhead goes up, performance flatlines.
  > - Disk-Bound / Large Files (I/O-Bound)	Disk I/O	If a thread blocks often (waiting for the disk), the CPU is idle. You must add many extra threads to ensure the CPU always has a ready thread to run. Context switching is the necessary cost of hiding latency.
- pros and cons of CPU affinity for multithreaded tasks?
- If I have 10000 concurrent requests, either I have 10000 thread control blocks holding the state of the RPC (multi-threaded synch grpc) or I have 10000 messages in my CQ holding the state of the RPC (event-driven async RPC), either way there is memory overhead, no?

# Scheduling
> - Metrics to evaluate scheduling algorithms: Throughput, Completion time, Waiting time, CPU Utilization.
> - Throughput and CPU Utilization are closely related, but their distinction matter because CPU utilization does not penalise context switching overhead. CPU Utilization measures BUSY time, while Throughput measures PRODUCTIVE time.
> - Completion time and Waiting time are closely related, but their distinction can matter e.g. wait time is more relevant for interactive systems, while completion time is more relevant for batch systems.
> - Inherent trade-off between the benefits of short timeslices (better responsiveness) and the overhead of frequent context switching. The ideal quantum must be large relative to the context switch time, but small enough to ensure good responsiveness.
> - In general, I/O bound interactive tasks benefit from smaller time slices (quanta) to ensure low latency and high device utilization, so they are given higher priority.
> - CPU-bound tasks benefit from larger quanta to reduce context switching overhead, so they are given lower priority. For CPU-bound tasks that are still regarded as high priority (e.g. time-sensitive tasks), you set a lower nice value to prevent starvation. 
> - To determine the nature of a task, MLFQ uses feedback (yield vs preemption) to classify tasks as I/O-bound or CPU-bound, and adjusts their priority accordingly.
> - Linux O(1) Scheduler: A complex, priority-based scheduler (140 levels - lower is better) designed for O(1) (constant time) task selection, using active and expired arrays and adjusting priorities based on time spent sleeping (feedback)

- How would you categorize different scheduling algorithms (FCFS, SJF, Priority, Round Robin, Multilevel Queue, Multilevel Feedback Queue) and the metrics (throughput, turnaround time, waiting time, response time, fairness) used to evaluate them? Scheduling concerns for CPU-bound vs I/O-bound workloads, batch vs interactive systems?
- preemption vs scheduling vs context switching vs interrupt - how are these terms related to each other? what are the common inherent tradeoffs between these metrics: throughput, average job completion time, average job wait time, and CPU utilization
- How does the CPU clock and hardware timer and interrupts work together to enable preemptive multitasking?
- Why is MLFQ implemented as an array of DLLs? How are operations like blocking, priority review, aging, promotion, demotion, and time quantum enforcement implemented efficiently, are they all constant time? How does MLFQ handle starvation of lower-priority queues? What problems do active and expired queues solve, when you can just re-queue in O(1) too? Does the O(1) review the priority of every task each time the hardware timer interrupts... how does aging happen? How do CPU-bound and I/O-bound processes behave differently in MLFQ? Does each CPU core have its own MLFQ, or is there a global MLFQ shared among all cores? How does this design choice impact load balancing and context switching?
- Why does CFS use a red-black tree for its run queue instead of a binary heap or BST? Why are arbitrary removal from RBT necessary? How does CFS ensure fairness among processes with different priorities and CPU burst characteristics? When is vruntime updated? How does CFS handle I/O-bound vs CPU-bound processes differently? What are the trade-offs between CFS and MLFQ in terms of responsiveness, throughput, and complexity? How does CFS scale with increasing numbers of processes and CPU cores? How does per-CPU run queue and CPU affinity reduce contention and improve cache locality but could lead to load imbalance/starvation? How does load balancing work between CPU cores in CFS?


# Memory management
- why do gaps exist even with demand paging? why can't flattened page tables handle sparse address spaces efficiently? addressing for cache lines vs pages vs frames vs segments vs disk blocks? parallels between hashmaps and page tables?
- what do TLBs actually contain and used in multi-level page tables? is it O(1) and how? how is cache coherence maintained across multi-core TLBs? why is there generally high temporal and spatial locality in memory references?


## Interprocess communication
- why is creating shared memory mapping relatively expensive? how is it different from normal memory allocation? how does the kernel manage shared memory regions between processes?

# SMP synchronisation
> - atomic instructions (usually involving bundling read and conditional write) protects against concurrent race conditions (within a core), mutual exclusion (enforced by a single gatekeeper/SSOT in shared memory) protects against parallel race conditions (across cores) - by forcing operations to be serialised through the memory controller, but leads to contention.
> - write-invalidate benefit from write amortization - multiple writes to the same cache line can be done in the cache before invalidating other caches. but floods the memory bus to fetch new data during high contention. preferable for write-heavy workloads and constrained memory bandwidth (high contention not the common case).
> - a test_and_set instruction often results in an invalidation event, even if the underlying lock value remains the same (i.e., it's already locked). that's why test-and-test-and-set is preferred - it first reads the lock value (which can be done from cache without invalidation) and only issues a test_and_set (which causes invalidation) if the lock appears to be free.
> - problem about spinlocks is mainly the contention they generate on the memory bus and cache. spin-on-read lock + delays help to reduce memory access/contention. queueling locks reduce contention by distributing the waiting threads across multiple cache lines resulting in O(1) overhead per lock acquisition under high contention.
> - cache coherence strategy and cache write policies are hardware properties, while synchronisation primitives are kernel or application properties built on top of them.

- cache coherence: how does no-write/write-through/write-back relate to write-invalidate/write-update strategy relate to CC and NCC architectures - which are hardware vs kernel vs application properties? why does write-invalidate result in O(N^2) memory references to maintain cache coherence for test_and_test_and_set? wouldn't delay still lead to O(N^2) cascading invalidations because all N threads would eventually read the same cache line? 
- performance metrics: tradeoffs between latency vs delay/waiting time vs contention?


# I/O management
> - DMA and PIO are mechanisms for data transfer between devices and memory. Memory-mapped IO and IO port model are two different methods for the CPU to communicate with devices. All of them are primarily determined by hardware and are abstracted by device drivers in the kernel, which provide a uniform interface to user-space processes.
> - Inodes solve the problem of file fragementation and metadata storage. Dentries solve the problem of mapping human-readable file names to inodes and slow path traversal. Superblocks solve the problem of managing filesystem-wide metadata and consistency. They serve the same purpose in distributed file systems, but with additional considerations for consistency models/coherence protocols.

- Put these concepts on a table: PCIe, memory-mapped IO, IO port model, controllers/drivers, PIO, DMA, OS bypass, synchronous/asynchronous IO, polling/interrupts, blocking/non-blocking IO, epoll vs select vs poll - what are the mechanisms at each layer (hardware, kernel, process) that enable these concepts? what are the tradeoffs involved?
- Is DMA, PIO, memory-mapped IO and IO port model determined by the hardware or OS? Do inodes, dentries and superblocks play a different role when the file system is distributed?
- How does the size of an inode determine the size of the file?

## Virtualization
> - virtualization abstracts away hardware: the CPU (instruction set architecture), memory (virtual address space via TLB and MMU), storage (virtual disks/volumes), network (virtual NICs, virtual switches/routers).

> - Cambridge University's Xen: Type 1 hypervisor, uses service VM/domain (dom0) for hardware management and device drivers, paravirtualization, guest VM/domain (domU), hypercalls, privileged instructions trapped to hypervisor, para-virtualized drivers in guest OS for I/O performance.
> - VMware ESX (legacy): Type 1 hypervisor, uses service console VM for hardware management, full virtualization.
> - VMware ESXi (modern): Type 1 hypervisor (VMM), no service VM, direct hardware access, all device drivers and management agents run in dedicated low-level kernel modules.
> - Microsoft Hyper-V: Type 1 hypervisor, uses parent partition (host OS) for hardware management, child partitions (guest VMs), uses hardware virtualization extensions, synthetic drivers for I/O performance.
> - Linux KVM module: Type 2/hybrid hypervisor, full virtualization, uses hardware virtualization extensions (Intel VT-x, AMD-V), QEMU for device emulation, IBM's VirtIO paravirtualized drivers (split-driver model) for I/O performance.
> - Sun/Oracle's VirtualBox: Type 2 hypervisor, uses hardware virtualization extensions, paravirtualized drivers for I/O performance.
> - Docker: OS-level virtualization, uses container engine (docker daemon) to manage containers, shares host OS kernel, uses namespaces and cgroups for isolation and resource management.
> - LXC: OS-level virtualization, uses Linux kernel features (namespaces, cgroups) for containerization, shares host OS kernel.

- what are the software and hardware mechanisms that enable virtualization at different levels of abstraction? e.g. running a docker container inside a VM: process, docker daemon, guest OS, hypervisor, host OS, hardware - what are the layers of abstraction and mechanisms at each layer that enable this? how do these differ between full virtualization, paravirtualization, OS-level virtualization, type 1 vs type 2 hypervisors?
- are VM exits/entries part of the trap-and-emulate mechanism - are they at the same level? VM vs process scheduling/context switching, system calls, interrupts? does the hardware differentiate between a VM exit caused by an interrupt vs a trap vs a hypercall vs a system call from the guest OS? what is the difference between hardware emulators, hardware extensions, hardware drivers, paravirtualized drivers?
- Put them on a table: Xen, KVM, VMware, Hyper-V, VirtualBox, Docker, LXC.
- how does caching work in VMs? Where are the page tables located? Are MMU and TLB aware of virtualization? how does nested page tables work?
- are passthrough/hypervisor-direct/split-device-driver model determined by the hardware platform or the hypervisor?
- how does nested virtualization work, how does processor, memory, device virtualization look like vs single-level virtualization?


### Remote Procedure Call (RPC)


## Distributed File Systems
> - Files and directories often have different semantics because of different access patterns and usage scenarios. Files are typically read and written sequentially, while directories are accessed randomly to look up file names. This leads to different design considerations for caching, locking, and consistency.
> - DFS design must consider network latency, bandwidth, fault tolerance, scalability, and consistency models.
> - coherence focuses on a single piece of data across the system, while consistency focuses on the ordering of all memory operations across all processors

- What are the parameters that a DFS design can have, and the tradeoffs associated with them? e.g. client-side caching, write-back vs write-through, stateless vs stateful, cache coherence protocols, consistency models? Put them on a table with examples of real-world DFS (NFS, AFS, HDFS, GFS, Ceph, Lustre, etc) and their design choices.


### Distributed Shared Memory
- Consistency models: what does strict, sequential, causal and weak consistency enable for the applications, and how does the underlying implementation differ?
- How do memory management and device IO concepts come together in DSM design?
- Is the DSM layer implemented in hardware, OS kernel, or as a device driver?


### Datacenter Technologies


<br></br>
---
# Formulas

### Useful Work during scheduling
> Useful work is the fraction of total time that is spent doing actual processing (as opposed to scheduling overhead).
>
> $useful\_work = {total\_processing_time \over total\_time}$
>
> Or, $useful\_work = {(N * T~p~) \over ((N * T~p~) + (N * T~sched~))}$

### Pipeline 
> $T ≈ (Time~to~fill~pipeline~)+(N * Time~of~slowest~stage)$
> 
> The speedup of a pipelined architecture is given by:
> 
> $Speedup = {T~non-pipeline~ \over T~pipeline~} = {N * T~stage~ \over (k + N - 1) * T~stage~} = {N \over k + N - 1}$
> where:
> - N = number of tasks
> - k = number of pipeline stages
> - T~stage~ = time taken by the slowest stage

### Scheduling
Throughput Formula:
jobs_completed / time_to_complete_all_job

Avg. Completion Time Formula:
sum_of_times_to_complete_each_job / jobs_completed

Avg. Wait Time Formula:
(t1_wait_time + t2_wait_time + t3_wait_time) / jobs_completed