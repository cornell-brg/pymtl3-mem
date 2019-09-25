#=========================================================================
# CoherentCacheFL_test.py
#=========================================================================

from __future__ import print_function

import pytest
import random
import struct

from pymtl      import *
from pclib.test import mk_test_case_table, run_sim

from pclib.ifcs import MemMsg,    MemReqMsg,    MemRespMsg
from pclib.ifcs import MemMsg4B,  MemReqMsg4B,  MemRespMsg4B
from pclib.ifcs import MemMsg16B, MemReqMsg16B, MemRespMsg16B
from ifcs.CoherentMemMsg import CoherentMemReqMsg, CoherentMemRespMsg, CoherentMemMsg16B

from pclib.test import TestSource

from test_modules.TestCacheSink   import TestCacheSink
from test_modules.TestCoherentDirMem import TestCoherentDirMemory as TestMemory

from coherent_cache.CoherentCacheFL import CoherentCacheFL
# We define all test cases here. They will be used to test _both_ FL and
# RTL models.
#
# Notice the difference between the TestHarness instances in FL and RTL.
#
# class TestHarness( Model ):
#   def __init__( s, src_msgs, sink_msgs, stall_prob, latency,
#                 src_delay, sink_delay, CacheModel, check_test, dump_vcd )
#
# The last parameter of TestHarness, check_test is whether or not we
# check the test field in the cacheresp. In FL model we don't care about
# test field and we set cehck_test to be False because FL model is just
# passing through cachereq to mem, so all cachereq sent to the FL model
# will be misses, whereas in RTL model we must set cehck_test to be True
# so that the test sink will know if we hit the cache properly.

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Model ):

  def __init__( s, src_msgs, sink1_msgs, sink2_msgs, fwd1_msgs, fwd2_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, check_test, dump_vcd, test_verilog=False ):

    # Messge type

    cache_msgs = CoherentMemMsg16B()
    mem_msgs   = CoherentMemMsg16B()

    # Instantiate models

    s.src   = TestSource   ( cache_msgs.req,  src_msgs,  src_delay  )
    s.mem   = TestMemory   ( mem_ifc_dtypes=mem_msgs )
    s.sink1  = TestCacheSink( cache_msgs.resp, sink1_msgs, sink_delay, check_test )
    s.sink2  = TestCacheSink( cache_msgs.resp, sink2_msgs, sink_delay, check_test )
    s.fwd1  = TestCacheSink( cache_msgs.req, fwd1_msgs, sink_delay, check_test )
    s.fwd2  = TestCacheSink( cache_msgs.req, fwd2_msgs, sink_delay, check_test )


    # Connect

    s.connect( s.src.out,  s.mem.reqs     )

    @s.tick_fl
    def tick():
      s.sink1.in_.val.next = 0
      s.sink2.in_.val.next = 0
      s.fwd1.in_.val.next = 0
      s.fwd2.in_.val.next = 0
      s.mem.resps.rdy.next = 1
      s.mem.fwds.rdy.next = 1

      if s.mem.resps.val and s.mem.resps.msg.dst == 0x0 and s.sink1.in_.rdy:
        s.sink1.in_.msg.next = s.mem.resps.msg
        s.sink1.in_.val.next = 1
      elif s.mem.resps.val and s.mem.resps.msg.dst == 0x1 and s.sink2.in_.rdy:
        s.sink2.in_.msg.next = s.mem.resps.msg
        s.sink2.in_.val.next = 1

      if s.mem.fwds.val and s.mem.fwds.msg.dst == 0x0 and s.fwd1.in_.rdy:
        s.fwd1.in_.msg.next = s.mem.fwds.msg
        s.fwd1.in_.val.next = 1
      elif s.mem.fwds.val and s.mem.fwds.msg.dst == 0x1 and s.fwd2.in_.rdy:
        s.fwd2.in_.msg.next = s.mem.fwds.msg
        s.fwd2.in_.val.next = 1


  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.src.done and s.sink1.done and s.sink2.done and s.fwd1.done and s.fwd2.done

  def line_trace( s ):
    return s.src.line_trace() + " "  \
        + s.mem.line_trace() + " resp1: " + s.sink1.line_trace() + " resp2: " + s.sink2.line_trace() + " fwd1: " + s.fwd1.line_trace() + " fwd2: " + s.fwd2.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( src, type_, opaque, addr, len, data ):
  msg = CoherentMemReqMsg()

  if   type_ == 'gets': msg.type_ = CoherentMemReqMsg.TYPE_GET_S
  elif type_ == 'getm': msg.type_ = CoherentMemReqMsg.TYPE_GET_M
  elif type_ == 'puts': msg.type_ = CoherentMemReqMsg.TYPE_PUT_S
  elif type_ == 'putm': msg.type_ = CoherentMemReqMsg.TYPE_PUT_M
  elif type_ == 'in_s': msg.type_ = CoherentMemReqMsg.TYPE_WRITE_INIT_S
  elif type_ == 'in_m': msg.type_ = CoherentMemReqMsg.TYPE_WRITE_INIT_M
  elif type_ == 'fwds': msg.type_ = CoherentMemReqMsg.TYPE_FWD_GET_S
  elif type_ == 'fwdm': msg.type_ = CoherentMemReqMsg.TYPE_FWD_GET_M
  elif type_ == 'inv': msg.type_ = CoherentMemReqMsg.TYPE_INV

  msg.src    = src
  msg.addr   = addr
  msg.opaque = opaque
  msg.len    = len
  msg.data   = data
  return msg

def resp( type_, opaque, test, len, data ):
  msg = CoherentMemRespMsg()

  if   type_ == 'data': msg.type_ = CoherentMemRespMsg.TYPE_DATA
  elif type_ == 'ack': msg.type_ = CoherentMemRespMsg.TYPE_PUT_ACK

  msg.opaque = opaque
  msg.len    = len
  msg.test   = test
  msg.data   = data
  return msg


def test_generic():
  req_msgs = [
    #     src    type    opq   addr      len  data
    req(  0x0,  'gets', 0x00, 0x00000000, 0, 0          ),
    req(  0x1,  'gets', 0x01, 0x00000000, 0, 0          ),
    req(  0x1,  'gets', 0x02, 0x00000010, 0, 0          ),
    req(  0x0,  'gets', 0x03, 0x00000010, 0, 0          ),
    req(  0x0,  'getm', 0x04, 0x00000010, 0, 0          ),
    req(  0x1,  'getm', 0x05, 0x00000010, 0, 0          ),
    req(  0x0,  'gets', 0x06, 0x00000010, 0, 0          ),
    req(  0x1,  'putm', 0x07, 0x00000010, 0, 0xbeefbeef ),
    req(  0x0,  'getm', 0x08, 0x00000010, 0, 0          ),
    ]

  resp_1_msgs = [
    #     type  opq test len  data
    resp('data', 0x00, 1, 0, 0xdeadbeef ),
    resp('data', 0x03, 0, 0, 0x00c0ffee ),
    resp('data', 0x04, 3, 0, 0x00c0ffee ),
    resp('data', 0x08, 3, 0, 0xbeefbeef ),
    ]

  resp_2_msgs = [
    #     type  opq test len  data
    resp('data', 0x01, 0, 0, 0xdeadbeef ),
    resp('data', 0x02, 1, 0, 0x00c0ffee ),
    resp('ack', 0x7,   0, 0, 0          ),
    ]

  fwd_1_msgs = [
    req(  0x2,  'fwdm', 0x05, 0x00000010, 0, 0          ),
    ]

  fwd_2_msgs = [
    req(  0x2,  'inv', 0x04, 0x00000010, 0, 0          ),
    req(  0x2,  'fwds', 0x06, 0x00000010, 0, 0          ),
    req(  0x2,  'inv', 0x08, 0x00000010, 0, 0          ),
    ]

  # Instantiate testharness
  harness = TestHarness( req_msgs, resp_1_msgs, resp_2_msgs, fwd_1_msgs, fwd_2_msgs,
                         0, 0,
                         0, 0,
                         CoherentCacheFL, False, False )
  mem = [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
    ]
  # Load memory before the test
  harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, False )

