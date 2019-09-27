#=========================================================================
# cacheNopeFL_test.py
#=========================================================================

from __future__ import print_function

import pytest
import random
import struct

from pymtl3      import *
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.test.test_srcs import TestSrcCL
from pymtl3.stdlib.test.test_sinks import TestSinkCL

from pymtl3.stdlib.ifcs import MemMsg,    MemReqMsg,    MemRespMsg
from pymtl3.stdlib.ifcs import MemMsg4B,  MemReqMsg4B,  MemRespMsg4B
from pymtl3.stdlib.ifcs import MemMsg16B, MemReqMsg16B, MemRespMsg16B

from pymtl3.stdlib.ifcs.ValRdyIfc import InValRdyIfc, OutValRdyIfc

from pymtl3.stdlib.cl.MemoryCL import MemoryCL

from NonBlockingCache.ifcs.CoherentMemMsg import *

from NonBlockingCache.NonBlockingCachePRTL import NonBlockingCachePRTL


#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Model ):
  def __init__( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, check_test, dump_vcd, test_verilog=False ):
    # Messge type

    cache_msgs = MemMsg4B()
    mem_msgs   = CoherentMemMsg16B()

    # Instantiate models

    s.src   = TestSrcCL   ( cache_msgs.req,  src_msgs,  src_delay  )
    s.cache = CacheModel   ( ncaches = 1, cache_id = 0 )
    s.mem   = MemoryCL   ( mem_msgs, 1, stall_prob, latency )
    s.sink  = TestSinkCL( cache_msgs.resp, sink_msgs, sink_delay, check_test )
    # Dump VCD

    if dump_vcd:
      s.cache.vcd_file = dump_vcd

    # Verilog translation

    if test_verilog:
      s.cache = TranslationTool( s.cache, enable_blackbox=True )

    # Proc -> Cache
    s.cachereq  = InValRdyIfc ( MemReqMsg4B )

    # Mem -> Cache
    s.memresp   = InValRdyIfc ( CoherentMemRespMsg16B )

    # Cache -> Proc
    s.cacheresp = OutValRdyIfc( MemRespMsg4B )

    # Cache -> Mem
    s.memreq    = OutValRdyIfc( CoherentMemReqMsg16B )

    # Mem -> Cache (fwdreq)

    s.fwdreq    = InValRdyIfc ( CoherentMemReqMsg16B )

    # Cache -> Mem (fwdresp)

    s.fwdresp   = OutValRdyIfc( CoherentMemRespMsg16B )

    # Connect
    s.connect_pairs(
      # cachereq
      s.cache.cachereq_val,   s.cachereq.val,
      s.cache.cachereq_rdy,   s.cachereq.rdy,
      s.cache.cachereq_msg,   s.cachereq.msg,

      # memresp
      s.cache.memresp_val,    s.memresp.val,
      s.cache.memresp_rdy,    s.memresp.rdy,
      s.cache.memresp_msg,    s.memresp.msg,

      # cacheresp
      s.cache.cacheresp_val,  s.cacheresp.val,
      s.cache.cacheresp_rdy,  s.cacheresp.rdy,
      s.cache.cacheresp_msg,  s.cacheresp.msg,

      # memreq
      s.cache.memreq_val,     s.memreq.val,
      s.cache.memreq_rdy,     s.memreq.rdy,
      s.cache.memreq_msg,     s.memreq.msg,

      # fwdreq
      s.cache.fwdreq_val,     s.fwdreq.val,
      s.cache.fwdreq_rdy,     s.fwdreq.rdy,
      s.cache.fwdreq_msg,     s.fwdreq.msg,

      # fwdresp
      s.cache.fwdresp_val,    s.fwdresp.val,
      s.cache.fwdresp_rdy,    s.fwdresp.rdy,
      s.cache.fwdresp_msg,    s.fwdresp.msg,
    )

    s.connect( s.src.out,       s.cachereq  )
    s.connect( s.sink.in_,      s.cacheresp )

    s.connect( s.memreq,  s.mem.reqs[0]     )
    s.connect( s.memresp, s.mem.resps[0]    )


  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.src.done and s.sink.done

  def line_trace( s ):
    return s.src.line_trace() + " " + s.cache.line_trace() + " " \
         + s.mem.line_trace() + " " + s.sink.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  msg = MemReqMsg4B()

  if   type_ == 'rd': msg.type_ = MemReqMsg.TYPE_READ
  elif type_ == 'wr': msg.type_ = MemReqMsg.TYPE_WRITE
  elif type_ == 'in': msg.type_ = MemReqMsg.TYPE_WRITE_INIT

  msg.addr   = addr
  msg.opaque = opaque
  msg.len    = len
  msg.data   = data
  return msg

def resp( type_, opaque, test, len, data ):
  msg = MemRespMsg4B()

  if   type_ == 'rd': msg.type_ = MemRespMsg.TYPE_READ
  elif type_ == 'wr': msg.type_ = MemRespMsg.TYPE_WRITE
  elif type_ == 'in': msg.type_ = MemRespMsg.TYPE_WRITE_INIT

  msg.opaque = opaque
  msg.len    = len
  msg.test   = test
  msg.data   = data
  return msg

#----------------------------------------------------------------------
# Test Case: read hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def read_hit_1word_clean( base_addr ):
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
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
def test_generic( test_params, dump_vcd ):
  msgs = test_params.msg_func( 0 )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( 0 )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         cacheNopePRTL, False, dump_vcd )
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, dump_vcd, max_cycles=100 )