"""
=========================================================================
 InvFlushTests.py
=========================================================================

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 March 2020
"""

import pytest
from test.sim_utils import SingleCacheTestParams

inv_flush_mem = [
  0x00000000, 1,
  0x00000004, 2,
  0x00000008, 3,
  0x0000000c, 4,
  0x00000010, 0x11,
  0x00000014, 0x12,
  0x00000018, 0x13,
  0x0000001c, 0x14,
  0x00000020, 0x21,
  0x00000024, 0x22,
  0x00000028, 0x23,
  0x0000002c, 0x24,
  0x00000030, 0x31,
  0x00000034, 0x32,
  0x00000038, 0x33,
  0x0000003c, 0x34,
  0x00020000, 5,
  0x00020004, 6,
  0x00020008, 7,
  0x0002000c, 8,
  0x00020010, 9,
  0x00020014, 0xa,
  0x00020018, 0xb,
  0x0002001c, 0xc,
  0x00030000, 0xd,
  0x00030004, 0xe,
  0x00030008, 0xf,
  0x0003000c, 0x10,
  0x00030010, 0xaaa,
  0x00030014, 0xbbb,
  0x00030018, 0xccc,
  0x0000005c, 9,
  0x00000060, 0xa,
]

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def invalidation_short():
  msg =  [
    #    type   opq addr        len data         type   opq test len data
    ( 'rd',  1,  0x00000000, 0,  0),    ( 'rd',  1,  0,   0,  0x01 ),
    ( 'rd',  2,  0x00000010, 0,  0),    ( 'rd',  2,  0,   0,  0x11 ),
    ( 'rd',  3,  0x00000020, 0,  0),    ( 'rd',  3,  0,   0,  0x21 ),
    ( 'rd',  4,  0x00000000, 0,  0),    ( 'rd',  4,  1,   0,  0x01 ), # hit
    ( 'rd',  5,  0x00000010, 0,  0),    ( 'rd',  5,  1,   0,  0x11 ),
    ( 'rd',  6,  0x00000020, 0,  0),    ( 'rd',  6,  1,   0,  0x21 ),
    ( 'inv', 7,  0x00000000, 0,  0),    ( 'inv', 7,  0,   0,  0 ),
    ( 'rd',  8,  0x00000000, 0,  0),    ( 'rd',  8,  0,   0,  0x01 ), # should be miss after invalidation
    ( 'rd',  9,  0x00000010, 0,  0),    ( 'rd',  9,  0,   0,  0x11 ),
    ( 'rd',  10, 0x00000020, 0,  0),    ( 'rd',  10, 0,   0,  0x21 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=256 )

def inv_evict_short():
  msg =  [
    #    type   opq addr        len data             type   opq test len data
    ( 'wr',  1,  0x00000014, 0,  0xc0ffee), ( 'wr',  1,  0,   0,  0 ),        # line 0x10 are valid and dirty
    ( 'rd',  2,  0x00020014, 0,  0),        ( 'rd',  2,  0,   0,  0xa ),      # line 0x20 is of the same set as 0x10
    ( 'inv', 3,  0x00000000, 0,  0),        ( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    ( 'rd',  4,  0x00030014, 0,  0),        ( 'rd',  4,  0,   0,  0xbbb ),    # this will replace the line addr=0x10
    ( 'rd',  5,  0x00000014, 0,  0),        ( 'rd',  5,  0,   0,  0xc0ffee ), # check if line 0x10 is properly written back
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=256 )

def invalidation_medium():
  msg =  [
    #    type   opq addr        len data         type   opq test len data
    ( 'rd',  1,  0x00000000, 0,  0),    ( 'rd',  1,  0,   0,  0x01 ),
    ( 'rd',  2,  0x00000010, 0,  0),    ( 'rd',  2,  0,   0,  0x11 ),
    ( 'rd',  3,  0x00000020, 0,  0),    ( 'rd',  3,  0,   0,  0x21 ),
    ( 'rd',  4,  0x00000000, 0,  0),    ( 'rd',  4,  1,   0,  0x01 ),
    ( 'rd',  5,  0x00000010, 0,  0),    ( 'rd',  5,  1,   0,  0x11 ),
    ( 'rd',  6,  0x00000020, 0,  0),    ( 'rd',  6,  1,   0,  0x21 ),
    ( 'inv', 7,  0x00000000, 0,  0),    ( 'inv', 7,  0,   0,  0 ),
    ( 'rd',  8,  0x00000000, 0,  0),    ( 'rd',  8,  0,   0,  0x01 ), # should be miss after invalidation
    ( 'rd',  9,  0x00000010, 0,  0),    ( 'rd',  9,  0,   0,  0x11 ),
    ( 'rd',  10, 0x00000020, 0,  0),    ( 'rd',  10, 0,   0,  0x21 ),
    ( 'rd',  11, 0x00000000, 0,  0),    ( 'rd',  11, 1,   0,  0x01 ),
    ( 'rd',  12, 0x00000010, 0,  0),    ( 'rd',  12, 1,   0,  0x11 ),
    ( 'rd',  13, 0x00000020, 0,  0),    ( 'rd',  13, 1,   0,  0x21 ),
    ( 'inv', 14, 0x00000000, 0,  0),    ( 'inv', 14, 0,   0,  0 ),
    ( 'rd',  15, 0x00000000, 0,  0),    ( 'rd',  15, 0,   0,  0x01 ),
    ( 'rd',  16, 0x00000010, 0,  0),    ( 'rd',  16, 0,   0,  0x11 ),
    ( 'rd',  17, 0x00000020, 0,  0),    ( 'rd',  17, 0,   0,  0x21 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=256 )

def flush_short():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'rd',  1,  0x00000000, 0,  0),          ( 'rd',  1,  0,   0,  0x01 ),
    ( 'wr',  2,  0x00000010, 0,  0xdeadbeef), ( 'wr',  2,  0,   0,  0 ),
    ( 'rd',  3,  0x00000020, 0,  0),          ( 'rd',  3,  0,   0,  0x21 ),
    ( 'wr',  4,  0x00000030, 0,  0x0c0ffee),  ( 'wr',  4,  0,   0,  0 ),
    ( 'fl',  5,  0,          0,  0),          ( 'fl',  5,  0,   0,  0 ),
    ( 'rd',  6,  0x00000000, 0,  0),          ( 'rd',  6,  1,   0,  0x01 ),       # should still be hits after flush
    ( 'rd',  7,  0x00000010, 0,  0),          ( 'rd',  7,  1,   0,  0xdeadbeef ),
    ( 'rd',  8,  0x00000020, 0,  0),          ( 'rd',  8,  1,   0,  0x21 ),
    ( 'rd',  9,  0x00000030, 0,  0),          ( 'rd',  9,  1,   0,  0x0c0ffee ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=256 )

def flush_last_line1():
  # tests flush on the last line of the cache
  msg =  [
    #    type   opq addr        len data         type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0x01), ( 'wr',  1,  0,   0,  0 ),
    ( 'fl',  2,  0,          0,  0),    ( 'fl',  2,  0,   0,  0 ),
    ( 'rd',  3,  0x00000000, 0,  0),    ( 'rd',  3,  1,   0,  0x01 ),      
    ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def flush_last_line2():
  # tests flush on the last 2 line of the cache
  msg =  [
    #    type   opq addr        len data         type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0x01), ( 'wr',  1,  0,   0,  0 ),
    ( 'wr',  2,  0x00000010, 0,  0x02), ( 'wr',  2,  0,   0,  0 ),
    ( 'fl',  3,  0,          0,  0),    ( 'fl',  3,  0,   0,  0 ),
    ( 'rd',  4,  0x00000000, 0,  0),    ( 'rd',  4,  1,   0,  0x01 ),      
    ( 'rd',  5,  0x00000010, 0,  0),    ( 'rd',  5,  1,   0,  0x02 ),      
    ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_flush_short():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'rd',  1,  0x00000000, 0,  0),          ( 'rd',  1,  0,   0,  0x01 ),
    ( 'wr',  2,  0x00000010, 0,  0xdeadbeef), ( 'wr',  2,  0,   0,  0 ),
    ( 'rd',  3,  0x00000020, 0,  0),          ( 'rd',  3,  0,   0,  0x21 ),
    ( 'wr',  4,  0x00000030, 0,  0x0c0ffee),  ( 'wr',  4,  0,   0,  0 ),
    ( 'fl',  5,  0,          0,  0),          ( 'fl',  5,  0,   0,  0 ),
    ( 'inv', 6,  0,          0,  0),          ( 'inv', 6,  0,   0,  0 ),
    ( 'rd',  7,  0x00000000, 0,  0),          ( 'rd',  7,  0,   0,  0x01 ),       # should be miss after invalidation
    ( 'rd',  8,  0x00000010, 0,  0),          ( 'rd',  8,  0,   0,  0xdeadbeef ),
    ( 'rd',  9,  0x00000020, 0,  0),          ( 'rd',  9,  0,   0,  0x21 ),
    ( 'rd',  10, 0x00000030, 0,  0),          ( 'rd',  10, 0,   0,  0x0c0ffee ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=256 )

def inv_simple1():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xff),       ( 'wr',  1,  0,   0,  0x00 ),
    ( 'inv', 2,  0x00000000, 0,  0),          ( 'inv', 2,  0,   0,  0 ),
    ( 'rd',  3,  0x00000000, 0,  0),          ( 'rd',  3,  0,   0,  0xff ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_simple2():
  msg =  [
    #    type   opq addr        len data       type   opq test len data
    ( 'rd',  1,  0x00000000, 0,  0),  ( 'rd',  1,  0,   0,  0x01 ),
    ( 'inv', 2,  0x00000000, 0,  0),  ( 'inv', 2,  0,   0,  0 ),
    ( 'rd',  3,  0x00000000, 0,  0),  ( 'rd',  3,  0,   0,  0x01 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_simple3():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xff),       ( 'wr',  1,  0,   0,  0x00 ),
    ( 'inv', 2,  0x00000000, 0,  0),          ( 'inv', 2,  0,   0,  0 ),
    ( 'wr',  3,  0x00000004, 0,  0x22),       ( 'wr',  3,  0,   0,  0 ),
    ( 'rd',  4,  0x00000000, 0,  0),          ( 'rd',  4,  1,   0,  0xff ),
    ( 'rd',  4,  0x00000004, 0,  0),          ( 'rd',  4,  1,   0,  0x22 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_refill_short1():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000014, 0,  0xc0ffee),   ( 'wr',  1,  0,   0,  0 ),          # line 0x10 word 1
    ( 'wr',  2,  0x0000001c, 0,  0xdeadbeef), ( 'wr',  2,  1,   0,  0 ),          # line 0x10 word 3
    ( 'inv', 3,  0x00000000, 0,  0),          ( 'inv', 3,  0,   0,  0 ),          # line 0x10 are invalid but dirty
    ( 'rd',  4,  0x00000014, 0,  0),          ( 'rd',  4,  0,   0,  0xc0ffee ),   # check the dirty word (0 and 3) are not overwritten by the refill
    ( 'rd',  5,  0x0000001c, 0,  0),          ( 'rd',  5,  1,   0,  0xdeadbeef ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_refill_short2():
  msg =  [
    #    type   opq addr        len data         type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0x1),  ( 'wr',  1,  0,   0,  0x00 ), # way 0
    ( 'wr',  2,  0x00020000, 0,  0x2),  ( 'wr',  2,  0,   0,  0x00 ), # way 1
    ( 'inv', 3,  0x00000000, 0,  0),    ( 'inv', 3,  0,   0,  0 ),
    ( 'rd',  4,  0x00000000, 0,  0),    ( 'rd',  4,  0,   0,  0x1 ),  # way 1
    ( 'rd',  5,  0x00020000, 0,  0),    ( 'rd',  5,  0,   0,  0x2 ),
    ( 'rd',  6,  0x00020004, 0,  0),    ( 'rd',  6,  1,   0,  0x6 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_refill_short3():
  msg =  [
    #    type   opq addr        len data         type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0x1),  ( 'wr',  1,  0,   0,  0x00 ), # way 0
    ( 'wr',  2,  0x00020000, 0,  0x2),  ( 'wr',  2,  0,   0,  0x00 ), # way 1
    ( 'inv', 3,  0x00000000, 0,  0),    ( 'inv', 3,  0,   0,  0 ),
    ( 'rd',  4,  0x00020000, 0,  0),    ( 'rd',  4,  0,   0,  0x2 ),  # way 1
    ( 'rd',  5,  0x00000000, 0,  0),    ( 'rd',  5,  0,   0,  0x1 ),
    ( 'rd',  6,  0x00020004, 0,  0),    ( 'rd',  6,  1,   0,  0x6 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def inv_refill_short4():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xc0ffee),   ( 'wr',  1,  0,   0,  0 ),          # line 0x10 word 1
    ( 'wr',  2,  0x0000000c, 0,  0xdeadbeef), ( 'wr',  2,  1,   0,  0 ),          # line 0x10 word 3
    ( 'inv', 3,  0x00000000, 0,  0),          ( 'inv', 3,  0,   0,  0 ),          # line 0x10 are invalid but dirty
    ( 'wr',  4,  0x00020000, 0,  0x1),        ( 'wr',  4,  0,   0,  0 ),          # check the dirty word (0 and 3) are not overwritten by the refill
    ( 'rd',  5,  0x0000000c, 0,  0),          ( 'rd',  5,  0,   0,  0xdeadbeef ),
    ( 'rd',  6,  0x00000000, 0,  0),          ( 'rd',  6,  1,   0,  0xc0ffee ),
    ( 'rd',  7,  0x00020000, 0,  0),          ( 'rd',  7,  1,   0,  0x1 ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

# check if the lru is set correctly
def inv_refill1():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xc0ffee),   ( 'wr',  1,  0,   0,  0 ),          # line 0x10 word 1
    ( 'wr',  2,  0x0002000c, 0,  0xdeadbeef), ( 'wr',  2,  0,   0,  0 ),          # line 0x10 word 3
    ( 'inv', 3,  0x00000000, 0,  0),          ( 'inv', 3,  0,   0,  0 ),          # line 0x10 are invalid but dirty
    ( 'rd',  4,  0x00000000, 0,  0),          ( 'rd',  4,  0,   0,  0xc0ffee ),
    ( 'rd',  5,  0x00030000, 0,  0),          ( 'rd',  5,  0,   0,  0xd ),        # replace way 1; LRU way 0
    ( 'rd',  7,  0x00000000, 0,  0),          ( 'rd',  7,  1,   0,  0xc0ffee ),   # LRU way 1
    ( 'rd',  6,  0x0002000c, 0,  0),          ( 'rd',  6,  0,   0,  0xdeadbeef ), # replace way 1; LRU way 0
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

# test with amos
def inv_refill2():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xc0ffee),   ( 'wr',  1,  0,   0,  0 ),        # line 0x10 word 1
    ( 'wr',  2,  0x0002000c, 0,  0xdeadbeef), ( 'wr',  2,  0,   0,  0 ),        # line 0x10 word 3
    ( 'inv', 3,  0x00000000, 0,  0),          ( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    ( 'ad',  4,  0x00000000, 0,  0x1),        ( 'ad',  4,  0,   0,  0xc0ffee ),
    ( 'rd',  5,  0x00000000, 0,  0),          ( 'rd',  5,  0,   0,  0xc0ffef ), # replace way 1; LRU way 0
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

# test with amos after inv
def inv_refill3():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xc0ffee),   ( 'wr',  1,  0,   0,  0 ),        # line 0x10 word 1
    ( 'wr',  2,  0x00020000, 0,  0x1),        ( 'wr',  2,  0,   0,  0 ),        # line 0x10 word 3
    ( 'inv', 3,  0x00000000, 0,  0),          ( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    ( 'ad',  4,  0x00020000, 0,  0x10),       ( 'ad',  4,  0,   0,  0x1 ),
    ( 'rd',  5,  0x00000000, 0,  0),          ( 'rd',  5,  0,   0,  0xc0ffee ), # replace way 1; LRU way 0
    ( 'rd',  6,  0x00020000, 0,  0),          ( 'rd',  6,  0,   0,  0x11 ),     # replace way 1; LRU way 0
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

# test with amos b4 inv
def inv_refill4():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x00000000, 0,  0xc0ffee),   ( 'wr',  1,  0,   0,  0 ),        # line 0x10 word 1
    ( 'wr',  2,  0x00020000, 0,  0x1),        ( 'wr',  2,  0,   0,  0 ),        # line 0x10 word 3
    ( 'ad',  4,  0x00020000, 0,  0x10),       ( 'ad',  4,  0,   0,  0x1 ),
    ( 'inv', 3,  0x00000000, 0,  0),          ( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    ( 'rd',  5,  0x00000000, 0,  0),          ( 'rd',  5,  0,   0,  0xc0ffee ), # replace way 1; LRU way 0
    ( 'rd',  6,  0x00020000, 0,  0),          ( 'rd',  6,  0,   0,  0x11 ),     # replace way 1; LRU way 0
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

# test with subword inv
def inv_refill5():
  msg =  [
    #    type   opq addr        len data               type   opq test len data
    ( 'wr',  1,  0x0000000e, 2,  0xffee),     ( 'wr',  1,  0,   2,  0 ),       
    ( 'inv', 2,  0x00000000, 0,  0),          ( 'inv', 2,  0,   0,  0 ),       
    ( 'rd',  3,  0x0000000e, 2,  0),          ( 'rd',  3,  0,   2,  0xffee ),  
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def hypo_1():
  # testing double flush
  msg =  [
    #    type   opq addr        len data        type  opq test len data
    ( 'fl',  0,  0x00000000, 0,  0x0), ( 'fl', 0,  0,   0,  0 ),    
    ( 'fl',  1,  0x00000000, 0,  0x0), ( 'fl', 1,  0,   0,  0 ),    
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def hypo_2():
  # testing double flush
  msg =  [
    #    type   opq addr        len data        type   opq test len data
    ( 'wr',  0,  0x00000000, 0,  0xa), ( 'wr',  0,  0,   0,  0 ),    
    ( 'inv', 1,  0x00000000, 0,  0x0), ( 'inv', 1,  0,   0,  0 ),    
    ( 'rd',  2,  0x00000000, 0,  0x0), ( 'rd',  2,  0,   0,  0xa ),    
    ( 'inv', 3,  0x00000000, 0,  0x0), ( 'inv', 3,  0,   0,  0 ),    
    ( 'rd',  4,  0x00000000, 0,  0x0), ( 'rd',  4,  0,   0,  0xa ),    
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def hypo_test():
  # testing double flush
  msg =  [
    #    type   opq addr        len data        type   opq test len data
    ( 'inv', 0,  0x00000000, 0,  0x0), ( 'inv', 0,  0,   0,  0 ),    
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

#-------------------------------------------------------------------------
# Test driver
#-------------------------------------------------------------------------

class InvFlushTests:
  @pytest.mark.parametrize(
    " name,    test,                stall_prob,latency,src_delay,sink_delay", [
    ("256B-2", invalidation_short,  0,         1,      0,        0   ),
    ("256B-2", inv_evict_short,     0,         1,      0,        0   ),
    ("256B-2", invalidation_medium, 0,         1,      0,        0   ),
    ("256B-2", flush_short,         0,         1,      0,        0   ),
    ("32B-1",  flush_last_line1,    0,         1,      0,        0   ),
    ("32B-1",  flush_last_line2,    0,         1,      0,        0   ),
    ("256B-2", inv_flush_short,     0,         1,      0,        0   ),
    ("64B-2",  inv_simple1,         0,         1,      0,        0   ),
    ("64B-2",  inv_simple2,         0,         1,      0,        0   ),
    ("64B-2",  inv_simple3,         0,         1,      0,        0   ),
    ("64B-2",  inv_refill_short1,   0,         1,      0,        0   ),
    ("64B-2",  inv_refill_short2,   0,         1,      0,        0   ),
    ("64B-2",  inv_refill_short3,   0,         1,      0,        0   ),
    ("64B-2",  inv_refill_short4,   0,         1,      0,        0   ),
    ("64B-2",  inv_refill1,         0,         1,      0,        0   ),
    ("64B-2",  inv_refill2,         0,         1,      0,        0   ),
    ("64B-2",  inv_refill3,         0,         1,      0,        0   ),
    ("64B-2",  inv_refill4,         0,         1,      0,        0   ),
    ("32B-1",  inv_refill5,         0,         1,      0,        0   ),
    ("32B-1",  hypo_1,              0,         1,      0,        0   ),
    ("32B-1",  hypo_2,              0,         1,      0,        0   ),
    ("32B-1",  hypo_test,              0,         1,      0,        0   ),
  ])
  def test_InvFlush( s, name, test, stall_prob, latency, src_delay, sink_delay,
                     cmdline_opts, max_cycles, dump_vtb, line_trace ):
    p = test()            
    s.run_test( p.msg, p.mem, p.CacheReqType, p.CacheRespType, p.MemReqType, p.MemRespType, 
                p.associativity, p.size, stall_prob, latency, src_delay, sink_delay, 
                cmdline_opts, max_cycles, dump_vtb, line_trace )
