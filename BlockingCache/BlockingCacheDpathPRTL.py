#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3            import *
from pymtl3.stdlib.rtl import RegEnRst
from sram.SramPRTL     import SramPRTL

class BlockingCacheDpathPRTL (Component):
  def construct(s, 
                size = 8192, # Cache size in bytes
                clw  = 128,  # Cacheline bitwidth
                way  = 1     # Associativity
  ):
    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------
    obw = 8			            # Opaque bitwidth
    abw = 32		            # Address bitwidth
    dbw = 32		            # Data bitwidth
    nbl = size*8//clw       # Number of Cache Blocks
    idw = clog2(nbl)        # Index bitwidth
    ofw = clog2(clw//8)     # Offset bitwidth
    tgw = abw - ofw - idw   # Tag bitwidth

		#---------------------------------------------------------------------
		# Interface
		#--------------------------------------------------------------------- 
		# Proc -> Cache
    s.cachereq_opaque  = InPort(mk_bits(obw))
    s.cachereq_type    = InPort(mk_bits(3))
    s.cachereq_addr    = InPort(mk_bits(abw))
    s.cachereq_data    = InPort(mk_bits(dbw))
		# Mem -> Cache
    s.memresp_opaque   = InPort(mk_bits(obw))
    s.memresp_data     = InPort(mk_bits(clw))
    # Cache -> Proc
    s.cacheresp_opaque = OutPort(mk_bits(obw))
    s.cacheresp_type   = OutPort(mkbits(3)) 
    s.cacheresp_data	 = OutPort(mkbits(dbw))	
    # Cache -> Mem
    s.memreq_opaque    = OutPort(mk_bits(obw))
    s.memreq_addr      = OutPort(mk_bits(abw))
    s.memreq_data			 = OutPort(mk_bits(clw))
    # Control Signals (ctrl -> dpath)
    s.reg_en_M0             = InPort(Bits1)
    s.write_data_mux_sel_M0 = InPort(Bits1)
    s.tag_array_val_M0      = InPort(Bits1)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(Bits3)
    s.data_array_val_M0     = InPort(Bits1)
    s.data_array_type_M0    = InPort(Bits1)
    s.data_array_wben_M0    = InPort(Bits3)

    s.reg_en_M1             = InPort(Bits1)
    s.tag_match_M1          = InPort(Bits1)
    s.read_data_mux_sel     = InPort(Bits1)
    s.read_word_mux_sel     = InPort(Bits3)
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    # Wires
    s.cachereq_opaque_M0  = Wire(mk_bits(obw))
    s.cachereq_type_M0    = Wire(mk_bits(3))
    s.cachereq_addr_M0    = Wire(mk_bits(abw))
    s.cachereq_data_M0    = Wire(mk_bits(dbw))
    s.memresp_opaque_M0   = Wire(mk_bits(obw))
    s.memresp_data_M0     = Wire(mk_bits(dbw))

    s.tag_array_idx_M0    = Wire(mk_bits(idw))
    s.tag_array_wdata_M0  = Wire(mk_bits(tgw))
    s.tag_array_rdata_M1  = Wire(mk_bits(tgw))

    s.data_array_idx_M0   = Wire(mk_bits(idw))
    s.data_array_wdata_M0 = Wire(mk_bits(dbw))
    s.data_array_rdata_M1 = Wire(mk_bits(dbw))
    
    # Connect wires
    s.tag_array_idx_M0    //= s.cachereq_address[mk_bits(idw+ofw):ofw]
    s.tag_array_wdata_M0  //= s.cachereq_address[tgw+idw+ofw:idw+ofw]
    s.data_array_idx_M0   //= s.cachereq_address[mk_bits(idw+ofw):ofw]
    s.data_array_wdata_M0 //= s.cachereq_address[tgw+idw+ofw:idw+ofw]

    s.cachereq_opaque_reg_M0 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_opaque,
      out = s.cachereq_type_M0,
    )

    s.cachereq_type_reg_M0 = RegEnRst(mk_bits(3))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_type,
      out = s.cachereq_type_M0,
    )
    
    s.cachereq_address_reg_M0 = RegEnRst(mk_bits(abw))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_addr,
      out = s.cachereq_addr_M0,
    )

    s.cachereq_data_reg_M0 = RegEnRst(mk_bits(dbw))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_data,
      out = cachereq_data_M0,
    )

    s.memresp_opaque_reg_M0 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M0,
      in_ = s.memresp_opaque,
      out = s.memresp_opaque_M0,
    )

    s.memresp_data_reg_M0 = RegEnRst(mk_bits(clw))(
      en  = s.reg_en_M0,
      in_ = s.memresp_data,
      out = s.memresp_data_M0,
    )

    s.tag_array = SramPRTL(tgw, nbl)(
      port0_val  = s.tag_array_val_M0,
      port0_type = s.tag_array_type_M0,
      port0_idx  = s.tag_array_idx_M0,
      port0_wdata = s.tag_array_wdata_M0,
      port0_wben  = s.tag_array_wben_M0,
      port0_rdata = s.tag_array_rdata_M1,
    )

    s.write_data_mux_M0 = Mux(Bits128, 2)(
      in_ = {0: s.cachereq_data,
             1: s.memresp_data},
      sel = s.write_data_mux_sel_M0,
      out = s.data_array_wdata_M0,
    )

    #-----------------------------------------------------
    # M1 Stage 
    #-----------------------------------------------------
    s.cachereq_opaque_reg_M1 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M1,
      in_ = s.cachereq_opaque_M0,
      out = s.cachereq_opaque_M1
    )

    s.cachereq_type_reg_M1 = RegEnRst(mk_bits(3))(
      en  = s.reg_en_M1,
      in_ = ,
      out = ,
    )
    
    s.cachereq_address_reg_M1 = RegEnRst(mk_bits(abw))(
      en  = s.reg_en_M1,
      in_ = ,
      out = ,
    )

    s.cachereq_data_reg_M1 = RegEnRst(mk_bits(dbw))(
      en  = s.reg_en_M1,
      in_ = ,
      out = ,
    )
  
    s.data_array = SramPRTL(tgw, nbl)(
      port0_val   = s.data_array_val_M0,
      port0_type  = s.data_array_type_M0,
      port0_idx   = s.data_array_idx_M0,
      port0_wdata = s.data_array_wdata_M0,
      port0_wben  = s.data_array_wben_M0,
      port0_rdata = s.data_array_rdata_M1,
    )

    s.cachereq_opaque_M1 //= s.cacheresp_opaque


  def line_trace( s ):
    return ""
