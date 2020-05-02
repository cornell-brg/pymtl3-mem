"""
=========================================================================
 RandomTestCases.py
=========================================================================
Random tests for various cache transactions and parameters

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 March 2020
"""

import random
import pytest

from pymtl3 import *

from test.sim_utils import (
  obw, abw, gen_req_resp, rand_mem, SingleCacheTestParams, mk_req
)
from mem_ifcs.MemMsg import mk_mem_msg, MemMsgType

from constants.constants import *

random.seed(0xdeadbeef) # randomness
def iterative_mem( start, end ):
  mem = []
  curr_addr = start
  while curr_addr <= end:
    mem.append(curr_addr)
    mem.append(curr_addr)
    curr_addr += 4
  return mem
random_memory = rand_mem( 0, 0xffff )
# iterative_memory = iterative_mem( 0, 0xffff )

def random_test_generator( mem, associativity, bitwidth_mem_data, bitwidth_cache_data, 
                           size, num_trans = 200 ):
  tp = SingleCacheTestParams( False, mem, associativity, bitwidth_mem_data, 
                              bitwidth_cache_data, size )
  max_addr = int( size // 4 * 3 * tp.associativity )
  type_choices = [ (MemMsgType.READ,     0.43) ,
                   (MemMsgType.WRITE,    0.43),
                   (MemMsgType.AMO_ADD,  0.02),
                   (MemMsgType.AMO_AND,  0.01),
                   (MemMsgType.AMO_OR,   0.01),
                   (MemMsgType.AMO_SWAP, 0.01),
                   (MemMsgType.AMO_MIN,  0.01),
                   (MemMsgType.AMO_MINU, 0.01),
                   (MemMsgType.AMO_MAX,  0.01),
                   (MemMsgType.AMO_MAXU, 0.01),
                   (MemMsgType.AMO_XOR,  0.01),
                   (MemMsgType.INV,      0.02),
                   (MemMsgType.FLUSH,    0.02),
                   ]
  types = random.choices(
      population = [ choices for choices,weights in type_choices ],
      weights = [ weights for choices,weights in type_choices ],
      k = num_trans )
  reqs = []
  for i in range( num_trans ):
    if types[i] == MemMsgType.INV or types[i] == MemMsgType.FLUSH:
      data = 0
      len_ = 0
      addr = 0
    else:
      data = random.randint(0, 0xffffffff)
      addr = Bits32(random.randint(0, max_addr))
      if types[i] >= MemMsgType.AMO_ADD and types[i] <= MemMsgType.AMO_XOR:
        len_ = 0 if bitwidth_cache_data == 32 else 4
        addr = addr & 0xfffffffc
      else:
        max_len_order = clog2( bitwidth_cache_data//8 )
        BitsLen = mk_bits( max_len_order )
        if types[i] == MemMsgType.WRITE:
          max_len_order = 2
        len_order = random.randint( 0, max_len_order )
        len_ = 2**len_order
        if len_ == 2:
          addr = addr & Bits32(0xfffffffe)
        elif len_ == 4:
          addr = addr & Bits32(0xfffffffc)
        elif len_ == 8:
          addr = addr & Bits32(0xfffffff8)
        elif len_ == 16:
          addr = addr & Bits32(0xfffffff0)
        elif len_ == 32:
          addr = addr & Bits32(0xffffffe0)
        
    reqs.append( ( types[i], i, addr, len_, data) )  
  reqs = mk_req( tp.CacheReqType, reqs )

  tp.msg = gen_req_resp( reqs, tp.mem, tp.CacheReqType, tp.CacheRespType, tp.MemReqType,
                        tp.MemRespType, tp.associativity, tp.size )
  # print stats
  hits = 0
  for i in range( 1, num_trans, 2 ):
    if tp.msg[i].test:
      hits += 1
  print( f"\nhit rate:{hits/num_trans}\n")

  return tp

def dmap_size16_lineb64_datab32():
  return random_test_generator(random_memory, 1, 64, 32, 16, 500)

def dmap_size32_lineb128_datab64():
  return random_test_generator(random_memory, 1, 128, 64, 32, 500)

def dmap_size32_lineb128_datab128():
  return random_test_generator(random_memory, 1, 128, 128, 32, 500)

def asso2_size32_lineb64_datab32():
  return random_test_generator(random_memory, 2, 64, 32, 32, 500)

def asso2_size64_lineb128_datab128():
  return random_test_generator(random_memory, 2, 128, 128, 64, 500)

def asso2_size4096_lineb128_datab128():
  return random_test_generator(random_memory, 2, 128, 128, 4096, 100)

def asso2_size4096_lineb128_datab32():
  return random_test_generator(random_memory, 2, 128, 32, 4096, 100)

#-------------------------------------------------------------------------
# Test driver
#-------------------------------------------------------------------------

class RandomTests:
  @pytest.mark.parametrize(
    " name,  test,                            stall_prob,latency,src_delay,sink_delay", [
    ("16B",  dmap_size16_lineb64_datab32,     0,         1,      0,        0   ),
    ("32B",  dmap_size32_lineb128_datab64,    0,         1,      0,        0   ),
    ("32B",  dmap_size32_lineb128_datab128,   0,         1,      0,        0   ),
    ("32B",  asso2_size32_lineb64_datab32,    0,         1,      0,        0   ),
    ("64B",  asso2_size64_lineb128_datab128,  0,         1,      0,        0   ),
    ("4KB",  asso2_size4096_lineb128_datab128,0,         1,      0,        0   ),
    ("4KB",  asso2_size4096_lineb128_datab32, 0,         1,      0,        0   ),
    ("16B",  dmap_size16_lineb64_datab32,     0,         2,      1,        2   ),
    ("32B",  dmap_size32_lineb128_datab64,    0,         2,      1,        2   ),
    ("32B",  dmap_size32_lineb128_datab128,   0,         2,      1,        2   ),
    ("32B",  asso2_size32_lineb64_datab32,    0,         2,      1,        2   ),
    ("64B",  asso2_size64_lineb128_datab128,  0,         2,      1,        2   ),
    ("4KB",  asso2_size4096_lineb128_datab128,0,         2,      1,        2   ),
    ("4KB",  asso2_size4096_lineb128_datab32, 0,         2,      1,        2   ),
  ])
  def test_random( s, name, test, dump_vcd, test_verilog, max_cycles,
                   stall_prob, latency, src_delay, sink_delay, dump_vtb ):
    p = test()
    s.run_test( p.msg, p.mem, p.CacheReqType, p.CacheRespType, p.MemReqType, p.MemRespType, 
                p.associativity, p.size, stall_prob, latency, src_delay, sink_delay, dump_vcd,
                test_verilog, max_cycles, dump_vtb )
