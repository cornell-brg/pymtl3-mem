"""
=========================================================================
MultiCache_test.py
=========================================================================
Tests for Multicache configuration using the BlockingCache

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 13 April 2020
"""

from pymtl3 import *
from ..BlockingCacheRTL import BlockingCacheRTL
from .MultiCacheTestCases import MultiCacheTestCases
from test.sim_utils import run_sim, MultiCacheTestHarness

class MultiCache_Tests( MultiCacheTestCases ):
  def run_test( s, tp, dump_vcd=False, test_verilog='zeros', max_cycles=500, trace=2 ):
    harness = MultiCacheTestHarness( BlockingCacheRTL, tp )
    harness.elaborate()
    if tp.mem != None:
      harness.load()
    run_sim( harness, max_cycles, dump_vcd, test_verilog, trace )
