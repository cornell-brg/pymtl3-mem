"""
=========================================================================
BlockingCacheRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and 
dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from BlockingCache.BlockingCacheCtrlRTL   import BlockingCacheCtrlRTL
from BlockingCache.BlockingCacheDpathRTL  import BlockingCacheDpathRTL
from BlockingCache.CacheParams            import CacheParams
from pymtl3                               import *
from pymtl3.stdlib.connects               import connect_pairs
from pymtl3.stdlib.ifcs.MemMsg            import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL

class BlockingCacheRTL ( Component ):

  def construct( s,                
    num_bytes     = 4096, # cache size in bytes
    CacheMsg      = "",   # Cache req/resp msg type
    MemMsg        = "",   # Memory req/resp msg type
    associativity = 1     # Associativity
  ):

    params = CacheParams(num_bytes=num_bytes, CacheMsg=CacheMsg, \
                         MemMsg=MemMsg, associativity=associativity)

    #----------------------------------------------------------------------------
    # Interface
    #----------------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( CacheMsg.Req )
    # Cache -> Proc
    s.cacheresp = SendIfcRTL( CacheMsg.Resp )
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemMsg.Resp )
    # Cache -> Mem
    s.memreq    = SendIfcRTL( MemMsg.Req )

    s.cacheDpath = BlockingCacheDpathRTL( params )\
    (
      cachereq            = s.cachereq.msg,
      memresp_Y           = s.memresp.msg,
      cacheresp_opaque_M2 = s.cacheresp.msg.opaque,
      cacheresp_type_M2   = s.cacheresp.msg.type_,
      cacheresp_data_M2   = s.cacheresp.msg.data,
      cacheresp_len_M2    = s.cacheresp.msg.len,
      memreq_opaque_M2    = s.memreq.msg.opaque,
      memreq_addr_M2      = s.memreq.msg.addr,
      memreq_data_M2      = s.memreq.msg.data,
    )

    s.cacheCtrl = BlockingCacheCtrlRTL( params )\
    (
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
      s.cacheCtrl.ctrl_bit_val_wr_M0,         s.cacheDpath.ctrl_bit_val_wr_M0,
      s.cacheCtrl.ctrl_bit_dty_wr_M0,         s.cacheDpath.ctrl_bit_dty_wr_M0,
      s.cacheCtrl.reg_en_M0,                  s.cacheDpath.reg_en_M0,
      s.cacheCtrl.addr_mux_sel_M0,            s.cacheDpath.addr_mux_sel_M0,
      s.cacheCtrl.memresp_type_M0,            s.cacheDpath.memresp_type_M0,     
      s.cacheCtrl.tag_array_val_M0,           s.cacheDpath.tag_array_val_M0,
      s.cacheCtrl.cachereq_type_M1,           s.cacheDpath.cachereq_type_M1,
      s.cacheCtrl.reg_en_M1,                  s.cacheDpath.reg_en_M1,
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
      s.cacheCtrl.read_2byte_mux_sel_M2,  s.cacheDpath.read_2byte_mux_sel_M2,
      s.cacheCtrl.subword_access_mux_sel_M2,  s.cacheDpath.subword_access_mux_sel_M2,
      s.cacheCtrl.read_data_mux_sel_M2,       s.cacheDpath.read_data_mux_sel_M2,
      s.cacheCtrl.cachereq_type_M2,           s.cacheDpath.cachereq_type_M2,
      s.cacheCtrl.offset_M2,                  s.cacheDpath.offset_M2,
      s.cacheCtrl.len_M2,                     s.cacheDpath.len_M2,
      s.cacheCtrl.stall_reg_en_M2,            s.cacheDpath.stall_reg_en_M2,
      s.cacheCtrl.stall_mux_sel_M2,           s.cacheDpath.stall_mux_sel_M2,

      # Associativity
      s.cacheCtrl.ctrl_bit_rep_wr_M0,         s.cacheDpath.ctrl_bit_rep_wr_M0,
      s.cacheCtrl.tag_match_way_M1,           s.cacheDpath.tag_match_way_M1,
      s.cacheCtrl.way_offset_M1,              s.cacheDpath.way_offset_M1,
      s.cacheCtrl.ctrl_bit_rep_rd_M1,         s.cacheDpath.ctrl_bit_rep_rd_M1,
      s.cacheCtrl.ctrl_bit_rep_en_M1,         s.cacheDpath.ctrl_bit_rep_en_M1,
      
      # MSHR Signals
      s.cacheCtrl.MSHR_alloc_en,              s.cacheDpath.MSHR_alloc_en,
      s.cacheCtrl.MSHR_dealloc_en,            s.cacheDpath.MSHR_dealloc_en,
      s.cacheCtrl.MSHR_full,                  s.cacheDpath.MSHR_full,
      s.cacheCtrl.MSHR_empty,                 s.cacheDpath.MSHR_empty,
      s.cacheCtrl.MSHR_ptr,                   s.cacheDpath.MSHR_ptr,
      s.cacheCtrl.MSHR_type,                  s.cacheDpath.MSHR_type,
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
    return msg
