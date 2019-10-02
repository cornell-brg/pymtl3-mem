#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3            import *
from pymtl3.stdlib.rtl import RegEnRst
from sram.SramPRTL     import SramPRTL

#-------------------------------------------------------------------------
# Bitwidths
#-------------------------------------------------------------------------
obw = 8			# Opaque bitwidth
abw = 32		# Address bitwidth
dbw = 32		# Data bitwidth

class BlockingCacheDpathPRTL (Component):
  def construct(s, 
                size = 8192, # Cache size in bytes
                clw  = 128, # Cacheline bitwidth
                way  = 1, # associativity

                mem_req_type = "inv",
                mem_resp_type = "inv",
                cache_req_type = "inv",
                cache_resp_type = "inv",
  ):
    nbl = size*8//clw # Short name for number of cache blocks, 8192*8/128 = 512
    idw = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw = clog2(clw//8)   # Short name for offset bit width, clog2(128/8) = 4
    tgw = abw - ofw - idw 
		#---------------------------------------------------------------------
		# Interface
		#--------------------------------------------------------------------- 
		# Cache Request Ports
    s.cachereq_opaque  = InPort(mk_bits(obw))
    s.cachereq_type    = InPort(mk_bits(3))
    s.cachereq_address = InPort(mk_bits(abw))
		s.cachereq_data    = InPort(mk_bits(dbw))
		# Memory Response Ports
		s.memresp_opaque   = InPort(mk_bits(obw))
		s.memresp_data     = InPort(mk_bits(clw))

		# Cache Response Ports
		s.cacheresp_opaque = OutPort(mk_bits(obw))
		s.cacheresp_type   = OutPort(mkbits(3)) 
		s.cacheresp_data	 = OutPort(mkbits(dbw))	
		
    # Memory Request Ports
		s.memreq_opaque    = OutPort(mk_bits(obw))
		s.memreq_addr      = OutPort(mk_bits(abw))
		s.memreq_data			 = OutPort(mk_bits(clw))

    # M0 Ctrl Signals
    # Tag Array
    s.tag_array_val_M0 = InPort(Bits1)
    s.tag_array_type_M0 = InPort(Bits1)
    s.tag_array_wben_M0 = InPort(Bits3)

		#--------------------------------------------------------------------
		# M0 Stage
		#--------------------------------------------------------------------
		s.cachereq_opaque_reg_M0 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_opaque,
      out = ,
    )

		s.cachereq_type_reg_M0 = RegEnRst(mk_bits(3))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_type,
      out = ,
    )
		
		s.cachereq_address_reg_M0 = RegEnRst(mk_bits(abw))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_address,
      out = ,
    )

		s.cachereq_data_reg_M0 = RegEnRst(mk_bits(dbw))(
      en  = s.reg_en_M0,
      in_ = s.cachereq_data,
      out = ,
    )

		s.memresp_opaque_reg_M0 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M0,
      in_ = s.memresp_opaque,
      out = ,
    )

		s.memresp_data_reg_M0 = RegEnRst(mk_bits(clw))(
      en  = s.reg_en_M0,
      in_ = s.memresp_data,
      out = ,
    )

		#-----------------------------------------------------
		# M1 Stage 
		#-----------------------------------------------------
		s.cachereq_opaque_reg_M1 = RegEnRst(mk_bits(obw))(
      en  = s.reg_en_M1,
      in_ = ,
      out = ,
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

    # Tag Array:
    s.tag_array_idx_M0   = Wire(mk_bits(idw))
    s.tag_array_wdata_M0 = Wire(mk_bits(tgw))
    s.tag_array_rdata_M1 = Wire(mk_bits(tgw))
    s.tag_array = SramPRTL(tgw, nbl)(
      port0_val  = s.tag_array_val_M0,
      port0_type = s.tag_array_type_M0,
      port0_idx  = s.tag_array_idx_M0,
      port0_wdata = s.tag_array_wdata_M0,
      port0_wben  = s.tag_array_wben_M0,
      port0_rdata = s.tag_array_rdata_M1,
    )
    s.tag_array_idx_M0   //= s.cachereq_msg.data[mk_bits(idw+ofw):ofw]
    s.tag_array_wdata_M0 //= s.cachereq_msg.data[tgw+idw+ofw:idw+ofw]




  def line_trace( s ):
    return ""
