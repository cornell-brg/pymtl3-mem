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
from BlockingCache.test.GenericTestCases import CacheGeneric_Tests
from BlockingCache.test.DmappedTestCases import CacheDmapped_Tests
from BlockingCache.BlockingCacheFL import ModelCache
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType


class TestDirMapCacheFL(CacheGeneric_Tests, CacheDmapped_Tests):
  
  def run_test( s,
   msgs, mem, CacheMsg, MemMsg, cacheSize=256, associativity=1,
   stall_prob=0, latency=1, src_delay=0, sink_delay=0):
    cache = ModelCache(cacheSize, associativity, 0, CacheMsg, 
    MemMsg, mem)
    src = msgs[::2]
    sink = msgs[1::2]
    for trans in src:
      if trans.type_ == MemMsgType.READ:
        cache.read(trans.addr, trans.opaque)
      elif trans.type_ == MemMsgType.WRITE:
        cache.write(trans.addr, trans.data, trans.opaque)
      elif trans.type_ == MemMsgType.WRITE_INIT:
        cache.init(trans.addr, trans.data, trans.opaque)
    resps = cache.get_transactions()[1::2]
    # print (resps)
    for i in range(len(sink)):
      print (f"{i}: {sink[i]} == {resps[i]}")
      if i < len(sink):
        assert sink[i] == resps[i]
         
