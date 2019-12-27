"""
=========================================================================
 BlockingCacheDpathPRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Datapath

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 15 November 2019
"""

from mem_pclib.rtl.utils            import EComp
from pymtl3                         import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.registers    import RegEnRst
from sram.SramPRTL                  import SramPRTL

# Constants
wr = y             = b1(1)
rd = n = x         = b1(0)

class BlockingCacheDpathPRTL (Component):
  def construct(s, 
                abw = 32,		 # Address bitwidth
                dbw = 32,		 # Data bitwidth
                clw = 128,   # Cacheline bitwidth
                idw = 5,     # Index bitwidth
                ofw = 4,     # Offset bitwidth
                tgw = 19,    # Tag bitwidth
                nbl = 512,   # Number of blocks total
                nby = 256,   # Number of blocks per way
                BitsAddr      = "inv",  # address bitstruct
                BitsOpaque    = "inv",  # opaque bitstruct
                BitsType      = "inv",  # type bitstruct
                BitsData      = "inv",  # data bitstruct
                BitsCacheline = "inv",  # cacheline bitstruct
                BitsIdx       = "inv",  # index bitstruct
                BitsTag       = "inv",  # tag bitstruct
                BitsOffset    = "inv",  # offset bitstruct
                BitsTagWben   = "inv",  # Tag array write byte enable
                BitsDataWben  = "inv",  # Data array write byte enable
                BitsRdDataMux = "inv",  # Read data mux M2 
                BitsAssoclog2 = "inv",  # Bits for associativity muxes
                BitsAssoc     = "inv",  # Bits for associativity mask 1 bit for each asso
                associativity = 1,      # Number of ways 
  ):
	
    #---------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------- 
		
    # Proc -> Cache
    s.cachereq_opaque_M0  = InPort(BitsOpaque)
    s.cachereq_type_M0    = InPort(BitsType)
    s.cachereq_addr_M0    = InPort(BitsAddr)
    s.cachereq_data_M0    = InPort(BitsData)
    # Mem -> Cache
    s.memresp_opaque_Y    = InPort(BitsOpaque)
    s.memresp_type_Y      = InPort(BitsType)
    s.memresp_data_Y      = InPort(BitsCacheline)
    # Cache -> Proc
    s.cacheresp_opaque_M2 = OutPort(BitsOpaque)
    s.cacheresp_type_M2   = OutPort(BitsType) 
    s.cacheresp_data_M2	  = OutPort(BitsData)	
    # Cache -> Mem 
    s.memreq_opaque_M2    = OutPort(BitsOpaque)
    s.memreq_addr_M2      = OutPort(BitsAddr)
    s.memreq_data_M2      = OutPort(BitsCacheline)
   
    #-------------------------------------------------------------------
    # Control Signals (ctrl -> dpath)
    #-------------------------------------------------------------------

    #--------------------------------------------------------------------------
    # M0 Dpath Signals 
    #--------------------------------------------------------------------------

    s.tag_array_val_M0      = InPort(BitsAssoc)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(BitsTagWben)
    s.ctrl_bit_val_wr_M0    = InPort(Bits1) 
    s.ctrl_bit_dty_wr_M0    = InPort(Bits1) 
    s.reg_en_M0             = InPort(Bits1)
    s.memresp_mux_sel_M0    = InPort(Bits1)
    s.addr_mux_sel_M0       = InPort(Bits2)
    s.wdata_mux_sel_M0      = InPort(Bits2)
    s.memresp_type_M0       = OutPort(BitsType)
    
    # Signals for multiway associativity
    # if associativity > 1:
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

    # MSHR Signals
    s.reg_en_MSHR           = InPort (Bits1)
    s.MSHR_type             = OutPort(BitsType)
    
    # Signals for multiway associativity
    # if associativity > 1:
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
    s.read_data_way_mux_sel_M2=InPort(BitsAssoclog2)
    s.read_word_mux_sel_M2  = InPort(BitsRdDataMux)
    s.cachereq_type_M2      = OutPort(BitsType)
    s.offset_M2             = OutPort(BitsOffset)

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    
    s.memresp_data_M0     = Wire(BitsCacheline)
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
    for i in range(0,clw,dbw):
      connect(s.rep_out_M0[i:i+dbw], s.cachereq_data_M0)
   
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
    sbw  = abw #tgw + 1 + 1 
    BitsTagSRAM = mk_bits(sbw)
    s.tag_array_idx_M0      = Wire(BitsIdx)
    s.tag_array_wdata_M0    = Wire(BitsTagSRAM)
    s.tag_array_rdata_M1    = [Wire(BitsTagSRAM) for _ in range(associativity)]

    s.tag_array_idx_M0               //= s.addr_M0[ofw:idw+ofw]
    s.tag_array_wdata_M0[0:tgw]      //= s.addr_M0[ofw+idw:idw+ofw+tgw]
    # valid bit at top
    s.tag_array_wdata_M0[sbw-1:sbw]  //= s.ctrl_bit_val_wr_M0
    # Dirty bit 2nd to top
    s.tag_array_wdata_M0[sbw-2:sbw-1]//= s.ctrl_bit_dty_wr_M0
    if associativity == 1:
      s.tag_array_M1 = SramPRTL(sbw, nby)(
        port0_val   = s.tag_array_val_M0,
        port0_type  = s.tag_array_type_M0,
        port0_idx   = s.tag_array_idx_M0,
        port0_wdata = s.tag_array_wdata_M0,
        port0_wben  = s.tag_array_wben_M0,
        port0_rdata = s.tag_array_rdata_M1[0],
      )
    else:
      s.ctrl_bit_rep_M1 = Wire(BitsAssoclog2) 
      
      # Register File to store the Replacement info
      # Can't store in SRAM since we need to constantly access
      # them for LRU
      s.replacement_bits_M1 = RegisterFile( BitsAssoclog2, nby )
      s.replacement_bits_M1.raddr[0] //= s.cachereq_addr_M1[ofw:idw+ofw]
      s.replacement_bits_M1.rdata[0] //= s.ctrl_bit_rep_M1
      s.replacement_bits_M1.waddr[0] //= s.cachereq_addr_M1[ofw:idw+ofw]
      s.replacement_bits_M1.wdata[0] //= s.ctrl_bit_rep_wr_M0
      s.replacement_bits_M1.wen[0]   //= s.ctrl_bit_rep_en_M1      
      # Can possibly store in SRAM if we use FIFO rep policy
      s.tag_arrays_M1 = [
        SramPRTL(sbw, nby)(
          port0_val   = s.tag_array_val_M0[i],
          port0_type  = s.tag_array_type_M0,
          port0_idx   = s.tag_array_idx_M0,
          port0_wdata = s.tag_array_wdata_M0,
          port0_wben  = s.tag_array_wben_M0,
          port0_rdata = s.tag_array_rdata_M1[i],
        ) for i in range(associativity)
      ]
      s.ctrl_bit_rep_rd_M1 //= s.ctrl_bit_rep_M1
      # rep_bw = clog2(associativity) # replacement bitwidth
      # srbw = sbw + rep_bw
      # s.tag_array_wdata_rep_M0    = Wire(mk_bits(srbw))
      # s.tag_arrays_M1 = [None]*associativity
      # s.tag_array_wdata_rep_M0[0:tgw]        //= s.addr_M0[ofw+idw:idw+ofw+tgw]
      # # valid bit at top
      # s.tag_array_wdata_rep_M0[srbw-1:srbw]  //= s.ctrl_bit_val_wr_M0
      # # Dirty bit 2nd to top
      # s.tag_array_wdata_rep_M0[srbw-2:srbw-1]//= s.ctrl_bit_dty_wr_M0
      # # Replacement way stored in sram_bw
      # s.tag_array_wdata_rep_M0[srbw-2-rep_bw:srbw-2] //= s.ctrl_bit_rep_wr_M0
      # s.tag_arrays_M1[0] = SramPRTL(srbw, nby)(
      #   port0_val     = s.tag_array_val_M0[0],
      #   port0_type    = s.tag_array_type_M0,
      #   port0_idx     = s.tag_array_idx_M0,
      #   port0_wdata   = s.tag_array_wdata_rep_M0,
      #   port0_wben    = s.tag_array_wben_M0,
      #   port0_rdata   = s.tag_array_rdata_M1[0],
      # )
      # for i in range( 1, associativity ):
      #   s.tag_arrays_M1[i] = SramPRTL(sbw, nby)(
      #     port0_val   = s.tag_array_val_M0[i],
      #     port0_type  = s.tag_array_type_M0,
      #     port0_idx   = s.tag_array_idx_M0,
      #     port0_wdata = s.tag_array_wdata_M0,
      #     port0_wben  = s.tag_array_wben_M0,
      #     port0_rdata = s.tag_array_rdata_M1[i],
      #   )
      # print (s.tag_arrays_M1[0], s.tag_arrays_M1[1])

    #--------------------------------------------------------------------
    # M1 Stage 
    #--------------------------------------------------------------------
    
    s.cachereq_opaque_M1  = Wire(BitsOpaque)
    s.cachereq_data_M1    = Wire(BitsCacheline)

    # Pipeline registers
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

    s.MSHR_type //= s.MSHR_type_M0 
    s.ctrl_bit_val_rd_M1 = Wire(BitsAssoc)
    # Output the valid bit
    for i in range( associativity ):
      s.ctrl_bit_val_rd_M1[i] //= s.tag_array_rdata_M1[i][sbw-1:sbw] 
      s.ctrl_bit_dty_rd_M1[i] //= s.tag_array_rdata_M1[i][sbw-2:sbw-1] 
     
    s.offset_M1 //= s.cachereq_addr_M1[0:ofw]
    # Comparator
    if associativity == 1:
      @s.update
      def DmappedComparator_M1():
        s.tag_match_M1 = n
        if ( s.ctrl_bit_val_rd_M1 ):
          if s.tag_array_rdata_M1[0][0:tgw] == s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw]:
            s.tag_match_M1 = y
    else: # Multiway asso
      s.match_way_M1 = Wire(BitsAssoclog2)
      s.tag_match_way_M1 //= s.match_way_M1
      @s.update
      def AssoComparator_M1():
        s.tag_match_M1 = n
        for i in range( associativity ):
          if ( s.ctrl_bit_val_rd_M1[i] ):
            if s.tag_array_rdata_M1[i][0:tgw] == s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw]:
              s.tag_match_M1 = y
              s.match_way_M1 = BitsAssoclog2(i) # If not valid, then no comparisons
          
          # required and we just say it is a miss by setting this to 0
    
    s.evict_way_out_M1 = Wire(BitsTag)
    # Mux for choosing which way to evict
    if associativity == 1:
      s.evict_way_out_M1 //= s.tag_array_rdata_M1[0][0:tgw]
    else:
      s.evict_way_mux_M1 = Mux(BitsTag, associativity)(
        sel = s.ctrl_bit_rep_M1,
        out = s.evict_way_out_M1
      )
      for i in range(associativity):
        s.evict_way_mux_M1.in_[i] //= s.tag_array_rdata_M1[i][0:tgw]

    s.evict_addr_M1       = Wire(BitsAddr)
    s.cache_addr_M1       = Wire(BitsAddr)
    s.evict_addr_M1[ofw+idw:abw] //= s.evict_way_out_M1 # set the tag
    # set the idx; idx is the same as the cachereq_addr
    s.evict_addr_M1[ofw:ofw+idw] //= s.cachereq_addr_M1[ofw:ofw+idw]
    # Zero the offset since this will be a memreq
    s.evict_addr_M1[0:ofw]       //= BitsOffset(0) 
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
      s.data_array_idx_M1 //= s.cachereq_addr_M1[ofw:idw+ofw]
    else:
      BitsNbl = mk_bits(clog2(nbl))
      s.data_array_idx_M1   = Wire(BitsNbl)
      @s.update
      def choice_calc_M1():
        s.data_array_idx_M1 = BitsNbl(s.cachereq_addr_M1[ofw:idw+ofw]) \
          + BitsNbl(s.way_offset_M1) * BitsNbl(nby)
    
    s.data_array_M2 = SramPRTL(clw, nbl)(
      port0_val   = s.data_array_val_M1,
      port0_type  = s.data_array_type_M1,
      port0_idx   = s.data_array_idx_M1,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.data_array_wben_M1,
      port0_rdata = s.data_array_rdata_M2,
    )
  
    #----------------------------------------------------------------
    # M2 Stage 
    #----------------------------------------------------------------
    # Pipeline registers
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

    s.read_word_mux_M2 = Mux(BitsData, clw//dbw+1)\
    (
      sel = s.read_word_mux_sel_M2,
      out = s.cacheresp_data_M2,
    )
    s.read_word_mux_M2.in_[0] //= BitsData(0) 
    for i in range(1, clw//dbw+1):
      s.read_word_mux_M2.in_[i] //= s.read_data_M2[(i-1)*dbw:i*dbw]

    s.cacheresp_type_M2       //= s.cachereq_type_M2
    s.offset_M2               //= s.cachereq_addr_M2[0:ofw]
    s.memreq_opaque_M2        //= s.cacheresp_opaque_M2
    s.memreq_addr_M2[ofw:abw] //= s.cachereq_addr_M2[ofw:abw]
    s.memreq_data_M2          //= s.read_data_M2

  def line_trace( s ):
    # msg = f"data v:{s.data_array_val_M1}; id:{s.data_array_idx_M1}"
    # msg += f" wben:{s.data_array_wben_M1}"
    # msg += f" data out:{s.data_array_rdata_M2}"
    msg = ""
    # msg += f"Didx:{s.data_array_idx_M1}"
    # msg += f"[{s.tag_array_rdata_M1[0]}][{s.tag_array_rdata_M1[1]}]"
    # msg+= f" {s.read_data_M2}"
    return msg
