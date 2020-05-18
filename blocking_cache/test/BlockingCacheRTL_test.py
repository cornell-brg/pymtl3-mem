"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 23 December 2019
"""
from test.sim_utils     import run_sim, TestHarness
from ..BlockingCacheRTL import BlockingCacheRTL
from .GenericTestCases  import GenericTestCases
from .AmoTests          import AmoTests
from .InvFlushTests     import InvFlushTests
from .RandomTestCases   import RandomTests
from .HypothesisTest    import HypothesisTests

class BlockingCacheRTL_Tests( GenericTestCases, InvFlushTests, AmoTests,
                              HypothesisTests, RandomTests ):

  def run_test( s, msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
                associativity, cacheSize, stall_prob, latency, src_delay, 
                sink_delay, cmdline_opts, trace ):

    th = TestHarness( msgs[::2], msgs[1::2], stall_prob, latency,
                           src_delay, sink_delay, BlockingCacheRTL,
                           CacheReqType, CacheRespType, MemReqType,
                           MemRespType, cacheSize, associativity )
    th.elaborate()
    if mem != None:
      th.load( mem[::2], mem[1::2] )
    sram_wrapper = True if cacheSize == 4096 else False    
    run_sim( th, cmdline_opts, trace, sram_wrapper )
