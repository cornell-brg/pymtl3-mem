"""
=========================================================================
BlockingCachePRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and 
dpath

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 15 November 2019
"""

from BlockingCache.BlockingCacheCtrlPRTL  import BlockingCacheCtrlPRTL
from BlockingCache.BlockingCacheDpathPRTL import BlockingCacheDpathPRTL
from pymtl3                               import *
from pymtl3.stdlib.connects               import connect_pairs
from pymtl3.stdlib.ifcs.MemMsg            import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL

class BlockingCachePRTL ( Component ):
  def construct( s,                
                 nbytes        = 4096, # cache size in bytes, nbytes
                 CacheMsg      = "",   # Cache req/resp msg type
                 MemMsg        = "",   # Memory req/resp msg type
                 associativity = 1     # Associativity
  ):
    s.explicit_modulename = 'PipelinedBlockingCache'

    #--------------------------------------------------------------------------
    # Bitwidths
    #--------------------------------------------------------------------------
    
    # assert MemMsg.abw == CacheMsg.abw, "abw not the same"  # Translation not implemnted error
    clw = MemMsg.dbw
    abw = MemMsg.abw
    obw = MemMsg.obw
    dbw = CacheMsg.dbw
    nbl = nbytes//clw        # number of cache blocks; 8192*8/128 = 512
    nby = nbl//associativity  # blocks per way; 1
    idw = clog2(nby)         # index width; clog2(512) = 9
    ofw = clog2(clw//8)      # offset bitwidth; clog2(128/8) = 4
    tgw = abw - ofw - idw    # tag bitwidth; 32 - 4 - 9 = 19
    twb = int(abw+7)//8      # Tag array write byte bitwidth
    dwb = int(clw+7)//8      # Data array write byte bitwidth 
    rmx2 = clog2(clw//dbw+1) # Read word mux bitwidth
    
    #--------------------------------------------------------------------------
    # Make bits
    #--------------------------------------------------------------------------
    
    BitsOpaque    = mk_bits(obw)   # opaque
    BitsType      = mk_bits(4)     # type, always 4 bits
    BitsAddr      = mk_bits(abw)   # address 
    BitsData      = mk_bits(dbw)   # data 
    BitsCacheline = mk_bits(clw)   # cacheline 
    BitsIdx       = mk_bits(idw)   # index 
    BitsTag       = mk_bits(tgw)   # tag 
    BitsOffset    = mk_bits(ofw)   # offset 
    BitsTagWben   = mk_bits(twb)   # Tag array write byte enable
    BitsDataWben  = mk_bits(dwb)   # Data array write byte enable
    BitsRdDataMux = mk_bits(rmx2)  # Read data mux M2 
    
    #--------------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------------
    
    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( CacheMsg.Req )
    # Cache -> Proc
    s.cacheresp = SendIfcRTL( CacheMsg.Resp )
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemMsg.Resp )
    # Cache -> Mem
    s.memreq    = SendIfcRTL( MemMsg.Req )

    s.cacheDpath = BlockingCacheDpathPRTL(
      abw, dbw, clw, idw, ofw, tgw, nby,
      BitsAddr, BitsOpaque, BitsType, BitsData, BitsCacheline, BitsIdx, BitsTag, BitsOffset,
      BitsTagWben, BitsDataWben, BitsRdDataMux,
      associativity
    )(
      cachereq_opaque_M0  = s.cachereq.msg.opaque,
      cachereq_type_M0    = s.cachereq.msg.type_,
      cachereq_addr_M0    = s.cachereq.msg.addr,
      cachereq_data_M0    = s.cachereq.msg.data,

      memresp_opaque_Y    = s.memresp.msg.opaque,
      memresp_type_Y      = s.memresp.msg.type_, 
      memresp_data_Y      = s.memresp.msg.data,

      cacheresp_opaque_M2 = s.cacheresp.msg.opaque,
      cacheresp_type_M2   = s.cacheresp.msg.type_,
      cacheresp_data_M2   = s.cacheresp.msg.data,

      memreq_opaque_M2    = s.memreq.msg.opaque,
      memreq_addr_M2      = s.memreq.msg.addr,
      memreq_data_M2      = s.memreq.msg.data,
      
    )
    s.cacheCtrl = BlockingCacheCtrlPRTL(
      dbw, ofw,
      BitsAddr, BitsOpaque, BitsType, BitsData, BitsCacheline, BitsIdx, BitsTag, BitsOffset,
      BitsTagWben, BitsDataWben, BitsRdDataMux, 
      twb, dwb, rmx2,
      associativity
    )(
      cachereq_en           = s.cachereq.en,
      cachereq_rdy          = s.cachereq.rdy,

      memresp_en            = s.memresp.en,
      memresp_rdy           = s.memresp.rdy,
      cacheresp_en          = s.cacheresp.en,
      cacheresp_rdy         = s.cacheresp.rdy,
      memreq_en             = s.memreq.en,
      memreq_rdy            = s.memreq.rdy,

      hit_M2                = s.cacheresp.msg.test,
      memreq_type           = s.memreq.msg.type_
    )
   
    connect_pairs(
      s.cacheCtrl.memresp_mux_sel_M0,   s.cacheDpath.memresp_mux_sel_M0,
      s.cacheCtrl.wdata_mux_sel_M0,     s.cacheDpath.wdata_mux_sel_M0,
      s.cacheCtrl.tag_array_val_M0,     s.cacheDpath.tag_array_val_M0,
      s.cacheCtrl.tag_array_type_M0,    s.cacheDpath.tag_array_type_M0,
      s.cacheCtrl.tag_array_wben_M0,    s.cacheDpath.tag_array_wben_M0,
      s.cacheCtrl.cachereq_type_M0,     s.cachereq.msg.type_,
      s.cacheDpath.cachereq_type_M0,    s.cachereq.msg.type_,
      s.cacheCtrl.ctrl_bit_val_wr_M0,   s.cacheDpath.ctrl_bit_val_wr_M0,
      s.cacheCtrl.ctrl_bit_dty_wr_M0,   s.cacheDpath.ctrl_bit_dty_wr_M0,
      s.cacheCtrl.reg_en_M0,            s.cacheDpath.reg_en_M0,
      s.cacheCtrl.addr_mux_sel_M0,      s.cacheDpath.addr_mux_sel_M0,
      s.cacheCtrl.memresp_type_M0,      s.cacheDpath.memresp_type_M0,     
 
      s.cacheCtrl.cachereq_type_M1,     s.cacheDpath.cachereq_type_M1,
      s.cacheCtrl.ctrl_bit_val_rd_M1,   s.cacheDpath.ctrl_bit_val_rd_M1,
      s.cacheCtrl.ctrl_bit_dty_rd_M1,   s.cacheDpath.ctrl_bit_dty_rd_M1,
      s.cacheCtrl.tag_match_M1,         s.cacheDpath.tag_match_M1,
      s.cacheCtrl.offset_M1,            s.cacheDpath.offset_M1,
      s.cacheCtrl.reg_en_M1,            s.cacheDpath.reg_en_M1,
      s.cacheCtrl.reg_en_MSHR,          s.cacheDpath.reg_en_MSHR,
      s.cacheCtrl.MSHR_type,            s.cacheDpath.MSHR_type,
      s.cacheCtrl.data_array_val_M1,    s.cacheDpath.data_array_val_M1,
      s.cacheCtrl.data_array_type_M1,   s.cacheDpath.data_array_type_M1,
      s.cacheCtrl.data_array_wben_M1,   s.cacheDpath.data_array_wben_M1,
      s.cacheCtrl.evict_mux_sel_M1,     s.cacheDpath.evict_mux_sel_M1,
      
      s.cacheCtrl.reg_en_M2,            s.cacheDpath.reg_en_M2,
      s.cacheCtrl.read_word_mux_sel_M2, s.cacheDpath.read_word_mux_sel_M2,
      s.cacheCtrl.read_data_mux_sel_M2, s.cacheDpath.read_data_mux_sel_M2,
      s.cacheCtrl.offset_M2,            s.cacheDpath.offset_M2,
      s.cacheCtrl.cachereq_type_M2,     s.cacheDpath.cachereq_type_M2,
    )

  # Line tracing
  def line_trace( s ):
    memory_msg = memreq_msg = memresp_msg = ""
    
    if s.memresp.en:
      memresp_msg = "<{}<".format(s.memresp.msg.data)
      memory_msg = memresp_msg
    elif s.memreq.en:
      memreq_msg  = ">{}>".format(s.memreq.msg.data)
      memory_msg = memreq_msg
    if s.memreq.en and s.memresp.en:
      memory_msg = "{}{}".format(memresp_msg,memreq_msg)

    msg = "{} {} {}".format(s.cacheCtrl.line_trace(),
     s.cacheDpath.line_trace(), memory_msg)
    
    return msg


