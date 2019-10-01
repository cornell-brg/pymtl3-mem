#=========================================================================
# BlockingCachePRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.ifcs.MemMsg import *
from pymtl3.stdlib.connects import connect_pairs


from BlockingCache.BlockingCacheCtrlPRTL import *
from BlockingCache.BlockingCacheDpathPRTL import *

MemReqMsg4B, MemRespMsg4B = mk_mem_msg(8,32,32)
MemReqMsg16B, MemRespMsg16B = mk_mem_msg(8,32,128)

opw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth

class BlockingCachePRTL ( Component ):
  def construct( s,                
                 size = 8192,# Cache size in bytes
                 clw  = 128, # cacheline bitwidth
                 way  = 1    # associativity
  ):
    s.explicit_modulename = 'BlockingCache'
    nbl = size*8/clw         # number of cache blocks; 8192*8/128 = 512
    nby = nbl/way            # blocks per way; 1
    idw = clog2(nbl)         # index width; clog2(512) = 9
    ofw = clog2(clw/8)       # offset bit width; clog2(128/8) = 4
    tgw = abw - ofw - idw    # tag bit width; 32 - 4 - 9 = 19
   #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( MemReqMsg4B )
    
    # Cache -> Proc
    s.cacheresp = SendIfcRTL( MemRespMsg4B )
    
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemRespMsg4B )

    # Cache -> Mem
    s.memreq    = SendIfcRTL( MemReqMsg4B )

    s.cacheDpath = BlockingCacheDpathPRTL(
      abw, dbw, size, clw, way, MemReqMsg4B, MemRespMsg4B,
      MemReqMsg4B, MemRespMsg4B
    )(
      cachereq_msg  = s.cachereq.msg,
      cacheresp_msg = s.cacheresp.msg,
      memreq_msg    = s.memreq.msg,
      memresp_msg   = s.memresp.msg,
    )

    s.cacheCtrl = BlockingCacheCtrlPRTL(
      abw, dbw, size, clw, way
    ) (
      cachereq_en   = s.cachereq.en,
      cachereq_rdy  = s.cachereq.rdy,
      cacheresp_en  = s.cacheresp.en,
      cacheresp_rdy = s.cacheresp.rdy,
      memreq_en     = s.memreq.en,
      memreq_rdy    = s.memreq.rdy,
      memresp_en    = s.memresp.en,
      memresp_rdy   = s.memresp.rdy,
    )
    
    # connect_pairs (
     
    # )

  # Line tracing

  def line_trace( s ):
    return s.cacheDpath.line_trace() + ' ' + s.cacheCtrl.line_trace()


