"""
#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================
Datapath of Pipelined Blocking Cache

Author : Xiaoyu Yan, Eric Tang
Date   : 11/04/19
"""
from pymtl3            import *
from pymtl3.stdlib.rtl.registers import RegEnRst
from pymtl3.stdlib.rtl.RegisterFile import RegisterFile
from pymtl3.stdlib.rtl.arithmetics import Mux
from sram.SramPRTL     import SramPRTL
from BlockingCache.utils import EComp

class BlockingCacheDpathPRTL (Component):
  def construct(s, 
                abw = 32,		 # Address bitwidth
                dbw = 32,		 # Data bitwidth
                clw = 128,   # Cacheline bitwidth
                idw = 5,     # Index bitwidth
                ofw = 4,     # Offset bitwidth
                tgw = 19,    # Tag bitwidth
                nbl = 512,   # Number of blocks
                BitsAddr  = "inv",  # address bitstruct
                BitsOpaque  = "inv",  # opaque bitstruct
                BitsType  = "inv",  # type bitstruct
                BitsData  = "inv",  # data bitstruct
                BitsCacheline  = "inv",  # cacheline bitstruct
                BitsIdx  = "inv",  # index bitstruct
                BitsTag  = "inv",  # tag bitstruct
                BitsOffset  = "inv",  # offset bitstruct
                BitsTagWben = "inv",  # Tag array write byte enable
                BitsDataWben = "inv",  # Data array write byte enable
                BitsRdDataMux = "inv",  # Read data mux M2 
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
    s.memresp_data_Y      = InPort(BitsCacheline)
    # Cache -> Proc
    s.cacheresp_opaque_M2 = OutPort(BitsOpaque)
    s.cacheresp_type_M2   = OutPort(BitsType) 
    s.cacheresp_data_M2	  = OutPort(BitsData)	
    # Cache -> Mem 
    # s.memreq_type_M2      = OutPort(BitsType)
    s.memreq_opaque_M2    = OutPort(BitsOpaque)
    s.memreq_addr_M2      = OutPort(BitsAddr)
    s.memreq_data_M2      = OutPort(BitsCacheline)

    #-------------------------------------------------------------------
    # Control Signals (ctrl -> dpath)
    #-------------------------------------------------------------------

    # M0 Signals
    s.tag_array_val_M0      = InPort(Bits1)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(BitsTagWben)
    s.ctrl_bit_val_wr_M0    = InPort(Bits1)
    s.reg_en_M0             = InPort(Bits1)
    s.memresp_mux_sel_M0    = InPort(Bits1)

    # M1 Signals
    s.reg_en_M1             = InPort(Bits1)
    s.data_array_val_M1     = InPort(Bits1)
    s.data_array_type_M1    = InPort(Bits1)
    s.data_array_wben_M1    = InPort(BitsDataWben)
    # s.ctrl_bit_dty_wr_M1    = InPort(Bits1)
    # s.ctrl_bit_dty_rd_M1    = OutPort(Bits1)
    s.ctrl_bit_val_rd_M1    = OutPort(Bits1)
    s.tag_match_M1          = OutPort(Bits1)
    s.cachereq_type_M1      = OutPort(BitsType)
    s.offset_M1             = OutPort(BitsOffset)

    # MSHR Signals
    s.reg_en_MSHR           = InPort(Bits1)

    # M2 Signals
    s.reg_en_M2             = InPort(Bits1)
    s.read_data_mux_sel_M2  = InPort(Bits1)
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

    # Duplicator
    s.rep_out_M0 = Wire(BitsCacheline)
    # @s.update
    # def Replicator():
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

    s.addr_mux_M0 = Mux(BitsAddr, 2)\
    (
      in_ = {0: s.cachereq_addr_M0,
             1: s.MSHR_addr_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.addr_M0,
    )

    s.write_data_mux_M0 = Mux(BitsCacheline, 2)\
    (
      in_ = {0: s.rep_out_M0,
             1: s.memresp_data_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.data_array_wdata_M0,
    )

    # Tag Array
    s.tag_array_idx_M0      = Wire(BitsIdx)
    s.tag_array_wdata_M0    = Wire(BitsAddr)
    s.tag_array_rdata_M1    = Wire(BitsAddr)

    s.tag_array_idx_M0              //= s.addr_M0[ofw:idw+ofw]
    s.tag_array_wdata_M0[0:tgw]     //= s.addr_M0[ofw+idw:idw+ofw+tgw]
    s.tag_array_wdata_M0[abw-1:abw] //= s.ctrl_bit_val_wr_M0

    s.tag_array_M1 = SramPRTL(abw, nbl)(
      port0_val   = s.tag_array_val_M0,
      port0_type  = s.tag_array_type_M0,
      port0_idx   = s.tag_array_idx_M0,
      port0_wdata = s.tag_array_wdata_M0,
      port0_wben  = s.tag_array_wben_M0,
      port0_rdata = s.tag_array_rdata_M1,
    )

    #--------------------------------------------------------------------
    # M1 Stage 
    #--------------------------------------------------------------------
    
    # s.RegFile_M1 = RegisterFile(Bits1,nbl)(
    #   raddr = s.tag_array_idx_M0,
    #   rdata = s.ctrl_bit_dty_rd_M1,
    #   waddr = s.tag_array_idx_M0,
    #   wdata = s.ctrl_bit_dty_wr_M1,
    #   wen   = b1(1)
    # )

    s.cachereq_opaque_M1  = Wire(BitsOpaque)
    s.cachereq_addr_M1    = Wire(BitsAddr)
    s.cachereq_data_M1    = Wire(BitsCacheline)
    
    # Pipeline registers
    s.cachereq_opaque_reg_M1 = RegEnRst(BitsOpaque)(
      en  = s.reg_en_M1,
      in_ = s.opaque_M0,
      out = s.cachereq_opaque_M1,
    )
    s.cachereq_type_reg_M1 = RegEnRst(BitsType)(
      en  = s.reg_en_M1,
      in_ = s.type_M0,
      out = s.cachereq_type_M1,
    )
    s.cachereq_address_reg_M1 = RegEnRst(BitsAddr)(
      en  = s.reg_en_M1,
      in_ = s.addr_M0,
      out = s.cachereq_addr_M1,
    )
    s.cachereq_data_reg_M1 = RegEnRst(BitsCacheline)(
      en  = s.reg_en_M1,
      in_ = s.data_array_wdata_M0,
      out = s.cachereq_data_M1,
    )

    # Output the valid bit
    s.ctrl_bit_val_rd_M1 //= s.tag_array_rdata_M1[abw-1:abw] 
    s.offset_M1 //= s.cachereq_addr_M1[2:ofw]

    # s.comp_in1 = Wire(BitsTag)
    # s.comp_in2 = Wire(BitsTag)
    # s.comp_in1 //= s.tag_array_rdata_M1[0:tgw]
    # s.comp_in2 //= s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw]
    # @s.update
    # def Comparator():
    #   s.tag_match_M1 = s.comp_in1 == s.comp_in2
    # Comparator
    s.Comparator = EComp(BitsTag)(
      in0 = s.tag_array_rdata_M1[0:tgw],
      in1 = s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw],
      out = s.tag_match_M1
    )

    # 1 Entry MSHR
    s.MSHR_type = RegEnRst(BitsType)(
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_type_M1,
      out = s.MSHR_type_M0,
    )
    s.MSHR_addr = RegEnRst(BitsAddr)(
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_addr_M1,
      out = s.MSHR_addr_M0,
    )

    # Data Array ( Btwn M1 and M2 )
    s.data_array_idx_M1   = Wire(BitsIdx)
    s.data_array_wdata_M1 = Wire(BitsCacheline)
    s.data_array_rdata_M2 = Wire(BitsCacheline)
    s.data_array_wdata_M1 //= s.cachereq_data_M1
    s.data_array_idx_M1   //= s.cachereq_addr_M1[ofw:idw+ofw]
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
    s.cachereq_opaque_reg_M2 = RegEnRst(BitsOpaque)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_opaque_M1,
      out = s.cacheresp_opaque_M2,
    )
    
    s.cachereq_type_reg_M2 = RegEnRst(BitsType)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_type_M1,
      out = s.cachereq_type_M2,
    )

    s.cachereq_addr_M2    = Wire(BitsAddr)
    s.cachereq_address_reg_M2 = RegEnRst(BitsAddr)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_addr_M1,
      out = s.cachereq_addr_M2,
    )

    s.cachereq_data_M2      = Wire(BitsCacheline)
    s.cachereq_data_reg_M2  = RegEnRst(BitsCacheline)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_data_M1,
      out = s.cachereq_data_M2,
    )

    s.read_data_M2          = Wire(BitsCacheline)
    s.read_data_mux_M2 = Mux(BitsCacheline, 2)(
      in_ = {0: s.data_array_rdata_M2,
             1: s.cachereq_data_M2},
      sel = s.read_data_mux_sel_M2,
      out = s.read_data_M2,
    )

    s.read_word_mux_M2 = Mux(BitsData, clw//dbw+1)(
      # in_ = {0: db(0),
      #       #  1: s.read_data_M2[0    :   dbw],
      #       #  2: s.read_data_M2[1*dbw: 2*dbw],
      #       #  3: s.read_data_M2[2*dbw: 3*dbw],
      #       #  4: s.read_data_M2[3*dbw: 4*dbw]
      #        },
      sel = s.read_word_mux_sel_M2,
      out = s.cacheresp_data_M2,
    )
    # @s.update
    # def dynamic_mux_connect():
    s.read_word_mux_M2.in_[0] //= BitsData(0) 
    for i in range(1, clw//dbw+1):
      s.read_word_mux_M2.in_[i] //= s.read_data_M2[(i-1)*dbw:i*dbw]

    s.cacheresp_type_M2     //= s.cachereq_type_M2

    s.offset_M2        //= s.cachereq_addr_M2[2:ofw]
    
    s.memreq_opaque_M2 //= s.cacheresp_opaque_M2
    s.memreq_addr_M2[ofw:abw]   //= s.cachereq_addr_M2[ofw:abw]
    # TODO fix this
    # s.memreq_addr_M2   //= s.cachereq_addr_M2
    s.memreq_data_M2   //= s.data_array_rdata_M2
    # s.memreq_type_M2   //= s.cachereq_type_M2 

      
  def line_trace( s ):
    # "mem resp:{}".format(s.memresp_data_Y)
    msg = ""
    
    # msg = (
    #   "TAG:T={}|A={}|wben={}  DATA:D={}|R={}|wben={} ".format(\
    #   s.tag_array_rdata_M1,
    #   s.cachereq_addr_M1,
    #   s.tag_array_wben_M0,
    #   s.data_array_rdata_M2,
    #   s.cacheresp_data_M2,
    #   s.data_array_wben_M1,
    #   # s.MSHR_addr_M0,
    #   # s.memresp_data_Y
    #   )
    # )
    return msg
    # return "tag_array_rdata = {}, cachereq_addr = {} ".format(\
    #   s.tag_array_rdata_M1[0:tgw],s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw])
    # return "t->{} ".format(s.tag_array_M1.line_trace())
    # return "{} {}".format(s.tag_array_M1.line_trace(),
    # s.data_array_M2.line_trace())
