"""
=========================================================================
MultiCache_test.py
=========================================================================
Tests for Multicache configuration using the BlockingCache

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 13 April 2020
"""

from pymtl3 import *
from pymtl3_mem.test.sim_utils import run_sim, MultiCacheTestHarness
from .MultiCacheTestCases import MultiCacheTestCases
from ..BlockingCacheRTL import BlockingCacheRTL

class MultiCache_Tests( MultiCacheTestCases ):
  def run_test( s, tp, cmdline_opts, trace=True ):
    harness = MultiCacheTestHarness( BlockingCacheRTL, tp )
    harness.elaborate()
    if tp.mem != None:
      harness.load()
    sram_wrapper = False
    run_sim( harness, cmdline_opts, trace, sram_wrapper )
