"""
=========================================================================
 CiferTests.py
=========================================================================
Direct mapped cache test cases

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 March 2020
"""

import random
import pytest
from mem_pclib.test.sim_utils import req, resp, CacheReqType, CacheRespType, \
  MemReqType, MemRespType, obw, abw, gen_req_resp
from ifcs.MemMsg import mk_mem_msg

# Main memory used in cifer test cases
def cifer_test_memory():
  return [
    0x00000000, 1,
    0x00000004, 2,
    0x00000008, 3,
    0x0000000c, 4,
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

def wr_hit_clean():
  return [
    #    type  opq   addr      len  data       type  opq test len  data
    req( 'rd', 0x00, 0x00000000, 0, 0),   resp( 'rd', 0x00, 0, 0, 1          ), #refill-write
    req( 'wr', 0x01, 0x00000000, 0, 0xf), resp( 'wr', 0x01, 1, 0, 0 ),          #evict
    req( 'wr', 0x02, 0x00000004, 0, 0xe), resp( 'wr', 0x02, 1, 0, 0 ),     #read new written data
    req( 'wr', 0x03, 0x00000008, 0, 0xc), resp( 'wr', 0x03, 1, 0, 0 ), #read-evicted data
    req( 'wr', 0x04, 0x0000000c, 0, 0xb), resp( 'wr', 0x04, 1, 0, 0 ), #read-evicted data
    req( 'wr', 0x05, 0x00000000, 0, 0xa), resp( 'wr', 0x05, 1, 0, 0 ), #read-evicted data
    ]

def cifer_hypo1():
  return [
    #    type  opq   addr      len  data       type  opq test len  data
    req( 'wr', 0x00, 0x0000005c, 0, 0xfff), resp( 'wr', 0x00, 0, 0, 0 ), #refill-write
    req( 'rd', 0x01, 0x00000008, 0, 0), resp( 'rd', 0x01, 0, 0, 3 ),     #evict
    req( 'rd', 0x02, 0x00000060, 0, 0), resp( 'rd', 0x02, 0, 0, 0xa ),     #read new written data
    ]

def amo_subword():
  return [
    #    type  opq   addr       len data         type  opq test len  data
    req( 'wr', 0x00, 0x00000000, 1, 0x01), resp( 'wr', 0x00, 0,  1,  0    ),          
    req( 'ad', 0x01, 0x00000000, 0, 0x02), resp( 'ad', 0x01, 0,  0,  0x01 ),  
    req( 'rd', 0x02, 0x00000000, 0, 0),    resp( 'rd', 0x02, 0,  0,  0x3 ),  
  ]

def amo_rd():
  return [
    #    type  opq   addr       len data         type  opq test len  data
    req( 'rd', 0x00, 0x00000000, 0, 0),    resp( 'rd', 0x00, 0,  0,  0x1 ),          
    req( 'ad', 0x01, 0x00000000, 0, 0x10), resp( 'ad', 0x01, 0,  0,  0x1 ),  
    req( 'rd', 0x02, 0x00000000, 0, 0),    resp( 'rd', 0x02, 0,  0,  0x11),  
  ]

def amo_cache_line():
  return [
    #    type  opq   addr       len data         type  opq test len  data
    req( 'wr', 0x00, 0x00000000, 0, 0x0f), resp( 'wr', 0x00, 0,  0,  0   ),          
    req( 'ad', 0x01, 0x00000000, 0, 0x10), resp( 'ad', 0x01, 0,  0,  0x0f),  
    req( 'rd', 0x02, 0x00000000, 0, 0),    resp( 'rd', 0x02, 0,  0,  0x1f),  
    req( 'wr', 0x00, 0x00000004, 0, 0xf0), resp( 'wr', 0x00, 1,  0,  0   ),          
    req( 'ad', 0x03, 0x00000004, 0, 0x3),  resp( 'ad', 0x03, 0,  0,  0xf0),  
    req( 'rd', 0x04, 0x00000004, 0, 0),    resp( 'rd', 0x04, 0,  0,  0xf3),  
    req( 'ad', 0x05, 0x00000008, 0, 0x4),  resp( 'ad', 0x05, 0,  0,  0x3 ),  
    req( 'rd', 0x06, 0x00000008, 0, 0),    resp( 'rd', 0x06, 0,  0,  0x7 ),  
    req( 'ad', 0x05, 0x0000000c, 0, 0x5),  resp( 'ad', 0x05, 0,  0,  0x4 ),  
    req( 'rd', 0x06, 0x0000000c, 0, 0),    resp( 'rd', 0x06, 0,  0,  0x9 ),  
]

def amo_diff_tag():
  return [
    #    type opq   addr     len data         type opq test len data
    req( 'wr', 1, 0x00000000, 0, 0xff), resp( 'wr', 1, 0,  0,  0 ),  
    req( 'ad', 2, 0x00020000, 0, 0x1 ), resp( 'ad', 2, 0,  0,  5 ),  
    req( 'rd', 3, 0x00000000, 0, 0   ), resp( 'rd', 3, 1,  0,  0xff ),  
  ]

def amo_hypo():
  return [
    #    type opq   addr     len data         type opq test len data
    req( 'wr', 1, 0x00000000, 0, 0xff), resp( 'wr', 1, 0,  0,  0 ),  
    req( 'ad', 2, 0x00000004, 0, 0x1 ), resp( 'ad', 2, 0,  0,  2 ),  
    req( 'rd', 3, 0x00000000, 0, 0   ), resp( 'rd', 3, 0,  0,  0xff ),  
  ]

def amo_2way_line():
  return [
    #    type opq   addr     len data         type opq test len data
    req( 'wr', 1, 0x00000000, 0, 0xff), resp( 'wr', 1, 0,  0,  0 ),# first set
    req( 'ad', 2, 0x00020000, 0, 0x1 ), resp( 'ad', 2, 0,  0,  5 ),# no change lru  
    req( 'wr', 2, 0x00030000, 0, 0x1f), resp( 'wr', 2, 0,  0,  0 ),# second set  
    req( 'rd', 2, 0x00000000, 0, 0x0 ), resp( 'rd', 2, 1,  0,  0xff ),# read first set
    req( 'rd', 2, 0x00030000, 0, 0x0 ), resp( 'rd', 2, 1,  0,  0x1f ),# 
    req( 'rd', 2, 0x00020000, 0, 0x0 ), resp( 'rd', 2, 0,  0,  6 ),# 
  ]

def amo_ad():
  return [
    #    type  opq   addr   len  data     type  opq test len  data
    req( 'ad', 0, 0x00000004, 0, 1), resp( 'ad', 0, 0, 0, 2 ),   
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0, 0, 1 ),   
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1, 0, 3 ),   
  ]

def amo_an():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'an', 0, 0x00000004, 0, 1), resp( 'an', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  0 ),
  ]

def amo_or():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'or', 0, 0x00000004, 0, 1), resp( 'or', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  3 ),
  ]

def amo_sw():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'sw', 0, 0x00000004, 0, 0xf), resp( 'sw', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  0xf ),
  ]

def amo_mi():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'mi', 0, 0x00000004, 0, -1), resp( 'mi', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0),  resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0),  resp( 'rd', 2, 1,  0,  -1 ),
  ]

def amo_mu():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'mu', 0, 0x00000004, 0, 1), resp( 'mu', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  1 ),
  ]

def amo_mx():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'mx', 0, 0x00000004, 0, 0x7fffffff), resp( 'mx', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  0x7fffffff ),
  ]

def amo_xu():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'xu', 0, 0x00000004, 0, -1), resp( 'xu', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  -1 ),
  ]

def amo_xo():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'xo', 0, 0x00000004, 0, 2), resp( 'xo', 0, 0,  0,  2 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'rd', 2, 0x00000004, 0, 0), resp( 'rd', 2, 1,  0,  0 ),
  ]

def amo_hypo2():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'rd', 0, 0x00000000, 0, 0), resp( 'rd', 0, 0,  0,  1 ),
    req( 'ad', 1, 0x00000000, 0, 0), resp( 'ad', 1, 0,  0,  1 ),
    req( 'wr', 2, 0x00000000, 0, 0), resp( 'wr', 2, 0,  0,  0 ),
    req( 'ad', 3, 0x00000000, 0, 0), resp( 'ad', 3, 0,  0,  0 ),
    req( 'rd', 4, 0x00000000, 0, 0), resp( 'rd', 4, 0,  0,  0 ),
  ]

def amo_hypo3():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'rd', 0, 0x00000000, 0, 0), resp( 'rd', 0, 0,  0,  1 ),
    req( 'wr', 1, 0x00000010, 0, 0), resp( 'wr', 1, 0,  0,  0 ),
    req( 'ad', 2, 0x00000010, 0, 0), resp( 'ad', 2, 0,  0,  0 ),
    req( 'rd', 3, 0x00000000, 0, 0), resp( 'rd', 3, 1,  0,  1 ),
  ]

def amo_hypo4():
  return [
    #    type opq   addr     len data      type opq test len data
    req( 'wr', 0, 0x00000010, 0, 0), resp( 'wr', 0, 0,  0,  0 ),
    req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 1, 0,  0,  1 ),
    req( 'ad', 2, 0x00000010, 0, 0), resp( 'ad', 2, 0,  0,  0 ),
    req( 'rd', 3, 0x00000000, 0, 0), resp( 'rd', 3, 1,  0,  1 ),
  ]

class CiferTests:
  
  @pytest.mark.parametrize( 
    " name,  test,           stall_prob,latency,src_delay,sink_delay", [
    ("Hypo", cifer_hypo1,    0,         1,      0,        0   ),
    ("AMO",  amo_subword,    0,         1,      0,        0   ),
    ("AMO",  amo_diff_tag,   0,         1,      0,        0   ),
    ("AMO",  amo_ad,         0,         1,      0,        0   ),
    ("AMO",  amo_an,         0,         1,      0,        0   ),
    ("AMO",  amo_or,         0,         1,      0,        0   ),
    ("AMO",  amo_sw,         0,         1,      0,        0   ),
    ("AMO",  amo_mi,         0,         1,      0,        0   ),
    ("AMO",  amo_mu,         0,         1,      0,        0   ),
    ("AMO",  amo_mx,         0,         1,      0,        0   ),
    ("AMO",  amo_xu,         0,         1,      0,        0   ),
    ("AMO",  amo_xo,         0,         1,      0,        0   ),
    ("AMO",  amo_rd,         0,         1,      0,        0   ),
    ("AMO",  amo_hypo,       0,         1,      0,        0   ),
    ("AMO",  amo_rd,         0.5,       2,      2,        2   ),
    ("AMO",  amo_diff_tag,   0.5,       2,      2,        2   ),
    ("Hypo", cifer_hypo1,    0.5,       2,      2,        2   ),
    ("AMO",  amo_subword,    0.5,       2,      2,        2   ),
    ("AMO",  amo_ad,         0.5,       2,      2,        2   ),
  ])
  def test_Cifer_dmapped_size16_clw64( s, name, test, dump_vcd, test_verilog, max_cycles, \
    stall_prob, latency, src_delay, sink_delay ):
    mem = cifer_test_memory() 
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    16, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles ) 

  @pytest.mark.parametrize( 
    " name,  test,           stall_prob,latency,src_delay,sink_delay", [
    ("DBPW", wr_hit_clean,   0,         1,      0,        0   ),
    ("AMO",  amo_cache_line, 0,         1,      0,        0   ),
    ("DBPW", wr_hit_clean,   0.5,       2,      4,        4   ),
    ("AMO",  amo_cache_line, 0.5,       2,      4,        4   ),
  ])
  def test_Cifer_dmapped_size32_clw128( s, name, test, dump_vcd, test_verilog, max_cycles, \
    stall_prob, latency, src_delay, sink_delay ):
    mem = cifer_test_memory() 
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    32, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles ) 

  @pytest.mark.parametrize( 
    " name,  test,           stall_prob,latency,src_delay,sink_delay", [
    ("DBPW", wr_hit_clean,   0,         1,      0,        0   ),
    ("AMO",  amo_cache_line, 0,         1,      0,        0   ),
    ("AMO",  amo_2way_line,  0,         1,      0,        0   ),
    ("AMO",  amo_diff_tag,   0,         1,      0,        0   ),
    ("AMO",  amo_diff_tag,   0.5,       2,      2,        2   ),
    ("AMO",  amo_2way_line,  0.5,       2,      4,        4   ),
    ("DBPW", wr_hit_clean,   0.5,       2,      4,        4   ),
    ("AMO",  amo_cache_line, 0.5,       2,      4,        4   ),
    ("AMO",  amo_ad,         0,         1,      0,        0   ),
    ("AMO",  amo_an,         0,         1,      0,        0   ),
    ("AMO",  amo_or,         0,         1,      0,        0   ),
    ("AMO",  amo_sw,         0,         1,      0,        0   ),
    ("AMO",  amo_mi,         0,         1,      0,        0   ),
    ("AMO",  amo_mu,         0,         1,      0,        0   ),
    ("AMO",  amo_mx,         0,         1,      0,        0   ),
    ("AMO",  amo_xu,         0,         1,      0,        0   ),
    ("AMO",  amo_xo,         0,         1,      0,        0   ),
    ("AMO",  amo_rd,         0,         1,      0,        0   ),
    ("AMO",  amo_hypo,       0,         1,      0,        0   ),
    ("AMO",  amo_hypo2,      0,         1,      0,        0   ),
  ])
  def test_Cifer_2way_size64_clw128( s, name, test, dump_vcd, test_verilog, max_cycles, \
    stall_prob, latency, src_delay, sink_delay ):
    mem = cifer_test_memory() 
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
    64, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles ) 

  @pytest.mark.parametrize( 
    " name,  test,           stall_prob,latency,src_delay,sink_delay", [
    ("AMO",  amo_hypo3,      0,         1,      0,        0   ),
    ("AMO",  amo_hypo4,      0,         1,      0,        0   ),
  ])
  def test_Cifer_2way_size32_clw64( s, name, test, dump_vcd, test_verilog, max_cycles, \
    stall_prob, latency, src_delay, sink_delay ):
    mem = cifer_test_memory() 
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test( test(), mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 2,
    32, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog, max_cycles ) 
