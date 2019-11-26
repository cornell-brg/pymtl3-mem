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

test_idx = 1
failed = False

def setup_golden_model(mem, addr, types):
  model = ModelCache(cacheSize, 1, 0, clw, mem)
  for i in range(num_trans):
    if types[i] == 'wr':
      # Write something
      model.write(addr[i] & Bits32(0xfffffffc), data[i])
    else:
      # Read something
      model.read(addr[i] & Bits32(0xfffffffc))
  return model.get_transactions()

#-------------------------------------------------------------------------
# mk_src_pkts
#-------------------------------------------------------------------------

@st.composite
def gen_packets( draw, ncols, nrows ):
  src_x = draw( st.integers(0, ncols-1), label="src_x" )
  src_y = draw( st.integers(0, nrows-1), label="src_y" )
  dst_x = draw( st.integers(0, ncols-1), label="dst_x" )
  dst_y = draw( st.integers(0, nrows-1), label="dst_y" )
  payload = draw( st.sampled_from([ 0xdeadface, 0xfaceb00c, 0xdeadbabe ]) )
  Pkt = mk_mesh_pkt( ncols, nrows, vc=2 )
  return Pkt( src_x, src_y, dst_x, dst_y, 0, 0, payload )

@hypothesis.settings( deadline = None )
@hypothesis.given(
  clw           = st.integers(6,10), #sample_from | pass in parameters
  cacheSize     = st.integers(7,14),
  transactions  = st.integers( 1, 50 ),
  # n_tests       = st.integers( 1, 50 ),
  type_         = st.list(0, 1),
  data          = st.list(),
  addr          = st.list(),
)
def test_hypothesis(clw,cacheSize,transactions,rand_out_dir):
  global test_idx, failed
  if cacheSize < 2*clw:
    cacheSize = 2*clw
  # Instantiate testharness
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  max_cycles = 500
  addr_min = 0
  addr_max = 400 # 400 words
  
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
    print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
    curr_cyc += 1
  assert curr_cyc < max_cycles

  if not failed:
    test_idx += 1

