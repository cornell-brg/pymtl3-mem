#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3            import *
from pymtl3.stdlib.rtl.registers import RegEnRst
from pymtl3.stdlib.rtl.arithmetics import Mux
from sram.SramPRTL     import SramPRTL

class BlockingCacheDpathPRTL (Component):
  def construct(s, 
                obw = 8,			            # Opaque bitwidth
                abw = 32,		            # Address bitwidth
                dbw = 32,		            # Data bitwidth
                size = 8192, # Cache size in bytes
                clw  = 128,  # Cacheline bitwidth
                way  = 1     # Associativity
  ):
    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------

    nbl = size*8//clw       # Number of Cache Blocks
    idw = clog2(nbl)        # Index bitwidth
    ofw = clog2(clw//8)     # Offset bitwidth
    tgw = abw - ofw - idw   # Tag bitwidth

		#---------------------------------------------------------------------
		# Interface
		#--------------------------------------------------------------------- 
		# Proc -> Cache
    s.cachereq_opaque  = InPort(mk_bits(obw))
    s.cachereq_type    = InPort(mk_bits(4))
    s.cachereq_addr    = InPort(mk_bits(abw))
    s.cachereq_data    = InPort(mk_bits(dbw))
		# Mem -> Cache
    s.memresp_opaque   = InPort(mk_bits(obw))
    s.memresp_data     = InPort(mk_bits(clw))
    # Cache -> Proc
    s.cacheresp_opaque = OutPort(mk_bits(obw))
    s.cacheresp_type   = OutPort(mk_bits(4)) 
    s.cacheresp_data	 = OutPort(mk_bits(dbw))	
    # Cache -> Mem
    s.memreq_opaque    = OutPort(mk_bits(obw))
    s.memreq_addr      = OutPort(mk_bits(abw))
    s.memreq_data			 = OutPort(mk_bits(clw))

    # Control Signals (ctrl -> dpath)
    # M0 Signals
    # s.reg_en_M0             = InPort(Bits1)
    s.write_data_mux_sel_M0 = InPort(Bits1)
    s.tag_array_val_M0      = InPort(Bits1)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(Bits4)
    # M1 
    s.reg_en_M1             = InPort(Bits1)
    s.data_array_val_M1     = InPort(Bits1)
    s.data_array_type_M1    = InPort(Bits1)
    s.data_array_wben_M1    = InPort(Bits16)
    s.tag_match_M1          = OutPort(Bits1)
    # M2
    s.reg_en_M2             = InPort(Bits1)
    # s.read_data_mux_sel_M2  = InPort(Bits1)
    s.read_word_mux_sel_M2  = InPort(Bits3)
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    # Tag Array
    # s.memresp_data_M0     = Wire(mk_bits(dbw))
    s.tag_array_idx_M0    = Wire(mk_bits(idw))
    s.tag_array_wdata_M0  = Wire(mk_bits(abw))
    s.tag_array_rdata_M1  = Wire(mk_bits(abw))

    s.tag_array_idx_M0    //= s.cachereq_addr[ofw:idw+ofw]
    s.tag_array_wdata_M0[0:tgw]  //= s.cachereq_addr[idw+ofw:tgw+idw+ofw]

    s.tag_array_M1 = SramPRTL(abw, nbl)(
      port0_val  = s.tag_array_val_M0,
      port0_type = s.tag_array_type_M0,
      port0_idx  = s.tag_array_idx_M0,
      port0_wdata = s.tag_array_wdata_M0,
      port0_wben  = s.tag_array_wben_M0,
      port0_rdata = s.tag_array_rdata_M1,
    )

    # s.write_data_mux_M0 = Mux(mk_bits(clw), 2)(
    #   in_ = {0: s.cachereq_data,
    #          1: s.memresp_data},
    #   sel = s.write_data_mux_sel_M0,
    #   out = s.data_array_wdata_M0,
    # )

    #-----------------------------------------------------
    # M1 Stage 
    #-----------------------------------------------------    
    # Pipeline registers
    s.cachereq_opaque_M1  = Wire(mk_bits(obw))
    s.cachereq_opaque_reg_M1 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M1,
      in_ = s.cachereq_opaque,
      out = s.cachereq_opaque_M1,
    )

    s.cachereq_type_M1    = Wire(mk_bits(4))
    s.cachereq_type_reg_M1 = RegEnRst(mk_bits(4))(
      en  = s.reg_en_M1,
      in_ = s.cachereq_type,
      out = s.cachereq_type_M1,
    )

    s.cachereq_addr_M1    = Wire(mk_bits(abw))
    s.cachereq_address_reg_M1 = RegEnRst(mk_bits(abw))(
      en  = s.reg_en_M1,
      in_ = s.cachereq_addr,
      out = s.cachereq_addr_M1,
    )

    s.cachereq_data_M1    = Wire(mk_bits(dbw))
    s.cachereq_data_reg_M1 = RegEnRst(mk_bits(dbw))(
      en  = s.reg_en_M1,
      in_ = s.cachereq_data,
      out = s.cachereq_data_M1,
    )

    # s.memresp_opaque_M0   = Wire(mk_bits(obw))
    # s.memresp_opaque_reg_M1 = RegEnRst(mk_bits(obw))(
    #   en  = s.reg_en_M1,
    #   in_ = s.memresp_opaque,
    #   out = s.memresp_opaque_M0,
    # )
    # s.memresp_data_reg_M1 = RegEnRst(mk_bits(clw))(
    #   en  = s.reg_en_M1,
    #   in_ = s.memresp_data,
    #   out = s.memresp_data_M0,
    # )

    # Comparator
    @s.update
    def Comparator():
      s.tag_match_M1 = s.tag_array_rdata_M1[0:tgw] == s.cachereq_addr_M1[idw+ofw:ofw+idw+tgw]

    # Duplicator
    s.rep_out_M1 = Wire(mk_bits(clw))
    @s.update
    def Replicator():
      s.rep_out_M1[0:dbw] = cachereq_data_M1
      s.rep_out_M1[1*dbw:2*dbw] = cachereq_data_M1
      s.rep_out_M1[2*dbw:3*dbw] = cachereq_data_M1
      s.rep_out_M1[3*dbw:4*dbw] = cachereq_data_M1

    # Data Array ( Btwn M1 and M2 )
    s.data_array_idx_M1   = Wire(mk_bits(idw))
    s.data_array_wdata_M1 = Wire(mk_bits(clw))
    s.data_array_rdata_M2 = Wire(mk_bits(clw))
    
    s.data_array_idx_M1   //= s.cachereq_addr_M1[ofw:idw+ofw]
    s.data_array_wdata_M1 //= s.rep_out_M1
    
    s.data_array_M1_M2 = SramPRTL(clw, nbl)(
      port0_val   = s.data_array_val_M1,
      port0_type  = s.data_array_type_M1,
      port0_idx   = s.data_array_idx_M1,
      port0_wdata = s.data_array_wdata_M1,
      port0_wben  = s.data_array_wben_M1,
      port0_rdata = s.data_array_rdata_M2,
    )

    #-----------------------------------------------------
    # M2 Stage 
    #-----------------------------------------------------
    # Pipeline registers
    s.cachereq_opaque_M2  = Wire(mk_bits(obw))
    s.cachereq_opaque_reg_M2 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M2,
      in_ = s.cachereq_opaque_M1,
      out = s.cacheresp_opaque,
    )
    s.cachereq_type_M2    = Wire(mk_bits(4))
    s.cachereq_type_reg_M2 = RegEnRst(mk_bits(4))(
      en  = s.reg_en_M2,
      in_ = s.cachereq_type_M1,
      out = s.cacheresp_type,
    )
    s.cachereq_addr_M2    = Wire(mk_bits(abw))
    s.cachereq_address_reg_M2 = RegEnRst(mk_bits(abw))(
      en  = s.reg_en_M2,
      in_ = s.cachereq_addr_M1,
      out = s.cachereq_addr_M2,
    )
    # s.cachereq_data_M2      = Wire(mk_bits(dbw))
    # s.cachereq_data_reg_M2  = RegEnRst(mk_bits(dbw))(
    #   en  = s.reg_en_M2,
    #   in_ = s.cachereq_data_M1,
    #   out = cachereq_data_M2,
    # )
    s.read_word_mux_M2 = Mux(mk_bits(dbw), 5)(
      in_ = {0: Bits32(0),
             1: s.data_array_rdata_M2[0    :   dbw],
             2: s.data_array_rdata_M2[1*dbw: 2*dbw],
             3: s.data_array_rdata_M2[2*dbw: 3*dbw],
             4: s.data_array_rdata_M2[3*dbw: 4*dbw]
             },
      sel = s.read_word_mux_sel_M2,
      out = s.cacheresp_data,
    )

    @s.update
    def tmp_comb_M2():   
      s.memreq_opaque = 0
      s.memreq_addr   = 0
      s.memreq_data   = 0
      
  def line_trace( s ):
    return ""
