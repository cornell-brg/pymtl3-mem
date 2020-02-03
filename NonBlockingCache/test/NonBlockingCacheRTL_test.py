"""
=========================================================================
NonBlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined NonBlocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 2 Feb 2020
"""

import pytest
from pymtl3      import *
from NonBlockingCache.NonBlockingCacheRTL import NonBlockingCacheRTL
from BlockingCache.test.DmappedTestCases import DmappedTestCases
from BlockingCache.test.Asso2WayTestCases import AssoTestCases
from BlockingCache.test.HypothesisTest import HypothesisTests
# commented since it will also run FL tests...
# from BlockingCache.test.BlockingCacheFL_test import DirMapCacheFL_Tests 
from mem_pclib.test.sim_utils import run_sim, translate_import, \
  NonBlockingCacheTestHarness

max_cycles = 500

class NonBlockingCacheRTL_Tests( DmappedTestCases, AssoTestCases):
# class NonBlockingCacheRTL_Tests( DmappedTestCases, AssoTestCases,
# HypothesisTests ):
  def run_test( s,
   msgs, mem, CacheMsg, MemMsg, associativity=1, cacheSize=512, 
   stall_prob=0, latency=1, src_delay=0, sink_delay=0):

    harness = NonBlockingCacheTestHarness( msgs[::2], msgs[1::2],
                           stall_prob, latency,
                           src_delay, sink_delay,
                           NonBlockingCacheRTL, CacheMsg,
                           MemMsg, cacheSize, associativity )  
    harness.elaborate()
    if mem != None:
      harness.load( mem[::2], mem[1::2] )
    run_sim( harness, max_cycles )
