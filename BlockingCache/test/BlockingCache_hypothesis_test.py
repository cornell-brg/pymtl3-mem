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
import random
import hypothesis
import time
from hypothesis import strategies as st
from BlockingCache.test.RandomTestCases import rand_mem, r, l
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes
from .ModelCache import ModelCache
from BlockingCache.test.BlockingCacheFL_test import TestHarness
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL

start_time = time.monotonic()
time_limit_reached = False
test_idx = 1
failed = False

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
  req   = st.data(), 
)
def test_hypothesis(clw,cacheSize,transactions,req,rand_out_dir):
  global test_idx, failed, time_limit_reached
  test_complexity = 0
  avg_addr = 0
  avg_data = 0
  avg_type = 0
  if cacheSize < 2*clw:
    cacheSize = 2*clw

  reqs_lst = req.draw(
      st.lists( gen_reqs( ), min_size = 1, max_size=transactions ),
      label= "requests"
    )
  mem = rand_mem(addr_min, addr_max)
  model = ModelCache(cacheSize, 1, 0, clw, mem)
  for i in range(len(reqs_lst)):
    addr, type_, data = reqs_lst[i]
    avg_addr += addr
    avg_data += data
    avg_type += type_
    test_complexity = test_complexity + addr + type_ + data
    if type_ == 1:
      model.write(addr & Bits32(0xfffffffc), data)
    else:
      # Read something
      model.read(addr & Bits32(0xfffffffc))
  test_complexity /= transactions
  avg_addr /= transactions
  avg_data /= transactions
  avg_type /= transactions
  msgs = model.get_transactions()
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  MemMsg = ReqRespMsgTypes(obw, abw, clw)
  harness = TestHarness(msgs[::2], msgs[1::2], \
  0, 2, 2, 2, BlockingCachePRTL, cacheSize,\
    CacheMsg, MemMsg, 1)
  harness.elaborate()
  harness.load( mem[::2], mem[1::2] )
  resp = transactions
  harness.apply( DynamicSim )
  local_failed = False
  if (time.monotonic() - start_time) > 54000:
    time_limit_reached = True
    failed = True
    assert False
  try:
    harness.sim_reset()
  except:
    failed = True
    local_failed = True
  curr_cyc = 0
  print("")
  while not harness.done() and curr_cyc < max_cycles:
    try:
      harness.tick()
      print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
    except:
      failed = True
      local_failed = True
      print ('FAILED')
      # if int(harness.sink.recv.msg.opaque) == 0:
      #   resp = transactions
      # else:
      #   resp = int(harness.sink.recv.msg.opaque)
      break
    curr_cyc += 1
  if local_failed or curr_cyc >= max_cycles:
    failed = True
    output = {"test":test_idx, "trans":resp, \
    "cacheSize":cacheSize, "clw":clw, "failed":failed,\
      "timeOut":time_limit_reached, \
        "testComplexity": test_complexity, "avg_addr": avg_addr, \
          "avg_data": avg_data, "avg_type": avg_type }
    with open(f"{rand_out_dir}", 'w') as fd:
      json.dump(output,fd,sort_keys=True, \
        indent=2, separators=(',',':'))
    raise AssertionError

  if not failed:
    test_idx += 1
    # raise AssertionError
# print (test_idx)
