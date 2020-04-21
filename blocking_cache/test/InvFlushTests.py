"""
=========================================================================
 InvFlushTests.py
=========================================================================

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 March 2020
"""

import random
import pytest

from pymtl3 import *

from test.sim_utils import (req, resp, CacheReqType, CacheRespType,
  MemReqType, MemRespType, obw, abw, gen_req_resp, rand_mem
)
from mem_ifcs.MemMsg import mk_mem_msg, MemMsgType

from constants.constants import *

# Main memory used in cifer test cases
def cifer_test_memory():
  return [
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

def cache_invalidation_short():
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'rd',  1,  0x00000000, 0,  0),    resp( 'rd',  1,  0,   0,  0x01 ),
    req( 'rd',  2,  0x00000010, 0,  0),    resp( 'rd',  2,  0,   0,  0x11 ),
    req( 'rd',  3,  0x00000020, 0,  0),    resp( 'rd',  3,  0,   0,  0x21 ),
    req( 'rd',  4,  0x00000000, 0,  0),    resp( 'rd',  4,  1,   0,  0x01 ), # hit
    req( 'rd',  5,  0x00000010, 0,  0),    resp( 'rd',  5,  1,   0,  0x11 ),
    req( 'rd',  6,  0x00000020, 0,  0),    resp( 'rd',  6,  1,   0,  0x21 ),
    req( 'inv', 7,  0x00000000, 0,  0),    resp( 'inv', 7,  0,   0,  0 ),
    req( 'rd',  8,  0x00000000, 0,  0),    resp( 'rd',  8,  0,   0,  0x01 ), # should be miss after invalidation
    req( 'rd',  9,  0x00000010, 0,  0),    resp( 'rd',  9,  0,   0,  0x11 ),
    req( 'rd',  10, 0x00000020, 0,  0),    resp( 'rd',  10, 0,   0,  0x21 ),
  ]

def cache_invalidation_short():
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'rd',  1,  0x00000000, 0,  0),    resp( 'rd',  1,  0,   0,  0x01 ),
    req( 'rd',  2,  0x00000010, 0,  0),    resp( 'rd',  2,  0,   0,  0x11 ),
    req( 'rd',  3,  0x00000020, 0,  0),    resp( 'rd',  3,  0,   0,  0x21 ),
    req( 'rd',  4,  0x00000000, 0,  0),    resp( 'rd',  4,  1,   0,  0x01 ), # hit
    req( 'rd',  5,  0x00000010, 0,  0),    resp( 'rd',  5,  1,   0,  0x11 ),
    req( 'rd',  6,  0x00000020, 0,  0),    resp( 'rd',  6,  1,   0,  0x21 ),
    req( 'inv', 7,  0x00000000, 0,  0),    resp( 'inv', 7,  0,   0,  0 ),
    req( 'rd',  8,  0x00000000, 0,  0),    resp( 'rd',  8,  0,   0,  0x01 ), # should be miss after invalidation
    req( 'rd',  9,  0x00000010, 0,  0),    resp( 'rd',  9,  0,   0,  0x11 ),
    req( 'rd',  10, 0x00000020, 0,  0),    resp( 'rd',  10, 0,   0,  0x21 ),
  ]

def cache_inv_evict_short():
  return [
    #    type   opq addr        len data             type   opq test len data
    req( 'wr',  1,  0x00000014, 0,  0xc0ffee), resp( 'wr',  1,  0,   0,  0 ),        # line 0x10 are valid and dirty
    req( 'rd',  2,  0x00020014, 0,  0),        resp( 'rd',  2,  0,   0,  0xa ),      # line 0x20 is of the same set as 0x10
    req( 'inv', 3,  0x00000000, 0,  0),        resp( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    req( 'rd',  4,  0x00030014, 0,  0),        resp( 'rd',  4,  0,   0,  0xbbb ),    # this will replace the line addr=0x10
    req( 'rd',  5,  0x00000014, 0,  0),        resp( 'rd',  5,  0,   0,  0xc0ffee ), # check if line 0x10 is properly written back
  ]

def cache_invalidation_medium():
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'rd',  1,  0x00000000, 0,  0),    resp( 'rd',  1,  0,   0,  0x01 ),
    req( 'rd',  2,  0x00000010, 0,  0),    resp( 'rd',  2,  0,   0,  0x11 ),
    req( 'rd',  3,  0x00000020, 0,  0),    resp( 'rd',  3,  0,   0,  0x21 ),
    req( 'rd',  4,  0x00000000, 0,  0),    resp( 'rd',  4,  1,   0,  0x01 ),
    req( 'rd',  5,  0x00000010, 0,  0),    resp( 'rd',  5,  1,   0,  0x11 ),
    req( 'rd',  6,  0x00000020, 0,  0),    resp( 'rd',  6,  1,   0,  0x21 ),
    req( 'inv', 7,  0x00000000, 0,  0),    resp( 'inv', 7,  0,   0,  0 ),
    req( 'rd',  8,  0x00000000, 0,  0),    resp( 'rd',  8,  0,   0,  0x01 ), # should be miss after invalidation
    req( 'rd',  9,  0x00000010, 0,  0),    resp( 'rd',  9,  0,   0,  0x11 ),
    req( 'rd',  10, 0x00000020, 0,  0),    resp( 'rd',  10, 0,   0,  0x21 ),
    req( 'rd',  11, 0x00000000, 0,  0),    resp( 'rd',  11, 1,   0,  0x01 ),
    req( 'rd',  12, 0x00000010, 0,  0),    resp( 'rd',  12, 1,   0,  0x11 ),
    req( 'rd',  13, 0x00000020, 0,  0),    resp( 'rd',  13, 1,   0,  0x21 ),
    req( 'inv', 14, 0x00000000, 0,  0),    resp( 'inv', 14, 0,   0,  0 ),
    req( 'rd',  15, 0x00000000, 0,  0),    resp( 'rd',  15, 0,   0,  0x01 ),
    req( 'rd',  16, 0x00000010, 0,  0),    resp( 'rd',  16, 0,   0,  0x11 ),
    req( 'rd',  17, 0x00000020, 0,  0),    resp( 'rd',  17, 0,   0,  0x21 ),
  ]

def cache_flush_short():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'rd',  1,  0x00000000, 0,  0),          resp( 'rd',  1,  0,   0,  0x01 ),
    req( 'wr',  2,  0x00000010, 0,  0xdeadbeef), resp( 'wr',  2,  0,   0,  0 ),
    req( 'rd',  3,  0x00000020, 0,  0),          resp( 'rd',  3,  0,   0,  0x21 ),
    req( 'wr',  4,  0x00000030, 0,  0x0c0ffee),  resp( 'wr',  4,  0,   0,  0 ),
    req( 'fl',  5,  0,          0,  0),          resp( 'fl',  5,  0,   0,  0 ),
    req( 'rd',  6,  0x00000000, 0,  0),          resp( 'rd',  6,  1,   0,  0x01 ),       # should still be hits after flush
    req( 'rd',  7,  0x00000010, 0,  0),          resp( 'rd',  7,  1,   0,  0xdeadbeef ),
    req( 'rd',  8,  0x00000020, 0,  0),          resp( 'rd',  8,  1,   0,  0x21 ),
    req( 'rd',  9,  0x00000030, 0,  0),          resp( 'rd',  9,  1,   0,  0x0c0ffee ),
  ]

def flush_last_line1():
  # tests flush on the last line of the cache
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0x01), resp( 'wr',  1,  0,   0,  0 ),
    req( 'fl',  2,  0,          0,  0),    resp( 'fl',  2,  0,   0,  0 ),
    req( 'rd',  3,  0x00000000, 0,  0),    resp( 'rd',  3,  1,   0,  0x01 ),      
    ]

def flush_last_line2():
  # tests flush on the last 2 line of the cache
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0x01), resp( 'wr',  1,  0,   0,  0 ),
    req( 'wr',  2,  0x00000010, 0,  0x02), resp( 'wr',  2,  0,   0,  0 ),
    req( 'fl',  3,  0,          0,  0),    resp( 'fl',  3,  0,   0,  0 ),
    req( 'rd',  4,  0x00000000, 0,  0),    resp( 'rd',  4,  1,   0,  0x01 ),      
    req( 'rd',  5,  0x00000010, 0,  0),    resp( 'rd',  5,  1,   0,  0x02 ),      
    ]

def cache_inv_flush_short():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'rd',  1,  0x00000000, 0,  0),          resp( 'rd',  1,  0,   0,  0x01 ),
    req( 'wr',  2,  0x00000010, 0,  0xdeadbeef), resp( 'wr',  2,  0,   0,  0 ),
    req( 'rd',  3,  0x00000020, 0,  0),          resp( 'rd',  3,  0,   0,  0x21 ),
    req( 'wr',  4,  0x00000030, 0,  0x0c0ffee),  resp( 'wr',  4,  0,   0,  0 ),
    req( 'fl',  5,  0,          0,  0),          resp( 'fl',  5,  0,   0,  0 ),
    req( 'inv', 6,  0,          0,  0),          resp( 'inv', 6,  0,   0,  0 ),
    req( 'rd',  7,  0x00000000, 0,  0),          resp( 'rd',  7,  0,   0,  0x01 ),       # should be miss after invalidation
    req( 'rd',  8,  0x00000010, 0,  0),          resp( 'rd',  8,  0,   0,  0xdeadbeef ),
    req( 'rd',  9,  0x00000020, 0,  0),          resp( 'rd',  9,  0,   0,  0x21 ),
    req( 'rd',  10, 0x00000030, 0,  0),          resp( 'rd',  10, 0,   0,  0x0c0ffee ),
  ]

def cache_inv_simple1():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xff),       resp( 'wr',  1,  0,   0,  0x00 ),
    req( 'inv', 2,  0x00000000, 0,  0),          resp( 'inv', 2,  0,   0,  0 ),
    req( 'rd',  3,  0x00000000, 0,  0),          resp( 'rd',  3,  0,   0,  0xff ),
  ]

def cache_inv_simple2():
  return [
    #    type   opq addr        len data       type   opq test len data
    req( 'rd',  1,  0x00000000, 0,  0),  resp( 'rd',  1,  0,   0,  0x01 ),
    req( 'inv', 2,  0x00000000, 0,  0),  resp( 'inv', 2,  0,   0,  0 ),
    req( 'rd',  3,  0x00000000, 0,  0),  resp( 'rd',  3,  0,   0,  0x01 ),
  ]

def cache_inv_simple3():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xff),       resp( 'wr',  1,  0,   0,  0x00 ),
    req( 'inv', 2,  0x00000000, 0,  0),          resp( 'inv', 2,  0,   0,  0 ),
    req( 'wr',  3,  0x00000004, 0,  0x22),       resp( 'wr',  3,  0,   0,  0 ),
    req( 'rd',  4,  0x00000000, 0,  0),          resp( 'rd',  4,  1,   0,  0xff ),
    req( 'rd',  4,  0x00000004, 0,  0),          resp( 'rd',  4,  1,   0,  0x22 ),
  ]

def cache_inv_refill_short1():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000014, 0,  0xc0ffee),   resp( 'wr',  1,  0,   0,  0 ),          # line 0x10 word 1
    req( 'wr',  2,  0x0000001c, 0,  0xdeadbeef), resp( 'wr',  2,  1,   0,  0 ),          # line 0x10 word 3
    req( 'inv', 3,  0x00000000, 0,  0),          resp( 'inv', 3,  0,   0,  0 ),          # line 0x10 are invalid but dirty
    req( 'rd',  4,  0x00000014, 0,  0),          resp( 'rd',  4,  0,   0,  0xc0ffee ),   # check the dirty word (0 and 3) are not overwritten by the refill
    req( 'rd',  5,  0x0000001c, 0,  0),          resp( 'rd',  5,  1,   0,  0xdeadbeef ),
  ]

def cache_inv_refill_short2():
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0x1),  resp( 'wr',  1,  0,   0,  0x00 ), # way 0
    req( 'wr',  2,  0x00020000, 0,  0x2),  resp( 'wr',  2,  0,   0,  0x00 ), # way 1
    req( 'inv', 3,  0x00000000, 0,  0),    resp( 'inv', 3,  0,   0,  0 ),
    req( 'rd',  4,  0x00000000, 0,  0),    resp( 'rd',  4,  0,   0,  0x1 ),  # way 1
    req( 'rd',  5,  0x00020000, 0,  0),    resp( 'rd',  5,  0,   0,  0x2 ),
    req( 'rd',  6,  0x00020004, 0,  0),    resp( 'rd',  6,  1,   0,  0x6 ),
  ]

def cache_inv_refill_short3():
  return [
    #    type   opq addr        len data         type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0x1),  resp( 'wr',  1,  0,   0,  0x00 ), # way 0
    req( 'wr',  2,  0x00020000, 0,  0x2),  resp( 'wr',  2,  0,   0,  0x00 ), # way 1
    req( 'inv', 3,  0x00000000, 0,  0),    resp( 'inv', 3,  0,   0,  0 ),
    req( 'rd',  4,  0x00020000, 0,  0),    resp( 'rd',  4,  0,   0,  0x2 ),  # way 1
    req( 'rd',  5,  0x00000000, 0,  0),    resp( 'rd',  5,  0,   0,  0x1 ),
    req( 'rd',  6,  0x00020004, 0,  0),    resp( 'rd',  6,  1,   0,  0x6 ),
  ]

def cache_inv_refill_short4():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xc0ffee),   resp( 'wr',  1,  0,   0,  0 ),          # line 0x10 word 1
    req( 'wr',  2,  0x0000000c, 0,  0xdeadbeef), resp( 'wr',  2,  1,   0,  0 ),          # line 0x10 word 3
    req( 'inv', 3,  0x00000000, 0,  0),          resp( 'inv', 3,  0,   0,  0 ),          # line 0x10 are invalid but dirty
    req( 'wr',  4,  0x00020000, 0,  0x1),        resp( 'wr',  4,  0,   0,  0 ),          # check the dirty word (0 and 3) are not overwritten by the refill
    req( 'rd',  5,  0x0000000c, 0,  0),          resp( 'rd',  5,  0,   0,  0xdeadbeef ),
    req( 'rd',  6,  0x00000000, 0,  0),          resp( 'rd',  6,  1,   0,  0xc0ffee ),
    req( 'rd',  7,  0x00020000, 0,  0),          resp( 'rd',  7,  1,   0,  0x1 ),
  ]

# check if the lru is set correctly
def cache_inv_refill1():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xc0ffee),   resp( 'wr',  1,  0,   0,  0 ),          # line 0x10 word 1
    req( 'wr',  2,  0x0002000c, 0,  0xdeadbeef), resp( 'wr',  2,  0,   0,  0 ),          # line 0x10 word 3
    req( 'inv', 3,  0x00000000, 0,  0),          resp( 'inv', 3,  0,   0,  0 ),          # line 0x10 are invalid but dirty
    req( 'rd',  4,  0x00000000, 0,  0),          resp( 'rd',  4,  0,   0,  0xc0ffee ),
    req( 'rd',  5,  0x00030000, 0,  0),          resp( 'rd',  5,  0,   0,  0xd ),        # replace way 1; LRU way 0
    req( 'rd',  7,  0x00000000, 0,  0),          resp( 'rd',  7,  1,   0,  0xc0ffee ),   # LRU way 1
    req( 'rd',  6,  0x0002000c, 0,  0),          resp( 'rd',  6,  0,   0,  0xdeadbeef ), # replace way 1; LRU way 0
  ]

# test with amos
def cache_inv_refill2():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xc0ffee),   resp( 'wr',  1,  0,   0,  0 ),        # line 0x10 word 1
    req( 'wr',  2,  0x0002000c, 0,  0xdeadbeef), resp( 'wr',  2,  0,   0,  0 ),        # line 0x10 word 3
    req( 'inv', 3,  0x00000000, 0,  0),          resp( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    req( 'ad',  4,  0x00000000, 0,  0x1),        resp( 'ad',  4,  0,   0,  0xc0ffee ),
    req( 'rd',  5,  0x00000000, 0,  0),          resp( 'rd',  5,  0,   0,  0xc0ffef ), # replace way 1; LRU way 0
  ]

# test with amos after inv
def cache_inv_refill3():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xc0ffee),   resp( 'wr',  1,  0,   0,  0 ),        # line 0x10 word 1
    req( 'wr',  2,  0x00020000, 0,  0x1),        resp( 'wr',  2,  0,   0,  0 ),        # line 0x10 word 3
    req( 'inv', 3,  0x00000000, 0,  0),          resp( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    req( 'ad',  4,  0x00020000, 0,  0x10),       resp( 'ad',  4,  0,   0,  0x1 ),
    req( 'rd',  5,  0x00000000, 0,  0),          resp( 'rd',  5,  0,   0,  0xc0ffee ), # replace way 1; LRU way 0
    req( 'rd',  6,  0x00020000, 0,  0),          resp( 'rd',  6,  0,   0,  0x11 ),     # replace way 1; LRU way 0
  ]

# test with amos b4 inv
def cache_inv_refill4():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x00000000, 0,  0xc0ffee),   resp( 'wr',  1,  0,   0,  0 ),        # line 0x10 word 1
    req( 'wr',  2,  0x00020000, 0,  0x1),        resp( 'wr',  2,  0,   0,  0 ),        # line 0x10 word 3
    req( 'ad',  4,  0x00020000, 0,  0x10),       resp( 'ad',  4,  0,   0,  0x1 ),
    req( 'inv', 3,  0x00000000, 0,  0),          resp( 'inv', 3,  0,   0,  0 ),        # line 0x10 are invalid but dirty
    req( 'rd',  5,  0x00000000, 0,  0),          resp( 'rd',  5,  0,   0,  0xc0ffee ), # replace way 1; LRU way 0
    req( 'rd',  6,  0x00020000, 0,  0),          resp( 'rd',  6,  0,   0,  0x11 ),     # replace way 1; LRU way 0
  ]

# test with subword inv
def cache_inv_refill5():
  return [
    #    type   opq addr        len data               type   opq test len data
    req( 'wr',  1,  0x0000000e, 2,  0xffee),     resp( 'wr',  1,  0,   2,  0 ),       
    req( 'inv', 2,  0x00000000, 0,  0),          resp( 'inv', 2,  0,   0,  0 ),       
    req( 'rd',  3,  0x0000000e, 2,  0),          resp( 'rd',  3,  0,   2,  0xffee ),  
  ]

def hypo_1():
  # testing double flush
  return [
    #    type   opq addr        len data        type  opq test len data
    req( 'fl',  0,  0x00000000, 0,  0x0), resp( 'fl', 0,  0,   0,  0 ),    
    req( 'fl',  1,  0x00000000, 0,  0x0), resp( 'fl', 1,  0,   0,  0 ),    
  ]

def hypo_2():
  # testing double flush
  return [
    #    type   opq addr        len data        type   opq test len data
    req( 'wr',  0,  0x00000000, 0,  0xa), resp( 'wr',  0,  0,   0,  0 ),    
    req( 'inv', 1,  0x00000000, 0,  0x0), resp( 'inv', 1,  0,   0,  0 ),    
    req( 'rd',  2,  0x00000000, 0,  0x0), resp( 'rd',  2,  0,   0,  0xa ),    
    req( 'inv', 3,  0x00000000, 0,  0x0), resp( 'inv', 3,  0,   0,  0 ),    
    req( 'rd',  4,  0x00000000, 0,  0x0), resp( 'rd',  4,  0,   0,  0xa ),    
  ]

def iterative_mem( start, end ):
  mem = []
  curr_addr = start
  while curr_addr <= end:
    mem.append(curr_addr)
    mem.append(curr_addr)
    curr_addr += 4
  return mem
random_memory = rand_mem( 0, 0xffff )
# random_memory = iterative_mem( 0, 0xffff )

def rand( size, clw, associativity, num_trans = 200 ):
  random.seed(0xdeadbeef)
  global random_memory
  max_addr = int( size // 4 * 3 * associativity )
  MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)
  type_choices = [ (MemMsgType.READ,     0.42) ,
                   (MemMsgType.WRITE,    0.42),
                   (MemMsgType.AMO_ADD,  0.02),
                   (MemMsgType.AMO_AND,  0.01),
                   (MemMsgType.AMO_OR,   0.01),
                   (MemMsgType.AMO_SWAP, 0.01),
                   (MemMsgType.AMO_MIN,  0.01),
                   (MemMsgType.AMO_MINU, 0.01),
                   (MemMsgType.AMO_MAX,  0.01),
                   (MemMsgType.AMO_MAXU, 0.01),
                   (MemMsgType.AMO_XOR,  0.01),
                   (MemMsgType.INV,      0.03),
                   (MemMsgType.FLUSH,    0.03),
                   ]
  types = random.choices(
      population = [ choices for choices,weights in type_choices ],
      weights = [ weights for choices,weights in type_choices ],
      k = num_trans )
  reqs = []
  for i in range( num_trans ):
    if types[i] == MemMsgType.INV or types[i] == MemMsgType.FLUSH:
      data = 0
      len_ = 0
      addr = 0
    else:
      data = random.randint(0, 0xffffffff)
      if types[i] < AMO:
        len_choices = [  # assuming 32 bit words
          (0, 0.4),
          (1, 0.3),
          (2, 0.3)
        ]
        len_ = random.choices(
          population = [ choices for choices,weights in len_choices ],
          weights = [ weights for choices,weights in len_choices ],
          k = 1 )
        len_ = len_[0]
        if len_ == 1:
          addr = Bits32(random.randint(0, max_addr)) & 0xffffffff
        elif len_ == 2:
          addr = Bits32(random.randint(0, max_addr)) & 0xfffffffe
        else:
          addr = Bits32(random.randint(0, max_addr)) & 0xfffffffc
      else:
        len_ = 0
        addr = Bits32(random.randint(0, max_addr)) & 0xfffffffc
    reqs.append( req( types[i], i, addr, len_, data) )

  trans = gen_req_resp( reqs, random_memory, CacheReqType, CacheRespType, MemReqType,
                        MemRespType, associativity, size )

  # print stats
  hits = 0
  for i in range( 1, num_trans, 2 ):
    if trans[i].test:
      hits += 1
  print( f"\nhit rate:{hits/num_trans}\n")

  return trans

def rand_d_16_64():
  return rand(16, 64, 1)

def rand_d_32_128():
  return rand(32, 128, 1)

def rand_2_32_64():
  return rand(32, 64, 2)

def rand_2_64_128():
  return rand(64, 128, 2)

def rand_2_4096_128():
  return rand(4096, 128, 2)

#-------------------------------------------------------------------------
# Test driver
#-------------------------------------------------------------------------

class InvFlushTests:

  @pytest.mark.parametrize(
    " name,    test,                          stall_prob,latency,src_delay,sink_delay", [
    ("INV",    cache_invalidation_short,      0,         1,      0,        0   ),
    ("INV",    cache_invalidation_medium,     0,         1,      0,        0   ),
    ("INV",    cache_inv_evict_short,         0,         1,      0,        0   ),
    ("INV",    cache_inv_refill_short1,       0,         1,      0,        0   ),
    ("INV",    cache_inv_refill_short2,       0,         1,      0,        0   ),
    ("FLUSH",  cache_flush_short,             0,         1,      0,        0   ),
    ("INVFL",  cache_inv_flush_short,         0,         1,      0,        0   ),
    ("INV",    cache_invalidation_short,      0,         5,      0,        0   ),
    ("INV",    cache_invalidation_medium,     0,         5,      0,        0   ),
    ("FLUSH",  cache_flush_short,             0,         5,      0,        0   ),
    ("INVFL",  cache_inv_flush_short,         0,         5,      0,        0   ),
    ("INV",    cache_invalidation_short,      0,         1,      2,        2   ),
    ("INV",    cache_invalidation_medium,     0,         1,      2,        2   ),
    ("INV",    cache_inv_evict_short,         0,         1,      2,        2   ),
    ("INV",    cache_inv_refill_short1,       0,         1,      2,        2   ),
    ("INV",    cache_inv_refill_short2,       0,         1,      2,        2   ),
    ("FLUSH",  cache_flush_short,             0,         1,      2,        2   ),
    ("INVFL",  cache_inv_flush_short,         0,         1,      2,        2   ),
    ("INV",    cache_invalidation_short,      0,         5,      2,        2   ),
    ("INV",    cache_invalidation_medium,     0,         5,      2,        2   ),
    ("FLUSH",  cache_flush_short,             0,         5,      2,        2   ),
    ("INVFL",  cache_inv_flush_short,         0,         5,      2,        2   ),
  ])
  def test_Cifer_2way_size256_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                      stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                256, stall_prob, latency, src_delay, sink_delay, dump_vcd,
                test_verilog, max_cycles, dump_vtb )

  @pytest.mark.parametrize(
    " name,    test,                          stall_prob,latency,src_delay,sink_delay", [
    ("INV",    cache_invalidation_short,      0,         1,      0,        0   ),
    ("INV",    cache_invalidation_medium,     0,         1,      0,        0   ),
    ("FLUSH",  cache_flush_short,             0,         1,      0,        0   ),
    ("INVFL",  cache_inv_flush_short,         0,         1,      0,        0   ),
    ("INV",    cache_invalidation_short,      0,         5,      0,        0   ),
    ("INV",    cache_invalidation_medium,     0,         5,      0,        0   ),
    ("FLUSH",  cache_flush_short,             0,         5,      0,        0   ),
    ("INVFL",  cache_inv_flush_short,         0,         5,      0,        0   ),
    ("RAND",   rand_2_4096_128,               0,         1,      0,        0   ),
    ("RAND",   rand_2_4096_128,               0,         2,      0,        2   ),
  ])
  def test_Cifer_2way_size4096_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                       stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                4096, stall_prob, latency, src_delay, sink_delay, dump_vcd,
                test_verilog, max_cycles, dump_vtb )

  @pytest.mark.parametrize(
    " name,    test,                    stall_prob,latency,src_delay,sink_delay", [
    ("INV",    cache_inv_refill_short1, 0,         1,      0,        0   ),
    ("INV",    cache_inv_refill_short2, 0,         1,      0,        0   ),
    ("INV",    cache_inv_refill_short3, 0,         1,      0,        0   ),
    ("INV",    cache_inv_refill_short4, 0,         1,      0,        0   ),
    ("INV",    cache_inv_simple1,       0,         1,      0,        0   ),
    ("INV",    cache_inv_simple2,       0,         1,      0,        0   ),
    ("INV",    cache_inv_simple3,       0,         1,      0,        0   ),
    ("INV",    cache_inv_refill1,       0,         1,      0,        0   ),
    ("INV",    cache_inv_refill2,       0,         1,      0,        0   ),
    ("INV",    cache_inv_refill3,       0,         1,      0,        0   ),
    ("INV",    cache_inv_refill4,       0,         1,      0,        0   ),
    ("INV",    cache_inv_refill_short1, 1,         2,      1,        2   ),
    ("INV",    cache_inv_refill_short2, 1,         2,      1,        2   ),
    ("INV",    cache_inv_refill_short3, 1,         2,      1,        2   ),
    ("INV",    cache_inv_refill_short4, 1,         2,      1,        2   ),
    ("INV",    cache_inv_simple1,       1,         2,      1,        2   ),
    ("INV",    cache_inv_simple2,       1,         2,      1,        2   ),
    ("INV",    cache_inv_refill1,       1,         2,      1,        2   ),
    ("INV",    cache_inv_refill2,       1,         2,      1,        2   ),
    ("INV",    cache_inv_refill3,       1,         2,      1,        2   ),
    ("INV",    cache_inv_refill4,       1,         2,      1,        2   ),
    ("HYP",    hypo_1,                  1,         2,      1,        2   ),
    ])
  def test_Cifer_2way_size64_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                     stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                64, stall_prob, latency, src_delay, sink_delay, dump_vcd,
                test_verilog, max_cycles, dump_vtb )


  @pytest.mark.parametrize(
    " name,    test,                    stall_prob,latency,src_delay,sink_delay", [
    ("HYP",    hypo_1,                  0,         1,      0,        0   ),
    ("HYP",    hypo_1,                  0,         1,      0,        1   ),
    ("HYP",    hypo_1,                  0,         1,      0,        2   ),
    ("HYP",    hypo_1,                  0,         1,      0,        3   ),
    ("HYP",    hypo_2,                  0,         1,      0,        0   ),
    ("FLUSH",  flush_last_line1,        0,         1,      0,        0  ),
    ("FLUSH",  flush_last_line2,        0,         1,      0,        0  ),
    ("INV",    cache_inv_refill5,       0,         1,      0,        0  ),
    ("INV",    cache_inv_refill5,       0,         1,      0,        2  ),
    ("RAND",   rand_d_32_128,           0,         1,      0,        0  ),
    ("RAND",   rand_d_32_128,           0,         2,      0,        2  ),
    ])
  def test_Cifer_dmapped_size32_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                     stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
                32, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, 
                max_cycles, dump_vtb )


  @pytest.mark.parametrize(
    " name,    test,                stall_prob,latency,src_delay,sink_delay", [
    ("RAND",   rand_2_64_128,       0,         1,      0,        0  ),
    ("RAND",   rand_2_64_128,       0,         1,      0,        2  ),
    ])
  def test_Cifer_2way_size64_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                     stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                64, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, 
                max_cycles, dump_vtb )
