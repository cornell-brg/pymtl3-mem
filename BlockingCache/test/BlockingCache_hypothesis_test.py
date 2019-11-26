"""
=========================================================================
BlockingCache_hypothesis_test.py
=========================================================================
Hypothesis test with cache

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 24 November 2019
"""
from pymtl3 import *
import json
import hypothesis
from hypothesis import strategies as st
from BlockingCache.test.RandomTestCases import rand_mem, r
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes
from .ModelCache import ModelCache
from BlockingCache.test.BlockingCacheFL_test import TestHarness
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
test_idx = 1
failed = False

# def setup_golden_model(mem, addr, types):
#   model = ModelCache(cacheSize, 1, 0, clw, mem)
#   for i in range(num_trans):
#     if types[i] == 'wr':
#       # Write something
#       model.write(addr[i] & Bits32(0xfffffffc), data[i])
#     else:
#       # Read something
#       model.read(addr[i] & Bits32(0xfffffffc))
#   return model.get_transactions()

#-------------------------------------------------------------------------
# mk_src_pkts
#-------------------------------------------------------------------------
# def req( CacheMsg, type_, opaque, addr, len, data ):
#   if   type_ == 'rd': type_ = MemMsgType.READ
#   elif type_ == 'wr': type_ = MemMsgType.WRITE
#   elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
#   return CacheMsg.Req( type_, opaque, addr, len, data )
obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
max_cycles = 1000
addr_min = 0
addr_max = 400 # 400 words
@st.composite
def gen_reqs( draw):
  addr = draw( st.integers(addr_min, addr_max), label="addr" )
  type_ = draw( st.integers(0, 1), label="type" )
  data = draw( st.integers(0, 0xffffffff), label="data" )
  return (addr,type_,data)

@hypothesis.settings( deadline = None )
@hypothesis.given(
  clw           = st.sampled_from([64,128,256,512,1024]), #sample_from | pass in parameters
  cacheSize     = st.sampled_from([128,256,512,1024,4096,8192,16384]),
  transactions  = st.integers( 1, 100 ),
  # n_tests       = st.integers( 1, 50 ),
  req   = st.data(),
  # addr = st.integers(addr_min, addr_max),
  # type_ = st.integers(0, 1),
  # data =  st.integers(0, 0xffffffff), 
)
def test_hypothesis(clw,cacheSize,transactions,req,rand_out_dir):
  global test_idx, failed
  if cacheSize < 2*clw:
    cacheSize = 2*clw

  reqs_lst = req.draw(
      st.lists( gen_reqs( ), min_size = 1, max_size=transactions ),
      label= "pkts"
    )
  # print (cacheSize, clw)

  mem = rand_mem(addr_min, addr_max)
  model = ModelCache(cacheSize, 1, 0, clw, mem)
  for i in range(len(reqs_lst)):
    addr, type_, data = reqs_lst[i]
    if type_ == 1:
      model.write(addr & Bits32(0xfffffffc), data)
    else:
      # Read something
      model.read(addr & Bits32(0xfffffffc))
  msgs = model.get_transactions()
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  MemMsg = ReqRespMsgTypes(obw, abw, clw)
  harness = TestHarness(msgs[::2], msgs[1::2], \
  r(), 1, 0, 0, BlockingCachePRTL, cacheSize,\
    CacheMsg, MemMsg, 1)
  harness.elaborate()
  harness.load( mem[::2], mem[1::2] )
  resp = transactions
  harness.apply( DynamicSim )
  harness.sim_reset()
  curr_cyc = 0
  # print("")
  try:
    while not harness.done() and curr_cyc < max_cycles:
      harness.tick()
      # print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
      curr_cyc += 1
    assert curr_cyc < max_cycles
  except:
    # print ('FAILED')
    resp =  int(harness.sink.recv.msg.opaque)
    failed = True
  if not failed:
    test_idx += 1
  else:
    output = {"test":test_idx, "trans":resp, \
    "cacheSize":cacheSize, "clw":clw, "failed":failed}
    with open(f"{rand_out_dir}", 'w') as fd:
      json.dump(output,fd,sort_keys=True, \
        indent=2, separators=(',',':'))
    raise AssertionError

# print (test_idx)
