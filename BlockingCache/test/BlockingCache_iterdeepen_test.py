"""
=========================================================================
BlockingCache_iterdeepen_test.py
=========================================================================
Random test with iterative deepening to find bugs

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 22 November 2019
"""

import json
from pymtl3 import *

from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from .ModelCache import ModelCache
from BlockingCache.test.RandomTestCases import rand_mem, \
  generate_data, generate_type, generate_address, r
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes
from BlockingCache.test.BlockingCacheFL_test import TestHarness

#-------------------------------------------------------------------------
# setup_golden_model
#-------------------------------------------------------------------------
def setup_golden_model(mem, addr_min, addr_max, num_trans, cacheSize, clw ):
  model = ModelCache(cacheSize, 1, 0, clw, mem)
  data  = generate_data(num_trans)
  types = generate_type(num_trans)
  addr  = generate_address(num_trans,addr_min,addr_max)
  for i in range(num_trans):
    if types[i] == 'wr':
      # Write something
      model.write(addr[i] & Bits32(0xfffffffc), data[i])
    else:
      # Read something
      model.read(addr[i] & Bits32(0xfffffffc))
  # print (model.get_transactions())
  return model.get_transactions()

#-------------------------------------------------------------------------
# run_test
#-------------------------------------------------------------------------
max_cycles = 1000

def test_iter_deepen(rand_out_dir):
  # Instantiate testharness
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  addr_min = 0
  addr_max = 400 # 100 words
  test_num = 0
  failed = False
  clw_arr       = [2**(6+i) for i in range(5)] # minimum cacheline size is 64 bits
  cacheSize_arr = [2**(7+i) for i in range(7)] #minimum cacheSize is 2 times clw
  ntests_per_step = 10      # 10
  max_transaction_len = 100 #100
  try:
    for i in range(len(clw_arr)):
      curr_clw = clw_arr[i]
      for j in range(i, len(cacheSize_arr)):
        curr_cacheSize = cacheSize_arr[j]
        print(f"clw[{clw_arr[i]}] size[{cacheSize_arr[j]}]")
        for num_trans in range(1,max_transaction_len):
          for test_number in range(ntests_per_step):
            test_num += 1
            mem = rand_mem(addr_min, addr_max)
            msgs = setup_golden_model(mem, addr_min,addr_max,\
              num_trans,cacheSize_arr[j],clw_arr[i])
            
            CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
            MemMsg = ReqRespMsgTypes(obw, abw, clw_arr[i])
            harness = TestHarness(msgs[::2], msgs[1::2], \
              r(), 1, 0, 0, BlockingCachePRTL, cacheSize_arr[j],\
                CacheMsg, MemMsg, 1)

            harness.elaborate()
            harness.load( mem[::2], mem[1::2] )
            resp = num_trans
            harness.apply( DynamicSim )
            harness.sim_reset()
            curr_cyc = 0
            try:
              # print("")
              while not harness.done() and curr_cyc < max_cycles:
                harness.tick()
                print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
                curr_cyc += 1
              assert curr_cyc < max_cycles
            except:
              # print ('FAILED')
              if int(harness.sink.recv.msg.opaque) == 0:
                resp = num_trans
              else:
                resp =  int(harness.sink.recv.msg.opaque)
              
              failed = True
              assert not failed
            
  except:
    pass
  output = {"test":test_num, "trans":resp, \
    "cacheSize":curr_cacheSize, "clw":curr_clw, "failed":failed}
  with open("{}".format(rand_out_dir)\
      , 'w') as fd:
    json.dump(output,fd,sort_keys=True, \
      indent=2, separators=(',',':'))
          
          


