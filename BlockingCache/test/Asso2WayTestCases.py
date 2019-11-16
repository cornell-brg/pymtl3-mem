"""
=========================================================================
Asso2WayTestCases.py
=========================================================================
2 way set associative cache test cases

Author : Xiaoyu Yan, Eric Tang
Date   : 16 November 2019
"""

import pytest
import struct
import random
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128
CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
MemMsg = ReqRespMsgTypes(obw, abw, clw)

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheMsg.Req( type_, opaque, addr, len, data )

def resp( type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheMsg.Resp( type_, opaque, test, len, data )

#-------------------------------------------------------------------------
# Test Case: Read Hit 2 way set associative
#-------------------------------------------------------------------------
# Test case designed for direct-mapped cache where a cache line must be evicted
def read_hit( base_addr ):
  return [
    #    type  opq  addr       len data                type  opq  test len data
    req( 'in', 0x0, 0x00000000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'in', 0x1, 0x00001000, 0, 0x00c0ffee ), resp( 'in', 0x1, 0,   0,  0          ),
    req( 'rd', 0x2, 0x00000000, 0, 0          ), resp( 'rd', 0x2, 1,   0,  0xdeadbeef ),
    req( 'rd', 0x3, 0x00001000, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0x00c0ffee ),
  ]
#-------------------------------------------------------------------------
# Test Case: Write Hit 2 way set associative
#-------------------------------------------------------------------------
# Test case designed for direct-mapped cache where a cache line must be evicted
def write_hit( base_addr ):
  return [
    #    type  opq  addr       len data                type  opq  test len data
    req( 'in', 0x0, 0x00000000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'in', 0x1, 0x00001000, 0, 0x00c0ffee ), resp( 'in', 0x1, 0,   0,  0          ),
    req( 'wr', 0x2, 0x00000000, 0, 0x8713450  ), resp( 'wr', 0x2, 1,   0,  0xdeadbeef ),
    req( 'wr', 0x3, 0x00001000, 0, 0xabcde    ), resp( 'wr', 0x3, 1,   0,  0x00c0ffee ),
    req( 'wr', 0x4, 0x00001000, 0, 0          ), resp( 'wr', 0x4, 1,   0,  0x00c0ffee ),
    req( 'rd', 0x5, 0x00000000, 0, 0          ), resp( 'rd', 0x5, 1,   0,  0x8713450  ),
    req( 'rd', 0x6, 0x00001000, 0, 0          ), resp( 'rd', 0x6, 1,   0,  0xabcde    ),
  ]

#-------------------------------------------------------------------------
# Test Case: test set associtivity
#-------------------------------------------------------------------------
# Test cases designed for two-way set-associative cache. We should set
# check_test to False if we use it to test set-associative cache.

def set_assoc_msg0( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    # Write to cacheline 0 way 0
    req( 'wr', 0x00, 0x00000000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ),
    req( 'wr', 0x01, 0x00000004, 0, 0xffffff01), resp( 'wr', 0x01, 1, 0, 0          ),
    req( 'wr', 0x02, 0x00000008, 0, 0xffffff02), resp( 'wr', 0x02, 1, 0, 0          ),
    req( 'wr', 0x03, 0x0000000c, 0, 0xffffff03), resp( 'wr', 0x03, 1, 0, 0          ), # LRU:1
    # Write to cacheline 0 way 1
    req( 'wr', 0x04, 0x00001000, 0, 0xffffff04), resp( 'wr', 0x04, 0, 0, 0          ),
    req( 'wr', 0x05, 0x00001004, 0, 0xffffff05), resp( 'wr', 0x05, 1, 0, 0          ),
    req( 'wr', 0x06, 0x00001008, 0, 0xffffff06), resp( 'wr', 0x06, 1, 0, 0          ),
    req( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), resp( 'wr', 0x07, 1, 0, 0          ), # LRU:0
    # Evict way 0
    req( 'rd', 0x08, 0x00002000, 0, 0         ), resp( 'rd', 0x08, 0, 0, 0x00facade ), # LRU:1
    # Read again from same cacheline to see if cache hit properly
    req( 'rd', 0x09, 0x00002004, 0, 0         ), resp( 'rd', 0x09, 1, 0, 0x05ca1ded ), # LRU:1
    # Read from cacheline 0 way 1 to see if cache hits properly,
    req( 'rd', 0x0a, 0x00001004, 0, 0         ), resp( 'rd', 0x0a, 1, 0, 0xffffff05 ), # LRU:0
    # Write to cacheline 0 way 1 to see if cache hits properly
    req( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), resp( 'wr', 0x0b, 1, 0, 0          ), # LRU:0
    # Read that back
    req( 'rd', 0x0c, 0x0000100c, 0, 0         ), resp( 'rd', 0x0c, 1, 0, 0xffffff09 ), # LRU:0
    # Evict way 0 again
    req( 'rd', 0x0d, 0x00000000, 0, 0         ), resp( 'rd', 0x0d, 0, 0, 0xffffff00 ), # LRU:1
    # Testing cacheline 7 now
    # Write to cacheline 7 way 0
    req( 'wr', 0x10, 0x00000070, 0, 0xffffff00), resp( 'wr', 0x10, 0, 0, 0          ),
    req( 'wr', 0x11, 0x00000074, 0, 0xffffff01), resp( 'wr', 0x11, 1, 0, 0          ),
    req( 'wr', 0x12, 0x00000078, 0, 0xffffff02), resp( 'wr', 0x12, 1, 0, 0          ),
    req( 'wr', 0x13, 0x0000007c, 0, 0xffffff03), resp( 'wr', 0x13, 1, 0, 0          ), # LRU:1
    # Write to cacheline 7 way 1
    req( 'wr', 0x14, 0x00001070, 0, 0xffffff04), resp( 'wr', 0x14, 0, 0, 0          ),
    req( 'wr', 0x15, 0x00001074, 0, 0xffffff05), resp( 'wr', 0x15, 1, 0, 0          ),
    req( 'wr', 0x16, 0x00001078, 0, 0xffffff06), resp( 'wr', 0x16, 1, 0, 0          ),
    req( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), resp( 'wr', 0x17, 1, 0, 0          ), # LRU:0
    # Evict way 0
    req( 'rd', 0x18, 0x00002070, 0, 0         ), resp( 'rd', 0x18, 0, 0, 0x70facade ), # LRU:1
    # Read again from same cacheline to see if cache hits properly
    req( 'rd', 0x19, 0x00002074, 0, 0         ), resp( 'rd', 0x19, 1, 0, 0x75ca1ded ), # LRU:1
    # Read from cacheline 7 way 1 to see if cache hits properly
    req( 'rd', 0x1a, 0x00001074, 0, 0         ), resp( 'rd', 0x1a, 1, 0, 0xffffff05 ), # LRU:0
    # Write to cacheline 7 way 1 to see if cache hits properly
    req( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), resp( 'wr', 0x1b, 1, 0, 0          ), # LRU:0
    # Read that back
    req( 'rd', 0x1c, 0x0000107c, 0, 0         ), resp( 'rd', 0x1c, 1, 0, 0xffffff09 ), # LRU:0
    # Evict way 0 again
    req( 'rd', 0x1d, 0x00000070, 0, 0         ), resp( 'rd', 0x1d, 0, 0, 0xffffff00 ), # LRU:1
  ]
#---------------------------------------------------------------------------------------------
# Test table for direct mapped cache tests
#---------------------------------------------------------------------------------------------

test_case_table_asso_2way = mk_test_case_table([
  ( "                        msg_func               mem_data_func        stall lat src sink"),
  [ "read_hit",              read_hit,              None,                0.0,  1,  0,  0    ],
  [ "write_hit",             write_hit,             None,                0.0,  1,  0,  0    ],
  [ "set_assoc_msg0",        set_assoc_msg0,        None,                0.0,  1,  0,  0    ],
  ])
