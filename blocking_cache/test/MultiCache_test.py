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
  def run_test( s, tp, cmdline_opts, trace=True ):
    harness = MultiCacheTestHarness( BlockingCacheRTL, tp )
    harness.elaborate()
    if tp.mem != None:
      harness.load()
    sram_wrapper = False
    run_sim( harness, cmdline_opts, trace, sram_wrapper )
