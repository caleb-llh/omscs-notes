# Lesson 2: OS Structures 

---

## **Part I: Fundamental Principles and Goals of Operating System Structure**

### **1. Defining Operating System Structure**
Operating system structure refers to the specific organization of system software in relation to the applications it serves and the underlying hardware it manages. It acts as the intermediary—the "burger between the buns"—connecting high-level applications to low-level technology.

### **2. Core Design Objectives**
The structure of an operating system is evaluated based on several key determinants:
*   **Protection:** The system must protect the user from the system, the system from the user, users from one another, and individual users from their own errors.
*   **Performance:** Measured by the time taken to execute services on behalf of an application. A superior structure provides necessary services quickly and then "gets out of the way".
*   **Flexibility/Extensibility:** The ability for services to be adapted or "morphed" to suit the specific requirements of an application rather than being "one size fits all".
*   **Scalability:** The principle that system performance should increase proportionally as more hardware resources are added.
*   **Agility:** The speed at which the operating system adapts to changes in application needs or hardware resource availability.
*   **Responsiveness:** How quickly the system reacts to external events, a critical factor for interactive applications like video games.

### **3. The "Triangle" of OS Attributes**
Operating system design involves balancing three primary attributes: **Performance, Extensibility, and Protection**. 
*   **DOS-like structures** prioritize performance and extensibility but lack safety/protection.
*   **Traditional Microkernels** achieve protection and extensibility but often suffer from performance issues.
*   **Monolithic structures** provide performance and protection but are difficult to extend.
The ultimate goal of modern research is to find a structure that sits at the center of this triangle, catering to all three attributes simultaneously.

---

## **Part II: Taxonomy of Basic OS Structures**

### **1. Monolithic Structure**
*   **Organization:** All system services—including the file system, network access, scheduling, and memory management—are contained within a single large "blob" or kernel program.
*   **Protection Model:** Hardware ensures each application is in its own address space, protecting them from each other. The OS also resides in its own hardware address space, protecting it from applications.
*   **Service Execution:** When an application requires a service, the system switches from the application's hardware address space to the OS address space.
*   **Pros:** High performance due to minimized border crossings and consolidated components that can communicate at procedure-call speeds.
*   **Cons:** Poor extensibility; the "one size fits all" model prevents customization for specific applications (e.g., a video game versus a prime-number cruncher).

### **2. DOS-like Structure**
*   **Organization:** There is no "hard" separation between the application and the operating system; the red line of protection is replaced by a dotted line.
*   **Protection Model:** Both the application and the OS share the same address space. There is no protection of the OS from errant or malicious applications.
*   **Service Execution:** Accessing system services is as fast as a standard procedure call (memory speeds).
*   **Pros:** Maximum performance and easy extensibility through new versions of services.
*   **Cons:** Total lack of safety/protection.

### **3. Traditional Microkernel Structure (e.g., Mach)**
*   **Organization:** The microkernel provides only minimal mechanisms (not policies) such as threads, address spaces, and Inter-Process Communication (IPC).
*   **Service Execution:** All higher-level services (file system, memory manager) are implemented as server processes running in their own individual user-level address spaces.
*   **Communication:** Applications must use IPC to contact a server, which may then need to use IPC to talk to other servers to fulfill a request.
*   **Pros:** High extensibility and strong protection between all components.
*   **Cons:** Significant potential for performance loss due to frequent border crossings and address space switches.

---

## **Part III: Hardware Translation and the Cost of Border Crossings**

### **1. Mechanics of Address Space Switching**
*   **Virtual to Physical Translation:** The CPU uses a **Translation Lookaside Buffer (TLB)** to map Virtual Page Numbers (VPN) to Physical Frame Numbers (PFN).
*   **TLB Matching:** A virtual address is split into an index and a tag; the index looks up the TLB entry, and the tag is matched against the hardware to find the corresponding physical frame.
*   **Context Switch Impact:** When switching processes, the virtual-to-physical mapping changes. If the TLB lacks "address space tags," it must be flushed to prevent the new process from using the old process's mappings.

### **2. Address Space Tagged TLBs**
*   **Functionality:** Some architectures (e.g., MIPS) include a **Process ID (PID)** or address space tag in each TLB entry.
*   **Two-Level Matching:** To achieve a hit, the hardware must match both the virtual address tag and the current process's PID against the TLB entry.
*   **Benefit:** This eliminates the need to flush the TLB on a context switch, as the hardware can disambiguate entries belonging to different processes.
*   **Intel Limitations:** Older Intel architectures (486, Pentium) do not have address space tags, requiring a flush of the user portion of the TLB on every context switch.

### **3. Explicit and Implicit Costs of Border Crossings**
*   **Explicit Costs:**
    *   Entering the kernel via a trap instruction.
    *   Switching privilege levels.
    *   Flushing the TLB (if not tagged).
    *   Thread switching and stashing volatile processor state (registers) in a context block.
*   **Implicit Costs:**
    *   **Loss of Locality:** The newly scheduled process or service may not find its "working set" in the cache, leading to cache misses.
    *   **Cache Pollution:** A large service can displace the data of other processes from the cache.
    *   **Data Copying:** Moving data between user and system space to preserve integrity.

---

## **Part IV: The SPIN Approach to Extensibility**

### **1. Core Concept: Co-location and Logical Protection Domains**
SPIN avoids the cost of hardware border crossings by co-locating the kernel and its extensions within the **same hardware address space**. Protection is achieved not through hardware boundaries, but through **Logical Protection Domains** enforced by a strongly typed programming language (Modula-3).

### **2. Language-Based Protection (Modula-3)**
*   **Strong Typing:** Prevents "cheating" like C-style pointer type-casting; pointers can only be used for their defined types.
*   **Encapsulation:** Objects serve as containers with well-defined entry points; internal data structures are hidden from outside access.
*   **Automatic Management:** Includes features like automatic storage management (no memory leaks) and safety mechanisms.
*   **Capabilities as Pointers:** In SPIN, a capability to an object is simply a language-supported pointer, making it much cheaper than traditional heavyweight OS capabilities.

### **3. SPIN Mechanisms for Extensions**
*   **Create:** Instantiates a logical protection domain from an object file and exports its entry point names.
*   **Resolve:** Dynamically links two protection domains by resolving names between a source and target; once resolved, calls happen at memory speeds (procedure calls).
*   **Combine:** Aggregates multiple small domains into a single larger domain to manage complexity and reduce the proliferation of small domains.

### **4. Event-Based Communication**
SPIN uses an event dispatcher to field external interrupts and exceptions. Services register event handlers with the dispatcher, supporting various mappings:
*   **Many-to-One:** e.g., both Ethernet and ATM packet arrivals mapping to a single IP handler.
*   **One-to-Many:** e.g., an IP packet arrival event triggering UDP, TCP, and ICMP handlers.
*   **One-to-One:** e.g., an ICMP event triggering a specific "ping" program.
*   **Guards:** Handlers can use "guards" (predicates) to ensure they only execute when specific conditions are met (e.g., only if the packet is an IP packet).

### **5. Core Services in SPIN**
*   **Memory Management:** SPIN provides interface headers (allocating/deallocating pages, translating addresses) but allows extensions to implement the actual logic. Once instantiated, these handlers are invoked automatically by hardware events without border crossings.
*   **CPU Scheduling:**
    *   **Global Scheduler:** Allocates time slices to extensions at a macro level.
    *   **Strands:** An abstraction representing a unit of scheduling; extensions define the semantics of a strand (e.g., mapping them to p-threads).
    *   **Event Handlers:** Extensions provide semantic meaning for events like `block`, `unblock`, `checkpoint`, and `resume`.

---


## **Part V: The Exokernel Approach to Extensibility**

### **1. Core Philosophy: Hardware Exposure and Decoupling**
The Exokernel architecture is defined by its name: it "exposes" hardware explicitly to the operating system extensions (Library Operating Systems) living above it. The fundamental design principle is the **decoupling of hardware authorization from its actual use**.

### **2. The Secure Binding Mechanism**
Exokernel acts as a "broker" or "doorman" for hardware resources. It manages the allocation of resources—such as memory pages, CPU time slices, or portions of a frame buffer—without dictating their semantics.

*   **Request and Validation:** A Library OS requests a specific hardware resource. The Exokernel validates the request and creates a **secure binding** between the Library OS and the hardware.
*   **Encrypted Keys (Capabilities):** Once a binding is established, Exokernel returns an **encrypted key** to the Library OS. This key authenticates subsequent uses of the resource and cannot be forged or transferred to another operating system.
*   **Authorization vs. Performance:** Establishing a binding is a "heavy-duty" operation involving the kernel. However, once the binding exists, the Library OS presents the key to the Exokernel for validation, allowing the actual use of the hardware to be highly efficient and occur at near-hardware speeds.

### **3. Managing Program Discontinuities (PE Data Structure)**
To handle events that interrupt normal execution, Exokernel maintains a **Processor Environment (PE) data structure** for every Library OS.
*   **Handler Entry Points:** The PE structure contains specific entry points for various events:
    *   **Exceptions:** Hardware-thrown errors like divide-by-zero.
    *   **External Interrupts:** Events like disk I/O completion.
    *   **Protected Entry Context:** The entry point for system calls made by processes within that Library OS.
    *   **Addressing Context:** The location of the handler for servicing page faults.
*   **Event Dispatch:** When the CPU incurs a trap or fault, Exokernel identifies the currently running Library OS (using its internal scheduling vector) and passes the discontinuity to the appropriate handler registered in the PE structure.

### **4. Resource Revocation and Reallocation**
Because Exokernel does not provide high-level abstractions, it must have a mechanism to reclaim resources it previously allocated.
*   **The Revoke Call:** This is an "up-call" from Exokernel to the Library OS, providing a **repossession vector** that lists the resources (e.g., specific page frames) being reclaimed.
*   **Library OS Responsibility:** Upon receiving a revocation notice, the Library OS must take corrective action, such as stashing the contents of reclaimed page frames to disk.
*   **Autosave Seeding:** To minimize the work required during active revocation, a Library OS can "seed" Exokernel with **autosave options**. For example, it can instruct the Exokernel to automatically dump specific pages to disk whenever they are revoked.

### **5. Downloaded Code and Security Risks**
Exokernel allows Library OSes to "download" code directly into the kernel to handle performance-critical tasks.
*   **Applications:** Examples include **packet filters** for demultiplexing network data or **garbage collection** mechanisms that run even when the Library OS is not scheduled.
*   **Interrupt Handling:** Downloaded code can provide first-level interrupt handling on behalf of the Library OS.
*   **Protection Compromise:** Unlike SPIN, which uses a strictly typed language for protection, Exokernel allows the execution of arbitrary downloaded code. This makes Exokernel potentially more vulnerable to security loopholes, as the kernel may have to step outside standard protection boundaries to allow these extensions to control hardware.

### **6. Core Services Implementation**
*   **CPU Scheduling:** Exokernel manages CPU time through a **linear vector of time slots** (epochs). Library OSes mark their preferred time slots at startup.
    *   **Context Switching:** When a timer interrupt occurs, Exokernel transfers control to the Library OS to save its context.
    *   **Bounded Time & Penalties:** The time allowed for context saving is strictly bounded. If a Library OS misbehaves by exceeding this limit, Exokernel docks its time in the next scheduled epoch.
*   **Memory Management:** 
    *   Library OSes establish mappings between virtual pages and physical frames. 
    *   Because installing mappings into the hardware TLB is a privileged operation, the Library OS must present the mapping and its encrypted key to Exokernel, which then performs the installation.

---

## **Part VI: The L3 Microkernel and Myth Debunking**

### **1. The L3 Thesis: Implementation over Principle**
The L3 microkernel was designed to prove that the performance issues historically associated with microkernels (such as Mach) were the result of poor implementation decisions rather than inherent flaws in the microkernel philosophy. 

L3's core thesis is two-fold:
1.  **Minimal Abstractions:** The kernel should only provide four fundamental mechanisms: **Address Spaces, Threads, Inter-Process Communication (IPC), and Unique Identifiers (UIDs)**.
2.  **Processor-Specific Implementation:** To achieve maximum performance, a microkernel *must* be non-portable. It should exploit every available hardware feature of a specific processor architecture, rather than aiming for architecture-independence.

### **2. Debunking Myth 1: The High Cost of Border Crossings**
Critics argued that switching between user and kernel space is inherently expensive. L3 debunked this by showing that:
*   **Cycle Counts:** While Mach required 900 cycles for a user-to-kernel switch on the same hardware, L3 achieved it in only **123 cycles**.
*   **Theoretical Limits:** L3’s performance is remarkably close to the theoretical minimum (approximately 107 cycles) required by the hardware instructions themselves.
*   **The Culprit - Code Bloat:** Mach's poor performance was attributed to **code bloat** caused by its focus on portability, which led to a large memory footprint and increased cache misses.

### **3. Debunking Myth 2: The Necessity of TLB Flushes**
A major "strike" against microkernels was the assumption that frequent address space switches necessitated frequent (and expensive) TLB flushes. L3 introduced techniques to avoid this:
*   **Address Space Tagging:** On hardware that supports it (e.g., MIPS), TLB entries are tagged with a Process ID (PID). This allows the hardware to disambiguate entries from different processes, making flushes unnecessary.
*   **Exploiting Segment Registers (x86/PowerPC):** For architectures without tagged TLBs, L3 uses hardware **segment registers** to carve a single linear hardware address space into multiple smaller protection domains.
*   **Protection without Flushes:** By using segment registers as a "first line of defense" to bound the legal virtual addresses a process can generate, multiple services can reside in the same hardware address space simultaneously, eliminating the need to flush the TLB during switches between them.

### **4. Debunking Myth 3: Memory and Locality Effects**
The myth stated that the loss of locality in microkernels is inherently worse than in monolithic systems. L3 countered this by analyzing the impact of protection domain size:
*   **Small Protection Domains:** If domains are small, they can be packed into a single hardware address space using the segment register technique. This keeps the caches "warm," as the working sets of different services are more likely to remain in the cache during switches.
*   **Large Protection Domains:** If a service (like a massive file system) is so large that it occupies the entire hardware address space, the loss of locality (cache pollution) is unavoidable regardless of the OS structure (Monolithic, SPIN, or Microkernel).
*   **Implicit vs. Explicit Costs:** For large domains, the **implicit costs** (cache effects) dominate the performance impact, making the **explicit cost** of the actual address space switch insignificant by comparison.

### **5. Debunking Myth 4: Expensive Thread Switching and IPC**
L3 demonstrated that the explicit costs of thread switching—saving and restoring the volatile state (registers) of the processor into a thread context block—could be implemented as efficiently in a microkernel as in SPIN or Exokernel.


---
<div style="page-break-after: always;"></div>
---