"""
=========================================================================
 GeneralTestCases.py
=========================================================================
Test Cases that verifies read/write/init transactions

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 11 November 2019
"""
import pytest
from test.sim_utils import SingleCacheTestParams

# Main test memory for dmapped tests
gen_mem = [
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

#-------------------------------------------------------------------------
# Test Case: test direct-mapped
#-------------------------------------------------------------------------
# Test cases designed for direct-mapped cache

def rd_hit_1wd():
  msg = [
      #    type  opq  addr     len data                type  opq  test len data
    ( 'in', 0x0, 0x000ab000, 0, 0xdeadbeef ), ( 'in', 0x0, 0,   0, 0          ),
    ( 'rd', 0x1, 0x000ab000, 0, 0          ), ( 'rd', 0x1, 1,   0, 0xdeadbeef ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def rd_hit_many():
  msg = []
  for i in range(4):
    #                  type  opq  addr          len data
    msg.append((  'in', i, ((0x00012000)<<2)+i*4, 0, i ))
    msg.append(( 'in', i, 0,             0, 0 ))
  for i in range(4):
    msg.append((  'rd', i, ((0x00012000)<<2)+i*4, 0, 0 ))
    msg.append(( 'rd', i, 1,             0, i ))
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#----------------------------------------------------------------------
# Test Case: Read Hits: Test for entire line hits
#----------------------------------------------------------------------

def rd_hit_cline():
  base_addr = 0x20
  msg = [
    ( 'in', 0x0, base_addr,    0, 0xdeadbeef ), ( 'in', 0x0, 0, 0, 0          ),
    ( 'in', 0x1, base_addr+4,  0, 0xcafecafe ), ( 'in', 0x1, 0, 0, 0          ),
    ( 'in', 0x2, base_addr+8,  0, 0xfafafafa ), ( 'in', 0x2, 0, 0, 0          ),
    ( 'in', 0x3, base_addr+12, 0, 0xbabababa ), ( 'in', 0x3, 0, 0, 0          ),
    ( 'rd', 0x4, base_addr,    0, 0          ), ( 'rd', 0x4, 1, 0, 0xdeadbeef ),
    ( 'rd', 0x5, base_addr+4,  0, 0          ), ( 'rd', 0x5, 1, 0, 0xcafecafe ),
    ( 'rd', 0x6, base_addr+8,  0, 0          ), ( 'rd', 0x6, 1, 0, 0xfafafafa ),
    ( 'rd', 0x7, base_addr+12, 0, 0          ), ( 'rd', 0x7, 1, 0, 0xbabababa ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#----------------------------------------------------------------------
# Test Case: Write Hit: CLEAN
#----------------------------------------------------------------------

def wr_hit_clean():
  msg = [
    #    type  opq  addr      len data                type  opq  test len data
    ( 'in', 0x0, 0x1180,    0, 0xdeadbeef ), ( 'in', 0x0, 0,   0,  0  ),
    ( 'wr', 0x1, 0x1180,    0, 50         ), ( 'wr', 0x1, 1,   0,  0  ),
    ( 'wr', 0x1, 0x1184,    0, 51         ), ( 'wr', 0x1, 1,   0,  0  ),
    ( 'wr', 0x1, 0x1188,    0, 52         ), ( 'wr', 0x1, 1,   0,  0  ),
    ( 'wr', 0x1, 0x118c,    0, 53         ), ( 'wr', 0x1, 1,   0,  0  ),
    ( 'rd', 0x2, 0x1180,    0, 0          ), ( 'rd', 0x2, 1,   0,  50 ),
    ( 'rd', 0x2, 0x1184,    0, 0          ), ( 'rd', 0x2, 1,   0,  51 ),
    ( 'rd', 0x2, 0x1188,    0, 0          ), ( 'rd', 0x2, 1,   0,  52 ),
    ( 'rd', 0x2, 0x118c,    0, 0          ), ( 'rd', 0x2, 1,   0,  53 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#----------------------------------------------------------------------
# Test Case: Write Hit: DIRTY
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def wr_hit_dirty():
  msg = [
    #    type  opq  addr      len data                type  opq  test len data
    ( 'in', 0x0, 0x66660,   0, 0xdeadbeef ), ( 'in', 0x0, 0,   0,  0          ),
    ( 'wr', 0x1, 0x66660,   0, 0xffffffff ), ( 'wr', 0x1, 1,   0,  0          ),
    ( 'wr', 0x2, 0x66664,   0, 0xc0ef     ), ( 'wr', 0x2, 1,   0,  0 ),
    ( 'wr', 0x3, 0x66668,   0, 0x39287    ), ( 'wr', 0x3, 1,   0,  0 ),
    ( 'wr', 0x4, 0x6666c,   0, 0xabcef    ), ( 'wr', 0x4, 1,   0,  0 ),
    ( 'rd', 0x5, 0x66668,   0, 0          ), ( 'rd', 0x5, 1,   0,  0x39287 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#----------------------------------------------------------------------
# Test Case: Write Hit: read/write hit
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def wr_hit_rd_hit():
  msg = [
  #   type  opq  addr len data         type  opq  test len data
    ( 'in', 0x0, 0, 0, 0xdeadbeef ), ( 'in', 0x0, 0,   0,  0          ),
    ( 'rd', 0x1, 0, 0, 0          ), ( 'rd', 0x1, 1,   0,  0xdeadbeef ),
    ( 'wr', 0x2, 0, 0, 0xffffffff ), ( 'wr', 0x2, 1,   0,  0          ),
    ( 'rd', 0x3, 0, 0, 0          ), ( 'rd', 0x3, 1,   0,  0xffffffff ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#----------------------------------------------------------------------
# Test Case: Read Miss Clean:
#----------------------------------------------------------------------

def rd_miss_1wd_cn():
  msg = [
    # type  opq  addr       len data            type  opq  test len data
    ( 'rd', 0x0, 0x00000000, 0, 0          ), ( 'rd', 0x0, 0,   0,  0 ),
    ( 'rd', 0x1, 0x00000004, 0, 0          ), ( 'rd', 0x1, 1,   0,  1 )
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#----------------------------------------------------------------------
# Test Case: Write Miss Clean:
#----------------------------------------------------------------------

def wr_miss_1wd_cn():
  msg = [
    # type  opq  addr       len data            type  opq test len data
    ( 'wr', 0x0, 0x00000000, 0, 0x00c0ffee ), ( 'wr', 0x0, 0,   0, 0          ),
    ( 'rd', 0x1, 0x00000000, 0, 0          ), ( 'rd', 0x1, 1,   0, 0x00c0ffee ),
    ( 'rd', 0x2, 0x00000008, 0, 0          ), ( 'rd', 0x2, 1,   0, 2 )
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#-------------------------------------------------------------------------
# Test cases: Write Dirty:
#-------------------------------------------------------------------------

def rd_miss_dty():
  msg = [
    # type  opq   addr        len data          type  opq   test len data
    ( 'wr', 0x0, 0x00000000,  0, 0xbeefbeeb ), ('wr', 0x0,   0,   0, 0          ),
    ( 'rd', 0x1, 0x00020000,  0, 0          ), ('rd', 0x1,   0,   0, 0xc ),
    ( 'rd', 0x2, 0x00000000,  0, 0          ), ('rd', 0x2,   0,   0, 0xbeefbeeb )
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

#-------------------------------------------------------------------------
# Test Case: Direct Mapped Read Evict
#-------------------------------------------------------------------------

def rd_ev_1wd():
  msg = [
    #  type  opq   addr      len  data           type  opq test len  data
    ( 'wr', 0x00, 0x00002000, 0, 0xffffff00), ( 'wr', 0x00, 0, 0, 0          ), # write something
    ( 'rd', 0x01, 0x00000000, 0, 0         ), ( 'rd', 0x01, 0, 0, 0 ), # read miss on dirty line
    ( 'rd', 0x02, 0x00002000, 0, 0         ), ( 'rd', 0x02, 0, 0, 0xffffff00 ), # read evicted address
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )


def long_msg_1way():
  msg = [
     # type  opq   addr      len  data           type  opq test len  data
      ( 'wr', 0x00, 0x00000000, 0, 0xffffff00), ( 'wr', 0x00, 0, 0, 0          ), # Write to cacheline 0
      ( 'wr', 0x01, 0x00000004, 0, 0xffffff01), ( 'wr', 0x01, 1, 0, 0          ),
      ( 'wr', 0x02, 0x00000008, 0, 0xffffff02), ( 'wr', 0x02, 1, 0, 0          ),
      ( 'wr', 0x03, 0x0000000c, 0, 0xffffff03), ( 'wr', 0x03, 1, 0, 0          ),
      ( 'wr', 0x04, 0x00001000, 0, 0xffffff04), ( 'wr', 0x04, 0, 0, 0          ), # Write to cacheline 0
      ( 'wr', 0x05, 0x00001004, 0, 0xffffff05), ( 'wr', 0x05, 1, 0, 0          ),
      ( 'wr', 0x06, 0x00001008, 0, 0xffffff06), ( 'wr', 0x06, 1, 0, 0          ),
      ( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), ( 'wr', 0x07, 1, 0, 0          ),
      ( 'rd', 0x08, 0x00002000, 0, 0         ), ( 'rd', 0x08, 0, 0, 0x00facade ), # Evict cache 0
      ( 'rd', 0x09, 0x00002004, 0, 0         ), ( 'rd', 0x09, 1, 0, 0x05ca1ded ), # Read again from same cacheline
      ( 'rd', 0x0a, 0x00001004, 0, 0         ), ( 'rd', 0x0a, 0, 0, 0xffffff05 ), # Read from cacheline 0
      ( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), ( 'wr', 0x0b, 1, 0, 0          ), # Write to cacheline 0
      ( 'rd', 0x0c, 0x0000100c, 0, 0         ), ( 'rd', 0x0c, 1, 0, 0xffffff09 ), # Read that back
      ( 'rd', 0x0d, 0x00000000, 0, 0         ), ( 'rd', 0x0d, 0, 0, 0xffffff00 ), # Evict cacheline 0
      ( 'wr', 0x10, 0x00000070, 0, 0xffffff00), ( 'wr', 0x10, 0, 0, 0          ), # Write to cacheline 7
      ( 'wr', 0x11, 0x00000074, 0, 0xffffff01), ( 'wr', 0x11, 1, 0, 0          ),
      ( 'wr', 0x12, 0x00000078, 0, 0xffffff02), ( 'wr', 0x12, 1, 0, 0          ),
      ( 'wr', 0x13, 0x0000007c, 0, 0xffffff03), ( 'wr', 0x13, 1, 0, 0          ),
      ( 'wr', 0x14, 0x00001070, 0, 0xffffff04), ( 'wr', 0x14, 0, 0, 0          ), # Write to cacheline 7
      ( 'wr', 0x15, 0x00001074, 0, 0xffffff05), ( 'wr', 0x15, 1, 0, 0          ),
      ( 'wr', 0x16, 0x00001078, 0, 0xffffff06), ( 'wr', 0x16, 1, 0, 0          ),
      ( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), ( 'wr', 0x17, 1, 0, 0          ),
      ( 'rd', 0x18, 0x00002070, 0, 0         ), ( 'rd', 0x18, 0, 0, 0x70facade ), # Evict cacheline 7
      ( 'rd', 0x19, 0x00002074, 0, 0         ), ( 'rd', 0x19, 1, 0, 0x75ca1ded ), # Read again from same cacheline
      ( 'rd', 0x1a, 0x00001074, 0, 0         ), ( 'rd', 0x1a, 0, 0, 0xffffff05 ), # Read from cacheline 7
      ( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), ( 'wr', 0x1b, 1, 0, 0          ), # Write to cacheline 7
      ( 'rd', 0x1c, 0x0000107c, 0, 0         ), ( 'rd', 0x1c, 1, 0, 0xffffff09 ), # Read that back
      ( 'rd', 0x1d, 0x00000070, 0, 0         ), ( 'rd', 0x1d, 0, 0, 0xffffff00 ), # Evict cacheline 0 again
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=4096 )

def rd_hit_1b():
  msg = [
    #  type  opq   addr      len  data          type  opq test len  data
    ( 'in', 0x00, 0x00000000, 0, 0xabcdef12), ( 'in', 0x00, 0, 0, 0 ),
    ( 'rd', 0x01, 0x00000000, 1, 0),          ( 'rd', 0x01, 1, 1, 0x00000012          ),
    ( 'rd', 0x02, 0x00000001, 1, 0),          ( 'rd', 0x02, 1, 1, 0x000000ef          ),
    ( 'rd', 0x03, 0x00000002, 1, 0),          ( 'rd', 0x03, 1, 1, 0x000000cd          ),
    ( 'rd', 0x04, 0x00000003, 1, 0),          ( 'rd', 0x04, 1, 1, 0x000000ab          ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def wr_hit_1b():
  msg = [
    #  type  opq   addr      len  data         type  opq test len  data
    ( 'in', 0x00, 0x00000000, 0, 0xabcdef12), ( 'in', 0x00, 0, 0, 0          ),
    ( 'wr', 0x01, 0x00000000, 1, 0x99),       ( 'wr', 0x01, 1, 1, 0          ),
    ( 'wr', 0x01, 0x00000001, 1, 0x66),       ( 'wr', 0x01, 1, 1, 0          ),
    ( 'wr', 0x01, 0x00000002, 1, 0x33),       ( 'wr', 0x01, 1, 1, 0          ),
    ( 'wr', 0x01, 0x00000003, 1, 0x11),       ( 'wr', 0x01, 1, 1, 0          ),
    ( 'rd', 0x02, 0x00000000, 0, 0),          ( 'rd', 0x02, 1, 0, 0x11336699 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def rd_miss_1b():
  msg = [
    # type  opq   addr      len  data      type  opq test len  data    ),
    ( 'rd', 0x00, 0x00001000, 1, 0), ( 'rd', 0x00, 0, 1, 0x04 ),
    ( 'rd', 0x01, 0x00001001, 1, 0), ( 'rd', 0x01, 1, 1, 0x03 ),
    ( 'rd', 0x02, 0x00001002, 1, 0), ( 'rd', 0x02, 1, 1, 0x02 ),
    ( 'rd', 0x03, 0x00001003, 1, 0), ( 'rd', 0x03, 1, 1, 0x01 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def wr_miss_1b():
  msg = [
    #  type  opq   addr      len  data     type  opq test len  data
    ( 'wr', 0x00, 0x00001001, 1, 0x11), ( 'wr', 0x00, 0, 1, 0          ),
    ( 'wr', 0x01, 0x00001005, 1, 0x22), ( 'wr', 0x01, 1, 1, 0          ),
    ( 'wr', 0x02, 0x00001009, 1, 0x33), ( 'wr', 0x02, 1, 1, 0 ),
    ( 'wr', 0x03, 0x0000100d, 1, 0x44), ( 'wr', 0x03, 1, 1, 0 ),
    ( 'rd', 0x00, 0x00001000, 0, 0),    ( 'rd', 0x00, 1, 0, 0x01021104 ),
    ( 'rd', 0x01, 0x00001004, 0, 0),    ( 'rd', 0x01, 1, 0, 0x05062208 ),
    ( 'rd', 0x02, 0x00001008, 0, 0),    ( 'rd', 0x02, 1, 0, 0x090a330c ),
    ( 'rd', 0x03, 0x0000100c, 0, 0),    ( 'rd', 0x03, 1, 0, 0x0d0e4410 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def rd_hit_2b():
  msg = [
  #    type  opq   addr      len  data           type  opq test len  data
    ( 'in', 0x00, 0x00000000, 0, 0xabcdef12), ( 'in', 0x00, 0, 0, 0          ),
    ( 'rd', 0x01, 0x00000000, 2, 0),          ( 'rd', 0x01, 1, 2, 0x0000ef12 ),
    ( 'rd', 0x02, 0x00000002, 2, 0),          ( 'rd', 0x02, 1, 2, 0x0000abcd ),
    ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def wr_hit_2b():
  msg = [
    #  type  opq   addr      len  data           type  opq test len  data
    ( 'in', 0x00, 0x00000000, 0, 0xabcdef12), ( 'in', 0x00, 0, 0, 0          ),
    ( 'wr', 0x01, 0x00000000, 2, 0x99),       ( 'wr', 0x01, 1, 2, 0          ),
    ( 'wr', 0x01, 0x00000002, 2, 0xac13),     ( 'wr', 0x01, 1, 2, 0          ),
    ( 'rd', 0x02, 0x00000000, 0, 0),          ( 'rd', 0x02, 1, 0, 0xac130099 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def rd_miss_2b():
  msg = [
  #    type  opq   addr      len  data      type  opq test len  data    ),
    ( 'rd', 0x00, 0x00001000, 2, 0), ( 'rd', 0x00, 0, 2, 0x0304 ),
    ( 'rd', 0x02, 0x00002002, 2, 0), ( 'rd', 0x02, 0, 2, 0x00fa ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def wr_miss_2b():
  msg = [
#    type  opq   addr      len  data    type  opq test len  data
    ('wr', 0x00, 0x00001000, 2, 0x11), ( 'wr', 0x00, 0, 2, 0          ),
    ('wr', 0x02, 0x00002002, 2, 0x33), ( 'wr', 0x02, 0, 2, 0 ),
    ('rd', 0x00, 0x00001000, 0, 0),    ( 'rd', 0x00, 0, 0, 0x01020011 ),
    ('rd', 0x02, 0x00002000, 0, 0),    ( 'rd', 0x02, 0, 0, 0x0033cade ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def rd_data128_line128():
  msg = [
    # type  opq addr        len data   type  opq test len  data
    ( 'rd', 0,  0x00001000, 0,  0 ), ( 'rd', 0,  0,   0,   0x0d0e0f10090a0b0c0506070801020304 ),
    # ( 'rd', 1,  0x00001004, 0,  0),  ( 'rd', 1,  1,   0,   0x0d0e0f10090a0b0c0506070801020304 ), # Not aligned
    ( 'rd', 2,  0x00001000, 1,  0),  ( 'rd', 2,  1,   1,   0x04 ),
    ( 'rd', 3,  0x00001001, 1,  0),  ( 'rd', 3,  1,   1,   0x03 ),
    ( 'rd', 4,  0x00001000, 2,  0),  ( 'rd', 4,  1,   2,   0x0304 ),
    ( 'rd', 5,  0x00001002, 2,  0),  ( 'rd', 5,  1,   2,   0x0102 ),
    ( 'rd', 6,  0x00001000, 4,  0),  ( 'rd', 6,  1,   4,   0x01020304 ),
    ( 'rd', 7,  0x00001008, 4,  0),  ( 'rd', 7,  1,   4,   0x090a0b0c ),
    ( 'rd', 8,  0x00001000, 8,  0),  ( 'rd', 8,  1,   8,   0x0506070801020304 ),
    ( 'rd', 9,  0x00001008, 8,  0),  ( 'rd', 9,  1,   8,   0x0d0e0f10090a0b0c ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=128 )

def wr_data128_line128():
  msg = [
    # type  opq addr        len data                                   type  opq test len  data
    ( 'wr', 0,  0x00001000, 0,  0x0123456789abcdeffedcba9876543210), ( 'wr', 0,  0,   0,   0 ),
    ( 'rd', 1,  0x00001000, 0,  0),                                  ( 'rd', 1,  1,   0,   0x0123456789abcdeffedcba9876543210 ),
    ( 'wr', 2,  0x00001000, 1,  0xff),                               ( 'wr', 2,  1,   1,   0 ),
    ( 'rd', 3,  0x00001000, 0,  0),                                  ( 'rd', 3,  1,   0,   0x0123456789abcdeffedcba98765432ff ),
    ( 'wr', 4,  0x00001002, 2,  0xff),                               ( 'wr', 4,  1,   2,   0 ),
    ( 'rd', 5,  0x00001000, 0,  0x00),                               ( 'rd', 5,  1,   0,   0x0123456789abcdeffedcba9800ff32ff ),
    ( 'wr', 6,  0x0000100c, 4,  0xff),                               ( 'wr', 6,  1,   4,   0 ),
    ( 'rd', 7,  0x00001000, 0,  0x00),                               ( 'rd', 7,  1,   0,   0x000000ff89abcdeffedcba9800ff32ff ),
    ( 'wr', 8,  0x00001000, 8,  0xff),                               ( 'wr', 8,  1,   8,   0 ),
    ( 'rd', 9,  0x00001000, 0,  0x00),                               ( 'rd', 9,  1,   0,   0x000000ff89abcdef00000000000000ff ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=128)

def rd_data32_line64():
  msg = [
    # type  opq addr        len data   type  opq test len  data
    ( 'rd', 0,  0x00001000, 0,  0),  ( 'rd', 0,  0,   0,   0x01020304 ),
    ( 'rd', 1,  0x00001004, 0,  0),  ( 'rd', 1,  1,   0,   0x05060708 ),
    ( 'rd', 2,  0x00001008, 0,  0),  ( 'rd', 2,  0,   0,   0x090a0b0c ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

#-------------------------------------------------------------------------
# 2-way associative test cases
#-------------------------------------------------------------------------

def rd_hit_1s():
  msg =  [
    #    type  opq  addr       len data                type  opq  test len data
    ( 'in', 0x0, 0x00000000, 0, 0xdeadbeef ), ( 'in', 0x0, 0,   0,  0          ),
    ( 'rd', 0x3, 0x00000000, 0, 0          ), ( 'rd', 0x3, 1,   0,  0xdeadbeef ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def wr_hit_1s():
  msg =  [
    #    type  opq  addr       len data           type  opq  test len data
    ( 'in', 0x0, 0x00002070, 0, 200 ),   ( 'in', 0x0, 0,   0,  0          ),
    ( 'wr', 0x1, 0x00002070, 0, 78787 ), ( 'wr', 0x1, 1,   0,  0          ),
    ( 'rd', 0x2, 0x00002070, 0, 0 ),     ( 'rd', 0x2, 1,   0,  78787   ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def wr_miss_1s():
  msg =  [
    #    type  opq  addr       len data           type  opq  test len data      
    ( 'wr', 0x1, 0x00002070, 0, 78787 ), ( 'wr', 0x1, 0,   0,  0          ),
    ( 'rd', 0x2, 0x00002070, 0, 0 ),     ( 'rd', 0x2, 1,   0,  78787   ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def rd_hit_2s():
  msg =  [
    #    type  opq  addr       len  data                type  opq  test len data
    ( 'in', 0x0, 0x00000000, 0, 0xdeadbeef ), ( 'in', 0x0, 0,   0,  0          ),
    ( 'wr', 0x2, 0x00002000, 0, 212        ), ( 'wr', 0x2, 0,   0,  0 ),
    ( 'rd', 0x2, 0x00000000, 0, 0          ), ( 'rd', 0x2, 1,   0,  0xdeadbeef ),
    ( 'rd', 0x3, 0x00002000, 0, 0          ), ( 'rd', 0x3, 1,   0,  212 ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def wr_hit_2s():
  msg =  [
    #    type  opq  addr       len data                type  opq  test len data
    ( 'in', 0x1, 0x00000000, 0, 44159     ),  ( 'in', 0x1, 0,   0,  0          ),
    ( 'wr', 0x2, 0x00000000, 0, 0x8713450  ), ( 'wr', 0x2, 1,   0,  0          ),
    ( 'rd', 0x4, 0x00000000, 0, 0          ), ( 'rd', 0x4, 1,   0,  0x8713450  ),
    ( 'wr', 0x3, 0x00001000, 0, 0xabcde    ), ( 'wr', 0x3, 0,   0,  0          ),
    ( 'rd', 0x5, 0x00001000, 0, 0          ), ( 'rd', 0x5, 1,   0,  0xabcde    ),
    ( 'rd', 0x5, 0x00000000, 0, 0          ), ( 'rd', 0x5, 1,   0,  0x8713450  ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def wr_miss_2s():
  msg =  [
    #    type  opq  addr       len data                type  opq  test len data
    ( 'wr', 0x2, 0x00000000, 0, 0x8713450  ), ( 'wr', 0x2, 0,   0,  0          ),
    ( 'wr', 0x3, 0x00001000, 0, 0xabcde    ), ( 'wr', 0x3, 0,   0,  0          ),
    ( 'rd', 0x4, 0x00000000, 0, 0          ), ( 'rd', 0x4, 1,   0,  0x8713450  ),
    ( 'rd', 0x5, 0x00001000, 0, 0          ), ( 'rd', 0x5, 1,   0,  0xabcde    ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def ev_2way():
  msg =  [
    #    type  opq  addr       len data              type  opq  test len data         ),
    ( 'wr', 0x2, 0x00000000, 0, 78787    ), ( 'wr', 0x2, 0,   0,  0          ),
    ( 'wr', 0x3, 0x00020000, 0, 0xc0ffee ), ( 'wr', 0x3, 0,   0,  0          ),
    ( 'rd', 0x4, 0x00001000, 0, 0        ), ( 'rd', 0x4, 0,   0,  0x01020304 ),
    ( 'rd', 0x5, 0x00020000, 0, 0        ), ( 'rd', 0x5, 1,   0,  0xc0ffee   ),
    ( 'rd', 0x6, 0x00000000, 0, 0        ), ( 'rd', 0x6, 0,   0,  78787   ),
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def long_msg_2way():
  msg =  [
    #    type  opq   addr      len  data               type  opq test len  data
    # Write to cacheline 0 way 0
    ( 'wr', 0x00, 0x000a0000, 0, 0xffffff00), ( 'wr', 0x00, 0, 0, 0          ),
    ( 'wr', 0x01, 0x000a0004, 0, 0xffffff01), ( 'wr', 0x01, 1, 0, 0          ),
    ( 'wr', 0x02, 0x000a0008, 0, 0xffffff02), ( 'wr', 0x02, 1, 0, 0          ),
    ( 'wr', 0x03, 0x000a000c, 0, 0xffffff03), ( 'wr', 0x03, 1, 0, 0          ), # LRU:1
    # Write to cacheline 0 way 1
    ( 'wr', 0x04, 0x00001000, 0, 0xffffff04), ( 'wr', 0x04, 0, 0, 0          ),
    ( 'wr', 0x05, 0x00001004, 0, 0xffffff05), ( 'wr', 0x05, 1, 0, 0          ),
    ( 'wr', 0x06, 0x00001008, 0, 0xffffff06), ( 'wr', 0x06, 1, 0, 0          ),
    ( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), ( 'wr', 0x07, 1, 0, 0          ), # LRU:0
    # Evict way 0
    ( 'rd', 0x08, 0x00002000, 0, 0         ), ( 'rd', 0x08, 0, 0, 0x00facade ), # LRU:1
    # Read again from same cacheline to see if cache hit properly
    ( 'rd', 0x09, 0x00002004, 0, 0         ), ( 'rd', 0x09, 1, 0, 0x05ca1ded ), # LRU:1
    # Read from cacheline 0 way 1 to see if cache hits properly,
    ( 'rd', 0x0a, 0x00001004, 0, 0         ), ( 'rd', 0x0a, 1, 0, 0xffffff05 ), # LRU:0
    # Write to cacheline 0 way 1 to see if cache hits properly
    ( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), ( 'wr', 0x0b, 1, 0, 0          ), # LRU:0
    # Read that back
    ( 'rd', 0x0c, 0x0000100c, 0, 0         ), ( 'rd', 0x0c, 1, 0, 0xffffff09 ), # LRU:0
    # Evict way 0 again
    ( 'rd', 0x0d, 0x000a0000, 0, 0         ), ( 'rd', 0x0d, 0, 0, 0xffffff00 ), # LRU:1
    # Testing cacheline 7 now
    # Write to cacheline 7 way 0
    ( 'wr', 0x10, 0x000a0070, 0, 0xffffff00), ( 'wr', 0x10, 0, 0, 0          ),
    ( 'wr', 0x11, 0x000a0074, 0, 0xffffff01), ( 'wr', 0x11, 1, 0, 0          ),
    ( 'wr', 0x12, 0x000a0078, 0, 0xffffff02), ( 'wr', 0x12, 1, 0, 0          ),
    ( 'wr', 0x13, 0x000a007c, 0, 0xffffff03), ( 'wr', 0x13, 1, 0, 0          ), # LRU:1
    # Write to cacheline 7 way 1
    ( 'wr', 0x14, 0x00001070, 0, 0xffffff04), ( 'wr', 0x14, 0, 0, 0          ),
    ( 'wr', 0x15, 0x00001074, 0, 0xffffff05), ( 'wr', 0x15, 1, 0, 0          ),
    ( 'wr', 0x16, 0x00001078, 0, 0xffffff06), ( 'wr', 0x16, 1, 0, 0          ),
    ( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), ( 'wr', 0x17, 1, 0, 0          ), # LRU:0
    # Evict way 0
    ( 'rd', 0x18, 0x00002070, 0, 0         ), ( 'rd', 0x18, 0, 0, 0x70facade ), # LRU:1
    # Read again from same cacheline to see if cache hits properly
    ( 'rd', 0x19, 0x00002074, 0, 0         ), ( 'rd', 0x19, 1, 0, 0x75ca1ded ), # LRU:1
    # Read from cacheline 7 way 1 to see if cache hits properly
    ( 'rd', 0x1a, 0x00001074, 0, 0         ), ( 'rd', 0x1a, 1, 0, 0xffffff05 ), # LRU:0
    # Write to cacheline 7 way 1 to see if cache hits properly
    ( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), ( 'wr', 0x1b, 1, 0, 0          ), # LRU:0
    # Read that back
    ( 'rd', 0x1c, 0x0000107c, 0, 0         ), ( 'rd', 0x1c, 1, 0, 0xffffff09 ), # LRU:0
    # Evict way 0 again
    ( 'rd', 0x1d, 0x000a0070, 0, 0         ), ( 'rd', 0x1d, 0, 0, 0xffffff00 ), # LRU:1
  ]
  return SingleCacheTestParams( msg, gen_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32, cache_size=4096 )

class GenericTestCases:

  @pytest.mark.parametrize(
    " name,   test,               stall_prob,latency,src_delay,sink_delay", [
    ("32B-1", rd_data128_line128, 0.0,       1,      0,        0   ),
    ("32B-1", wr_data128_line128, 0.0,       1,      0,        0   ),
    ("16B-1", rd_data32_line64,   0.0,       1,      0,        0   ),
    ("32B-1", rd_hit_1wd,         0.0,       1,      0,        0   ),
    ("32B-1", rd_hit_many,        0.0,       1,      0,        0   ),
    ("32B-1", rd_hit_cline,       0.0,       1,      0,        0   ),
    ("32B-1", wr_hit_clean,       0.0,       1,      0,        0   ),
    ("32B-1", wr_hit_dirty,       0.0,       1,      0,        0   ),
    ("32B-1", wr_hit_rd_hit,      0.0,       1,      0,        0   ),
    ("32B-1", rd_hit_1b,          0.0,       1,      0,        0   ),
    ("32B-1", wr_hit_1b,          0.0,       1,      0,        0   ),
    ("32B-1", rd_hit_2b,          0.0,       1,      0,        0   ),
    ("32B-1", wr_hit_2b,          0.0,       1,      0,        0   ),
    ("32B-1", rd_miss_1wd_cn,     0.0,       1,      0,        0   ),
    ("32B-1", wr_miss_1wd_cn,     0.0,       1,      0,        0   ),
    ("32B-1", rd_miss_dty,        0.0,       1,      0,        0   ),
    ("32B-1", rd_ev_1wd,          0.0,       1,      0,        0   ),
    ("32B-1", rd_miss_1b,         0.0,       1,      0,        0   ),
    ("32B-1", wr_miss_1b,         0.0,       1,      0,        0   ),
    ("32B-1", rd_miss_2b,         0.0,       1,      0,        0   ),
    ("32B-1", wr_miss_2b,         0.0,       1,      0,        0   ),
    ("4KB-1", long_msg_1way,      0.0,       1,      0,        0   ),
    ("32B-2", rd_hit_1s,          0.0,       1,      0,        0   ),
    ("32B-2", wr_hit_1s,          0.0,       1,      0,        0   ),
    ("32B-2", wr_miss_1s,         0.0,       1,      0,        0   ),
    ("32B-2", rd_hit_2s,          0.0,       1,      0,        0   ),
    ("32B-2", wr_hit_2s,          0.0,       1,      0,        0   ),
    ("32B-2", wr_miss_2s,         0.0,       1,      0,        0   ),
    ("32B-2", ev_2way,            0.0,       1,      0,        0   ),
    ("4KB-2", long_msg_2way,      0.0,       1,      0,        0   ),
    ("32B-1", rd_data128_line128, 0.0,       2,      1,        2   ),
    ("32B-1", wr_data128_line128, 0.0,       2,      1,        2   ),
    ("16B-1", rd_data32_line64,   0.0,       2,      1,        2   ),
    ("32B-1", rd_hit_1wd,         0.0,       2,      1,        2   ),
    ("32B-1", rd_hit_many,        0.0,       2,      1,        2   ),
    ("32B-1", rd_hit_cline,       0.0,       2,      1,        2   ),
    ("32B-1", wr_hit_clean,       0.0,       2,      1,        2   ),
    ("32B-1", wr_hit_dirty,       0.0,       2,      1,        2   ),
    ("32B-1", wr_hit_rd_hit,      0.0,       2,      1,        2   ),
    ("32B-1", rd_hit_1b,          0.0,       2,      1,        2   ),
    ("32B-1", wr_hit_1b,          0.0,       2,      1,        2   ),
    ("32B-1", rd_hit_2b,          0.0,       2,      1,        2   ),
    ("32B-1", wr_hit_2b,          0.0,       2,      1,        2   ),
    ("32B-1", rd_miss_1wd_cn,     0.0,       2,      1,        2   ),
    ("32B-1", wr_miss_1wd_cn,     0.0,       2,      1,        2   ),
    ("32B-1", rd_miss_dty,        0.0,       2,      1,        2   ),
    ("32B-1", rd_ev_1wd,          0.0,       2,      1,        2   ),
    ("32B-1", rd_miss_1b,         0.0,       2,      1,        2   ),
    ("32B-1", wr_miss_1b,         0.0,       2,      1,        2   ),
    ("32B-1", rd_miss_2b,         0.0,       2,      1,        2   ),
    ("32B-1", wr_miss_2b,         0.0,       2,      1,        2   ),
    ("4KB-1", long_msg_1way,      0.0,       2,      1,        2   ),
    ("32B-2", rd_hit_1s,          0.0,       2,      1,        2   ),
    ("32B-2", wr_hit_1s,          0.0,       2,      1,        2   ),
    ("32B-2", wr_miss_1s,         0.0,       2,      1,        2   ),
    ("32B-2", rd_hit_2s,          0.0,       2,      1,        2   ),
    ("32B-2", wr_hit_2s,          0.0,       2,      1,        2   ),
    ("32B-2", wr_miss_2s,         0.0,       2,      1,        2   ),
    ("32B-2", ev_2way,            0.0,       2,      1,        2   ),
    ("4KB-2", long_msg_2way,      0.0,       2,      1,        2   ),
   ])
  def test_ReadWrite( s, name, test, stall_prob, latency, src_delay, sink_delay,
                      cmdline_opts, line_trace ):  
    p = test()
    s.run_test( p.msg, p.mem, p.CacheReqType, p.CacheRespType, p.MemReqType, p.MemRespType, 
                p.associativity, p.size, stall_prob, latency, src_delay, sink_delay, 
                cmdline_opts, line_trace )
