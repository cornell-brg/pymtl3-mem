# Pipelined Blocking Cache 
1. Written in PyMTL3 and tested using new method based testing.
2. NOPE support (eventually?)
3. SRAM tag array and data array 

## Datapath
![Pipelined Blocking Cache Datapath](/figures/pipelined_blocking_cache.svg)
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
We have three possible cases each for read and write.

### Init 
| `M0`        | `M1`        | `M2`          |
| :---:        | :----:   |          :---: |
| Tag array write | Data array write| Data mux select 0   |
| Set valid bit   |         | Cache response valid    |

### Hit (read/write)
```
             1  2  3  4  5  6
Hit       : M0 M1 M2                              <- 2 Cycle Latency
Hit       :    M0 M1 M2                           
Hit       :       M0 M1 M2                         
Hit       :          M0 M1 M2                     <- 6 cycles for 4 transactions
```
#### Read Hit Stages
| `M0`           | `M1`           | `M2`          |
| :---:          | :----:         |          :---: |
| Cache request select | Data array read| Data mux select    |
| Tag array read | Tag match/Hit  | Cache response valid|
|                |                |                     |

#### Write Hit Stages
##### Write Hit Clean: 
TODO

| `M0`           | `M1`           | `M2`          |
| :---:          | :----:         |          :---: |
| Cache request select | Data array write| Data mux select 0|
| Tag array read | Tag match/Hit  | Cache response valid|
|                | Dirty bit = 0  |                     |
|                | Stall to write dirty bit     |                     |
|                | `M0`           |  `M1`           | `M2`          |
|                | :----:         |    :----:       |:----:|

##### `M1`: 
- Hit check; tag match and valid bit from tag array. Dirty bit from regfile(?). HIT 
- Write data to data array
- _Set the dirty bit at index_

TODO

##### Write Hit Dirty: 
| `M0`           | `M1`           | `M2`          |
| :---:          | :----:         |          :---: |
| Cache request select | Data array write| Data mux select 0|
| Tag array read | Tag match/Hit  | Cache response valid|

### Miss Clean (read/write)
```
Miss      : M0 M1 M2 .......... M0 M1 M2          <- Refill path
Trans     :    Y  Y  ...........Y  M0 M1 M2       <- Next Transaction Path 
```
#### Read Miss Clean Stages
| `M0`           | `M1`           | `M2`          |  `M0`: Refill Response|`M1`: Refill Response|`M2`: Refill Response
| :---:          | :----:         |          :---: |:---: |:---: |:---: |
| Cache request select | Data array read| Send memory request for refill|Mem Response select|New cacherequest can come in|Data mux select
| Tag array read | Tag match/Hit  | Cache response invalid|Deallocate from MSHR|Write refilled cacheline data to data array|cache response valid
|                |Allocate address and type in MSHR| Tag array write  |
|                |Ostall          |                |                  |

#### Write Miss Clean Stages
| `M0`           | `M1`           | `M2`          |  `M0`: Refill Response|`M1`: Refill Response|`M2`: Refill Response
| :---:          | :----:         |          :---: |:---: |:---: |:---: |
|Cache request select| Data array read|Send memory request for refill|Mem Response select|New cacherequest can come in|Data mux select 0
|Tag array read | Tag match/Hit  | Cache response invalid|Deallocate from MSHR|Write refilled cacheline data to data array|cache response valid
|                |Allocate address and type in MSHR| Tag array write  |
|                |Ostall          |                |                  |

TODO

##### `M0`: Refill Response/Write
- Deallocate from MSHR and select mux for type, opaque, address, and data
- Write new valid tag to tag array 
- _Insert write data into response cacheline before writing to data array_
##### `M1`: Refill Response
- New cacherequest can come in
- Write refilled cacheline data to data array 
- Set dirty bit

TODO

### Miss and dirty (read/write)
```
Miss Dirty: M0 M1 M2 .......... M0 M1 M2          <- Evict path
                  M1 M2 .......... M0 M1 M2       <- Refill path - New transaction spawns
Hit       : Y  Y  Y  Y  ...........Y  M0 M1 M2    <- Hit path
```
#### Read Miss Dirty Stages
| `M0`           | `M1`: Evict | `M2`: Evict Request|  `M0`: Refill Response|`M1`: Refill Response|`M2`: Refill Response
| :---:          | :----:         |          :---: |:---: |:---: |:---: |
|Cache request select|Tag match/Hit |Send memory write request|Mem Response select|New cacherequest can come in|Data mux select 0
|Tag array read | New write memory transaction| Cache response invalid|Deallocate from MSHR|Write refilled cacheline data to data array|cache response valid
|                |Allocate address and type in MSHR| Tag array write  |
|                |Ostall          |                |                  |
|                |                | `M1`: Refill Request |                  |
##### `M1`: Refill Request
- Allocate address and type in MSHR
##### `M2`: Refill Request
- Send memory refill request
##### `M0/M1/M2`: Evict Response
- Ignore? Don't really need to move through the pipeline since nothing changes
##### `M0`: Refill Response
- Deallocate from MSHR and select mux for type, opaque, address, and data
- Write new valid tag to tag array 
##### `M1`: Refill Response
- New cacherequest can come in
- Write refilled cacheline data to data array 
- Clear dirty bit
##### `M2`: Refill Response
- Data mux select correct word and cache response valid

#### Write Miss Dirty Stages
##### `M0`: 
- Tag array read using index
##### `M1`: Evict
- Hit check; tag match and valid bit from tag array. Dirty bit from regfile(?). MISS
- Send address and type to MSHR
- Stall signal to prevent new cache request from coming in
- Generate new write memory transaction
##### `M2`: Evict
- Send memory write request
##### `M1`: Refill Request
- Allocate address and type in MSHR
##### `M2`: Refill Request
- Send memory write request
##### `M0`: Refill Response/Write
- Deallocate from MSHR and select mux for type, opaque, address, and data
- Write new valid tag to tag array 
- _Insert write data into response cacheline before writing to data array_
##### `M1`: Refill Response
- New cacherequest can come in
- Write refilled cacheline data to data array 
- Set dirty bit
##### `M2`: Refill Response
- Data mux select 0 and cache response valid
