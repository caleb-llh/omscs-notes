# 12_Storage_Technologies (Synthesized Notes)

# Module 7: DRAM Technology, Memory Organization, and Storage

This module explores the physical construction of DRAM, how memory chips are organized internally, techniques for speeding up memory accesses, and introduces persistent storage mechanisms, specifically magnetic disks.

---

## 1. DRAM Technology and Organization

### 1.1 Why Trench Cells?
DRAM (Dynamic Random Access Memory) uses a single transistor and a capacitor to store a bit of data. Modern DRAM relies on **trench cells**, where the capacitor is physically buried deep into the silicon rather than sitting on top of it.
- **Intuition**: Counter-intuitively, trench cells are actually *harder* to manufacture than normal planar capacitors.
- **Why use them?**: The cost of a microchip is heavily dependent on its surface area. A trench cell occupies significantly less horizontal space on the silicon die. A smaller cell area means more bits per chip and more chips per wafer, drastically reducing the overall cost per bit. The cost savings from reduced area far outweigh the increased manufacturing complexity.

### 1.2 Memory Chip Architecture
A single memory chip is internally organized as a grid (array) of memory cells:
- **Word Lines & Row Decoder**: A memory address is split into a row address and a column address. The **row decoder** uses the row address to activate a single **word line**.
- **Bit Lines**: Activating a word line connects all the memory cells in that entire row to their respective **bit lines**.
- **Sense Amplifiers**: DRAM cells are weak because they rely on microscopic capacitors. When a cell discharges its tiny amount of stored charge into a long bit line, it only changes the bit line's voltage slightly. **Sense amplifiers** detect this minute voltage shift and strongly amplify it to a full logical 0 or 1. Because sense amplifiers require beefy circuitry, there is only one per bit line (not one per cell).
- **Row Buffer**: Once the sense amplifiers resolve the data, the entire row's bits are latched into a storage element called the **row buffer**.
- **Column Decoder**: Finally, the **column decoder** uses the column address to select the specific bit(s) from the row buffer to output to the processor.

### 1.3 Destructive Reads and Writes
- **Destructive Read**: Reading a DRAM cell physically discharges its capacitor. The data is lost from the cell the moment it is read onto the bit line.
- **Read-then-Write**: Because the read is destructive, the sense amplifier must drive the amplified value *back* into the cell to restore it. Thus, every single DRAM read is actually a "read and restore (write)" operation under the hood.
- **Why DRAM is slower than SRAM**:
  1. Sense amplifiers need time to detect small voltage changes (SRAM cells actively drive the lines).
  2. The mandatory write-back (restoration) takes additional time before the memory is ready for the next operation.
- **Writing Data**: To write a new value to a specific column, the memory must:
  1. Read the entire row into the row buffer.
  2. Overwrite the target bit(s) in the row buffer.
  3. Write the entire modified row buffer back into the physical memory cells.

### 1.4 Memory Refresh
- **Leakage**: DRAM capacitors constantly leak charge. If left alone, they will lose their data (typically within tens of milliseconds).
- **Refresh Mechanism**: A read-then-write cycle naturally restores a cell's charge. To prevent data loss, a hardware refresh counter sequentially goes through all rows, ensuring every row is "refreshed" (read and written back) within the maximum refresh period ($T$).
- **Impact on Performance**: Refreshes consume valuable memory bandwidth. While a refresh is occurring, the row decoder, sense amplifiers, and row buffer are fully occupied. Any useful read/write request from the CPU must wait.
  - *Example*: A memory array with 4,096 rows and a 500µs refresh period must perform ~8.2 million refreshes per second. If a read takes 25ns, the memory spends about 20% of its total time just refreshing itself, directly eating into the maximum possible read/write throughput.

---

## 2. Fast Page Mode and Access Scheduling

### 2.1 Fast Page Mode (FPM)
- **Mental Model**: Think of the row buffer as a tiny, ultra-fast cache that holds exactly one DRAM row (often called a "page", typically thousands of bits). Note: This "page" has nothing to do with OS virtual memory pages.
- **Opening a Page**: Supplying the row address, sensing the data, and latching it into the row buffer. This is slow.
- **Page Hits (Fast Page Mode)**: If subsequent memory accesses target the *same* row, we only need to change the column address and read directly from the already-populated row buffer. This skips the slow row activation and sense amplification steps, making the access significantly faster.
- **Closing a Page**: Writing the row buffer contents back to the physical memory cells, freeing up the sense amplifiers to open a different row.

### 2.2 DRAM Access Scheduling
- **Motivation**: Cache misses from the CPU don't always arrive in a perfectly sequential order. If the memory controller naively accesses memory in the exact order requests arrive, it might constantly open and close different pages (thrashing).
- **Reordering**: The memory controller is smart. It can reorder pending memory requests to group accesses that target the same row. By doing this, it maximizes Fast Page Mode (page hits).
- *Example Impact*: Instead of taking 17ns per access (open, read, close) for three interleaved accesses to different rows (51ns total), grouped accesses might take 10ns to open, 2ns per read (x3), and 5ns to close. Three accesses to the same row drop from 51ns to just 21ns.

---

## 3. Connecting DRAM to the Processor

### 3.1 Traditional Architecture (Front Side Bus)
- **Flow**: CPU $\rightarrow$ Front Side Bus (FSB) $\rightarrow$ Memory Controller (Northbridge chip on the motherboard) $\rightarrow$ Memory Channel $\rightarrow$ DRAM.
- The memory controller translates generic CPU read/write requests into the low-level DRAM commands (open row, read column, close row).
- **Bottleneck**: The FSB adds significant latency and acts as a bandwidth bottleneck, slowing down memory accesses.

### 3.2 Modern Architecture (Integrated Memory Controller)
- **Flow**: The memory controller is integrated directly onto the processor die itself.
- **Advantages**: Eliminates the FSB bottleneck. The CPU communicates directly with its internal memory controller via fast on-chip wiring, reducing overall memory latency by 10-30%.
- **Trade-offs**: The CPU is now physically tied to a specific memory standard (e.g., DDR4 or DDR5). The memory modules must be highly standardized (like DIMMs) so that upgrading RAM capacity doesn't require redesigning the CPU.

---

## 4. Storage Systems

### 4.1 Role of Storage
- **Persistence**: Retains programs, data, OS, and user settings when power is off.
- **Virtual Memory**: Extends memory by swapping inactive physical RAM pages to the disk.
- **Metrics**: Evaluated by **Throughput** (bytes/sec) and **Latency** (time to first byte). Storage latency is improving much slower than CPU or DRAM speeds, widening the performance gap.
- **Reliability**: Crucial. A CPU crash causes a temporary reboot; a storage crash causes permanent data loss.

### 4.2 Magnetic Disks (Hard Disk Drives - HDDs)
Despite the rise of SSDs, magnetic disks remain foundational for high-capacity storage.
- **Anatomy**:
  - **Spindle**: The central motor that rotates all platters simultaneously.
  - **Platters**: Rigid disks coated with magnetic material on both surfaces (top and bottom).
  - **Head Assembly**: An actuator arm holding read/write heads for all surfaces. All heads move in and out together in unison.
- **Data Organization**:
  - **Track**: A single concentric circle of data on one platter surface.
  - **Cylinder**: The set of all tracks across *all* surfaces that are at the same distance from the spindle. The heads can access an entire cylinder without moving the actuator arm.
  - **Sector**: The smallest readable/writable unit on a track (typically 512 bytes or 4KB). Each sector includes a preamble (sync pattern), the actual data, and error-correcting codes (ECC/checksum).
- **Capacity Calculation**:
  `Capacity = (Platters × 2 surfaces/platter) × (Tracks / surface) × (Sectors / track) × (Bytes / sector)`
- **Physical Constraints**: With thousands of tracks packed onto a small surface, the read/write heads must be positioned with extreme mechanical precision.


---

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

---

