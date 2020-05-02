"""
=========================================================================
 AmoTests.py
=========================================================================

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 March 2020
"""

import pytest
from test.sim_utils import SingleCacheTestParams

amo_mem = [
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

def cifer_hypo1():
  msg =  [
    #    type  opq   addr      len  data          type  opq test len  data
    ( 'wr', 0x00, 0x0000005c, 0, 0xfff), ( 'wr', 0x00, 0, 0, 0 ), # refill-write
    ( 'rd', 0x01, 0x00000008, 0, 0),     ( 'rd', 0x01, 0, 0, 3 ),     # evict
    ( 'rd', 0x02, 0x00000060, 0, 0),     ( 'rd', 0x02, 0, 0, 0xa ),   # read new written data
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def subword():
  msg =  [
    #    type  opq   addr       len data         type  opq test len  data
    ( 'wr', 0x00, 0x00000000, 1, 0x01), ( 'wr', 0x00, 0,  1,  0    ),
    ( 'ad', 0x01, 0x00000000, 0, 0x02), ( 'ad', 0x01, 0,  0,  0x01 ),
    ( 'rd', 0x02, 0x00000000, 0, 0),    ( 'rd', 0x02, 0,  0,  0x3 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def amo_read():
  msg =  [
    #    type  opq   addr       len data         type  opq test len  data
    ( 'rd', 0x00, 0x00000000, 0, 0),    ( 'rd', 0x00, 0,  0,  0x1 ),
    ( 'ad', 0x01, 0x00000000, 0, 0x10), ( 'ad', 0x01, 0,  0,  0x1 ),
    ( 'rd', 0x02, 0x00000000, 0, 0),    ( 'rd', 0x02, 0,  0,  0x11),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def line_1way():
  msg =  [
    #    type  opq   addr       len data         type  opq test len  data
    ( 'wr', 0x00, 0x00000000, 0, 0x0f), ( 'wr', 0x00, 0,  0,  0   ),
    ( 'ad', 0x01, 0x00000000, 0, 0x10), ( 'ad', 0x01, 0,  0,  0x0f),
    ( 'rd', 0x02, 0x00000000, 0, 0),    ( 'rd', 0x02, 0,  0,  0x1f),
    ( 'wr', 0x00, 0x00000004, 0, 0xf0), ( 'wr', 0x00, 1,  0,  0   ),
    ( 'ad', 0x03, 0x00000004, 0, 0x3),  ( 'ad', 0x03, 0,  0,  0xf0),
    ( 'rd', 0x04, 0x00000004, 0, 0),    ( 'rd', 0x04, 0,  0,  0xf3),
    ( 'ad', 0x05, 0x00000008, 0, 0x4),  ( 'ad', 0x05, 0,  0,  0x3 ),
    ( 'rd', 0x06, 0x00000008, 0, 0),    ( 'rd', 0x06, 0,  0,  0x7 ),
    ( 'ad', 0x05, 0x0000000c, 0, 0x5),  ( 'ad', 0x05, 0,  0,  0x4 ),
    ( 'rd', 0x06, 0x0000000c, 0, 0),    ( 'rd', 0x06, 0,  0,  0x9 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def diff_tag():
  msg =  [
    #    type opq   addr     len data         type opq test len data
    ( 'wr', 1, 0x00000000, 0, 0xff), ( 'wr', 1, 0,  0,  0 ),
    ( 'ad', 2, 0x00020000, 0, 0x1 ), ( 'ad', 2, 0,  0,  5 ),
    ( 'rd', 3, 0x00000000, 0, 0   ), ( 'rd', 3, 1,  0,  0xff ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )


def line_2way():
  msg =  [
    #    type opq   addr     len data         type opq test len data
    ( 'wr', 1, 0x00000000, 0, 0xff), ( 'wr', 1, 0,  0,  0 ),# first set
    ( 'ad', 2, 0x00020000, 0, 0x1 ), ( 'ad', 2, 0,  0,  5 ),# no change lru
    ( 'wr', 2, 0x00030000, 0, 0x1f), ( 'wr', 2, 0,  0,  0 ),# second set
    ( 'rd', 2, 0x00000000, 0, 0x0 ), ( 'rd', 2, 1,  0,  0xff ),# read first set
    ( 'rd', 2, 0x00030000, 0, 0x0 ), ( 'rd', 2, 1,  0,  0x1f ),#
    ( 'rd', 2, 0x00020000, 0, 0x0 ), ( 'rd', 2, 0,  0,  6 ),#
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def amo_ad():
  msg =  [
    #    type  opq   addr   len  data     type  opq test len  data
    ( 'ad', 0, 0x00000004, 0, 1), ( 'ad', 0, 0, 0, 2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0, 0, 1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1, 0, 3 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_an():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'an', 0, 0x00000004, 0, 1), ( 'an', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  0 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_or():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'or', 0, 0x00000004, 0, 1), ( 'or', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  3 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_sw():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'sw', 0, 0x00000004, 0, 0xf), ( 'sw', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  0xf ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_mi():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'mi', 0, 0x00000004, 0, -1), ( 'mi', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0),  ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0),  ( 'rd', 2, 1,  0,  -1 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_mu():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'mu', 0, 0x00000004, 0, 1), ( 'mu', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  1 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_mx():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'mx', 0, 0x00000004, 0, 0x7fffffff), ( 'mx', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  0x7fffffff ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_xu():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'xu', 0, 0x00000004, 0, -1), ( 'xu', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  -1 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_xo():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'xo', 0, 0x00000004, 0, 2), ( 'xo', 0, 0,  0,  2 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'rd', 2, 0x00000004, 0, 0), ( 'rd', 2, 1,  0,  0 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def same_line():
  msg =  [
    #    type opq   addr     len data         type opq test len data
    ( 'wr', 1, 0x00000000, 0, 0xff), ( 'wr', 1, 0,  0,  0 ),
    ( 'ad', 2, 0x00000004, 0, 0x1 ), ( 'ad', 2, 0,  0,  2 ),
    ( 'rd', 3, 0x00000000, 0, 0   ), ( 'rd', 3, 0,  0,  0xff ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=1, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def amo_hypo2():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'rd', 0, 0x00000000, 0, 0), ( 'rd', 0, 0,  0,  1 ),
    ( 'ad', 1, 0x00000000, 0, 0), ( 'ad', 1, 0,  0,  1 ),
    ( 'wr', 2, 0x00000000, 0, 0), ( 'wr', 2, 0,  0,  0 ),
    ( 'ad', 3, 0x00000000, 0, 0), ( 'ad', 3, 0,  0,  0 ),
    ( 'rd', 4, 0x00000000, 0, 0), ( 'rd', 4, 0,  0,  0 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def amo_hypo3():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'rd', 0, 0x00000000, 0, 0), ( 'rd', 0, 0,  0,  1 ),
    ( 'wr', 1, 0x00000010, 0, 0), ( 'wr', 1, 0,  0,  0 ),
    ( 'ad', 2, 0x00000010, 0, 0), ( 'ad', 2, 0,  0,  0 ),
    ( 'rd', 3, 0x00000000, 0, 0), ( 'rd', 3, 1,  0,  1 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def amo_hypo4():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'wr', 0, 0x00000010, 0, 0), ( 'wr', 0, 0,  0,  0 ),
    ( 'rd', 1, 0x00000000, 0, 0), ( 'rd', 1, 0,  0,  1 ),
    ( 'ad', 2, 0x00000010, 0, 0), ( 'ad', 2, 0,  0,  0 ),
    ( 'rd', 3, 0x00000000, 0, 0), ( 'rd', 3, 1,  0,  1 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=64, 
                                bitwidth_cache_data=32 )

def amo_hypo5():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'rd', 0, 0x00000010, 0, 0), ( 'rd', 0, 0,  0,  0x11 ),
    ( 'rd', 1, 0x00000030, 0, 0), ( 'rd', 1, 0,  0,  0x31 ),
    ( 'ad', 2, 0x00000010, 0, 0), ( 'ad', 2, 0,  0,  0x11 ),
    ( 'rd', 3, 0x00000010, 0, 0), ( 'rd', 3, 0,  0,  0x11 ),
    ( 'rd', 4, 0x00000030, 0, 0), ( 'rd', 4, 1,  0,  0x31 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

def amo_hypo6():
  msg =  [
    #    type opq   addr     len data      type opq test len data
    ( 'rd', 0, 0x00000010, 0, 0), ( 'rd', 0, 0,  0,  0x11 ),
    ( 'rd', 1, 0x00000030, 0, 0), ( 'rd', 1, 0,  0,  0x31 ),
    ( 'ad', 2, 0x00000030, 0, 1), ( 'ad', 2, 0,  0,  0x31 ),
    ( 'rd', 3, 0x00000030, 0, 0), ( 'rd', 3, 0,  0,  0x32 ),
    ( 'rd', 4, 0x00000010, 0, 0), ( 'rd', 4, 1,  0,  0x11 ),
  ]
  return SingleCacheTestParams( msg, amo_mem, associativity=2, bitwidth_mem_data=128, 
                                bitwidth_cache_data=32 )

# We're not supporting multiword writes yet! 
# def clw128_dbw128():
#   msg = [
#  #    type  opq addr        len data     type  opq test len data
#     ( 'wr', 0,  0x00000000, 8,  0x02), ( 'wr', 0,  0,   8,  0 ),
#     ( 'ad', 1,  0x00000000, 4,  0x02), ( 'ad', 1,  0,   4,  0x02 ),
#     ( 'rd', 2,  0x00000000, 8,  0x00), ( 'rd', 2,  0,   8,  0x200000004 ),
#   ]
#   msg =  mk__( mk_mem_msg(obw, abw, 128, False), msg )

class AmoTests:
  @pytest.mark.parametrize(
    " name,   test,      stall_prob,latency,src_delay,sink_delay", [
    ("32B-1", subword,   0,         1,      0,        0   ),
    ("16B-1", amo_read,  0,         1,      0,        0   ),
    ("32B-1", line_1way, 0,         1,      0,        0   ),
    ("64B-2", diff_tag,  0,         1,      0,        0   ),
    ("64B-2", line_2way, 0,         1,      0,        0   ),
    ("16B-1", amo_ad,    0,         1,      0,        0   ),
    ("16B-1", amo_an,    0,         1,      0,        0   ),
    ("16B-1", amo_or,    0,         1,      0,        0   ),
    ("16B-1", amo_sw,    0,         1,      0,        0   ),
    ("16B-1", amo_mi,    0,         1,      0,        0   ),
    ("16B-1", amo_mu,    0,         1,      0,        0   ),
    ("16B-1", amo_mx,    0,         1,      0,        0   ),
    ("16B-1", amo_xu,    0,         1,      0,        0   ),
    ("16B-1", amo_xo,    0,         1,      0,        0   ),
    ("32B-1", same_line, 0,         1,      0,        0   ),
    ("64B-2", amo_hypo2, 0,         1,      0,        0   ),
    ("64B-2", amo_hypo3, 0,         1,      0,        0   ),
    ("32B-2", amo_hypo4, 0,         1,      0,        0   ),
    ("64B-2", amo_hypo5, 0,         1,      0,        0   ),
    ("64B-2", amo_hypo6, 0,         1,      0,        0   ),
  ])
  def test_AMO( s, name, test, stall_prob, latency, src_delay, sink_delay,
                cmdline_opts, max_cycles, dump_vtb ):
    p = test()            
    s.run_test( p.msg, p.mem, p.CacheReqType, p.CacheRespType, p.MemReqType, p.MemRespType, 
                p.associativity, p.size, stall_prob, latency, src_delay, sink_delay, 
                cmdline_opts, max_cycles, dump_vtb )
