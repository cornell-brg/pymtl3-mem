#=========================================================================
# BlockingCachePRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg
from pymtl3.stdlib.connects import connect_pairs


from BlockingCache.BlockingCacheCtrlPRTL import BlockingCacheCtrlPRTL
from BlockingCache.BlockingCacheDpathPRTL import BlockingCacheDpathPRTL

MemReqMsg4B, MemRespMsg4B = mk_mem_msg(8,32,32)
MemReqMsg16B, MemRespMsg16B = mk_mem_msg(8,32,128)

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth

class BlockingCachePRTL ( Component ):
  def construct( s,                
                 size = 8192,# Cache size in bytes
                 clw  = 128, # cacheline bitwidth
                 way  = 1    # associativity
  ):
    s.explicit_modulename = 'BlockingCache'
    nbl = size*8//clw        # number of cache blocks; 8192*8/128 = 512
    nby = nbl/way            # blocks per way; 1
    idw = clog2(nbl)         # index width; clog2(512) = 9
    ofw = clog2(clw//8)      # offset bit width; clog2(128/8) = 4
    tgw = abw - ofw - idw    # tag bit width; 32 - 4 - 9 = 19
   #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( MemReqMsg4B )
    
    # Cache -> Proc
    s.cacheresp = SendIfcRTL( MemRespMsg4B )
    
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemRespMsg16B )

    # Cache -> Mem
    s.memreq    = SendIfcRTL( MemReqMsg16B )

    # M0 Signals to be connected
    s.reg_en_M0             = Wire(Bits1)
    s.write_data_mux_sel_M0 = Wire(mk_bits(clog2(2)))
    s.tag_array_val_M0      = Wire(Bits1) 
    s.tag_array_type_M0     = Wire(Bits1)
    s.tag_array_wben_M0     = Wire(Bits4)
    # M1 
    s.reg_en_M1             = Wire(Bits1)
    s.tag_match_M1          = Wire(Bits1)
    s.data_array_val_M1     = Wire(Bits1)
    s.data_array_type_M1    = Wire(Bits1)
    s.data_array_wben_M1    = Wire(Bits16)
    # M2
    s.reg_en_M2             = Wire(Bits1)
    # s.read_data_mux_sel_M2  = Wire(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = Wire(mk_bits(clog2(5)))
    # Output Signals

    s.cacheDpath = BlockingCacheDpathPRTL(
      obw, abw, dbw, size, clw, way
    )(
      cachereq_opaque       = s.cachereq.msg.opaque,
      cachereq_type         = s.cachereq.msg.type_,
      cachereq_addr         = s.cachereq.msg.addr,
      cachereq_data         = s.cachereq.msg.data,

      memresp_opaque        = s.memresp.msg.opaque,
      memresp_data          = s.memresp.msg.data,

      cacheresp_opaque      = s.cacheresp.msg.opaque,
      cacheresp_type        = s.cacheresp.msg.type_,
      cacheresp_data        = s.cacheresp.msg.data,

      memreq_opaque         = s.memreq.msg.opaque,
      memreq_addr           = s.memreq.msg.addr,
      memreq_data           = s.memreq.msg.data,
      
      # reg_en_M0             = s.reg_en_M0,
      write_data_mux_sel_M0 = s.write_data_mux_sel_M0,
      tag_array_val_M0      = s.tag_array_val_M0,
      tag_array_type_M0     = s.tag_array_type_M0,
      tag_array_wben_M0     = s.tag_array_wben_M0,
      
      reg_en_M1             = s.reg_en_M1    ,
      tag_match_M1          = s.tag_match_M1 ,
      data_array_val_M1     = s.data_array_val_M1,
      data_array_type_M1    = s.data_array_type_M1,
      data_array_wben_M1    = s.data_array_wben_M1,
      
      reg_en_M2             = s.reg_en_M2           ,
      # read_data_mux_sel_M2  = s.read_data_mux_sel_M2,
      read_word_mux_sel_M2  = s.read_word_mux_sel_M2,
    )

    s.cacheCtrl = BlockingCacheCtrlPRTL(
      abw, dbw, size, clw, way
    ) (
      cachereq_en           = s.cachereq.en,
      cachereq_rdy          = s.cachereq.rdy,
      cachereq_type         = s.cachereq.msg.type_,

      memresp_en            = s.memresp.en,
      memresp_rdy           = s.memresp.rdy,
      cacheresp_en          = s.cacheresp.en,
      cacheresp_rdy         = s.cacheresp.rdy,
      memreq_en             = s.memreq.en,
      memreq_rdy            = s.memreq.rdy,

      # reg_en_M0             = s.reg_en_M0,
      write_data_mux_sel_M0 = s.write_data_mux_sel_M0,
      tag_array_val_M0      = s.tag_array_val_M0,
      tag_array_type_M0     = s.tag_array_type_M0,
      tag_array_wben_M0     = s.tag_array_wben_M0,
      
      reg_en_M1             = s.reg_en_M1    ,
      tag_match_M1          = s.tag_match_M1 ,
      data_array_val_M1     = s.data_array_val_M1,
      data_array_type_M1    = s.data_array_type_M1,
      data_array_wben_M1    = s.data_array_wben_M1,

      reg_en_M2             = s.reg_en_M2           ,
      # read_data_mux_sel_M2  = s.read_data_mux_sel_M2,
      read_word_mux_sel_M2  = s.read_word_mux_sel_M2,

      hit                   = s.cacheresp.msg.test,
    )
    


  # Line tracing
  def line_trace( s ):
    return s.cacheDpath.line_trace() + ' ' + s.cacheCtrl.line_trace()


