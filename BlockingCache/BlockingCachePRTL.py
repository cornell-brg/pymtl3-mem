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
    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------
    nbl = size*8//clw        # number of cache blocks; 8192*8/128 = 512
    nby = nbl/way            # blocks per way; 1
    idw = clog2(nbl)         # index width; clog2(512) = 9
    ofw = clog2(clw//8)      # offset bit width; clog2(128/8) = 4
    tgw = abw - ofw - idw    # tag bit width; 32 - 4 - 9 = 19
    #-------------------------------------------------------------------------
    # Dtypes
    #-------------------------------------------------------------------------
    ob = mk_bits(obw)
    ty = mk_bits(4)
    ab = mk_bits(abw)
    db = mk_bits(dbw)
    cl = mk_bits(clw)
    ix = mk_bits(idw)
    tg = mk_bits(tgw)
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


    # Y  Signals to be connected
    s.cachereq_opaque_Y    = Wire(ob)
    s.cachereq_type_Y      = Wire(ty)
    s.cachereq_addr_Y      = Wire(ab)
    s.cachereq_data_Y      = Wire(db)

    s.tag_array_val_Y      = Wire(Bits1) 
    s.tag_array_type_Y     = Wire(Bits1)
    s.tag_array_wben_Y     = Wire(Bits4)
    s.ctrl_bit_val_wr_Y     = Wire(Bits1)

    # M0 Signals to be connected
    s.reg_en_M0             = Wire(Bits1)
    s.write_data_mux_sel_M0 = Wire(mk_bits(clog2(2)))
    # M1 
    s.cachereq_type_M1      = Wire(ty)
    s.ctrl_bit_val_rd_M1     = Wire(Bits1)
    s.tag_match_M1          = Wire(Bits1)
    s.reg_en_M1             = Wire(Bits1)
    s.data_array_val_M1     = Wire(Bits1)
    s.data_array_type_M1    = Wire(Bits1)
    s.data_array_wben_M1    = Wire(Bits16)
    # M2
    s.reg_en_M2             = Wire(Bits1)
    # s.read_data_mux_sel_M2  = Wire(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = Wire(mk_bits(clog2(5)))
    s.cachereq_type_M2      = Wire(ty)
    # Output Signals

    @s.update
    def input_cast(): # Required as a result of the test harness using ints after it sends all the transactions
      s.cachereq_opaque_Y = ob(s.cachereq.msg.opaque)
      s.cachereq_type_Y   = ty(s.cachereq.msg.type_)
      s.cachereq_addr_Y   = ab(s.cachereq.msg.addr)
      s.cachereq_data_Y   = db(s.cachereq.msg.data)

    s.cacheDpath = BlockingCacheDpathPRTL(
      obw, abw, dbw, size, clw, way
    )(
      cachereq_opaque       = s.cachereq_opaque_Y,
      cachereq_type         = s.cachereq_type_Y,
      cachereq_addr         = s.cachereq_addr_Y,
      cachereq_data         = s.cachereq_data_Y,

      memresp_opaque        = s.memresp.msg.opaque,
      memresp_data          = s.memresp.msg.data,

      cacheresp_opaque      = s.cacheresp.msg.opaque,
      cacheresp_type        = s.cacheresp.msg.type_,
      cacheresp_data        = s.cacheresp.msg.data,

      memreq_opaque         = s.memreq.msg.opaque,
      memreq_addr           = s.memreq.msg.addr,
      memreq_data           = s.memreq.msg.data,
      
      tag_array_val_Y       = s.tag_array_val_Y,
      tag_array_type_Y      = s.tag_array_type_Y,
      tag_array_wben_Y      = s.tag_array_wben_Y,
      ctrl_bit_val_wr_Y        = s.ctrl_bit_val_wr_Y,
      
      reg_en_M0             = s.reg_en_M0,
      
      reg_en_M1             = s.reg_en_M1    ,
      data_array_val_M1     = s.data_array_val_M1,
      data_array_type_M1    = s.data_array_type_M1,
      data_array_wben_M1    = s.data_array_wben_M1,
      ctrl_bit_val_rd_M1     = s.ctrl_bit_val_rd_M1,
      tag_match_M1          = s.tag_match_M1 ,
      cachereq_type_M1      = s.cachereq_type_M1,
      
      reg_en_M2             = s.reg_en_M2           ,
      # read_data_mux_sel_M2  = s.read_data_mux_sel_M2,
      read_word_mux_sel_M2  = s.read_word_mux_sel_M2,
      cachereq_type_M2      = s.cachereq_type_M2,
    )

    s.cacheCtrl = BlockingCacheCtrlPRTL(
      obw, abw, dbw, size, clw, way
    )(
      cachereq_en           = s.cachereq.en,
      cachereq_rdy          = s.cachereq.rdy,

      memresp_en            = s.memresp.en,
      memresp_rdy           = s.memresp.rdy,
      cacheresp_en          = s.cacheresp.en,
      cacheresp_rdy         = s.cacheresp.rdy,
      memreq_en             = s.memreq.en,
      memreq_rdy            = s.memreq.rdy,

      tag_array_val_Y       = s.tag_array_val_Y,
      tag_array_type_Y      = s.tag_array_type_Y,
      tag_array_wben_Y      = s.tag_array_wben_Y,
      cachereq_type_Y       = s.cachereq.msg.type_,
      ctrl_bit_val_wr_Y     = s.ctrl_bit_val_wr_Y,

      reg_en_M0             = s.reg_en_M0,
      
      cachereq_type_M1      = s.cachereq_type_M1,
      ctrl_bit_val_rd_M1    = s.ctrl_bit_val_rd_M1,
      tag_match_M1          = s.tag_match_M1 ,
      reg_en_M1             = s.reg_en_M1    ,
      data_array_val_M1     = s.data_array_val_M1,
      data_array_type_M1    = s.data_array_type_M1,
      data_array_wben_M1    = s.data_array_wben_M1,

      cachereq_type_M2      = s.cachereq_type_M2,
      reg_en_M2             = s.reg_en_M2           ,
      # read_data_mux_sel_M2  = s.read_data_mux_sel_M2,
      read_word_mux_sel_M2  = s.read_word_mux_sel_M2,

      hit_M2                = s.cacheresp.msg.test,
    )

  # Line tracing
  def line_trace( s ):
    return s.cacheDpath.line_trace() + ' ' + s.cacheCtrl.line_trace()


