"""
=========================================================================
 BlockingCacheDpathRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 20 February 2020
"""

from mem_pclib.constants.constants  import *
from mem_pclib.ifcs.dpathStructs    import mk_pipeline_msg
from mem_pclib.rtl.AddrDecoder      import AddrDecoder
from mem_pclib.rtl.MSHR_v1          import MSHR
from mem_pclib.rtl.PMux             import PMux
from mem_pclib.rtl.utils            import EComp
from pymtl3                         import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn
from sram.SramPRTL                  import SramPRTL

class BlockingCacheDpathRTL (Component):

  def construct( s, p ):

    #--------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------
    
    # Proc -> Cache
    s.cachereq            = InPort(p.CacheMsg.Req)
    
    # Mem -> Cache
    s.memresp_Y           = InPort(p.MemMsg.Resp)
    
    s.ctrl_in             = InPort(p.CtrlSignalsOut)
    s.dpath_out           = OutPort(p.DpathSignalsOut)
    
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------

    # Pipeline Registers
    s.pipeline_reg_M0 = RegEnRst(p.MemMsg.Resp)(
      en  = s.ctrl_in.reg_en_M0,
      in_ = s.memresp_Y
    )
    s.dpath_out.memresp_type_M0 //= s.pipeline_reg_M0.out.type_

    # Cachereq or Memresp select muxes
    s.cachereq_M0         = Wire(p.PipelineMsg)
    s.MSHR_dealloc_out    = Wire(p.MSHRMsg)

    s.cachereq_msg_mux_in_M0 = Wire( p.MuxM0Msg ) 
    s.MSHR_dealloc_mux_in_M0 = Wire( p.MuxM0Msg ) 
    s.cachereq_msg_mux_in_M0.type_ //= s.cachereq.type_
    s.cachereq_msg_mux_in_M0.opaque//= s.cachereq.opaque
    s.cachereq_msg_mux_in_M0.len   //= s.cachereq.len
    s.cachereq_msg_mux_in_M0.data  //= s.cachereq.data
    s.MSHR_dealloc_mux_in_M0.type_ //= s.MSHR_dealloc_out.type_
    s.MSHR_dealloc_mux_in_M0.opaque//= s.MSHR_dealloc_out.opaque
    s.MSHR_dealloc_mux_in_M0.len   //= s.MSHR_dealloc_out.len
    s.MSHR_dealloc_mux_in_M0.data  //= s.MSHR_dealloc_out.data

    s.cachereq_msg_mux_M0 = Mux( p.MuxM0Msg , 2)(
      in_ = {
        0: s.cachereq_msg_mux_in_M0,
        1: s.MSHR_dealloc_mux_in_M0
      },
      sel = s.ctrl_in.memresp_mux_sel_M0,
    )

    s.cachereq_M0.len             //= s.cachereq_msg_mux_M0.out.len
    s.cachereq_M0.type_           //= s.cachereq_msg_mux_M0.out.type_
    s.cachereq_M0.opaque          //= s.cachereq_msg_mux_M0.out.opaque

    s.cachereq_addr_M1_forward = Wire(p.BitsAddr)
    s.addr_mux_M0 = Mux(p.BitsAddr, 3)\
    (
      in_ = {
        0: s.cachereq.addr,
        1: s.MSHR_dealloc_out.addr,
        2: s.cachereq_addr_M1_forward
      },
      sel = s.ctrl_in.addr_mux_sel_M0,
      out = s.cachereq_M0.addr,
    )

    # Replicator
    s.replicator_out_M0   = Wire(p.BitsCacheline)
    @s.update
    def replicator(): 
      if s.cachereq_msg_mux_M0.out.len == 1: 
        for i in range(0,p.bitwidth_cacheline,8): # byte
          s.replicator_out_M0[i:i+8] = s.cachereq_msg_mux_M0.out.data
      elif s.cachereq_msg_mux_M0.out.len == 2:
        for i in range(0,p.bitwidth_cacheline,16): # half word
          s.replicator_out_M0[i:i+16] = s.cachereq_msg_mux_M0.out.data
      else:
        for i in range(0,p.bitwidth_cacheline,p.bitwidth_data):
          s.replicator_out_M0[i:i+p.bitwidth_data] = s.cachereq_msg_mux_M0.out.data

    s.write_data_mux_M0 = Mux(p.BitsCacheline, 2)\
    (
      in_ = {
        0: s.replicator_out_M0,
        1: s.pipeline_reg_M0.out.data
      },
      sel = s.ctrl_in.wdata_mux_sel_M0,
      out = s.cachereq_M0.data,
    )

    s.addr_decode_M0 = AddrDecoder(p)(
      addr_in     = s.cachereq_M0.addr
    )

    # Tag Array Signals
    s.tag_array_idx_M0      = Wire(p.BitsIdx)
    s.tag_array_wdata_M0    = Wire(p.BitsTagArray)
    s.tag_array_rdata_M1    = [Wire(p.BitsTagArray) for _ in range(p.associativity)]

    s.tag_array_idx_M0                      //= s.addr_decode_M0.index_out
    s.tag_array_wdata_M0[0:p.bitwidth_tag]  //= s.addr_decode_M0.tag_out 
    s.tag_array_wdata_M0[p.bitwidth_tag_array-1:p.bitwidth_tag_array]   //= s.ctrl_in.ctrl_bit_val_wr_M0 # Valid bit 
    s.tag_array_wdata_M0[p.bitwidth_tag_array-2:p.bitwidth_tag_array-1] //= s.ctrl_in.ctrl_bit_dty_wr_M0 # Dirty bit

    s.dpath_out.cachereq_type_M0  //= s.cachereq_msg_mux_M0.out.type_

    #--------------------------------------------------------------------
    # M1 Stage 
    #--------------------------------------------------------------------

    # Pipeline registers
    s.cachereq_M1 = RegEnRst(p.PipelineMsg)(
      en  = s.ctrl_in.reg_en_M1,
      in_ = s.cachereq_M0,
    )
    s.cachereq_addr_M1_forward //= s.cachereq_M1.out.addr

    s.addr_decode_M1 = AddrDecoder(p)(
      addr_in     = s.cachereq_M1.out.addr,
    )

    # Register File to store the Replacement info
    # Can possibly store in SRAM if we use FIFO rep policy
    s.ctrl_bit_rep_M1 = Wire(p.BitsAssoclog2) 
    s.replacement_bits_M1 = RegisterFile( p.BitsAssoclog2, p.nblocks_per_way )
    s.replacement_bits_M1.raddr[0] //= s.addr_decode_M1.index_out
    s.replacement_bits_M1.rdata[0] //= s.ctrl_bit_rep_M1
    s.replacement_bits_M1.waddr[0] //= s.addr_decode_M1.index_out
    s.replacement_bits_M1.wdata[0] //= s.ctrl_in.ctrl_bit_rep_wr_M0
    s.replacement_bits_M1.wen[0]   //= s.ctrl_in.ctrl_bit_rep_en_M1      
    
    # TODO change the initialization 
    s.tag_array_out_M1 = [Wire(p.BitsTagArray) for _ in range(p.associativity)]
    s.tag_arrays_M1 = [
      SramPRTL(p.bitwidth_tag_array, p.nblocks_per_way)(
        port0_val   = s.ctrl_in.tag_array_val_M0[i],
        port0_type  = s.ctrl_in.tag_array_type_M0,
        port0_idx   = s.tag_array_idx_M0,
        port0_wdata = s.tag_array_wdata_M0,
        port0_wben  = s.ctrl_in.tag_array_wben_M0,
        port0_rdata = s.tag_array_out_M1[i],
      ) for i in range(p.associativity)
    ]
    
    s.stall_reg_M1 = [RegEn( p.BitsTagArray )( # Saves output of the SRAM during stall
      en  = s.ctrl_in.stall_reg_en_M1,         # which is only saved for 1 cycle
      in_ = s.tag_array_out_M1[i],
    ) for i in range(p.associativity)]
    
    s.stall_mux_M1 = [Mux( p.BitsTagArray, 2 )(
      in_ = {
        0: s.tag_array_out_M1[i],
        1: s.stall_reg_M1[i].out 
      },
      sel = s.ctrl_in.stall_mux_sel_M1,
      out = s.tag_array_rdata_M1[i],
    ) for i in range(p.associativity)]

    # MSHR (1 entry) 
    s.MSHR_alloc_in    = Wire(p.MSHRMsg)
    s.MSHR_alloc_id    = Wire(p.BitsOpaque)
    s.mshr = MSHR( p, 1 )(
      alloc_en   = s.ctrl_in.MSHR_alloc_en,
      alloc_in   = s.MSHR_alloc_in,
      alloc_id   = s.MSHR_alloc_id,
      full       = s.dpath_out.MSHR_full,
      empty      = s.dpath_out.MSHR_empty,
      dealloc_id = s.pipeline_reg_M0.out.opaque,
      dealloc_en = s.ctrl_in.MSHR_dealloc_en,
      dealloc_out= s.MSHR_dealloc_out,
    )
    s.MSHR_alloc_in.type_   //= s.cachereq_M1.out.type_
    s.MSHR_alloc_in.addr    //= s.cachereq_M1.out.addr
    s.MSHR_alloc_in.opaque  //= s.cachereq_M1.out.opaque
    s.MSHR_alloc_in.data    //= s.cachereq_M1.out.data[0:p.bitwidth_data] 
    s.MSHR_alloc_in.len     //= s.cachereq_M1.out.len
    s.MSHR_alloc_in.repl    //= s.dpath_out.ctrl_bit_rep_rd_M1

    # Output the valid bit
    s.ctrl_bit_val_rd_M1 = Wire(p.BitsAssoc)
    for i in range( p.associativity ):
      s.ctrl_bit_val_rd_M1[i] //= s.tag_array_rdata_M1[i][p.bitwidth_tag_array-1:p.bitwidth_tag_array] 
      s.dpath_out.ctrl_bit_dty_rd_M1[i] //= s.tag_array_rdata_M1[i][p.bitwidth_tag_array-2:p.bitwidth_tag_array-1] 
    
    # Comparator
    @s.update
    def Comparator():
      s.dpath_out.tag_match_M1 = n
      s.dpath_out.tag_match_way_M1 = p.BitsAssoclog2(0)
      for i in range( p.associativity ):
        if ( s.ctrl_bit_val_rd_M1[i] ):
          if s.tag_array_rdata_M1[i][0:p.bitwidth_tag] == s.addr_decode_M1.tag_out:
            s.dpath_out.tag_match_M1 = y
            s.dpath_out.tag_match_way_M1 = p.BitsAssoclog2(i) 
    
    # Mux for choosing which way to evict
    s.evict_way_out_M1 = Wire(p.BitsTag)
    s.evict_way_mux_M1 = PMux(p.BitsTag, p.associativity)(
      sel = s.ctrl_bit_rep_M1,
      out = s.evict_way_out_M1
    )
    for i in range(p.associativity):
      s.evict_way_mux_M1.in_[i] //= s.tag_array_rdata_M1[i][0:p.bitwidth_tag]

    s.evict_addr_M1    = Wire(p.BitsAddr)
    s.evict_addr_M1[p.bitwidth_offset+p.bitwidth_index:p.bitwidth_addr] //= s.evict_way_out_M1 # set tag
    s.evict_addr_M1[p.bitwidth_offset:p.bitwidth_offset+p.bitwidth_index] //= s.addr_decode_M1.index_out  # set index
    s.evict_addr_M1[0:p.bitwidth_offset] //= p.BitsOffset(0) # Zero the offset since this will be a memreq
    s.cachereq_M1_2 = Wire(p.PipelineMsg)
    s.evict_mux_M1  = Mux(p.BitsAddr, 2)\
    (
      in_ = {
        0: s.cachereq_M1.out.addr,
        1: s.evict_addr_M1 
      },
      sel = s.ctrl_in.evict_mux_sel_M1,
      out = s.cachereq_M1_2.addr
    )

    # Data Array
    s.data_array_wdata_M1 = Wire(p.BitsCacheline)
    s.data_array_wdata_M1 //= s.cachereq_M1.out.data  
    
    # Index bits change depending on associativity
    BitsClogNlines = mk_bits(clog2(p.total_num_cachelines))
    s.data_array_idx_M1 = Wire(BitsClogNlines)
    @s.update
    def choice_calc_M1():
      s.data_array_idx_M1 = BitsClogNlines(s.addr_decode_M1.index_out) \
        + BitsClogNlines(s.ctrl_in.way_offset_M1) * BitsClogNlines(p.nblocks_per_way)
    
    s.cachereq_M1_2.len     //= s.cachereq_M1.out.len
    s.cachereq_M1_2.data    //= s.cachereq_M1.out.data
    s.cachereq_M1_2.type_   //= s.cachereq_M1.out.type_
    s.cachereq_M1_2.opaque  //= s.cachereq_M1.out.opaque

    s.dpath_out.ctrl_bit_rep_rd_M1  //= s.ctrl_bit_rep_M1
    s.dpath_out.cachereq_type_M1    //= s.cachereq_M1.out.type_
    s.dpath_out.len_M1              //= s.cachereq_M1.out.len
    s.dpath_out.offset_M1           //= s.addr_decode_M1.offset_out
    s.dpath_out.MSHR_ptr            //= s.MSHR_dealloc_out.repl
    s.dpath_out.MSHR_type           //= s.MSHR_dealloc_out.type_ 
    
    #--------------------------------------------------------------------
    # M2 Stage 
    #--------------------------------------------------------------------
    
    # Pipeline registers
    s.cachereq_M2 = RegEnRst(p.PipelineMsg)(
      en  = s.ctrl_in.reg_en_M2,
      in_ = s.cachereq_M1_2,
    )
    s.dpath_out.len_M2              //= s.cachereq_M2.out.len
    s.dpath_out.cacheresp_len_M2    //= s.cachereq_M2.out.len
    s.dpath_out.cacheresp_opaque_M2 //= s.cachereq_M2.out.opaque
    s.dpath_out.cachereq_type_M2    //= s.cachereq_M2.out.type_

    s.data_array_M2 = SramPRTL(p.bitwidth_cacheline, p.total_num_cachelines)(
      port0_val   = s.ctrl_in.data_array_val_M1,
      port0_type  = s.ctrl_in.data_array_type_M1,
      port0_idx   = s.data_array_idx_M1,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.ctrl_in.data_array_wben_M1
    )

    s.stall_reg_M2 = RegEn( p.BitsCacheline )(
      en  = s.ctrl_in.stall_reg_en_M2,
      in_ = s.data_array_M2.port0_rdata
    )
    
    s.stall_mux_M2 = Mux( p.BitsCacheline, 2 )(
      in_ = {
        0: s.data_array_M2.port0_rdata,
        1: s.stall_reg_M2.out 
      },
      sel = s.ctrl_in.stall_mux_sel_M2
    )

    s.read_data_mux_M2 = Mux(p.BitsCacheline, 2)\
    (
      in_ = {
        0: s.stall_mux_M2.out,
        1: s.cachereq_M2.out.data
      },
      sel = s.ctrl_in.read_data_mux_sel_M2
    )
    
    # Word select mux 
    s.read_word_mux_M2 = Mux(p.BitsData, p.bitwidth_cacheline // p.bitwidth_data + 1)\
    (
      sel = s.ctrl_in.read_word_mux_sel_M2
    )
    s.read_word_mux_M2.in_[0] //= p.BitsData(0) 
    for i in range(1, p.bitwidth_cacheline//p.bitwidth_data+1):
      s.read_word_mux_M2.in_[i] //= s.read_data_mux_M2.out[(i - 1) * p.bitwidth_data:i * p.bitwidth_data]
        
    # Two byte select mux
    s.read_half_word_mux_M2 = Mux(Bits16, p.bitwidth_data//16)(
      sel = s.ctrl_in.read_2byte_mux_sel_M2 
    )
    for i in range(p.bitwidth_data//16):
      s.read_half_word_mux_M2.in_[i] //= s.read_word_mux_M2.out[i * 16:(i + 1) * 16]

    s.half_word_read_zero_extended_M2 = Wire(p.BitsData)
    s.half_word_read_zero_extended_M2[16:p.bitwidth_data] //= 0
    s.half_word_read_zero_extended_M2[0:16] //= s.read_half_word_mux_M2.out

    # Byte select mux
    s.read_byte_mux_M2 = Mux(Bits8, p.bitwidth_data//8)(
      sel = s.ctrl_in.read_byte_mux_sel_M2
    )
    for i in range(p.bitwidth_data//8):
      s.read_byte_mux_M2.in_[i] //= s.read_word_mux_M2.out[i * 8:(i + 1) * 8]

    s.byte_read_zero_extended_M2 = Wire(p.BitsData)
    s.byte_read_zero_extended_M2[8:p.bitwidth_data] //= 0
    s.byte_read_zero_extended_M2[0:8] //= s.read_byte_mux_M2.out

    # Datasize Mux
    s.subword_access_mux = Mux(p.BitsData, 3)(
      in_ = {
        0: s.read_word_mux_M2.out,
        1: s.byte_read_zero_extended_M2,
        2: s.half_word_read_zero_extended_M2
      },
      sel = s.ctrl_in.subword_access_mux_sel_M2,
      out = s.dpath_out.cacheresp_data_M2,
    )

    s.dpath_out.cacheresp_type_M2                                 //= s.dpath_out.cachereq_type_M2
    s.dpath_out.offset_M2                                         //= s.cachereq_M2.out.addr[0:p.bitwidth_offset]
    s.dpath_out.memreq_opaque_M2                                  //= s.cachereq_M2.out.opaque
    s.dpath_out.memreq_addr_M2[0:p.bitwidth_offset]               //= p.BitsOffset(0)
    s.dpath_out.memreq_addr_M2[p.bitwidth_offset:p.bitwidth_addr] //= s.cachereq_M2.out.addr[p.bitwidth_offset:p.bitwidth_addr]
    s.dpath_out.memreq_data_M2                                    //= s.read_data_mux_M2.out

  def line_trace( s ):
    msg = ""
    msg += s.mshr.line_trace()
    return msg
