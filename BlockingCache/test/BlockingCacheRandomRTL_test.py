"""
=========================================================================
 BlockingCacheRandomRTL_test.py
=========================================================================
Random Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 18 November 2019
"""

import pytest
import time
import json
import random
from pymtl3      import *
from BlockingCache.test.BlockingCacheFL_test import TestHarness
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.RandomTestCases import complete_random_test, rand_mem,\
generate_data, generate_type, generate_address
from .ModelCache import ModelCache
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes


base_addr = 0x0
max_cycles = 1000

#-------------------------------------------------------------------------
# Complete random testing
#-------------------------------------------------------------------------

def test_complete_random(rand_out_dir):
  start_time = time.monotonic()
  time_limit_reached = False
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  addr_min = 0
  addr_max = 400 # 100 words
  fail_test = 0
  failed = False
  ntests_per_step = 100
  # print(f"clw[{clw}] size[{cacheSize}]")

  for i in range(ntests_per_step): # max amount of tests before we give up
    test_complexity = 0
    fail_test += 1  
    clw  = 2**(6+random.randint(0,4)) # minimum cacheline size is 64 bits
    cacheSize = 2**( clog2(clw) + random.randint(1,6)) #minimum cacheSize is 2 times clw
    CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
    MemMsg = ReqRespMsgTypes(obw, abw, clw) 
    transaction_length = random.randint(1,100)
    mem = rand_mem(addr_min, addr_max)
    # Setup golden model
    model = ModelCache(cacheSize, 1, 0, clw, mem)
    data  = generate_data(transaction_length)
    types = generate_type(transaction_length)
    addr  = generate_address(transaction_length,addr_min,addr_max)
    for i in range(transaction_length): 
      if types[i] == 'wr':
        test_complexity = test_complexity + 1 + addr[i] + data[i]
        # Write something
        model.write(addr[i] & Bits32(0xfffffffc), data[i])
      else:
        test_complexity = test_complexity + addr[i] + data[i]
        # Read something
        model.read(addr[i] & Bits32(0xfffffffc))
    msgs = model.get_transactions()
    test_complexity /= transaction_length
    # Instantiate testharness
    harness = TestHarness( msgs[::2], msgs[1::2],
                          0, 2, 2, 2, BlockingCachePRTL, cacheSize,
                          CacheMsg, MemMsg, 1)
    harness.elaborate()
    # Load memory before the test
    harness.load( mem[::2], mem[1::2] )
    # Run the test
    resp = transaction_length
    harness.apply( DynamicSim )
    harness.sim_reset()
    curr_cyc = 0
    if (time.monotonic() - start_time) > 54000:
      time_limit_reached = failed = True
      assert False
    try:
      print("")
      while not harness.done() and curr_cyc < max_cycles:
        harness.tick()
        print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
        curr_cyc += 1
        
      assert curr_cyc < max_cycles
    except:
      # print("FAILED")
      if int(harness.sink.recv.msg.opaque) > 1:
        resp = int(harness.sink.recv.msg.opaque - 1)
      else:
        resp =  int(harness.sink.recv.msg.opaque)
      
      failed = True
      break

  output = {"test":fail_test, "trans":resp, \
    "cacheSize":cacheSize, "clw":clw, "failed":failed, \
      "timeOut":time_limit_reached, \
        "testComplexity": test_complexity}
  with open("{}".format(rand_out_dir)\
      , 'w') as fd:
    json.dump(output,fd,sort_keys=True, \
      indent=2, separators=(',',':'))
      

