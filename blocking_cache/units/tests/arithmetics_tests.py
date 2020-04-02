"""
=========================================================================
arithmetrics_tests.py
=========================================================================
Tests some cache dpath moduels

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 26 March 2020
"""

from pymtl3 import *
from pymtl3.stdlib.test.test_utils import run_test_vector_sim

from ifcs.MemMsg import MemMsgType, mk_mem_msg

from constants.constants import *
from blocking_cache.CacheDerivedParams  import CacheDerivedParams

from ..arithmetics import *

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

def test_replicator( dump_vcd, test_verilog, max_cycles ):
  replicator_header_str = ( "msg_len", "data", "is_amo", "offset", "out*" )
  test_vectors = [ replicator_header_str,
    # msg_len|data    |is_amo|offset|out*
    [  0,     0xabcd,  0,     0,     0x0000abcd0000abcd0000abcd0000abcd ],
    [  0,     0xabcd,  0,     0,     0x0000abcd0000abcd0000abcd0000abcd ],
    [  1,     0xab,    0,     0x4,   0xabababababababababababababababab ],
    [  1,     0xab,    0,     0x4,   0xabababababababababababababababab ],
    [  2,     0xabcd,  0,     0x4,   0xabcdabcdabcdabcdabcdabcdabcdabcd ],
    [  2,     0xabcd,  0,     0x4,   0xabcdabcdabcdabcdabcdabcdabcdabcd ],
    [  0,     0xabcd,  1,     0,     0x0000000000000000000000000000abcd ],
    [  0,     0xabcd,  1,     4,     0x0000000000000000000000000000abcd ],
    [  0,     0xabcd,  1,     8,     0x0000000000000000000000000000abcd ],
    [  0,     0xabcd,  1,     0xc,   0x0000000000000000000000000000abcd ],
  ]
  run_test_vector_sim( CacheDataReplicator(cache_params), test_vectors, dump_vcd, test_verilog )

def test_WriteMaskSelector( dump_vcd, test_verilog, max_cycles ):
  replicator_header_str = ( "in_", "out*", "is_amo", "offset", "en" )
  test_vectors = [ replicator_header_str,
    # in_|out*    |is_amo |offset|en
    [  1, 0,       0,      0,     1 ],
    [  0, 1,       0,      0,     1 ],
    [  0, 0b1,     1,      0x0,   1 ],
    [  0, 0b10,    1,      0x4,   1 ],
    [  0, 0b100,   1,      0x8,   1 ],
    [  0, 0b1000,  1,      0xc,   1 ],
  ]
  run_test_vector_sim( WriteMaskSelector(cache_params), test_vectors, dump_vcd, test_verilog, max_cycles )
