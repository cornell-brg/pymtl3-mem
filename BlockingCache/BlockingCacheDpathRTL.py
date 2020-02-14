"""
=========================================================================
 BlockingCacheDpathRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 15 November 2019
"""

from mem_pclib.constants.constants  import *
from mem_pclib.ifcs.dpathStructs    import mk_pipeline_msg
from mem_pclib.rtl.AddrDecoder      import AddrDecoder
from mem_pclib.rtl.MSHR_v1          import MSHR
from mem_pclib.rtl.utils            import EComp
from pymtl3                         import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn
from sram.SramPRTL                  import SramPRTL

class BlockingCacheDpathRTL (Component):

  def construct( s, param ):

    #---------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------- 
    
    # Proc -> Cache
    s.cachereq            = InPort(param.CacheMsg.Req)
    
    # Mem -> Cache
    s.memresp_Y           = InPort(param.MemMsg.Resp)

    # Cache -> Proc
    s.cacheresp_opaque_M2 = OutPort(param.BitsOpaque)
    s.cacheresp_type_M2   = OutPort(param.BitsType) 
    s.cacheresp_data_M2	  = OutPort(param.BitsData)	
    s.cacheresp_len_M2    = OutPort(param.BitsLen)
    
    # Cache -> Mem 
    s.memreq_opaque_M2    = OutPort(param.BitsOpaque)
    s.memreq_addr_M2      = OutPort(param.BitsAddr)
    s.memreq_data_M2      = OutPort(param.BitsCacheline)

    #--------------------------------------------------------------------------
    # M0 Dpath Signals 
    #--------------------------------------------------------------------------

    s.tag_array_val_M0      = InPort(param.BitsAssoc)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(param.BitsTagwben)
    s.ctrl_bit_val_wr_M0    = InPort(Bits1) 
    s.ctrl_bit_dty_wr_M0    = InPort(Bits1) 
    s.reg_en_M0             = InPort(Bits1)
    s.memresp_mux_sel_M0    = InPort(Bits1)
    s.addr_mux_sel_M0       = InPort(Bits2)
    s.wdata_mux_sel_M0      = InPort(Bits1)
    s.memresp_type_M0       = OutPort(param.BitsType)
    
    # Signals for multiway param.associativity
    s.ctrl_bit_rep_wr_M0    = InPort(param.BitsAssoclog2)

    #--------------------------------------------------------------------------
    # M1 Dpath Signals
    #--------------------------------------------------------------------------

    s.reg_en_M1             = InPort(Bits1)
    s.data_array_val_M1     = InPort(Bits1)
    s.data_array_type_M1    = InPort(Bits1)
    s.data_array_wben_M1    = InPort(param.BitsDataWben)
    s.evict_mux_sel_M1      = InPort(Bits1)
    s.ctrl_bit_dty_rd_M1    = OutPort(param.BitsAssoc) 
    s.tag_match_M1          = OutPort(Bits1) 
    s.cachereq_type_M1      = OutPort(param.BitsType)
    s.offset_M1             = OutPort(param.BitsOffset)
    s.len_M1                = OutPort(param.BitsLen)

    # MSHR Signals
    s.MSHR_alloc_en         = InPort (Bits1)
    s.MSHR_dealloc_en       = InPort(Bits1)
    s.MSHR_full             = OutPort(Bits1)
    s.MSHR_empty            = OutPort(Bits1)
    s.MSHR_type             = OutPort(param.BitsType)
    s.MSHR_ptr              = OutPort(param.BitsAssoclog2)

    # Stall Registers for saving outputs from tag array
    s.stall_mux_sel_M1      = InPort(Bits1)
    s.stall_reg_en_M1       = InPort(Bits1)
    
    # Signals for multiway param.associativity
    s.tag_match_way_M1      = OutPort(param.BitsAssoclog2)
    s.way_offset_M1         = InPort(param.BitsAssoclog2)
    s.ctrl_bit_rep_en_M1    = InPort(Bits1)
    s.ctrl_bit_rep_rd_M1    = OutPort(param.BitsAssoclog2)
    
    if param.associativity == 1: # Not necessary for Dmapped cache
      s.tag_match_way_M1  //= param.BitsAssoclog2(0)
      s.ctrl_bit_rep_rd_M1//= param.BitsAssoclog2(0)
    #---------------------------------------------------------------------------
    # M2 Dpath Signals
    #--------------------------------------------------------------------------

    s.reg_en_M2                 = InPort(Bits1)
    s.read_data_mux_sel_M2      = InPort(Bits1)
    s.read_word_mux_sel_M2      = InPort(param.BitsRdWordMuxSel)
    s.read_byte_mux_sel_M2      = InPort(param.BitsRdByteMuxSel)
    s.read_2byte_mux_sel_M2     = InPort(param.BitsRd2ByteMuxSel)
    s.subword_access_mux_sel_M2 = InPort(Bits2)
    s.cachereq_type_M2          = OutPort(param.BitsType)
    s.offset_M2                 = OutPort(param.BitsOffset)
    s.len_M2                    = OutPort(param.BitsLen)
    # Saves the data from data array in case of stalls
    s.stall_reg_en_M2           = InPort(Bits1)
    s.stall_mux_sel_M2          = InPort(Bits1)

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    
    s.cachereq_M0         = Wire(param.PipelineMsg)
    s.cachereq_M1         = Wire(param.PipelineMsg)
    s.MSHR_dealloc_out    = Wire(param.MSHRMsg)

    # Replicator
    s.cachereq_data_M0    = Wire(param.BitsData)
    s.replicator_out_M0   = Wire(param.BitsCacheline)
    @s.update
    def replicator(): # replicates based on word access (len)
      if s.cachereq_M0.len == 1: 
        for i in range(0,param.bitwidth_cacheline,8): # byte
          s.replicator_out_M0[i:i+8] = s.cachereq_data_M0
      elif s.cachereq_M0.len == 2:
        for i in range(0,param.bitwidth_cacheline,16): #hald word
          s.replicator_out_M0[i:i+16] = s.cachereq_data_M0
      else:
        for i in range(0,param.bitwidth_cacheline,param.bitwidth_data):
          s.replicator_out_M0[i:i+param.bitwidth_data] = s.cachereq_data_M0

    # Pipeline Registers
    s.memresp_M0 = Wire(param.MemMsg.Resp)
    s.pipeline_reg_M0 = RegEnRst(param.MemMsg.Resp)(
      en  = s.reg_en_M0,
      in_ = s.memresp_Y,
      out = s.memresp_M0,
    )
    s.memresp_type_M0 //= s.memresp_M0.type_

    # Cachereq or Memresp select muxes
    s.len_mux_M0 = Mux(param.BitsLen, 2)\
    (
      in_ = {
        0: s.cachereq.len,
        1: s.MSHR_dealloc_out.len
      },
      sel = s.memresp_mux_sel_M0,
      out = s.cachereq_M0.len,
    )
    
    s.opaque_mux_M0 = Mux(param.BitsOpaque, 2)\
    (
      in_ = {
        0: s.cachereq.opaque,
        1: s.MSHR_dealloc_out.opaque
      },
      sel = s.memresp_mux_sel_M0,
      out = s.cachereq_M0.opaque,
    )

    s.type_mux_M0 = Mux(param.BitsType, 2)\
    (
      in_ = {
        0: s.cachereq.type_,
        1: s.MSHR_dealloc_out.type_
      },
      sel = s.memresp_mux_sel_M0,
      out = s.cachereq_M0.type_,
    )

    s.addr_mux_M0 = Mux(param.BitsAddr, 3)\
    (
      in_ = {
        0: s.cachereq.addr,
        1: s.MSHR_dealloc_out.addr,
        2: s.cachereq_M1.addr
      },
      sel = s.addr_mux_sel_M0,
      out = s.cachereq_M0.addr,
    )

    # Located before the replicator
    s.dealloc_data_mux_M0 = Mux(param.BitsData, 2)(
      in_ = {
        0: s.cachereq.data,
        1: s.MSHR_dealloc_out.data
      },
      sel = s.memresp_mux_sel_M0,
      out = s.cachereq_data_M0
    )

    s.write_data_mux_M0 = Mux(param.BitsCacheline, 2)\
    (
      in_ = {
        0: s.replicator_out_M0,
        1: s.memresp_M0.data
      },
      sel = s.wdata_mux_sel_M0,
      out = s.cachereq_M0.data,
    )

    s.addr_tag_M0    = Wire(param.BitsTag)
    s.addr_index_M0  = Wire(param.BitsIdx)
    s.addr_offset_M0 = Wire(param.BitsOffset)
    s.addr_tag_M1    = Wire(param.BitsTag)
    s.addr_index_M1  = Wire(param.BitsIdx)
    s.addr_offset_M1 = Wire(param.BitsOffset)
    s.addr_decode_M0 = AddrDecoder(param)(
      addr_in     = s.cachereq_M0.addr,
      tag_out     = s.addr_tag_M0, 
      index_out   = s.addr_index_M0,
      offset_out  = s.addr_offset_M0,
    )

    ## Tag Array ##
    s.tag_array_idx_M0      = Wire(param.BitsIdx)
    s.tag_array_wdata_M0    = Wire(param.BitsTagArray)
    s.tag_array_rdata_M1    = [Wire(param.BitsTagArray) for _ in range(param.associativity)]

    s.tag_array_idx_M0                          //= s.addr_index_M0
    s.tag_array_wdata_M0[0:param.bitwidth_tag]  //= s.addr_tag_M0
    # valid bit at top
    s.tag_array_wdata_M0[param.bitwidth_tag_array-1:param.bitwidth_tag_array]  //= s.ctrl_bit_val_wr_M0
    # Dirty bit 2nd to top
    s.tag_array_wdata_M0[param.bitwidth_tag_array-2:param.bitwidth_tag_array-1]//= s.ctrl_bit_dty_wr_M0
    if param.associativity == 1:
      s.tag_array_out_M1 = Wire(param.BitsTagArray)
      s.tag_array_M1 = SramPRTL(param.bitwidth_tag_array, param.nblocks_per_way)(
        port0_val   = s.tag_array_val_M0,
        port0_type  = s.tag_array_type_M0,
        port0_idx   = s.tag_array_idx_M0,
        port0_wdata = s.tag_array_wdata_M0,
        port0_wben  = s.tag_array_wben_M0,
        port0_rdata = s.tag_array_out_M1,
      )
      s.stall_out_M1 = Wire(param.BitsTagArray)
      s.stall_reg_M1 = RegEn( param.BitsTagArray )(
        en  = s.stall_reg_en_M1,
        in_ = s.tag_array_out_M1,
        out = s.stall_out_M1 
      )
      s.stall_mux_M1 = Mux( param.BitsTagArray, 2 )(
        in_ = {
          0: s.tag_array_out_M1,
          1: s.stall_out_M1 
        },
        sel = s.stall_mux_sel_M1,
        out = s.tag_array_rdata_M1[0],
      )
    else:
      s.ctrl_bit_rep_M1 = Wire(param.BitsAssoclog2) 
      
      # Register File to store the Replacement info
      # Can't store in SRAM since we need to constantly access
      # them for LRU
      s.replacement_bits_M1 = RegisterFile( param.BitsAssoclog2, param.nblocks_per_way )
      s.replacement_bits_M1.raddr[0] //= s.addr_index_M1
      s.replacement_bits_M1.rdata[0] //= s.ctrl_bit_rep_M1
      s.replacement_bits_M1.waddr[0] //= s.addr_index_M1
      s.replacement_bits_M1.wdata[0] //= s.ctrl_bit_rep_wr_M0
      s.replacement_bits_M1.wen[0]   //= s.ctrl_bit_rep_en_M1      
      # Can possibly store in SRAM if we use FIFO rep policy
      s.tag_array_out_M1 = [Wire(param.BitsTagArray) for _ in range(param.associativity)]
      s.tag_arrays_M1 = [
        SramPRTL(param.bitwidth_tag_array, param.nblocks_per_way)(
          port0_val   = s.tag_array_val_M0[i],
          port0_type  = s.tag_array_type_M0,
          port0_idx   = s.tag_array_idx_M0,
          port0_wdata = s.tag_array_wdata_M0,
          port0_wben  = s.tag_array_wben_M0,
          port0_rdata = s.tag_array_out_M1[i],
        ) for i in range(param.associativity)
      ]
      s.ctrl_bit_rep_rd_M1 //= s.ctrl_bit_rep_M1

      s.stall_out_M1 = [Wire(param.BitsTagArray) for _ in range(param.associativity)]
      
      s.stall_reg_M1 = [RegEn( param.BitsTagArray )( # Saves output of the SRAM during stall
        en  = s.stall_reg_en_M1,               # which is only saved for 1 cycle
        in_ = s.tag_array_out_M1[i],
        out = s.stall_out_M1[i] 
      ) for i in range(param.associativity)]
      
      s.stall_mux_M1 = [Mux( param.BitsTagArray, 2 )(
        in_ = {
          0: s.tag_array_out_M1[i],
          1: s.stall_out_M1[i] 
        },
        sel = s.stall_mux_sel_M1,
        out = s.tag_array_rdata_M1[i],
      ) for i in range(param.associativity)]

    #--------------------------------------------------------------------
    # M1 Stage 
    #--------------------------------------------------------------------
    s.cachereq_M1_2       = Wire(param.PipelineMsg)

    # Pipeline registers
    s.pipeline_reg_M1 = RegEnRst(param.PipelineMsg)(
      en  = s.reg_en_M1,
      in_ = s.cachereq_M0,
      out = s.cachereq_M1,
    )

    s.addr_decode_M1 = AddrDecoder(param)(
      addr_in     = s.cachereq_M1.addr,
      tag_out     = s.addr_tag_M1, 
      index_out   = s.addr_index_M1,
      offset_out  = s.addr_offset_M1,
    )

    s.cachereq_type_M1 //= s.cachereq_M1.type_
    s.len_M1 //= s.cachereq_M1.len

    ## MSHR ##
    # keep entries at 1
    s.MSHR_alloc_in    = Wire(param.MSHRMsg)
    s.MSHR_alloc_id    = Wire(param.BitsOpaque)
    s.MSHR_dealloc_id  = Wire(param.BitsOpaque)
    s.mshr = MSHR( param, 1 )(
      alloc_en   = s.MSHR_alloc_en,
      alloc_in   = s.MSHR_alloc_in,
      alloc_id   = s.MSHR_alloc_id,
      full       = s.MSHR_full,
      empty      = s.MSHR_empty,
      dealloc_id = s.MSHR_dealloc_id,
      dealloc_en = s.MSHR_dealloc_en,
      dealloc_out= s.MSHR_dealloc_out,
    )
    s.MSHR_alloc_in.type_   //= s.cachereq_M1.type_
    s.MSHR_alloc_in.addr    //= s.cachereq_M1.addr
    s.MSHR_alloc_in.opaque  //= s.cachereq_M1.opaque
    s.MSHR_alloc_in.data    //= s.cachereq_M1.data[0:param.bitwidth_data] 
    s.MSHR_alloc_in.len     //= s.cachereq_M1.len
    s.MSHR_alloc_in.repl    //= s.ctrl_bit_rep_rd_M1
    s.MSHR_dealloc_id       //= s.memresp_M0.opaque
    s.MSHR_ptr              //= s.MSHR_dealloc_out.repl
    s.MSHR_type             //= s.MSHR_dealloc_out.type_ 

    s.ctrl_bit_val_rd_M1 = Wire(param.BitsAssoc)
    # Output the valid bit
    for i in range( param.associativity ):
      s.ctrl_bit_val_rd_M1[i] //= s.tag_array_rdata_M1[i][param.bitwidth_tag_array-1:param.bitwidth_tag_array] 
      s.ctrl_bit_dty_rd_M1[i] //= s.tag_array_rdata_M1[i][param.bitwidth_tag_array-2:param.bitwidth_tag_array-1] 
    
    s.offset_M1 //= s.addr_offset_M1
    # Comparator
    if param.associativity == 1:
      @s.update
      def DmappedComparator_M1():
        s.tag_match_M1 = n
        if ( s.ctrl_bit_val_rd_M1 ):
          if s.tag_array_rdata_M1[0][0:param.bitwidth_tag] == s.addr_tag_M1:
            s.tag_match_M1 = y
    else: # Multiway asso
      s.match_way_M1 = Wire(param.BitsAssoclog2)
      s.tag_match_way_M1 //= s.match_way_M1 # way pointer
      @s.update
      def AssoComparator_M1():
        s.tag_match_M1 = n
        for i in range( param.associativity ):
          if ( s.ctrl_bit_val_rd_M1[i] ):
            if s.tag_array_rdata_M1[i][0:param.bitwidth_tag] == s.addr_tag_M1:
              s.tag_match_M1 = y
              s.match_way_M1 = param.BitsAssoclog2(i) # If not valid, then no comparisons
          
          # required and we just say it is a miss by setting this to 0
    
    s.evict_way_out_M1 = Wire(param.BitsTag)
    # Mux for choosing which way to evict
    if param.associativity == 1:
      s.evict_way_out_M1 //= s.tag_array_rdata_M1[0][0:param.bitwidth_tag]
    else:
      # If more than one way, we would have a mux to determine which way to
      # select
      s.evict_way_mux_M1 = Mux(param.BitsTag, param.associativity)(
        sel = s.ctrl_bit_rep_M1,
        out = s.evict_way_out_M1
      )
      for i in range(param.associativity):
        s.evict_way_mux_M1.in_[i] //= s.tag_array_rdata_M1[i][0:param.bitwidth_tag]

    s.evict_addr_M1       = Wire(param.BitsAddr)
    s.evict_addr_M1[param.bitwidth_offset+param.bitwidth_index:param.bitwidth_addr] //= s.evict_way_out_M1 # set the tag
    # set the idx; idx is the same as the cachereq_addr
    s.evict_addr_M1[param.bitwidth_offset:param.bitwidth_offset+param.bitwidth_index] //= s.addr_index_M1
    # Zero the offset since this will be a memreq
    s.evict_addr_M1[0:param.bitwidth_offset]       //= param.BitsOffset(0) 
    s.evict_mux_M1 = Mux(param.BitsAddr, 2)\
    (
      in_ = {
        0: s.cachereq_M1.addr,
        1: s.evict_addr_M1
      },
      sel = s.evict_mux_sel_M1,
      out = s.cachereq_M1_2.addr
    )

    ## Data Array ##
    s.data_array_wdata_M1 = Wire(param.BitsCacheline)
    s.data_array_rdata_M2 = Wire(param.BitsCacheline)
    s.data_array_wdata_M1 //= s.cachereq_M1.data  
    
    # Index bits change depending on param.associativity
    if param.associativity == 1:
      s.data_array_idx_M1   = Wire(param.BitsIdx)
      s.data_array_idx_M1 //= s.addr_index_M1
    else:
      BitsClogNlines = mk_bits(clog2(param.total_num_cachelines))
      s.data_array_idx_M1   = Wire(BitsClogNlines)
      @s.update
      def choice_calc_M1():
        s.data_array_idx_M1 = BitsClogNlines(s.addr_index_M1) \
          + BitsClogNlines(s.way_offset_M1) * BitsClogNlines(param.nblocks_per_way)
    
    s.data_array_out_M2 = Wire(param.BitsCacheline)
    s.data_array_M2 = SramPRTL(param.bitwidth_cacheline, param.total_num_cachelines)(
      port0_val   = s.data_array_val_M1,
      port0_type  = s.data_array_type_M1,
      port0_idx   = s.data_array_idx_M1,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.data_array_wben_M1,
      port0_rdata = s.data_array_out_M2,
    )
    s.stall_out_M2 = Wire( param.BitsCacheline )
    s.stall_reg_M2 = RegEn( param.BitsCacheline )(
      en  = s.stall_reg_en_M2,
      in_ = s.data_array_out_M2,
      out = s.stall_out_M2
    )
    s.stall_mux_M2 = Mux( param.BitsCacheline, 2 )(
      in_ = {
        0: s.data_array_out_M2,
        1: s.stall_out_M2 
      },
      sel = s.stall_mux_sel_M2,
      out = s.data_array_rdata_M2,
    )

    s.cachereq_M1_2.len     //= s.cachereq_M1.len
    s.cachereq_M1_2.data    //= s.cachereq_M1.data
    s.cachereq_M1_2.type_   //= s.cachereq_M1.type_
    s.cachereq_M1_2.opaque  //= s.cachereq_M1.opaque
    #----------------------------------------------------------------
    # M2 Stage 
    #----------------------------------------------------------------
    
    # Pipeline registers
    s.cachereq_M2 = Wire(param.PipelineMsg)
    s.pipeline_reg_M2 = RegEnRst(param.PipelineMsg)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_M1_2,
      out = s.cachereq_M2,
    )
    s.len_M2              //= s.cachereq_M2.len
    s.cacheresp_len_M2    //= s.cachereq_M2.len
    s.cacheresp_opaque_M2 //= s.cachereq_M2.opaque
    s.cachereq_type_M2    //= s.cachereq_M2.type_

    s.read_data_M2     = Wire(param.BitsCacheline)
    s.read_data_mux_M2 = Mux(param.BitsCacheline, 2)\
    (
      in_ = {
        0: s.data_array_rdata_M2,
        1: s.cachereq_M2.data
      },
      sel = s.read_data_mux_sel_M2,
      out = s.read_data_M2,
    )
    
    # WORD SELECT MUX
    s.read_word_mux_out_M2 = Wire(param.BitsData)
    s.read_word_mux_M2 = Mux(param.BitsData, param.bitwidth_cacheline//param.bitwidth_data+1)\
    (
      sel = s.read_word_mux_sel_M2,
      out = s.read_word_mux_out_M2,
    )
    s.read_word_mux_M2.in_[0] //= param.BitsData(0) 
    for i in range(1, param.bitwidth_cacheline//param.bitwidth_data+1):
      s.read_word_mux_M2.in_[i] //= s.read_data_M2[(i-1)*param.bitwidth_data:i*param.bitwidth_data]
    
    # Bytes are always 8 bits
    # BYTE SELECT MUX
    s.byte_read_mux_out_M2 = Wire(Bits8)
    s.read_byte_mux_M2 = Mux(Bits8, param.bitwidth_data//8)(
      sel = s.read_byte_mux_sel_M2,
      out = s.byte_read_mux_out_M2
    )
    # Parameterization
    for i in range(param.bitwidth_data//8):
      s.read_byte_mux_M2.in_[i] //= s.read_word_mux_out_M2[i*8:(i+1)*8]
    # must zero extend the output to param.bitwidth_data (16 -> 32 bits)
    s.byte_read_zero_extended_M2 = Wire(param.BitsData)
    s.byte_read_zero_extended_M2[8:param.bitwidth_data] //= 0
    s.byte_read_zero_extended_M2[0:8]    //= s.byte_read_mux_out_M2
    
    # half word mux always 16 bits
    # TWO BYTE SELECT MUX
    s.half_word_read_mux_out_M2 = Wire(Bits16)
    s.read_half_word_mux_M2 = Mux(Bits16, param.bitwidth_data//16)(
      sel = s.read_2byte_mux_sel_M2 ,
      out = s.half_word_read_mux_out_M2
    )
    for i in range(param.bitwidth_data//16):
      s.read_half_word_mux_M2.in_[i] //= s.read_word_mux_out_M2[i*16:(i+1)*16]

    s.half_word_read_zero_extended_M2 = Wire(param.BitsData)
    s.half_word_read_zero_extended_M2[16:param.bitwidth_data] //= 0
    s.half_word_read_zero_extended_M2[0:16]   //= s.half_word_read_mux_out_M2

    # Subword Access Mux
    s.subword_access_mux = Mux(param.BitsData, 3)(
      in_ = {
        0: s.read_word_mux_out_M2,
        1: s.byte_read_zero_extended_M2,
        2: s.half_word_read_zero_extended_M2
      },
      sel = s.subword_access_mux_sel_M2,
      out = s.cacheresp_data_M2,
    )

    s.cacheresp_type_M2       //= s.cachereq_type_M2
    s.offset_M2               //= s.cachereq_M2.addr[0:param.bitwidth_offset]
    s.memreq_opaque_M2        //= s.cachereq_M2.opaque
    s.memreq_addr_M2[0:param.bitwidth_offset] //= param.BitsOffset(0)
    s.memreq_addr_M2[param.bitwidth_offset:param.bitwidth_addr] //= s.cachereq_M2.addr[param.bitwidth_offset:param.bitwidth_addr]
    s.memreq_data_M2          //= s.read_data_M2

  def line_trace( s ):
    msg = ""
    msg += s.mshr.line_trace()
    return msg
