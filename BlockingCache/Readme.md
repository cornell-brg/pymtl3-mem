
# Pipelined Block Cache 
1. Written in PyMTL3 and tested using new method based testing.
2. Supports init, read, and write transactions
3. NOPE support (eventually?)
4. SRAM tag array and data array
5. Valid and dirty bits stored in SRAM
6. Parametrizable by cache size, cache line size, associativity, and replacement policy 

## Pipeline Stages
`Y `: Prior to receiving transaction. Pretransaction stage.

`M0`: Refill stage used to process the memory response from a refill or a writeback request.

`M1`: Data returns from tag array SRAM. Cache performs tag check and set signals for the data array.

`M2`: Cache response and memory request stage.   

## Tag Array
- `tag_width = addr_width - offset_width - idx_width; tgw = abw - ofw - idw `
- 32-bit width SRAM with blocks equal to number of cachelines
- We store valid at highest bit

Example Cacheline
```
|v | ... |  tag   |
 31   tgw        0
```

## Possible Transaction Cases
We have three possible cases each for read and write.

### Hit (read/write)
```
Hit       : Y  M1 M2                           <- 2 Cycle Latency
```

### Miss Clean (read/write)
```
Miss      : Y  M1 M2 .......... Y  M0 M1 M2       <- Refill path
Trans     :    Y  Y  ............. Y  M1 M2    <- Next Transaction Path 
```

### Miss and dirty (read/write)
```
Miss Dirty: Y  M1 M2 .......... Y  M0 M1 M2       <- Evict path
                  M1 M2 .......... Y  M0 M1 M2    <- Refill path - New transaction spawns
Hit       : Y  Y  Y  Y  ............. Y  M1 M2 <- Hit path
```


