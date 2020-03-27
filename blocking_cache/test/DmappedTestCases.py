"""
=========================================================================
 DmappedTestCases.py
=========================================================================
Direct mapped cache test cases

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 11 November 2019
"""
import pytest
from mem_pclib.test.sim_utils import req, resp, CacheReqType, CacheRespType, \
  MemReqType, MemRespType

# Main test memory for dmapped tests
def dmapped_mem():
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

def rd_hit_1wd():
  return [
      #    type  opq  addr     len data                type  opq  test len data
    req( 'in', 0x0, 0x000ab000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0, 0          ),
    req( 'rd', 0x1, 0x000ab000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0xdeadbeef ),
  ]

def rd_hit_many():
  msgs = []
  for i in range(4):
    #                  type  opq  addr          len data
    msgs.append(req(  'in', i, ((0x00012000)<<2)+i*4, 0, i ))
    msgs.append(resp( 'in', i, 0,             0, 0 ))
  for i in range(4):
    msgs.append(req(  'rd', i, ((0x00012000)<<2)+i*4, 0, 0 ))
    msgs.append(resp( 'rd', i, 1,             0, i ))
  return msgs

#----------------------------------------------------------------------
# Test Case: Read Hits: Test for entire line hits
#----------------------------------------------------------------------

def rd_hit_cline():
  base_addr = 0x20
  return [
    req( 'in', 0x0, base_addr,    0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
    req( 'in', 0x1, base_addr+4,  0, 0xcafecafe ), resp( 'in', 0x1, 0, 0, 0          ),
    req( 'in', 0x2, base_addr+8,  0, 0xfafafafa ), resp( 'in', 0x2, 0, 0, 0          ),
    req( 'in', 0x3, base_addr+12, 0, 0xbabababa ), resp( 'in', 0x3, 0, 0, 0          ),
    req( 'rd', 0x4, base_addr,    0, 0          ), resp( 'rd', 0x4, 1, 0, 0xdeadbeef ),
    req( 'rd', 0x5, base_addr+4,  0, 0          ), resp( 'rd', 0x5, 1, 0, 0xcafecafe ),
    req( 'rd', 0x6, base_addr+8,  0, 0          ), resp( 'rd', 0x6, 1, 0, 0xfafafafa ),
    req( 'rd', 0x7, base_addr+12, 0, 0          ), resp( 'rd', 0x7, 1, 0, 0xbabababa ),
  ]

#----------------------------------------------------------------------
# Test Case: Write Hit: CLEAN
#----------------------------------------------------------------------
def wr_hit_clean():
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, 0x118c,    0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0  ),
    req( 'wr', 0x1, 0x1184,    0, 55         ), resp( 'wr', 0x1, 1,   0,  0  ),
    req( 'rd', 0x2, 0x1184,    0, 0          ), resp( 'rd', 0x2, 1,   0,  55 ),
  ]

#----------------------------------------------------------------------
# Test Case: Write Hit: DIRTY
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def wr_hit_dirty():
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, 0x66660,   0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'wr', 0x1, 0x66660,   0, 0xffffffff ), resp( 'wr', 0x1, 1,   0,  0          ),
    req( 'wr', 0x2, 0x66664,   0, 0xc0ef     ), resp( 'wr', 0x2, 1,   0,  0 ),
    req( 'wr', 0x3, 0x66668,   0, 0x39287    ), resp( 'wr', 0x3, 1,   0,  0 ),
    req( 'wr', 0x4, 0x6666c,   0, 0xabcef    ), resp( 'wr', 0x4, 1,   0,  0 ),
    req( 'rd', 0x5, 0x66668,   0, 0          ), resp( 'rd', 0x5, 1,   0,  0x39287 ),
  ]

#----------------------------------------------------------------------
# Test Case: Write Hit: read/write hit
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def wr_hit_rd_hit():
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'in', 0x0, 0, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x1, 0, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
    req( 'wr', 0x2, 0, 0, 0xffffffff ), resp( 'wr', 0x2, 1,   0,  0          ),
    req( 'rd', 0x3, 0, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0xffffffff ),
  ]
#----------------------------------------------------------------------
# Test Case: Read Miss Clean:
#----------------------------------------------------------------------

def rd_miss_1wd_cn():
  return [
    #    type  opq  addr       len data                type  opq  test len data
    req( 'rd', 0x0, 0x00000000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0 ),
    req( 'rd', 0x1, 0x00000004, 0, 0          ), resp( 'rd', 0x1, 1,   0,  1 )
  ]

#----------------------------------------------------------------------
# Test Case: Write Miss Clean:
#----------------------------------------------------------------------

def wr_miss_1wd_cn():
  return [
    #    type  opq  addr       len data                type  opq test len data
    req( 'wr', 0x0, 0x00000000, 0, 0x00c0ffee ), resp( 'wr', 0x0, 0,   0, 0          ),
    req( 'rd', 0x1, 0x00000000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0x00c0ffee ),
    req( 'rd', 0x2, 0x00000008, 0, 0          ), resp( 'rd', 0x2, 1,   0, 2 )
  ]

#-------------------------------------------------------------------------
# Test cases: Write Dirty:
#-------------------------------------------------------------------------

def rd_miss_dty():
  return [
    #    type  opq   addr                 len data               type  opq   test len data
    req( 'wr', 0x0, 0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ),
    req( 'rd', 0x1, 0x00020000,  0, 0          ), resp('rd', 0x1,   0,   0, 0xc ),
    req( 'rd', 0x2, 0x00000000,  0, 0          ), resp('rd', 0x2,   0,   0, 0xbeefbeeb )
  ]

#-------------------------------------------------------------------------
# Test Case: Direct Mapped Read Evict
#-------------------------------------------------------------------------

def rd_ev_1wd():
  return [
      #    type  opq   addr      len  data               type  opq test len  data
    req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), # write something
    req( 'rd', 0x01, 0x00000000, 0, 0         ), resp( 'rd', 0x01, 0, 0, 0 ), # read miss on dirty line
    req( 'rd', 0x02, 0x00002000, 0, 0         ), resp( 'rd', 0x02, 0, 0, 0xffffff00 ), # read evicted address
  ]

#-------------------------------------------------------------------------
# Test Case: test direct-mapped
#-------------------------------------------------------------------------
# Test cases designed for direct-mapped cache

def long_msg():
  return [
     #    type  opq   addr      len  data               type  opq test len  data
      req( 'wr', 0x00, 0x00000000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), # Write to cacheline 0
      req( 'wr', 0x01, 0x00000004, 0, 0xffffff01), resp( 'wr', 0x01, 1, 0, 0          ),
      req( 'wr', 0x02, 0x00000008, 0, 0xffffff02), resp( 'wr', 0x02, 1, 0, 0          ),
      req( 'wr', 0x03, 0x0000000c, 0, 0xffffff03), resp( 'wr', 0x03, 1, 0, 0          ),
      req( 'wr', 0x04, 0x00001000, 0, 0xffffff04), resp( 'wr', 0x04, 0, 0, 0          ), # Write to cacheline 0
      req( 'wr', 0x05, 0x00001004, 0, 0xffffff05), resp( 'wr', 0x05, 1, 0, 0          ),
      req( 'wr', 0x06, 0x00001008, 0, 0xffffff06), resp( 'wr', 0x06, 1, 0, 0          ),
      req( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), resp( 'wr', 0x07, 1, 0, 0          ),
      req( 'rd', 0x08, 0x00002000, 0, 0         ), resp( 'rd', 0x08, 0, 0, 0x00facade ), # Evict cache 0
      req( 'rd', 0x09, 0x00002004, 0, 0         ), resp( 'rd', 0x09, 1, 0, 0x05ca1ded ), # Read again from same cacheline
      req( 'rd', 0x0a, 0x00001004, 0, 0         ), resp( 'rd', 0x0a, 0, 0, 0xffffff05 ), # Read from cacheline 0
      req( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), resp( 'wr', 0x0b, 1, 0, 0          ), # Write to cacheline 0
      req( 'rd', 0x0c, 0x0000100c, 0, 0         ), resp( 'rd', 0x0c, 1, 0, 0xffffff09 ), # Read that back
      req( 'rd', 0x0d, 0x00000000, 0, 0         ), resp( 'rd', 0x0d, 0, 0, 0xffffff00 ), # Evict cacheline 0
      req( 'wr', 0x10, 0x00000070, 0, 0xffffff00), resp( 'wr', 0x10, 0, 0, 0          ), # Write to cacheline 7
      req( 'wr', 0x11, 0x00000074, 0, 0xffffff01), resp( 'wr', 0x11, 1, 0, 0          ),
      req( 'wr', 0x12, 0x00000078, 0, 0xffffff02), resp( 'wr', 0x12, 1, 0, 0          ),
      req( 'wr', 0x13, 0x0000007c, 0, 0xffffff03), resp( 'wr', 0x13, 1, 0, 0          ),
      req( 'wr', 0x14, 0x00001070, 0, 0xffffff04), resp( 'wr', 0x14, 0, 0, 0          ), # Write to cacheline 7
      req( 'wr', 0x15, 0x00001074, 0, 0xffffff05), resp( 'wr', 0x15, 1, 0, 0          ),
      req( 'wr', 0x16, 0x00001078, 0, 0xffffff06), resp( 'wr', 0x16, 1, 0, 0          ),
      req( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), resp( 'wr', 0x17, 1, 0, 0          ),
      req( 'rd', 0x18, 0x00002070, 0, 0         ), resp( 'rd', 0x18, 0, 0, 0x70facade ), # Evict cacheline 7
      req( 'rd', 0x19, 0x00002074, 0, 0         ), resp( 'rd', 0x19, 1, 0, 0x75ca1ded ), # Read again from same cacheline
      req( 'rd', 0x1a, 0x00001074, 0, 0         ), resp( 'rd', 0x1a, 0, 0, 0xffffff05 ), # Read from cacheline 7
      req( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), resp( 'wr', 0x1b, 1, 0, 0          ), # Write to cacheline 7
      req( 'rd', 0x1c, 0x0000107c, 0, 0         ), resp( 'rd', 0x1c, 1, 0, 0xffffff09 ), # Read that back
      req( 'rd', 0x1d, 0x00000070, 0, 0         ), resp( 'rd', 0x1d, 0, 0, 0xffffff00 ), # Evict cacheline 0 again
  ]

def rd_hit_1b():
  return [
    #    type  opq   addr      len  data                type  opq test len  data
    req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0 ),
    req( 'rd', 0x01, 0x00000000, 1, 0), resp( 'rd', 0x01, 1, 1, 0x00000012          ),
    req( 'rd', 0x02, 0x00000001, 1, 0), resp( 'rd', 0x02, 1, 1, 0x000000ef          ),
    req( 'rd', 0x03, 0x00000002, 1, 0), resp( 'rd', 0x03, 1, 1, 0x000000cd          ),
    req( 'rd', 0x04, 0x00000003, 1, 0), resp( 'rd', 0x04, 1, 1, 0x000000ab          ),
  ]

def wr_hit_1b():
  return [
    #    type  opq   addr      len  data                type  opq test len  data
    req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0          ),
    req( 'wr', 0x01, 0x00000000, 1, 0x99),       resp( 'wr', 0x01, 1, 1, 0          ),
    req( 'wr', 0x01, 0x00000001, 1, 0x66),       resp( 'wr', 0x01, 1, 1, 0          ),
    req( 'wr', 0x01, 0x00000002, 1, 0x33),       resp( 'wr', 0x01, 1, 1, 0          ),
    req( 'wr', 0x01, 0x00000003, 1, 0x11),       resp( 'wr', 0x01, 1, 1, 0          ),
    req( 'rd', 0x02, 0x00000000, 0, 0),          resp( 'rd', 0x02, 1, 0, 0x11336699 ),
  ]

def rd_miss_1b():
  return [
    #    type  opq   addr      len  data      type  opq test len  data    ),
    req( 'rd', 0x00, 0x00001000, 1, 0), resp( 'rd', 0x00, 0, 1, 0x04 ),
    req( 'rd', 0x01, 0x00001001, 1, 0), resp( 'rd', 0x01, 1, 1, 0x03 ),
    req( 'rd', 0x02, 0x00001002, 1, 0), resp( 'rd', 0x02, 1, 1, 0x02 ),
    req( 'rd', 0x03, 0x00001003, 1, 0), resp( 'rd', 0x03, 1, 1, 0x01 ),
  ]

def wr_miss_1b():
  return [
    #    type  opq   addr      len  data         type  opq test len  data
    req( 'wr', 0x00, 0x00001001, 1, 0x11), resp( 'wr', 0x00, 0, 1, 0          ),
    req( 'wr', 0x01, 0x00001005, 1, 0x22), resp( 'wr', 0x01, 1, 1, 0          ),
    req( 'wr', 0x02, 0x00001009, 1, 0x33), resp( 'wr', 0x02, 1, 1, 0 ),
    req( 'wr', 0x03, 0x0000100d, 1, 0x44), resp( 'wr', 0x03, 1, 1, 0 ),
    req( 'rd', 0x00, 0x00001000, 0, 0),    resp( 'rd', 0x00, 1, 0, 0x01021104 ),
    req( 'rd', 0x01, 0x00001004, 0, 0),    resp( 'rd', 0x01, 1, 0, 0x05062208 ),
    req( 'rd', 0x02, 0x00001008, 0, 0),    resp( 'rd', 0x02, 1, 0, 0x090a330c ),
    req( 'rd', 0x03, 0x0000100c, 0, 0),    resp( 'rd', 0x03, 1, 0, 0x0d0e4410 ),
  ]

def rd_hit_2b():
  return [
    #    type  opq   addr      len  data                type  opq test len  data
    req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0          ),
    req( 'rd', 0x01, 0x00000000, 2, 0),          resp( 'rd', 0x01, 1, 2, 0x0000ef12 ),
    req( 'rd', 0x02, 0x00000002, 2, 0),          resp( 'rd', 0x02, 1, 2, 0x0000abcd ),
    ]

def wr_hit_2b():
  return [
    #    type  opq   addr      len  data                type  opq test len  data
    req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0          ),
    req( 'wr', 0x01, 0x00000000, 2, 0x99),       resp( 'wr', 0x01, 1, 2, 0          ),
    req( 'wr', 0x01, 0x00000002, 2, 0xac13),     resp( 'wr', 0x01, 1, 2, 0          ),
    req( 'rd', 0x02, 0x00000000, 0, 0),          resp( 'rd', 0x02, 1, 0, 0xac130099 ),
  ]

def rd_miss_2b():
  return [
    #    type  opq   addr      len  data      type  opq test len  data    ),
    req( 'rd', 0x00, 0x00001000, 2, 0), resp( 'rd', 0x00, 0, 2, 0x0304 ),
    req( 'rd', 0x02, 0x00002002, 2, 0), resp( 'rd', 0x02, 0, 2, 0x00fa ),
  ]

def wr_miss_2b():
  return [
    #    type  opq   addr      len  data                type  opq test len  data
    req( 'wr', 0x00, 0x00001000, 2, 0x11), resp( 'wr', 0x00, 0, 2, 0          ),
    req( 'wr', 0x02, 0x00002002, 2, 0x33), resp( 'wr', 0x02, 0, 2, 0 ),
    req( 'rd', 0x00, 0x00001000, 0, 0), resp( 'rd', 0x00, 0, 0, 0x01020011 ),
    req( 'rd', 0x02, 0x00002000, 0, 0), resp( 'rd', 0x02, 0, 0, 0x0033cade ),
  ]  

class DmappedTestCases:

  @pytest.mark.parametrize( 
    " name,  test,          stall_prob,latency,src_delay,sink_delay", [
    ("Hit",  rd_hit_1wd,    0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_many,   0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_cline,  0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_clean,  0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_dirty,  0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_rd_hit, 0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_1b,     0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_1b,     0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_2b,     0.0,       1,      0,        0   ),
    ("Hit",  wr_hit_2b,     0.0,       1,      0,        0   ),
    ("Miss", rd_miss_1wd_cn,0.0,       1,      0,        0   ),
    ("Miss", wr_miss_1wd_cn,0.0,       1,      0,        0   ),
    ("Miss", rd_miss_dty,   0.0,       1,      0,        0   ),
    ("Miss", rd_ev_1wd,     0.0,       1,      0,        0   ),
    ("Miss", rd_miss_1b,    0.0,       1,      0,        0   ),
    ("Miss", wr_miss_1b,    0.0,       1,      0,        0   ),
    ("Miss", rd_miss_2b,    0.0,       1,      0,        0   ),
    ("Miss", wr_miss_2b,    0.0,       1,      0,        0   ),
    ("Hit",  rd_hit_1wd,    0.5,       2,      2,        2   ),
    ("Hit",  rd_hit_many,   0.5,       2,      2,        2   ),
    ("Hit",  rd_hit_cline,  0.5,       2,      2,        2   ),
    ("Hit",  wr_hit_clean,  0.5,       2,      2,        2   ),
    ("Hit",  wr_hit_dirty,  0.5,       2,      2,        2   ),
    ("Hit",  wr_hit_rd_hit, 0.5,       2,      2,        2   ),
    ("Hit",  rd_hit_1b,     0.5,       2,      2,        2   ),
    ("Hit",  wr_hit_1b,     0.5,       2,      2,        2   ),
    ("Hit",  rd_hit_2b,     0.5,       2,      2,        2   ),
    ("Hit",  wr_hit_2b,     0.5,       2,      2,        2   ),
    ("Miss", rd_miss_1wd_cn,0.5,       2,      2,        2   ),
    ("Miss", wr_miss_1wd_cn,0.5,       2,      2,        2   ),
    ("Miss", rd_miss_dty,   0.5,       2,      2,        2   ),
    ("Miss", rd_ev_1wd,     0.5,       2,      2,        2   ),
    ("Miss", rd_miss_1b,    0.5,       2,      2,        2   ),
    ("Miss", wr_miss_1b,    0.5,       2,      2,        2   ),
    ("Miss", rd_miss_2b,    0.5,       2,      2,        2   ),
    ("Miss", wr_miss_2b,    0.5,       2,      2,        2   ),
  ])
  def test_Dmapped_size32_clw128( s, name, test, dump_vcd, test_verilog, max_cycles, \
    stall_prob, latency, src_delay, sink_delay ):
    mem = dmapped_mem() 
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    32, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles ) 

  @pytest.mark.parametrize( 
    " name,  test,          stall_prob,latency,src_delay,sink_delay", [
    ("Gen",  long_msg,      0.0,       1,      0,        0   ),
    ("Gen",  long_msg,      0.5,       2,      2,        2   ),
  ])
  def test_Dmapped_size4096_clw128( s, name, test, dump_vcd, test_verilog, max_cycles, \
    stall_prob, latency, src_delay, sink_delay ):
    mem = dmapped_mem() 
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    4096, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles ) 
