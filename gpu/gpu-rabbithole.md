### m1
- nuances between SIMD vs SPMD? Is SPMD compiled down into SIMD? What are CPU vector extensions and how does the OS and applications integrate with it?
- relate these concepts - core, SM, lanes, grid, threads, warps, warp scheduler, SP. what's the purpose of each abstraction?
- how is matrix multiply-accumulate done in a single instruction? how does reducing floating point precision lead to twice as many mathematical operations - what was the bottleneck?
- Is the transformer engine of the hopper architecture a compiler or something run during runtime? What exactly is CUDA?

> the deeper a pipeline, the more it behaves like streaming instead of batch, thus maximising throughput.

### m2