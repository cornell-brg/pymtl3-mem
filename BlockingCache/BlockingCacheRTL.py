"""
=========================================================================
BlockingCacheRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and 
dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 15 November 2019
"""

from BlockingCache.BlockingCacheCtrlRTL   import BlockingCacheCtrlRTL
from BlockingCache.BlockingCacheDpathRTL  import BlockingCacheDpathRTL
from pymtl3                               import *
from pymtl3.stdlib.connects               import connect_pairs
from pymtl3.stdlib.ifcs.MemMsg            import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL

class BlockingCacheRTL ( Component ):
  def construct( s,                
                 nbytes        = 4096, # cache size in bytes, nbytes
                 CacheMsg      = "",   # Cache req/resp msg type
                 MemMsg        = "",   # Memory req/resp msg type
                 associativity = 1     # Associativity
  ):
    
    #--------------------------------------------------------------------------
    # Bitwidths
    #--------------------------------------------------------------------------
    
    # assert MemMsg.bitwidth_addr == CacheMsg.bitwidth_addr, "bitwidth_addr not the same"  # Translation not implemnted error
    bitwidth_cacheline        = MemMsg.bitwidth_data
    bitwidth_addr             = MemMsg.bitwidth_addr
    bitwidth_opaque           = MemMsg.bitwidth_opaque
    bitwidth_data             = CacheMsg.bitwidth_data
    nblocks                   = nbytes // bitwidth_cacheline        # number of cache blocks; 8192*8/128 = 512
    nblocks_per_way           = nblocks // associativity            # blocks per way; 1
    bitwidth_index            = clog2( nblocks_per_way )            # index width; clog2(512) = 9
    bitwidth_offset           = clog2( bitwidth_cacheline // 8 )    # offset bitwidth; clog2(128/8) = 4
    bitwidth_tag              = bitwidth_addr - bitwidth_offset - bitwidth_index    # tag bitwidth; 32 - 4 - 9 = 19
    bitwidth_tag_array        = int( bitwidth_tag + 1 + 1 + 7 ) // 8 * 8 
    bitwidth_tag_wben         = int( bitwidth_tag_array + 7 ) // 8      # Tag array write byte bitwidth
    bitwidth_data_wben        = int( bitwidth_cacheline + 7 ) // 8      # Data array write byte bitwidth 
    bitwidth_rd_wd_mux_sel    = clog2( bitwidth_cacheline // bitwidth_data + 1 ) # Read word mux bitwidth
    bitwidth_rd_byte_mux_sel  = clog2( bitwidth_data // 8 )     # Read byte mux sel bitwidth
    bitwidth_rd_2byte_mux_sel = clog2( bitwidth_data // 16 )    # Read half word mux sel bitwidth

    #--------------------------------------------------------------------------
    # Make bits
    #--------------------------------------------------------------------------
    
    BitsLen           = mk_bits(clog2(bitwidth_data//8))
    BitsOpaque        = mk_bits(bitwidth_opaque)   # opaque
    BitsType          = mk_bits(4)     # type, always 4 bits
    BitsAddr          = mk_bits(bitwidth_addr)   # address 
    BitsData          = mk_bits(bitwidth_data)   # data 
    BitsCacheline     = mk_bits(bitwidth_cacheline)   # cacheline 
    BitsIdx           = mk_bits(bitwidth_index)   # index 
    BitsTag           = mk_bits(bitwidth_tag)   # tag 
    BitsOffset        = mk_bits(bitwidth_offset)   # offset 
    BitsTagArray      = mk_bits(bitwidth_tag_array)   # Tag array write byte enable
    BitsTagwben       = mk_bits(bitwidth_tag_wben)   # Tag array write byte enable
    BitsDataWben      = mk_bits(bitwidth_data_wben)   # Data array write byte enable
    BitsRdWordMuxSel  = mk_bits(bitwidth_rd_wd_mux_sel)  # Read data mux M2 
    BitsRdByteMuxSel  = mk_bits(bitwidth_rd_byte_mux_sel)
    BitsRd2ByteMuxSel = mk_bits(bitwidth_rd_2byte_mux_sel)
    BitsAssoc         = mk_bits(associativity)
    if associativity == 1:
      BitsAssoclog2 = Bits1
    else:
      BitsAssoclog2  = mk_bits(clog2(associativity))
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

    s.cacheDpath = BlockingCacheDpathRTL(
      bitwidth_addr, bitwidth_data, bitwidth_cacheline, bitwidth_index, bitwidth_offset, bitwidth_tag, nblocks, nblocks_per_way, 
      BitsLen, BitsAddr, BitsOpaque, BitsType, BitsData, BitsCacheline, BitsIdx, BitsTag, BitsOffset,
      BitsTagArray, BitsTagwben, BitsDataWben, BitsRdWordMuxSel, BitsRdByteMuxSel,
      BitsRd2ByteMuxSel, BitsAssoclog2, BitsAssoc,
      bitwidth_tag_array, associativity
    )(
      cachereq_opaque_M0  = s.cachereq.msg.opaque,
      cachereq_type_M0    = s.cachereq.msg.type_,
      cachereq_addr_M0    = s.cachereq.msg.addr,
      cachereq_data_M0    = s.cachereq.msg.data,
      cachereq_len_M0     = s.cachereq.msg.len,

      memresp_opaque_Y    = s.memresp.msg.opaque,
      memresp_type_Y      = s.memresp.msg.type_, 
      memresp_data_Y      = s.memresp.msg.data,

      cacheresp_opaque_M2 = s.cacheresp.msg.opaque,
      cacheresp_type_M2   = s.cacheresp.msg.type_,
      cacheresp_data_M2   = s.cacheresp.msg.data,
      cacheresp_len_M2   = s.cacheresp.msg.len,

      memreq_opaque_M2    = s.memreq.msg.opaque,
      memreq_addr_M2      = s.memreq.msg.addr,
      memreq_data_M2      = s.memreq.msg.data,
      
    )
    s.cacheCtrl = BlockingCacheCtrlRTL(
      bitwidth_data, bitwidth_offset,
      BitsLen, BitsAddr, BitsOpaque, BitsType, BitsData, BitsCacheline, BitsIdx, BitsTag, BitsOffset,
      BitsTagwben, BitsDataWben, BitsRdWordMuxSel, BitsRdByteMuxSel, BitsRd2ByteMuxSel, 
      BitsAssoclog2, BitsAssoc,
      bitwidth_tag_wben, bitwidth_data_wben, bitwidth_rd_wd_mux_sel, bitwidth_rd_byte_mux_sel, bitwidth_rd_2byte_mux_sel,
      associativity,
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
      s.cacheCtrl.memresp_mux_sel_M0,         s.cacheDpath.memresp_mux_sel_M0,
      s.cacheCtrl.wdata_mux_sel_M0,           s.cacheDpath.wdata_mux_sel_M0,
      s.cacheCtrl.tag_array_type_M0,          s.cacheDpath.tag_array_type_M0,
      s.cacheCtrl.tag_array_wben_M0,          s.cacheDpath.tag_array_wben_M0,
      s.cacheCtrl.cachereq_type_M0,           s.cachereq.msg.type_,
      s.cacheDpath.cachereq_type_M0,          s.cachereq.msg.type_,
      s.cacheCtrl.ctrl_bit_val_wr_M0,         s.cacheDpath.ctrl_bit_val_wr_M0,
      s.cacheCtrl.ctrl_bit_dty_wr_M0,         s.cacheDpath.ctrl_bit_dty_wr_M0,
      s.cacheCtrl.reg_en_M0,                  s.cacheDpath.reg_en_M0,
      s.cacheCtrl.addr_mux_sel_M0,            s.cacheDpath.addr_mux_sel_M0,
      s.cacheCtrl.memresp_type_M0,            s.cacheDpath.memresp_type_M0,     
      s.cacheCtrl.tag_array_val_M0,           s.cacheDpath.tag_array_val_M0,
 
      s.cacheCtrl.cachereq_type_M1,           s.cacheDpath.cachereq_type_M1,
      s.cacheCtrl.reg_en_M1,                  s.cacheDpath.reg_en_M1,
      s.cacheCtrl.reg_en_MSHR,                s.cacheDpath.reg_en_MSHR,
      s.cacheCtrl.MSHR_type,                  s.cacheDpath.MSHR_type,
      s.cacheCtrl.data_array_type_M1,         s.cacheDpath.data_array_type_M1,
      s.cacheCtrl.data_array_wben_M1,         s.cacheDpath.data_array_wben_M1,
      s.cacheCtrl.evict_mux_sel_M1,           s.cacheDpath.evict_mux_sel_M1,
      s.cacheCtrl.data_array_val_M1,          s.cacheDpath.data_array_val_M1,
      s.cacheCtrl.tag_match_M1,               s.cacheDpath.tag_match_M1,
      s.cacheCtrl.ctrl_bit_dty_rd_M1,         s.cacheDpath.ctrl_bit_dty_rd_M1,
      s.cacheCtrl.offset_M1,                  s.cacheDpath.offset_M1,
      s.cacheCtrl.len_M1,                     s.cacheDpath.len_M1,
      s.cacheCtrl.stall_mux_sel_M1,           s.cacheDpath.stall_mux_sel_M1,
      s.cacheCtrl.stall_reg_en_M1,            s.cacheDpath.stall_reg_en_M1,

      s.cacheCtrl.reg_en_M2,                  s.cacheDpath.reg_en_M2,
      s.cacheCtrl.read_word_mux_sel_M2,       s.cacheDpath.read_word_mux_sel_M2,
      s.cacheCtrl.read_byte_mux_sel_M2,       s.cacheDpath.read_byte_mux_sel_M2,
      s.cacheCtrl.read_half_word_mux_sel_M2,  s.cacheDpath.read_half_word_mux_sel_M2,
      s.cacheCtrl.subword_access_mux_sel_M2,  s.cacheDpath.subword_access_mux_sel_M2,
      s.cacheCtrl.read_data_mux_sel_M2,       s.cacheDpath.read_data_mux_sel_M2,
      s.cacheCtrl.cachereq_type_M2,           s.cacheDpath.cachereq_type_M2,
      s.cacheCtrl.offset_M2,                  s.cacheDpath.offset_M2,
      s.cacheCtrl.len_M2,                     s.cacheDpath.len_M2,
      s.cacheCtrl.stall_reg_en_M2,            s.cacheDpath.stall_reg_en_M2,
      s.cacheCtrl.stall_mux_sel_M2,           s.cacheDpath.stall_mux_sel_M2,
    )

    # if associativity > 1:
    connect_pairs(
      s.cacheCtrl.ctrl_bit_rep_wr_M0,         s.cacheDpath.ctrl_bit_rep_wr_M0,
      s.cacheCtrl.tag_match_way_M1,           s.cacheDpath.tag_match_way_M1,
      s.cacheCtrl.way_offset_M1,              s.cacheDpath.way_offset_M1,
      s.cacheCtrl.ctrl_bit_rep_rd_M1,         s.cacheDpath.ctrl_bit_rep_rd_M1,
      s.cacheCtrl.ctrl_bit_rep_en_M1,         s.cacheDpath.ctrl_bit_rep_en_M1,
    )

  # Line tracing
  def line_trace( s ):
    memreq_msg = memresp_msg = "{:42}".format(" ")
    
    if s.memresp.en:
      memresp_msg = "{}".format(s.memresp.msg)
    if s.memreq.en:
      memreq_msg  = "{}".format(s.memreq.msg)

    msg = "{} {} {}{}".format(\
      s.cacheCtrl.line_trace(),memreq_msg,memresp_msg,
      s.cacheDpath.line_trace())
    # msg += "{}{} {}".format(memresp_msg, \
    #   s.cacheCtrl.line_trace(),
    #   s.cacheDpath.line_trace())
    #  memreq_msg, s.cacheDpath.line_trace())
    # msg = "{} {}".format(s.cacheCtrl.line_trace(),
    #  s.cacheDpath.line_trace())
    return msg


