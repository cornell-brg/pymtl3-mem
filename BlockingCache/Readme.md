
# Pipelined Blocking Cache 
1. Written in PyMTL3 and tested using new method based testing.
2. Supports init, read, and write transactions
3. NOPE support (eventually?)
4. SRAM tag array and data array
5. Valid and dirty bits stored in SRAM
6. Parametrizable by cache size, cache line size, associativity, and replacement policy 

## Datapath
![Pipelined Blocking Cache Datapath](/figures/pipelined_blocking_cache.svg)
## Pipeline Stages

`Y `: Prior to receiving transaction. Pretransaction stage. NOT USING ANYMORE

`M0`: Refill stage used to process the memory response from a refill or a writeback request.

`M1`: Data returns from tag array SRAM. Cache performs tag check and set signals for the data array.

`M2`: Cache response and memory request stage.   

## Tag Array
- `tag_width = addr_width - offset_width - idx_width; tgw = abw - ofw - idw `
- 32-bit width SRAM with blocks equal to number of cachelines
- We store valid at highest bit

Example Cacheline
```
|v | ...free bits... | tag |
 31               tgw     0
```

## Possible Transaction Cases
We have three possible cases each for read and write.

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
#### Read
`Y `: Tag array access by setting index, valid, and read req.

`M1`: Hit check; tag match and valid bit from tag array. Results in a miss and not dirty

`M2`: Build and send memory request for refill request. Save opaque, address, and type in 1 entry MSHR or registers?

.

`M0`: Memory response   
 

### Miss and dirty (read/write)
```
Miss Dirty: M0 M1 M2 .......... M0 M1 M2          <- Evict path
                  M1 M2 .......... M0 M1 M2       <- Refill path - New transaction spawns
Hit       : Y  Y  Y  Y  ...........Y  M0 M1 M2    <- Hit path
```


