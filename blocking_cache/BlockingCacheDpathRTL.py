"""
=========================================================================
 BlockingCacheDpathRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 February 2020
"""

from pymtl3                         import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn
from pymtl3.stdlib.connects.connect_bits2bitstruct import *

from mem_pclib.constants.constants  import *
from mem_pclib.rtl.cifer            import *
from mem_pclib.rtl.MSHR_v1          import MSHR
from mem_pclib.rtl.muxes            import *
from mem_pclib.rtl.arithmetics      import Indexer, Comparator, CacheDataReplicator
from mem_pclib.rtl.registers        import DpathPipelineRegM0, DpathPipelineReg, ReplacementBitsReg
from sram.SramPRTL                  import SramPRTL

from .constants                     import *

class BlockingCacheDpathRTL (Component):

  def construct( s, p ):

    #--------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------

    s.cachereq_Y = InPort ( p.CacheReqType )
    s.memresp_Y  = InPort ( p.MemRespType  )
    s.ctrl       = InPort ( p.StructCtrl   ) # Control signals from Ctrl unit
    s.status     = OutPort( p.StructStatus ) # Status signals to Ctrl unit

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------

    # Pipeline Registers
    s.pipeline_reg_M0 = DpathPipelineRegM0( p )(
      en  = s.ctrl.reg_en_M0,
      in_ = s.memresp_Y
    )

    # Forward declaration: output from MSHR
    s.MSHR_dealloc_out = Wire( p.MSHRMsg  )

    s.MSHR_dealloc_mux_in_M0 = Wire( p.CacheReqType )
    s.MSHR_dealloc_mux_in_M0.type_  //= s.MSHR_dealloc_out.type_
    s.MSHR_dealloc_mux_in_M0.opaque //= s.MSHR_dealloc_out.opaque
    s.MSHR_dealloc_mux_in_M0.len    //= s.MSHR_dealloc_out.len
    s.MSHR_dealloc_mux_in_M0.data   //= s.MSHR_dealloc_out.data
    s.MSHR_dealloc_mux_in_M0.addr   //= s.MSHR_dealloc_out.addr
    s.status.amo_hit_M0             //= s.MSHR_dealloc_out.amo_hit

    # Chooses the cache request from proc or MSHR
    s.MSHR_mux_M0 = Mux( p.CacheReqType, 2 )(
      in_ = {
        0: s.cachereq_Y,
        1: s.MSHR_dealloc_mux_in_M0
      },
      sel = s.ctrl.memresp_mux_sel_M0,
    )

    s.cachereq_M0 = Wire( p.PipelineMsg )
    s.cachereq_M0.len    //= s.MSHR_mux_M0.out.len
    s.cachereq_M0.type_  //= s.MSHR_mux_M0.out.type_
    s.cachereq_M0.opaque //= s.MSHR_mux_M0.out.opaque

    # Chooses addr bypassed from L1 as a result of write hit clean
    s.cachereq_addr_M1_forward = Wire( p.BitsAddr )
    s.addr_mux_M0 = Mux( p.BitsAddr, 2 )(
      in_ = {
        0: s.MSHR_mux_M0.out.addr,
        1: s.cachereq_addr_M1_forward
      },
      sel = s.ctrl.addr_mux_sel_M0,
    )
    connect_bits2bitstruct( s.cachereq_M0.addr, s.addr_mux_M0.out )

    s.replicator_M0 = CacheDataReplicator( p )(
      msg_len = s.MSHR_mux_M0.out.len,
      data    = s.MSHR_mux_M0.out.data,
      type_   = s.MSHR_mux_M0.out.type_,
      offset  = s.cachereq_M0.addr.offset
    )

    s.write_data_mux_M0 = Mux( p.BitsCacheline, 2 )(
      in_ = {
        0: s.replicator_M0.out,
        1: s.pipeline_reg_M0.out.data
      },
      sel = s.ctrl.wdata_mux_sel_M0,
      out = s.cachereq_M0.data,
    )

    # Update per-word dirty bits
    s.hit_way_M1_bypass = Wire( p.BitsAssoclog2 )
    s.dirty_mask_M1_bypass = [ Wire( p.BitsDirty ) for _ in range( p.associativity ) ]
    s.dirty_bit_writer = DirtyBitWriter( p )(
      offset             = s.cachereq_M0.addr.offset,
      hit_way            = s.hit_way_M1_bypass,
      is_write_refill    = s.ctrl.is_write_refill_M0,
      is_write_hit_clean = s.ctrl.is_write_hit_clean_M0
    )

    for i in range( p.associativity ):
      s.dirty_bit_writer.dirty_bit[i] //= s.dirty_mask_M1_bypass[i]

    # Tag array inputs
    s.tag_array_idx_M0    = Wire( p.BitsIdx )
    s.tag_array_struct_M0 = Wire( p.StructTagArray )
    s.tag_array_idx_M0        //= s.cachereq_M0.addr.index
    s.tag_array_struct_M0.dty //= s.ctrl.ctrl_bit_dty_wr_M0
    s.tag_array_struct_M0.tag //= s.cachereq_M0.addr.tag
    s.tag_array_struct_M0.val //= s.ctrl.ctrl_bit_val_wr_M0
    if not p.full_sram:
      s.tag_array_struct_M0.tmp //= p.BitsTagArrayTmp( 0 )
    s.tag_array_wdata_M0 = Wire( p.BitsTagArray )
    connect_bits2bitstruct( s.tag_array_wdata_M0, s.tag_array_struct_M0 )

    # Mux for tag arrays
    s.tag_array_wdata_mux_M0 = Mux( mk_bits( p.bitwidth_tag_array ), 2 )(
      in_ = {
        0: s.tag_array_wdata_M0,
        1: mk_bits( p.bitwidth_tag_array )( 0 )
      },
      sel = s.ctrl.tag_array_in_sel_M0,
    )

    s.tag_array_idx_mux_M0 = Mux( p.BitsIdx, 2 )(
      in_ = {
        0: s.tag_array_idx_M0,
        1: s.ctrl.tag_array_init_idx_M0,
      },
      sel = s.ctrl.tag_array_idx_sel_M0,
    )

    # Send the M0 status signals to control
    s.status.memresp_type_M0   //= s.pipeline_reg_M0.out.type_
    s.status.new_dirty_bits_M0 //= s.dirty_bit_writer.out
    s.status.cachereq_type_M0  //= s.MSHR_mux_M0.out.type_

    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------

    # Pipeline registers
    s.cachereq_M1 = DpathPipelineReg( p )(
      en  = s.ctrl.reg_en_M1,
      in_ = s.cachereq_M0,
    )

    # Foward the M1 addr to M0
    connect_bits2bitstruct( s.cachereq_addr_M1_forward, s.cachereq_M1.out.addr )

    # Register file to store the replacement info
    s.ctrl_bit_rep_M1 = Wire( p.BitsAssoclog2 )
    s.replacement_bits_M1 = ReplacementBitsReg( p )(
      raddr = s.cachereq_M1.out.addr.index,
      rdata = s.ctrl_bit_rep_M1,
      waddr = s.cachereq_M1.out.addr.index,
      wdata = s.ctrl.ctrl_bit_rep_wr_M0,
      wen   = s.ctrl.ctrl_bit_rep_en_M1
    )

    # Tag arrays
    tag_arrays_M1 = []
    for i in range( p.associativity ):
      tag_arrays_M1.append(
        SramPRTL( p.bitwidth_tag_array, p.nblocks_per_way )
        (
          port0_val   = s.ctrl.tag_array_val_M0[i],
          port0_type  = s.ctrl.tag_array_type_M0,
          port0_idx   = s.tag_array_idx_mux_M0.out,
          port0_wdata = s.tag_array_wdata_mux_M0.out,
          port0_wben  = s.ctrl.tag_array_wben_M0,
        )
      )
    s.tag_arrays_M1 = tag_arrays_M1

    # Struct for the tag array output
    s.tag_array_out_M1 = [ Wire( p.StructTagArray ) for _ in range( p.associativity ) ]

    # Saves output of the SRAM during stall
    stall_regs_M1 = []
    for i in range( p.associativity ):
      # Connect the Bits object output of SRAM to a struct
      connect_bits2bitstruct( s.tag_arrays_M1[i].port0_rdata, s.tag_array_out_M1[i] )
      stall_regs_M1.append(
        RegEn( p.StructTagArray )(
          en  = s.ctrl.stall_reg_en_M1,
          in_ = s.tag_array_out_M1[i],
        )
      )
    s.stall_reg_M1 = stall_regs_M1

    stall_muxes_M1 = []
    for i in range( p.associativity ):
      stall_muxes_M1.append(
        Mux( p.StructTagArray, 2 )(
          in_ = {
            0: s.tag_array_out_M1[i],
            1: s.stall_reg_M1[i].out
          },
          sel = s.ctrl.stall_mux_sel_M1,
        )
      )
    s.tag_array_rdata_mux_M1 = stall_muxes_M1
    for i in range( p.associativity ):
      s.dirty_mask_M1_bypass[i] //= s.tag_array_rdata_mux_M1[i].out.dty

    # An one-entry MSHR for holding the cache request during a miss
    s.MSHR_alloc_in = Wire( p.MSHRMsg )
    s.MSHR_alloc_in.type_   //= s.cachereq_M1.out.type_
    connect_bits2bitstruct( s.MSHR_alloc_in.addr, s.cachereq_M1.out.addr )
    s.MSHR_alloc_in.opaque  //= s.cachereq_M1.out.opaque
    # select only one word of data to store since the rest is replicated
    s.MSHR_alloc_in.data    //= s.cachereq_M1.out.data[0:p.bitwidth_data]
    s.MSHR_alloc_in.len     //= s.cachereq_M1.out.len
    s.MSHR_alloc_in.repl    //= s.status.ctrl_bit_rep_rd_M1
    s.MSHR_alloc_in.amo_hit //= s.ctrl.MSHR_amo_hit
    s.MSHR_alloc_id = Wire(p.BitsOpaque)

    s.mshr = MSHR( p, 1 )(
      alloc_en    = s.ctrl.MSHR_alloc_en,
      alloc_in    = s.MSHR_alloc_in,
      alloc_id    = s.MSHR_alloc_id,
      full        = s.status.MSHR_full,
      empty       = s.status.MSHR_empty,
      dealloc_id  = s.pipeline_reg_M0.out.opaque,
      dealloc_en  = s.ctrl.MSHR_dealloc_en,
      dealloc_out = s.MSHR_dealloc_out,
    )

    s.comparator_set = Comparator( p )(
      addr_tag = s.cachereq_M1.out.addr.tag,
      hit      = s.status.hit_M1,
      hit_way  = s.status.hit_way_M1,
      type_    = s.cachereq_M1.out.type_,
      line_val = s.status.line_valid_M1,
    )

    for i in range( p.associativity ):
      s.comparator_set.tag_array[i] //= s.tag_array_rdata_mux_M1[i].out

    s.hit_way_M1_bypass //= s.comparator_set.hit_way

    dirty_line_detector_M1 = []
    for i in range( p.associativity ):
      dirty_line_detector_M1.append(
        DirtyLineDetector( p )(
          is_hit     = s.comparator_set.hit,
          offset     = s.cachereq_M1.out.addr.offset,
          dirty_bits = s.tag_array_rdata_mux_M1[i].out.dty
        )
      )
    s.dirty_line_detector_M1 = dirty_line_detector_M1

    s.write_mask_M1 = Wire( p.BitsDirty )
    s.write_mask_M1 //= lambda: s.tag_array_rdata_mux_M1[s.ctrl_bit_rep_M1].out.dty

    for i in range( p.associativity ):
      s.status.ctrl_bit_dty_rd_M1[i] //= s.dirty_line_detector_M1[i].is_dirty

    # Mux for choosing which way to evict
    s.evict_way_mux_M1 = PMux( p.BitsTag, p.associativity )(
      sel = s.ctrl_bit_rep_M1,
    )
    for i in range( p.associativity ):
      s.evict_way_mux_M1.in_[i] //= s.tag_array_rdata_mux_M1[i].out.tag

    s.evict_addr_M1 = Wire( p.StructAddr )
    s.evict_addr_M1.tag    //= s.evict_way_mux_M1.out
    s.evict_addr_M1.index  //= s.cachereq_M1.out.addr.index
    s.evict_addr_M1.offset //= p.BitsOffset(0) # Memreq offset doesn't matter

    s.cachereq_M1_2 = Wire(p.PipelineMsg)

    s.evict_mux_M1 = Mux( p.StructAddr, 2 )(
      in_ = {
        0: s.cachereq_M1.out.addr,
        1: s.evict_addr_M1
      },
      sel = s.ctrl.evict_mux_sel_M1,
      out = s.cachereq_M1_2.addr
    )

    # Data array inputs
    s.data_array_wdata_M1 = Wire( p.BitsCacheline )
    s.data_array_wdata_M1 //= s.cachereq_M1.out.data

    s.index_offset_M1 = Indexer( p )(
      index  = s.cachereq_M1.out.addr.index,
      offset = s.ctrl.way_offset_M1,
    )

    s.cachereq_M1_2.len    //= s.cachereq_M1.out.len
    s.cachereq_M1_2.data   //= s.cachereq_M1.out.data
    s.cachereq_M1_2.type_  //= s.cachereq_M1.out.type_
    s.cachereq_M1_2.opaque //= s.cachereq_M1.out.opaque

    # Send the M1 status signals to control
    s.status.ctrl_bit_rep_rd_M1 //= s.ctrl_bit_rep_M1
    s.status.cachereq_type_M1   //= s.cachereq_M1.out.type_
    s.status.len_M1             //= s.cachereq_M1.out.len
    s.status.offset_M1          //= s.cachereq_M1.out.addr.offset
    s.status.MSHR_ptr           //= s.MSHR_dealloc_out.repl
    s.status.MSHR_type          //= s.MSHR_dealloc_out.type_

    #--------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------

    # Pipeline registers
    s.cachereq_M2 = DpathPipelineReg( p )(
      in_ = s.cachereq_M1_2,
      en  = s.ctrl.reg_en_M2,
    )

    s.write_mask_M2 = RegEnRst( p.BitsDirty )(
      in_ = s.write_mask_M1,
      en  = s.ctrl.reg_en_M2
    )

    s.status.len_M2              //= s.cachereq_M2.out.len
    s.status.cacheresp_len_M2    //= s.cachereq_M2.out.len
    s.status.cacheresp_opaque_M2 //= s.cachereq_M2.out.opaque
    s.status.cachereq_type_M2    //= s.cachereq_M2.out.type_

    s.data_array_M2 = SramPRTL( p.bitwidth_cacheline, p.total_num_cachelines )(
      port0_val   = s.ctrl.data_array_val_M1,
      port0_type  = s.ctrl.data_array_type_M1,
      port0_idx   = s.index_offset_M1.out,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.ctrl.data_array_wben_M1
    )

    s.stall_reg_M2 = RegEnRst( p.BitsCacheline )(
      en  = s.ctrl.stall_reg_en_M2,
      in_ = s.data_array_M2.port0_rdata
    )

    s.stall_mux_M2 = Mux( p.BitsCacheline, 2 )(
      in_ = {
        0: s.data_array_M2.port0_rdata,
        1: s.stall_reg_M2.out
      },
      sel = s.ctrl.stall_mux_sel_M2
    )

    s.read_data_mux_M2 = Mux( p.BitsCacheline, 2 )(
      in_ = {
        0: s.stall_mux_M2.out,
        1: s.cachereq_M2.out.data
      },
      sel = s.ctrl.read_data_mux_sel_M2
    )

    # Data size select mux for subword accesses
    s.data_size_mux_M2 = DataSizeMux( p )(
      data   = s.read_data_mux_M2.out,
      en     = s.ctrl.data_size_mux_en_M2,
      len_   = s.cachereq_M2.out.len,
      offset = s.cachereq_M2.out.addr.offset,
    )

    s.memreq_addr_out = Wire(p.StructAddr)
    s.memreq_addr_out.tag    //= s.cachereq_M2.out.addr.tag
    s.memreq_addr_out.index  //= s.cachereq_M2.out.addr.index
    s.memreq_addr_out.offset //= p.BitsOffset(0)

    # Send the M2 status signals to control
    s.status.write_mask_M2     //= s.write_mask_M2.out
    s.status.cacheresp_data_M2 //= s.data_size_mux_M2.out
    s.status.cacheresp_type_M2 //= s.status.cachereq_type_M2
    s.status.offset_M2         //= s.cachereq_M2.out.addr.offset
    s.status.memreq_opaque_M2  //= s.cachereq_M2.out.opaque
    s.status.memreq_addr_M2    //= s.memreq_addr_out
    s.status.memreq_data_M2    //= s.read_data_mux_M2.out

  def line_trace( s ):
    msg = ""
    return msg
