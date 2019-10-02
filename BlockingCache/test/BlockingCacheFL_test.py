#=========================================================================
# BlockingCacheFL_test.py
#=========================================================================

import pytest
import struct

from pymtl3 import *
from pymtl3.stdlib.cl.MemoryCL import MemoryCL
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvCL2SendRTL, RecvIfcRTL, RecvRTL2SendCL, SendIfcRTL  
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.test.test_srcs import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks import TestSinkCL, TestSinkRTL
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL

MemReqMsg4B, MemRespMsg4B = mk_mem_msg(8,32,32)
MemReqMsg16B, MemRespMsg16B = mk_mem_msg(8,32,128)

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):
  
  def construct( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, test_verilog=False ):
    # Instantiate models
    s.src   = TestSrcRTL(MemReqMsg4B, src_msgs, src_delay)
    s.cache = CacheModel()
    s.mem   = MemoryCL( 1, mem_ifc_dtypes=[MemReqMsg4B, MemRespMsg4B], latency=latency)
    s.cache2mem = RecvRTL2SendCL(MemReqMsg4B)
    s.mem2cache = RecvCL2SendRTL(MemRespMsg4B)
    s.sink  = TestSinkRTL(MemRespMsg4B, sink_msgs, sink_delay)

    s.connect( s.src.send,  s.cache.cachereq  )
    s.connect( s.sink.recv, s.cache.cacheresp )

    s.connect( s.mem.ifc[0].resp, s.mem2cache.recv )
    s.connect( s.cache.memresp, s.mem2cache.send )

    s.connect( s.cache.memreq, s.cache2mem.recv )
    s.connect( s.mem.ifc[0].req, s.cache2mem.send )


  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " " + s.cache.line_trace() + " " \
         + s.mem.line_trace() + " " + s.sink.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  msg = MemReqMsg4B()

  if   type_ == 'rd': msg.type_ = MemMsgType.READ
  elif type_ == 'wr': msg.type_ = MemMsgType.WRITE
  elif type_ == 'in': msg.type_ = MemMsgType.WRITE_INIT

  msg.addr   = addr
  msg.opaque = opaque
  msg.len    = len
  msg.data   = data
  print (msg)
  return msg

def resp( type_, opaque, test, len, data ):
  msg = MemRespMsg4B()
  # print ("msg = " + str( msg))

  if   type_ == 'rd': msg.type_ = MemMsgType.READ
  elif type_ == 'wr': msg.type_ = MemMsgType.WRITE
  elif type_ == 'in': msg.type_ = MemMsgType.WRITE_INIT

  msg.opaque = opaque
  msg.len    = len
  msg.test   = test
  msg.data   = data

  return msg

#---------
# Run the simulation
#---------
def run_sim(th, max_cycles):
  # print (" -----------starting simulation----------- ")
  th.apply( SimpleSim )
  curr_cyc = 0
  while not th.done():
    print 
    print ("cycle starts -------")
    th.tick()
    print (th.line_trace())
    print ("cycle ends   -------")
    curr_cyc += 1
    assert curr_cyc < max_cycles


#----------------------------------------------------------------------
# Test Case: read hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def read_hit_1word_clean( base_addr=0 ):
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'wr', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'wr', 0x0, 0,   0,  0          ),
    req( 'rd', 0x1, base_addr, 0, 0          ), resp( 'rd', 0x1, 0,   0,  0xdeadbeef ),
  ]

#-------------------------------------------------------------------------
# Test table for generic test
#-------------------------------------------------------------------------

test_case_table_generic = mk_test_case_table([
  (                         "msg_func               mem_data_func         stall lat src sink"),
  [ "read_hit_1word_clean",  read_hit_1word_clean,  None,                 0.0,  0,  0,  0    ],
])

@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params):
  msgs = test_params.msg_func( 0 )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( 0 )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL, False)
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles=100 )
