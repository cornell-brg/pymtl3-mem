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
  cls_name    = "StructDpathStatus"
  req_cls = mk_bitstruct( cls_name, {

    # M0 Dpath Signals
    'cachereq_type_M0'    : p.BitsType,
    'memresp_type_M0'     : p.BitsType,
    'offset_M0'           : p.BitsOffset,
    'new_dirty_bits_M0'   : p.BitsDirty,
    'amo_hit_M0'          : Bits1,

    # M1 Dpath Signals
    'cachereq_type_M1'    : p.BitsType,
    'ctrl_bit_dty_rd_M1'  : p.BitsAssoc,
    'hit_M1'              : Bits1,
    'offset_M1'           : p.BitsOffset,
    'len_M1'              : p.BitsLen,
    'line_valid_M1'       : p.BitsAssoc,
    
    ## Signals for multiway associativity
    'hit_way_M1'          : p.BitsAssoclog2,
    'ctrl_bit_rep_rd_M1'  : p.BitsAssoclog2,

    # M2 Dpath Signals
    'cachereq_type_M2'    : p.BitsType,
    
    # MSHR Signals
    'MSHR_full'           : Bits1,
    'MSHR_empty'          : Bits1,
    'MSHR_type'           : p.BitsType,
    'MSHR_ptr'            : p.BitsAssoclog2,


  })
  return req_cls

def mk_ctrl_signals_struct( p ):
  cls_name    = f"StructCtrlSignals"

  req_cls = mk_bitstruct( cls_name, {

    # M0 Ctrl Signals
    'reg_en_M0'         : Bits1,
    'memresp_mux_sel_M0': Bits1,
    'addr_mux_sel_M0'   : Bits1,
    'wdata_mux_sel_M0'  : Bits1,
    'tag_array_val_M0'  : p.BitsAssoc,
    'tag_array_type_M0' : Bits1,
    'tag_array_wben_M0' : p.BitsTagwben,
    'ctrl_bit_val_wr_M0': Bits1,
    'ctrl_bit_dty_wr_M0': p.BitsDirty,
    'ctrl_bit_rep_wr_M0': Bits1,
    'is_write_refill_M0': Bits1,
    'is_write_hit_clean_M0': Bits1,
    'tag_array_in_sel_M0' : Bits1,
    'tag_array_idx_sel_M0': Bits1,
    'tag_array_init_idx_M0' : p.BitsIdx,

    # M1 Ctrl Signals
    'reg_en_M1'         : Bits1,
    'data_array_val_M1' : Bits1,
    'data_array_type_M1': Bits1,
    'data_array_wben_M1': p.BitsDataWben,
    'evict_mux_sel_M1'  : Bits1,
    'stall_reg_en_M1'   : Bits1,
    'hit_stall_eng_en_M1' : Bits1,
    'ctrl_bit_rep_en_M1': Bits1,
    'way_offset_M1'     : p.BitsAssoclog2,

    # M2 Ctrl Signals
    'reg_en_M2'           : Bits1,
    'read_data_mux_sel_M2': Bits1,
    'data_size_mux_en_M2' : Bits1,
    'stall_reg_en_M2'     : Bits1,
    'hit_M2'              : Bits2,
    'memreq_type'         : p.BitsType,
    'MSHR_alloc_en'       : Bits1,
    'MSHR_dealloc_en'     : Bits1,

  })
  return req_cls

# =========================================================================
#  ctrlStructs.py
# =========================================================================
# Bitstructs used within the cache control module

def mk_ctrl_pipeline_struct( ):
  cls_name    = f"StructCtrlPipeline"

  def req_to_str( self ):
    return "{}:{}:{}:{}".format(
      Bits1( self.val ),
      Bits1( self.is_refill ),
      Bits1( self.is_write_hit_clean ),
      Bits1( self.is_write_refill ),
    )

  req_cls = mk_bitstruct( cls_name,
    {
      'val'               : Bits1,
      'is_refill'         : Bits1,
      'is_write_hit_clean': Bits1,
      'is_write_refill'   : Bits1,
      'is_amo'            : Bits1,
    },
  )
  return req_cls

# =========================================================================
#  dpathStructs.py
# =========================================================================

from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

def mk_pipeline_msg( p ):
  cls_name    = f"StructDpathPipeline"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      p.BitsOpaque( self.opaque ),
      self.addr,
      p.BitsLen( self.len ),
      p.BitsData( self.data ),
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
  cls_name    = f"StructMSHR"

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
    'type_':  p.BitsType,
    'opaque': p.BitsOpaque,
    'addr':   p.BitsAddr,
    'len':    p.BitsLen,
    'data':   p.BitsData,
    'repl':   p.BitsAssoclog2,
    'amo_hit':Bits1,
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls

def mk_addr_struct( p ):
  def req_to_str( self ):
    return "{}{}{}".format(
      self.tag, self.index, self.offset
    )
  # declaration alignment MATTERS here
  struct = mk_bitstruct( "StructAddr", {
    'tag'   : p.BitsTag,
    'index' : p.BitsIdx,
    'offset': p.BitsOffset
  },
  namespace = {
    '__str__' : req_to_str
  } )
  return struct

def mk_tag_array_struct( p ):
  if p.full_sram:
    struct = mk_bitstruct( "StructTagArray", {
      'val': Bits1,
      'dty': p.BitsDirty,  # n bits for cifer, 1 bit otherwise
      'tag': p.BitsTag,
    } )
  else:
    struct = mk_bitstruct( "StructTagArray", {
      'val': Bits1,
      'dty': p.BitsDirty,
      'tag': p.BitsTag,
      'tmp': p.BitsTagArrayTmp # extra space in the SRAM #TODO fix this?
    } )
  return struct

def mk_short_tag_array_struct( p ):
  if p.full_sram:
    struct = mk_bitstruct( "StructShortTagArray", {
      'dty': p.BitsDirty,
      'tag': p.BitsTag,
    } )
  else:
    struct = mk_bitstruct( "StructShortTagArray", {
      'dty': p.BitsDirty,
      'tag': p.BitsTag,
      'tmp': p.BitsTagArrayTmp
    } )
  return struct

def mk_tag_ctrl_M1_struct( p ):
  # Aggreate the ctrl signals together
  struct = mk_bitstruct( "StructTagValAggregate", {
    'val': Bits1,
    'dty': p.BitsDirty,
    'tag': p.BitsTag,
  } )
  return struct
