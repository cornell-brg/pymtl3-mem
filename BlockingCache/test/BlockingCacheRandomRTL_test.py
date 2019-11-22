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
from BlockingCache.test.BlockingCacheFL_test import test_case_table_generic, \
  TestHarness, run_sim, setup_tb
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.RandomTestCases import test_case_table_random
from BlockingCache.test.RandomTestCases import test_case_table_random_lat
from BlockingCache.test.RandomTestCases import test_case_table_enhanced_random
from BlockingCache.test.RandomTestCases import CacheMsg  as RandomCacheMsg
from BlockingCache.test.RandomTestCases import MemMsg    as RandomMemMsg
from BlockingCache.test.RandomTestCases import cacheSize as RandomCacheSize
from BlockingCache.test.RandomTestCases import rand_bug_inject, rand_mem
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes


import json
import random

base_addr = 0x0
max_cycles = 500

#-------------------------------------------------------------------------
# Random tests for both baseline and alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_random_lat )
def test_random( test_params ):
  stall = test_params.stall
  lat   = test_params.lat
  src   = test_params.src
  sink  = test_params.sink
  
  msg = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  else:
    mem = None
  setup_tb( msg, mem, BlockingCachePRTL, RandomCacheSize, 
  RandomCacheMsg, RandomMemMsg, 
  stall, lat, src, sink, 1 )


#-------------------------------------------------------------------------
# Random tests for both baseline and alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_enhanced_random )
def test_random( test_params ):
  
  # msg = test_params.msg_func()
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( 0 )
  else:
    mem = None

  msgs = test_params.msg_func( mem )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL, RandomCacheSize,
                         RandomCacheMsg, RandomMemMsg, 1)
  harness.elaborate()
  # Load memory before the test
  if mem != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles )

#-------------------------------------------------------------------------
# Random tests for both baseline and alternative design
#-------------------------------------------------------------------------

# @pytest.mark.parametrize( **test_case_table_enhanced_random )
def test_bug_inject(rand_out_dir):
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  min_addr = 0
  max_addr = 50 # 100 words
  fail_test = 1
  failed = False
  clw  = 128
  cacheSize = random.choice([256,512,1024,2048,4096,8192,16384])
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  MemMsg = ReqRespMsgTypes(obw, abw, clw)
  for i in range(100): # max amount of tests before we give up
    transaction_length = random.randint(1,50)
    mem = rand_mem(min_addr, max_addr)
    msgs = rand_bug_inject(mem,min_addr,max_addr,transaction_length,cacheSize,clw)

    # Instantiate testharness
    harness = TestHarness( msgs[::2], msgs[1::2],
                          0, 1,
                          0, 0,
                          BlockingCachePRTL, cacheSize,
                          CacheMsg, MemMsg, 1)
    harness.elaborate()
    # Load memory before the test
    if mem != None:
      harness.load( mem[::2], mem[1::2] )
    # Run the test
    resp = transaction_length
    try:
      harness.apply( DynamicSim )
      harness.sim_reset()
      curr_cyc = 0
      # print("")
      while not harness.done() and curr_cyc < max_cycles:
        harness.tick()
        # print ("{:3d}: {}".format(curr_cyc, harness.line_trace()))
        curr_cyc += 1
      assert curr_cyc < max_cycles
    except:
      if int(harness.sink.recv.msg.opaque) > 1:
        resp = int(harness.sink.recv.msg.opaque - 1)
      else:
        resp =  int(harness.sink.recv.msg.opaque)
      fail_test = i+1
      failed = True
      break
      # assert False

  output = {"test":fail_test, "trans":resp, \
    "cacheSize":cacheSize, "clw":clw, "failed":failed}
  with open("{}".format(rand_out_dir)\
      , 'w') as fd:
    json.dump(output,fd,sort_keys=True, \
      indent=2, separators=(',',':'))
    # print("\nFailed at test {} and trans {}".format(\
    #   fail_test, resp))
      

