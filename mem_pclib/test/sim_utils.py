"""
=========================================================================
sim_util.py
=========================================================================
Utilty functions for running a testing simulation

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 21 Decemeber 2019
"""

import struct
import random
from pymtl3 import *

from pymtl3.stdlib.test.test_srcs    import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks   import TestSinkCL, TestSinkRTL
from pymtl3.stdlib.cl.MemoryCL       import MemoryCL
from pymtl3.stdlib.ifcs.SendRecvIfc  import RecvCL2SendRTL, RecvIfcRTL, RecvRTL2SendCL, SendIfcRTL
from pymtl3.passes.backends.verilog  import TranslationImportPass, VerilatorImportConfigs
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg as mk_cache_msg

# cifer specific memory req/resp msg
from ifcs.MemMsg import mk_mem_msg

from .proc_model import ProcModel
from .MemoryCL   import MemoryCL as CiferMemoryCL

from blocking_cache.BlockingCacheFL import ModelCache

#----------------------------------------------------------------------
# Run the simulation
#---------------------------------------------------------------------
def run_sim( th, max_cycles = 1000, dump_vcd = False, translation='zeros', trace=2 ):
  # print (" -----------starting simulation----------- ")
  if translation:
    th.cache.verilog_translate_import = True
    th.cache.config_verilog_import = VerilatorImportConfigs(
          vl_xinit = translation, # init all bits as zeros, ones, or rand
          vl_trace = True if dump_vcd else False, # view vcd using gtkwave
          vl_Wno_list=['UNOPTFLAT', 'WIDTH', 'UNSIGNED'],
      )
    th = TranslationImportPass()( th )

  th.apply( SimulationPass() )
  th.sim_reset()
  ncycles  = 0
  print("")
  while not th.done() and ncycles < max_cycles:
    th.tick()
    print ("{:3d}: {}".format(ncycles, th.line_trace(trace)))
    ncycles += 1
  # check timeout
  assert ncycles < max_cycles
  th.tick()
  th.tick()

#----------------------------------------------------------------------
# Generate req/response pair from the requests using ref model
#---------------------------------------------------------------------
def gen_req_resp( reqs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
 associativity, cacheSize):

  cache = ModelCache(cacheSize, associativity, 0, CacheReqType, CacheRespType, 
                     MemReqType, MemRespType, mem)
  for request in reqs:
    if request.type_ == MemMsgType.READ:
      cache.read(request.addr, request.opaque, request.len)
    elif request.type_ == MemMsgType.WRITE:
      cache.write(request.addr, request.data, request.opaque, request.len)
    elif request.type_ == MemMsgType.WRITE_INIT:
      cache.init(request.addr, request.data, request.opaque, request.len)
    elif request.type_ >= MemMsgType.AMO_ADD:
      cache.amo(request.addr, request.data, request.opaque, request.type_)
  return cache.get_transactions()

def rand_mem(addr_min=0, addr_max=0xfff):
  '''
  Randomly generate start state for memory
  :returns: list of memory addresses w/ random data values
  '''
  mem = []
  curr_addr = addr_min
  while curr_addr <= addr_max:
    mem.append(curr_addr)
    mem.append(random.randint(0,0xffffffff))
    curr_addr += 4
  return mem

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, src_msgs, sink_msgs, stall_prob, latency, src_delay,
                 sink_delay, CacheModel, CacheReqType, CacheRespType,
                 MemReqType, MemRespType, cacheSize=128, associativity=1 ):
    # Instantiate models
    s.src   = TestSrcRTL(CacheReqType, src_msgs, src_delay, src_delay)
    s.proc_model = ProcModel(CacheReqType, CacheRespType)
    s.cache = CacheModel(CacheReqType, CacheRespType, MemReqType, MemRespType,
                         cacheSize, associativity)
    s.mem   = CiferMemoryCL( 1, [(MemReqType, MemRespType)], latency) # Use our own modified mem
    s.cache2mem = RecvRTL2SendCL(MemReqType)
    s.mem2cache = RecvCL2SendRTL(MemRespType)
    s.sink  = TestSinkRTL(CacheRespType, sink_msgs, src_delay, sink_delay)

    # Set the test signals to better model the processor

    # Connect the src and sink to model proc
    s.src.send  //= s.proc_model.proc.req
    s.sink.recv //= s.proc_model.proc.resp
    # Connect the proc model to the cache
    s.proc_model.cache //= s.cache.mem_minion_ifc

    # Connect the cache req and resp ports to test memory
    connect( s.mem.ifc[0].resp, s.mem2cache.recv )
    connect( s.cache.mem_master_ifc.resp, s.mem2cache.send )
    connect( s.cache.mem_master_ifc.req, s.cache2mem.recv )
    connect( s.mem.ifc[0].req, s.cache2mem.send )

  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s, trace ):
    return s.src.line_trace() + " " + s.cache.line_trace() + " " \
        + s.proc_model.line_trace() + s.mem.line_trace()  + " " + s.sink.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128 # cacheline bitwidth

CacheReqType, CacheRespType = mk_cache_msg(obw, abw, dbw)
MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)

def decode_type( type_ ):
  # type_ as string
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  elif type_ == 'ad': type_ = MemMsgType.AMO_ADD
  elif type_ == 'an': type_ = MemMsgType.AMO_AND  
  elif type_ == 'or': type_ = MemMsgType.AMO_OR   
  elif type_ == 'sw': type_ = MemMsgType.AMO_SWAP 
  elif type_ == 'mi': type_ = MemMsgType.AMO_MIN  
  elif type_ == 'mu': type_ = MemMsgType.AMO_MINU 
  elif type_ == 'mx': type_ = MemMsgType.AMO_MAX  
  elif type_ == 'xu': type_ = MemMsgType.AMO_MAXU 
  elif type_ == 'xo': type_ = MemMsgType.AMO_XOR  
  
  return type_ # as appropriate int

def req( type_, opaque, addr, len, data ):
  type_ = decode_type( type_ )
  return CacheReqType( type_, opaque, addr, len, data )

def resp( type_, opaque, test, len, data ):
  type_ = decode_type( type_ )
  return CacheRespType( type_, opaque, test, len, data )
