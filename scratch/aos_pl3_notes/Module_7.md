# Playlist 3 Module 7: Time-Sensitive Linux

## Introduction
Traditionally, general-purpose operating systems catered to throughput-oriented applications (e.g., databases, scientific apps). However, there is a growing need to support soft real-time guarantees for latency-sensitive applications (e.g., synchronous AV players, video games).

**Time-Sensitive (TS) Linux** is an extension of the commodity general-purpose Linux operating system that addresses two main questions:
1. How to provide guarantees for real-time applications in the presence of background throughput?
2. How to bound the performance loss of throughput-oriented applications in the presence of latency-sensitive applications?

## Sources of Latency
Time-sensitive applications require immediate responses to events. In a typical general-purpose OS, there are three primary sources of latency that increase the distance between **Event Happening** and **Event Activation** (the point where the app is scheduled to react):

1. **Timer Latency:** Inaccuracy of the timing mechanism.
   - The delay between when an event should have triggered an interrupt and when the timer interrupt actually occurs, primarily due to the coarse granularity of periodic timers (e.g., 10ms in standard Linux).
2. **Kernel Preemption Latency:** The delay caused when the kernel cannot be interrupted.
   - Occurs when the kernel is modifying critical shared data structures (interrupts are turned off) or is already handling a higher-priority interrupt.
3. **Scheduler Latency:** The delay in scheduling the required process after the interrupt is delivered.
   - The application waiting for the timer event cannot be scheduled immediately because a higher-priority task is occupying the CPU.

## Types of Timers
An OS typically provides different timer mechanisms, each with pros and cons:

- **Periodic Timers** (Standard in UNIX)
  - **Pro:** Periodicity reduces willy-nilly interruptions.
  - **Con:** High event recognition latency; worst-case latency equals the period length itself.
- **One-Shot Timers**
  - **Pro:** High timeliness and exact accuracy.
  - **Con:** High processing and reprogramming overhead for every single interrupt.
- **Soft Timers**
  - **Pro:** Extremely low interrupt overhead, as they avoid timer interrupts entirely.
  - **Mechanism:** The kernel polls for events at strategic points (e.g., during system calls or external network interrupts).
  - **Con:** Polling latency and the overhead of checking all events to see if any expired.

## Firm Timer Design
**Firm Timer** is a novel mechanism in TS Linux that combines the benefits of Periodic, One-Shot, and Soft timers to provide accurate timing with very low overhead.

### The "Overshoot" Parameter
- **Mechanism:** A one-shot timer is programmed to fire slightly *after* the exact event time. This delay is the "overshoot window."
- **Soft Timer Synergy:** If a system call or external interrupt brings execution into the kernel *during* this overshoot window, the kernel dispatches the expired timer immediately and reprograms it for the next event.
- **Benefit:** It achieves the accuracy of a one-shot timer but frequently avoids the actual hardware interrupt cost (acting like a soft timer).

### Long-Distance Optimization (Periodic Synergy)
- **Mechanism:** If there is a long time distance between two one-shot events, there will likely be several standard periodic timer interrupts occurring in between. 
- **Action:** The kernel dispatches the upcoming one-shot event slightly early, during a preceding periodic interrupt.
- **Benefit:** Eliminates the use of expensive one-shot timers altogether for distant events. Periodic timer data structures ($O(1)$) are much more efficient than one-shot timer structures ($O(\log N)$).

## Firm Timer Implementation
- **Hardware Support:** Relies on the **APIC (Advanced Programmable Interrupt Controller)**, available on modern CPUs (Intel Pentium+).
  - Reprogramming an APIC one-shot timer takes only a few CPU cycles, making overhead negligible.
  - Theoretical accuracy is 10ns (on a 100MHz bus), though limited in practice by interrupt handling time.
- **Data Structure:** Uses a timer queue where tasks are sorted by their expiry time. 
- **Execution:** When the APIC timer expires, the interrupt handler triggers the callback for the expired task, removes it from the queue, and reprograms the timer (either periodic or one-shot) for the next event.

## Reducing Kernel Preemption Latency
To prevent delays when the kernel is busy manipulating shared data, TS Linux employs a **Lock-Breaking Preemptable Kernel** (a technique due to Robert Love).

- **Core Ideas Combined:**
  1. Explicitly inserting preemption points in the kernel.
  2. Allowing preemption anytime the kernel is *not* manipulating shared data structures.
- **Mechanism:** Long critical sections are broken down. The kernel acquires a lock, manipulates shared data, **releases the lock, checks for expired timers/preemptions**, and then reacquires the lock to continue.
- **Benefit:** Safely reduces spin-lock holding times and creates more opportunities for the kernel to respond to latency-sensitive events.

## Reducing Scheduling Latency
Once the timer event is handled, the scheduler must act fast. TS Linux addresses scheduler latency through two mechanisms:

### 1. Proportional Period Scheduling
- **Mechanism:** Applications request a specific proportion of CPU time ($Q$) per time quantum/window ($T$). 
- **Admission Control:** The scheduler only admits a task if the system can accommodate the requested capacity.
- **Benefits:** 
  - Provides temporal protection and highly accurate scheduling for time-sensitive tasks.
  - Allows TS Linux to reserve a fixed proportion of CPU time strictly for throughput-oriented tasks, ensuring they are not starved and can still make forward progress.

### 2. Priority-Based Scheduling (Addressing Priority Inversion)
- **The Problem (Priority Inversion):** A high-priority task ($C_1$) makes a blocking call to a low-priority server. While the server is executing, a medium-priority task ($C_2$) becomes runnable and preempts the server. Now, $C_1$ is indirectly delayed by $C_2$.
- **The Solution (Priority Inheritance):** When $C_1$ makes a request to the server, the server's priority is boosted to match $C_1$'s priority.
- **Benefit:** $C_2$ can no longer preempt the server, completely eliminating priority inversion.

## Conclusion
By fixing the three primary sources of latency, TS Linux successfully provides Quality of Service (QoS) guarantees for real-time applications on commodity operating systems. 

**Summary of TS Linux Innovations:**
1. **Firm Timers:** High timer accuracy without exorbitant overhead.
2. **Lock-Breaking Preemptable Kernel:** Significantly reduced kernel preemption latency.
3. **Proportional & Priority-Based Scheduling:** Minimized scheduler latency, prevention of priority inversion, and protected CPU time for throughput applications.
