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
from BlockingCache.test.DmappedTestCases import DmappedTestCases
from BlockingCache.test.Asso2WayTestCases import AssoTestCases
from BlockingCache.BlockingCacheFL import ModelCache
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

class CacheFL_Tests(DmappedTestCases, AssoTestCases):
  
  def run_test( s,
   msgs, mem, CacheMsg, MemMsg, associativity=1, cacheSize=512,
   stall_prob=0, latency=1, src_delay=0, sink_delay=0):
    cache = ModelCache(cacheSize, associativity, 0, CacheMsg, 
    MemMsg, mem)
    src = msgs[::2]
    sink = msgs[1::2]
    for trans in src:
      if trans.type_ == MemMsgType.READ:
        cache.read(trans.addr, trans.opaque, trans.len)
      elif trans.type_ == MemMsgType.WRITE:
        cache.write(trans.addr, trans.data, trans.opaque, trans.len)
      elif trans.type_ == MemMsgType.WRITE_INIT:
        cache.init(trans.addr, trans.data, trans.opaque, trans.len)
    resps = cache.get_transactions()[1::2]
    for i in range(len(sink)):
      print ("{:3d}: {} > {} == {}".format(i,src[i],
      resps[i],sink[i]))
      # print (f"{i}: {src[i]} > {resps[i]} == {sink[i]}")
      if i < len(sink):
        assert sink[i] == resps[i]
         
