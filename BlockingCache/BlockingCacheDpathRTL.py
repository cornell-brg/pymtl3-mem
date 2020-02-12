"""
=========================================================================
 BlockingCacheDpathRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 15 November 2019
"""

from mem_pclib.rtl.utils            import EComp
from pymtl3                         import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn
from sram.SramPRTL                  import SramPRTL
from mem_pclib.constants            import *
# from mem_pclib.ifc.dpathStructs     import mk_pipeline_msg

class BlockingCacheDpathRTL (Component):

  def construct( s, param ):
    
    #---------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------- 
    
    # Proc -> Cache
    s.cachereq_M0         = InPort(param.CacheMsg.Req)
    # s.s.cachereq_M0.opaque  = InPort(param.BitsOpaque)
    # s.s.cachereq_M0.type_    = InPort(param.BitsType)
    # s.cachereq_M0.addr    = InPort(param.BitsAddr)
    # s.cachereq_M0.data    = InPort(param.BitsData)
    # s.cachereq_M0.len     = InPort(param.BitsLen)
    
    # Mem -> Cache
    s.memresp_Y           = InPort(param.MemMsg.Resp)
    # s.memresp_Y.opaque    = InPort(param.BitsOpaque)
    # s.memresp_Y.type_      = InPort(param.BitsType)
    # s.memresp_Y.data      = InPort(param.BitsCacheline)
    
    # Cache -> Proc
    # s.cachresp_M2         = InPort(param.CacheMsg.Resp)
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
    s.wdata_mux_sel_M0      = InPort(Bits2)
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
    s.reg_en_MSHR           = InPort (Bits1)
    s.MSHR_type             = OutPort(param.BitsType)
    # Stall Registers
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

    s.reg_en_M2             = InPort(Bits1)
    s.read_data_mux_sel_M2  = InPort(Bits1)
    s.read_word_mux_sel_M2  = InPort(param.BitsRdWordMuxSel)
    s.read_byte_mux_sel_M2  = InPort(param.BitsRdByteMuxSel)
    s.read_half_word_mux_sel_M2 = InPort(param.BitsRd2ByteMuxSel)
    s.subword_access_mux_sel_M2 = InPort(Bits2)
    s.cachereq_type_M2      = OutPort(param.BitsType)
    s.offset_M2             = OutPort(param.BitsOffset)
    s.len_M2                = OutPort(param.BitsLen)
    s.stall_reg_en_M2                = InPort(Bits1)
    s.stall_mux_sel_M2                = InPort(Bits1)

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    
    s.memresp_data_M0     = Wire(param.BitsCacheline)
    s.len_M0              = Wire(param.BitsLen)
    s.MSHR_len_M0         = Wire(param.BitsLen)
    s.memresp_opaque_M0   = Wire(param.BitsOpaque)
    s.opaque_M0           = Wire(param.BitsOpaque)
    s.data_array_wdata_M0 = Wire(param.BitsCacheline)
    s.MSHR_type_M0        = Wire(param.BitsType)
    s.type_M0             = Wire(param.BitsType)
    s.MSHR_addr_M0        = Wire(param.BitsAddr)
    s.addr_M0             = Wire(param.BitsAddr)
    s.MSHR_data_M0        = Wire(param.BitsCacheline)
    s.cachereq_M1.addr    = Wire(param.BitsAddr)
    s.rep_out_M0          = Wire(param.BitsCacheline)

    # Replicator
    @s.update
    def replicator(): # replicates based on word access
      if s.len_M0 == 1: 
        for i in range(0,param.bitwidth_cacheline,8): # byte
          s.rep_out_M0[i:i+8] = s.cachereq_M0.data
      elif s.len_M0 == 2:
        for i in range(0,param.bitwidth_cacheline,16): #hald word
          s.rep_out_M0[i:i+16] = s.cachereq_M0.data
      else:
        for i in range(0,param.bitwidth_cacheline,param.bitwidth_data):
          s.rep_out_M0[i:i+param.bitwidth_data] = s.cachereq_M0.data
  
    # Pipeline Registers
    s.memresp_M0 = Wire(param.MemMsg.Resp)
    s.pipeline_reg_M0 = RegEnRst(param.MemMsg.Resp)(
      en  = s.reg_en_M0,
      in_ = s.memresp_Y,
      out = s.memresp_M0,
    )
    s.memresp_type_M0 //= s.memresp_M0.type_
    # s.memresp_data_reg_M0 = RegEnRst(param.BitsCacheline)\
    # (
    #   en  = s.reg_en_M0,
    #   in_ = s.memresp_Y.data,
    #   out = s.memresp_data_M0,
    # )

    # s.memresp_opaque_reg_M0 = RegEnRst(param.BitsOpaque)\
    # (
    #   en  = s.reg_en_M0,
    #   in_ = s.memresp_Y.opaque,
    #   out = s.memresp_opaque_M0,
    # )

    # s.memresp_type_reg_M0 = RegEnRst(param.BitsType)\
    # (
    #   en  = s.reg_en_M0,
    #   in_ = s.memresp_Y.type_,
    #   out = s.memresp_type_M0
    # )

    # Cachereq or Memresp select muxes
    s.len_mux_M0 = Mux(param.BitsLen, 2)\
    (
      in_ = {
        0: s.cachereq_M0.len,
        1: s.MSHR_len_M0
      },
      sel = s.memresp_mux_sel_M0,
      out = s.len_M0,
    )
    
    s.opaque_mux_M0 = Mux(param.BitsOpaque, 2)\
    (
      in_ = {
        0: s.cachereq_M0.opaque,
        1: s.memresp_M0.opaque
      },
      sel = s.memresp_mux_sel_M0,
      out = s.opaque_M0,
    )

    s.type_mux_M0 = Mux(param.BitsType, 2)\
    (
      in_ = {
        0: s.cachereq_M0.type_,
        1: s.MSHR_type_M0
      },
      sel = s.memresp_mux_sel_M0,
      out = s.type_M0,
    )

    s.addr_mux_M0 = Mux(param.BitsAddr, 3)\
    (
      in_ = {
        0: s.cachereq_M0.addr,
        1: s.MSHR_addr_M0,
        2: s.cachereq_M1.addr
      },
      sel = s.addr_mux_sel_M0,
      out = s.addr_M0,
    )

    s.write_data_mux_M0 = Mux(param.BitsCacheline, 3)\
    (
      in_ = {0: s.rep_out_M0,
            1: s.memresp_M0.data,
            2: s.MSHR_data_M0},
      sel = s.wdata_mux_sel_M0,
      out = s.data_array_wdata_M0,
    )

    # Tag Array

    s.tag_array_idx_M0      = Wire(param.BitsIdx)
    s.tag_array_wdata_M0    = Wire(param.BitsTagArray)
    s.tag_array_rdata_M1    = [Wire(param.BitsTagArray) for _ in range(param.associativity)]

    s.tag_array_idx_M0               //= s.addr_M0[param.bitwidth_offset:param.bitwidth_index+param.bitwidth_offset]
    s.tag_array_wdata_M0[0:param.bitwidth_tag]      //= s.addr_M0[param.bitwidth_offset+param.bitwidth_index:param.bitwidth_index+param.bitwidth_offset+param.bitwidth_tag]
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
      s.replacement_bits_M1.raddr[0] //= s.cachereq_M1.addr[param.bitwidth_offset:param.bitwidth_index+param.bitwidth_offset]
      s.replacement_bits_M1.rdata[0] //= s.ctrl_bit_rep_M1
      s.replacement_bits_M1.waddr[0] //= s.cachereq_M1.addr[param.bitwidth_offset:param.bitwidth_index+param.bitwidth_offset]
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
    
    s.cachereq_opaque_M1  = Wire(param.BitsOpaque)
    s.cachereq_len_M1     = Wire(param.BitsLen)
    s.cachereq_data_M1    = Wire(param.BitsCacheline)
    
    # Pipeline registers
    s.cachereq_M1 = Wire(param.CacheMsg.Req)
    s.pipeline_reg_M1 = RegEnRst(param.CacheMsg.Req)(
      en  = s.reg_en_M1,
      in_ = s.cachereq_M0,
      out = s.cachereq_M1,
    )

    cachereq_type_M1 //= s.cachereq_M1.type_
    # s.len_M1 //= s.cachereq_len_M1
    # s.cachereq_len_reg_M1 = RegEnRst(param.BitsLen)\
    # ( # registers for subword/word acess 0 = word, 1 = byte, 2 = 2-byte
    #   en  = s.reg_en_M1,
    #   in_ = s.len_M0,
    #   out = s.cachereq_len_M1,
    # )

    # s.cachereq_opaque_reg_M1 = RegEnRst(param.BitsOpaque)\
    # (
    #   en  = s.reg_en_M1,
    #   in_ = s.opaque_M0,
    #   out = s.cachereq_opaque_M1,
    # )

    # s.cachereq_type_reg_M1 = RegEnRst(param.BitsType)\
    # (
    #   en  = s.reg_en_M1,
    #   in_ = s.type_M0,
    #   out = s.cachereq_type_M1,
    # )

    # s.cachereq_address_reg_M1 = RegEnRst(param.BitsAddr)\
    # (
    #   en  = s.reg_en_M1,
    #   in_ = s.addr_M0,
    #   out = s.cachereq_M1.addr,
    # )

    # s.cachereq_data_reg_M1 = RegEnRst(param.BitsCacheline)\
    # (
    #   en  = s.reg_en_M1,
    #   in_ = s.data_array_wdata_M0,
    #   out = s.cachereq_data_M1,
    # )

    # 1 Entry MSHR
    s.MSHR_type_reg = RegEnRst(param.BitsType)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_M1.type_,
      out = s.MSHR_type_M0,
    )

    s.MSHR_addr_reg = RegEnRst(param.BitsAddr)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_M1.addr,
      out = s.MSHR_addr_M0
    )

    s.MSHR_data_reg = RegEnRst(param.BitsCacheline)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_M1.data,
      out = s.MSHR_data_M0
    )

    s.MSHR_len_reg = RegEnRst(param.BitsLen)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_M1.len,
      out = s.MSHR_len_M0
    )

    s.MSHR_type //= s.MSHR_type_M0 
    s.ctrl_bit_val_rd_M1 = Wire(param.BitsAssoc)
    # Output the valid bit
    for i in range( param.associativity ):
      s.ctrl_bit_val_rd_M1[i] //= s.tag_array_rdata_M1[i][param.bitwidth_tag_array-1:param.bitwidth_tag_array] 
      s.ctrl_bit_dty_rd_M1[i] //= s.tag_array_rdata_M1[i][param.bitwidth_tag_array-2:param.bitwidth_tag_array-1] 
    
    s.offset_M1 //= s.cachereq_M1.addr[0:param.bitwidth_offset]
    # Comparator
    if param.associativity == 1:
      @s.update
      def DmappedComparator_M1():
        s.tag_match_M1 = n
        if ( s.ctrl_bit_val_rd_M1 ):
          if s.tag_array_rdata_M1[0][0:param.bitwidth_tag] == s.cachereq_M1.addr[param.bitwidth_index+param.bitwidth_offset:param.bitwidth_offset+param.bitwidth_index+param.bitwidth_tag]:
            s.tag_match_M1 = y
    else: # Multiway asso
      s.match_way_M1 = Wire(param.BitsAssoclog2)
      s.tag_match_way_M1 //= s.match_way_M1
      @s.update
      def AssoComparator_M1():
        s.tag_match_M1 = n
        for i in range( param.associativity ):
          if ( s.ctrl_bit_val_rd_M1[i] ):
            if s.tag_array_rdata_M1[i][0:param.bitwidth_tag] == s.cachereq_M1.addr[param.bitwidth_index+param.bitwidth_offset:param.bitwidth_offset+param.bitwidth_index+param.bitwidth_tag]:
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
    s.cache_addr_M1       = Wire(param.BitsAddr)
    s.evict_addr_M1[param.bitwidth_offset+param.bitwidth_index:param.bitwidth_addr] //= s.evict_way_out_M1 # set the tag
    # set the idx; idx is the same as the cachereq_addr
    s.evict_addr_M1[param.bitwidth_offset:param.bitwidth_offset+param.bitwidth_index] //= s.cachereq_M1.addr[param.bitwidth_offset:param.bitwidth_offset+param.bitwidth_index]
    # Zero the offset since this will be a memreq
    s.evict_addr_M1[0:param.bitwidth_offset]       //= param.BitsOffset(0) 
    s.evict_mux_M1 = Mux(param.BitsAddr, 2)\
    (
      in_ = {
        0: s.cachereq_M1.addr,
        1: s.evict_addr_M1
      },
      sel = s.evict_mux_sel_M1,
      out = s.cache_addr_M1
    )

    # Data Array ( Btwn M1 and M2 )
    s.data_array_wdata_M1 = Wire(param.BitsCacheline)
    s.data_array_rdata_M2 = Wire(param.BitsCacheline)
    s.data_array_wdata_M1 //= s.cachereq_data_M1  
    
    # Index bits change depending on param.associativity
    if param.associativity == 1:
      s.data_array_idx_M1   = Wire(param.BitsIdx)
      s.data_array_idx_M1 //= s.cachereq_M1.addr[param.bitwidth_offset:param.bitwidth_index+param.bitwidth_offset]
    else:
      Bitsparam.total_num_cachelines = mk_bits(clog2(param.total_num_cachelines))
      s.data_array_idx_M1   = Wire(Bitsparam.total_num_cachelines)
      @s.update
      def choice_calc_M1():
        s.data_array_idx_M1 = Bitsparam.total_num_cachelines(s.cachereq_M1.addr[param.bitwidth_offset:param.bitwidth_index+param.bitwidth_offset]) \
          + Bitsparam.total_num_cachelines(s.way_offset_M1) * Bitsparam.total_num_cachelines(param.nblocks_per_way)
    
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

    #----------------------------------------------------------------
    # M2 Stage 
    #----------------------------------------------------------------
    
    # Pipeline registers
    s.cachereq_M2 = Wire(param.CacheMsg.Req)
    s.pipeline_reg_M2 = RegEnRst(param.CacheMsg.Req)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_M1,
      out = s.cachereq_M2,
    )
    s.cacheresp_len_M2    //= s.cachereq_M2.len
    s.len_M2              //= s.cachereq_M2.len
    s.cacheresp_opaque_M2 //= s.cachereq_M2.opaque
    s.cachereq_type_M2    //= s.cachereq_M2.type_
    # s.cachereq_len_M2 = Wire(param.BitsLen)
    # s.cachereq_len_reg_M2 = RegEnRst(param.BitsLen)\
    # (
    #   en  = s.reg_en_M2,
    #   in_ = s.cachereq_len_M1,
    #   out = s.cachereq_len_M2,
    # )
    
    # s.cachereq_opaque_M2  = Wire(param.BitsOpaque)
    # s.cachereq_opaque_reg_M2 = RegEnRst(param.BitsOpaque)\
    # (
    #   en  = s.reg_en_M2,
    #   in_ = s.cachereq_opaque_M1,
    #   out = s.cacheresp_opaque_M2,
    # )
    
    # s.cachereq_type_reg_M2 = RegEnRst(param.BitsType)\
    # (
    #   en  = s.reg_en_M2,
    #   in_ = s.cachereq_type_M1,
    #   out = s.cachereq_type_M2,
    # )

    # s.cachereq_addr_M2    = Wire(param.BitsAddr)
    # s.cachereq_address_reg_M2 = RegEnRst(param.BitsAddr)\
    # (
    #   en  = s.reg_en_M2,
    #   in_ = s.cache_addr_M1,
    #   out = s.cachereq_addr_M2,
    # )

    # s.cachereq_data_M2      = Wire(param.BitsCacheline)
    # s.cachereq_data_reg_M2  = RegEnRst(param.BitsCacheline)\
    # (
    #   en  = s.reg_en_M2,
    #   in_ = s.cachereq_data_M1,
    #   out = s.cachereq_data_M2,
    # )

    s.read_data_M2          = Wire(param.BitsCacheline)
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
      sel = s.read_half_word_mux_sel_M2 ,
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
    s.memreq_addr_M2[param.bitwidth_offset:param.bitwidth_addr] //= s.cachereq_M2.addr[param.bitwidth_offset:param.bitwidth_addr]
    s.memreq_data_M2          //= s.read_data_M2

  def line_trace( s ):
    msg = ""
    return msg
