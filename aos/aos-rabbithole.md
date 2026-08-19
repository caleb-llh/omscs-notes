### L1 - intro to aos
- data path vs control logic? why is control logic regarded as a finite state machine what are the fixed state set of states, inputs and transitions?
- how does system bus communication happen synchronously? how about with the bridge and IO bus? how do the data lines, address lines and interrupt lines work together? are these lines connected from the memory both to the CPU as well as the host bridge (for DMA)? what exactly is a "packet" on a bridge and is it transferred in one cycle? what is the setup overhead of DMA exactly and how does PIO circumvent it?
- are interrupt vector tables stored in registers or in the memory (kernel space)? are there instances where the CPU is interrupted but does not handle the interrupt immediately? how does interrupt masking work in hardware?
- is the privilege bit software (part of instruction) or hardware (a register)? is it the hardware or kernel code that sets the privilege bit? how and when? what happens during bootup, how does the kernel code configure the hardware?
- what is the anatomy of a program binary? what exactly is loaded during the startup of a program, is it the same as what happens during a context switch? what are ELF binary headers and relocation tables? what is BSS? what is dynamic linking? program image vs VM image?

### L2 - os structures
- What value did DOS bring if it did not arbitrate between multiple applications? examples of microkernel in modern day? 
- are SPIN and exokernel still used today? what are the modern-day equivalents?
- what in microkernel MUST belong to the core and what can be delegated? does every application/service to service call involve a context switch and all the overhead associated with it?
- LRU for caches vs LRU for page replacement - which is handled by the hardware vs by the OS? why would database management system (DBMS) often prefers to manage its own caching and memory replacement rather than relying on the OS's generic LRU page replacement algorithm?
