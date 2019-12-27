"""
=========================================================================
HypothesisTest.py
=========================================================================
Hypothesis test with cache

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 25 December 2019  Merry Christmas!!
"""

from pymtl3 import *
import random
import hypothesis
from hypothesis import strategies as st
from BlockingCache.BlockingCacheFL import ModelCache
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from mem_pclib.ifcs.ReqRespMsgTypes import ReqRespMsgTypes

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
max_cycles = 500
addr_min = 0
addr_max = 300 # 400 words

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
  addr = draw( st.integers(addr_min, addr_max), label="addr" )
  type_ = draw( st.integers(0, 1), label="type" )
  data = draw( st.integers(0, 0xffffffff), label="data" )
  return (addr,type_,data)

class CacheHypothesis_Tests:
  
  def hypothesis_test_harness(s, associativity, clw, cacheSize,
    transactions, req):
    if cacheSize < 2*clw*associativity:
      cacheSize = 2*clw*associativity
    mem = rand_mem(addr_min, addr_max)
    CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
    MemMsg = ReqRespMsgTypes(obw, abw, clw)
    # FL Model to generate expected transactions
    model = ModelCache(cacheSize, associativity, 0, \
      CacheMsg, MemMsg, mem)
    # Grab list of generated transactions
    reqs_lst = req.draw(
      st.lists( gen_reqs( ), min_size = 1, max_size=transactions ),
      label= "requests"
    )
    for i in range(len(reqs_lst)):
      addr, type_, data = reqs_lst[i]
      if type_ == MemMsgType.WRITE:
        model.write(addr & Bits32(0xfffffffc), data, i)
      else:
        # Read something
        model.read(addr & Bits32(0xfffffffc), i)
    msgs = model.get_transactions() # Get FL response
    # Prepare RTL test harness
    s.run_test(msgs, mem, CacheMsg, MemMsg, associativity, cacheSize)

  
  @hypothesis.settings( deadline = None, max_examples=150 )
  @hypothesis.given(
    clw           = st.sampled_from([64,128,256,512,1024]), #sample_from | pass in parameters
    cacheSize     = st.sampled_from([256,512,1024,4096,8192]),
    transactions  = st.integers( 1, 100 ),
    req           = st.data(), 
  )
  def test_hypothesis_2way(s, clw, cacheSize, transactions, req):
    s.hypothesis_test_harness(2, clw, cacheSize, transactions, req)
  
  @hypothesis.given(
    clw           = st.sampled_from([64,128,256,512,1024]), #sample_from | pass in parameters
    cacheSize     = st.sampled_from([128,256,512,1024,4096,8192]),
    transactions  = st.integers( 1, 100 ),
    req           = st.data(), 
  )
  def test_hypothesis_dmapped(s, clw, cacheSize, transactions, req):
    s.hypothesis_test_harness(1, clw, cacheSize, transactions, req)

  @hypothesis.settings( deadline = None, max_examples=150 )
  @hypothesis.given(
    clw           = st.sampled_from([64,128,256,512,1024]), #sample_from | pass in parameters
    cacheSize     = st.sampled_from([128,256,512,1024,4096,8192,16384,32768]),
    transactions  = st.integers( 1, 100 ),
    req           = st.data(), 
    associativity = st.sampled_from([1, 2]),
  )
  def test_hypothesis_cache_gen(s, clw, cacheSize, transactions, 
    req, associativity):
    s.hypothesis_test_harness(associativity, clw, cacheSize, \
      transactions, req)