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
from ifcs.MemMsg import mk_mem_msg, MemMsgType

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

#-------------------------------------------------------------------------
# Test driver
#-------------------------------------------------------------------------

class InvFlushTests:

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
  ])
  def test_Cifer_2way_size256_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                      stall_prob, latency, src_delay, sink_delay ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                256, stall_prob, latency, src_delay, sink_delay, dump_vcd,
                test_verilog, max_cycles )

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
  ])
  def test_Cifer_2way_size4096_clw128( s, name, test, dump_vcd, test_verilog, max_cycles,
                                      stall_prob, latency, src_delay, sink_delay ):
    mem = random_memory if name == "RAND" else cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
                4096, stall_prob, latency, src_delay, sink_delay, dump_vcd,
                test_verilog, max_cycles )