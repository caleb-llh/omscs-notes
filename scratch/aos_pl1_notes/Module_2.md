# Playlist 1, Module 2: Synchronization Algorithms

This module covers advanced locking mechanisms designed to improve fairness and reduce network contention, as well as barrier synchronization techniques for coordinating multiple threads.

## 1. Ticket Lock
The ticket lock is designed to ensure **fairness** in lock acquisition, similar to a ticketing system in a deli shop.

* **Goal:** Ensure the lock is acquired in the order requested (FIFO), preventing starvation.
* **Data Structure Fields:**
  * `next ticket`: The ticket number to be given to the next requester.
  * `now serving`: The ticket number currently holding the lock.
* **Acquire Algorithm:**
  1. Perform an atomic `fetch-and-increment` on `next ticket` to get a unique ticket number.
  2. Spin (wait) until `now serving == my ticket`.
* **Release Algorithm:**
  * Increment `now serving` by 1.
* **Pros:**
  * Preserves strict fairness (FIFO).
* **Cons:**
  * **Noisy Release (Network Contention):** Every time the lock is released, the `now serving` variable is updated via cache coherence across all waiting processors' local caches, causing a burst of network contention.

## 2. Array-Based Queueing Lock (Anderson's Lock)
Designed by Anderson, this lock achieves fairness while eliminating the network contention caused by noisy releases.

* **Data Structure:**
  * A circular array of `flags` with a size $N$ equal to the total number of processors.
  * `Q last`: A variable tracking the next available slot in the queue (initialized to 0).
* **States:** Each array element is either `has lock` (HL) or `must wait` (MW).
  * **Initialization:** The first slot is HL, and all others are MW.
* **Acquire Algorithm:**
  1. Perform an atomic `fetch-and-increment` on `Q last` to reserve a unique, distinct slot in the array.
  2. Spin on the reserved slot until its state changes from MW to HL.
* **Release Algorithm:**
  1. Mark the current slot as MW (for future requesters).
  2. Signal the next slot in the circular queue `(current + 1) mod N` by changing it to HL.
* **Pros:**
  * **Fairness:** Strictly FIFO.
  * **Low Network Contention:** Each processor spins on a *private, distinct variable* (its designated array slot). Releasing the lock only signals exactly one waiting processor.
  * **Efficiency:** Requires exactly one atomic operation per critical section.
* **Cons:**
  * **Space Complexity:** $O(N)$ space per lock, where $N$ is the total number of processors, regardless of the actual dynamic contention. This static size can consume significant memory in large-scale multiprocessors.
  * Requires advanced hardware instructions (e.g., `fetch-and-increment`).

## 3. Link-Based Queueing Lock (MCS Lock)
Designed by Mellor-Crummey and Scott, this lock uses a dynamic linked list to solve the space complexity issue of Anderson's lock.

* **Data Structure:**
  * **Lock Head (Dummy Node):** A pointer representing the tail of the queue (initialized to `nil`).
  * **Q Node:** Allocated dynamically per requester. Contains:
    * `guarded`: A Boolean flag (true = have lock, false = must wait).
    * `next`: A pointer to the successor node.
* **Acquire Algorithm:**
  1. Perform an atomic `fetch-and-store` on the Lock Head to swap my `Q Node` into the tail of the queue and retrieve the predecessor node.
  2. If the predecessor is not `nil`, set the predecessor's `next` pointer to point to me, and spin on my own `guarded` variable.
* **Release Algorithm & The Corner Case:**
  * **Normal Release:** Remove myself and signal the successor by setting their `guarded` variable to true.
  * **Corner Case:** If there is no successor (`next == nil`), I must set the Lock Head back to `nil`. However, a new requester might be joining concurrently.
  * **Solution:** Use an atomic `compare-and-swap` (CAS) operation.
    * Compare Lock Head with my node. If they match, set Lock Head to `nil`.
    * If CAS fails (a new requester is forming), spin until my `next` pointer is no longer `nil`, then signal the new successor.
* **Pros:**
  * **Fairness:** Strictly FIFO.
  * **Low Contention:** Spins on a private variable; signals exactly one processor.
  * **Space Complexity:** $O(K)$, where $K$ is the dynamic number of actual requesters. Memory overhead scales with contention, not system size.
* **Cons:**
  * Linked list maintenance adds overhead.
  * Requires advanced atomic instructions (`fetch-and-store`, `compare-and-swap`).

## 4. Spinlock Algorithm Summary & Grading
Choosing the right synchronization algorithm depends on the hardware and the level of contention.

* **Low Contention:** A simple spinlock with exponential backoff delay is often the best performer.
* **High Contention:** Spinlocks with static delay slots or Queueing locks (Anderson's or MCS) perform best.
* **Hardware Constraints:** If the architecture only supports basic `test-and-set` (and lacks `fetch-and-increment`, `fetch-and-store`, or `compare-and-swap`), queueing locks must simulate these using `test-and-set`, which can degrade their performance.

## 5. Barrier Synchronization
A barrier ensures that a group of threads all reach a specific point in execution before any are allowed to proceed. Common in scientific applications with distinct computation phases.

### Centralized Counting Barrier
* **Concept:** Uses a shared `count` variable initialized to the number of threads ($N$).
* **Algorithm:**
  * Arriving threads atomically decrement `count` and spin until `count == 0`.
  * The last thread to arrive (decrementing `count` to 0) resets `count` back to $N$.
* **The Flaw:** A race condition exists. If threads leave the barrier as soon as `count == 0` but *before* the last thread resets it to $N$, fast threads could race to the *next* barrier and incorrectly fall through.
* **The Fix:** Requires **two spinning episodes**. Threads must first wait for `count == 0`, and then wait again for `count == N` before proceeding.

### Sense Reversing Barrier
* **Concept:** Optimizes the counting barrier by reducing it to a single spinning episode per barrier phase.
* **Data Structure:** Introduces a shared `sense` variable (e.g., boolean). It alternates (true for one barrier, false for the next).
* **Algorithm:**
  * Threads decrement the `count` and spin on the `sense` variable reversing its state.
  * The last thread resets the `count` to $N$ and then **reverses the `sense` flag**.
  * The reversal of the `sense` flag acts as a broadcast signal, releasing all waiting threads simultaneously.
* **Pros:** Only one spinning episode per barrier.
* **Cons:** Both the `count` and `sense` variables are centralized shared variables. In a large-scale multiprocessor, many threads spinning on and modifying these single locations causes significant network contention (a "hot spot"), limiting scalability.
