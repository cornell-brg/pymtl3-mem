#=========================================================================
# cacheNopePRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.ifcs import MemReqMsg4B, MemRespMsg4B

# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst


from NonBlockingCache.ifcs.CoherentMemMsg import *

from NonBlockingCache.NonBlockingCacheCtrlPRTL import *
from NonBlockingCache.NonBlockingCacheDpathPRTL import *

class NonBlockingCachePRTL ( Model ):
  def construct( s,
    ncaches = 1,
    cache_id = 0,
    opw  = 8,   # Short name for opaque bitwidth
    abw  = 32,  # Short name for addr bitwidth
    dbw  = 32,  # Short name for data bitwidth
    clw  = 128, # Short name for cacheline bitwidth
    nbl  = 512, # Short name for number of cache blocks, 8192*8/128 = 512
    tgw  = 28,  # Short name for tag bit width, 32-4 = 28
    stw  = 4,   # Short name for state bit width
    ctw  = 3,   # Cache type's bit width
    mtw  = 4,   # Mem type's bit width
    ccbw = 4,   # bit width of cache commands (from S1 -> S2)
    srw  = 2   # Bit width of src and dst IDs
  ):
    s.explicit_modulename = 'CacheNOPE'
    idw  = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw  = clog2(clw/8)   # Short name for offset bit width, clog2(128/8) = 4

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

    # Mem -> Cache (fwdreq)
    s.fwdreq_val      = InPort  ( 1 )
    s.fwdreq_rdy      = OutPort ( 1 )
    s.fwdreq_msg      = InPort  ( CoherentMemReqMsg16B )

    # Cache -> Mem (fwdresp)
    s.fwdresp_val     = OutPort ( 1 )
    s.fwdresp_rdy     = InPort  ( 1 )
    s.fwdresp_msg     = OutPort ( CoherentMemRespMsg16B )

    s.cacheDpath = cacheNopeDpathPRTL(
      ncaches,
      cache_id,
      opw,   
      abw, 
      dbw,  
      clw, 
      nbl,
      tgw,
      stw,  
      ctw,   
      mtw,   
      ccbw, 
      srw   
    )

    s.cacheCtrl = cacheNopeCtrlPRTL(
      ncaches,
      cache_id,
      opw,   
      abw, 
      dbw,  
      clw, 
      nbl,
      tgw,
      stw,  
      ctw,   
      mtw,   
      ccbw, 
      srw  
    )

  # Line tracing

  def line_trace( s ):
    return s.cacheDpath.line_trace() + ' ' + s.cacheCtrl.line_trace()


