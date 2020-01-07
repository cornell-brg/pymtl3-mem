"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 23 December 2019
"""

import pytest
from pymtl3      import *
from BlockingCache.BlockingCacheRTL import BlockingCacheRTL
from BlockingCache.test.GenericTestCases import GenericTestCases
from BlockingCache.test.DmappedTestCases import DmappedTestCases
# commented since it will also run FL tests...
# from BlockingCache.test.BlockingCacheFL_test import DirMapCacheFL_Tests 
from mem_pclib.test.sim_utils import run_sim, translate_import, TestHarness

max_cycles = 500

class DirMapBlockingCacheRTL_Tests( GenericTestCases, DmappedTestCases ):

  def run_test( s,
   msgs, mem, CacheMsg, MemMsg, cacheSize=256, associativity=1,
   stall_prob=0, latency=1, src_delay=0, sink_delay=0):

    harness = TestHarness( msgs[::2], msgs[1::2],
                           stall_prob, latency,
                           src_delay, sink_delay,
                           BlockingCacheRTL, CacheMsg,
                           MemMsg, cacheSize, associativity )  
    harness.elaborate()
    if mem != None:
      harness.load( mem[::2], mem[1::2] )
    run_sim( harness, max_cycles )
