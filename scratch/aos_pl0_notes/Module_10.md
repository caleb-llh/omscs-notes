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
