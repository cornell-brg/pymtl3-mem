"""
=========================================================================
AssoTestCases.py
=========================================================================
2 way set associative cache test cases

Author : Xiaoyu Yan, Eric Tang
Date   : 16 November 2019
"""

import pytest

from test.sim_utils import (
  req, resp, CacheReqType, CacheRespType, MemReqType, MemRespType
)

# Main test memory for asso tests
def asso_mem():
  return [
    0x00000000, 0,
    0x00000004, 1,
    0x00000008, 2,
    0x0000000c, 3,
    0x00000010, 4,
    0x00000014, 5,
    0x00000018, 6,
    0x0000001c, 7,
    0x00000020, 8,
    0x00000024, 9,
    0x00000028, 0xa,
    0x0000002c, 0xb,
    0x00020000, 0xc,
    0x00020004, 0xd,
    0x00020008, 0xe,
    0x0002000c, 0xf,
    0x00020010, 0x10,
    0x00020014, 0x11,
    0x00001000, 0x01020304,
    0x00001004, 0x05060708,
    0x00001008, 0x090a0b0c,
    0x0000100c, 0x0d0e0f10,
    0x00002000, 0x00facade,
    0x00002004, 0x05ca1ded,
    0x00002070, 0x70facade,
    0x00002074, 0x75ca1ded,
  ]

def rd_hit_1s():
  return [
    #    type  opq  addr       len data                type  opq  test len data
    req( 'in', 0x0, 0x00000000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x3, 0x00000000, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0xdeadbeef ),
  ]

def wr_hit_1s():
  return [
    #    type  opq  addr       len data           type  opq  test len data
    req( 'in', 0x0, 0x00002070, 0, 200 ),   resp( 'in', 0x0, 0,   0,  0          ),
    req( 'wr', 0x1, 0x00002070, 0, 78787 ), resp( 'wr', 0x1, 1,   0,  0          ),
    req( 'rd', 0x2, 0x00002070, 0, 0 ),     resp( 'rd', 0x2, 1,   0,  78787   ),
  ]

#-------------------------------------------------------------------------
# Test Case: Read Miss 2 way set associative but with 1 way
#-------------------------------------------------------------------------

def rd_miss_1s():
  return [
    req( 'rd', 0x0, 0x00000004, 0, 0 ), resp( 'rd', 0x0, 0,   0,  1          ),
  ]

def wr_miss_1s():
  return [
    #    type  opq  addr       len data           type  opq  test len data         ),
    req( 'wr', 0x1, 0x00002070, 0, 78787 ), resp( 'wr', 0x1, 0,   0,  0          ),
    req( 'rd', 0x2, 0x00002070, 0, 0 ),     resp( 'rd', 0x2, 1,   0,  78787   ),
  ]

#-------------------------------------------------------------------------
# Test Case: Read Hit 2 way set associative
#-------------------------------------------------------------------------
# Test case designed for direct-mapped cache where a cache line must be evicted

def rd_hit_2s():
  return [
    #    type  opq  addr       len  data                type  opq  test len data
    req( 'in', 0x0, 0x00000000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'wr', 0x2, 0x00002000, 0, 212        ), resp( 'wr', 0x2, 0,   0,  0 ),
    req( 'rd', 0x2, 0x00000000, 0, 0          ), resp( 'rd', 0x2, 1,   0,  0xdeadbeef ),
    req( 'rd', 0x3, 0x00002000, 0, 0          ), resp( 'rd', 0x3, 1,   0,  212 ),
  ]

#-------------------------------------------------------------------------
# Test Case: Write Hit 2 way set associative
#-------------------------------------------------------------------------

def wr_hit_2s():
  return [
    #    type  opq  addr       len data                type  opq  test len data
    req( 'in', 0x1, 0x00000000, 0, 44159     ),  resp( 'in', 0x1, 0,   0,  0          ),
    req( 'wr', 0x2, 0x00000000, 0, 0x8713450  ), resp( 'wr', 0x2, 1,   0,  0          ),
    req( 'rd', 0x4, 0x00000000, 0, 0          ), resp( 'rd', 0x4, 1,   0,  0x8713450  ),
    req( 'wr', 0x3, 0x00001000, 0, 0xabcde    ), resp( 'wr', 0x3, 0,   0,  0          ),
    req( 'rd', 0x5, 0x00001000, 0, 0          ), resp( 'rd', 0x5, 1,   0,  0xabcde    ),
    req( 'rd', 0x5, 0x00000000, 0, 0          ), resp( 'rd', 0x5, 1,   0,  0x8713450  ),
  ]

#-------------------------------------------------------------------------
# Test Case: Write Miss 2 way set associative
#-------------------------------------------------------------------------
# Test case designed for direct-mapped cache where a cache line must be evicted

def wr_miss_2s():
  return [
    #    type  opq  addr       len data                type  opq  test len data
    req( 'wr', 0x2, 0x00000000, 0, 0x8713450  ), resp( 'wr', 0x2, 0,   0,  0          ),
    req( 'wr', 0x3, 0x00001000, 0, 0xabcde    ), resp( 'wr', 0x3, 0,   0,  0          ),
    req( 'rd', 0x4, 0x00000000, 0, 0          ), resp( 'rd', 0x4, 1,   0,  0x8713450  ),
    req( 'rd', 0x5, 0x00001000, 0, 0          ), resp( 'rd', 0x5, 1,   0,  0xabcde    ),
  ]

#-------------------------------------------------------------------------
# Test Case: Eviction Tests
#-------------------------------------------------------------------------

def evict():
  return [
    #    type  opq  addr       len data              type  opq  test len data         ),
    req( 'wr', 0x2, 0x00000000, 0, 78787    ), resp( 'wr', 0x2, 0,   0,  0          ),
    req( 'wr', 0x3, 0x00020000, 0, 0xc0ffee ), resp( 'wr', 0x3, 0,   0,  0          ),
    req( 'rd', 0x4, 0x00001000, 0, 0        ), resp( 'rd', 0x4, 0,   0,  0x01020304 ),
    req( 'rd', 0x5, 0x00020000, 0, 0        ), resp( 'rd', 0x5, 1,   0,  0xc0ffee   ),
    req( 'rd', 0x6, 0x00000000, 0, 0        ), resp( 'rd', 0x6, 0,   0,  78787   ),
  ]

#-------------------------------------------------------------------------
# Test Case: test set associtivity
#-------------------------------------------------------------------------
# Test cases designed for two-way set-associative cache. We should set
# check_test to False if we use it to test set-associative cache.

def long_msg():
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    # Write to cacheline 0 way 0
    req( 'wr', 0x00, 0x000a0000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ),
    req( 'wr', 0x01, 0x000a0004, 0, 0xffffff01), resp( 'wr', 0x01, 1, 0, 0          ),
    req( 'wr', 0x02, 0x000a0008, 0, 0xffffff02), resp( 'wr', 0x02, 1, 0, 0          ),
    req( 'wr', 0x03, 0x000a000c, 0, 0xffffff03), resp( 'wr', 0x03, 1, 0, 0          ), # LRU:1
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
    req( 'rd', 0x0d, 0x000a0000, 0, 0         ), resp( 'rd', 0x0d, 0, 0, 0xffffff00 ), # LRU:1
    # Testing cacheline 7 now
    # Write to cacheline 7 way 0
    req( 'wr', 0x10, 0x000a0070, 0, 0xffffff00), resp( 'wr', 0x10, 0, 0, 0          ),
    req( 'wr', 0x11, 0x000a0074, 0, 0xffffff01), resp( 'wr', 0x11, 1, 0, 0          ),
    req( 'wr', 0x12, 0x000a0078, 0, 0xffffff02), resp( 'wr', 0x12, 1, 0, 0          ),
    req( 'wr', 0x13, 0x000a007c, 0, 0xffffff03), resp( 'wr', 0x13, 1, 0, 0          ), # LRU:1
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
    req( 'rd', 0x1d, 0x000a0070, 0, 0         ), resp( 'rd', 0x1d, 0, 0, 0xffffff00 ), # LRU:1
  ]

class AssoTestCases:

  @pytest.mark.parametrize(
    " name,  test,          stall_prob,latency,src_delay,sink_delay", [
    ("Hit",  rd_hit_1s,     0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_1s,     0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_2s,     0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_2s,     0.0,       1,      0,        0   ),
    ("Miss", rd_miss_1s,    0.0,       1,      0,        0   ),
    ("Miss", wr_miss_1s,    0.0,       1,      0,        0   ),
    ("Miss", wr_miss_2s,    0.0,       1,      0,        0   ),
    ("Miss", evict,         0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_1s,     0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_1s,     0.5,       2,      2,        2   ),
    ("Hit",  rd_hit_2s,     0.5,       2,      2,        2   ),
    ("Hit",  wr_hit_2s,     0.5,       2,      2,        2   ),
    ("Miss", rd_miss_1s,    0.5,       2,      2,        2   ),
    ("Miss", wr_miss_1s,    0.5,       2,      2,        2   ),
    ("Miss", wr_miss_2s,    0.5,       2,      2,        2   ),
    ("Miss", evict,         0.5,       2,      2,        2   ),
  ])
  def test_2way_size64_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                               stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = asso_mem()
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                64, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles, dump_vtb )

  @pytest.mark.parametrize(
    " name,  test,          stall_prob,latency,src_delay,sink_delay", [
    ("Gen",  long_msg,      0.0,       1,      0,        0   ),
    ("Gen",  long_msg,      0.5,       2,      2,        2   ),
    ("Hit",  rd_hit_1s,     0.0,       1,      0,        0   ),
  ])
  def test_2way_size4096_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                 stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    mem = asso_mem()
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                4096, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles, dump_vtb )
