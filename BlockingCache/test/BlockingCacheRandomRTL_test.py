"""
=========================================================================
 BlockingCacheRandomRTL_test.py
=========================================================================
Random Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 18 November 2019
"""

import pytest
from pymtl3      import *
from BlockingCache.test.BlockingCacheFL_test import TestHarness
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.RandomTestCases import complete_random_test, rand_mem, r, l
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes


import json
import random

base_addr = 0x0
max_cycles = 500

#-------------------------------------------------------------------------
# Complete random testing
#-------------------------------------------------------------------------

def test_complete_random(rand_out_dir):
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  min_addr = 0
  max_addr = 400 # 100 words
  fail_test = 0
  failed = False
  ntests_per_step = 50
  # print(f"clw[{clw}] size[{cacheSize}]")

  for i in range(ntests_per_step): # max amount of tests before we give up
    fail_test += 1  
    clw  = 2**(6+random.randint(0,4)) # minimum cacheline size is 64 bits
    cacheSize = 2**( clog2(clw) + random.randint(1,6)) #minimum cacheSize is 2 times clw
    CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
    MemMsg = ReqRespMsgTypes(obw, abw, clw)
    transaction_length = random.randint(1,50)
    mem = rand_mem(min_addr, max_addr)
    msgs = complete_random_test(mem,min_addr,max_addr,transaction_length,cacheSize,clw)

    # Instantiate testharness
    harness = TestHarness( msgs[::2], msgs[1::2],
                          r(), 1, 0, 0, BlockingCachePRTL, cacheSize,
                          CacheMsg, MemMsg, 1)
    harness.elaborate()
    # Load memory before the test
    harness.load( mem[::2], mem[1::2] )
    # Run the test
    resp = transaction_length
    harness.apply( DynamicSim )
    harness.sim_reset()
    curr_cyc = 0
    try:
    # print("")
      while not harness.done() and curr_cyc < max_cycles:
        harness.tick()
        # print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
        curr_cyc += 1
      assert curr_cyc < max_cycles
    except:
      print("FAILED")
      # if int(harness.sink.recv.msg.opaque) > 1:
        # resp = int(harness.sink.recv.msg.opaque - 1)
      # else:
      resp =  int(harness.sink.recv.msg.opaque)
      
      failed = True
      break

  output = {"test":fail_test, "trans":resp, \
    "cacheSize":cacheSize, "clw":clw, "failed":failed}
  with open("{}".format(rand_out_dir)\
      , 'w') as fd:
    json.dump(output,fd,sort_keys=True, \
      indent=2, separators=(',',':'))
      

