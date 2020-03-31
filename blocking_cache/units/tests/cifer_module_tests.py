"""
=========================================================================
cifer_tests.py
=========================================================================
Testbench for cifer functions

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 23 March 2020
"""

from pymtl3      import *
from mem_pclib.rtl.cifer import *
from pymtl3.stdlib.test.test_utils import run_test_vector_sim
from blocking_cache.CacheDerivedParams  import CacheDerivedParams
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128 # cacheline bitwidth

CacheReqType, CacheRespType = mk_mem_msg(obw, abw, dbw)
MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)
num_bytes = 32
associativity = 1

cache_params = CacheDerivedParams( CacheReqType, CacheRespType, MemReqType, 
    MemRespType, num_bytes, associativity )


#-----------------------------------------------------------------------
# DirtyLineDetector Tests
#-----------------------------------------------------------------------

dirtyLineDetector_header_str = \
  ( "is_hit", "offset", "dirty_bits", "is_dirty*" )

def test_DirtyLineDetector( dump_vcd, test_verilog ):
  # Check the correctness of different inputs
  test_vectors = [ dirtyLineDetector_header_str,
    # is_hit,offset,dirty_bits,is_dirty*
    [    1  ,  0   ,  0b0000  ,  0  ], # hit tests with no dirty
    [    1  ,  0   ,  0b0001  ,  1  ],
    [    1  ,  4   ,  0b0010  ,  1  ],
    [    1  ,  8   ,  0b0100  ,  1  ],
    [    1  ,  12  ,  0b1000  ,  1  ], 
    [    0  ,  12  ,  0b0000  ,  0  ], # miss which just checks for 1 hot
    [    0  ,  12  ,  0b0111  ,  1  ],
    [    0  ,  12  ,  0b0001  ,  1  ],
  ]
  run_test_vector_sim( DirtyLineDetector(cache_params), test_vectors, dump_vcd, test_verilog )

#-----------------------------------------------------------------------
# DirtyBitWriter Tests
#-----------------------------------------------------------------------

DirtyBitWriter_dmapped_header_str = ( "offset", "dirty_bit[0]", "hit_way", \
  "is_write_refill", "is_write_hit_clean", "out*" )

def test_DirtyBitWriter_dmapped( dump_vcd, test_verilog ):
  test_vectors = [ DirtyBitWriter_dmapped_header_str,
    # offset,dirty_bit,hit_way,is_write_refill,is_write_hit_clean,out
    [    0  , 0b0000  ,      0,       0       ,               0  , 0      ], # dmapped cache
    [    0  , 0b0000  ,      0,       0       ,               1  , 0b0001 ], 
    [    0  , 0b0010  ,      0,       0       ,               1  , 0b0011 ], # other bits 
    [    4  , 0b0100  ,      0,       0       ,               1  , 0b0110 ], 
    [    0  , 0b0000  ,      0,       1       ,               0  , 0b0001 ], 
    [    4  , 0b0001  ,      0,       1       ,               0  , 0b0010 ], 
    [    8  , 0b0011  ,      0,       1       ,               0  , 0b0100 ], 
    [    12 , 0b0000  ,      0,       1       ,               0  , 0b1000 ], 
  ]
  run_test_vector_sim( DirtyBitWriter(cache_params), test_vectors, dump_vcd, test_verilog )

DirtyBitWriter_asso_header_str = ( "offset", "dirty_bit[0]", "dirty_bit[1]",\
   "hit_way", "is_write_refill", "is_write_hit_clean", "out*" )

def test_DirtyBitWriter_2wayAssoc( dump_vcd, test_verilog ):
  test_vectors = [ DirtyBitWriter_asso_header_str,
    # offset,dirty_bit[0],dirty_bit[1],hit_way,is_write_refill,is_write_hit_clean,out
    [    0  , 0b0000     ,      0b0000,      0,       0       ,               0  , 0      ], # dmapped cache
    [    0  , 0b0000     ,      0b0000,      0,       0       ,               1  , 0b0001 ], 
    [    0  , 0b0010     ,      0b0000,      0,       0       ,               1  , 0b0011 ], # other bits 
    [    4  , 0b0100     ,      0b0000,      0,       0       ,               1  , 0b0110 ], 
    [    0  , 0b0000     ,      0b0000,      0,       1       ,               0  , 0b0001 ], 
    [    4  , 0b0001     ,      0b0000,      0,       1       ,               0  , 0b0010 ], 
    [    8  , 0b0011     ,      0b0000,      0,       1       ,               0  , 0b0100 ], 
    [    12 , 0b0000     ,      0b0000,      0,       1       ,               0  , 0b1000 ], 
  ]
  associativity = 2
  cache_params = CacheDerivedParams( CacheReqType, CacheRespType, MemReqType, 
    MemRespType, num_bytes, associativity )
  run_test_vector_sim( DirtyBitWriter(cache_params), test_vectors, dump_vcd, test_verilog )
