# Lesson 3: Virtualization 

# Technical Manual: Advanced Operating System Virtualization

This manual provides a comprehensive structural synthesis of virtualization technologies, methodologies, and resource management strategies as presented in the source lectures.

---

## Part I: Foundations and Architectural Framework

### 1. Conceptual Definition and "The Big Picture"
Virtualization is the process of virtualizing hardware resources—specifically the **CPU, memory hierarchy, and devices**—to make them safely and transparently available to multiple operating systems (OS) running atop a single hypervisor. 
*   **The Utility Model:** Modern virtualization treats computing as a utility, similar to electricity or water, where resources are provided on a rental basis. 
*   **Resource Isolation:** The hypervisor provides complete performance isolation, allowing providers to bill individual users separately based on recorded usage.
*   **The "Black Box" Analogy:** To the end-user (e.g., "Bala Inc."), the platform is a black box that affords the same abstractions and capabilities as a physical server without the associated maintenance costs.

### 2. Historical Evolution and Resurgence
*   **Origins:** The concept began with the **IBM VM/370** in the 1960s/70s, designed to provide users the illusion of sole ownership and to support legacy binary applications.
*   **The 80s and 90s:** The field evolved through microkernels (80s) and OS extensibility (90s), such as the **HYDRA, SPIN, and Exokernel** projects.
*   **Modern Resurgence:** Driven by server consolidation, application mobility, and distributed web services, the **Stanford SimOS** project in the late 90s laid the foundation for modern VMware-style virtualization.
*   **Hardware Integration:** Today, chip makers (Intel, AMD) incorporate hardware-assisted virtualization to overcome architectural "quirks" and allow unmodified guest OSs to run efficiently.

### 3. Hypervisor Taxonomy
A Virtual Machine Monitor (VMM) or **Hypervisor** acts as an "operating system for operating systems".
*   **Type 1: Native (Bare-Metal):** Runs directly on hardware. It offers the best performance by interfering minimally with guest operations, echoing the philosophy of extensible systems like Exokernel.
*   **Type 2: Hosted:** Runs as an application process on a host OS (e.g., VMware Workstation, VirtualBox). It allows users to emulate other operating systems on top of their primary platform.

---

## Part II: Core Virtualization Paradigms

### 1. Full Virtualization (e.g., VMware)
The primary objective is to leave the guest OS **untouched**, running unchanged binaries on the hypervisor.
*   **Mechanism:** Guest OSs run as user-level processes. When they attempt to execute privileged instructions (kernel mode), the hardware triggers a **trap**.
*   **Trap-and-Emulate:** The hypervisor catches these traps and emulates the intended functionality.
*   **Binary Translation:** Some architectures have instructions that "fail silently" instead of trapping. In these cases, the hypervisor uses binary editing to identify and replace these "gotchas" with safe code.

### 2. Para-Virtualization (e.g., Xen)
This approach involves **modifying the source code** of the guest OS to make it aware that it is running on a hypervisor.
*   **Optimization:** Modifications allow the guest to see real hardware resources and employ tricks like **page coloring**.
*   **User/Application Impact:** While the kernel is modified, the **API remains identical**; applications (e.g., Windows/Linux apps) require no changes.
*   **Modification Scope:** Research (Xen) shows that the required changes are minuscule—often **less than 2%** of the original code base (approx. 1.36% for Linux).
*   **Hypercalls:** Instead of implicit traps, the guest makes explicit API calls (hypercalls) to the hypervisor for privileged operations.

---

## Part III: Memory Virtualization

### 1. The Three-Tier Address Hierarchy
In a virtualized environment, there is a two-step translation process:
1.  **VPN (Virtual Page Number):** The process's view of memory.
2.  **PPN (Physical Page Number):** The Guest OS's illusion of contiguous physical memory.
3.  **MPN (Machine Page Number):** The actual hardware memory controlled by the hypervisor.

### 2. Shadow Page Tables (S-PT)
To maintain performance, the hypervisor uses **Shadow Page Tables** to map VPNs directly to MPNs.
*   **Functionality:** When a guest OS tries to update its own page table (a privileged instruction), it results in a trap. The hypervisor catches this and updates the Shadow Page Table to point the VPN directly to the MPN.
*   **Hardware Alignment:** In many architectures (like X86), the Shadow Page Table is the real hardware page table used by the CPU/TLB for address translation.

### 3. Efficiency Strategies by Paradigm
*   **Full Virtualization (VMware):** Because the guest is oblivious to machine pages, the hypervisor must manage the PPN-to-MPN mapping entirely. It bypasses the guest's page table by installing VPN-to-MPN translations directly into the hardware TLB.
*   **Para-Virtualization (Xen):** The guest OS is aware that its physical memory is discontiguous and handles the PPN-to-MPN mapping itself.
    *   **Management via Hypercalls:** The guest uses specific hypercalls: `create page table` (initialization), `switch page table` (context switching), and `update page table` (handling modifications or page faults).

### 4. Dynamic Memory Management: Ballooning
Hypervisors must manage "bursty" memory requirements across VMs.
*   **The Problem:** When one VM (e.g., Windows) needs more memory but the hypervisor's "bank" is empty, it must reclaim memory from another VM (e.g., Linux).
*   **The Balloon Driver:** A special device driver is installed in the guest OS.
*   **Inflation (Reclamation):** The hypervisor tells the balloon driver to inflate. The driver requests memory from the guest OS. To satisfy this, the guest OS pages out unwanted pages to disk. The balloon driver then returns the freed **machine memory** to the hypervisor.
*   **Deflation (Allocation):** To give memory back, the hypervisor instructs the driver to deflate, releasing memory back to the guest's available pool for processes to page back in from disk.

### 5. Allocation Policies and Taxing
*   **Share-Based:** Resources are allocated based on service agreements ("pay more, get more").
*   **Working-Set-Based:** Memory is allocated based on actual active usage.
*   **Idle-Adjusted Shares:** To prevent "hoarding," hypervisors tax idle pages more than active ones. 
    *   **Tax Rates:** A 100% tax is "socialistic" (use it or lose it), while a 0% tax is "plutocratic". VMware ESX typically uses a **50-75% tax**, allowing a buffer for sudden working-set increases while reclaiming most idle memory.

### 6. Content-Based Page Sharing
To maximize memory utility, hypervisors can share identical pages (e.g., core OS code) across VMs.
*   **Implicit/Oblivious Sharing (VMware):**
    *   **Hashing:** The hypervisor maintains a hash table of machine page contents.
    *   **Comparison:** It scans machine memory in the background. If it finds a content hash match, it performs a full comparison to ensure equality.
    *   **Mapping:** If they match, the hypervisor updates the VM's PPN-to-MPN mapping to point to the existing machine page and frees the redundant page.
*   **Safety:** Shared pages are marked **Copy-on-Write (COW)**. If any VM tries to modify the page, a fault occurs, and the hypervisor creates a private copy for that VM.

---


## Part IV: CPU Virtualization

The objective of CPU virtualization is to multiplex multiple Guest OSs onto a physical CPU while providing each with the **illusion of exclusive ownership**.

### 1. The Virtualization Illusion
*   **Multiplexing Layer:** Just as a native OS multiplexes processes onto a CPU, the hypervisor multiplexes entire operating systems.
*   **Granularity:** The primary difference is the scale; the hypervisor manages resources at the granularity of an entire OS rather than individual application threads.
*   **Transparency:** Ideally, a guest OS remains unaware of other guests sharing the same physical processor.

### 2. Handling Program Discontinuities
A running process experiences discontinuities that the hypervisor must manage and redirect to the correct guest OS.
*   **Fielding Events:** The hypervisor catches discontinuities including:
    *   **System Calls:** Requests from a process to its parent guest OS (e.g., opening a file).
    *   **Page Faults:** Occur when a virtual page is not currently in machine memory.
    *   **Exceptions:** Program-driven errors, such as a "divide by zero".
    *   **External Interrupts:** Asynchronous events (like I/O completion) that occur independently of the currently running process.
*   **Delivery Mechanism:** The hypervisor packages these events as **software interrupts** and passes them up to the appropriate guest OS. 

### 3. CPU Scheduling and Policies
The hypervisor determines how much time each VM receives based on established agreements.
*   **Proportional Share Scheduler:** Allocates CPU time commensurate with a specific service agreement (e.g., VMware ESX).
*   **Fair Share Scheduler:** Distributed CPU time equally among all guest operating systems.
*   **Time Accounting:** The hypervisor precisely records usage for billing. It must account for "stolen time"—for example, if an external interrupt intended for VM B arrives while VM A is executing, the hypervisor tracks the time spent servicing that interrupt and rewards it back to VM A later.

### 4. Privilege Levels and Hardware "Quirks"
Guest OSs are typically executed as **user-level processes**.
*   **The Trap-and-Emulate Requirement:** When a guest OS attempts a privileged instruction (thinking it is in kernel mode), it must trigger a hardware trap to the hypervisor for emulation.
*   **Architectural Challenges:** Some older architectures (notably x86) have privileged instructions that **fail silently** instead of trapping when executed at the user level.
*   **Solutions:**
    *   **Full Virtualization:** The hypervisor performs **binary translation/rewriting**, scanning the guest OS binary for these "gotchas" and replacing them with code that ensures a trap occurs.
    *   **Para-virtualization:** The guest OS is modified to avoid these instructions or call the hypervisor explicitly.
    *   **Hardware-Assisted Virtualization:** Modern Intel and AMD chips incorporate specific hardware features to handle these quirks, allowing unmodified guests to run with higher efficiency.

---

## Part V: Device I/O and Data Transfer

Device virtualization involves managing the safe and efficient movement of data and control between the hypervisor and guest domains.

### 1. Control Transfer Paradigms
*   **Implicit (Full Virtualization):** Occurs via traps. When a guest attempts to access a device it believes it owns, the hardware traps into the hypervisor, which emulates the intended I/O operation.
*   **Explicit (Para-virtualization):** Occurs via **Hypercalls**. The guest uses a specific API to request I/O services from the hypervisor.
*   **Event Notification:** The hypervisor communicates back to the guest using software interrupts. In para-virtualized settings (Xen), a guest can use hypercalls to temporarily disable event notifications, similar to an OS disabling hardware interrupts.

### 2. Data Transfer Mechanisms: The Asynchronous I/O Ring
To avoid the high overhead of copying data between the guest and hypervisor address spaces, para-virtualized systems like Xen use **shared I/O rings**.
*   **Structure:** A circular data structure consisting of **descriptors**.
*   **Zero-Copy Communication:** Instead of placing the actual data (like a network packet) into the ring, the guest places a **pointer** to a machine page it already owns.
*   **Asynchronous Operation:**
    *   **Producer/Consumer Model:** The guest produces requests; the hypervisor (Xen) consumes them. Conversely, Xen produces responses which the guest consumes.
    *   **Pointers:** The system uses a combination of shared and private pointers to track the next available slot for requests and the next pending response.
    *   **Identification:** Every descriptor has a unique ID, allowing the guest to match responses to their original requests.

### 3. Case Studies in Virtualized I/O (Xen)
*   **Network Virtualization:**
    *   Each guest uses two I/O rings (one for transmission, one for reception).
    *   For transmission, pages containing packets are **pinned** to prevent them from being moved or paged out until Xen completes the transfer.
    *   For reception, Xen can swap a machine page containing an incoming packet with an existing guest page to maintain zero-copy efficiency.
*   **Disk I/O Virtualization:**
    *   Follows the same ring-based, asynchronous philosophy.
    *   **Reorder Barrier:** Because Xen might reorder disk requests for efficiency, it provides a "barrier" mechanism. This allows guests to enforce specific ordering for critical operations like **write-ahead logging**.

---

## Part VI: Resource Accountability and the Utility Model

### 1. Utility Computing and Economics
Virtualization transforms computing into a **utility** similar to water or electricity.
*   **The Service Shift:** Companies focus on providing services through data centers rather than just manufacturing low-margin hardware.
*   **Burstiness and Aggregation:** Sharing is effective because individual resource usage is often bursty. By aggregating multiple users (e.g., "Bala, Piero, and Kim"), the cumulative usage is more stable, allowing the provider to offer more resources to each user at a lower cost than individual ownership.

### 2. Measurement and Billing
Because resources are shared, the hypervisor must serve as an accurate accountant.
*   **Metrics:** The hypervisor records both **time** (CPU usage) and **space** (memory and storage footprints).
*   **Complete Isolation:** The platform must provide performance isolation to ensure one tenant's "burst" does not unfairly degrade another's experience, while still allowing the provider to bill each tenant separately based on their actual consumption.


---
<div style="page-break-after: always;"></div>
---