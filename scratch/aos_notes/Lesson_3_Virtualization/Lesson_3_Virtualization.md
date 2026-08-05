# Lesson_3_Virtualization (Synthesized Notes)

# Module 8: Virtualization

## Introduction
- **Evolution of OS Design**: The drive for extensibility in operating system services led to innovations in the internal structure of operating systems and the dynamic loading of modules.
- **Virtualization**: Takes the vision of extensibility to a new level by allowing the simultaneous coexistence of entire operating systems on top of the same hardware platform.

## Contexts of Virtualization
The term "virtualization" appears across various computing and cultural contexts:
- **Virtual Memory Systems**
- **Data Centers & Cloud Computing** (e.g., AWS, Microsoft)
- **Virtual Machines**: Java Virtual Machine (JVM), Dalvik (Android)
- **Desktop/Workstation Virtualization**: VirtualBox, VMware Workstation
- **Historical/Pioneering Systems**: IBM VM 370 (the "mother of all virtualization" from the 1960s/70s)
- **Pop Culture & Tech Hype**: Google Glass, the movie *Inception*

## Platform Virtualization
- **Virtual Platforms**: An operating system running on top of some hardware that provides the illusion of an exclusive platform.
- **Motivation (Alice Inc. vs. Bala Inc.)**: 
  - *Alice Inc.* can afford dedicated physical servers.
  - *Bala Inc.* wants the exact same capabilities and abstractions but at a fraction of the cost. Virtual platforms provide this experience.
- **User Perspective**: Users treat the virtual platform as a black box; they only care that their applications run correctly.
- **Designer Perspective**: Operating system designers focus on providing the illusion of a dedicated platform without incurring the associated hardware acquisition and maintenance costs.

## Utility Computing
- **Resource Sharing**: Multiple user communities (e.g., Bala, Piero, Kim) share the same underlying hardware resources.
- **Bursty Usage**: Individual resource usage (like memory) is typically very bursty. By combining multiple users, the cumulative usage pattern smooths out.
- **Cost Efficiency**:
  - Buying dedicated hardware requires purchasing for peak usage (plus a safety margin).
  - A shared virtual machine pools resources, providing a total capacity larger than any individual's needs.
  - The costs of acquiring, maintaining, and upgrading hardware are collectively shared among users.
- **Utility Model**: Similar to electricity and water utilities, data centers provide computing resources on a shared, rental basis. Users gain access to massive resources at a fraction of the individual cost.
- **Connection to Extensibility**: Virtualization is extensibility applied at the granularity of an entire operating system (rather than individual OS services like in SPIN or Exokernel).

## Hypervisors (Virtual Machine Monitors)
- **Definition**: An "operating system of operating systems" that manages hardware sharing and protection. Often referred to as a **Virtual Machine Manager (VMM)** or **Hypervisor**.
- **Guest OS / Virtual Machine (VM)**: The operating systems running on top of the shared hardware. *(Note: In this context, VM stands for Virtual Machine, not Virtual Memory).*
- **Types of Hypervisors**:
  - **Type 1: Native (Bare-Metal) Hypervisor**:
    - Runs directly on top of the bare hardware.
    - Guest operating systems are clients of this hypervisor.
    - Interferes minimally with guest OS operations, offering the best performance (conceptually similar to Exokernel).
  - **Type 2: Hosted Hypervisor**:
    - Runs as an application process on top of a host operating system.
    - Guest OSes emulate functionality through this host.
    - Examples: VMware Workstation, VirtualBox.

## Historical Timeline: Connecting the Dots
- **1960s–1970s**: IBM VM 370 pioneered virtualization to give users the illusion of owning a computer and to support legacy binary applications.
- **1980s–Early 1990s**: The rise of microkernels.
- **1990s**: Extensibility of operating systems became a focus.
- **Late 1990s**: Stanford's SimOS project laid the groundwork for modern OS-level virtualization (and became the basis for VMware).
- **Early 2000s**: Papers on Xen and VMware proposed virtualization for application mobility, server consolidation, and distributed web services.
- **Today**: A massive resurgence in data centers. Companies (IBM, Microsoft, Amazon, HP) shifted focus to providing isolated services on a utility basis, creating a win-win for users and providers.

## Virtualization Approaches

### 1. Full Virtualization
- **Concept**: The guest operating system remains completely unmodified. Its unchanged binary runs directly on the hypervisor.
- **Mechanism (Trap and Emulate)**:
  - Guest OSes run as user-level processes.
  - When the guest OS attempts to execute privileged instructions (thinking it is in kernel mode on bare metal), it generates a trap.
  - The hypervisor catches the trap and emulates the intended hardware functionality.
- **Challenges (Silent Failures)**:
  - On some older architectures (early Intel/AMD), privileged instructions might fail silently without generating a trap.
- **Solution (Binary Translation)**:
  - The hypervisor scans the unmodified guest OS binary for problematic instructions and edits them to ensure they are caught and handled appropriately. *(Note: Modern hardware now includes built-in virtualization support to solve this).*
- **Example**: Utilized by VMware.

### 2. Para Virtualization
- **Concept**: The source code of the guest operating system is modified to make it "hypervisor-aware."
- **Advantages**:
  - Avoids the problematic instructions that plague full virtualization.
  - Allows for optimizations (e.g., exposing real hardware resources to the guest OS, enabling page coloring tricks).
- **Application Transparency**: The API presented to applications remains completely identical. Applications require zero changes.
- **Modification Scope**: Surprisingly small.
  - **Less than 2%** of the original OS codebase needs to be modified.
  - *Proof of concept (Xen)*: Modifying Linux required changing only ~1.36% of the code, and Windows XP required a minuscule change ("in the noise").
- **Example**: Utilized by the Xen hypervisor family.

## The Big Picture
Regardless of the approach (Full or Para Virtualization), the core responsibilities of a hypervisor are:
1. **Virtualizing Hardware Resources**: Safely and transparently realizing the memory hierarchy, CPU, and physical devices for the guest operating systems.
2. **Transfer Mechanisms**: Managing the data and control transfers between the guest operating systems and the underlying hypervisor.


---

# Module 9: Virtualizing Memory Management

## 1. Introduction and Recall
- **Goal:** Support virtualization of hardware resources for multiple operating systems efficiently and safely.
- **Importance of Memory:** Memory hierarchy is crucial for performance. Efficient device virtualization also relies heavily on how memory is virtualized.
- **Traditional Memory Subsystem:**
  - Each process is in its own protection domain with a separate hardware address space.
  - The OS maintains a **Page Table** to map **Virtual Page Numbers (VPN)** to **Physical Page Numbers (PPN)**.
  - Physical memory is contiguous, but the virtual address space is scattered all over the physical memory.

## 2. Memory Management in a Virtualized Setup
- The hypervisor sits between the guest OS and the hardware.
- The hypervisor does not natively know about the individual processes running within each guest OS (e.g., Windows, Linux).
- **Machine Memory vs. Physical Memory:**
  - **Machine Memory (MPN - Machine Page Number):** The actual, real physical memory controlled by the hypervisor. It is contiguous.
  - **Physical Memory (PPN - Physical Page Number):** The illusion of physical memory given to the guest OS. It is typically non-contiguous in the underlying machine memory because the hypervisor partitions real memory among multiple guest OSes and handles dynamic, bursty memory requests.

## 3. Address Translation and Shadow Page Tables
In a virtualized setting, address translation involves a two-step process:
1. **VPN to PPN:** Mapped by the guest OS page table.
2. **PPN to MPN:** Mapped by the **Shadow Page Table (SPT)**.

### Where is the PPN to MPN Mapping Kept?
- **Full Virtualization:** The guest OS is unaware it is not on bare metal. The hypervisor must maintain the PPN to MPN mapping.
- **Paravirtualization:** The guest OS knows it is virtualized and its memory is fragmented. The mapping is typically kept in the guest OS itself.

## 4. Efficient Memory Mapping
Address translation must be extremely efficient because it happens on every memory access. Avoiding the double indirection of page tables is key to good performance.

### Full Virtualization Mapping (e.g., VMware ESX Server)
- The hypervisor bypasses the guest OS page table for hardware translation.
- Updating the page table is a privileged instruction. When the guest OS tries to establish a VPN to PPN mapping, it triggers a **trap**.
- The hypervisor catches the trap and updates the **Shadow Page Table** (which acts as the real hardware page table or TLB) directly with the VPN to MPN mapping.
- The CPU uses the TLB and hardware page table to directly translate the VPN to MPN without guest OS intervention on every memory access.

### Paravirtualization Mapping (e.g., Xen)
- The burden of efficient mapping is shifted to the guest OS, which knows its physical memory is discontiguous.
- Xen provides **Hypercalls** for the guest OS to manage page tables:
  - **Create Page Table:** Allocate and initialize a page frame for a new process.
  - **Switch Page Table:** Used during context switches to point the hardware register to a new process's page table.
  - **Update Page Table:** Update mappings when dealing with page faults, effectively establishing the VPN to MPN translation.

## 5. Dynamically Managing Memory
Memory requirements are dynamic and bursty. The hypervisor must efficiently allocate real memory on demand, sometimes needing to reclaim it from one OS to give to another.

### Ballooning
- A technique to handle memory pressure by reclaiming memory from an underutilized guest OS without anomalous behavior.
- A special **Balloon Device Driver** is installed in the guest OS by the hypervisor.
- **Inflate:** When the hypervisor needs memory, it tells the balloon driver (via a private channel) to request more memory from the guest OS. The guest OS may page out unwanted pages to disk to satisfy this. The balloon driver then returns this real physical memory to the hypervisor.
- **Deflate:** When the hypervisor has extra memory to give, it tells the balloon driver to contract its footprint, releasing memory back to the guest OS, allowing it to page in working sets.
- Works in both full and paravirtualized environments through implicit cooperation.

## 6. Sharing Memory Across Virtual Machines
Sharing identical memory pages (e.g., immutable code pages for identical OSes or applications like Firefox) maximizes resource utilization without compromising safety.

### VM-Oblivious Page Sharing (Content-Based Sharing)
- Used in VMware ESX Server; requires no changes to the guest OS.
- **Content Hash:** The hypervisor hashes the contents of machine pages and stores the signatures in a hash table.
- **Matching Process:**
  - The hypervisor scans pages (usually as a background activity when lightly loaded) and generates a content hash.
  - If a hash matches an existing entry, it serves as a **hint** that the pages might be identical.
  - A **Full Comparison** is performed to verify exact content match.
- **Copy-on-Write (CoW):**
  - If the pages match exactly, the hypervisor maps both VMs to the same machine page and increments a reference count.
  - The entries are marked as Copy-on-Write. If either VM tries to modify the page, the hypervisor creates a separate copy and updates the mappings to ensure integrity.

## 7. Memory Allocation Policies
How should a hypervisor allocate and reclaim memory from domains?

- **Pure Share-Based:** Resources are allocated strictly based on payment/SLA ("you pay less, you get less").
  - *Problem:* Can lead to hoarding where a VM holds unused memory.
- **Working Set-Based:** Memory is allocated based on actual active usage.
- **Dynamic Idle-Adjusted Shares:**
  - Combines the two approaches by "taxing" idle memory.
  - **Tax Rate:**
    - **0% (Plutocracy):** You keep what you pay for, even if idle.
    - **100% (Socialism):** Use it or lose it. Ignores shares completely.
    - **Intermediate (e.g., 50-75%):** Used by VMware ESX. Reclaims most idle memory but leaves some reserves for sudden working set increases before a VM is forced to fault pages back in.


---

# Module 10: CPU and Device Virtualization

## 1. Introduction to CPU and Device Virtualization
- **Core Challenge:** While memory virtualization is hidden, CPU and device virtualization involve explicit interference among virtual machines (VMs).
- **Main Goal:** Provide the illusion to each guest operating system (OS) that it exclusively owns the CPU and devices. The hypervisor protects and allocates these resources on a need basis.
- **Key Aspects of CPU Virtualization:**
  1. Providing the illusion of CPU ownership (similar to how a time-shared OS isolates processes).
  2. Fielding events and program discontinuities by the hypervisor and passing them to the correct VM.

## 2. CPU Virtualization

### 2.1 CPU Scheduling and Allocation
- **Multiplexing:** Each guest OS maintains a ready-queue of processes. The hypervisor sits between the guest OS and the physical CPU.
- **Illusion of Ownership:** The hypervisor allocates CPU time to a VM, and the guest OS freely schedules its processes during that time using its own scheduling policy.
- **Accounting:** The hypervisor precisely accounts for the CPU time used by each VM, which is crucial for billing in data centers.
- **Scheduling Policies:**
  - **Proportional Share Scheduler:** Allocates a proportional share of the CPU to each guest OS based on service agreements (e.g., used in VMware ESX server).
  - **Fair Share Scheduler:** Allocates an equal share of the CPU to each guest OS.
- **Handling Interrupts:** If an external interrupt intended for one VM occurs while another VM is running, the hypervisor tracks the "stolen" time and credits it back to the interrupted VM later through its accounting procedure.

### 2.2 Handling Program Discontinuities (Full & Para-Virtualization)
- **Execution at Hardware Speeds:** Once scheduled, normal process execution and virtual-to-machine address translation happen at hardware speeds.
- **Types of Program Discontinuities:**
  1. **System Calls:** (e.g., opening a file).
  2. **Page Faults:** Virtual page not found in machine memory.
  3. **Exceptions:** (e.g., divide by zero).
  4. **External Interrupts:** Asynchronous events unrelated to the currently running process.
- **Event Delivery:** The hypervisor fields these discontinuities and passes them up to the parent guest OS packaged as **software interrupts**.
- **Privileged Instructions & Architecture Quirks:**
  - The guest OS runs in unprivileged (user) mode but needs to handle discontinuities as if it were privileged.
  - **Full Virtualization Issue:** The unmodified guest OS is unaware it lacks privileges. It executes privileged instructions expecting a trap.
  - **Silent Failures:** On older x86 architectures, some privileged instructions executed in user mode fail silently instead of trapping.
  - **Solution (Full):** The hypervisor uses **binary rewriting** to catch and safely handle these problematic instructions.
  - **Solution (Para):** The guest OS is modified to know it is not running on bare metal and explicitly asks the hypervisor for help.
  - **Hardware Support:** Newer Intel and AMD processors include hardware virtualization support to eliminate these architectural quirks.
- **Guest-to-Hypervisor Communication:**
  - **Full Virtualization:** Implicit, occurring via traps.
  - **Para-Virtualization:** Explicit, occurring via APIs/hypercalls (e.g., a guest OS asking the hypervisor to install a page table entry).

## 3. Device Virtualization

### 3.1 Overview
- **Goal:** Give the illusion to guest OSs that they own the I/O devices.
- **Two Main Concerns:**
  1. **Control Transfer:** Moving execution control back and forth between the hypervisor and the guest.
  2. **Data Transfer:** Moving data between different protection domains efficiently.

### 3.2 Full Virtualization vs. Para-Virtualization
- **Full Virtualization:**
  - Uses the **trap-and-emulate** technique.
  - The OS thinks it owns the devices. Any access traps into the hypervisor, which emulates the intended device functionality.
  - Limited scope for performance innovation.
- **Para-Virtualization:**
  - The I/O devices seen by the guest are exactly the hardware devices available to the platform.
  - High scope for innovation (e.g., clean device abstractions, shared buffers) to make virtualization more efficient.

### 3.3 Control Transfer
- **Full Virtualization:**
  - **Guest to Hypervisor:** Implicit via traps (when executing privileged instructions).
  - **Hypervisor to Guest:** Via software interrupts.
- **Para-Virtualization:**
  - **Guest to Hypervisor:** Explicit via **hypercalls** (API calls).
  - **Hypervisor to Guest:** Via software interrupts.
  - **Event Notification Control:** Guests can use hypercalls to dynamically enable or disable event notifications, similar to an OS disabling hardware interrupts.

### 3.4 Data Transfer and I/O Rings (Xen)
- **Full Virtualization:** Data transfer is implicit.
- **Para-Virtualization (e.g., Xen):** Explicit data movement focusing on:
  1. **Time Management:** Precise CPU time accountability for processing interrupts and managing buffers.
  2. **Space Management:** Efficient memory buffer allocation and management.
- **Asynchronous I/O Rings (Xen):**
  - A shared ring data structure used for communication between the guest OS and Xen.
  - **Descriptors:** The ring contains descriptors, each representing a unique I/O request with a unique ID.
  - **Producers and Consumers:**
    - The **Guest OS** places requests (producer) and updates its pointer.
    - **Xen** reads the requests (consumer), processes them, and places responses back using the same unique ID (response producer).
    - The **Guest OS** reads the responses (response consumer).
  - **Zero-Copy Data Transfer:** Descriptors only contain pointers to machine pages owned by the guest. Xen reads/writes data directly to/from these pages without copying, drastically reducing overhead.

### 3.5 Device Virtualization in Action

#### Network Virtualization (Xen)
- **Two I/O Rings per Guest:** One for transmission (Tx) and one for reception (Rx).
- **Transmission:**
  - Guest enqueues descriptors with pointers to network packets in the Tx ring via hypercalls.
  - Xen pins the pages, schedules transmission (using a Round Robin packet scheduler across VMs), and sends them. No data copying occurs.
- **Reception:**
  - Xen receives a packet. To avoid copying, it can:
    1. Place the packet directly into a pre-allocated network buffer owned by the guest.
    2. Swap the machine page containing the received packet with a page already owned by the guest.

#### Disk I/O Virtualization (Xen)
- **Dedicated I/O Ring:** Each VM has a dedicated I/O ring for disk operations.
- **Zero-Copy:** Descriptors point to guest OS buffers where data is read from or written to.
- **Asynchronous Operations:** Requests and responses happen asynchronously.
- **Reorder Barrier:** Because Xen may reorder I/O requests for throughput efficiency, it provides a "reorder barrier" API. This allows the guest OS to enforce strict execution ordering when required by higher-level semantics (e.g., write-ahead logging).

## 4. Resource Usage and Billing
- **Utility Computing:** Resources (CPU, memory, storage, network) are shared among multiple clients.
- **Measurement:** Virtualized environments must have precise mechanisms for recording both time (CPU usage) and space (memory buffers) to accurately bill users for their resource consumption.

## 5. Conclusion
- **Virtualization Focus:** Compared to extensible OSs (which focus on individual applications), virtualization (e.g., Xen, VMware) focuses on **protection and flexibility** at the granularity of entire operating systems.
- **Hardware-Assisted Virtualization:** Modern processors (Intel, AMD) have incorporated virtualization support to make hypervisor implementation easier and avoid architectural quirks. This allows even para-virtualization platforms like Xen to run unmodified guest OSs.
- **Industry Impact:** Virtualization technology, rooted in IBM VM/370 and extensible systems, is now the mainstream technology powering modern data centers and utility computing worldwide.


---

