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

from pymtl3.stdlib.ifcs.mem_ifcs     import MemMasterIfcRTL, MemMinionIfcRTL
from pymtl3.stdlib.test.test_srcs    import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks   import TestSinkCL, TestSinkRTL
from pymtl3.stdlib.ifcs.SendRecvIfc  import RecvCL2SendRTL, RecvIfcRTL, RecvRTL2SendCL, SendIfcRTL
# from pymtl3.passes.backends.verilog  import (
#   TranslationImportPass, VerilatorImportConfigs, VerilogPlaceholderPass, VerilogTBGenPass
# )
from pymtl3.passes.backends.verilog  import (
  VerilatorImportPass, VerilogTBGenPass
)
# cifer specific memory req/resp msg
from mem_ifcs.MemMsg import MemMsgType, mk_mem_msg

from .ProcModel import ProcModel
from .MemoryCL  import MemoryCL as CiferMemoryCL
from .MulticoreModel import MulticoreModel

from blocking_cache.BlockingCacheFL import ModelCache
from blocking_cache.translate import replace_sram, sram_wrapper_file
import subprocess

#----------------------------------------------------------------------
# Run the simulation
#---------------------------------------------------------------------

def run_sim( th, cmdline_opts, max_cycles, trace, dump_vtb, sram_wrapper ):
  translation = bool(cmdline_opts['test_verilog'])
  vl_trace    = bool(cmdline_opts['dump_vcd'])
  xinit       = cmdline_opts['test_verilog']
  file_name   = str(th.cache.param) + ".v"
  if translation:
    th.cache.set_metadata( TranslationImportPass.enable, True )
    th.cache.set_metadata( VerilatorImportPass.vl_xinit, xinit )
    th.cache.set_metadata( VerilatorImportPass.vl_trace, vl_trace )
    th.cache.set_metadata( explicit_module_name, str(th.cache.param) )
    # TODO
    # th.cache.verilog_translate_import = True
    # th.cache.config_verilog_translate = TranslationConfigs(
    #   explicit_module_name = str(th.cache.param),
    # )
    # th.cache.config_verilog_import = VerilatorImportConfigs(
    #       vl_xinit = translation, # init all bits as zeros, ones, or rand
    #       vl_trace = True if dump_vcd else False, # view vcd using gtkwave
    #       vl_Wno_list=['UNOPTFLAT', 'WIDTH', 'UNSIGNED'],
    #   )
    
    # th.apply( VerilogPlaceholderPass() )
    th = TranslationImportPass()( th )

    if dump_vtb:
      th.cache.verilog_tbgen = dump_vtb
      th.apply( VerilogTBGenPass() )
    
    # Replace sram with wrapper
    if sram_wrapper: 
      replace_sram( file_name )
      bashCommand = f"cat {sram_wrapper_file} >> {file_name}"
      process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)
      output, error = process.communicate()

  th.apply( SimulationPass(print_line_trace=True) )
  th.sim_reset()
  # ncycles  = 0
  # print("")
  while not th.done() and th.sim_cycle_count() < max_cycles:
    th.sim_tick()
    # print ("{:3d}: {}".format(ncycles, th.line_trace(trace)))
    # ncycles += 1
 # Check timeout
  assert th.sim_cycle_count() < max_cycles
  th.sim_tick()
  th.sim_tick()
  th.sim_tick()

#----------------------------------------------------------------------
# Generate req/response pair from the requests using ref model
#---------------------------------------------------------------------

def gen_req_resp( reqs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
                  associativity, cacheSize ):
  cache = ModelCache( cacheSize, associativity, 0, CacheReqType, CacheRespType,
                      MemReqType, MemRespType, mem )
  for request in reqs:
    if request.type_ == MemMsgType.READ:
      cache.read(request.addr, request.opaque, request.len)
    elif request.type_ == MemMsgType.WRITE:
      cache.write(request.addr, request.data, request.opaque, request.len)
    elif request.type_ == MemMsgType.WRITE_INIT:
      cache.init(request.addr, request.data, request.opaque, request.len)
    elif request.type_ >= MemMsgType.AMO_ADD and request.type_ <= MemMsgType.AMO_XOR:
      cache.amo(request.addr, request.data, request.opaque, request.len, request.type_)
    elif request.type_ == MemMsgType.INV:
      cache.invalidate(request.opaque)
    elif request.type_ == MemMsgType.FLUSH:
      cache.flush(request.opaque)
    else:
      assert False, "FL model: Undefined transaction type"
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
    s.mem   = CiferMemoryCL( 1, [(MemReqType, MemRespType)],
                             stall_prob=stall_prob, latency=latency) # Use our own modified mem
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

  def line_trace( s ):
    return s.src.line_trace() + " " + s.cache.line_trace() + " " \
        + s.proc_model.line_trace() + s.mem.line_trace()  + " " + s.sink.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128 # cacheline bitwidth

CacheReqType, CacheRespType = mk_mem_msg(obw, abw, dbw, has_wr_mask=False)
MemReqType, MemRespType = mk_mem_msg(obw, abw, clw, has_wr_mask=True)

def decode_type( type_ ):
  # type_ as string
  if   type_ == 'rd':  type_ = MemMsgType.READ
  elif type_ == 'wr':  type_ = MemMsgType.WRITE
  elif type_ == 'in':  type_ = MemMsgType.WRITE_INIT
  elif type_ == 'ad':  type_ = MemMsgType.AMO_ADD
  elif type_ == 'an':  type_ = MemMsgType.AMO_AND
  elif type_ == 'or':  type_ = MemMsgType.AMO_OR
  elif type_ == 'sw':  type_ = MemMsgType.AMO_SWAP
  elif type_ == 'mi':  type_ = MemMsgType.AMO_MIN
  elif type_ == 'mu':  type_ = MemMsgType.AMO_MINU
  elif type_ == 'mx':  type_ = MemMsgType.AMO_MAX
  elif type_ == 'xu':  type_ = MemMsgType.AMO_MAXU
  elif type_ == 'xo':  type_ = MemMsgType.AMO_XOR
  elif type_ == 'inv': type_ = MemMsgType.INV
  elif type_ == 'fl':  type_ = MemMsgType.FLUSH
  return type_ # as appropriate int

def req( type_, opaque, addr, len, data ):
  type_ = decode_type( type_ )
  return CacheReqType( type_, opaque, addr, len, data )

def resp( type_, opaque, test, len, data ):
  type_ = decode_type( type_ )
  return CacheRespType( type_, opaque, test, len, data )

def mk_req( ReqType, msg ):
  out = [0]*len(msg)
  for i in range( 0, len(msg)):
    type_, opaque, addr, len_, data = msg[i]
    type_ = decode_type( type_ )
    out[i] = ReqType( type_, opaque, addr, len_, data )
  return out

def mk_req_resp( ReqRespType, msg ):
  out = [0]*len(msg)
  ReqType, RespType = ReqRespType
  for i in range( 0, len(msg), 2):
    type_, opaque, addr, len_, data = msg[i]
    type_ = decode_type( type_ )
    out[i] = ReqType( type_, opaque, addr, len_, data )
    type_, opaque, test, len_, data = msg[i+1]
    type_ = decode_type( type_ )
    out[i+1] = RespType( type_, opaque, test, len_, data )
  return out

class SingleCacheTestParams:
  def __init__( self, msg, mem, associativity, bitwidth_mem_data, bitwidth_cache_data, 
                cache_size=None):
    self.CacheReqType, self.CacheRespType = mk_mem_msg( obw, abw, bitwidth_cache_data, False )
    self.MemReqType, self.MemRespType = mk_mem_msg( obw, abw, bitwidth_mem_data, True )
    self.msg = mk_req_resp( (self.CacheReqType, self.CacheRespType), msg ) if msg else None 
    if cache_size == None:
      self.size = bitwidth_mem_data * 2 // 8 * associativity
    else:
      assert cache_size >= (bitwidth_mem_data * 2 // 8 * associativity), \
              "Cache size too small for param line size"
      self.size = cache_size
    self.associativity = associativity
    self.mem = mem

# Request wrapper for testing multi-cache configureations
# cache: transaction for that cache
# order: decides if transaction will happen sequentially or in parallel
def mreq( cache, order, type_, opaque, addr, len, data ):
  type_ = decode_type( type_ )
  return (cache, order, CacheReqType( type_, opaque, addr, len, data ))

#-------------------------------------------------------------------------
# CacheTestParams - Multicache
#-------------------------------------------------------------------------
# Test parameters for the cache

class CacheTestParams:
  def __init__( self, msgs, mem, CacheReqType, CacheRespType, MemReqType,
                MemRespType, associativity=[1], cache_size=[64], stall_prob=0,
                latency=1, src_delay=0, sink_delay=0 ):
    assert isinstance(associativity, list) and len(associativity) > 0, \
      f'associativity must be an array, len={len(associativity)}'
    assert isinstance(associativity, list) and len(cache_size) > 0, \
      f'cache_size must be an array, len={len(cache_size)}'
    assert len(associativity) == len(cache_size), \
      f'cache_size must equal to Assoc, cache_size={len(associativity)} Assoc={len(cache_size)}'
    self.msgs = msgs
    self.mem = mem
    self.CacheReqType = CacheReqType
    self.CacheRespType = CacheRespType
    self.MemReqType = MemReqType
    self.MemRespType = MemRespType
    self.associativity = associativity
    self.cache_size = cache_size
    self.stall_prob = stall_prob
    self.latency = latency
    self.src_delay = src_delay
    self.sink_delay = sink_delay
    self.ncaches = len(associativity)
    self.src_init_delay = 0
    self.sink_init_delay = 0
    # self.src_init_delay = [0] * self.ncaches
    # self.sink_init_delay = [0] * self.ncaches

#-------------------------------------------------------------------------
# MultiCacheTestHarness
#-------------------------------------------------------------------------

# Helper module to store all the caches for translation
class MultiCache( Component ):

  def construct( s, Cache, p ):
    s.p = p
    s.param = f'MultiCache_{p.ncaches}'
    s.mem_minion_ifc = [ MemMinionIfcRTL( p.CacheReqType, p.CacheRespType ) for i in range( p.ncaches ) ]
    s.mem_master_ifc = [ MemMasterIfcRTL( p.MemReqType, p.MemRespType ) for i in range( p.ncaches ) ]

    s.caches = [ Cache( p.CacheReqType, p.CacheRespType, p.MemReqType, p.MemRespType,
                        p.cache_size[i], p.associativity[i] ) for i in range( p.ncaches ) ]
    for i in range( p.ncaches ):
      s.caches[i].mem_minion_ifc //= s.mem_minion_ifc[i]
      s.caches[i].mem_master_ifc //= s.mem_master_ifc[i]

  def line_trace( s, trace ):
    for i in range(s.p.ncaches):
      msg += s.caches[i].line_trace()

# Test Harness for multi-cache tests
class MultiCacheTestHarness( Component ):
  def construct( s, Cache, test_params ):
    p = s.tp = test_params
    # Processor model that models a multicore processor
    s.proc = MulticoreModel( p )
    # Module that integrates all the caches into one for easier translation
    s.cache = MultiCache( Cache, p )
    # L2 cache or main memory model
    s.mem   = CiferMemoryCL( p.ncaches, [(p.MemReqType, p.MemRespType)]*p.ncaches, latency=p.latency )
    for i in range( p.ncaches ):
      connect( s.proc.mem_master_ifc[i],  s.cache.mem_minion_ifc[i] )
      connect( s.cache.mem_master_ifc[i], s.mem.ifc[i]              )

  def load( s ):
    addrs = s.tp.mem[::2]
    data_ints = s.tp.mem[1::2]
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return s.proc.done()

  def line_trace( s, trace ):
    msg = ''
    # msg += s.cache.line_trace()
    msg += s.proc.line_trace()
    # msg += s.mem.line_trace()
    return msg
