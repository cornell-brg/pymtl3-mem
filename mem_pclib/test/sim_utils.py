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

from pymtl3.stdlib.test.test_srcs    import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks   import TestSinkCL, TestSinkRTL
from pymtl3.stdlib.cl.MemoryCL       import MemoryCL
from pymtl3.stdlib.ifcs.SendRecvIfc  import RecvCL2SendRTL, RecvIfcRTL,\
   RecvRTL2SendCL, SendIfcRTL
from pymtl3.passes.backends.verilog import TranslationImportPass, \
VerilatorImportConfigs
from .proc_model import ProcModel

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

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, src_msgs, sink_msgs, stall_prob, latency, src_delay,
                 sink_delay, CacheModel, CacheReqType, CacheRespType,
                 MemReqType, MemRespType, cacheSize=128, associativity=1 ):
    # Instantiate models
    s.src   = TestSrcRTL(CacheReqType, src_msgs, 0, src_delay)
    s.proc_model = ProcModel(CacheReqType, CacheRespType)
    s.cache = CacheModel(CacheReqType, CacheRespType, MemReqType, MemRespType,
                         cacheSize, associativity)
    s.mem   = MemoryCL( 1, [(MemReqType, MemRespType)], latency) # Use our own modified mem
    s.cache2mem = RecvRTL2SendCL(MemReqType)
    s.mem2cache = RecvCL2SendRTL(MemRespType)
    s.sink  = TestSinkRTL(CacheRespType, sink_msgs, 0, sink_delay)

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
