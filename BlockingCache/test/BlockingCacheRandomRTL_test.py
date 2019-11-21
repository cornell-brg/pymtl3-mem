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
base_addr = 0x0
max_cycles = 10000

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
def test_bug_inject(  ):
  min_addr = 0
  max_addr = 0x30
  fail_test = 0
  for i in range(10):
    mem = rand_mem(min_addr, max_addr)
    msgs = rand_bug_inject(mem,min_addr,max_addr)


    # Instantiate testharness
    harness = TestHarness( msgs[::2], msgs[1::2],
                          0, 1,
                          0, 0,
                          BlockingCachePRTL, RandomCacheSize,
                          RandomCacheMsg, RandomMemMsg, 1)
    harness.elaborate()
    # Load memory before the test
    if mem != None:
      harness.load( mem[::2], mem[1::2] )
    # Run the test
    try:
      run_sim( harness, max_cycles )
    except:
      fail_test = i
      break
  print("Failed at test {}".format(fail_test))
      

