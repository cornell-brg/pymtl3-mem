#=========================================================================
# CoherentCacheFL_test.py
#=========================================================================

from __future__ import print_function

import pytest
import random
import struct

from pymtl      import *
from pclib.test import mk_test_case_table, run_sim
from pclib.test import TestSource

from pclib.ifcs import MemMsg,    MemReqMsg,    MemRespMsg
from pclib.ifcs import MemMsg4B,  MemReqMsg4B,  MemRespMsg4B
from pclib.ifcs import MemMsg16B, MemReqMsg16B, MemRespMsg16B

from ifcs.CoherentMemMsg import CoherentMemReqMsg, CoherentMemRespMsg, CoherentMemMsg16B

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

  def __init__( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, check_test, dump_vcd, test_verilog=False ):

    # Messge type

    cache_msgs = CoherentMemMsg16B()
    mem_msgs   = CoherentMemMsg16B()

    # Instantiate models

    s.src   = TestSource   ( cache_msgs.req,  src_msgs,  src_delay  )
    s.mem   = TestMemory   ( mem_msgs, 1, stall_prob, latency )
    s.sink  = TestCacheSink( cache_msgs.resp, sink_msgs, sink_delay, check_test )


    # Connect

    s.connect( s.src.out,  s.mem.reqs     )
    s.connect( s.sink.in_, s.mem.resps    )


  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.src.done and s.sink.done

  def line_trace( s ):
    return s.src.line_trace() + " "  \
         + s.mem.line_trace() + " " + s.sink.line_trace()

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

  msg.src = src
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

#----------------------------------------------------------------------
# Test Case: read hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def gets_after_inits( base_addr ):
  return [
    #    src    type  opq  addr      len data                type  opq  test len data
    req( 0x0,  'in_s', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'ack', 0x0, 1,   0,  0          ),
    req( 0x0,  'gets', 0x1, base_addr, 0, 0          ), resp( 'data', 0x1, 0,   0,  0xdeadbeef ),
  ]

#----------------------------------------------------------------------
# Test Case: read hit/miss path, many requests
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def gets_many_inits( base_addr ):
  array = []
  for i in xrange(4):
    #                   src  type  opq  addr          len data

    array.append(req(   0x0,   'in_s', 0x0, base_addr+32*i, 0, i ))
    #                  type  opq  test          len data
    array.append(resp(  0x0,   'in_s', 0x0, 1,             0, 0 ))

  for i in xrange(4):
    array.append(req(  'gets', 0x1, base_addr+32*i, 0, 0 ))
    array.append(resp( 'gets', 0x1, 0,             0, i ))

  return array

#-------------------------------------------------------------------------
# Test Case: read miss path
#-------------------------------------------------------------------------

def gets_after_gets_msg( base_addr ):
  return [
    #    src    type  opq   addr      len  data                    type  opq test len  data
    req( 0x0,   'gets', 0x00, 0x00000000, 0, 0          ), resp('data', 0x00, 1, 0, 0xdeadbeef ), # read word  0x00000000
    req( 0x0,   'gets', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 1, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x0,   'gets', 0x02, 0x00000010, 0, 0          ), resp('data', 0x02, 0, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x0,   'gets', 0x03, 0x00000010, 0, 0          ), resp('data', 0x03, 0, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x1,   'gets', 0x04, 0x00000010, 0, 0          ), resp('data', 0x04, 0, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x1,   'gets', 0x05, 0x00000010, 0, 0          ), resp('data', 0x05, 0, 0, 0x00c0ffee ), # read word  0x00000010
  ]

# Data to be loaded into memory before running the test

def gets_after_gets_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]

#-------------------------------------------------------------------------
# Test cases: I -> S -> I
#-------------------------------------------------------------------------

def I_S_I_msg( base_addr ):
  return [
    #     src   type    opq   addr      len  data                type  opq test len  data
    req(  0x0,  'gets', 0x00, 0x00000000, 0, 0          ), resp('data', 0x00, 1, 0, 0xdeadbeef ), # read word  0x00000000
    req(  0x0,  'gets', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 1, 0, 0x00c0ffee ), # read word  0x00000010
    req(  0x0,  'puts', 0x02, 0x00000000, 0, 0          ), resp('ack',  0x02, 5, 0, 0x0        ), # evict word 0x00000000
    req(  0x0,  'puts', 0x03, 0x00000010, 0, 0          ), resp('ack',  0x03, 5, 0, 0x0        ), # evict word 0x00000010
  ]

def I_S_I_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]

#-------------------------------------------------------------------------
# Test cases: I -> S -> S -> I
#-------------------------------------------------------------------------

def I_S_S_I_msg( base_addr ):
  return [
    #    src    type    opq   addr      len  data                type  opq test len  data
    req( 0x0,   'gets', 0x00, 0x00000000, 0, 0          ), resp('data', 0x00, 1, 0, 0xdeadbeef ), # read word  0x00000000
    req( 0x0,   'gets', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 1, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x1,   'gets', 0x02, 0x00000010, 0, 0          ), resp('data', 0x02, 0, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x0,   'puts', 0x03, 0x00000000, 0, 0          ), resp('ack',  0x03, 5, 0, 0x0        ), # evict word 0x00000000
    req( 0x0,   'puts', 0x04, 0x00000010, 0, 0          ), resp('ack',  0x04, 0, 0, 0x0        ), # evict word 0x00000010
    req( 0x1,   'puts', 0x05, 0x00000010, 0, 0          ), resp('ack',  0x05, 5, 0, 0x0        ), # evict word 0x00000010
  ]

def I_S_S_I_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]
#-------------------------------------------------------------------------
# Test cases: I -> M -> I
#-------------------------------------------------------------------------

def I_M_I_msg( base_addr ):
  return [
    #    src    type    opq   addr      len  data                type  opq test len  data
    req( 0x0,  'getm', 0x00, 0x00000000, 0, 0          ), resp('data', 0x00, 2, 0, 0xdeadbeef ), # read word  0x00000000
    req( 0x0,  'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 2, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x0,  'putm', 0x02, 0x00000000, 0, 0          ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000000
    req( 0x0,  'putm', 0x03, 0x00000010, 0, 0          ), resp('ack',  0x03, 6, 0, 0x0        ), # evict word 0x00000010
  ]

def I_M_I_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]

#-------------------------------------------------------------------------
# Test cases: I -> S -> M -> I
#-------------------------------------------------------------------------

def I_S_M_I_msg( base_addr ):
  return [
    #    src type    opq   addr      len  data                type  opq test len  data
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c0ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0          ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
  ]

def I_S_M_I_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]


def I_S_M_I_20x_msg( base_addr ):
  return [
    #    src    type    opq   addr      len  data                type  opq test len  data
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c0ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c0ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c1ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c1ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c1ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c2ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c2ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c2ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c3ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c3ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c3ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c4ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c4ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c4ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c5ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c5ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c5ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c6ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c6ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c6ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c7ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c7ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c7ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c8ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c8ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c8ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c9ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c9ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c9ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c1ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c1ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c1ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c2ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c2ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c2ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c3ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c3ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c3ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c4ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c4ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c4ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c5ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c5ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c5ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c6ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c6ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c6ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c7ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c7ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c7ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c8ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c8ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c8ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c9ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
    req( 0x0,   'gets', 0x00, 0x00000010, 0, 0          ), resp('data', 0x00, 1, 0, 0x00c9ffee ), # read word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 3, 0, 0x00c9ffee ), # upgr word  0x00000010
    req( 0x0,   'putm', 0x02, 0x00000010, 0, 0x00c0ffee ), resp('ack',  0x02, 6, 0, 0x0        ), # evict word 0x00000010
  ]

def I_S_M_I_20x_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]
#-------------------------------------------------------------------------
# Test cases: puts I/M
#-------------------------------------------------------------------------

def puts_IM_msg( base_addr ):
  return [
    #    src    type    opq   addr      len  data                type  opq test len  data
    req( 0x0,   'puts', 0x00, 0x00000000, 0, 0          ), resp('ack',  0x00, 0, 0, 0x0        ), # evict word  0x00000010
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 2, 0, 0x00c0ffee ), # upgr word  0x00000010
    req( 0x1,   'puts', 0x02, 0x00000010, 0, 0          ), resp('ack',  0x02, 0, 0, 0x0        ), # evict word  0x00000010
  ]

def puts_IM_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]

#-------------------------------------------------------------------------
# Test cases: putm I
#-------------------------------------------------------------------------

def putm_I_msg( base_addr ):
  return [
    #    src    type    opq   addr      len  data                type  opq test len  data
    req( 0x0,   'putm', 0x00, 0x00000000, 0, 0          ), resp('ack',  0x00, 0, 0, 0x0        ), # evict word  0x00000000
    req( 0x0,   'gets', 0x01, 0x00000000, 0, 0xdeadbeef ), resp('data', 0x01, 1, 0, 0xdeadbeef ), # read  word  0x00000000
  ]

def putm_I_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]

#-------------------------------------------------------------------------
# Test cases: putm M
#-------------------------------------------------------------------------

def putm_M_msg( base_addr ):
  return [
    #    src     type    opq   addr      len  data                type  opq test len  data
    req( 0x0,   'getm', 0x01, 0x00000010, 0, 0          ), resp('data', 0x01, 2, 0, 0x00c0ffee ), # upgr word  0x00000010
    req( 0x1,   'putm', 0x02, 0x00000010, 0, 0          ), resp('ack',  0x02, 0, 0, 0x0        ), # evict word  0x00000010
  ]

def putm_M_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0xdeadbeef,
    0x00000010, 0x00c0ffee,
  ]
#-------------------------------------------------------------------------
# Test cases: more on read-hit path
#-------------------------------------------------------------------------

def read_hit_1word_dirty( base_addr ):
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
    req( 'wr', 0x1, base_addr, 0, 0xbabababa ), resp( 'wr', 0x1, 1, 0, 0          ),
    req( 'rd', 0x2, base_addr, 0, 0          ), resp( 'rd', 0x2, 1, 0, 0xbabababa ),
  ]

def read_hit_1line_clean( base_addr ):
  return [
    req( 'in', 0x0, base_addr,    0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
    req( 'in', 0x1, base_addr+4,  0, 0xcafecafe ), resp( 'in', 0x1, 0, 0, 0          ),
    req( 'in', 0x2, base_addr+8,  0, 0xfafafafa ), resp( 'in', 0x2, 0, 0, 0          ),
    req( 'in', 0x3, base_addr+12, 0, 0xbabababa ), resp( 'in', 0x3, 0, 0, 0          ),
    req( 'rd', 0x4, base_addr,    0, 0          ), resp( 'rd', 0x4, 1, 0, 0xdeadbeef ),
    req( 'rd', 0x5, base_addr+4,  0, 0          ), resp( 'rd', 0x5, 1, 0, 0xcafecafe ),
    req( 'rd', 0x6, base_addr+8,  0, 0          ), resp( 'rd', 0x6, 1, 0, 0xfafafafa ),
    req( 'rd', 0x7, base_addr+12, 0, 0          ), resp( 'rd', 0x7, 1, 0, 0xbabababa ),
  ]

#-------------------------------------------------------------------------
# Test cases: more on write-hit path
#-------------------------------------------------------------------------

def write_hit_1word_dirty( base_addr ):
  return [
    #    type  opq   addr      len data               type  opq   test len data
    req( 'in', 0x00, base_addr, 0, 0x0a0b0c0d ), resp('in', 0x00, 0,   0,  0          ), # write word  0x00000000
    req( 'wr', 0x01, base_addr, 0, 0xbeefbeeb ), resp('wr', 0x01, 1,   0,  0          ), # write word  0x00000000
    req( 'wr', 0x02, base_addr, 0, 0xc0ffeebb ), resp('wr', 0x02, 1,   0,  0          ), # write word  0x00000000
    req( 'rd', 0x03, base_addr, 0, 0          ), resp('rd', 0x03, 1,   0,  0xc0ffeebb ), # read  word  0x00000000
  ]

#----------------------------------------------------------------------
# Test Case: random
#----------------------------------------------------------------------

def random_msgs( base_addr ):

  rgen = random.Random()
  rgen.seed(0xa4e28cc2)

  vmem = [ rgen.randint(0,0xffffffff) for _ in range(20) ]
  msgs = []

  for i in range(20):
    msgs.extend([
      req( 'wr', i, base_addr+4*i, 0, vmem[i] ), resp( 'wr', i, 2, 0, 0 ),
    ])

  for i in range(20):
    idx = rgen.randint(0,19)

    if rgen.randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', i, base_addr+4*idx, 0, 0 ), resp( 'rd', i, 2, 0, correct_data ),
      ])

    else:

      new_data = rgen.randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, base_addr+4*idx, 0, new_data ), resp( 'wr', i, 2, 0, 0 ),
      ])

  return msgs

#----------------------------------------------------------------------
# Test Case: stream
#----------------------------------------------------------------------

def stream_msgs( base_addr ):
  msgs = []
  for i in range(20):
    msgs.extend([
      req( 'wr', i, base_addr+4*i, 0, i ), resp( 'wr', i, 2, 0, 0 ),
      req( 'rd', i, base_addr+4*i, 0, 0 ), resp( 'rd', i, 2, 0, i ),
    ])

  return msgs

#-------------------------------------------------------------------------
# Test Case: write miss path
#-------------------------------------------------------------------------

def write_miss_1word_msg( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    req( 'rd', 0x00, 0x00000000, 0, 0          ), resp('rd', 0x00, 0, 0, 0x0e5ca18d ), # read  word 0x00000000
    req( 'rd', 0x01, 0x00000000, 0, 0          ), resp('rd', 0x01, 1, 0, 0x0e5ca18d ), # read  word 0x00000000
    req( 'rd', 0x02, 0x00000004, 0, 0          ), resp('rd', 0x02, 1, 0, 0x00ba11ad ), # read  word 0x00000004
    req( 'wr', 0x03, 0x00000100, 0, 0x00e1de57 ), resp('wr', 0x03, 0, 0, 0          ), # write word 0x00000100
    req( 'rd', 0x04, 0x00000100, 0, 0          ), resp('rd', 0x04, 1, 0, 0x00e1de57 ), # read  word 0x00000100
  ]

# Data to be loaded into memory before running the test

def write_miss_1word_mem( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0x0e5ca18d,
    0x00000004, 0x00ba11ad,
  ]

#-------------------------------------------------------------------------
# Test Case: force eviction
#-------------------------------------------------------------------------

def evict_msg( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    req( 'wr', 0x00, 0x00000000, 0, 0x0a0b0c0d ), resp('wr', 0x00, 0, 0, 0          ), # write word  0x00000000
    req( 'wr', 0x01, 0x00000004, 0, 0x0e0f0102 ), resp('wr', 0x01, 1, 0, 0          ), # write word  0x00000004
    req( 'rd', 0x02, 0x00000000, 0, 0          ), resp('rd', 0x02, 1, 0, 0x0a0b0c0d ), # read  word  0x00000000
    req( 'rd', 0x03, 0x00000004, 0, 0          ), resp('rd', 0x03, 1, 0, 0x0e0f0102 ), # read  word  0x00000004

    # try forcing some conflict misses to force evictions

    req( 'wr', 0x04, 0x00004000, 0, 0xcafecafe ), resp('wr', 0x04, 0, 0, 0x0        ), # write word  0x00004000
    req( 'wr', 0x05, 0x00004004, 0, 0xebabefac ), resp('wr', 0x05, 1, 0, 0x0        ), # write word  0x00004004
    req( 'rd', 0x06, 0x00004000, 0, 0          ), resp('rd', 0x06, 1, 0, 0xcafecafe ), # read  word  0x00004000
    req( 'rd', 0x07, 0x00004004, 0, 0          ), resp('rd', 0x07, 1, 0, 0xebabefac ), # read  word  0x00004004

    req( 'wr', 0x00, 0x00008000, 0, 0xaaaeeaed ), resp('wr', 0x00, 0, 0, 0x0        ), # write word  0x00008000
    req( 'wr', 0x01, 0x00008004, 0, 0x0e0f0102 ), resp('wr', 0x01, 1, 0, 0x0        ), # write word  0x00008004
    req( 'rd', 0x03, 0x00008004, 0, 0          ), resp('rd', 0x03, 1, 0, 0x0e0f0102 ), # read  word  0x00008004
    req( 'rd', 0x02, 0x00008000, 0, 0          ), resp('rd', 0x02, 1, 0, 0xaaaeeaed ), # read  word  0x00008000

    req( 'wr', 0x04, 0x0000c000, 0, 0xcacafefe ), resp('wr', 0x04, 0, 0, 0x0        ), # write word  0x0000c000
    req( 'wr', 0x05, 0x0000c004, 0, 0xbeefbeef ), resp('wr', 0x05, 1, 0, 0x0        ), # write word  0x0000c004
    req( 'rd', 0x06, 0x0000c000, 0, 0          ), resp('rd', 0x06, 1, 0, 0xcacafefe ), # read  word  0x0000c000
    req( 'rd', 0x07, 0x0000c004, 0, 0          ), resp('rd', 0x07, 1, 0, 0xbeefbeef ), # read  word  0x0000c004

    req( 'wr', 0xf5, 0x0000c004, 0, 0xdeadbeef ), resp('wr', 0xf5, 1, 0, 0x0        ), # write word  0x0000c004
    req( 'wr', 0xd5, 0x0000d004, 0, 0xbeefbeef ), resp('wr', 0xd5, 0, 0, 0x0        ), # write word  0x0000d004
    req( 'wr', 0xe5, 0x0000e004, 0, 0xbeefbeef ), resp('wr', 0xe5, 0, 0, 0x0        ), # write word  0x0000e004
    req( 'wr', 0xc5, 0x0000f004, 0, 0xbeefbeef ), resp('wr', 0xc5, 0, 0, 0x0        ), # write word  0x0000f004

    # now refill those same cache lines to make sure we wrote to the
    # memory earlier and make sure we can read from memory

    req( 'rd', 0x06, 0x00004000, 0, 0          ), resp('rd', 0x06, 0, 0, 0xcafecafe ), # read  word  0x00004000
    req( 'rd', 0x07, 0x00004004, 0, 0          ), resp('rd', 0x07, 1, 0, 0xebabefac ), # read  word  0x00004004
    req( 'rd', 0x02, 0x00000000, 0, 0          ), resp('rd', 0x02, 0, 0, 0x0a0b0c0d ), # read  word  0x00000000
    req( 'rd', 0x03, 0x00000004, 0, 0          ), resp('rd', 0x03, 1, 0, 0x0e0f0102 ), # read  word  0x00000004
    req( 'rd', 0x03, 0x00008004, 0, 0          ), resp('rd', 0x03, 0, 0, 0x0e0f0102 ), # read  word  0x00008004
    req( 'rd', 0x02, 0x00008000, 0, 0          ), resp('rd', 0x02, 1, 0, 0xaaaeeaed ), # read  word  0x00008000
    req( 'rd', 0x06, 0x0000c000, 0, 0          ), resp('rd', 0x06, 0, 0, 0xcacafefe ), # read  word  0x0000c000
    req( 'rd', 0x07, 0x0000c004, 0, 0          ), resp('rd', 0x07, 1, 0, 0xdeadbeef ), # read  word  0x0000c004
    req( 'rd', 0x07, 0x0000d004, 0, 0          ), resp('rd', 0x07, 0, 0, 0xbeefbeef ), # read  word  0x0000d004
    req( 'rd', 0x08, 0x0000e004, 0, 0          ), resp('rd', 0x08, 0, 0, 0xbeefbeef ), # read  word  0x0000e004
    req( 'rd', 0x09, 0x0000f004, 0, 0          ), resp('rd', 0x09, 0, 0, 0xbeefbeef ), # read  word  0x0000f004
  ]

#-------------------------------------------------------------------------
# Test Case: test direct-mapped
#-------------------------------------------------------------------------
# Test cases designed for direct-mapped cache. We should set check_test
# to False if we use it to test set-associative cache.

def dir_mapped_long0_msg( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    # Write to cacheline 0
    req( 'wr', 0x00, 0x00000000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ),
    req( 'wr', 0x01, 0x00000004, 0, 0xffffff01), resp( 'wr', 0x01, 1, 0, 0          ),
    req( 'wr', 0x02, 0x00000008, 0, 0xffffff02), resp( 'wr', 0x02, 1, 0, 0          ),
    req( 'wr', 0x03, 0x0000000c, 0, 0xffffff03), resp( 'wr', 0x03, 1, 0, 0          ),
    # Write to cacheline 0
    req( 'wr', 0x04, 0x00001000, 0, 0xffffff04), resp( 'wr', 0x04, 0, 0, 0          ),
    req( 'wr', 0x05, 0x00001004, 0, 0xffffff05), resp( 'wr', 0x05, 1, 0, 0          ),
    req( 'wr', 0x06, 0x00001008, 0, 0xffffff06), resp( 'wr', 0x06, 1, 0, 0          ),
    req( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), resp( 'wr', 0x07, 1, 0, 0          ),
    # Evict cache 0
    req( 'rd', 0x08, 0x00002000, 0, 0         ), resp( 'rd', 0x08, 0, 0, 0x00facade ),
    # Read again from same cacheline
    req( 'rd', 0x09, 0x00002004, 0, 0         ), resp( 'rd', 0x09, 1, 0, 0x05ca1ded ),
    # Read from cacheline 0
    req( 'rd', 0x0a, 0x00001004, 0, 0         ), resp( 'rd', 0x0a, 0, 0, 0xffffff05 ),
    # Write to cacheline 0
    req( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), resp( 'wr', 0x0b, 1, 0, 0          ),
    # Read that back
    req( 'rd', 0x0c, 0x0000100c, 0, 0         ), resp( 'rd', 0x0c, 1, 0, 0xffffff09 ),
    # Evict cache 0 again
    req( 'rd', 0x0d, 0x00000000, 0, 0         ), resp( 'rd', 0x0d, 0, 0, 0xffffff00 ),
    # Testing cacheline 7 now
    # Write to cacheline 7
    req( 'wr', 0x10, 0x00000070, 0, 0xffffff00), resp( 'wr', 0x10, 0, 0, 0          ),
    req( 'wr', 0x11, 0x00000074, 0, 0xffffff01), resp( 'wr', 0x11, 1, 0, 0          ),
    req( 'wr', 0x12, 0x00000078, 0, 0xffffff02), resp( 'wr', 0x12, 1, 0, 0          ),
    req( 'wr', 0x13, 0x0000007c, 0, 0xffffff03), resp( 'wr', 0x13, 1, 0, 0          ),
    # Write to cacheline 7
    req( 'wr', 0x14, 0x00001070, 0, 0xffffff04), resp( 'wr', 0x14, 0, 0, 0          ),
    req( 'wr', 0x15, 0x00001074, 0, 0xffffff05), resp( 'wr', 0x15, 1, 0, 0          ),
    req( 'wr', 0x16, 0x00001078, 0, 0xffffff06), resp( 'wr', 0x16, 1, 0, 0          ),
    req( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), resp( 'wr', 0x17, 1, 0, 0          ),
    # Evict cacheline 7
    req( 'rd', 0x18, 0x00002070, 0, 0         ), resp( 'rd', 0x18, 0, 0, 0x70facade ),
    # Read again from same cacheline
    req( 'rd', 0x19, 0x00002074, 0, 0         ), resp( 'rd', 0x19, 1, 0, 0x75ca1ded ),
    # Read from cacheline 7
    req( 'rd', 0x1a, 0x00001074, 0, 0         ), resp( 'rd', 0x1a, 0, 0, 0xffffff05 ),
    # Write to cacheline 7 way 1 to see if cache hits properly
    req( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), resp( 'wr', 0x1b, 1, 0, 0          ),
    # Read that back
    req( 'rd', 0x1c, 0x0000107c, 0, 0         ), resp( 'rd', 0x1c, 1, 0, 0xffffff09 ),
    # Evict cacheline 0 again
    req( 'rd', 0x1d, 0x00000070, 0, 0         ), resp( 'rd', 0x1d, 0, 0, 0xffffff00 ),
  ]

def dir_mapped_long0_mem( base_addr ):
  return [
    # addr      # data (in int)
    0x00002000, 0x00facade,
    0x00002004, 0x05ca1ded,
    0x00002070, 0x70facade,
    0x00002074, 0x75ca1ded,
  ]

#-------------------------------------------------------------------------
# Test table for generic test
#-------------------------------------------------------------------------

test_case_table_generic = mk_test_case_table([
  (                         "msg_func               mem_data_func         stall lat src sink"),
  [ "gets_after_inits",      gets_after_inits,      None,                 0.0,  0,  0,  0    ],
  [ "gets_after_gets",       gets_after_gets_msg,   gets_after_gets_mem,  0.0,  0,  0,  0    ],
  [ "I_S_I",                 I_S_I_msg,             I_S_I_mem,            0.0,  0,  0,  0    ],
  [ "I_S_S_I",               I_S_S_I_msg,           I_S_S_I_mem,          0.0,  0,  0,  0    ],
  [ "I_M_I",                 I_M_I_msg,             I_M_I_mem,            0.0,  0,  0,  0    ],
  [ "I_S_M_I",               I_S_M_I_msg,           I_S_M_I_mem,          0.0,  0,  0,  0    ],
  [ "puts_IM",               puts_IM_msg,           puts_IM_mem,          0.0,  0,  0,  0    ],
  [ "putm_I",                putm_I_msg,            putm_I_mem,           0.0,  0,  0,  0    ],
  [ "putm_M",                putm_M_msg,            putm_M_mem,           0.0,  0,  0,  0    ],
  [ "I_S_M_I_20x",           I_S_M_I_20x_msg,       I_S_M_I_20x_mem,      0.0,  0,  0,  0    ],
  [ "I_S_M_I_20x_lat4",      I_S_M_I_20x_msg,       I_S_M_I_20x_mem,      0.0,  4,  0,  0    ],
  [ "I_S_M_I_20x_stall0.5",  I_S_M_I_20x_msg,       I_S_M_I_20x_mem,      0.5,  0,  0,  0    ],
  [ "I_S_M_I_20x_both",      I_S_M_I_20x_msg,       I_S_M_I_20x_mem,      0.5,  5,  0,  0    ],


  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # LAB TASK: Add test cases to this table
  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
  #[ "random",                random_msgs,           None,                 0.0,  0,  0,  0    ],
  #[ "random_stall0.5_lat0",  random_msgs,           None,                 0.5,  0,  0,  0    ],
  #[ "random_stall0.0_lat4",  random_msgs,           None,                 0.0,  4,  0,  0    ],
  #[ "random_stall0.5_lat4",  random_msgs,           None,                 0.5,  4,  0,  0    ],
  #[ "stream",                stream_msgs,           None,                 0.0,  0,  0,  0    ],
  #[ "stream_stall0.5_lat0",  stream_msgs,           None,                 0.5,  0,  0,  0    ],
  #[ "stream_stall0.0_lat4",  stream_msgs,           None,                 0.0,  4,  0,  0    ],
  #[ "stream_stall0.5_lat4",  stream_msgs,           None,                 0.5,  4,  0,  0    ],
  #[ "write_miss_1word",      write_miss_1word_msg,  write_miss_1word_mem, 0.0,  0,  0,  0    ],
  #[ "evict",                 evict_msg,             None,                 0.0,  0,  0,  0    ],
  #[ "evict_stall0.5_lat0",   evict_msg,             None,                 0.5,  0,  0,  0    ],
  #[ "evict_stall0.0_lat4",   evict_msg,             None,                 0.0,  4,  0,  0    ],
  #[ "evict_stall0.5_lat4",   evict_msg,             None,                 0.5,  4,  0,  0    ],

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

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
                         CoherentCacheFL, True, dump_vcd )
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, dump_vcd )

#-------------------------------------------------------------------------
# Test table for direct-mapped cache (baseline design)
#-------------------------------------------------------------------------

test_case_table_dir_mapped = mk_test_case_table([
  (                                  "msg_func              mem_data_func          stall lat src sink"),

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # LAB TASK: Add test cases to this table
  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  #[ "dir_maped_test_long0",           dir_mapped_long0_msg, dir_mapped_long0_mem,  0.0,  0,  0,  0    ],
  #[ "dir_maped_test_long0_lat4_3x14", dir_mapped_long0_msg, dir_mapped_long0_mem,  0.5,  4,  3,  14   ],

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

])

#@pytest.mark.parametrize( **test_case_table_dir_mapped )
#def test_dir_mapped( test_params, dump_vcd ):
#  msgs = test_params.msg_func( 0 )
#  if test_params.mem_data_func != None:
#    mem  = test_params.mem_data_func( 0 )
#  # Instantiate testharness
#  harness = TestHarness( msgs[::2], msgs[1::2],
#                         test_params.stall, test_params.lat,
#                         test_params.src, test_params.sink,
#                         CoherentCacheFL, True, dump_vcd )
#  # Load memory before the test
#  if test_params.mem_data_func != None:
#    harness.load( mem[::2], mem[1::2] )
#  # Run the test
#  run_sim( harness, dump_vcd )
#
