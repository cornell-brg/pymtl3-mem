"""
=========================================================================
RandomRTL_test.py
=========================================================================
Random Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 19 November 2019
"""

import pytest
import random
from pymtl3      import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvCL2SendRTL, RecvIfcRTL,\
   RecvRTL2SendCL, SendIfcRTL
from BlockingCache.test.CacheMemory import CacheMemoryCL
from pymtl3.stdlib.test.test_srcs import TestSrcCL, TestSrcRTL

from BlockingCache.test.BlockingCacheFL_test import run_sim, setup_tb

from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.BlockingCacheFL import BlockingCacheFL


class RandomTestHarness( Component ):
  """
  Uses the FL model to verify the RTL model and uses random tests
  For cache, we use random transactions
  """
  def construct(s, src_msgs, stall_prob, latency, src_delay, sink_delay,
  DUT, REF, cacheSize, cacheMsg, MemMsg, associativity):
    s.src   = TestSrcRTL(CacheMsg.Req, src_msgs, src_delay)
    s.DUT = DUT(cacheSize, CacheMsg, MemMsg, associativity)
    s.REF = REF(cacheSize, CacheMsg, MemMsg, associativity)
    s.DUTmem   = CacheMemoryCL( 1, [(MemMsg.Req, MemMsg.Resp)], latency) # Use our own modified mem
    s.REFmem   = CacheMemoryCL( 1, [(MemMsg.Req, MemMsg.Resp)], latency) # Use our own modified mem
    s.DUTcache2mem = RecvRTL2SendCL(MemMsg.Req)
    s.DUTmem2cache = RecvCL2SendRTL(MemMsg.Resp)
    s.REFcache2mem = RecvRTL2SendCL(MemMsg.Req)
    s.REFmem2cache = RecvCL2SendRTL(MemMsg.Resp)
    s.sink = CacheTestSinkRTL(CacheMsg.Resp, sink_delay)

    s.src.send  //= s.DUT.cachereq
    s.src.send  //= s.REF.cachereq
    s.sink.recv //= s.DUT.cacheresp
    s.sink.recv //= s.REF.cacheresp

    s.DUTmem.ifc[0].resp //= s.DUTmem2cache.recv
    s.DUT.memresp         //= s.DUTmem2cache.send
    s.DUT.memreq          //= s.DUTcache2mem.recv
    s.DUTmem.ifc[0].req  //= s.DUTcache2mem.send

    s.REFmem.ifc[0].resp //= s.REFmem2cache.recv
    s.REF.memresp         //= s.REFmem2cache.send
    s.REF.memreq          //= s.REFcache2mem.recv
    s.REFmem.ifc[0].req  //= s.REFcache2mem.send
    
  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.DUTmem.write_mem( addr, data_bytes_a )
      s.REFmem.write_mem( addr, data_bytes_a )
  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " " + s.cache.line_trace() + " " \
           + s.DUTmem.line_trace()  + " " + s.sink.line_trace()

#----------------------------------------------------------------------
# Run the simulation
#---------------------------------------------------------------------
def run_sim(th, max_cycles):
  # print (" -----------starting simulation----------- ")
  th.apply( DynamicSim )
  th.sim_reset()
  curr_cyc = 0
  print("")
  while not th.done() and curr_cyc < max_cycles:
    th.tick()
    print ("{:3d}: {}".format(curr_cyc, th.line_trace()))
    curr_cyc += 1
  assert curr_cyc < max_cycles
  th.tick()
  th.tick()

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128
CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
MemMsg = ReqRespMsgTypes(obw, abw, clw)
cacheSize = 1024

def rand_transaction_gen(num):
  

def test_random_sweep():
  tb = RandomTestHarness()