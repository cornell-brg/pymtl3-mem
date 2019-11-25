"""
=========================================================================
BlockingCache_hypothesis_test.py
=========================================================================
Hypothesis test with cache

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 24 November 2019
"""
from pymtl3 import *
import Hypothesis
from hypothesis import strategies as st
from BlockingCache.test.RandomTestCases import rand_mem
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes

def setup_golden_model(mem, addr):
  

@hypothesis.settings( deadline = None )
@hypothesis.given(
  clw           = st.integers().filter(lambda x: ),
  cacheSize     = st.integers(),
  transactions  = st.integers( 1, 50 ),
  # n_tests       = st.integers( 1, 50 ),
  type_         = st.integers(0, 1),
  data          = st.list(),
  addr          = st.list(),
)
def test_hypothesis(clw,cacheSize,transactions,rand_out_dir):
  # Instantiate testharness
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  max_cycles = 500
  addr_min = 
  addr_max = 400 # 100 words
  test_num = 0
  failed = False
  test_num += 1
  mem = rand_mem(addr_min, addr_max)
  msgs = setup_golden_model(mem, addr,\
    cacheSize,clw)
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  MemMsg = ReqRespMsgTypes(obw, abw, clw)
  harness = TestHarness(msgs[::2], msgs[1::2], \
  0, 1, 0, 0, BlockingCachePRTL, cacheSize,\
    CacheMsg, MemMsg, 1)
  harness.elaborate()
  harness.load( mem[::2], mem[1::2] )
  resp = num_trans
  harness.apply( DynamicSim )
  harness.sim_reset()
  curr_cyc = 0
  # print("")
  while not harness.done() and curr_cyc < max_cycles:
    harness.tick()
    # print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
    curr_cyc += 1
  assert curr_cyc < max_cycles


