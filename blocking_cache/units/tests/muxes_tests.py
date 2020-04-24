"""
=========================================================================
muxes_tests.py
=========================================================================
Testbench for cifer functions

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 23 April 2020
"""


from pymtl3 import *
from pymtl3.stdlib.test.test_utils import run_test_vector_sim
from mem_ifcs.MemMsg import MemMsgType, mk_mem_msg
from blocking_cache.CacheDerivedParams import CacheDerivedParams
from ..muxes import DataSelectMux

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth

def test_DataSelectMux_dbw32_clw128( dump_vcd, test_verilog ):
  CacheReqType, CacheRespType = mk_mem_msg(obw, abw, 32) 
  MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
  num_bytes = 32
  associativity = 1
  # cache model
  cache_params = CacheDerivedParams( CacheReqType, CacheRespType, MemReqType,
      MemRespType, num_bytes, associativity )
  # Check the correctness of different inputs
  test_vectors = [ (
      'in_',                              'out*',     'en', 'len_', 'offset' ),
    [  1,                                  0,          0,    0,      0  ], 
    [  1,                                  1,          1,    0,      0  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x76543210, 1,    0,      0b0000 ], 
    [  0x0123456789abcdeffedcba9876543210, 0xfedcba98, 1,    0,      0b0100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x89abcdef, 1,    0,      0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x01234567, 1,    0,      0b1100  ], 
  ]
  run_test_vector_sim( DataSelectMux(cache_params), test_vectors, dump_vcd, test_verilog )

def test_DataSelectMux_dbw128_clw128( dump_vcd, test_verilog ):
  CacheReqType, CacheRespType = mk_mem_msg(obw, abw, 128) 
  MemReqType, MemRespType = mk_mem_msg(obw, abw, 128)
  num_bytes = 32
  associativity = 1
  # cache model
  cache_params = CacheDerivedParams( CacheReqType, CacheRespType, MemReqType,
      MemRespType, num_bytes, associativity )
  # Check the correctness of different inputs
  test_vectors = [ (
      'in_',                              'out*',     'en', 'len_', 'offset' ),
    [  1,                                  0,          0,    0,      0  ], 
    [  1,                                  1,          1,    0,      0  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x0123456789abcdeffedcba9876543210, 1,    0,      0  ], 
  ]
  run_test_vector_sim( DataSelectMux(cache_params), test_vectors, dump_vcd, test_verilog )
