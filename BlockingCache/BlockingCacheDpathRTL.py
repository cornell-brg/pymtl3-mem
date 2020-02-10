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

# Constants
wr = y             = b1(1)
rd = n = x         = b1(0)

class BlockingCacheDpathRTL (Component):
  def construct(s, 
    bitwidth_addr      = 32,	    # Address bitwidth
    bitwidth_data      = 32,	  	# Data bitwidth
    bitwidth_cacheline = 128,    # Cacheline bitwidth
    bitwidth_index     = 5,      # Index bitwidth
    bitwidth_offset    = 4,      # Offset bitwidth
    bitwidth_tag       = 19,     # Tag bitwidth
    nbl                = 512,    # Number of blocks total
    nby                = 256,    # Number of blocks per way
    BitsLen            = "inv",  # word access type
    BitsAddr           = "inv",  # address type
    BitsOpaque         = "inv",  # opaque type
    BitsType           = "inv",  # type type
    BitsData           = "inv",  # data type
    BitsCacheline      = "inv",  # cacheline type
    BitsIdx            = "inv",  # index type
    BitsTag            = "inv",  # tag type
    BitsOffset         = "inv",  # offset type
    BitsTagArray       = "inv",  # Tag array write byte enable
    BitsTagwben        = "inv",
    BitsDataWben       = "inv",  # Data array write byte enable
    BitsRdWordMuxSel   = "inv",  # Read data mux M2 
    BitsRdByteMuxSel   = "inv",  # Read data mux M2 
    BitsRdHwordMuxSel  = "inv",  # Read data mux M2 
    BitsAssoclog2      = "inv",  # Bits for associativity muxes
    BitsAssoc          = "inv",  # Bits for associativity mask 1 bit for each asso
    bitwidth_tag_array = 32,     # SRAM bit width
    associativity      = 1,      # Number of ways 
  ):
    
    #---------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------- 
    
    # Proc -> Cache
    s.cachereq_opaque_M0  = InPort(BitsOpaque)
    s.cachereq_type_M0    = InPort(BitsType)
    s.cachereq_addr_M0    = InPort(BitsAddr)
    s.cachereq_data_M0    = InPort(BitsData)
    s.cachereq_len_M0     = InPort(BitsLen)
    
    # Mem -> Cache
    s.memresp_opaque_Y    = InPort(BitsOpaque)
    s.memresp_type_Y      = InPort(BitsType)
    s.memresp_data_Y      = InPort(BitsCacheline)
    
    # Cache -> Proc
    s.cacheresp_opaque_M2 = OutPort(BitsOpaque)
    s.cacheresp_type_M2   = OutPort(BitsType) 
    s.cacheresp_data_M2	  = OutPort(BitsData)	
    s.cacheresp_len_M2    = OutPort(BitsLen)
    
    # Cache -> Mem 
    s.memreq_opaque_M2    = OutPort(BitsOpaque)
    s.memreq_addr_M2      = OutPort(BitsAddr)
    s.memreq_data_M2      = OutPort(BitsCacheline)

    #--------------------------------------------------------------------------
    # M0 Dpath Signals 
    #--------------------------------------------------------------------------

    s.tag_array_val_M0      = InPort(BitsAssoc)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(BitsTagwben)
    s.ctrl_bit_val_wr_M0    = InPort(Bits1) 
    s.ctrl_bit_dty_wr_M0    = InPort(Bits1) 
    s.reg_en_M0             = InPort(Bits1)
    s.memresp_mux_sel_M0    = InPort(Bits1)
    s.addr_mux_sel_M0       = InPort(Bits2)
    s.wdata_mux_sel_M0      = InPort(Bits2)
    s.memresp_type_M0       = OutPort(BitsType)
    
    # Signals for multiway associativity
    s.ctrl_bit_rep_wr_M0    = InPort(BitsAssoclog2)

    #--------------------------------------------------------------------------
    # M1 Dpath Signals
    #--------------------------------------------------------------------------

    s.reg_en_M1             = InPort(Bits1)
    s.data_array_val_M1     = InPort(Bits1)
    s.data_array_type_M1    = InPort(Bits1)
    s.data_array_wben_M1    = InPort(BitsDataWben)
    s.evict_mux_sel_M1      = InPort(Bits1)
    s.ctrl_bit_dty_rd_M1    = OutPort(BitsAssoc) 
    s.tag_match_M1          = OutPort(Bits1) 
    s.cachereq_type_M1      = OutPort(BitsType)
    s.offset_M1             = OutPort(BitsOffset)
    s.len_M1                = OutPort(BitsLen)

    # MSHR Signals
    s.reg_en_MSHR           = InPort (Bits1)
    s.MSHR_type             = OutPort(BitsType)
    # Stall Registers
    s.stall_mux_sel_M1      = InPort(Bits1)
    s.stall_reg_en_M1       = InPort(Bits1)
    # Signals for multiway associativity
    s.tag_match_way_M1      = OutPort(BitsAssoclog2)
    s.way_offset_M1         = InPort(BitsAssoclog2)
    s.ctrl_bit_rep_en_M1    = InPort(Bits1)
    s.ctrl_bit_rep_rd_M1    = OutPort(BitsAssoclog2)
    if associativity == 1: # Not necessary for Dmapped cache
      s.tag_match_way_M1  //= BitsAssoclog2(0)
      s.ctrl_bit_rep_rd_M1//= BitsAssoclog2(0)
    #---------------------------------------------------------------------------
    # M2 Dpath Signals
    #--------------------------------------------------------------------------

    s.reg_en_M2             = InPort(Bits1)
    s.read_data_mux_sel_M2  = InPort(Bits1)
    s.read_word_mux_sel_M2  = InPort(BitsRdWordMuxSel)
    s.read_byte_mux_sel_M2  = InPort(BitsRdByteMuxSel)
    s.read_half_word_mux_sel_M2 = InPort(BitsRdHwordMuxSel)
    s.subword_access_mux_sel_M2 = InPort(Bits2)
    s.cachereq_type_M2      = OutPort(BitsType)
    s.offset_M2             = OutPort(BitsOffset)
    s.len_M2                = OutPort(BitsLen)
    s.stall_reg_en_M2                = InPort(Bits1)
    s.stall_mux_sel_M2                = InPort(Bits1)

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    
    s.memresp_data_M0     = Wire(BitsCacheline)
    s.len_M0              = Wire(BitsLen)
    s.MSHR_len_M0         = Wire(BitsLen)
    s.memresp_opaque_M0   = Wire(BitsOpaque)
    s.opaque_M0           = Wire(BitsOpaque)
    s.data_array_wdata_M0 = Wire(BitsCacheline)
    s.MSHR_type_M0        = Wire(BitsType)
    s.type_M0             = Wire(BitsType)
    s.MSHR_addr_M0        = Wire(BitsAddr)
    s.addr_M0             = Wire(BitsAddr)
    s.MSHR_data_M0        = Wire(BitsCacheline)
    s.cachereq_addr_M1    = Wire(BitsAddr)
    s.rep_out_M0          = Wire(BitsCacheline)

    # Replicator
    @s.update
    def replicator(): # replicates based on word access
      if s.len_M0 == 1: 
        for i in range(0,bitwidth_cacheline,8): # byte
          s.rep_out_M0[i:i+8] = s.cachereq_data_M0
      elif s.len_M0 == 2:
        for i in range(0,bitwidth_cacheline,16): #hald word
          s.rep_out_M0[i:i+16] = s.cachereq_data_M0
      else:
        for i in range(0,bitwidth_cacheline,bitwidth_data):
          s.rep_out_M0[i:i+bitwidth_data] = s.cachereq_data_M0
  
    # Pipeline Registers
    s.memresp_data_reg_M0 = RegEnRst(BitsCacheline)\
    (
      en  = s.reg_en_M0,
      in_ = s.memresp_data_Y,
      out = s.memresp_data_M0,
    )

    s.memresp_opaque_reg_M0 = RegEnRst(BitsOpaque)\
    (
      en  = s.reg_en_M0,
      in_ = s.memresp_opaque_Y,
      out = s.memresp_opaque_M0,
    )

    s.memresp_type_reg_M0 = RegEnRst(BitsType)\
    (
      en  = s.reg_en_M0,
      in_ = s.memresp_type_Y,
      out = s.memresp_type_M0
    )

    # Cachereq or Memresp select muxes
    s.len_mux_M0 = Mux(BitsLen, 2)\
    (
      in_ = {0: s.cachereq_len_M0,
            1: s.MSHR_len_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.len_M0,
    )
    
    s.opaque_mux_M0 = Mux(BitsOpaque, 2)\
    (
      in_ = {0: s.cachereq_opaque_M0,
            1: s.memresp_opaque_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.opaque_M0,
    )

    s.type_mux_M0 = Mux(BitsType, 2)\
    (
      in_ = {0: s.cachereq_type_M0,
            1: s.MSHR_type_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.type_M0,
    )

    s.addr_mux_M0 = Mux(BitsAddr, 3)\
    (
      in_ = {0: s.cachereq_addr_M0,
            1: s.MSHR_addr_M0    ,
            2: s.cachereq_addr_M1},
      sel = s.addr_mux_sel_M0,
      out = s.addr_M0,
    )

    s.write_data_mux_M0 = Mux(BitsCacheline, 3)\
    (
      in_ = {0: s.rep_out_M0,
            1: s.memresp_data_M0,
            2: s.MSHR_data_M0},
      sel = s.wdata_mux_sel_M0,
      out = s.data_array_wdata_M0,
    )

    # Tag Array

    s.tag_array_idx_M0      = Wire(BitsIdx)
    s.tag_array_wdata_M0    = Wire(BitsTagArray)
    s.tag_array_rdata_M1    = [Wire(BitsTagArray) for _ in range(associativity)]

    s.tag_array_idx_M0               //= s.addr_M0[bitwidth_offset:bitwidth_index+bitwidth_offset]
    s.tag_array_wdata_M0[0:bitwidth_tag]      //= s.addr_M0[bitwidth_offset+bitwidth_index:bitwidth_index+bitwidth_offset+bitwidth_tag]
    # valid bit at top
    s.tag_array_wdata_M0[bitwidth_tag_array-1:bitwidth_tag_array]  //= s.ctrl_bit_val_wr_M0
    # Dirty bit 2nd to top
    s.tag_array_wdata_M0[bitwidth_tag_array-2:bitwidth_tag_array-1]//= s.ctrl_bit_dty_wr_M0
    if associativity == 1:
      s.tag_array_out_M1 = Wire(BitsTagArray)
      s.tag_array_M1 = SramPRTL(bitwidth_tag_array, nby)(
        port0_val   = s.tag_array_val_M0,
        port0_type  = s.tag_array_type_M0,
        port0_idx   = s.tag_array_idx_M0,
        port0_wdata = s.tag_array_wdata_M0,
        port0_wben  = s.tag_array_wben_M0,
        port0_rdata = s.tag_array_out_M1,
      )
      s.stall_out_M1 = Wire(BitsTagArray)
      s.stall_reg_M1 = RegEn( BitsTagArray )(
        en  = s.stall_reg_en_M1,
        in_ = s.tag_array_out_M1,
        out = s.stall_out_M1 
      )
      s.stall_mux_M1 = Mux( BitsTagArray, 2 )(
        in_ = {
          0: s.tag_array_out_M1,
          1: s.stall_out_M1 
        },
        sel = s.stall_mux_sel_M1,
        out = s.tag_array_rdata_M1[0],
      )
    else:
      s.ctrl_bit_rep_M1 = Wire(BitsAssoclog2) 
      
      # Register File to store the Replacement info
      # Can't store in SRAM since we need to constantly access
      # them for LRU
      s.replacement_bits_M1 = RegisterFile( BitsAssoclog2, nby )
      s.replacement_bits_M1.raddr[0] //= s.cachereq_addr_M1[bitwidth_offset:bitwidth_index+bitwidth_offset]
      s.replacement_bits_M1.rdata[0] //= s.ctrl_bit_rep_M1
      s.replacement_bits_M1.waddr[0] //= s.cachereq_addr_M1[bitwidth_offset:bitwidth_index+bitwidth_offset]
      s.replacement_bits_M1.wdata[0] //= s.ctrl_bit_rep_wr_M0
      s.replacement_bits_M1.wen[0]   //= s.ctrl_bit_rep_en_M1      
      # Can possibly store in SRAM if we use FIFO rep policy
      s.tag_array_out_M1 = [Wire(BitsTagArray) for _ in range(associativity)]
      s.tag_arrays_M1 = [
        SramPRTL(bitwidth_tag_array, nby)(
          port0_val   = s.tag_array_val_M0[i],
          port0_type  = s.tag_array_type_M0,
          port0_idx   = s.tag_array_idx_M0,
          port0_wdata = s.tag_array_wdata_M0,
          port0_wben  = s.tag_array_wben_M0,
          port0_rdata = s.tag_array_out_M1[i],
        ) for i in range(associativity)
      ]
      s.ctrl_bit_rep_rd_M1 //= s.ctrl_bit_rep_M1

      s.stall_out_M1 = [Wire(BitsTagArray) for _ in range(associativity)]
      
      s.stall_reg_M1 = [RegEn( BitsTagArray )( # Saves output of the SRAM during stall
        en  = s.stall_reg_en_M1,               # which is only saved for 1 cycle
        in_ = s.tag_array_out_M1[i],
        out = s.stall_out_M1[i] 
      ) for i in range(associativity)]
      
      s.stall_mux_M1 = [Mux( BitsTagArray, 2 )(
        in_ = {
          0: s.tag_array_out_M1[i],
          1: s.stall_out_M1[i] 
        },
        sel = s.stall_mux_sel_M1,
        out = s.tag_array_rdata_M1[i],
      ) for i in range(associativity)]

    #--------------------------------------------------------------------
    # M1 Stage 
    #--------------------------------------------------------------------
    
    s.cachereq_opaque_M1  = Wire(BitsOpaque)
    s.cachereq_len_M1     = Wire(BitsLen)
    s.cachereq_data_M1    = Wire(BitsCacheline)
    s.len_M1 //= s.cachereq_len_M1
    # Pipeline registers
    s.cachereq_len_reg_M1 = RegEnRst(BitsLen)\
    ( # registers for subword/word acess 0 = word, 1 = byte, 2 = 2-byte
      en  = s.reg_en_M1,
      in_ = s.len_M0,
      out = s.cachereq_len_M1,
    )

    s.cachereq_opaque_reg_M1 = RegEnRst(BitsOpaque)\
    (
      en  = s.reg_en_M1,
      in_ = s.opaque_M0,
      out = s.cachereq_opaque_M1,
    )

    s.cachereq_type_reg_M1 = RegEnRst(BitsType)\
    (
      en  = s.reg_en_M1,
      in_ = s.type_M0,
      out = s.cachereq_type_M1,
    )

    s.cachereq_address_reg_M1 = RegEnRst(BitsAddr)\
    (
      en  = s.reg_en_M1,
      in_ = s.addr_M0,
      out = s.cachereq_addr_M1,
    )

    s.cachereq_data_reg_M1 = RegEnRst(BitsCacheline)\
    (
      en  = s.reg_en_M1,
      in_ = s.data_array_wdata_M0,
      out = s.cachereq_data_M1,
    )

    # 1 Entry MSHR
    s.MSHR_type_reg = RegEnRst(BitsType)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_type_M1,
      out = s.MSHR_type_M0,
    )

    s.MSHR_addr_reg = RegEnRst(BitsAddr)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_addr_M1,
      out = s.MSHR_addr_M0
    )

    s.MSHR_data_reg = RegEnRst(BitsCacheline)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_data_M1,
      out = s.MSHR_data_M0
    )

    s.MSHR_len_reg = RegEnRst(BitsLen)\
    (
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_len_M1,
      out = s.MSHR_len_M0
    )

    s.MSHR_type //= s.MSHR_type_M0 
    s.ctrl_bit_val_rd_M1 = Wire(BitsAssoc)
    # Output the valid bit
    for i in range( associativity ):
      s.ctrl_bit_val_rd_M1[i] //= s.tag_array_rdata_M1[i][bitwidth_tag_array-1:bitwidth_tag_array] 
      s.ctrl_bit_dty_rd_M1[i] //= s.tag_array_rdata_M1[i][bitwidth_tag_array-2:bitwidth_tag_array-1] 
    
    s.offset_M1 //= s.cachereq_addr_M1[0:bitwidth_offset]
    # Comparator
    if associativity == 1:
      @s.update
      def DmappedComparator_M1():
        s.tag_match_M1 = n
        if ( s.ctrl_bit_val_rd_M1 ):
          if s.tag_array_rdata_M1[0][0:bitwidth_tag] == s.cachereq_addr_M1[bitwidth_index+bitwidth_offset:bitwidth_offset+bitwidth_index+bitwidth_tag]:
            s.tag_match_M1 = y
    else: # Multiway asso
      s.match_way_M1 = Wire(BitsAssoclog2)
      s.tag_match_way_M1 //= s.match_way_M1
      @s.update
      def AssoComparator_M1():
        s.tag_match_M1 = n
        for i in range( associativity ):
          if ( s.ctrl_bit_val_rd_M1[i] ):
            if s.tag_array_rdata_M1[i][0:bitwidth_tag] == s.cachereq_addr_M1[bitwidth_index+bitwidth_offset:bitwidth_offset+bitwidth_index+bitwidth_tag]:
              s.tag_match_M1 = y
              s.match_way_M1 = BitsAssoclog2(i) # If not valid, then no comparisons
          
          # required and we just say it is a miss by setting this to 0
    
    s.evict_way_out_M1 = Wire(BitsTag)
    # Mux for choosing which way to evict
    if associativity == 1:
      s.evict_way_out_M1 //= s.tag_array_rdata_M1[0][0:bitwidth_tag]
    else:
      s.evict_way_mux_M1 = Mux(BitsTag, associativity)(
        sel = s.ctrl_bit_rep_M1,
        out = s.evict_way_out_M1
      )
      for i in range(associativity):
        s.evict_way_mux_M1.in_[i] //= s.tag_array_rdata_M1[i][0:bitwidth_tag]

    s.evict_addr_M1       = Wire(BitsAddr)
    s.cache_addr_M1       = Wire(BitsAddr)
    s.evict_addr_M1[bitwidth_offset+bitwidth_index:bitwidth_addr] //= s.evict_way_out_M1 # set the tag
    # set the idx; idx is the same as the cachereq_addr
    s.evict_addr_M1[bitwidth_offset:bitwidth_offset+bitwidth_index] //= s.cachereq_addr_M1[bitwidth_offset:bitwidth_offset+bitwidth_index]
    # Zero the offset since this will be a memreq
    s.evict_addr_M1[0:bitwidth_offset]       //= BitsOffset(0) 
    s.evict_mux_M1 = Mux(BitsAddr, 2)\
    (
      in_ = {0: s.cachereq_addr_M1,
            1: s.evict_addr_M1},
      sel = s.evict_mux_sel_M1,
      out = s.cache_addr_M1
    )

    # Data Array ( Btwn M1 and M2 )
    s.data_array_wdata_M1 = Wire(BitsCacheline)
    s.data_array_rdata_M2 = Wire(BitsCacheline)
    s.data_array_wdata_M1 //= s.cachereq_data_M1  
    
    # Index bits change depending on associativity
    if associativity == 1:
      s.data_array_idx_M1   = Wire(BitsIdx)
      s.data_array_idx_M1 //= s.cachereq_addr_M1[bitwidth_offset:bitwidth_index+bitwidth_offset]
    else:
      BitsNbl = mk_bits(clog2(nbl))
      s.data_array_idx_M1   = Wire(BitsNbl)
      @s.update
      def choice_calc_M1():
        s.data_array_idx_M1 = BitsNbl(s.cachereq_addr_M1[bitwidth_offset:bitwidth_index+bitwidth_offset]) \
          + BitsNbl(s.way_offset_M1) * BitsNbl(nby)
    
    s.data_array_out_M2 = Wire(BitsCacheline)
    s.data_array_M2 = SramPRTL(bitwidth_cacheline, nbl)(
      port0_val   = s.data_array_val_M1,
      port0_type  = s.data_array_type_M1,
      port0_idx   = s.data_array_idx_M1,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.data_array_wben_M1,
      port0_rdata = s.data_array_out_M2,
    )
    s.stall_out_M2 = Wire(BitsCacheline)
    s.stall_reg_M2 = RegEn( BitsCacheline )(
      en  = s.stall_reg_en_M2,
      in_ = s.data_array_out_M2,
      out = s.stall_out_M2
    )
    s.stall_mux_M2 = Mux( BitsCacheline, 2 )(
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
    s.cachereq_len_M2 = Wire(BitsLen)
    s.cachereq_len_reg_M2 = RegEnRst(BitsLen)\
    (
      en  = s.reg_en_M2,
      in_ = s.cachereq_len_M1,
      out = s.cachereq_len_M2,
    )
    s.cacheresp_len_M2 //= s.cachereq_len_M2
    s.len_M2           //= s.cachereq_len_M2
    
    s.cachereq_opaque_M2  = Wire(BitsOpaque)
    s.cachereq_opaque_reg_M2 = RegEnRst(BitsOpaque)\
    (
      en  = s.reg_en_M2,
      in_ = s.cachereq_opaque_M1,
      out = s.cacheresp_opaque_M2,
    )
    
    s.cachereq_type_reg_M2 = RegEnRst(BitsType)\
    (
      en  = s.reg_en_M2,
      in_ = s.cachereq_type_M1,
      out = s.cachereq_type_M2,
    )

    s.cachereq_addr_M2    = Wire(BitsAddr)
    s.cachereq_address_reg_M2 = RegEnRst(BitsAddr)\
    (
      en  = s.reg_en_M2,
      in_ = s.cache_addr_M1,
      out = s.cachereq_addr_M2,
    )

    s.cachereq_data_M2      = Wire(BitsCacheline)
    s.cachereq_data_reg_M2  = RegEnRst(BitsCacheline)\
    (
      en  = s.reg_en_M2,
      in_ = s.cachereq_data_M1,
      out = s.cachereq_data_M2,
    )

    s.read_data_M2          = Wire(BitsCacheline)
    s.read_data_mux_M2 = Mux(BitsCacheline, 2)\
    (
      in_ = {0: s.data_array_rdata_M2,
            1: s.cachereq_data_M2},
      sel = s.read_data_mux_sel_M2,
      out = s.read_data_M2,
    )
    
    # WORD SELECT MUX
    s.read_word_mux_out_M2 = Wire(BitsData)
    s.read_word_mux_M2 = Mux(BitsData, bitwidth_cacheline//bitwidth_data+1)\
    (
      sel = s.read_word_mux_sel_M2,
      out = s.read_word_mux_out_M2,
    )
    s.read_word_mux_M2.in_[0] //= BitsData(0) 
    for i in range(1, bitwidth_cacheline//bitwidth_data+1):
      s.read_word_mux_M2.in_[i] //= s.read_data_M2[(i-1)*bitwidth_data:i*bitwidth_data]
    
    # Bytes are always 8 bits
    # BYTE SELECT MUX
    s.byte_read_mux_out_M2 = Wire(Bits8)
    s.read_byte_mux_M2 = Mux(Bits8, bitwidth_data//8)(
      sel = s.read_byte_mux_sel_M2,
      out = s.byte_read_mux_out_M2
    )
    # Parameterization
    for i in range(bitwidth_data//8):
      s.read_byte_mux_M2.in_[i] //= s.read_word_mux_out_M2[i*8:(i+1)*8]
    # must zero extend the output to bitwidth_data (16 -> 32 bits)
    s.byte_read_zero_extended_M2 = Wire(BitsData)
    s.byte_read_zero_extended_M2[8:bitwidth_data] //= 0
    s.byte_read_zero_extended_M2[0:8]    //= s.byte_read_mux_out_M2
    
    # half word mux always 16 bits
    # HALF WORD SELECT MUX
    s.half_word_read_mux_out_M2 = Wire(Bits16)
    s.read_half_word_mux_M2 = Mux(Bits16, bitwidth_data//16)(
      sel = s.read_half_word_mux_sel_M2 ,
      out = s.half_word_read_mux_out_M2
    )
    for i in range(bitwidth_data//16):
      s.read_half_word_mux_M2.in_[i] //= s.read_word_mux_out_M2[i*16:(i+1)*16]

    s.half_word_read_zero_extended_M2 = Wire(BitsData)
    s.half_word_read_zero_extended_M2[16:bitwidth_data] //= 0
    s.half_word_read_zero_extended_M2[0:16]   //= s.half_word_read_mux_out_M2

    # Subword Access Mux
    s.subword_access_mux = Mux(BitsData, 3)(
      in_ = {
        0: s.read_word_mux_out_M2,
        1: s.byte_read_zero_extended_M2,
        2: s.half_word_read_zero_extended_M2
      },
      sel = s.subword_access_mux_sel_M2,
      out = s.cacheresp_data_M2,
    )

    s.cacheresp_type_M2       //= s.cachereq_type_M2
    s.offset_M2               //= s.cachereq_addr_M2[0:bitwidth_offset]
    s.memreq_opaque_M2        //= s.cacheresp_opaque_M2
    s.memreq_addr_M2[bitwidth_offset:bitwidth_addr] //= s.cachereq_addr_M2[bitwidth_offset:bitwidth_addr]
    s.memreq_data_M2          //= s.read_data_M2

  def line_trace( s ):
    msg = ""
    return msg
