"""
=========================================================================
 BlockingCacheDpathRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 February 2020
"""

from pymtl3                         import *
from pymtl3.stdlib.basic_rtl        import Mux, RegisterFile, RegEnRst, RegEn

# Import generic constants used in the repo
from constants  import *

# Generic behavioral SRAM model
from sram.SramPRTL        import SramPRTL

# Import cache specific constants
from .cache_constants import *
# Import from modules specific to the cache
from .units           import *

class BlockingCacheDpathRTL( Component ):

  def construct( s, p ):

    #--------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------

    s.cachereq_Y   = InPort (p.CacheReqType )
    s.cacheresp_M2 = OutPort(p.CacheRespType)
    s.memresp_Y    = InPort (p.MemRespType  )
    s.memreq_M2    = OutPort(p.MemReqType   )
    s.ctrl         = InPort (p.StructCtrl   ) # Control signals from Ctrl unit
    s.status       = OutPort(p.StructStatus ) # Status signals to Ctrl unit

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------

    # Pipeline Registers
    s.pipeline_reg_M0 = m = RegEnRst(p.MemRespType, p.MemRespType())
    m.in_ //= s.memresp_Y
    m.en  //= s.ctrl.reg_en_M0

    # Forward declaration: output from MSHR
    s.MSHR_dealloc_out = Wire(p.MSHRMsg)
    # Deallocating from MSHR
    s.MSHR_dealloc_mux_in_M0 = Wire(p.CacheReqType)
    # Set the CacheReqType by picking values from MSHR
    s.MSHR_dealloc_mux_in_M0 //= lambda: p.CacheReqType(s.MSHR_dealloc_out.type_,
      s.MSHR_dealloc_out.opaque, s.MSHR_dealloc_out.addr, s.MSHR_dealloc_out.len,
      s.MSHR_dealloc_out.data)
    s.status.amo_hit_M0 //= s.MSHR_dealloc_out.amo_hit

    # Chooses the cache request from proc or MSHR (memresp)
    s.cachereq_memresp_mux_M0 = m = Mux(p.CacheReqType, 2)
    m.in_[0] //= s.cachereq_Y
    m.in_[1] //= s.MSHR_dealloc_mux_in_M0
    m.sel    //= s.ctrl.cachereq_memresp_mux_sel_M0 

    s.cachereq_M0 = Wire(p.PipelineMsg)
    s.cachereq_M0.len    //= s.cachereq_memresp_mux_M0.out.len
    s.cachereq_M0.type_  //= s.cachereq_memresp_mux_M0.out.type_
    s.cachereq_M0.opaque //= s.cachereq_memresp_mux_M0.out.opaque

    # Chooses addr bypassed from L1 as a result of write hit clean
    s.cachereq_addr_M1_forward = Wire(p.bitwidth_addr)
    s.addr_mux_M0 = m = Mux(p.bitwidth_addr, 2)
    m.in_[0] //= s.cachereq_memresp_mux_M0.out.addr
    m.in_[1] //= s.cachereq_addr_M1_forward
    m.sel    //= s.ctrl.addr_mux_sel_M0
    @update
    def cachereq_M0_addr_bits_to_bitstruct():
      s.cachereq_M0.addr @= s.addr_mux_M0.out

    # Converts a 32-bit word to 128-bit line by replicated the word multiple times
    s.replicator_M0 = m = DataReplicator(p)
    m.len_ //= s.cachereq_memresp_mux_M0.out.len
    m.in_  //= s.cachereq_memresp_mux_M0.out.data
    m.amo  //= s.ctrl.is_amo_M0
    
    # Selects between data from the memory resp or from the replicator
    # Dependent on if we have a refill response
    s.write_data_mux_M0 = m = Mux(p.bitwidth_cacheline, 2)
    m.in_[0] //= s.replicator_M0.out
    m.in_[1] //= s.pipeline_reg_M0.out.data
    m.sel    //= s.ctrl.wdata_mux_sel_M0
    m.out    //= s.cachereq_M0.data


    s.hit_way_M1_bypass = Wire(p.bitwidth_clog_asso)
    # Update tag-array entry
    s.update_tag_way_mux_M0 = m = Mux(p.bitwidth_clog_asso, 2)
    m.in_[0] //= s.hit_way_M1_bypass
    m.in_[1] //= s.ctrl.update_tag_way_M0
    m.sel    //= s.ctrl.update_tag_sel_M0

    # Decides the bits that will be written into the sram depending on the state
    s.update_tag_unit = m = UpdateTagArrayUnit(p)
    m.way        //= s.update_tag_way_mux_M0.out
    m.offset     //= s.cachereq_M0.addr.offset
    m.cmd        //= s.ctrl.update_tag_cmd_M0
    m.refill_dty //= s.MSHR_dealloc_out.dirty_bits
    
    s.tag_entries_M1_bypass = [ Wire(p.StructTagArray) for _ in range(p.associativity) ]
    for i in range(p.associativity):
      s.update_tag_unit.old_entries[i] //= s.tag_entries_M1_bypass[i]

    # Index select for the tag array as a result of cache initialization
    s.tag_array_idx_mux_M0 = m = Mux(p.bitwidth_index, 2)
    m.in_[0] //= s.cachereq_M0.addr.index
    m.in_[1] //= s.ctrl.tag_array_init_idx_M0
    m.sel    //= s.ctrl.tag_array_idx_sel_M0

    # Select if we need to rewrite the tag from the tab unit
    s.tag_array_tag_mux_M0 = m = Mux(p.bitwidth_tag, 2)
    m.in_[0] //= s.cachereq_M0.addr.tag
    m.in_[1] //= s.update_tag_unit.out.tag
    m.sel    //= s.ctrl.update_tag_sel_M0

    # Tag array inputs
    s.tag_array_struct_M0 = Wire(p.StructTagArray)
    s.tag_array_struct_M0.tag //= s.tag_array_tag_mux_M0.out
    s.tag_array_struct_M0.val //= s.update_tag_unit.out.val
    s.tag_array_struct_M0.dty //= s.update_tag_unit.out.dty
    s.tag_array_wdata_M0 = Wire(p.bitwidth_tag_array)
    @update
    def tag_array_struct_M0_bits_to_bitstruct():
      s.tag_array_wdata_M0 @= s.tag_array_struct_M0

    # Send the M0 status signals to control
    s.status.memresp_type_M0   //= s.pipeline_reg_M0.out.type_
    s.status.cachereq_type_M0  //= s.cachereq_memresp_mux_M0.out.type_

    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------

    # Pipeline registers
    s.cachereq_M1 = m = RegEnRst( p.PipelineMsg, p.PipelineMsg() )
    m.in_ //= s.cachereq_M0
    m.en  //= s.ctrl.reg_en_M1

    # Data array idx
    s.flush_idx_M1 = m = RegEnRst(p.bitwidth_index)
    m.in_ //= s.ctrl.tag_array_init_idx_M0
    m.en  //= s.ctrl.flush_init_reg_en_M1

    # Send the dty bits to the M1 stage and use for wben mask into data array
    s.dty_bits_mask_M1 = m = RegEnRst(p.bitwidth_dirty)
    m.in_ //= s.MSHR_dealloc_out.dirty_bits # From M0 stage
    m.en  //= s.ctrl.reg_en_M1

    # Foward the M1 addr to M0
    @update
    def up_cachereq_addr_M1_forward_bits_to_bitstruct():
      s.cachereq_addr_M1_forward @= s.cachereq_M1.out.addr

    # Register file to store the replacement info
    s.replacement_bits_M1 = m = ReplacementBitsReg(p)
    m.raddr //= s.cachereq_M1.out.addr.index
    m.waddr //= s.cachereq_M1.out.addr.index
    m.wdata //= s.ctrl.ctrl_bit_rep_wr_M0
    m.wen   //= s.ctrl.ctrl_bit_rep_en_M1
  
    # Tag arrays instantiations
    s.tag_arrays_M1 = [ SramPRTL( p.bitwidth_tag_array, p.nblocks_per_way ) 
                        for _ in range(p.associativity) ]
    for i, m in enumerate(s.tag_arrays_M1):
      m.port0_val   //= s.ctrl.tag_array_val_M0[i]
      m.port0_type  //= s.ctrl.tag_array_type_M0
      m.port0_idx   //= s.tag_array_idx_mux_M0.out
      m.port0_wdata //= s.tag_array_wdata_M0
      m.port0_wben  //= s.ctrl.tag_array_wben_M0

    # Saves output of the SRAM during stall 
    s.tag_array_rdata_M1 = [ StallEngine(p.StructTagArray) for _ in range(p.associativity) ]
    for i, m in enumerate(s.tag_array_rdata_M1):
      m.in_ //= lambda: s.tag_arrays_M1[i].port0_rdata
      m.en  //= s.ctrl.stall_reg_en_M1

    # An one-entry MSHR for holding the cache request during a miss
    s.MSHR_alloc_in = Wire(p.MSHRMsg)
    s.MSHR_alloc_in.type_   //= s.cachereq_M1.out.type_
    s.MSHR_alloc_in.addr    //= lambda: s.cachereq_M1.out.addr
    s.MSHR_alloc_in.opaque  //= s.cachereq_M1.out.opaque
    # select only one word of data to store since the rest is replicated
    s.MSHR_alloc_in.data    //= s.cachereq_M1.out.data[0:p.bitwidth_data]
    s.MSHR_alloc_in.len     //= s.cachereq_M1.out.len
    s.MSHR_alloc_in.repl    //= s.ctrl.way_offset_M1
    s.MSHR_alloc_in_amo_hit_bypass = Wire(p.StructHit)
    s.MSHR_alloc_in.amo_hit //= s.MSHR_alloc_in_amo_hit_bypass.hit
    s.write_mask_M1 = Wire(p.bitwidth_dirty)
    s.MSHR_alloc_in.dirty_bits //= lambda: (s.write_mask_M1 & s.ctrl.dirty_evict_mask_M1)

    # s.MSHR_alloc_id = Wire( p.BitsOpaque )
    s.mshr = m = MSHR(p, 1)
    m.alloc_en    //= s.ctrl.MSHR_alloc_en
    m.alloc_in    //= s.MSHR_alloc_in
    # m.alloc_id    //= s.MSHR_alloc_id # don't need for now; only required for nonblocking cache
    m.full        //= s.status.MSHR_full
    m.empty       //= s.status.MSHR_empty
    m.dealloc_id  //= s.pipeline_reg_M0.out.opaque
    m.dealloc_en  //= s.ctrl.MSHR_dealloc_en
    m.dealloc_out //= s.MSHR_dealloc_out

    # Combined comparator set for both dirty line detection and hit detection
    # It has an enable to so it doesn't always look at the output of the sram
    s.tag_array_PU = m = TagArrayRDataProcessUnit(p)
    m.addr_tag   //= s.cachereq_M1.out.addr.tag
    m.is_init    //= s.ctrl.is_init_M1
    m.hit        //= s.status.hit_M1
    m.hit_way    //= s.status.hit_way_M1
    m.inval_hit  //= s.status.inval_hit_M1
    m.offset     //= s.cachereq_M1.out.addr.offset
    m.line_dirty //= s.status.ctrl_bit_dty_rd_line_M1
    m.word_dirty //= s.status.ctrl_bit_dty_rd_word_M1
    m.en         //= s.ctrl.tag_processing_en_M1
    
    # Send the output of tag array sram into the processing unit
    for i in range(p.associativity):
      m.tag_array[i] //= s.tag_array_rdata_M1[i].out
      
      # Bypass the current tag-array entries to M0
      s.tag_entries_M1_bypass[i] //= m.tag_entires[i]

    s.hit_way_M1_bypass //= s.tag_array_PU.hit_way
    s.write_mask_M1 //= lambda: s.tag_array_PU.tag_entires[s.ctrl.way_offset_M1].dty

    # stall engine to save the hit bit into the MSHR for AMO operations only
    StructHit = p.StructHit
    s.hit_stall_engine = m = StallEngine(StructHit)
    m.in_ //= lambda: StructHit(s.tag_array_PU.hit | s.tag_array_PU.inval_hit,
                                s.tag_array_PU.hit_way)
    m.en  //= s.ctrl.hit_stall_eng_en_M1
    m.out //= s.MSHR_alloc_in_amo_hit_bypass

    # Mux for choosing which way to evict
    s.evict_way_mux_M1 = m = Mux(p.bitwidth_tag, p.associativity)
    m.sel //= s.ctrl.way_offset_M1
    for i in range( p.associativity ):
      m.in_[i] //= s.tag_array_rdata_M1[i].out.tag

    s.flush_idx_mux_M1 = m = Mux(p.bitwidth_index, 2)
    m.in_[0] //= s.cachereq_M1.out.addr.index
    m.in_[1] //= s.flush_idx_M1.out
    m.sel    //= s.ctrl.flush_idx_mux_sel_M1

    s.evict_addr_M1 = Wire(p.StructAddr)
    s.evict_addr_M1.tag    //= s.evict_way_mux_M1.out
    s.evict_addr_M1.index  //= s.flush_idx_mux_M1.out # s.cachereq_M1.out.addr.index
    s.evict_addr_M1.offset //= 0 # Memreq offset doesn't matter

    s.cachereq_M1_2 = Wire(p.PipelineMsg)

    s.evict_mux_M1 = m = Mux(p.StructAddr, 2)
    m.in_[0] //= s.cachereq_M1.out.addr
    m.in_[1] //= s.evict_addr_M1
    m.sel //= s.ctrl.evict_mux_sel_M1
    m.out //= s.cachereq_M1_2.addr

    # Data array inputs
    s.data_array_wdata_M1 = Wire(p.bitwidth_cacheline)
    s.data_array_wdata_M1 //= s.cachereq_M1.out.data

    s.index_offset_M1 = m = Indexer( p )
    m.index  //= s.cachereq_M1_2.addr.index
    m.offset //= s.ctrl.way_offset_M1

    s.WbenGen_M1 = m = WriteBitEnGen( p )
    m.offset   //= s.cachereq_M1.out.addr.offset
    m.len_     //= s.cachereq_M1.out.len
    m.dty_mask //= s.dty_bits_mask_M1.out
    m.cmd      //= s.ctrl.wben_cmd_M1

    s.cachereq_M1_2.len    //= s.cachereq_M1.out.len
    s.cachereq_M1_2.data   //= s.cachereq_M1.out.data
    s.cachereq_M1_2.type_  //= s.cachereq_M1.out.type_
    s.cachereq_M1_2.opaque //= s.cachereq_M1.out.opaque

    # Send the M1 status signals to control
    s.status.ctrl_bit_rep_rd_M1 //= s.replacement_bits_M1.rdata
    s.status.cachereq_type_M1   //= s.cachereq_M1.out.type_
    s.status.MSHR_ptr           //= s.MSHR_dealloc_out.repl
    s.status.MSHR_type          //= s.MSHR_dealloc_out.type_
    s.status.amo_hit_way_M1     //= s.MSHR_alloc_in_amo_hit_bypass.hit_way

    #--------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------

    # Pipeline registers
    s.cachereq_M2 = m = RegEnRst( p.PipelineMsg, p.PipelineMsg() )
    m.in_ //= s.cachereq_M1_2
    m.en  //= s.ctrl.reg_en_M2

    s.write_mask_M2 = m = RegEnRst(p.bitwidth_dirty)
    m.in_ //= s.write_mask_M1
    m.en  //= s.ctrl.reg_en_M2

    s.data_array_M2 = m = SramPRTL(p.bitwidth_cacheline, p.total_num_cachelines)
    m.port0_val   //= s.ctrl.data_array_val_M1
    m.port0_type  //= s.ctrl.data_array_type_M1
    m.port0_idx   //= s.index_offset_M1.out
    m.port0_wdata //= s.data_array_wdata_M1
    m.port0_wben  //= s.WbenGen_M1.out

    s.stall_engine_M2 = m = StallEngine(p.bitwidth_cacheline)
    m.in_ //= s.data_array_M2.port0_rdata
    m.en  //= s.ctrl.stall_reg_en_M2

    s.read_data_mux_M2 = m = Mux(p.bitwidth_cacheline, 2)
    m.in_[0] //= s.stall_engine_M2.out
    m.in_[1] //= s.cachereq_M2.out.data
    m.sel    //= s.ctrl.read_data_mux_sel_M2

    # Data size select mux for subword accesses
    s.data_size_mux_M2 = m = FastDataSelectMux(p)
    m.in_    //= s.read_data_mux_M2.out
    m.en     //= s.ctrl.data_size_mux_en_M2
    m.amo    //= s.ctrl.is_amo_M2
    m.len_   //= s.cachereq_M2.out.len
    m.offset //= s.cachereq_M2.out.addr.offset
    
    # selects the appropriate offset and len for memreq based on the type
    s.mem_req_off_len_M2 = m = OffsetLenSelector(p)
    m.len_i    //= s.cachereq_M2.out.len
    m.offset_i //= s.cachereq_M2.out.addr.offset
    m.is_amo   //= s.ctrl.is_amo_M2

    # Send the M2 status signals to control
    s.status.cachereq_type_M2 //= s.cachereq_M2.out.type_

    # Construct the memreq signal
    # build a addr struct to zip the addr, idx, and tag together
    s.memreq_addr_out = Wire(p.StructAddr)
    s.memreq_addr_out.tag    //= s.cachereq_M2.out.addr.tag
    s.memreq_addr_out.index  //= s.cachereq_M2.out.addr.index
    s.memreq_addr_out.offset //= s.mem_req_off_len_M2.offset_o

    s.memreq_addr_bits = Wire(p.bitwidth_addr)
    @update
    def memreq_addr_bits_to_bitstruct():
      s.memreq_addr_bits @= s.memreq_addr_out

    s.memreq_M2.type_   //= s.ctrl.memreq_type
    s.memreq_M2.opaque  //= s.cachereq_M2.out.opaque
    s.memreq_M2.addr    //= s.memreq_addr_bits
    s.memreq_M2.len     //= s.mem_req_off_len_M2.len_o
    s.memreq_M2.wr_mask //= s.write_mask_M2.out
    s.memreq_M2.data    //= s.read_data_mux_M2.out

    # Construct the cacheresp signal
    s.cacheresp_M2.type_  //= s.cachereq_M2.out.type_
    s.cacheresp_M2.opaque //= s.cachereq_M2.out.opaque
    s.cacheresp_M2.test   //= s.ctrl.hit_M2
    s.cacheresp_M2.len    //= s.cachereq_M2.out.len
    s.cacheresp_M2.data   //= s.data_size_mux_M2.out

  def line_trace( s ):
    msg = ""
    return msg
