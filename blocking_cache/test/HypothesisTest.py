"""
=========================================================================
HypothesisTest.py
=========================================================================
Hypothesis test with cache
Now with Latencies!!

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 25 December 2019  Merry Christmas!! UWU
"""

from pymtl3 import *
import random
import hypothesis
from hypothesis import strategies as st
from blocking_cache.BlockingCacheFL import ModelCache
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg as mk_cache_msg
# cifer specific memory req/resp msg
from mem_pclib.ifcs.MemMsg     import mk_mem_msg 


obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
max_cycles = 500
addr_min = 0
addr_max = 200 # 4-byte words

def rand_mem(addr_min=0, addr_max=0xfff):
  '''
  Randomly generate start state for memory
  :returns: list of memory addresses w/ random data values
  '''
  mem = []
  curr_addr = addr_min
  while curr_addr <= addr_max:
    mem.append(curr_addr)
    mem.append(random.randint(0,0xffffffff))
    curr_addr += 4
  return mem

@st.composite
def gen_reqs( draw ):
  len_ = draw( st.integers(0, 2), label="len" )
  addr = draw( st.integers(addr_min, addr_max), label="addr" )
  type_ = draw( st.integers(0, 1), label="type" )
  data = draw( st.integers(0, 0xffffffff), label="data" )
  if len_ == 0:
    addr = addr & Bits32(0xfffffffc)
  elif len_ == 1:
    addr = addr & Bits32(0xffffffff)
  elif len_ == 2:
    addr = addr & Bits32(0xfffffffe)
  else:
    addr = addr & Bits32(0xfffffffc)

  return (addr, type_, data, len_)

class HypothesisTests:

  def hypothesis_test_harness(s, associativity, clw, num_blocks, transactions, 
  req, stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog):
    cacheSize = (clw * associativity * num_blocks) // 8
    mem = rand_mem(addr_min, addr_max)
    CacheReqType, CacheRespType = mk_cache_msg(obw, abw, dbw)
    MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)
    # FL Model to generate expected transactions
    model = ModelCache(cacheSize, associativity, 0, CacheReqType, CacheRespType,
     MemReqType, MemRespType, mem)
    # Grab list of generated transactions
    reqs_lst = req.draw(
      st.lists( gen_reqs( ), min_size = 1, max_size=transactions ),
      label= "requests"
    )
    for i in range(len(reqs_lst)):
      addr, type_, data, len_ = reqs_lst[i]
      if type_ == MemMsgType.WRITE:
        model.write(addr, data, i, len_)
      else:
        # Read something
        model.read(addr, i, len_)
    msgs = model.get_transactions() # Get FL response
    # Prepare RTL test harness
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
     associativity, cacheSize, stall_prob, latency, src_delay, sink_delay,
     dump_vcd, test_verilog, 1)

  @hypothesis.settings( deadline = None, max_examples=100 )
  @hypothesis.given(
    clw          = st.sampled_from([64,128,256]),
    block_order  = st.integers( 1, 7 ), 
    transactions = st.integers( 1, 100 ),
    req          = st.data(),
    stall_prob   = st.integers( 0, 1 ),
    latency      = st.integers( 1, 5 ),
    src_delay    = st.integers( 0, 5 ),
    sink_delay   = st.integers( 0, 5 )
  )
  def test_hypothesis_2way(s, clw, block_order, transactions, req,
    stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog):
    num_blocks = 2**block_order
    s.hypothesis_test_harness(2, clw, num_blocks, transactions, req, stall_prob,
    latency, src_delay, sink_delay, dump_vcd, test_verilog)

  @hypothesis.settings( deadline = None, max_examples=100 )
  @hypothesis.given(
    clw          = st.sampled_from([64,128,256]),
    block_order  = st.integers( 1, 7 ), # order of number of blocks based 2
    transactions = st.integers( 1, 100 ), 
    req          = st.data(),
    stall_prob   = st.integers( 0, 1 ),
    latency      = st.integers( 1, 5 ),
    src_delay    = st.integers( 0, 5 ),
    sink_delay   = st.integers( 0, 5 )
  )
  def test_hypothesis_dmapped(s, clw, block_order, transactions, req,
    stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog):
    num_blocks = 2**block_order
    s.hypothesis_test_harness(1, clw, num_blocks, transactions, req, stall_prob,
    latency, src_delay, sink_delay, dump_vcd, test_verilog)

  @hypothesis.settings( deadline = None, max_examples=100 )
  @hypothesis.given(
    clw           = st.sampled_from([64,128,256]),
    block_order  = st.integers( 1, 7 ), # order of number of blocks based 2
    transactions  = st.integers( 1, 200 ),
    req           = st.data(),
    associativity = st.sampled_from([1, 2]),
    stall_prob    = st.integers( 0, 1 ),
    latency       = st.integers( 1, 5 ),
    src_delay     = st.integers( 0, 5 ),
    sink_delay    = st.integers( 0, 5 )
  )
  def test_hypothesis_cache_gen(s, clw, block_order, transactions,
    req, associativity, stall_prob, latency, src_delay, sink_delay, dump_vcd, 
    test_verilog):
    num_blocks = 2**block_order
    s.hypothesis_test_harness(associativity, clw, num_blocks, transactions, req,
    stall_prob, latency, src_delay, sink_delay, dump_vcd, test_verilog)
