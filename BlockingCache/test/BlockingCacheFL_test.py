#=========================================================================
# BlockingCacheFL_test.py
#=========================================================================

import pytest
import struct
import random

from pymtl3 import *
from pymtl3.stdlib.cl.MemoryCL import MemoryCL
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvCL2SendRTL, RecvIfcRTL, RecvRTL2SendCL, SendIfcRTL  
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.test.test_srcs import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks import TestSinkCL, TestSinkRTL
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
# from BlockingCache.test.CacheMemory import MemoryCL

from pymtl3.passes.yosys import TranslationImportPass # Translation to Verilog


MemReqMsg4B, MemRespMsg4B = mk_mem_msg(8,32,32)
MemReqMsg16B, MemRespMsg16B = mk_mem_msg(8,32,128)
obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 512

#-------------------------------------------------------------------------
# ReqRespMsgTypes
#-------------------------------------------------------------------------

class ReqRespMsgTypes():
  def __init__(s, opq, addr, data):
    s.Req, s.Resp = mk_mem_msg(opq, addr, data)
    s.obw = opq
    s.abw = addr
    s.dbw = data

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):
  
  def construct( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, CacheModel, test_verilog=False ):
    
    CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
    MemMsg = ReqRespMsgTypes(obw, abw, clw)
    cacheSize = 8196 # size in bytes
    # Instantiate models
    s.src   = TestSrcRTL(CacheMsg.Req, src_msgs, src_delay)
    s.cache = CacheModel(cacheSize, CacheMsg, MemMsg)
    s.mem   = MemoryCL( 1, mem_ifc_dtypes=[(MemMsg.Req, MemMsg.Resp)], latency=latency)
    s.cache2mem = RecvRTL2SendCL(MemMsg.Req)
    s.mem2cache = RecvCL2SendRTL(MemMsg.Resp)
    s.sink  = TestSinkRTL(CacheMsg.Resp, sink_msgs, sink_delay)

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
         + s.mem.line_trace() + " " + s.sink.line_trace()

#-------------------------------------------------------------------------
# Translate Function for the cache
#-------------------------------------------------------------------------

def translate():
  # Translate the checksum unit and import it back in using the yosys
  # backend
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  MemMsg = ReqRespMsgTypes(obw, abw, clw)
  cacheSize = 8196 # size in bytes
  dut = BlockingCachePRTL(cacheSize, CacheMsg, MemMsg)
  dut.elaborate()
  dut.yosys_translate_import = True
  dut = TranslationImportPass(  )( dut )

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  msg = CacheMsg.Req()

  if   type_ == 'rd': msg.type_ = MemMsgType.READ
  elif type_ == 'wr': msg.type_ = MemMsgType.WRITE
  elif type_ == 'in': msg.type_ = MemMsgType.WRITE_INIT

  msg.addr   = addr
  msg.opaque = opaque
  msg.len    = len
  msg.data   = data
  return msg

def resp( type_, opaque, test, len, data ):
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  msg = CacheMsg.Resp()
  # print ("msg = " + str( msg))

  if   type_ == 'rd': msg.type_ = MemMsgType.READ
  elif type_ == 'wr': msg.type_ = MemMsgType.WRITE
  elif type_ == 'in': msg.type_ = MemMsgType.WRITE_INIT

  msg.opaque = opaque
  msg.len    = len
  msg.test   = test
  msg.data   = data

  return msg

#----------------------------------------------------------------------
# Run the simulation
#---------------------------------------------------------------------
def run_sim(th, max_cycles):
  # print (" -----------starting simulation----------- ")
  th.apply( DynamicSim )
  th.sim_reset()
  curr_cyc = 0
  print("")
  while not th.done():
    th.tick()
    print (str(curr_cyc) + " " + th.line_trace())
    curr_cyc += 1
    assert curr_cyc < max_cycles
  th.tick()


#----------------------------------------------------------------------
# Test Case: read hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_hit_1word_clean( base_addr=0 ):
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'in', 0x0, base_addr+0xff000000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x1, base_addr+0xff000000, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
  ]

#----------------------------------------------------------------------
# Test Case: read hit/miss path, many requests
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_hit_many_clean( base_addr=100 ):
  array = []
  for i in range(4):
    #                  type  opq  addr          len data
    array.append(req(  'in', i, ((base_addr+0x0f000000)<<2)+i*4, 0, i ))
    array.append(resp( 'in', i, 0,             0, 0 ))
  for i in range(4):
    array.append(req(  'rd', i, ((base_addr+0x0f000000)<<2)+i*4, 0, 0 ))
    array.append(resp( 'rd', i, 1,             0, i ))
  return array

#----------------------------------------------------------------------
# Test Case: read hit/miss path,random requests
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_hit_random_clean( base_addr=100 ):
  array = []
  test_amount = 4
  random.seed(0)
  addr = [(base_addr + random.randint(0,0xfffff)) << 2 for i in range(test_amount)]
  data = [random.randint(0,0xfffff) for i in range(test_amount)] 
  for i in range(test_amount):
    #                  type  opq  addr     len data
    array.append(req(  'in', i,   addr[i], 0,  data[i]))
    #                  type  opq  test     len data
    array.append(resp( 'in', i,   0,       0,  0 ))
  for i in range(test_amount):
    array.append(req(  'rd', i, addr[i], 0, 0 ))
    array.append(resp( 'rd', i, 1,       0, data[i] ))
  return array

#----------------------------------------------------------------------
# Test Case: write hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def write_hit_1word_clean( base_addr=0 ):
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'wr', 0x1, base_addr, 0, 0xffffffff ), resp( 'wr', 0x1, 1,   0,  0          ),
    req( 'rd', 0x2, base_addr, 0, 0          ), resp( 'rd', 0x2, 1,   0,  0xffffffff ),
  ]
#----------------------------------------------------------------------
# Test Case: write hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def write_hits_read_hits( base_addr=0 ):
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x1, base_addr, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
    req( 'wr', 0x2, base_addr, 0, 0xffffffff ), resp( 'wr', 0x2, 1,   0,  0          ),
    req( 'rd', 0x3, base_addr, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0xffffffff ),
  ]

#-------------------------------------------------------------------------
# Test table for generic test
#-------------------------------------------------------------------------

test_case_table_generic = mk_test_case_table([
  ( "                        msg_func               mem_data_func  stall lat src sink"),
  [ "read_hit_1word_clean",  read_hit_1word_clean,  None,          0.0,  0,  0,  0    ],
  [ "read_hit_many_clean",   read_hit_many_clean,   None,          0.0,  0,  0,  0    ],
  [ "read_hit_random_clean", read_hit_random_clean, None,          0.0,  0,  0,  0    ],
  [ "write_hit_1word_clean", write_hit_1word_clean, None,          0.0,  0,  0,  0    ],
  [ "write_hits_read_hits", write_hits_read_hits, None,          0.0,  0,  0,  0    ],
  [ "write_hits_read_hits", write_hits_read_hits, None,          0.5,  1,  0,  0    ],
])
@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params):
  msgs = test_params.msg_func( 100 )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( 100 )
  # Instantiate testharness
  th = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL, False)
  th.elaborate()
  # translate()
  # Load memory before the test
  if test_params.mem_data_func != None:
    th.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( th, max_cycles=20 )
