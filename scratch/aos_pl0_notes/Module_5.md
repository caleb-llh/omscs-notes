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