"""
=========================================================================
 BlockingCacheDpathRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 20 February 2020
"""

from mem_pclib.constants.constants  import *
from mem_pclib.rtl.MSHR_v1          import MSHR
from mem_pclib.rtl.Muxes            import *
from mem_pclib.rtl.Replicator       import CacheDataReplicator
from mem_pclib.rtl.arithmetics      import Indexer, Comparator
from mem_pclib.rtl.registers        import DpathPipelineRegM0, DpathPipelineReg
from sram.SramPRTL                  import SramPRTL
from pymtl3                         import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn
from pymtl3.stdlib.connects.connect_bits2bitstruct import *

class BlockingCacheDpathRTL( Component ):

  def construct( s, p ):

    #--------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------

    s.cachereq_Y = InPort ( p.CacheReqType )
    s.memresp_Y  = InPort ( p.MemRespType  )
    s.ctrl       = InPort ( p.StructCtrl   ) # Control signals from ctrl unit
    s.status     = OutPort( p.StructStatus ) # Status signals to ctrl unit

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------

    # Pipeline registers for memresp
    s.pipeline_reg_M0 = DpathPipelineRegM0( p )(
      en  = s.ctrl.reg_en_M0,
      in_ = s.memresp_Y
    )


    # Pack MSHR output into a cache reqeuest message
    s.MSHR_dealloc_out       = Wire( p.MSHRMsg  ) # MSHR output
    s.MSHR_dealloc_mux_in_M0 = Wire( p.CacheReqType )
    s.MSHR_dealloc_mux_in_M0.type_  //= s.MSHR_dealloc_out.type_
    s.MSHR_dealloc_mux_in_M0.opaque //= s.MSHR_dealloc_out.opaque
    s.MSHR_dealloc_mux_in_M0.len    //= s.MSHR_dealloc_out.len
    s.MSHR_dealloc_mux_in_M0.data   //= s.MSHR_dealloc_out.data
    s.MSHR_dealloc_mux_in_M0.addr   //= s.MSHR_dealloc_out.addr

    # Chooses cache request from proc or MSHR
    s.MSHR_mux_M0 = Mux( p.CacheReqType , 2 )(
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

    # Bypass mux for addr from M1 as the result of write hit clean
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
      data    = s.MSHR_mux_M0.out.data
    )

    s.write_data_mux_M0 = Mux( p.BitsCacheline, 2 )(
      in_ = {
        0: s.replicator_M0.out,
        1: s.pipeline_reg_M0.out.data
      },
      sel = s.ctrl.wdata_mux_sel_M0,
      out = s.cachereq_M0.data,
    )

    # Tag array inputs
    s.tag_array_idx_M0    = Wire( p.BitsIdx )
    s.tag_array_struct_M0 = Wire( p.StructTagArray )
    s.tag_array_wdata_M0  = Wire( p.BitsTagArray )

    s.tag_array_idx_M0        //= s.cachereq_M0.addr.index
    s.tag_array_struct_M0.val //= s.ctrl.ctrl_bit_val_wr_M0
    s.tag_array_struct_M0.dty //= s.ctrl.ctrl_bit_dty_wr_M0
    s.tag_array_struct_M0.tag //= s.cachereq_M0.addr.tag
    if not p.full_sram:
      s.tag_array_struct_M0.tmp //= p.BitsTagArrayTmp( 0 )

    connect_bits2bitstruct( s.tag_array_wdata_M0, s.tag_array_struct_M0 )

    # M0 status signals
    s.status.memresp_type_M0  //= s.pipeline_reg_M0.out.type_
    s.status.cachereq_type_M0 //= s.MSHR_mux_M0.out.type_

    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------

    # Pipeline registers
    s.cachereq_M1 = DpathPipelineReg( p )(
      en  = s.ctrl.reg_en_M1,
      in_ = s.cachereq_M0,
    )

    # Connect the M1 addr backwards to M0 (bypass)
    connect_bits2bitstruct( s.cachereq_addr_M1_forward, s.cachereq_M1.out.addr )

    # Register File to store the replacement info
    s.ctrl_bit_rep_M1 = Wire( p.BitsAssoclog2 )
    s.replacement_bits_M1 = RegisterFile( p.BitsAssoclog2, p.nblocks_per_way )
    s.replacement_bits_M1.raddr[0] //= s.cachereq_M1.out.addr.index
    s.replacement_bits_M1.rdata[0] //= s.ctrl_bit_rep_M1
    s.replacement_bits_M1.waddr[0] //= s.cachereq_M1.out.addr.index
    s.replacement_bits_M1.wdata[0] //= s.ctrl.ctrl_bit_rep_wr_M0
    s.replacement_bits_M1.wen  [0] //= s.ctrl.ctrl_bit_rep_en_M1

    # Tag arrays (one per way)
    tag_arrays_M1 = []
    for i in range( p.associativity ):
      tag_arrays_M1.append(
        SramPRTL( p.bitwidth_tag_array, p.nblocks_per_way )
        (
          port0_val   = s.ctrl.tag_array_val_M0[i],
          port0_type  = s.ctrl.tag_array_type_M0,
          port0_idx   = s.tag_array_idx_M0,
          port0_wdata = s.tag_array_wdata_M0,
          port0_wben  = s.ctrl.tag_array_wben_M0,
        )
      )
    s.tag_arrays_M1 = tag_arrays_M1
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

    # An one-entry MSHR holding a cache request during miss
    s.MSHR_alloc_in = Wire( p.MSHRMsg )
    s.MSHR_alloc_id = Wire( p.BitsOpaque )

    s.MSHR_alloc_in.type_  //= s.cachereq_M1.out.type_
    connect_bits2bitstruct( s.MSHR_alloc_in.addr, s.cachereq_M1.out.addr )
    s.MSHR_alloc_in.opaque //= s.cachereq_M1.out.opaque
    # select only one word of data to store since the rest is replicated
    s.MSHR_alloc_in.data   //= s.cachereq_M1.out.data[0:p.bitwidth_data]
    s.MSHR_alloc_in.len    //= s.cachereq_M1.out.len
    s.MSHR_alloc_in.repl   //= s.status.ctrl_bit_rep_rd_M1

    s.mshr = MSHR( p, 1 )(
      alloc_en   = s.ctrl.MSHR_alloc_en,
      alloc_in   = s.MSHR_alloc_in,
      alloc_id   = s.MSHR_alloc_id,
      full       = s.status.MSHR_full,
      empty      = s.status.MSHR_empty,
      dealloc_id = s.pipeline_reg_M0.out.opaque,
      dealloc_en = s.ctrl.MSHR_dealloc_en,
      dealloc_out= s.MSHR_dealloc_out,
    )

    for i in range( p.associativity ):
      s.status.ctrl_bit_dty_rd_M1[i] //= s.tag_array_rdata_mux_M1[i].out.dty

    s.comparator_set = Comparator( p )(
      addr_tag       = s.cachereq_M1.out.addr.tag,
      hit            = s.status.hit_M1,
      hit_way        = s.status.hit_way_M1,
    )
    for i in range( p.associativity ):
      s.comparator_set.tag_array[i] //= s.tag_array_rdata_mux_M1[i].out

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

    s.cachereq_M1_2 = Wire( p.PipelineMsg )
    s.evict_mux_M1  = Mux( p.StructAddr, 2 )(
      in_ = {
        0: s.cachereq_M1.out.addr,
        1: s.evict_addr_M1
      },
      sel = s.ctrl.evict_mux_sel_M1,
      out = s.cachereq_M1_2.addr
    )

    # Data array input
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

    # M1 status signals
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
      en  = s.ctrl.reg_en_M2,
      in_ = s.cachereq_M1_2,
    )

    s.status.len_M2              //= s.cachereq_M2.out.len
    s.status.cacheresp_len_M2    //= s.cachereq_M2.out.len
    s.status.cacheresp_opaque_M2 //= s.cachereq_M2.out.opaque
    s.status.cachereq_type_M2    //= s.cachereq_M2.out.type_

    # Data array
    s.data_array_M2 = SramPRTL( p.bitwidth_cacheline, p.total_num_cachelines )(
      port0_val   = s.ctrl.data_array_val_M1,
      port0_type  = s.ctrl.data_array_type_M1,
      port0_idx   = s.index_offset_M1.out,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.ctrl.data_array_wben_M1
    )

    s.stall_reg_M2 = RegEn( p.BitsCacheline )(
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

    s.status.cacheresp_data_M2 //= s.data_size_mux_M2.out
    s.status.cacheresp_type_M2 //= s.status.cachereq_type_M2
    s.status.offset_M2         //= s.cachereq_M2.out.addr.offset
    s.status.memreq_opaque_M2  //= s.cachereq_M2.out.opaque

    s.memreq_addr_out = Wire( p.StructAddr )
    s.memreq_addr_out.tag    //= s.cachereq_M2.out.addr.tag
    s.memreq_addr_out.index  //= s.cachereq_M2.out.addr.index
    s.memreq_addr_out.offset //= p.BitsOffset(0)
    s.status.memreq_addr_M2  //= s.memreq_addr_out
    s.status.memreq_data_M2  //= s.read_data_mux_M2.out

  def line_trace( s ):
    msg = ""
    # msg += s.mshr.line_trace()
    return msg
