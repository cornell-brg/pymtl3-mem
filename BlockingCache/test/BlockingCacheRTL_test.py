"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 15 November 2019
"""

import pytest
from pymtl3      import *
# from BlockingCache.test.BlockingCacheFL_test import test_case_table_generic, \
#   TestHarness
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.GenericTestCases import CacheGeneric_Tests
# from BlockingCache.test.GenericTestCases import test_case_table_generic
# from BlockingCache.test.GenericTestCases import CacheMsg as GenericCacheMsg
# from BlockingCache.test.GenericTestCases import MemMsg   as GenericMemMsg
from BlockingCache.test.DmappedTestCases import CacheDmapped_Tests
# from BlockingCache.test.DmappedTestCases import test_case_table_dmap
# from BlockingCache.test.DmappedTestCases import CacheMsg as DmapCacheMsg
# from BlockingCache.test.DmappedTestCases import MemMsg   as DmapMemMsg
from mem_pclib.test.sim_utils import run_sim, translate_import,\
TestHarness

max_cycles = 500

class TestDirMapBlockingCacheRTL(CacheGeneric_Tests, CacheDmapped_Tests):
  def run_test( s,
   msgs, mem, CacheMsg, MemMsg, cacheSize=256, associativity=1,
   stall_prob=0, latency=1, src_delay=0, sink_delay=0):
    harness = TestHarness( msgs[::2], msgs[1::2],
                           stall_prob, latency,
                           src_delay, sink_delay,
                           BlockingCachePRTL, CacheMsg,
                           MemMsg, cacheSize, associativity )  
    harness.elaborate( )
    if mem != None:
      harness.load( mem[::2], mem[1::2] )
    run_sim( harness, max_cycles )


# @pytest.mark.parametrize( **test_case_table_generic )
# def test_generic( test_params ):
#   msgs = test_params.msg_func( base_addr )
#   if test_params.mem_data_func != None:
#     mem = test_params.mem_data_func( base_addr )
#   # Instantiate testharness
#   harness = TestHarness( msgs[::2], msgs[1::2],
#                          test_params.stall, test_params.lat,
#                          test_params.src, test_params.sink,
#                          BlockingCachePRTL, GenericCacheMsg,
#                          GenericMemMsg)
#   harness.elaborate()
#   # translate_import(harness, harness.cache)
#   # Load memory before the test
#   if test_params.mem_data_func != None:
#     harness.load( mem[::2], mem[1::2] )
#   # Run the test
#   run_sim( harness, max_cycles )

# @pytest.mark.parametrize( **test_case_table_dmap )
# def test_dmap( test_params ):
#   msgs = test_params.msg_func( base_addr )
#   if test_params.mem_data_func != None:
#     mem = test_params.mem_data_func( base_addr )
#   # Instantiate testharness
#   harness = TestHarness( msgs[::2], msgs[1::2],
#                          test_params.stall, test_params.lat,
#                          test_params.src, test_params.sink,
#                          BlockingCachePRTL, DmapCacheMsg,
#                          DmapMemMsg)
#   harness.elaborate()
#   # translate()
#   # Load memory before the test
#   if test_params.mem_data_func != None:
#     harness.load( mem[::2], mem[1::2] )
#   # Run the test
#   run_sim( harness, max_cycles )

