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
