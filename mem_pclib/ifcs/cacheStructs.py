"""
#=========================================================================
# cacheStructs.py
#=========================================================================

bitstructs for cache signals between the ctrl and dpath
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 19 February 2020
"""

from pymtl3 import *

def mk_dpath_signals_out_struct( p ):
  cls_name    = f"DpathMsg_out"
  req_cls = mk_bitstruct( cls_name, {
    #--------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------
    'cacheresp_opaque_M2' : p.BitsOpaque,
    'cacheresp_type_M2'   : p.BitsType,
    'cacheresp_data_M2'   : p.BitsData,
    'cacheresp_len_M2'    : p.BitsLen,
    'memreq_opaque_M2'    : p.BitsOpaque,
    'memreq_addr_M2'      : p.BitsAddr,
    'memreq_data_M2'      : p.BitsCacheline,
    #--------------------------------------------------------------------
    # M0 Dpath Signals 
    #--------------------------------------------------------------------
    'cachereq_type_M0'    : p.BitsType,
    'memresp_type_M0'     : p.BitsType,
    #--------------------------------------------------------------------
    # M1 Dpath Signals
    #--------------------------------------------------------------------
    'cachereq_type_M1'    : p.BitsType,
    'ctrl_bit_dty_rd_M1'  : p.BitsAssoc,
    'tag_match_M1'        : Bits1,
    'offset_M1'           : p.BitsOffset,
    'len_M1'              : p.BitsLen,
    # MSHR Signals
    'MSHR_full'           : Bits1,
    'MSHR_empty'          : Bits1,
    'MSHR_type'           : p.BitsType,
    'MSHR_ptr'            : p.BitsAssoclog2,
    # Signals for multiway associativity
    'tag_match_way_M1'    : p.BitsAssoclog2,
    'ctrl_bit_rep_rd_M1'  : p.BitsAssoclog2,
    #--------------------------------------------------------------------
    # M2 Dpath Signals
    #--------------------------------------------------------------------
    'cachereq_type_M2'    : p.BitsType,
    'offset_M2'           : p.BitsOffset,
    'len_M2'              : p.BitsLen,
  })
  return req_cls

def mk_ctrl_signals_out_struct( p ):
  cls_name    = f"CtrlMsg_out"

  req_cls = mk_bitstruct( cls_name, {
    #--------------------------------------------------------------------------
    # M0 Ctrl Signals 
    #--------------------------------------------------------------------------
    'reg_en_M0'         : Bits1,
    'memresp_mux_sel_M0': Bits1,
    'addr_mux_sel_M0'   : Bits2,
    'wdata_mux_sel_M0'  : Bits1,
    'tag_array_val_M0'  : p.BitsAssoc,
    'tag_array_type_M0' : Bits1,
    'tag_array_wben_M0' : p.BitsTagwben,
    'ctrl_bit_val_wr_M0': Bits1,
    'ctrl_bit_dty_wr_M0': Bits1,
    'ctrl_bit_rep_wr_M0': Bits1,
    #--------------------------------------------------------------------------
    # M1 Ctrl Signals
    #--------------------------------------------------------------------------
    # 'reg_en_M1'         : Bits1,
    'data_array_val_M1' : Bits1,
    'data_array_type_M1': Bits1,
    'data_array_wben_M1': p.BitsDataWben,
    'evict_mux_sel_M1'  : Bits1,
    'stall_mux_sel_M1'  : Bits1,
    'stall_reg_en_M1'   : Bits1,
    'ctrl_bit_rep_en_M1': Bits1,
    'way_offset_M1'     : Bits1,
    #---------------------------------------------------------------------------
    # M2 Ctrl Signals
    #--------------------------------------------------------------------------
    'reg_en_M2'           : Bits1,
    'read_data_mux_sel_M2': Bits1,
    'read_word_mux_sel_M2': p.BitsRdWordMuxSel,
    'read_byte_mux_sel_M2': p.BitsRdByteMuxSel,
    'read_2byte_mux_sel_M2': p.BitsRd2ByteMuxSel,
    'subword_access_mux_sel_M2': Bits2,
    'stall_reg_en_M2': Bits1,
    'stall_mux_sel_M2': Bits1,
    'hit_M2': Bits2,
    'memreq_type': p.BitsType,
    'MSHR_alloc_en': Bits1,
    'MSHR_dealloc_en': Bits1,
  })
  return req_cls