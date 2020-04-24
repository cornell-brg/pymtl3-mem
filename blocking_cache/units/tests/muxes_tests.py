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
      'in_',                              'out*',     'en', 'amo', 'len_', 'offset' ),
    [  1,                                  0,          0,    0,     0,      0  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x76543210, 1,    0,     0,      0b0000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xfedcba98, 1,    0,     0,      0b0100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x89abcdef, 1,    0,     0,      0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x01234567, 1,    0,     0,      0b1100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x0000cdef, 1,    0,     2,      0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x000089ab, 1,    0,     2,      0b1010  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x00000067, 1,    0,     1,      0b1100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x00000045, 1,    0,     1,      0b1101  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x00000023, 1,    0,     1,      0b1110  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x00000001, 1,    0,     1,      0b1111  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x76543210, 1,    1,     1,      0b1111  ], 
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
      'in_',                              'out*',     'en', 'amo', 'len_', 'offset' ),
    [  1,                                  0,          0,    0,     0,      0  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x0123456789abcdeffedcba9876543210, 0,  1,  0,      0  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x0123456789abcdeffedcba9876543210, 1,  0,  0,      0  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xfedcba9876543210, 1,    0,     0x8,    0b0000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x0123456789abcdef, 1,    0,     0x8,    0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x76543210, 1,    0,     0x4,    0b0000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xfedcba98, 1,    0,     0x4,    0b0100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x89abcdef, 1,    0,     0x4,    0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x01234567, 1,    0,     0x4,    0b1100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x3210,     1,    0,     0x2,    0b0000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x7654,     1,    0,     0x2,    0b0010  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xba98,     1,    0,     0x2,    0b0100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xfedc,     1,    0,     0x2,    0b0110  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xcdef,     1,    0,     0x2,    0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x89ab,     1,    0,     0x2,    0b1010  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x4567,     1,    0,     0x2,    0b1100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x0123,     1,    0,     0x2,    0b1110  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x10,       1,    0,     0x1,    0b0000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x32,       1,    0,     0x1,    0b0001  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x54,       1,    0,     0x1,    0b0010  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x76,       1,    0,     0x1,    0b0011  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x98,       1,    0,     0x1,    0b0100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xba,       1,    0,     0x1,    0b0101  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xdc,       1,    0,     0x1,    0b0110  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xfe,       1,    0,     0x1,    0b0111  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xef,       1,    0,     0x1,    0b1000  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xcd,       1,    0,     0x1,    0b1001  ], 
    [  0x0123456789abcdeffedcba9876543210, 0xab,       1,    0,     0x1,    0b1010  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x89,       1,    0,     0x1,    0b1011  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x67,       1,    0,     0x1,    0b1100  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x45,       1,    0,     0x1,    0b1101  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x23,       1,    0,     0x1,    0b1110  ], 
    [  0x0123456789abcdeffedcba9876543210, 0x01,       1,    0,     0x1,    0b1111  ], 
  ]
  run_test_vector_sim( DataSelectMux(cache_params), test_vectors, dump_vcd, test_verilog )
