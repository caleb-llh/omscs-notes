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
