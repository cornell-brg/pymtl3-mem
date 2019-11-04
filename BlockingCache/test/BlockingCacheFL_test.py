"""
=========================================================================
 BlockingCacheFL_test.py
=========================================================================
Test for Pipelined Blocking Cache FL model

Author : Xiaoyu Yan, Eric Tang
Date   : 04 November 2019
"""
import pytest
import struct
import random

from pymtl3 import *
from pymtl3.stdlib.cl.MemoryCL import MemoryCL
from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvCL2SendRTL, RecvIfcRTL,\
   RecvRTL2SendCL, SendIfcRTL
from pymtl3.stdlib.test.test_srcs import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks import TestSinkCL, TestSinkRTL
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.BlockingCacheFL import BlockingCacheFL
from BlockingCache.test.CacheMemory import CacheMemoryCL

from pymtl3.passes.yosys import TranslationImportPass # Translation to Verilog
from BlockingCache.test.GenericTestCases import test_case_table_generic
from BlockingCache.test.GenericTestCases import CacheMsg as GenericCacheMsg
from BlockingCache.test.GenericTestCases import MemMsg   as GenericMemMsg

base_addr = 0x70
max_cycles = 1000

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):

  def construct( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, CacheMsg, MemMsg ):

    
    cacheSize = 8196 # size in bytes
    # Instantiate models
    s.src   = TestSrcRTL(CacheMsg.Req, src_msgs, src_delay)
    s.cache = CacheModel(cacheSize, CacheMsg, MemMsg)
    s.mem   = CacheMemoryCL( 1, [(MemMsg.Req, MemMsg.Resp)], latency) # Use our own modified mem
    s.cache2mem = RecvRTL2SendCL(MemMsg.Req)
    s.mem2cache = RecvCL2SendRTL(MemMsg.Resp)
    s.sink  = TestSinkRTL(CacheMsg.Resp, sink_msgs, sink_delay)

    # s.cache.yosys_translate_import = True

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

#-------------------------------------------------------------------------
# Translate Function for the cache
#-------------------------------------------------------------------------

# def translate():
#   # Translate the checksum unit and import it back in using the yosys
#   # backend
#   cacheSize = 8196 # size in bytes
#   dut = BlockingCachePRTL(cacheSize, CacheMsg, MemMsg)
#   dut.elaborate()
#   dut.yosys_translate_import = True
#   dut = TranslationImportPass(  )( dut )
#   dut.elaborate()
#   dut.apply( TranslationPass() )


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



@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params):
  msgs = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  # Instantiate testharness
  th = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCacheFL, GenericCacheMsg,
                         GenericMemMsg)
  th.elaborate()
  # translate()
  # Load memory before the test
  if test_params.mem_data_func != None:
    th.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( th, max_cycles )


