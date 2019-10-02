#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3            import *
from pymtl3.stdlib.rtl import RegEnRst

#-------------------------------------------------------------------------
# Bitwidths
#-------------------------------------------------------------------------
obw = 8			# Opaque bitwidth
abw = 32		# Address bitwidth
dbw = 32		# Data bitwidth
clw = 128		# Cacheline bitwidth

class BlockingCacheDpathPRTL (Component):
  def construct(s): 
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


  def line_trace( s ):
    return ""
