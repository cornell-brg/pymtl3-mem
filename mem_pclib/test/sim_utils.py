"""
=========================================================================
sim_util.py
=========================================================================
Utilty functions for running a testing simulation

Author : Xiaoyu Yan, Eric Tang
Date   : 21 Decemeber 2019
"""

import struct
from pymtl3 import *

from pymtl3.passes.backends.sverilog import ImportPass, TranslationPass
from pymtl3.stdlib.test.test_srcs    import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks   import TestSinkCL, TestSinkRTL
from blocking_cache.test.CacheMemory import CacheMemoryCL
from pymtl3.stdlib.ifcs.SendRecvIfc  import RecvCL2SendRTL, RecvIfcRTL,\
   RecvRTL2SendCL, SendIfcRTL

#----------------------------------------------------------------------
# Run the simulation
#---------------------------------------------------------------------
def run_sim( th, max_cycles = 1000 ):
  # print (" -----------starting simulation----------- ")
  th.apply( SimulationPass() )
  th.sim_reset()
  ncycles  = 0
  print("")
  while not th.done() and ncycles < max_cycles:
    th.tick()
    print ("{:3d}: {}".format(ncycles, th.line_trace()))
    ncycles += 1
  # check timeout
  assert ncycles < max_cycles
  th.tick()
  th.tick()

#----------------------------------------------------------------------
# Translate the cache and import the results
#---------------------------------------------------------------------
def translate_import( model ):
  # model.elaborate()
  model.yosys_translate = True
  model.apply( TranslationPass() )
  # model = TranslationImportPass( )( model )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):

  def construct( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, CacheMsg,
                MemMsg, cacheSize=128, associativity=1):
    # Instantiate models
    s.src   = TestSrcRTL(CacheMsg.Req, src_msgs, 0, src_delay)
    s.cache = CacheModel(cacheSize, CacheMsg, MemMsg, associativity)
    s.mem   = CacheMemoryCL( 1, [(MemMsg.Req, MemMsg.Resp)], latency) # Use our own modified mem
    s.cache2mem = RecvRTL2SendCL(MemMsg.Req)
    s.mem2cache = RecvCL2SendRTL(MemMsg.Resp)
    s.sink  = TestSinkRTL(CacheMsg.Resp, sink_msgs, 0, sink_delay)

    connect( s.src.send,  s.cache.cachereq  )
    connect( s.sink.recv, s.cache.cacheresp )

    connect( s.mem.ifc[0].resp, s.mem2cache.recv )
    connect( s.cache.memresp, s.mem2cache.send )

    connect( s.cache.memreq, s.cache2mem.recv )
    connect( s.mem.ifc[0].req, s.cache2mem.send )

  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " " + s.cache.line_trace() + " " \
           + s.mem.line_trace()  + " " + s.sink.line_trace()


