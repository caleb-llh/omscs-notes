# High Performance Computer Architecture (HPCA) Notes
## Module 2: Power, Cost, and Performance Metrics

---

### 1. The Power Trade-off: Static vs. Dynamic Power

#### Background & Intuition
In the previous module, we learned that **Dynamic (Active) Power** is proportional to $Voltage^2 \times Frequency$. To save power, a natural strategy is to lower the voltage. However, there's a limit to how low we can go. This constraint is dictated by **Static Power** (also known as leakage power).

**Mental Model: Transistors as Electronic Faucets**
Think of a transistor as a water faucet.
- **Water Pressure** = Voltage
- **Valve Control** = Controlled by water pressure from another faucet.
When the valve is open, water flows (transistor is ON). When closed, water shouldn't flow (transistor is OFF).

If we lower the power supply voltage (reduce the water pressure), the pressure used to keep the faucet tightly closed is also reduced. Because the pressure is "wimpy," the valve doesn't close perfectly, and water (current) begins to leak. This leakage is the source of **Static Power**.

#### The Voltage Sweet Spot
- **Dynamic Power:** Decreases rapidly as voltage drops.
- **Static Power (Leakage):** Very low at high voltages but increases exponentially as voltage drops too low (because the "valve" can't close properly).
- **Total Power:** The sum of dynamic and static power creates a U-shaped curve.
  - If voltage is too high: Dynamic power is overwhelming.
  - If voltage is too low: Static power dominates.
  - **Optimal Voltage:** There is a sweet spot where total power is minimized.

**Other Leakage Sources:** As transistors become physically smaller (due to Moore's Law), the "valves" inherently become leakier, adding to static power even if voltage isn't dropped.

---

### 2. Active Power Calculations

Let's explore the mathematical relationship between power, voltage, and frequency.

**Formula Recap:**
$Power \propto Voltage^2 \times Frequency$

**Scenario:**
- **Voltage Options:** 0.9V to 1.5V (in 0.1V steps)
- **Frequency Options:** 1.8 GHz to 3.0 GHz (in 0.2 GHz steps)
- **Constraint:** Higher frequencies require higher minimum voltages (e.g., 1.8 GHz needs 0.9V; 2.0 GHz needs 1.0V; 3.0 GHz needs 1.5V).
- **Baseline Measurement:** At 2.0 GHz and 1.0V, the processor consumes **30W**.

#### Most Power-Efficient Setting
To minimize power, we must minimize both voltage and frequency.
- **Setting:** 1.8 GHz at 0.9V
- **Calculation:**
  $Power_{efficient} = 30\text{W} \times \left(\frac{0.9}{1.0}\right)^2 \times \left(\frac{1.8}{2.0}\right) = 30 \times 0.81 \times 0.9 = 21.87\text{W} \approx 21.9\text{W}$

#### Highest Performance Setting
To maximize performance, we maximize frequency (which forces us to use maximum voltage).
- **Setting:** 3.0 GHz at 1.5V
- **Calculation:**
  $Power_{performance} = 30\text{W} \times \left(\frac{1.5}{1.0}\right)^2 \times \left(\frac{3.0}{2.0}\right) = 30 \times 2.25 \times 1.5 = 101.25\text{W} \approx 101.3\text{W}$

**Key Insight:** Increasing performance by a factor of 1.5x (from 2.0 to 3.0 GHz) increases power consumption by nearly **3.4x** (from 30W to 101.3W). This disproportionate growth occurs because power scales with the *square* of the voltage.

---

### 3. Fabrication Cost and Chip Area

#### The Manufacturing Process
Chips are manufactured on circular silicon disks called **wafers** (typically 12 inches in diameter). The wafer undergoes numerous complex processing steps to print circuitry. Finally, the wafer is cut into individual square chips, packaged (with pins), and tested.

- **Fixed Cost:** Processing a wafer costs a fixed, large amount (e.g., thousands of dollars) regardless of how many chips are on it.
- **Base Cost per Chip:** Roughly equals `Wafer Cost / Number of Working Chips`.

#### Fabrication Yield
Not all manufactured chips work. **Yield** is the percentage of working chips relative to the total number of chips cut from the wafer.

**Why do chips fail? (Defects)**
Wafers naturally have defects (due to silicon impurities or manufacturing dust). If a defect lands on a chip, that entire chip is ruined and must be thrown away.

**Why Cost Scales Non-Linearly with Size:**
1. **Edge Wasted Space:** Trying to fit square chips onto a round wafer wastes edge space. Larger squares result in more wasted area at the edges.
2. **Defect Impact:** A defect ruins whatever chip it touches.
   - If chips are small, a single defect destroys a very tiny portion of the wafer.
   - If chips are large, a single defect destroys a massive portion of the wafer.
   - Therefore, larger chips inherently have a much lower yield.

**Conclusion:** The cost of a processor is **more than linearly proportional** to its area. A chip that is 100x larger than another will cost significantly *more* than 100x the price.

---

### 4. Fabrication Cost Example

Let's model cost using a hypothetical **$5,000 wafer** with exactly **10 defects**.

| Chip Size | Max Chips per Wafer | Chips Lost to Defects | Good Chips | Cost per Chip | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Small** | 400 | 10 | 390 | **$12.82** | |
| **Large** (4x area) | 96 *(edge loss)* | 10 | 86 | **$58.14** | Cost is ~4.5x the small chip. |
| **Huge** (16x area) | 20 *(edge loss)* | 9 *(defects overlap)* | 11 | **$454.54** | Cost is ~35x the small chip! |

**Takeaway:** For large chips, even a slight increase in area drastically drops yield and exponentially increases cost.

#### Moore's Law & Design Choices
As Moore's Law allows us to fit more transistors in the same space, architects have two main choices:
1. **Shrink the Chip (Same Functionality):** Move an existing design to a newer, smaller process. It becomes drastically cheaper (e.g., this is how smartphones and digital watches eventually became affordable).
2. **Keep Area Constant (More Capability):** Use the newly available transistors to add performance and features while keeping the chip size (and cost) the same. (Typical for high-end desktop processors).

---

### 5. Performance Measurement: Latency vs. Throughput

To improve a computer, we must first be able to measure it. The two primary metrics of performance are Latency and Throughput.

- **Latency (Response/Execution Time):** How long does it take from the moment a task starts until it is fully completed? (e.g., 4 hours to build a car).
- **Throughput (Bandwidth):** How many tasks can be completed per unit of time? (e.g., 5 cars produced per hour).

**Crucial Distinction:** Throughput is **not** simply `1 / Latency`.

**Mental Model: The Assembly Line (Pipelining)**
Imagine a car factory. It takes 4 hours (latency) for a single chassis to go through 20 distinct steps to become a finished car. If we waited for one car to finish before starting the next, throughput would be `1 car / 4 hours = 0.25 cars/hour`.
However, using an assembly line, once a car moves from Step 1 to Step 2, a new car enters Step 1. Because cars are processed in parallel stages, a finished car rolls off the line every 12 minutes.
- **Latency:** 4 hours
- **Throughput:** 5 cars per hour

#### Parallelism Example (Web Servers)
Imagine a website with 2 servers. Processing one order takes exactly 1 millisecond.
- **Latency:** 1 ms (Time to serve a specific user).
- **Throughput:** 2,000 orders per second. (Each server handles 1,000 orders/sec. By replicating hardware, we doubled throughput without changing latency).

---

### 6. Comparing Performance (Speedup)

When evaluating two systems (System X and System Y), we quantify the improvement using **Speedup**.

$\text{Speedup of X over Y} = \frac{\text{Speed of X}}{\text{Speed of Y}}$

How you calculate "Speed" depends on your metric:
- **For Throughput:** Speed is directly proportional to throughput.
  $\text{Speedup} = \frac{\text{Throughput}_X}{\text{Throughput}_Y}$
- **For Latency:** Speed is inversely proportional to latency (longer latency = lower speed).
  $\text{Speedup} = \frac{\text{Latency}_Y}{\text{Latency}_X}$

**Example:**
- Old Laptop (Y) compresses a video in 4 hours (240 minutes).
- New Laptop (X) compresses the same video in 10 minutes.
- $\text{Speedup} = \frac{240}{10} = \mathbf{24x}$
- We can confidently say "The new laptop is 24 times faster."