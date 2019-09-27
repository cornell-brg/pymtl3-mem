#=========================================================================
# BlockingCachePRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.ifcs import MemReqMsg4B, MemRespMsg4B
# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst
from BlockingCache.BlockingCacheCtrlPRTL import *
from BlockingCache.BlockingCacheDpathPRTL import *

opw  = 8,   # Short name for opaque bitwidth
abw  = 32,  # Short name for addr bitwidth
dbw  = 32,  # Short name for data bitwidth

class BlockingCachePRTL ( Component ):
  def construct( s,                
                 size = 8192, # Cache size in bytes
                 clw  = 128, # Short name for cacheline bitwidth
                 way  = 1 # associativity
  ):
    s.explicit_modulename = 'BlockingCache'
    nbl = size*8/clw, # Short name for number of cache blocks, 8192*8/128 = 512
    idw = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw = clog2(clw/8)   # Short name for offset bit width, clog2(128/8) = 4
    tgw = abw - ofw - idw # tag bit width; 32 - 4 - 9 = 19
    #---------------------------------------------------------------------
    # Interface to Proc & Mem
    #---------------------------------------------------------------------
    # Proc -> Cache
    s.cachereq_val    = InPort  ( 1 )
    s.cachereq_rdy    = OutPort ( 1 )
    s.cachereq_msg    = InPort  ( MemReqMsg4B )

    # Mem -> Cache
    s.memresp_val     = InPort  ( 1 )
    s.memresp_rdy     = OutPort ( 1 )
    s.memresp_msg     = InPort  ( CoherentMemRespMsg16B )

    # Cache -> Proc
    s.cacheresp_val   = OutPort ( 1 )
    s.cacheresp_rdy   = InPort  ( 1 )
    s.cacheresp_msg   = OutPort ( MemRespMsg4B )

    # Cache -> Mem
    s.memreq_val      = OutPort ( 1 )
    s.memreq_rdy      = InPort  ( 1 )
    s.memreq_msg      = OutPort ( CoherentMemReqMsg16B )

    s.cacheDpath = BlockingCacheDpathPRTL(
      abw, dbw, size, clw, way 
    )

    s.cacheCtrl = BlockingCacheCtrlPRTL(
      abw, dbw, size, clw, way 
    )

  # Line tracing

  def line_trace( s ):
    return s.cacheDpath.line_trace() + ' ' + s.cacheCtrl.line_trace()


