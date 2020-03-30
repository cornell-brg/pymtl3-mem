"""
=========================================================================
arithmetrics_tests.py
=========================================================================
Tests some cache dpath moduels

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 26 March 2020
"""

from pymtl3      import *
from mem_pclib.rtl.arithmetics import *
from pymtl3.stdlib.test.test_utils import run_test_vector_sim
from blocking_cache.CacheDerivedParams  import CacheDerivedParams
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg
from mem_pclib.constants.constants import *

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

def test_replicator( dump_vcd, test_verilog ):
  replicator_header_str = ( "msg_len", "data", "type_", "offset", "out*" )
  test_vectors = [ replicator_header_str,
    # msg_len|data       |type_ |offset|out*
    [  0,     0xabcd,     READ,  0,     0x0000abcd0000abcd0000abcd0000abcd ], 
    [  0,     0xabcd,     WRITE, 0,     0x0000abcd0000abcd0000abcd0000abcd ], 
    [  0,     0xabcd,     AMO,   0,     0x0000000000000000000000000000abcd ], 
    [  1,     0xab,       READ,  0x4,   0xabababababababababababababababab ], 
    [  1,     0xab,       WRITE, 0x4,   0xabababababababababababababababab ], 
    [  2,     0xabcd,     READ,  0x4,   0xabcdabcdabcdabcdabcdabcdabcdabcd ], 
    [  2,     0xabcd,     WRITE, 0x4,   0xabcdabcdabcdabcdabcdabcdabcdabcd ], 
    [  0,     0xabcdef01, AMO,   0x4,   0x0000000000000000abcdef0100000000 ], 
    [  0,     0xabcdef01, AMO,   0x8,   0x00000000abcdef010000000000000000 ], 
    [  0,     0xabcdef01, AMO,   0xc,   0xabcdef01000000000000000000000000 ], 
  ]
  run_test_vector_sim( CacheDataReplicator(cache_params), test_vectors, dump_vcd, test_verilog )
