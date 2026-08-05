# High Performance Computer Architecture: Module 3 (Part 5) - RAID & Fault Tolerance

Welcome to the detailed notes for Module 3 (Part 5) of the High Performance Computer Architecture (HPCA) course! This module dives deep into **RAID (Redundant Array of Independent Disks)** performance, reliability mathematics, parity-based error detection in DRAM, and an introduction to multiprocessing. 

These notes have been synthesized to ensure *no information is lost* from the original lectures, while adding background contexts, intuitions, and examples to make the concepts easier to digest.

---

## 1. RAID 1: Performance and Reliability (Deep Dive)

**Background Context:** RAID 1 is also known as "mirroring." The intuition is simple: write the exact same data to two separate disks. If one dies, the other has a perfect copy. 

### Capacity and Throughput
Let's analyze a 2-disk RAID 1 array where each disk has:
- **Capacity:** 200 GB
- **Throughput:** 10 MB/s
- **MTTF (Mean Time To Failure):** 100,000 hours
- **MTTR (Mean Time To Repair):** 24 hours (time to swap in a new disk and copy data over)

* **Capacity:** 200 GB (Data capacity equals a single disk because both store identical data).
* **Read Throughput:** 20 MB/s. (Reads can be issued to both disks simultaneously, doubling the bandwidth).
* **Write Throughput:** 10 MB/s. (Writes must go to *both* disks at once, so it operates at the speed of a single disk).

### The "50/50 Workload" Trap
**Mental Model:** You cannot simply average the read and write throughputs (e.g., $(20 + 10) / 2 = 15$ MB/s). Why? Because reads process twice as fast as writes, they consume less *time*!

If a workload is 50% reads and 50% writes (by number of accesses), you spend disproportionately more time waiting for writes to finish.
* In 1 second, to keep the number of reads and writes equal, you spend **1/3 of a second reading** (at 20 MB/s) and **2/3 of a second writing** (at 10 MB/s).
* Data read in 1/3 sec = $20 \times (1/3) = 6.67$ MB.
* Data written in 2/3 sec = $10 \times (2/3) = 6.67$ MB.
* Total data processed in 1 second = $13.33$ MB.
* **True Throughput = 13.33 MB/s** (not 15 MB/s!).

### RAID 1 Reliability (MTTF)
How reliable is this 2-disk array?
1. The MTTF for the *first* disk failure is $100,000 / 2 = 50,000$ hours (since either of the two disks could fail first).
2. When a disk fails, you have 24 hours to repair it. The chance of the *surviving* disk failing during this 24-hour window is the ratio of MTTF to MTTR: $100,000 / 24 = 4,166.66$. 
3. This means you can successfully survive and repair a single disk failure about 4,166 times before you statistically encounter a second disk failure *during* a rebuild.
4. **Total RAID 1 MTTF:** $50,000 \times 4,166.66 \approx 208,333,333$ hours (about **24,000 years**!).
*Takeaway:* RAID 1 dramatically improves data reliability from 11 years (single disk) to tens of thousands of years.

---

## 2. RAID 4: Block Interleaved Parity

**Background Context:** RAID 3 is rarely used today, so we skip to RAID 4. RAID 4 is crucial for understanding RAID 5. Instead of mirroring everything (which wastes 50% of your drives), RAID 4 uses **parity** to save space while still surviving a disk failure.

### How it Works
* Uses $N$ disks. 
* $N-1$ disks hold actual data (striped across them like RAID 0).
* The **last disk** is dedicated purely to holding **parity blocks**.
* **Parity Computation:** The parity bit is calculated by XOR-ing the bits across the data disks. (e.g., $Bit_1 \oplus Bit_2 \oplus Bit_3 = Parity$).
* If one disk fails, you can mathematically reconstruct its lost data by XOR-ing the surviving data disks and the parity disk. 

*Intuition:* Mirroring is just an extreme case of RAID 4 where $N=2$. If you have 1 data disk and 1 parity disk, XOR-ing a single bit with nothing just gives you the same bit—hence, a mirror.

### Cost vs. Mirroring
In a 4-disk RAID 4 array, 3 disks are data, 1 is parity. You only sacrifice **25%** of your capacity to redundancy, compared to **50%** in RAID 1. 

### RAID 4 Performance
* **Reads:** Excellent! You can read from all $N-1$ data disks in parallel. (e.g., 3x throughput in a 4-disk array). You don't need to read the parity disk during normal operations.
* **Writes:** Terrible! Every single write operation must update the data disk *and* the dedicated parity disk.
  * To update parity, the system must: **Read** old data, **Read** old parity, **Write** new data, **Write** new parity.
  * Because *every* write hits the parity disk, the parity disk becomes a massive bottleneck.
  * **Write throughput is strictly limited to 1/2 the throughput of a single disk**, regardless of how many data disks you add.

### RAID 4 Reliability
If you do *not* replace failed disks, RAID 4 is mathematically **less reliable** than a single disk (because you now rely on a chain of disks, and the first failure compromises the array's safety net). You *must* perform repairs.

With repairs, the MTTF formula is:
$$ \text{MTTF}_{RAID4} = \frac{\text{MTTF}_{disk}^2}{N \times (N-1) \times \text{MTTR}} $$
For a 5-disk array (4 data, 1 parity) with the same specs as before:
* Total capacity: 800 GB (4 $\times$ 200 GB)
* Read throughput: 40 MB/s (4 $\times$ 10 MB/s)
* Write throughput: 5 MB/s (1/2 of a single disk)
* MTTF: Over 2,000 years! (Lower than RAID 1's 24,000 years, but highly acceptable given the capacity savings).

---

## 3. Hardware Interlude: Parity in DRAM

**Background Context:** Parity isn't just for hard drives; it's used in memory (RAM) to detect bit flips caused by cosmic rays or electrical interference.

Imagine we have an unprotected 8-bit memory system made of eight $1024 \times 1024$ bit arrays (each array supplies 1 bit of an 8-bit word). We want to add 1 parity bit for every 4 data bits. 

**Design Question:** Should we widen each existing array to hold the parity bits (fine-grained), or add two completely separate 1-bit array modules (coarse-grained)?

**Answer:** Adding **separate, extra modules** is far superior for two reasons:
1. **Design Reusability:** You don't have to custom-redesign the internal layout of the memory chips. You just use standard chips and add two more of them to the board.
2. **Geographical Distribution of Risk (Fault Tolerance):** If a component fails locally—such as a row decoder breaking and reading an entire row as zeros—the error is contained. If parity was built into the same row, the broken decoder would read the *wrong row's* parity, which would mathematically validate the wrong data! By keeping parity on separate physical chips, a catastrophic failure on a data chip will be instantly caught because the independent parity chip is still reading the correct parity data. 
*Mental Model:* Don't put the backup generator in the same room as the primary generator; if the room floods, you lose both.

---

## 4. RAID 5: Distributed Block Interleaved Parity

**Background Context:** RAID 4's dedicated parity disk is a massive write bottleneck. RAID 5 fixes this beautifully by spreading the workload.

### How it Works
RAID 5 takes the parity blocks and **distributes them in a round-robin fashion** across *all* the disks in the array. 
* Stripe 1: Parity is on Disk 4.
* Stripe 2: Parity is on Disk 3.
* Stripe 3: Parity is on Disk 2.
...and so on.

### Performance Improvements
* **Reads:** Even better than RAID 4. Because data is spread across *all $N$* disks (since no disk is exclusively parity), you can utilize the read bandwidth of all $N$ disks (statistically speaking).
* **Writes:** The massive bottleneck is gone! While a write still requires 4 accesses (Read old data/parity, Write new data/parity), these accesses are now distributed across all $N$ disks rather than hammering a single parity drive. 
* **Write Throughput:** $(N / 4) \times (\text{Single Disk Throughput})$. For a 5-disk array, write throughput is $5/4 = 1.25 \times$ a single disk (e.g., 12.5 MB/s), which is vastly superior to RAID 4's strict 5 MB/s limit.

### Reliability
RAID 5 has the exact same fault tolerance as RAID 4: it can survive the loss of **exactly 1 disk**. 

---

## 5. RAID 6: Double Parity (Is it Overkill?)

**Background Context:** What if one disk fails, and while you are rebuilding it (which can take hours or days), a *second* disk fails? In RAID 5, your entire array is destroyed. Enter RAID 6.

### How it Works
RAID 6 stores **two different types of parity blocks** (using different mathematical check equations) per stripe. 
* It can survive **2 simultaneous disk failures**.
* **Overhead:** You lose the capacity of 2 disks instead of 1.
* **Write Penalty:** A write now requires **6 accesses** (Read old data + 2 old parities, Write new data + 2 new parities).

### Is RAID 6 Overkill?
Mathematically, the probability of two independent drives randomly failing within the 24-hour rebuild window is astronomically low. So why pay the performance and capacity penalty of RAID 6?

**The Argument for RAID 6: Correlated Failures**
Failures in the real world are rarely independent. A classic "correlated failure" scenario:
1. Disk 2 fails in a RAID 5 array. The system stays online.
2. A human operator goes to the server rack to replace Disk 2.
3. Because the drives were labeled 0, 1, 2, 3, 4, the operator accidentally pulls out the *third* drive in the physical rack instead of the drive logically labeled "2".
4. *Boom.* A second drive is removed while the array is degraded. The RAID 5 array is completely destroyed due to human error.

In RAID 6, if the operator pulls the wrong drive, the array simply degrades to its secondary parity and stays alive, giving the operator time to realize their mistake, plug the drive back in, and pull the correct one. **RAID 6 protects against correlated failures and human error.**

---

## 6. Introduction to Multiprocessing

**Background Context:** As we wrap up fault tolerance, we shift our view to the future of computer architecture.
* Historically, executing multiple threads or processes simultaneously was reserved for massive supercomputers or high-end servers.
* Today (and in the foreseeable future), almost every consumer device—from smartphones to laptops—has **multiple cores**, often with multiple threads per core (e.g., Hyper-Threading).
* **Takeaway:** All modern processing is essentially multi-processing. To squeeze performance out of modern hardware, we must understand how to architect for parallel execution, which is the focus of upcoming modules. 
