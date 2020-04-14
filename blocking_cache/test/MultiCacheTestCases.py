"""
=========================================================================
 MultiCacheTestCases.py
=========================================================================
Test cases for multicache configs

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 13 April 2020
"""

import pytest
from test.sim_utils import (
  mreq, resp, CacheReqType, CacheRespType, MemReqType, MemRespType, CacheTestParams
)

# Main test memory for dmapped tests
def multicache_mem():
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

def gen_test1():
  associativities = [ 1, 1 ]
  cache_sizes = [ 32, 32 ]
  msgs = [
    #     cache ord type  opq addr        len data         type  opq test len  data
    mreq( 0,    0,  'rd', 0,  0x00000000, 0,  0x00), resp( 'rd', 0,  0,   0,   0          ),
    mreq( 0,    0,  'wr', 0,  0x00000000, 0,  0x01), resp( 'wr', 0,  1,   0,   0          ),
    mreq( 0,    0,  'rd', 0,  0x00020004, 0,  0x00), resp( 'rd', 0,  0,   0,   0xd        ),
    mreq( 1,    1,  'rd', 0,  0x00000000, 0,  0x00), resp( 'rd', 0,  0,   0,   0x01       ),
  ]
  return associativities, cache_sizes, msgs


class MultiCacheTestCases:

  @pytest.mark.parametrize(
    " name,  test,          stall_prob,latency,src_delay,sink_delay", [
    ("",  gen_test1,         0.0,       1,      0,        0   ),
    ])
  # defaults to 4 word cache line by importing from sim_utils
  def test_generic( s, name, test, dump_vcd, test_verilog, max_cycles, stall_prob,
   latency, src_delay, sink_delay ):
    mem = multicache_mem()
    associativities, cache_sizes, msgs = test()
    tp = CacheTestParams( msgs, mem, CacheReqType, CacheRespType, MemReqType,
    MemRespType, associativities, cache_sizes, stall_prob, latency, src_delay, 
    sink_delay )
    s.run_test( tp, dump_vcd, test_verilog, max_cycles, stall_prob )
