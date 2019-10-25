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

# PARAMETRIZED BY TYPE OF CACHEREQ RESPONSE MEMREQ RESPONSE
class BlockingCachePRTL ( Component ):
  def construct( s,                
                 size = 4096, # cache size in bytes, nbytes
                 clw  = 128,  # cacheline bitwidth CHANGE TO BYTES, cacheline_nbytes
                 way  = 1     # associativity, name: associativity
  ):
    s.explicit_modulename = 'PipelinedBlockingCache'

    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------
    
    nbl = size*8//clw        # number of cache blocks; 8192*8/128 = 512
    nby = nbl/way            # blocks per way; 1
    idw = clog2(nbl)         # index width; clog2(512) = 9
    ofw = clog2(clw//8)      # offset bitwidth; clog2(128/8) = 4
    tgw = abw - ofw - idw    # tag bitwidth; 32 - 4 - 9 = 19
    twb_b = int(abw+7)//8    # Tag array write byte bitwidth
    dwb_b = int(clw+7)//8    # Data array write byte bitwidth 
    mx2_b = clog2(clw//dbw+1)# Read word mux bitwidth
    
    #-------------------------------------------------------------------------
    # Make bits
    #-------------------------------------------------------------------------
    
    BitsOpaque    = mk_bits(obw)   # opaque
    BitsType      = mk_bits(4)     # type, always 4 bits
    BitsAddress   = mk_bits(abw)   # address 
    BitsData      = mk_bits(dbw)   # data 
    BitsCacheline = mk_bits(clw)   # cacheline 
    BitsIndex     = mk_bits(idw)   # index 
    BitsTag       = mk_bits(tgw)   # tag 
    BitsOffset    = mk_bits(ofw-2) # offset 
    twb = mk_bits(twb_b)     # Tag array write byte enable
    dwb = mk_bits(dwb_b)     # Data array write byte enable
    mx2 = mk_bits(mx2_b)     # Read data mux M2 
    
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
    s.cachereq_opaque_Y     = Wire(BitsOpaque)
    s.cachereq_type_Y       = Wire(BitsType)
    s.cachereq_addr_Y       = Wire(BitsAddress)
    s.cachereq_data_Y       = Wire(BitsData)
 
    s.tag_array_val_Y       = Wire(Bits1) 
    s.tag_array_type_Y      = Wire(Bits1)
    s.tag_array_wben_Y      = Wire(twb)
    s.ctrl_bit_val_wr_Y     = Wire(Bits1)

    # M0 Signals to be connected
    s.reg_en_M0             = Wire(Bits1)
    s.write_data_mux_sel_M0 = Wire(mk_bits(clog2(2)))
    # M1 
    s.cachereq_type_M1      = Wire(BitsType)
    s.ctrl_bit_val_rd_M1    = Wire(Bits1)
    s.tag_match_M1          = Wire(Bits1)
    s.offset_M1             = Wire(BitsOffset)
    s.reg_en_M1             = Wire(Bits1)
    s.data_array_val_M1     = Wire(Bits1)
    s.data_array_type_M1    = Wire(Bits1)
    s.data_array_wben_M1    = Wire(dwb)
    # M2
    s.reg_en_M2             = Wire(Bits1)
    s.offset_M2             = Wire(BitsOffset)
    # s.read_data_mux_sel_M2  = Wire(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = Wire(mx2)
    s.cachereq_type_M2      = Wire(BitsType)
    # Output Signals

    # Required as a result of the test harness using ints after it sends all the transactions
    @s.update
    def input_cast(): 
      s.cachereq_opaque_Y = BitsOpaque(s.cachereq.msg.opaque)
      s.cachereq_type_Y   = BitsType(s.cachereq.msg.type_)
      s.cachereq_addr_Y   = BitsAddress(s.cachereq.msg.addr)
      s.cachereq_data_Y   = BitsData(s.cachereq.msg.data)

    s.cacheDpath = BlockingCacheDpathPRTL(
      abw, dbw, clw, idw, ofw, tgw, 
      nbl,
      BitsAddress, BitsOpaque, BitsType, BitsData, BitsCacheline, BitsIndex, BitsTag, BitsOffset,
      twb, dwb, mx2,
    )(
      cachereq_opaque_Y     = s.cachereq_opaque_Y,
      cachereq_type_Y       = s.cachereq_type_Y,
      cachereq_addr_Y       = s.cachereq_addr_Y,
      cachereq_data_Y       = s.cachereq_data_Y,

      memresp_opaque_Y      = s.memresp.msg.opaque,
      memresp_data_Y        = s.memresp.msg.data,

      cacheresp_opaque      = s.cacheresp.msg.opaque,
      cacheresp_type        = s.cacheresp.msg.type_,
      cacheresp_data        = s.cacheresp.msg.data,

      memreq_opaque         = s.memreq.msg.opaque,
      memreq_addr           = s.memreq.msg.addr,
      memreq_data           = s.memreq.msg.data,
      
      tag_array_val_Y       = s.tag_array_val_Y,
      tag_array_type_Y      = s.tag_array_type_Y,
      tag_array_wben_Y      = s.tag_array_wben_Y,
      ctrl_bit_val_wr_Y     = s.ctrl_bit_val_wr_Y,
      
      reg_en_M0             = s.reg_en_M0,
      
      reg_en_M1             = s.reg_en_M1,
      data_array_val_M1     = s.data_array_val_M1,
      data_array_type_M1    = s.data_array_type_M1,
      data_array_wben_M1    = s.data_array_wben_M1,
      ctrl_bit_val_rd_M1    = s.ctrl_bit_val_rd_M1,
      tag_match_M1          = s.tag_match_M1 ,
      cachereq_type_M1      = s.cachereq_type_M1,
      offset_M1             = s.offset_M1,
      
      reg_en_M2             = s.reg_en_M2,
      # read_data_mux_sel_M2  = s.read_data_mux_sel_M2,
      read_word_mux_sel_M2  = s.read_word_mux_sel_M2,
      cachereq_type_M2      = s.cachereq_type_M2,
      offset_M2             = s.offset_M2,
    )
    # TODO: AUTO CONNECT, GET RID OF TMP WIRES
    s.cacheCtrl = BlockingCacheCtrlPRTL(
      ofw,
      BitsAddress, BitsOpaque, BitsType, BitsData, BitsCacheline, BitsIndex, BitsTag, BitsOffset,
      twb, dwb, mx2, 
      twb_b, dwb_b, mx2_b
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
      offset_M1             = s.offset_M1,
      reg_en_M1             = s.reg_en_M1    ,
      data_array_val_M1     = s.data_array_val_M1,
      data_array_type_M1    = s.data_array_type_M1,
      data_array_wben_M1    = s.data_array_wben_M1,

      cachereq_type_M2      = s.cachereq_type_M2,
      offset_M2             = s.offset_M2,
      reg_en_M2             = s.reg_en_M2           ,
      # read_data_mux_sel_M2  = s.read_data_mux_sel_M2,
      read_word_mux_sel_M2  = s.read_word_mux_sel_M2,

      hit_M2                = s.cacheresp.msg.test,
    )

  # Line tracing
  def line_trace( s ):
    return s.cacheDpath.line_trace() + ' ' + s.cacheCtrl.line_trace()


