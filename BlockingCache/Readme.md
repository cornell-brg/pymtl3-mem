
# Pipelined Block Cache 
1. Written in PyMTL3 and tested using new method based testing.
2. Supports init, read, and write transactions
3. NOPE support (eventually?)
4. SRAM tag array and data array
5. Valid and dirty bits stored in SRAM
6. Parametrizable by cache size, cache line size, associativity, and replacement policy 

## Possible Transaction Cases
### Hit (read/write)
```
Hit       : Y  M1 M2
```

### Miss (read/write)

### Miss and dirty (read/write)
```
Miss Dirty: Y  M1 M2 .......... M0 M1 M2       <- Evict path
                  M1 M2 .......... M0 M1 M2    <- Refill path
Hit       : Y  Y  Y  Y  ...........Y  Y  M1 M2 <- Hit path
```


