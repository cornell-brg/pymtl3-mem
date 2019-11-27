"""
=========================================================================
BlockingCache_iterdeepen_test.py
=========================================================================
Random test with iterative deepening to find bugs

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 22 November 2019
"""

import json
import time
from pymtl3 import *

from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from .ModelCache import ModelCache
from BlockingCache.test.RandomTestCases import rand_mem, \
  generate_data, generate_type, generate_address, r, l
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
  start_time = time.monotonic()
  time_limit_reached = False
  
  # Instantiate testharness
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  addr_min = 0
  addr_max = 400 # 100 words
  test_num = 0
  failed = False
  clw_arr       = [2**(6+i) for i in range(5)] # minimum cacheline size is 64 bits
  cacheSize_arr = [i+1      for i in range(7)] #minimum cacheSize is 2 times clw
  ntests_per_step = 5      # 10
  max_transaction_len = 100 #100
  
  for i in range(len(clw_arr)):
    curr_clw = clw_arr[i]
    for j in range(i, len(cacheSize_arr)):
      curr_cacheSize = 2**cacheSize_arr[j]*curr_clw
      for num_trans in range(1,max_transaction_len):
        for test_number in range(ntests_per_step):
          if (time.monotonic() - start_time) > 54000:
            time_limit_reached = True
          test_complexity = 0
          avg_addr = 0
          avg_data = 0
          avg_type = 0
          test_num += 1
          mem = rand_mem(addr_min, addr_max)
          # Setup Golden Model
          model = ModelCache(curr_cacheSize, 1, 0, curr_clw, mem)
          data  = generate_data(num_trans)
          types = generate_type(num_trans)
          addr  = generate_address(num_trans,addr_min,addr_max)
          for i in range(num_trans):
            avg_addr += addr[i]
            avg_data += data[i]
            if types[i] == 'wr':
              test_complexity = test_complexity + 1 + addr[i] + data[i]
              # Write something
              model.write(addr[i] & Bits32(0xfffffffc), data[i])
              avg_type += 1
            else:
              test_complexity = test_complexity + addr[i] + data[i]
              # Read something
              model.read(addr[i] & Bits32(0xfffffffc))
          test_complexity /= num_trans
          avg_type /= num_trans
          avg_addr /= num_trans
          avg_data /= num_trans
          msgs = model.get_transactions()
          
          CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
          MemMsg = ReqRespMsgTypes(obw, abw, curr_clw)
          harness = TestHarness(msgs[::2], msgs[1::2], \
            0, 2, 2, 2, BlockingCachePRTL, curr_cacheSize,\
              CacheMsg, MemMsg, 1)

          harness.elaborate()
          harness.load( mem[::2], mem[1::2] )
          resp = num_trans
          harness.apply( DynamicSim )

          harness.sim_reset()
          curr_cyc = 0
          try:
            print("")
            while not harness.done() and curr_cyc < max_cycles:
              harness.tick()
              print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
              curr_cyc += 1
              
            assert curr_cyc < max_cycles and not time_limit_reached
          except:
            failed = True
            # print ('FAILED')
            if int(harness.sink.recv.msg.opaque) == 0:
              resp = num_trans
            else:
              resp =  int(harness.sink.recv.msg.opaque)
            
              output = {"test":test_num, "trans":resp, \
              "cacheSize":curr_cacheSize, "clw":curr_clw, "failed":failed,\
                "timeOut":time_limit_reached, \
                  "testComplexity": test_complexity, "avg_addr": avg_addr, \
                    "avg_data": avg_data, "avg_type": avg_type }
            with open("{}".format(rand_out_dir)\
                , 'w') as fd:
              json.dump(output,fd,sort_keys=True, \
                indent=2, separators=(',',':'))
            return #exits instantly

  output = {"test":test_num, "trans":resp, \
  "cacheSize":curr_cacheSize, "clw":curr_clw, "failed":failed,\
    "timeOut":time_limit_reached, \
      "testComplexity": test_complexity, "avg_addr": avg_addr, \
        "avg_data": avg_data, "avg_type": avg_type }
  with open("{}".format(rand_out_dir)\
      , 'w') as fd:
    json.dump(output,fd,sort_keys=True, \
      indent=2, separators=(',',':'))
          

          
          


