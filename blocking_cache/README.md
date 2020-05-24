# Pipelined Blocking Cache 

## Datapath
![Pipelined Blocking Cache Datapath](/figures/pipelined_blocking_cache_cifer.svg)
## Pipeline Stages

`M0`: Tag array SRAM access. Refill response comes to M0 as well.

`M1`: Data returns from tag array SRAM. Cache performs tag check and sets signals for the data array.

`M2`: Cache response and memory request stage.   

### Tag Array
- `tag_width = addr_width - offset_width - idx_width`
- `tgw = abw - ofw - idw`
- 32-bit width SRAM with blocks equal to number of cachelines
- We store valid and dirty at the highest bits

#### Tag Array Bits Distribution
```
   |v | ...free bits... | tag |
abw|                 tgw|    0|
```

### Data Array
- Bit width is cacheline size (`clw`)

#### Data Array Bits Distribution
```
   | ..data.. | ... | ..data.. |
clw|             dbw|         0|
```

## Possible Transaction Cases

### Hit (read/write)
```
             1  2  3  4  5  6
Hit       : M0 M1 M2                              <- 2 Cycle Latency
Hit       :    M0 M1 M2                           
Hit       :       M0 M1 M2                         
Hit       :          M0 M1 M2                     <- 6 cycles for 4 transactions
```

### Miss Clean (read/write)
```
Miss      : M0 M1 M2 .......... M0 M1 M2          <- Refill path
Trans     :    Y  Y  ...........Y  M0 M1 M2       <- Next Transaction Path 
```
### Miss and dirty (read/write)
```
Miss Dirty: M0 M1 M2 .......... M0 M1 M2          <- Evict path
                  M1 M2 .......... M0 M1 M2       <- Refill path - New transaction spawns
Hit       : Y  Y  Y  Y  ...........Y  M0 M1 M2    <- Hit path
```

## Running The Code

### Testing

To run all tests including RTL and FL tests:

```
% git clone git@github.com:cornell-brg/pymtl3-mem.git
% cd pymtl3-mem
% mkdir build && cd build
% pytest ../blocking_cache/test/ 
```
All commands will be run from the `build` directory.

To run RTL tests:

```
% pytest ../blocking_cache/test/BlockingCacheRTL_test.py 
```

Flags:
```
--test-verilog: translate the cache to verilog and run all test cases
--dump-vcd    : dumps vcd waveforms after translation and running the tests
--trace       : controls verbosity of the line trace [0 - no trace, 2 - all the trace]
```

### Translation
The cache is translatable to Verilog using
```
% python ../blocking_cache/translate.py
```
This command will translate the cache to a Verilog (.v) file and not run the tests.

To change the cache paramemters, use the optional flags
```
--size: cache size in bytes (default 4096)
--clw : cache line bitwidth (default 128)
--dbw : data bitwidth (default 32)
--abw : address bitwidth (default 32)
--obw : opaque bitwidth (default 8)
--asso: associativity (default 1)
```
