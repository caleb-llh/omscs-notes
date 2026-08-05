# Lesson_2_OS_Structures (Synthesized Notes)

# Operating System Structures

## 1. Introduction
* **Core Responsibilities:** An operating system (OS) must protect the integrity of hardware resources while providing services to applications.
* **Key Questions in OS Design:**
  * How should functional components fit together?
  * Must the entire OS run in privileged mode?
  * Can OS services (e.g., memory management) be personalized to suit specific application needs?
  * Does flexibility compromise performance or safety?
* **Case Studies Covered:** This module explores solutions for OS extensibility using **SPIN**, **Exokernel**, and a microkernel approach using the **L3 Microkernel**.

## 2. Goals of Operating System Structure
Operating system structure refers to the way OS software is organized relative to the applications it serves and the hardware it manages ("the burger between the buns"). The structure aims to achieve several goals:
* **Protection:** Protecting users from the system, the system from users, users from each other, and users from their own mistakes.
* **Performance:** Minimizing the time taken to perform services on behalf of an application. A good OS provides service quickly and gets out of the way.
* **Flexibility / Extensibility:** Ensuring services are not "one-size-fits-all" but adaptable to the specific requirements of different applications.
* **Scalability:** Guaranteeing that as hardware resources increase, system performance proportionally increases.
* **Agility:** The speed at which the OS adapts to changes in application needs or underlying resource availability.
* **Responsiveness:** How quickly the OS reacts to external events, which is crucial for interactive applications (e.g., video games).

## 3. Approaches to OS Structuring

### 3.1 Monolithic Structure
In a monolithic structure, all OS services (file system, network, scheduling, virtual memory, etc.) are contained in a single, large blob.
* **Architecture:** 
  * Hardware is at the bottom, applications at the top.
  * Each application runs in its own hardware address space (providing application-level protection).
  * The entire OS runs in its own privileged address space, protected from applications.
  * An application requests a service by trapping into the OS (switching address spaces), executing the privileged system code, and returning.
* **Pros:** 
  * **Protection:** Strong separation between the OS and applications.
  * **Performance:** Once inside the OS address space, components (e.g., file system, memory manager, storage manager) can communicate rapidly via simple procedure calls without further address space switches. Data can be shared without copying.
* **Cons:** 
  * **Lack of Extensibility:** It is difficult to customize services for different applications (one-size-fits-all model). Any change requires rebuilding the entire monolithic kernel.

### 3.2 DOS-like Structure
Historically used in early PCs (e.g., Microsoft DOS), designed under the assumption of a single-user running a single application at a time.
* **Architecture:** 
  * No hard separation between the application's address space and the OS's address space. 
* **Pros:** 
  * **Performance:** Applications can access system services as quickly as standard procedure calls (at memory speeds).
  * **Extensibility:** Easy to build new versions of system services for specific application needs.
* **Cons:** 
  * **Lack of Protection:** An errant application can easily compromise or corrupt the OS data structures, either maliciously or unintentionally.

### 3.3 Microkernel-Based Structure
Designed to address the need for extensibility and customization that monolithic kernels lack.
* **Architecture:**
  * **Microkernel:** Runs in privileged mode but contains **no policies**, only basic **mechanisms** (threads, address spaces, inter-process communication (IPC)).
  * **OS Services:** Implemented as independent server processes (e.g., virtual memory, CPU scheduling, file system) running in user space on top of the microkernel.
  * Applications and server processes communicate heavily via IPC provided by the microkernel.
* **Pros:**
  * **Extensibility & Customization:** Different applications can use different server implementations (e.g., varying file systems) simultaneously. 
  * **Protection:** Strong boundaries separate applications from each other, applications from services, services from each other, and everything from the microkernel.
* **Cons:**
  * **Performance Loss:** High overhead due to frequent "border crossings" (address space switches).
    * *Explicit costs:* Time taken to switch hardware address spaces.
    * *Implicit costs:* Loss of execution locality (cache misses) when jumping between different address spaces.
    * *Data copying:* Need to copy data between user space and system space across boundaries.

## 4. The Need for Customization
Why avoid a "one-size-fits-all" approach? Different applications have vastly different requirements.
* **Interactive Video Games:** Require high **responsiveness** to external events.
* **Scientific Computing (e.g., Prime Number Generation):** Requires sustained **CPU time** (performance).
* **Memory Management (Page Faults):** The OS typically runs a page replacement algorithm to free up frames. Because the OS cannot perfectly predict an application's memory access pattern, a generic algorithm may be inefficient. Customization allows an application to dictate a page replacement policy tailored to its specific memory access behavior. Similar customization opportunities exist in CPU scheduling and interrupt handling.

## 5. Summary: The OS Structure Triangle
OS design is often a trade-off between three key attributes: **Protection**, **Performance**, and **Extensibility**.

| OS Structure | Protection | Performance | Extensibility |
| :--- | :--- | :--- | :--- |
| **Monolithic** | Yes | Yes | No |
| **DOS-like** | No | Yes | Yes |
| **Microkernel** | Yes | Potential Loss | Yes |

* **The Ultimate Goal:** The holy grail of OS research is to reach the center of this triangle—achieving protection, high performance, and extensibility simultaneously. 
* **Note on Microkernels:** While early microkernels suffered from performance issues due to IPC overhead, careful implementation (such as the **L3 Microkernel**) can overcome these performance bottlenecks.

---

# Module 6: Operating System Extensibility (SPIN & Exokernel)

## 1. Introduction and Goals of OS Structure
The primary goal of modern OS structure is to achieve **extensibility** without compromising **protection** or **performance**.
- **Monolithic Design:** Offers high performance and protection but lacks extensibility (policies are heavily ingrained in the kernel).
- **Microkernel Design:** Highly extensible and portable, but compromises performance due to frequent border crossings (context switches between kernel and user-space servers).

### Core Goals for an Ideal OS Structure
- **Thin Kernel:** Only mechanisms should reside in the kernel; policies should be implemented externally.
- **Fine-Grained Access:** Resource access should occur without expensive border crossings, resembling a DOS-like structure.
- **Flexibility:** Resource management should be easily adaptable to suit specific application needs.
- **Performance & Protection:** Must match the speeds and security guarantees of a monolithic kernel.

---

## 2. Historical Approaches to Extensibility
- **Hydra OS (CMU, 1981):** 
  - Provided kernel mechanisms (not policies) for resource allocation.
  - Used a **Capability-based approach** (unforgeable, verifiable tokens passed between objects).
  - *Drawback:* Capabilities were a heavyweight mechanism. To reduce border-crossing overhead, Hydra used coarse-grained objects, which severely limited customization and extensibility.
- **Mach OS (CMU, early 90s):**
  - A microkernel design providing limited mechanisms; OS services ran as user-level server processes.
  - *Focus:* Portability and extensibility.
  - *Drawback:* Poor performance due to frequent border crossings gave microkernels a bad reputation.

---

## 3. The SPIN Approach to Extensibility
**Core Idea:** Co-locate a minimal kernel and its extensions within the same hardware address space to completely avoid border-crossing overhead.

### Language-Enforced Protection
Instead of relying on hardware address spaces for protection, SPIN relies on the characteristics of a **strongly typed programming language (Modula-3)**.
- **Modula-3 Features:** Built-in safety, encapsulation, automatic memory management (no memory leaks), objects with well-defined entry points, threads, and exceptions.
- **No Typecasting:** Unlike C, pointers cannot be forged or arbitrarily cast to bypass protection, ensuring compile-time checking and runtime modularity.

### Logical Protection Domains
- **Definition:** Data abstractions (like objects) serve as containers for logical protection domains. 
- The kernel provides only generic interfaces; domains implement the actual functionality.
- Applications can dynamically bind to different implementations of the same interface, providing flexibility.
- **Capabilities as Pointers:** Access to resources is provided via capabilities, which in SPIN are simply language-supported pointers. This makes them extremely cheap and lightweight compared to traditional capabilities.
- *Result:* Extensions become as cheap as standard procedure calls while maintaining monolithic-level safety.

### SPIN Mechanisms for Protection Domains
SPIN provides three core mechanisms to manage domains:
1. **Create:** Initiates an object file and exports its entry point method names to be visible externally.
2. **Resolve:** Dynamically links (binds) a source and target logical protection domain. Once resolved, access happens at memory speeds (like a procedure call).
3. **Combine:** Aggregates multiple protection domains into a single larger domain (a union of entry points) to combat the proliferation of many small domains.

**Example Extensions:**
- Implementing a full UNIX OS as an extension on top of SPIN.
- Running a client-server application (like a video server and its display client) directly on top of SPIN without a traditional OS middleman.

### Event-Based Communication in SPIN
SPIN handles external events (interrupts, page faults, system calls) via an event dispatcher:
- **Event Handlers:** Services register handlers with the central dispatcher.
- **Mappings Supported:**
  - **1:1 Mapping:** E.g., ICMP packet arrival triggers the Ping application handler.
  - **1:Many Mapping:** E.g., IP packet arrival triggers UDP, TCP, and ICMP handlers.
  - **Many:1 Mapping:** E.g., Ethernet and ATM packet arrivals both map to the same IP handler.
- **Guards:** Handlers can specify guards for finer-grained execution (e.g., only execute the handler if the incoming packet is strictly an IP packet).

### Default Core Services in SPIN
SPIN provides interface functions (header files), while extensions implement the semantics:
- **Memory Management:** SPIN handles the macro-allocation of physical memory to extensions. Interface functions include allocating/deallocating frames and virtual pages, translating addresses, and event handlers for page/access faults.
- **CPU Scheduling:** Uses a global scheduler for macro-level time allocation. 
  - **Strand:** The abstraction for the unit of scheduling. The extension defines the exact semantics of a strand (e.g., mapping to POSIX threads).
  - Events provided include block, unblock, checkpoint, and resume.

---

## 4. The Exokernel Approach to Extensibility
**Core Idea:** Expose hardware explicitly to library operating systems (Library OS) and decouple the **authorization** of a hardware resource from its **actual use**.

### Secure Bindings
- The Library OS requests a resource. Exokernel validates the request, binds the resource, and returns an **encrypted key (capability)**.
- The Library OS presents this unforgeable key to the Exokernel for subsequent uses of the resource.
- *Result:* Establishing the secure binding is a heavy-duty operation, but using the binding occurs at hardware speeds with minimal Exokernel intervention.

### Mechanisms for Implementing Secure Bindings
1. **Hardware Mechanisms:** e.g., Granting a physical page frame, TLB entry, or portion of a frame buffer.
2. **Software Caching:** e.g., Shadow TLB (sTLB) to avoid massive context switch penalties.
3. **Downloading Code into Kernel:** e.g., Installing a packet filter or garbage collector. Allows the Library OS to inject code to run at kernel privilege, avoiding border crossings. 
   - *Security Note:* This compromises protection more than SPIN's language-enforced domains (since arbitrary code is injected), but is necessary for maximum performance.

### Exokernel Candidate Resources
- **TLB Entry:** The Library OS establishes a virtual-to-physical mapping and presents it to Exokernel with a key. Exokernel securely installs it into the hardware TLB. Future translations by the process happen entirely via hardware.
- **Packet Filter:** The Library OS loads predicates into the kernel. Exokernel automatically checks incoming packets against these predicates without expensive border crossings to the Library OS.

### Default Core Services in Exokernel
- **Memory Management (Page Faults):** 
  - A thread incurs a page fault. Exokernel fields it and kicks it up to the currently running Library OS via a registered handler.
  - The Library OS allocates a frame, maps the virtual page, and presents the mapping + encrypted key to Exokernel.
  - Exokernel validates the key and performs the privileged operation of installing the mapping into the hardware TLB.
- **CPU Scheduling:** 
  - Exokernel maintains a **linear vector of time slots (epochs)**. Each Library OS marks its time quantums at startup.
  - Exokernel enforces bounded time for context switching. If a Library OS misbehaves (takes too long to save context), Exokernel penalizes it by taking time off its next scheduled slot.
- **Revocation of Resources:**
  - Exokernel can reclaim resources via an upcall (`revoke`) providing a **repossession vector** (e.g., "taking away page frames 20 and 25").
  - The Library OS must take corrective action (e.g., stash frame contents to disk).
  - **Autosave Seeding:** A Library OS can pre-seed Exokernel with autosave instructions so Exokernel performs the cleanup (e.g., writing to disk) on its behalf during revocation.

### Exokernel Data Structures
- **PE (Processor Environment) Data Structure:** Maintained per Library OS. Contains entry points for handling program discontinuities:
  - Exceptions
  - External Interrupts
  - System Calls (Protected Entry Context)
  - Page Faults (Addressing Context)
- **Software TLB (sTLB):** Maintains a snapshot of "guaranteed mappings" for each Library OS. On a context switch, Exokernel dumps current guaranteed mappings into the outgoing OS's sTLB and preloads the incoming OS's sTLB into the hardware TLB, drastically mitigating the loss of locality.

---

## 5. Performance Results (SPIN vs. Exokernel)
- **Evaluation Context:** Systems research relies on building and measuring. SPIN and Exokernel were compared against Monolithic OS (Unix) and Microkernel OS (Mach).
- **Protected Procedure Calls (Cross-Domain):** Both SPIN and Exokernel vastly exceed the performance of the Mach microkernel.
- **System Calls:** Both SPIN and Exokernel perform just as well as traditional monolithic kernels, proving that extensibility can be achieved without sacrificing performance.

---

# Module 7: L3 Microkernel and OS Structuring

## Introduction
- **Historical Context:** Spin and Exokernel were built on the assumption that microkernel-based operating system structures are inherently poised for poor performance.
- **Mach Microkernel:** This assumption was largely based on Mach (developed at CMU), which was a popular microkernel of the time but prioritized *portability* over pure performance.
- **L3's Contrarian View:** The L3 microkernel provides a contrarian viewpoint, proving that a microkernel-based approach can achieve high performance.

## Microkernel-Based OS Structure (Refresher)
- **Core Concept:** The microkernel provides only a minimal set of simple abstractions.
- **Key Abstractions Provided:**
  - Address spaces
  - Threads
  - Inter-process communication (IPC)
  - Unique IDs (UIDs)
- **System Services:** Operating system services (e.g., file system, memory manager, CPU scheduling) are implemented as *user-level processes* running above the microkernel.
- **Privilege Levels:** 
  - System services run at the same privilege level as user applications, each in its own distinct address space.
  - Only the microkernel runs at the highest, processor-provided privilege level.
- **Cooperation:** Services cooperate to satisfy user requests via IPC, mediated by the microkernel.

## Potentials for Performance Loss (Strikes Against Microkernels)
Microkernel architectures face four main potential performance bottlenecks:

### 1. Border Crossing Costs (Explicit Cost)
- **Definition:** The cost of transitioning from user-level privilege (application) to kernel-level privilege (microkernel), and vice versa.
- **Impact:** Occurs frequently, as applications must cross the border for every system call.

### 2. Address Space Switches (Explicit Cost)
- **Definition:** The cost of moving between the distinct hardware address spaces of different system services.
- **Mechanism:** Cross-domain communication is implemented as *protected procedure calls*, which can be up to 100x more expensive than normal procedure calls.
- **TLB Impact:** Going across hardware address spaces minimally involves flushing the Translation Lookaside Buffer (TLB) to make room for the new domain's entries.

### 3. Thread Switches and IPC (Explicit Cost)
- **Definition:** The cost of the microkernel mediating communication between servers.
- **Impact:** Protected procedure calls require thread switches and IPC, both of which must be mediated by the kernel. The explicit cost involves saving and restoring volatile processor state (registers, etc.).

### 4. Memory Effects / Loss of Locality (Implicit Cost)
- **Definition:** The performance hit caused by changing locality when switching address spaces.
- **Impact:** The new thread may not find the cache "warm." Both TLB (address translation) and CPU caches (data and instructions) suffer cache misses, forcing the system to fetch from slower memory.

---

## Debunking the Myths: The L3 Microkernel Approach
L3 systematically debunks the performance myths of microkernels by *proof of construction*, arguing that poor performance is a result of **inefficient implementation**, not the microkernel principle itself.

### Debunking Myth 1: User-Kernel Border Crossing
- **L3 Performance:** L3 accomplishes a border crossing in just **123 processor cycles** (including TLB and cache misses).
- **Theoretical Minimum:** L3 calculates the absolute hardware minimum for this operation to be ~107 cycles. L3's implementation is incredibly close to this limit.
- **Comparison to Mach:** Mach took ~900 cycles on the exact same hardware.
- **The Real Culprit in Mach:** Mach's slow border crossings were due to its focus on *portability*. Architecture-independent code caused significant "code bloat," leading to a larger memory footprint, more cache misses, and longer latency.

### Debunking Myth 2: Address Space Switches
The cost of address space switches depends heavily on the processor's TLB architecture:

- **With Address Space Tagged TLB (e.g., MIPS):**
  - TLB entries include a Process ID (PID) tag.
  - The hardware matches both the PID and the virtual address tag.
  - **Result:** No TLB flush is required during a context switch.
- **Without Address Space Tagged TLB (e.g., Intel x86/Pentium):**
  - TLB flushes are normally required, but L3 uses clever hardware exploitation to avoid them.
  - **For Small Protection Domains:** L3 uses hardware **segment registers** to carve a single linear hardware address space into multiple smaller, protected regions. This bounds legal virtual addresses and avoids TLB flushes entirely.
  - **For Large Protection Domains:** If a service occupies the entire address space, a TLB flush is unavoidable. However, for large domains, the *implicit cost* (loss of cache locality) vastly dominates the *explicit cost* (TLB flush). This locality loss affects monolithic kernels and exokernels just as much.

### Debunking Myth 3: Thread Switches and IPC
- **L3 Performance:** By careful construction, L3 proves that thread switch times can be just as competitive and fast as those in Spin or Exokernel.

### Debunking Myth 4: Memory Effects
- **Small Domains:** By packing small protection domains into the same hardware address space (using segment registers), the caches remain "warm," mitigating locality loss.
- **Large Domains:** Cache pollution is an unavoidable consequence of executing large subsystems, regardless of whether the OS is monolithic or microkernel-based.

---

## L3's Thesis for OS Structuring
L3 goes beyond debunking myths to propose a definitive thesis for how operating systems should be built:

1. **Minimal Abstractions:** The microkernel must only provide the absolute minimum abstractions required by any subsystem: Threads, IPC, Address Spaces, and UIDs.
2. **Processor-Specific Implementation:** To achieve high performance, the microkernel must aggressively exploit specific hardware features. Therefore, **microkernels are inherently non-portable**.
3. **Processor-Independent Higher Layers:** By combining the right abstractions with a highly optimized, processor-specific microkernel, all high-level system services (file systems, networking, scheduling) can be built efficiently and in a processor-independent manner.
   - *Performance and portability are at loggerheads at the microkernel level, but can coexist at the subsystem level.*

## Conclusion
- The mid-90s saw contemporaneous, mutually informing innovations in OS structure: **Spin**, **Exokernel**, and **L3**.
- L3 proved that microkernel architectures are viable and highly performant.
- These principles heavily influenced modern OS design, laying the groundwork for concepts like dynamically loaded device drivers and, eventually, virtualization.


---

