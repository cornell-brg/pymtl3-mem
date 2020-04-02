"""
=========================================================================
 BlockingCacheFL_test.py
=========================================================================
Test for Pipelined Blocking Cache FL model

Author : Xiaoyu Yan, Eric Tang
Date   : 17 November 2019
"""

import pytest
import struct
import random

from pymtl3 import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg

from ..BlockingCacheFL import ModelCache

from .DmappedTestCases import DmappedTestCases
from .Asso2WayTestCases import AssoTestCases
from .HypothesisTest import HypothesisTests
from .AmoTests import AmoTests

class CacheFL_Tests( DmappedTestCases, AssoTestCases, AmoTests ):

  def run_test( s, msgs, mem, CacheReqType, CacheRespType, MemReqType,
                MemRespType, associativity=1, cacheSize=512, stall_prob=0,
                latency=1, src_delay=0, sink_delay=0, dump_vcd=False,
                test_verilog='zeros', max_cycles=500, trace=2 ):

    cache = ModelCache(cacheSize, associativity, 0, CacheReqType, CacheRespType,
     MemReqType, MemRespType, mem)
    src = msgs[::2]
    sink = msgs[1::2]
    for trans in src:
      if trans.type_ == MemMsgType.READ:
        cache.read(trans.addr, trans.opaque, trans.len)
      elif trans.type_ == MemMsgType.WRITE:
        cache.write(trans.addr, trans.data, trans.opaque, trans.len)
      elif trans.type_ == MemMsgType.WRITE_INIT:
        cache.init(trans.addr, trans.data, trans.opaque, trans.len)
      elif trans.type_ >= MemMsgType.AMO_ADD:
        cache.amo(trans.addr, trans.data, trans.opaque, trans.type_)
    resps = cache.get_transactions()[1::2]
    print("")
    for i in range(len(sink)):
      print ("{:3d}: ({}) > {} ".format(i, src[i], resps[i]))
      if i < len(sink):
        assert sink[i] == resps[i], "\n  actual:{}\nexpected:{}".format(
          resps[i], sink[i]
        )
