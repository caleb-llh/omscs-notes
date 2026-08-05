# Module 2: Advanced Fault Tolerance, Memory Protection, and RAID

## 1. N-Modular Redundancy (NMR)

**Background & Intuition:**
N-Modular Redundancy (NMR), commonly implemented as Triple Modular Redundancy (TMR), is a hardware-level fault tolerance technique. It involves running the exact same computation on multiple identical hardware modules (e.g., three identical computers). Their outputs are compared, and the final result is determined by a majority vote (e.g., two or three out of three agree). 

*Mental Model:* Think of a panel of three judges. If one judge gets distracted and hallucinates an answer, the other two will still agree, and the correct decision is reached by the majority.

**Capabilities & Limitations:**
Replicating identical hardware in the same location only protects against specific types of isolated faults:
- **Tolerated (Single Event Upsets):** 
  - An **alpha particle strike** hitting a single processor. The affected processor may output garbage, but the other two processors remain unaffected and agree on the correct result.
- **Not Tolerated (Correlated Failures):**
  - **Building collapses / Earthquakes:** A localized physical disaster will destroy all collocated computers simultaneously. *(Solution: Geographic distribution).*
  - **Design Mistakes / Processor Bugs:** Because the hardware is *identical*, a fundamental design flaw will manifest in all three processors at the exact same time, causing them to agree on the *wrong* result. *(Solution: N-Version Programming, where different teams design processors with different architectures).*

---

## 2. Fault Tolerance for Memory and Storage

**Background & Intuition:**
Using Dual or Triple Modular Redundancy for memory and storage is overkill and prohibitively expensive. NMR is usually reserved for computational hardware (processors) where cheaper error-correction techniques aren't feasible. For memory and storage, we can use Error Detection and Correction (EDC) codes, which append a small amount of redundant information to detect and fix bit flips.

*Mental Model:* Instead of sending three identical letters to guarantee the message arrives (NMR), you send one letter with a mathematical "checksum" at the bottom. If a few letters get smudged, the receiver can use the checksum to deduce the missing characters.

**Key Techniques:**
1. **Parity Bit:** 
   - **Mechanism:** Adds 1 extra bit to the data bits, computed simply as the XOR sum of all the data bits. 
   - **Capability:** Detects any single-bit flip (the parity bit will no longer match the XOR of the read data bits). However, it *cannot* correct the error.
2. **Error Correction Codes (ECC):**
   - **Mechanism:** Uses more sophisticated coding, commonly **SECDED** (Single Error Correction, Double Error Detection).
   - **Capability:** Can detect *and fix* any single-bit flip on the fly (users won't even notice it happened). If two bits flip, it detects the error and halts the system to prevent data corruption, but cannot correct it.
3. **Advanced Codes (Reed-Solomon):**
   - **Mechanism:** Used extensively in hard drives to detect and correct multiple bit errors.
   - **Capability:** Especially powerful against a "streak" or "burst" of flipped bits. 
   - **Example:** If a spinning hard drive head oscillates and flies too high above the platter, it might miss a whole contiguous sequence of bits. Reed-Solomon can reconstruct this burst of missing data.

---

## 3. RAID 0 (Striping)

**Background & Intuition:**
RAID (Redundant Array of Independent Disks) groups multiple physical disks into a single logical unit. 
**RAID 0** focuses entirely on **performance** through *striping*. It has zero redundancy.

*Mental Model:* Imagine having to read a 100-page book. If one person reads it, it takes 100 minutes. If two people read it simultaneously (one reads the even pages, the other reads the odd pages), it takes 50 minutes.

**How it Works (Performance & Capacity):**
- A physical disk has tracks. Accessing them sequentially limits throughput because the read/write head must physically move and wait for rotation.
- RAID 0 spreads logical "stripes" across multiple disks. For two disks: Disk A gets Stripe 0, Disk B gets Stripe 1, Disk A gets Stripe 2, Disk B gets Stripe 3, etc.
- **Throughput:** Assuming requests are evenly spread, $N$ disks provide nearly $N \times$ the throughput of a single disk. If Disk A and Disk B read data simultaneously, the system bus handles the combined data rate.
- **Latency:** Because the array has higher throughput, it processes the queue faster, resulting in less queuing delay for incoming requests.
- **Capacity:** $N \times$ Capacity of a single disk.

**Reliability (MTTF - Mean Time To Failure):**
- *Warning:* RAID 0 decreases reliability. If *any* disk fails, the entire array's data is lost.
- **Formula:** The failure rate of the array is $N \times$ the failure rate of a single disk. Therefore, the Mean Time To Data Loss (MTTDL or MTTF) is:
  $$MTTF_{RAID0} = \frac{MTTF_{Single Disk}}{N}$$
- **Example Quiz:** For a 4-disk RAID 0 array using 200 GB disks (10 MB/s throughput, 100,000 hours MTTF):
  - **Capacity:** 800 GB
  - **Throughput:** 40 MB/s
  - **MTTF:** 100,000 / 4 = 25,000 hours (~2.85 years). *Note: The array is highly likely to fail within a typical 5-year hardware lifespan.*

---

## 4. RAID 1 (Mirroring)

**Background & Intuition:**
**RAID 1** focuses on **reliability** through *mirroring*. It duplicates the exact same data across two (or more) disks. 

*Mental Model:* Keeping an exact photocopy of your passport in a separate secure drawer. If you lose the original, you have a perfect backup ready immediately.

**Performance & Capacity:**
- **Capacity:** Equal to the capacity of just *one* disk. You pay for two disks but only get the storage space of one.
- **Throughput (Reads):** Twice as fast ($2 \times$ throughput) because the controller can fetch different data from both disks simultaneously.
- **Throughput (Writes):** Same speed as a single disk ($1 \times$ throughput) because every write must be committed to *both* disks.
- **Mixed Workload Example:** Suppose a workload is 50% reads and 50% writes (by number of requests) on a 2-disk RAID 1 array (single disk throughput = 10 MB/s). 
  - Because reads are twice as fast (20 MB/s), they take half the time of writes (10 MB/s). 
  - In 1 second, the system spends $1/3$ sec reading (fetching $\approx 6.67$ MB) and $2/3$ sec writing (writing $\approx 6.67$ MB). 
  - Total throughput is $13.33 \text{ MB/s}$ (not the naive average of 15 MB/s).

**Reliability (MTTF & MTTR):**
- **Scenario A: No Replacement (Theoretical & Bad Practice)**
  - If a disk fails and is *never* replaced, the array survives until the first disk fails ($MTTF_{single} / 2$), and then the remaining single disk survives for its expected lifespan ($MTTF_{single}$).
  - Total time to data loss = $1.5 \times MTTF_{single}$. This is a terrible return on investment for buying two disks!
- **Scenario B: With Replacement (Practical & Intended Use)**
  - When a disk fails, it must be replaced immediately. The time it takes to swap the hardware and rebuild the data copy is the **Mean Time To Repair (MTTR)** (e.g., 24 hours).
  - The array only suffers total data loss if the *second* disk fails *during the MTTR rebuild window* of the first disk.
  - Probability of second disk failing during repair $\approx \frac{MTTR}{MTTF}$.
  - Expected number of successful repairs before a double-fault $\approx \frac{MTTF}{MTTR}$.
  - **MTTDL (Mean Time To Data Loss) Formula:**
    $$MTTDL_{RAID1} = \frac{MTTF_{Single Disk}^2}{2 \times MTTR}$$
  - **Example Quiz:** Single disk MTTF = 100,000 hours. MTTR = 24 hours. 
    - $MTTDL = \frac{100,000^2}{2 \times 24} = \frac{10,000,000,000}{48} \approx 208,333,333 \text{ hours}$ (over 23,000 years).
  - *Takeaway:* Actively replacing failed disks turns a 10-year disk reliability into a practically immortal 23,000-year array reliability. RAID 1 is dramatically effective at preventing data loss.
