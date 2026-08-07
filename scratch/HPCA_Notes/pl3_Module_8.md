# Module 8: Storage Devices & I/O

Welcome to Module 8! In this module, we transition from processors and memory down to **Storage Devices and I/O (Input/Output)**. We will explore how different storage technologies work under the hood, how their performance is measured, and how they physically connect to the rest of the computer system.

---

## 1. Access Time for Magnetic Disks

**🧠 Mental Model: The Record Player**
> Think of a magnetic hard drive like a classic vinyl record player. To play a specific part of a song, you first have to move the mechanical arm (the head) over the correct groove on the record (the cylinder/track). Then, you have to wait for the record to spin until the exact start of the song segment (the sector) passes under the needle.

When you request data from a magnetic disk, the time it takes to actually get that data (assuming the disk is already spinning) is called the **Disk Access Time**. It consists of several components:

1. **Seek Time**: The time it takes to mechanically move the head assembly to the correct cylinder (track) where the data resides. 
2. **Rotational Latency**: Once the head is over the correct track, the disk platter is still spinning. Rotational latency is the time spent waiting for the start of the desired sector to rotate and position itself under the head. On average, this takes **half of a full rotation**.
3. **Data Read (Transfer) Time**: The time it takes for the sector to actually pass under the head so the data can be read. This depends heavily on how fast the disk spins and how many sectors are packed into a single track. (e.g., if a track has 10 sectors, reading one sector takes 1/10th of a rotation).
4. **Controller Time**: The time it takes for the disk's built-in controller to verify checksums and ensure the sector's data isn't corrupted.
5. **I/O Bus Time**: The time required to transmit the read data from the disk drive's controller over the bus (cable) into the computer's main memory.

**⚠️ Queuing Delay**
Unlike RAM, which can handle multiple data accesses simultaneously, a magnetic disk has a single mechanical head assembly. It can only seek to one track and read one piece of data at a time. If the OS sends multiple requests, they form a queue. The total latency for a request often includes a **significant queuing delay** while waiting for previous physical disk operations to finish.

### 📝 Example: Calculating Access Time
Imagine a disk with the following specs:
* **1000 cylinders** (tracks) numbered 0 to 999.
* **10 sectors** per track.
* **Head starts at cylinder 0**.
* **Seek speed**: 10 microseconds (µs) per cylinder.
* **Rotational speed**: 100 rotations per second.
* *Assume perfect controller and bus (0 delay), and no queuing delay.*

**Question**: What is the average time to read a randomly chosen byte?

**Calculation**:
1. **Average Seek Time**: The byte could be on any cylinder with equal probability. On average, the head must move across half the disk (500 cylinders).
   * `500 cylinders × 10 µs/cylinder = 5000 µs = 5 milliseconds (ms)`
2. **Average Rotational Latency**: On average, we wait for half a rotation.
   * 1 full rotation takes `1 second / 100 = 0.01s = 10 ms`.
   * Half a rotation = `5 ms`.
3. **Data Read Time**: We need to read the sector containing the byte. There are 10 sectors per track, so reading one sector takes 1/10th of a rotation.
   * `1/10 × 10 ms = 1 ms`.
   
**Total Average Access Time** = `5 ms + 5 ms + 1 ms = 11 ms`.

---

## 2. Trends for Magnetic Disks

While magnetic disk **capacities** (how many gigabytes you can store) have grown exponentially over the years, their **mechanical properties** (seek time, rotational speed) have improved very slowly. 

**Insight**: It is physically difficult to make a mechanical platter spin significantly faster without it shattering, or to move a physical metal arm much faster without breaking it. Therefore, while we can pack data much more densely (improving capacity and transfer rates), the fundamental latency of seeking and waiting for rotations remains a severe bottleneck.

---

## 3. Optical Disks (CDs, DVDs)

Optical disks are structurally similar to magnetic disks—they have rotating platters and tracks. However, instead of using magnetism, they use a **laser** to read reflections off the disk surface to determine 0s and 1s.

**🌟 Advantages over Magnetic Disks:**
* **Resilience to Dust & Dirt**: A magnetic disk head hovers incredibly close to the platter; a single speck of dust can crash the head, scratch the surface, and destroy the drive. Thus, hard drives must be sealed in enclosed cases. Optical drives read from a distance using light. A speck of dust won't crash the laser, making optical disks durable enough to be portable.

**📉 The Cost of Standardization:**
Because optical disks are meant to be portable and shared, they require strict industry **standardization** (e.g., the exact format of a CD or DVD). 
* Technology might improve rapidly in a lab, but consumers won't see it until a massive committee agrees on a new standard (like transitioning from DVD to Blu-ray) and releases compliant products.
* **Magnetic hard drives**, on the other hand, are sealed "black boxes." As long as the *outside* connector (like SATA) meets standard, engineers can radically change and improve the *inside* technology with every new model. This allows magnetic disks to evolve much faster.

---

## 4. Magnetic Tape

Magnetic tape (similar to a cassette tape) is traditionally used for **secondary storage** and **backups**. 

* **Sequential Access**: Tape is fundamentally sequential. To read data in the middle of a tape, you must physically fast-forward past all the preceding data. 
* **Use Cases**: It is terrible for random access (like running an OS or acting as virtual memory), but excellent for reading/writing massive, continuous blocks of data (like a full system backup).

**Current Trends**:
Tapes are slowly dying out. Because relatively few people use tapes compared to hard drives, they lack the massive economies of scale. Hard drives are mass-produced so cheaply that today, it is often more cost-effective to just buy an external USB hard drive for backups than to invest in specialized tape reels and reading machines.

> 🐱 **Fun Fact**: If you want to make a cat happy, give it a reel of magnetic tape, not a hard drive. Cats love stringy things!

---

## 5. Using RAM for Storage (Solid State vs. Flash)

Given how slow mechanical hard drives are (milliseconds), why not just use RAM (microseconds) for storage?
1. **Cost**: RAM is roughly 100x more expensive per gigabyte than magnetic disks.
2. **Volatility**: Standard DRAM loses all its data when power is turned off.

Early attempts at "Solid State Drives" (SSDs) literally used DRAM hooked up to a battery. It was incredibly fast but extremely expensive and risky (if the battery died, data was lost).

**Enter Flash Memory:**
Flash memory is a type of solid-state storage fabricated using semiconductor technology (like processors and RAM). 
* **Non-volatile**: It retains data for years without power.
* **Fast & Efficient**: It has zero moving parts, consumes very little power, and offers incredibly fast access times compared to mechanical disks.

---

## 6. Hybrid Magnetic / Flash Drives

To get the best of both worlds, engineers created **Hybrid Drives** that combine a large, cheap magnetic disk with a smaller, ultra-fast Flash memory cache.

**How it works:**
* The vast majority of data lives on the cheap, high-capacity magnetic disk.
* Frequently accessed data is copied to the fast Flash memory cache.
* **Power Savings**: Because the flash cache handles most requests, the mechanical magnetic disk can actually spin down and turn off for minutes at a time, saving immense amounts of power. It only spins up when there is a "cache miss" (the data isn't in the flash).
* **Reliability**: Because both Flash and Magnetic disks are non-volatile, an unexpected power outage won't result in data loss (unlike a DRAM cache).

### 📝 Example: Disk vs. Flash vs. Hybrid
Imagine a user plays a game for 2 hours (requiring 2GB of random reads and 10MB of random writes), then watches a movie for 2 hours (1GB of sequential reads). They repeat this cycle 4 times.

* **Disk speeds**: 100 MB/s sequential, 1 MB/s random.
* **Flash speeds**: 1 GB/s (1000 MB/s) for both.

**Time taken for all 4 cycles:**
1. **Disk Only**: Random reads take forever (2GB at 1MB/s = 2000 seconds per cycle). Total time spent waiting on the disk across 4 cycles is over **8,000 seconds** (~2.2 hours of pure loading time).
2. **Flash Only**: Flash blazes through 2GB in 2 seconds. Total time across 4 cycles is a mere **~12 seconds**.
3. **Hybrid (Disk + 4GB Flash Cache)**: 
   * *Cycle 1*: The cache is empty. The system must read from the slow magnetic disk, taking ~2020 seconds. However, as it reads, it stores the game and movie data into the 4GB Flash cache.
   * *Cycles 2, 3, 4*: The data is now in the Flash cache! The mechanical disk stays asleep, and the system accesses the data at Flash speeds (~3 seconds per cycle). 
   * *Total Time*: ~2029 seconds. The hybrid drive pays a large penalty on the very first run, but provides near-instant Flash performance for all subsequent runs, all while offering the massive, cheap storage capacity of a traditional hard drive.

---

## 7. Connecting I/O Devices

To ensure you can plug any hard drive into any computer, the industry uses **Standardized I/O Buses**. However, we don't connect every device directly to the CPU using one universal bus. Instead, we use a **Hierarchy of Buses**.

**The Hierarchy:**
1. **Mezzanine Bus (e.g., PCI Express)**: Very fast, short-distance buses connected directly to the processor. Used for components that absolutely need massive bandwidth, like Graphics Cards.
2. **Storage Buses (e.g., SATA, SCSI)**: Slower buses specifically designed for storage. A SATA controller plugs into the PCIe bus, and hard drives plug into the SATA controller. 
3. **Peripheral Buses (e.g., USB)**: Even slower buses for keyboards, mice, and thumb drives. A USB Hub plugs into the PCIe bus, providing USB ports.

**Why use a hierarchy instead of connecting everything to PCIe?**
* **Pacing Standards**: A graphics card needs the cutting-edge speed of the newest PCIe standard. A hard drive is fundamentally slow; it doesn't need PCIe speeds. 
* By keeping storage on a separate, slower standard like SATA, consumers don't have to throw away their hard drives every time a new motherboard with a faster PCIe standard is released. The SATA standard can remain stable for a decade, providing excellent backwards compatibility, while the high-end PCIe bus evolves rapidly.

---

## 8. Looking Ahead
Now we understand how storage devices work and how they connect to the processor. But what happens when these mechanical or solid-state components physically fail? And how can we design systems to prevent data loss? That will be the topic of our next lesson!