# High Performance Computer Architecture (HPCA)
## Playlist 4, Module 1: Fault Tolerance & Dependability

This module introduces the fundamental concepts of fault tolerance, system dependability, and how we design computer architectures to function correctly even when individual components fail.

---

### 1. Dependability: The Core Concept

**Background Context:** In computer architecture, performance (speed) and efficiency (power) are often the primary focus. However, if a system crashes constantly or produces incorrect results, its speed is irrelevant. We need systems we can trust.

**Dependability** is the quality of delivered service that justifies relying on the system to provide its intended function. It revolves around two definitions of service:
- **Specified Service:** The ideal, expected behavior of the system (what it *should* do).
- **Delivered Service:** The actual behavior of the system (what it *actually* does).

A system is dependable if its delivered service consistently matches its specified service.

**Mental Model: The Modular System**
Think of a computer as a collection of interacting **modules** (e.g., processor, memory, hard drive). Each module has its own specified behavior. When a module deviates from its ideal behavior, it threatens the dependability of the entire system.

---

### 2. The Fault-Error-Failure Pipeline

When a system deviates from its specified behavior, we use three distinct terms to describe the breakdown. Understanding the causal relationship between these three is the most important concept in fault tolerance.

**Mental Model: The Chain Reaction**
`Fault (The Root Cause)` ➔ `Error (Internal Manifestation)` ➔ `Failure (External Impact)`

1. **Fault:** A deviation from specified behavior at the lowest level. It is the root cause. Faults can be **latent** (dormant), meaning they exist but haven't caused any problems yet. 
2. **Error:** The internal state of the system becomes incorrect. An error occurs when a fault is **activated**.
3. **Failure:** The system as a whole deviates from its specified behavior. This is when the user or external environment actually experiences the problem.

#### Crucial Intuitions
* **A fault does not always cause an error:** A software bug (fault) only causes an error if that specific line of buggy code is executed.
* **An error does not always cause a failure:** A bit in memory might flip (error), but if the system never reads that memory location, or if the corrupted value doesn't affect the final output, the system never fails.

#### Examples
**Example 1: The Buggy `add()` Function**
* **The Setup:** You write an `add(a, b)` function. It works perfectly, except `add(5, 3)` incorrectly returns `7` instead of `8`.
* **The Fault:** The programming mistake itself (a latent fault).
* **The Error:** You call `add(5, 3)` and store `7` in a CPU register. The internal state is now wrong (an effective error).
* **The Failure:** That register is used to schedule a critical calendar meeting for 7:00 AM instead of 8:00 AM. The system failed its specified service.

**Example 2: The Dropped Laptop (Quiz)**
* **Scenario:** A laptop falls out of a bag, hits the pavement. The pavement cracks, winter expands the crack, and eventually, the pavement breaks and must be replaced.
* **The Fault:** The laptop hitting the pavement (the event that sparked the problem).
* **The First Error:** The pavement developing a crack (internal structural integrity is compromised, but it still functions as pavement).
* **The Failure:** The pavement breaks completely (it can no longer perform its function as a walking surface).

---

### 3. Metrics: Reliability vs. Availability

Dependability is a broad concept; **Reliability** and **Availability** are how we mathematically measure it.

A system transitions between two states:
* **Service Accomplishment:** Functioning normally.
* **Service Interruption:** Down/broken.

#### Reliability (MTTF)
Reliability measures continuous, uninterrupted service.
* **Metric:** **MTTF** (Mean Time To Failure). 
* **Intuition:** "How long will this system run before it breaks?"
* **Use Case:** Critical for systems where any failure is catastrophic (e.g., airplane flight controls, space shuttles). A system that runs for 1 year, fails, and runs for another year has an MTTF of 1 year.

#### Availability
Availability measures the overall fraction of time the system is in the service accomplishment state.
* **Metric:** Percentage of uptime. 
* **Formula:** `Availability = MTTF / (MTTF + MTTR)`
    * *MTTR = Mean Time To Repair (how long it takes to fix the system after a failure).*
* **Intuition:** "What are the odds the system is working right now when I need it?"
* **Use Case:** Critical for web servers (e.g., Google, Amazon). It's acceptable if individual servers fail frequently (low MTTF) as long as they reboot or are replaced almost instantly (extremely low MTTR), resulting in high availability ("five nines" or 99.999% uptime).

**Availability Quiz Example:**
A hard disk works for 12 months, breaks (1 month to repair), works for 4 months, breaks (2 months to repair), works for 14 months, breaks (3 months to repair).
* **MTTF:** (12 + 4 + 14) / 3 = **10 months**
* **MTTR:** (1 + 2 + 3) / 3 = **2 months**
* **Availability:** 10 / (10 + 2) = 10 / 12 = **83.33%**

---

### 4. Classifying Faults

Understanding what kind of fault you are dealing with dictates how you defend against it.

#### Classification by Cause
1. **Hardware Faults:** Physical components fail (e.g., a transistor degrades).
2. **Design Faults:** Mistakes made by humans during creation. Includes software bugs and hardware logic errors (e.g., the infamous Intel Pentium FDIV bug where division logic was flawed).
3. **Operation Faults:** User or administrator mistakes (e.g., accidentally typing a shutdown command on a production server).
4. **Environmental Faults:** External physical factors (e.g., fire in the data center, power outages, sabotage).

#### Classification by Duration
1. **Permanent:** The fault stays until physically repaired (e.g., a processor physically snaps in half; a permanent software design flaw).
2. **Intermittent:** The fault recurs repeatedly but isn't constantly active (e.g., a loose wire that disconnects when it vibrates, or a CPU that crashes only when it overheats due to overclocking).
3. **Transient:** A one-time event that disappears. If you reboot, the system is fine (e.g., a cosmic alpha particle strikes a memory chip and flips a bit).

**Quiz Example: The Wet Phone**
You drop your phone in water. It has a wetness sensor meant to prevent it from turning on, but the sensor fails. You turn it on, it heats up, and explodes.
* **Getting wet:** Environmental (cause), Transient (duration - it would eventually dry).
* **Sensor failing to prevent boot:** Design fault (cause - flawed logic/hardware), Permanent (duration).
* **Explosion:** Permanent fault (duration - it's permanently destroyed).

---

### 5. Improving Dependability: Avoidance vs. Tolerance

How do we build better systems? We use a combination of two philosophies:

1. **Fault Avoidance:** Preventing faults from occurring in the first place.
    * *Example:* "No coffee allowed in the server room" prevents environmental faults. Strict code-review processes avoid design faults.
2. **Fault Tolerance:** Accepting that faults *will* occur, and designing the system to prevent those faults from escalating into failures.
    * *Example:* **ECC (Error Correcting Code) Memory.** If a transient fault (alpha particle) flips a bit in RAM (error), ECC logic detects the flipped bit and corrects it before the CPU uses it. The fault never becomes a system failure.
3. **Speeding up Repair (Availability):** Keeping a spare hard drive on-site. The failure still happens, but MTTR is drastically reduced, improving overall availability.

---

### 6. Architectural Fault Tolerance Techniques

If we want our hardware to be fault-tolerant, we implement specific architectural strategies.

#### 1. Checkpointing
* **Mechanism:** The system periodically saves its known-good state. If an error is detected, the system "rolls back" to the last safe checkpoint and resumes.
* **Best for:** Transient and Intermittent faults. If an alpha particle flips a bit, rolling back and recalculating will likely succeed because the particle is gone.
* **Caveat:** Checkpointing must be fast. If it takes too long to save/restore state, the delay itself becomes a "service interruption."

#### 2. N-Modular Redundancy (NMR)
Redundancy involves running multiple identical modules to do the same work.

* **2-Way Redundancy:** Two modules compute the same task. We compare their outputs. 
    * *Benefit:* Excellent **Error Detection**. If results differ, we know a fault occurred.
    * *Drawback:* Cannot correct the error on its own (doesn't know *which* module is right). Requires a rollback/checkpointing mechanism to recover.
* **3-Way Redundancy (TMR - Triple Modular Redundancy):** Three modules do the same work. A "voter" circuit compares the three outputs.
    * *Benefit:* **Error Detection AND Correction**. If one module fails and outputs `5`, but the other two output `8`, the voter takes the majority (`8`). The system successfully masks the fault.
    * *Drawback:* Expensive (3x the hardware, plus the voter circuit). Cannot tolerate 2 simultaneous faults.
* **General N-Way Redundancy:** Used in ultra-critical systems. 
    * *Example:* The Space Shuttle used 5 redundant computers. If one failed, the system fell back to 4. If another failed, 3. This allowed the shuttle to sustain multiple consecutive faults without aborting the mission or losing control.

*(Note: The auto-generated transcript near the end regarding N-Modular Redundancy and Space Shuttles is highly garbled due to captioning errors, but the underlying architectural principle taught in this segment is N-Modular Redundancy and majority voting.)*