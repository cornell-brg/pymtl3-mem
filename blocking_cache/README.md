# Pipelined Blocking Cache Generator 

## Table of Contents
1. [Introduction](#introduction)
2. [Datapath](#datapath)
   1. [Interface](#interface-ifc)
   2. [Interface Messages](#ifc-messages)
3. [Transactions](#transactions)
4. [Testing](#testing)
   1. [Single Cache Testbench](#single-cache-testbench)
   2. [Multi-Cache Testbench](#multi-cache-testbench)
5. [Running the Code](#running-the-code) 

## Introduction
We developed
PyMTL3-mem, a 3-stage pipelined write-back, write-allocate blocking cache generator parameterizable
by size, cache line size, data width, and associativity. The cache is mainly used as an L1 cache for processors and
will have great modularity to fit into any future projects and tape-outs within BRG. It is one of the
many IPs available in PyMTL3, a Python-based hardware description language.

### Future Goals
- More Testing
  - Hypothesis testing for individual modules in dpath and ctrl to reduce state space and get more coverage
  - Parallell testing to reduce test times
- Move CIFER branch to Master
  - Will be main IP for the cache and deprecate CIFER (don't create new cache)
  - Different settings: cifer, read_only, read/write cache
- Additional Features
  - Associativity greater than 2 using pseudo LRU (able to choose policy)
  - Nonblocking cache

## Datapath
![Pipelined Blocking Cache Datapath](/doc/figures/pipelined_blocking_cache_cifer.svg)

### Interface (IFC)

The cache has two interfaces: `MemMinion` and `MemMaster`. `MemMinion` allows for the cache to
behave as a minion handling requests from a master, usually a processor or an upper-level cache.
The cache is a master in `MemMaster` where it sends requests to a minion module, which is usually
a lower level cache or main memory.

<!-- <span style="color:blue"></span> -->

|IFC| Dpath | Ctrl | Y | M0| M2 |
|:-:|:---:|:---:|:---:|:---:|:---:|
|`MemMinion.req.msg`  | x |   |   | x ||
|`MemMinion.req.en`   |   | x |   | x | |
|`MemMinion.req.rdy`  |   | x |   | x | |
|`MemMinion.resp.msg` | x |   |   |   | x |
|`MemMinion.resp.en`  |   | x |   |   | x |
|`MemMinion.resp.rdy` |   | x |   |   | x |
|`MemMaster.req.msg`  | x |   |   |   | x |
|`MemMaster.req.en`   |   | x |   |   | x |
|`MemMaster.req.rdy`  |   | x |   |   | x |
|`MemMaster.resp.msg` | x |   | x |   |
|`MemMaster.resp.en`  |   | x | x |   |
|`MemMaster.resp.rdy` |   | x | x |   |

#### IFC Messages
|`Req`| Bit Width | Description |
|:-------------:|:---------:|:-----------:|
|`type`         |   4       | Transaction type 
|`opaque`       |   8       |Transaction identification number. Not very important for blocking cache|
|`addr`         |   32      | Address to fetch the data. 0 on a FLUSH and INV transaction
|`len`          | clog2(data_bit_wdith/8) |Read/write access width (1-byte, 2-byte, 4-byte, 8-byte, 16-byte)|
|`data`         | varies (base 2)  | Some data if WRITE otherwise 0
|`wr_mask`      | data_bit_wdith/32 | Stores the per-word dirty bits. Only required for CIFER

|`Resp`| Bit Width | Description |
|:-------------:|:---------:|:-----------:|
|`type`         |   4       | Transaction type 
|`opaque`       |   8       | Transaction identification number |
|`test`         |   2       | If the cache hit or not. Useful for debugging |
|`len`          | clog2(data_bit_wdith/8) |Read/write access width (1-byte, 2-byte, 4-byte, 8-byte, 16-byte)|
|`data`         | varies (base 2) | Data read from the cache. Is 0 for WRITE, WRITE_INIT, INV, and FLUSH transactions
|`wr_mask`      | data_bit_wdith/32 | Stores the per-word dirty bits. Only required for CIFER

For `MemMinion`, we do not use `wr_mask` at all since the processor does not need it. For `MemMaster`, the cache only uses the `opaque` and `data` on the response and ignores all other fields.  

### Y Stage
The `Y` stage handles incoming messages from the `MemMaster.resp` interface. We used registered inputs to keep the timing within the cache without incurring a large penalty.

### M0 Stage

#### FSM
The cache has an FSM in the M0 stage. The states are INIT, READY, REPLAY, INV, FLUSH, and
FLUSH_WAIT. The INIT state is for SRAM initialization during power on. We use an FSM and a counter
to write zeros to all entries in the tag array and data array. We load the counter with the total number
of cache lines and it will count down each cycle. There’s a modulo operator for different higher
associative cache so that we can reset the index back for the next set. The READY state handles normal
cache transactions that are not replays. The REPLAY stage handles replays from when the memMaster
response returns with the refill or AMO. INV, FLUSH and FLUSH_WAIT states are for CIFER specific
transactions involving iterating through every single cache line.

#### Tag Array
- `tag_width = addr_width - offset_width - idx_width`
- 32-bit width SRAM with blocks equal to number of cachelines
- We store valid and dirty at the highest bits

##### Tag Array Bits Distribution Example
For a 4KB 2-way associative cache with 32-bit address and 32-bit data, the tag width is 24 bits and the valid is 1 bit. If the cache is a CIFER cache, then there are 4 dirty bits making the total number of bits stored in the SRAM 26.

|26||||22|...|0|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|v|d|d|d|d|tag|tag

Because we stored the control bits within the
tag array SRAM, we must reset all values in the tag array during power on. For a 4 KB cache, this
requires a one time cost of 256 cycles, which is insignificant in comparison to run time.

### M1 Stage
The M1 stage performs the tag check and processes the control bits such as valid and dirty bits
with a data read from the tag array. The cache allocates to the MSHR if there is a miss and sets the
inputs to the data array SRAM during this stage as well. The M2 stage sends responses to the master
and requests to the minion if we need a refill.

For a 2-way associative cache, we had to store the replacement bits in a register to implement true LRU. For multiway associative cache, we use multiple tag arrays since we need to read from all of
them at the same time and check all the tags but only one large data array since by the M1 stage,
we will have known which way to read or write to. 

### M2 Stage
Sends the `MemMinion.resp` back to the processor and contains the `DataSizeMux`, which is a series of muxes to select the return data size based on the `len` field.

## Transactions
The cache supports the following transactions
1. [READ and Write](#read-and-write)
2. [WRITE_INIT](#write_init)
3. [Atomic Memory Operations (AMO)](#atomic-memory-operations-amo)
   1. AMO_ADD
   2. AMO_AND
   3. AMO_OR     
   4. AMO_SWAP   
   5. AMO_MIN    
   6. AMO_MINU   
   7. AMO_MAX    
   8. AMO_MAXU   
   9. AMO_XOR    
4. [INV](#inv)
5. [FLUSH](#flush)

### READ and WRITE
Reading and writing are the most basic operations of the cache. For reads, the cache reads from
the tag array in M0 and checks for a hit in M1 using the `TagArrayProcessingUnit`. This module
performs a tag check, reads the dirty bits, and marks which way the hit occurs. It also serves as a
gateway between the output of the tag array and the rest of the cache. If we read from the tag array,
then we will propagate the output of the tag array, otherwise, we ignore the tag array values. If
we have a hit, then we read from the data array with the index at the correct way offset and send
the minion response in M2. If we have a miss to a clean cache line, then we must perform a refill
request. The cache allocates an entry in the `MSHR`, which prompts the cache to stall, and sends a memory request in the M2 stage `MemMaster` interface. When we get the response, we will first refill
the cache and then replay the same transaction down the cache line. This requires two cycles but
isn’t significant in comparison to the memory access latency.

#### Hit Clean 
If we have a WRITE hit to a clean cache line, we must stall one extra cycle to write the dirty bit into the tag array. 
| transaction | 1 | 2 | 3 | 4 | 5 | 6 |
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|
|  rd (hit)   |M0 |M1 |M2 |
|  wr (hit clean)   |   |M0 |M0*|M1 |M2 |
|  wr (hit)   |   |   |  |M0 | M1|M2 |

#### Hit Dirty 
| transaction | 1 | 2 | 3 | 4 | 5 | 6 |
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|
|  rd (hit)   |M0 |M1 |M2 |
|  rd (hit)   |   |M0 |M1 |M2 |
|  rd (hit)   |   |   |M0 |M1 | M2|
|  rd (hit)   |   |   |   |M0 | M1| M2

#### Miss Clean 
If we have a miss, then we refuse the next transaction coming in until the miss is resolved.

| transaction | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|  rd (miss)  |M0 |M1 |M2 |...| Y |M0 |M1 |M2 |
|  rd (hit)   |   |   |   |   |   |   |M0 |M1 |M2|

#### Miss Dirty 
For a miss to a dirty line, we send a write memory request for the writeback and and read memory request for the refill. One transaction spawns two new ones going down the pipeline. Write responses are ignored.

| transaction | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |10
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| rd (evict)  |M0 |M1 |M2 |...|   |   |   |   |
|  refill     |   |   |M1 |M2 |...| Y |M0 |M1 |M2 |
|  rd (hit)   |   |   |   |   |   |   |   |M0 |M1 |M2 |

### WRITE_INIT
Init transaction is for testing only and allows the master to write directly into the cache. This is most useful in debugging and testing and should not be used in the final product.

### Atomic Memory Operations (AMO)
AMOs are handled in the main memory or L2 cache. This cache’s job is to pass the AMO using its `MemMaster` interface to a lower level cache, which will perform the
AMO and return values. There are some specific constraints; if we have cached data with the same
line as the target of the AMO, this data will be stale and we need to invalidate them. If the cached data is dirty, then we need to write back. All AMO behave the same in this cache since we just
forward the operation to the lower level cache. To build the request for MemMaster properly, we need
to use the `OffsetLenSelector` to choose the number of bytes to access. For
AMO, this will be 4 for 4-byte access. For any other transactions, we will default the byte access to 0
meaning we want line access.

#### AMO to Clean Line
| transaction | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |10
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|   rd        |M0 |M1 |M2 ||   |   |   |   |
|  AMO        |   |M0 |M1 |M2 |...| Y |M0 |M1 |M2 |

#### AMO to Dirty Line
| transaction | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |10
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|   wr        |M0 |M1 |M2 ||   |   |   |   |
| AMO (evict) |   |M0 |M1 |M2 |...|  |
|  AMO        |   |   |   |M1 |M2 |...| Y |M0 |M1 |M2 |


### INV
The invalidate transaction iterates through each line in the cache and invalidates it. Therefore,
we only need to write the control bits in the tag array. Just like cache initialization, we use the same
counter to set the index to the tag array and write zero to the valid bit. To help organize the writing
of the control bits and the tag in the tag array, we used a `UpdateTagArrayUnit` to build the tag array
write data depending on the transaction and state. We use this unit for the initialization state to
write clear all the data and for refills to set the control bits. To properly implement SC3, when we
have a miss to an invalid but dirty cache line, we do not perform a write-back because that is a flush.
Instead, we request a refill like a clean miss and then use the inverted dirty bits as the write mask for
the data array during refill. To achieve this, we store the dirty bits in the `MSHR` and use the `WbitEnGen`
to generate the write enable mask for the data array. The enable is bitwise so the WbitEnGen converts
the 4-bit dirty control to a 128-bit write enable mask where each bit in the dirty control is one 32-bit
word. We also added a invalid_hit status bit to signal that we have a hit to a dirty invalid line
and not just a regular invalid line. The cache relies on the invariant that an invalid and dirty line
will only be the result of an invalidate transaction because we initialize the tag array. One area for
improvement is that instead of always refill, we can look at the dirty bit and offset and check if the
word accessed is dirty. If it is dirty, then we simply respond with the word without requiring an
expensive refill request.

#### INV

| transaction | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |10
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| INV (start) |M0 |M1 |M2 ||   |   |   |   |
|     (write) |   |M0 |M1 |M2   |
|     ...     |   |
|     (end)   |   |  ... |M0 |M1 |M2 ||


### FLUSH
The flush transaction goes through every line and write back dirty lines and leave clean lines.
This transaction moves the FSM to FLUSH. The FSM is useful because the flush will spawn multiple
transactions that will go down the pipeline whose goal is to look at each line in the cache. Because
we stored the dirty bits in the tag array, we need two cycles max for each line. One cycle to read
from the tag array and if dirty, clear that dirty bit. This requires two accesses to the tag array, which
makes the two-cycle latency mandatory. We want to check if the line is dirty because we only write
back dirty lines in order to efficiently use the memory bandwidth. First, we read a line from the
tag array to check the first bit. If the line is dirty, the cache will then read the data from the data
array and send the write request to the main memory. Finally, the cache will transition to the state
FLUSH_WAIT and block until it receives a write acknowledgment from the main memory. For read
and write transactions, the cache ignores these because it uses the refill acknowledgment instead but
for flush it allows us to go down the pipeline again to clear the dirty bit in the tag array. After the
acknowledgment and dirty line update, we repeat this process for the next line.

#### FLUSH Example

| transaction | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |10
|:-:          |:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| FLUSH(start)|M0 |M1 |M2 ||  |   |   |   |
| (read/write)|   |M0 |M1 |M2 |...|Y  |M0 |M1 |M2 |
|      (wait) |   |   |M0 |M1 |M2 |
|      (wait) |   |   |   |M0 |M1 |M2 |
|      (wait) |   |   |   |   |M0 |M1 |M2 |
|      (wait) |   |   |   |   |   |M0 |M1 |M2 |
|      (end)  |   |   |   |   |   |   |   |M0 |M1 |M2 |

This example shows flushing a line that is dirty. We always read the line first for the dirty bit and then send a writeback if the line is dirty. If the line is dirty, we also need to clear the dirty, whose latency is hidden in the wait stages. While the writeback is in flight, the cache waits until the write comes back. This is the only case where a write response isn't ignored. The end state sends a `MemMinion.resp` signal to the processor to let it know it terminated.

## Testing

### Single Cache Testbench
The sink collects the output from the cache and checks for
correctness. The CIFER processor only sets the cache response ready signal only when it sends a
cache request. However, since we have separate models for the source and sink we cannot easily
replicate this dependency by simply connecting the source and sink to the DUT. For this reason, we created a `ProcModel` where we implement this rule to unify the cache request enable signal in the source and the cache response ready signal in the sink. The cache also connects to the magic memory that acts as a lower level cache for refills and AMO transactions.

![Single Cache Testbench](/doc/figures/testbench/single_cache_testing.svg)

### Multi-Cache Testbench
For multi-cache testing, we designed a modular test bench reusing components from single
cache testing and contains multiple single cache test
benches. The main challenge for testing multiple caches is that we have the possibility of transactions
executing in parallel. For example, transactions to two different caches can execute simultaneously
or sequentially and the user should be able to decide this outcome. To this end, we added an extra
layer to the test bench called the multicache model. We added two extra fields to each transaction:
cache number and order. Cache number indicates which cache this transaction is for and the order is
the priority of the transaction. The order of the transaction will determine when it will execute or sent
the cache. All transactions with the same order can execute simultaneously while transactions with
higher orders must wait for transactions with lower orders to finish executing. Currently, the multicache
testing only supports direct test cases where the user comes up with a sequence of transactions
and then test it. Random testing has many additional challenges such as the test generator needing
to generate a valid sequence of transactions that ensure coherence. This requires implementing an
additional coherence reference model for transactions.

![Multi-Cache Testbench](/doc/figures/testbench/multi_cache_testing.svg)

The testbench introduces two new modules `CurrOrderInFlight`,
which tracks the total number of transactions of this order still in flight, and `CurrOrderCounter`,
which keep track of the current order in the testbench. Before each order of transactions executes, we
load `CurrOrderInFlight` with the count of all transactions with the order. We can tell if the transaction
terminates by looking at the cache’s `MemMinion.resp.en` signal, which the cache pulls high
when it finishes executing a transaction. This is used to keep track of the number of transactions that
terminated per cycle and we subtract that from the amount in `CurrOrderInFlight`. Once we reach
zero, we increment the current order stored in `CurrOrderCounter` and load the number of transactions
with the next order. The `CurrOrderCounter` controls the `MemMinion.req.rdy` signal along with
the cache. It will only set the ready signal to high if the order of the incoming transaction matches
the order in `CurrOrderCounter`.

## Running The Code

### Running the Testbench

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
--dump-vtb    : dumps the verilog testbench 
--dump-vcd    : dumps vcd waveforms after translation and running the tests
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
--dbw : data bitwidth       (default 32)
--abw : address bitwidth    (default 32)
--obw : opaque bitwidth     (default 8)
--asso: associativity       (default 1)
```
