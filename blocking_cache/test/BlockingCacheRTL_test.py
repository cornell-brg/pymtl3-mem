"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 23 December 2019
"""

import pytest

from pymtl3      import *

from test.sim_utils import run_sim, TestHarness

from ..BlockingCacheRTL import BlockingCacheRTL

from .DmappedTestCases import DmappedTestCases
from .Asso2WayTestCases import AssoTestCases
from .HypothesisTest import HypothesisTests
from .CiferTests import CiferTests

class BlockingCacheRTL_Tests( DmappedTestCases, AssoTestCases, HypothesisTests,
                              CiferTests ):

  def run_test( s, msgs, mem, CacheReqType, CacheRespType, MemReqType,
                MemRespType, associativity=1, cacheSize=64, stall_prob=0,
                latency=1, src_delay=0, sink_delay=0, dump_vcd=False,
                test_verilog='zeros', max_cycles = 500, trace=2 ):

    harness = TestHarness( msgs[::2], msgs[1::2], stall_prob, latency,
                           src_delay, sink_delay, BlockingCacheRTL,
                           CacheReqType, CacheRespType, MemReqType,
                           MemRespType, cacheSize, associativity )
    harness.elaborate()
    if mem != None:
      harness.load( mem[::2], mem[1::2] )
    run_sim( harness, max_cycles, dump_vcd, test_verilog, trace )
