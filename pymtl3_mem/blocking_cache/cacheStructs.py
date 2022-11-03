"""
#=========================================================================
# cacheStructs.py
#=========================================================================
bitstructs for cache signals between the ctrl and dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 19 February 2020
"""

from pymtl3 import *

def mk_dpath_status_struct( p ):
  cls_name = f"StructDpathStatus_{p.num_bytes}_{p.bitwidth_cacheline}_{p.bitwidth_addr}_"\
             f"{p.bitwidth_data}_{p.associativity}"
  req_cls = mk_bitstruct( cls_name, {

    # M0 Dpath Signals
    'cachereq_type_M0'        : p.BitsType,
    'memresp_type_M0'         : p.BitsType,
    'offset_M0'               : p.BitsOffset,
    'amo_hit_M0'              : Bits1,

    # M1 Dpath Signals
    'cachereq_type_M1'        : p.BitsType,
    # Tag PU outputs
    'ctrl_bit_dty_rd_line_M1' : p.BitsAssoc,
    'ctrl_bit_dty_rd_word_M1' : p.BitsAssoc,
    'hit_M1'                  : Bits1,
    'inval_hit_M1'            : Bits1,
    'hit_way_M1'              : p.BitsAssoclog2,
    ## Signals for multiway associativity
    'ctrl_bit_rep_rd_M1'      : p.BitsAssoclog2,
    'amo_hit_way_M1'          : p.BitsAssoclog2,

    # M2 Dpath Signals
    'cachereq_type_M2'        : p.BitsType,

    # MSHR Signals
    'MSHR_full'               : Bits1,
    'MSHR_empty'              : Bits1,
    'MSHR_type'               : p.BitsType,
    'MSHR_ptr'                : p.BitsAssoclog2,


  })
  return req_cls

def mk_ctrl_signals_struct( p ):
  cls_name = f"StructCtrlSignals_{p.num_bytes}_{p.bitwidth_cacheline}_{p.bitwidth_addr}_"\
             f"{p.bitwidth_data}_{p.associativity}"

  req_cls = mk_bitstruct( cls_name, {

    # M0 Ctrl Signals
    'reg_en_M0'                   : Bits1,
    'cachereq_memresp_mux_sel_M0' : Bits1,
    'addr_mux_sel_M0'             : Bits1,
    'wdata_mux_sel_M0'            : Bits1,
    'tag_array_val_M0'            : p.BitsAssoc,
    'update_tag_way_M0'           : p.BitsAssoclog2,
    'tag_array_type_M0'           : Bits1,
    'tag_array_wben_M0'           : p.BitsTagWben,
    'ctrl_bit_rep_wr_M0'          : Bits1,
    'update_tag_cmd_M0'           : Bits3,
    'update_tag_sel_M0'           : Bits1,
    'tag_array_idx_sel_M0'        : Bits1,
    'tag_array_init_idx_M0'       : p.BitsIdx,
    'is_amo_M0'                   : Bits1,

    # M1 Ctrl Signals
    'reg_en_M1'            : Bits1,
    'flush_init_reg_en_M1' : Bits1,
    'data_array_val_M1'    : Bits1,
    'data_array_type_M1'   : Bits1,
    'evict_mux_sel_M1'     : Bits1,
    'stall_reg_en_M1'      : Bits1,
    'hit_stall_eng_en_M1'  : Bits1,
    'ctrl_bit_rep_en_M1'   : Bits1,
    'way_offset_M1'        : p.BitsAssoclog2,
    'is_init_M1'           : Bits1,
    'flush_idx_mux_sel_M1' : Bits1,
    'dirty_evict_mask_M1'  : p.BitsDirty,
    'wben_cmd_M1'          : Bits2,
    'tag_processing_en_M1' : Bits1,

    # M2 Ctrl Signals
    'reg_en_M2'            : Bits1,
    'read_data_mux_sel_M2' : Bits1,
    'data_size_mux_en_M2'  : Bits1,
    'stall_reg_en_M2'      : Bits1,
    'hit_M2'               : Bits2,
    'memreq_type'          : p.BitsType,
    'MSHR_alloc_en'        : Bits1,
    'MSHR_dealloc_en'      : Bits1,
    'is_amo_M2'            : Bits1,

  })
  return req_cls

# =========================================================================
#  ctrlStructs.py
# =========================================================================
# Bitstructs used within the cache control module

def mk_ctrl_pipeline_struct( ):
  cls_name    = f"StructCtrlPipeline"
  req_cls = mk_bitstruct( cls_name,
  {
    'val'               : Bits1,
    'is_refill'         : Bits1,
    'is_write_hit_clean': Bits1,
    'is_write_refill'   : Bits1,
    'is_amo'            : Bits1,
  }
  )
  return req_cls

# =========================================================================
#  dpathStructs.py
# =========================================================================

from pymtl3_mem.mem_ifcs.MemMsg import MemMsgType

def mk_pipeline_msg( p ):
  cls_name    = f"StructDpathPipeline_{p.BitsCacheline.nbits}_{p.BitsLen.nbits}"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      p.BitsOpaque( self.opaque ),
      self.addr,
      p.BitsLen( self.len ),
      self.data ,
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':  p.BitsType,
    'opaque': p.BitsOpaque,
    'addr':   p.StructAddr,
    'len':    p.BitsLen,
    'data':   p.BitsCacheline,
  },
  namespace = {
    '__str__' : req_to_str
  }
  )
  return req_cls

def mk_MSHR_msg( p ):
  cls_name    = f"StructMSHR_{p.BitsData.nbits}_{p.BitsLen.nbits}"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      p.BitsOpaque( self.opaque ),
      self.addr ,
      p.BitsLen( self.len ),
      p.BitsData( self.data ),
      p.BitsAssoclog2(self.repl)
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':   p.BitsType,
    'opaque':  p.BitsOpaque,
    'addr':    p.BitsAddr,
    'len':     p.BitsLen,
    'data':    p.BitsData,
    'repl':    p.BitsAssoclog2,
    'amo_hit': Bits1,
    'dirty_bits': p.BitsDirty
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls

def mk_addr_struct( p ):
  # declaration alignment MATTERS here
  struct = mk_bitstruct( f"StructAddr_{p.bitwidth_tag}_{p.bitwidth_index}_{p.bitwidth_offset}",
  {
    'tag'   : p.BitsTag,
    'index' : p.BitsIdx,
    'offset': p.BitsOffset
  } )
  return struct

def mk_tag_array_struct( p ):
  struct = mk_bitstruct( f"StructTagArray_{p.bitwidth_val}_{p.bitwidth_dirty}_{p.bitwidth_tag}", {
    'val': p.BitsVal,
    'dty': p.BitsDirty,  # n bits for cifer, 1 bit otherwise
    'tag': p.BitsTag,
  } )
  return struct

def mk_hit_stall_struct( p ):
  struct = mk_bitstruct( f"StructHitInfo_{p.bitwidth_clog_asso}", {
    'hit':     Bits1,
    'hit_way': p.BitsAssoclog2,
  } )
  return struct
