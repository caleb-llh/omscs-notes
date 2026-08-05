# Lesson 2: OS Structures 


---

#### 1. Fundamental Goals of Operating System Structure
The organization of OS software relative to applications and hardware is defined by its ability to manage resources while providing services. 

*   **1.1 Core Design "Triangle":** 
    *   **Protection (Safety):** Protecting the system from users, users from the system, and users from each other, including self-protection from errors.
    *   **Performance:** The efficiency of service delivery (time taken for application requests). A high-performance OS provides services quickly and "gets out of the way".
    *   **Flexibility (Extensibility):** Ensuring services are not "one size fits all" but adaptable to specific application requirements.

*   **1.2 Supplemental Metrics:**
    *   **Scalability:** Performance should increase proportionally with the addition of hardware resources.
    *   **Agility:** The speed at which the OS adapts to changes in application needs or hardware resource availability.
    *   **Responsiveness:** Reaction time to external events, critical for interactive applications like video games.

---

#### 2. Comparison of Foundational OS Structures
Historically, OS designs have traded off the core goals of the "Triangle".

*   **2.1 Monolithic Structure:**
    *   **Organization:** All services (File System, Network, Scheduling, Memory Management) are contained in a single large kernel "blob".
    *   **Protection:** High. Applications exist in distinct hardware address spaces, and the OS resides in its own privileged address space. Malfunctioning applications do not compromise OS integrity.
    *   **Performance:** High. Internal component communication (e.g., File System calling the Storage Manager) occurs via fast procedure calls within the same address space. Border crossings are minimized (one to enter the kernel, one to return).
    *   **Drawback:** Low flexibility. Rebuilding or customizing services is difficult; it is a "one size fits all" model.

*   **2.2 DOS-like Structure:**
    *   **Organization:** No hard separation between application and OS address spaces.
    *   **Performance:** Exceptional. System services are accessed at memory speeds as simple procedure calls.
    *   **Protection:** None. Errant or malicious applications can easily corrupt OS data structures.
    *   **Context:** Designed for early single-user, single-tasking PCs where performance and simplicity were prioritized over safety.

*   **2.3 Microkernel-Based Structure (Initial Concepts, e.g., Mach):**
    *   **Organization:** The microkernel provides only minimal mechanisms (Address Space, Threads, IPC, UIDs). Policies and services (File System, Memory Management) run as separate user-level server processes in their own address spaces.
    *   **Protection:** Very High. Hard lines exist between applications, servers, and the kernel.
    *   **Flexibility:** High. Services are extensible and replaceable by different server processes.
    *   **Performance:** Historically poor. Frequent **border crossings** (IPC calls across address spaces) lead to significant overhead.

---

#### 3. Hardware Mechanisms for Translation and Protection
Effective OS structuring requires a deep understanding of hardware-level address translation and protection mechanisms.

*   **3.1 Translation Lookaside Buffer (TLB) Operations:**
    *   The TLB caches mappings from **Virtual Page Numbers (VPN)** to **Physical Frame Numbers (PFN)**.
    *   **Explicit Cost of Context Switch:** On a traditional context switch, virtual-to-physical mappings change, necessitating a TLB flush if the hardware cannot disambiguate mappings between processes.

*   **3.2 Address Space Tagged TLBs:**
    *   **Mechanism:** Entries include a **Process ID (PID)** or Address Space Tag alongside the virtual address tag.
    *   **Matching Logic:** A TLB "hit" occurs only if both the PID of the current process and the virtual address tag match the entry.
    *   **Benefit:** Eliminates the need to flush the TLB on context switches, as mappings for multiple processes can coexist.
    *   **Architectural Examples:** MIPS uses tagged TLBs; Intel 486 and Pentium do not.

*   **3.3 Optimization on Non-Tagged Architectures (e.g., Intel):**
    *   **Split TLB:** The TLB is divided into User and Kernel portions. The kernel portion is common across processes and is not flushed during a switch.
    *   **Segment Registers:** Used to define a legal range of virtual addresses for a process. 
        *   **Protection Domains:** By carving the linear address space into regions (S1, S2, etc.) using segment registers, the hardware can enforce boundaries without flushing the TLB, provided the domains are small enough to coexist in the linear space.

---

#### 4. The "Myths" of Performance Loss in Microkernels
A significant portion of research (specifically the **L3 microkernel**) focuses on debunking perceived inherent costs of microkernel designs.

*   **4.1 The Border Crossing Myth:**
    *   **Assertion:** Moving from user space to kernel space is inherently slow.
    *   **Debunking:** L3 achieves this in **123 processor cycles** (including TLB and cache misses), while the theoretical minimum on that hardware is 107 cycles. In contrast, Mach took **900 cycles** due to "code bloat" and portability-focused design which ruined locality.

*   **4.2 The Address Space Switch Myth:**
    *   **Assertion:** Switching hardware address spaces is too expensive due to TLB flushes.
    *   **Debunking:** For small protection domains, techniques like segment registers or tagged TLBs mitigate explicit costs. For large domains, the **implicit cost** (cache effects/loss of locality) dominates any explicit TLB flush cost regardless of the OS structure.

*   **4.3 The Thread Switch and IPC Myth:**
    *   **Assertion:** Kernel-mediated thread switches and IPC are inherently slow.
    *   **Debunking:** L3 demonstrates that thread switch times can be competitive with extensible systems like SPIN and Exokernel through careful construction.

*   **4.4 The Memory Effects Myth:**
    *   **Assertion:** Microkernels suffer more from loss of locality than monolithic kernels.
    *   **Debunking:** If small protection domains are packed into the same hardware address space, caches remain "warm" during switches. Large subsystems will pollute the cache in any architecture (monolithic or microkernel) because caches are physically tagged.

---


#### 5. The SPIN Architecture: Language-Based Extensibility
SPIN achieves extensibility by co-locating the kernel and its extensions (services) within the same **hardware address space**. This design eliminates the overhead of traditional border crossings, making system services as efficient as procedure calls.

*   **5.1 Logical Protection Domains:**
    *   Instead of relying on hardware boundaries (which require expensive TLB/address space switches), SPIN uses a **strongly typed programming language** (Modula-3) to enforce modularity and safety.
    *   **Enforcement Mechanisms:** The compiler and runtime environment ensure that code cannot "cheat." Unlike C, pointers in Modula-3 cannot be forged or type-cast to subvert data abstractions.
    *   **Capabilities as Pointers:** In SPIN, a capability—traditionally a heavyweight OS mechanism—is implemented simply as a language-supported pointer. These pointers serve as secure containers for logical protection domains.

*   **5.2 Operational Primitives:**
    *   **Create:** Instantiates an object file as a logical protection domain and exports its entry point methods to be visible externally.
    *   **Resolve:** Dynamically links two protection domains (a source and a target). Once resolved, the source can invoke methods in the target at memory speeds.
    *   **Combine:** Aggregates multiple small logical protection domains into a single larger domain. This is used as a software engineering tool to manage the complexity and proliferation of numerous small domains.

*   **5.3 SPIN Core Services:**
    *   **Memory Management:** SPIN provides a toolbox of **interface procedures** (header files) rather than rigid policies.
        *   **Functions:** `Allocate`, `Deallocate`, and `Reclaim` for physical frames; `Translate` for managing address space mappings.
        *   **Event Handlers:** Extensions must implement the actual logic for page faults, access violations, and bad address exceptions. Once instantiated, these handlers are invoked automatically by hardware events without border crossing.
    *   **CPU Scheduling:** 
        *   **Global Scheduler:** Operates at a macro level, allocating time slices (e.g., in milliseconds) to different extensions.
        *   **Strands:** The unit of scheduling provided by SPIN. Extensions (like a guest Linux or Windows OS) map their internal thread semantics onto these strands.
        *   **Event Interface:** Provides primitives such as `Block`, `Unblock`, `Checkpoint`, and `Resume`. For example, a disk interrupt may trigger an `Unblock` event for a strand waiting on I/O.

*   **5.4 Event-Based Communication:**
    *   SPIN uses a dispatcher to field external events (interrupts, exceptions, system calls).
    *   **Mapping Models:** Supports one-to-one, one-to-many, and many-to-one mappings.
    *   **Case Study (Network Protocol Stack):** Multiple hardware interfaces (Ethernet, ATM) can map to a single IP handler (many-to-one). Conversely, an IP packet arrival event can trigger multiple handlers (TCP, UDP, ICMP) simultaneously (one-to-many).
    *   **Guards:** Handlers can specify "guards" (predicates) to ensure they only execute when specific conditions (e.g., a specific packet type) are met.

---

#### 6. The Exokernel Architecture: Hardware Exposure and Library OSes
The Exokernel philosophy is to expose hardware resources explicitly and decouple resource **authorization** from resource **use**.

*   **6.1 Secure Bindings and Authorization:**
    *   **Mechanism:** A Library OS (LibOS) requests a resource. The Exokernel validates the request and creates a "secure binding" to the hardware.
    *   **Encrypted Keys:** Upon binding, the Exokernel issues an **encrypted key** (capability) to the LibOS. This key is unforgeable and cannot be transferred to other operating systems.
    *   **The "Doorman" Model:** The Exokernel acts as a doorman. It checks the key only when a LibOS enters the "apartment" (accesses the resource). Once inside, the LibOS manages the resource semantics entirely on its own.

*   **6.2 Resource Revocation:**
    *   **Upcalls:** Since the Exokernel has no knowledge of how a LibOS uses resources, it uses a **revoke** mechanism to reclaim them.
    *   **Repossession Vector:** An upcall informs the LibOS exactly which resources (e.g., specific page frames) are being taken back.
    *   **Corrective Action:** The LibOS is responsible for cleaning up (e.g., stashing page contents to disk).
    *   **Autosave Options:** A LibOS can "seed" the Exokernel with autosave instructions, allowing the kernel to automatically dump data to disk upon revocation to reduce LibOS overhead.

*   **6.3 Exokernel Core Services:**
    *   **Memory Management:** 
        *   When a thread incurs a page fault, the Exokernel fields the trap and kicks it up to the LibOS through a registered handler.
        *   The LibOS establishes the virtual-to-physical mapping and presents it to the Exokernel along with the encrypted key for a specific TLB entry. 
        *   The Exokernel validates the key and performs the **privileged operation** of installing the entry into the hardware TLB.
    *   **CPU Scheduling:**
        *   Exokernel maintains a **linear vector of time slots** (epochs T1, T2, etc.).
        *   LibOSes mark their desired slots at startup. 
        *   **Penalties:** If a LibOS exceeds its bounded time for context saving during a switch, the Exokernel records this misbehavior and penalizes the LibOS by reducing its future time allocations.

*   **6.4 The PE (Processor Environment) Data Structure:**
    *   The Exokernel maintains a unique PE structure for every LibOS.
    *   It contains entry points for handling **program discontinuities**: exceptions, external interrupts, system calls, and page faults.

*   **6.5 Software TLB (STLB) and Locality:**
    *   To mitigate the loss of locality during address space switches, the Exokernel maintains a Software TLB for each LibOS.
    *   On a context switch, the Exokernel "dumps" a subset of the hardware TLB mappings (guaranteed mappings) into the STLB of the outgoing LibOS and pre-loads the hardware TLB with the STLB of the incoming LibOS.

---

#### 7. Comparative Performance and Protection Synthesis
*   **7.1 Protection Philosophies:** 
    *   SPIN relies on **compile-time checking** and language-enforced safety. 
    *   Exokernel relies on **secure hardware bindings** and encrypted keys.
    *   **Risk:** Exokernel may compromise protection more because it allows downloading **arbitrary code** (like packet filters) into the kernel. However, SPIN also occasionally steps outside language boundaries to control hardware.

*   **7.2 Performance Benchmarks (The Research "Trends"):**
    *   **Against Microkernels:** Both SPIN and Exokernel significantly outperform Mach for protected procedure calls.
    *   **Against Monolithic Kernels:** Both architectures achieve performance for system calls that is "as well as" a monolithic kernel. 
    *   **Hardware Speed:** Once a binding is established in Exokernel (e.g., a TLB entry), the application runs at hardware speeds without further kernel intervention.

---


#### 8. The L3 Microkernel Architecture
The L3 microkernel was developed contemporaneously with SPIN and Exokernel to prove that microkernel performance issues (like those seen in Mach) are not inherent to the structure itself but are results of specific design choices.

*   **8.1 Minimalist Abstraction Thesis:**
    *   L3 posits that a microkernel must provide only the **minimal set of abstractions** required by any subsystem. 
    *   **The Four Pillars:** 
        1.  **Address Spaces:** For protection and isolation.
        2.  **Threads:** The unit of execution.
        3.  **Inter-Process Communication (IPC):** To allow servers to cooperate and satisfy user requests.
        4.  **Unique Identifiers (UIDs):** To identify subsystems globally.
    *   **Optimization of the Common Case:** By strictly limiting the kernel to these four abstractions, the "common case" of system operations can be highly optimized.

*   **8.2 Processor-Specific Implementation:**
    *   L3 argues that a microkernel **must be processor-specific** to achieve high performance. 
    *   **The Portability Trade-off:** While Mach prioritized portability (architecture independence), L3 argues that processor independence at the kernel level necessitates "code bloat" and sacrifices performance.
    *   **Layered Design:** L3 suggests using a processor-specific kernel as a foundation for building **processor-independent abstractions** (like file systems or network protocols) at higher layers of the OS stack.

---

#### 9. Technical Deconstruction of the "Four Strikes" against Microkernels
The "Four Strikes" represent the explicit and implicit costs traditionally cited as the reasons for microkernel performance degradation.

*   **9.1 Strike 1: User/Kernel Border Crossing (Explicit Cost):**
    *   **The Myth:** Moving from user space to privileged kernel mode (via a trap instruction) is inherently expensive.
    *   **L3 Debunking:** On a specific processor architecture, L3 count the hand-coded machine instructions required for a border crossing and found the theoretical minimum to be **107 cycles**. L3 achieves the crossing in **123 cycles**, including TLB and cache misses. 
    *   **Mach Comparison:** On the same hardware, Mach takes **900 cycles**. This is attributed to code bloat and a large memory footprint caused by its focus on portability, which destroys locality and increases cache misses.

*   **9.2 Strike 2: Address Space Switches (Explicit Cost):**
    *   **The Myth:** Switching between hardware address spaces requires flushing the TLB, which is prohibitively slow.
    *   **Hardware Context:** 
        *   **Tagged TLBs:** Architectures like MIPS include a Process ID (PID) in TLB entries. A "hit" requires both a Virtual Page Number (VPN) and a PID match, meaning the TLB **never needs to be flushed** during a context switch.
        *   **Non-Tagged TLBs:** Architectures like Intel 486/Pentium lack PID tags, requiring a flush of the user-portion of the TLB during every context switch.
    *   **Liedtke’s Optimization (Segment Registers):** For non-tagged hardware, L3 uses **segment registers** (available in x86 and PowerPC) to carve a single linear hardware address space into multiple **small protection domains** (S1, S2, etc.).
    *   **The Result:** Hardware checks ensure a process stays within its assigned segment. This allows multiple small protection domains to coexist in the TLB simultaneously, **eliminating the need for flushes** during context switches between them.

*   **9.3 Strike 3: Thread Switches and IPC (Explicit Cost):**
    *   **The Myth:** Kernel-mediated thread switching and IPC for protected procedure calls are significantly slower than normal procedure calls.
    *   **L3 Debunking:** By construction, L3 proves that its thread switch times are competitive with extensible systems like SPIN and Exokernel. It minimizes the time taken to save and restore volatile processor state (registers) into thread context blocks.

*   **9.4 Strike 4: Memory Effects and Locality (Implicit Cost):**
    *   **The Myth:** Microkernels suffer more from a loss of locality (cache pollution) than monolithic kernels.
    *   **Small Protection Domains:** If domains are small and packed into the same hardware address space, caches remain "warm" during switches, preserving the working set of the newly scheduled thread.
    *   **Large Protection Domains:** If a service (e.g., a massive file system) is so large it occupies the entire hardware address space, it will **pollute the cache regardless of the OS structure** (Monolithic, SPIN, or Microkernel). Because caches are physically tagged, large subsystems inevitably displace the previous working set.

---

#### 10. The Structural Scorecard: Synthesizing OS Architectures
The following table summarizes how different structures satisfy the core OS design goals.

| Structure | Protection | Performance | Extensibility | Primary Characteristic |
| :--- | :--- | :--- | :--- | :--- |
| **Monolithic** | High | High | Low | One-size-fits-all "blob" |
| **DOS-like** | None | Exceptional | High | No address space separation |
| **Microkernel** | Very High | Low (Trad.) | Very High | Minimalist core; user-level servers |
| **L3 (Optimized)** | Very High | High | Very High | Processor-specific optimizations |
| **SPIN** | High | High | High | Language-enforced safety; co-location |
| **Exokernel** | High | High | High | Hardware exposure; secure bindings |

*   **The Design Goal:** Modern OS research seeks to reach the **center of the "Triangle"**, simultaneously achieving Performance, Extensibility, and Protection.

---

#### 11. Advanced Comparison: SPIN vs. Exokernel
*   **11.1 Protection Mechanism:**
    *   **SPIN:** Uses Modula-3's strong typing, compile-time checking, and runtime verification to enforce "logical protection domains".
    *   **Exokernel:** Uses secure hardware bindings and unforgeable encrypted keys to authorize resource access.
*   **11.2 Safety Risks:**
    *   Exokernel potentially compromises protection more than SPIN because it allows the downloading of **arbitrary code** (e.g., packet filters) into the kernel.
    *   SPIN is generally safer due to language enforcement, though it may occasionally "step outside" the language to control hardware directly.
*   **11.3 Border Crossings:**
    *   Both SPIN and Monolithic kernels result in the **least number of border crossings**. 
    *   In SPIN, moving between protection domains is as cheap as a procedure call because they are logical, not hardware-based.

---

<div style="page-break-after: always;"></div>
---