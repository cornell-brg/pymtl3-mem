#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3            import *
from pymtl3.stdlib.rtl.registers import RegEnRst
from pymtl3.stdlib.rtl.arithmetics import Mux
from sram.SramPRTL     import SramPRTL

class BlockingCacheDpathPRTL (Component):
  def construct(s, 
                abw = 32,		 # Address bitwidth
                dbw = 32,		 # Data bitwidth
                clw = 128,   # Cacheline bitwidth
                idw = 5,     # Index bitwidth
                ofw = 4,     # Offset bitwidth
                tgw = 19,    # Tag bitwidth
                nbl = 512,   # Number of blocks
                ab  = "inv",  # address bitstruct
                ob  = "inv",  # opaque bitstruct
                ty  = "inv",  # type bitstruct
                db  = "inv",  # data bitstruct
                cl  = "inv",  # cacheline bitstruct
                ix  = "inv",  # index bitstruct
                tg  = "inv",  # tag bitstruct
                of  = "inv",  # offset bitstruct
                twb = "inv",  # Tag array write byte enable
                dwb = "inv",  # Data array write byte enable
                mx2 = "inv",  # Read data mux M2 
  ):
	
  	#---------------------------------------------------------------------
		# Interface
		#--------------------------------------------------------------------- 
		
    # Proc -> Cache
    s.cachereq_opaque_M0  = InPort(ob)
    s.cachereq_type_M0    = InPort(ty)
    s.cachereq_addr_M0    = InPort(ab)
    s.cachereq_data_M0    = InPort(db)
		# Mem -> Cache
    s.memresp_opaque_Y   = InPort(ob)
    s.memresp_data_Y     = InPort(cl)
    # Cache -> Proc
    s.cacheresp_opaque_M2   = OutPort(ob)
    s.cacheresp_type_M2     = OutPort(ty) 
    s.cacheresp_data_M2	   = OutPort(db)	
    # Cache -> Mem  
    s.memreq_opaque_M2      = OutPort(ob)
    s.memreq_addr_M2        = OutPort(ab)
    s.memreq_data_M2			   = OutPort(cl)

    #-------------------------------------------------------------------
    # Control Signals (ctrl -> dpath)
    #-------------------------------------------------------------------

    # M0 Signals
    s.tag_array_val_M0       = InPort(Bits1)
    s.tag_array_type_M0      = InPort(Bits1)
    s.tag_array_wben_M0      = InPort(twb)
    s.ctrl_bit_val_wr_M0     = InPort(Bits1)
    s.reg_en_M0             = InPort(Bits1)
    s.memresp_mux_sel_M0  = InPort(Bits1)

    # M1 Signals
    s.reg_en_M1             = InPort(Bits1)
    s.data_array_val_M1     = InPort(Bits1)
    s.data_array_type_M1    = InPort(Bits1)
    s.data_array_wben_M1    = InPort(dwb)
    s.ctrl_bit_val_rd_M1    = OutPort(Bits1)
    s.tag_match_M1          = OutPort(Bits1)
    s.cachereq_type_M1      = OutPort(ty)
    s.offset_M1             = OutPort(of)

    # MSHR Signals
    s.reg_en_MSHR           = InPort(Bits1)

    # M2 Signals
    s.reg_en_M2             = InPort(Bits1)
    s.read_data_mux_sel_M2  = InPort(Bits1)
    s.read_word_mux_sel_M2  = InPort(mx2)
    s.cachereq_type_M2      = OutPort(ty)
    s.offset_M2             = OutPort(of)

    #--------------------------------------------------------------------
    # Y  Stage
    #--------------------------------------------------------------------
    
    # Duplicator
    s.rep_out_M0 = Wire(cl)
    @s.update
    def Replicator():
      for i in range(0,clw,dbw):
        s.rep_out_M0[i:i+dbw] = s.cachereq_data_M0

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
   
    s.memresp_data_M0     = Wire(cl)
    s.memresp_opaque_M0   = Wire(ob)
    s.opaque_M0         = Wire(ob)
    s.data_array_wdata_M0 = Wire(cl)
    s.MSHR_type_M0        = Wire(ty)
    s.type_M0           = Wire(ty)
    s.MSHR_addr_M0        = Wire(ab)
    s.addr_M0           = Wire(ab)
    
    # Pipeline Registers
    s.memresp_data_reg_M0 = RegEnRst(cl)\
    (
      en  = s.reg_en_M0,
      in_ = s.memresp_data_Y,
      out = s.memresp_data_M0,
    )

    s.memresp_opaque_reg_M0 = RegEnRst(ob)\
    (
      en  = s.reg_en_M0,
      in_ = s.memresp_opaque_Y,
      out = s.memresp_opaque_M0,
    )

    # Cachereq or Memresp select muxes
    s.opaque_mux_M0 = Mux(ob, 2)\
    (
      in_ = {0: s.cachereq_opaque_M0,
             1: s.memresp_opaque_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.opaque_M0,
    )

    s.type_mux_M0 = Mux(ty, 2)\
    (
      in_ = {0: s.cachereq_type_M0,
             1: s.MSHR_type_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.type_M0,
    )

    s.addr_mux_M0 = Mux(ab, 2)\
    (
      in_ = {0: s.cachereq_addr_M0,
             1: s.MSHR_addr_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.addr_M0,
    )

    s.write_data_mux_M0 = Mux(cl, 2)\
    (
      in_ = {0: s.rep_out_M0,
             1: s.memresp_data_M0},
      sel = s.memresp_mux_sel_M0,
      out = s.data_array_wdata_M0,
    )

    # Tag Array
    s.tag_array_idx_M0      = Wire(ix)
    s.tag_array_wdata_M0    = Wire(ab)
    s.tag_array_rdata_M1    = Wire(ab)

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
    
    s.cachereq_opaque_M1  = Wire(ob)
    s.cachereq_addr_M1    = Wire(ab)
    s.cachereq_data_M1    = Wire(cl)
    
    # Pipeline registers
    s.cachereq_opaque_reg_M1 = RegEnRst(ob)(
      en  = s.reg_en_M1,
      in_ = s.opaque_M0,
      out = s.cachereq_opaque_M1,
    )
    s.cachereq_type_reg_M1 = RegEnRst(ty)(
      en  = s.reg_en_M1,
      in_ = s.type_M0,
      out = s.cachereq_type_M1,
    )
    s.cachereq_address_reg_M1 = RegEnRst(ab)(
      en  = s.reg_en_M1,
      in_ = s.addr_M0,
      out = s.cachereq_addr_M1,
    )
    s.cachereq_data_reg_M1 = RegEnRst(cl)(
      en  = s.reg_en_M1,
      in_ = s.data_array_wdata_M0,
      out = s.cachereq_data_M1,
    )

    # Output the valid bit
    s.ctrl_bit_val_rd_M1 //= s.tag_array_rdata_M1[abw-1:abw] 
    s.offset_M1 //= s.cachereq_addr_M1[2:ofw]
      
    # Comparator
    @s.update
    def Comparator():
      s.tag_match_M1 = s.tag_array_rdata_M1[0:tgw] == s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw]

    # 1 Entry MSHR
    s.MSHR_type = RegEnRst(ty)(
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_type_M1,
      out = s.MSHR_type_M0,
    )
    s.MSHR_addr = RegEnRst(ab)(
      en  = s.reg_en_MSHR,
      in_ = s.cachereq_addr_M1,
      out = s.MSHR_addr_M0,
    )

    # Data Array ( Btwn M1 and M2 )
    s.data_array_idx_M1   = Wire(ix)
    s.data_array_wdata_M1 = Wire(cl)
    s.data_array_rdata_M2 = Wire(cl)
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
    s.cachereq_opaque_M2  = Wire(ob)
    s.cachereq_opaque_reg_M2 = RegEnRst(ob)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_opaque_M1,
      out = s.cacheresp_opaque_M2,
    )
    
    s.cachereq_type_reg_M2 = RegEnRst(ty)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_type_M1,
      out = s.cachereq_type_M2,
    )

    s.cachereq_addr_M2    = Wire(ab)
    s.cachereq_address_reg_M2 = RegEnRst(ab)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_addr_M1,
      out = s.cachereq_addr_M2,
    )

    s.cachereq_data_M2      = Wire(cl)
    s.cachereq_data_reg_M2  = RegEnRst(cl)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_data_M1,
      out = s.cachereq_data_M2,
    )

    s.read_data_M2          = Wire(cl)
    s.read_data_mux_M2 = Mux(cl, 2)(
      in_ = {0: s.data_array_rdata_M2,
             1: s.cachereq_data_M2},
      sel = s.read_data_mux_sel_M2,
      out = s.read_data_M2,
    )

    s.read_word_mux_M2 = Mux(db, clw//dbw+1)(
      # in_ = {0: db(0),
      #       #  1: s.read_data_M2[0    :   dbw],
      #       #  2: s.read_data_M2[1*dbw: 2*dbw],
      #       #  3: s.read_data_M2[2*dbw: 3*dbw],
      #       #  4: s.read_data_M2[3*dbw: 4*dbw]
      #        },
      sel = s.read_word_mux_sel_M2,
      out = s.cacheresp_data_M2,
    )
    @s.update
    def dynamic_mux_connect():
      s.read_word_mux_M2.in_[0] = db(0) 
      for i in range(1, clw//dbw+1):
        s.read_word_mux_M2.in_[i] = s.read_data_M2[(i-1)*dbw:i*dbw]


    s.cacheresp_type_M2     //= s.cachereq_type_M2

    s.offset_M2     //= s.cachereq_addr_M2[2:ofw]
    s.memreq_opaque_M2 //= s.cacheresp_opaque_M2
    s.memreq_addr_M2   //= s.cachereq_addr_M2
    s.memreq_data_M2   //= s.data_array_rdata_M2
      
      
  def line_trace( s ):
    return (
      "TAG:T={}|A={}  DATA:D={}|R={}".format(\
      s.tag_array_rdata_M1,
      s.cachereq_addr_M1,
      s.data_array_rdata_M2,
      s.cacheresp_data_M2
      )
    )
    # return "tag_array_rdata = {}, cachereq_addr = {} ".format(\
    #   s.tag_array_rdata_M1[0:tgw],s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw])
    # return "t->{} ".format(s.tag_array_M1.line_trace())
    # return "{} {}".format(s.tag_array_M1.line_trace(),
    # s.data_array_M2.line_trace())
