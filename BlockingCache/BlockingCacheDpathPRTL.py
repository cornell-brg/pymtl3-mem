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

    #-------------------------------------------------------------------------
    # Dtypes
    #-------------------------------------------------------------------------
    ab = mk_bits(abw)
    ob = mk_bits(obw)
    ty = mk_bits(4)
    db = mk_bits(dbw)
    cl = mk_bits(clw)
    ix = mk_bits(idw)
    tg = mk_bits(tgw)
		#---------------------------------------------------------------------
		# Interface
		#--------------------------------------------------------------------- 
		# Proc -> Cache
    s.cachereq_opaque  = InPort(ob)
    s.cachereq_type    = InPort(ty)
    s.cachereq_addr    = InPort(ab)
    s.cachereq_data    = InPort(db)
		# Mem -> Cache
    s.memresp_opaque   = InPort(ob)
    s.memresp_data     = InPort(cl)
    # Cache -> Proc
    s.cacheresp_opaque = OutPort(ob)
    s.cacheresp_type   = OutPort(ty) 
    s.cacheresp_data	 = OutPort(db)	
    # Cache -> Mem
    s.memreq_opaque    = OutPort(ob)
    s.memreq_addr      = OutPort(ab)
    s.memreq_data			 = OutPort(cl)

    # Control Signals (ctrl -> dpath)
    #-----------------
    # M0 Signals
    #-----------------
    # s.reg_en_M0             = InPort(Bits1)
    s.write_data_mux_sel_M0 = InPort(Bits1)
    s.tag_array_val_M0      = InPort(Bits1)
    s.tag_array_type_M0     = InPort(Bits1)
    s.tag_array_wben_M0     = InPort(Bits4)
    #-----------------
    # M1 
    #-----------------
    s.reg_en_M1             = InPort(Bits1)
    s.data_array_val_M1     = InPort(Bits1)
    s.data_array_type_M1    = InPort(Bits1)
    s.data_array_wben_M1    = InPort(Bits16)
    s.tag_match_M1          = OutPort(Bits1)
    #-----------------
    # M2
    #-----------------
    s.reg_en_M2             = InPort(Bits1)
    # s.read_data_mux_sel_M2  = InPort(Bits1)
    s.read_word_mux_sel_M2  = InPort(mk_bits(clog2(5)))
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    # Tag Array
    # s.memresp_data_M0     = Wire(mk_bits(dbw))
    s.tag_array_idx_M0    = Wire(ix)
    s.tag_array_wdata_M0  = Wire(ab)
    s.tag_array_rdata_M1  = Wire(ab)
    @s.update
    def tag_array_M1_connect():
      s.tag_array_idx_M0   = ab(s.cachereq_addr)[ofw:idw+ofw]
      #   print("-->{}".format(type(s.cachereq_addr)))
      s.tag_array_wdata_M0[0:tgw] = ab(s.cachereq_addr)[ofw+idw:idw+ofw+tgw]


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
    s.cachereq_opaque_M1  = Wire(ob)
    s.cachereq_opaque_reg_M1 = RegEnRst(ob)(
      en  = s.reg_en_M1,
      in_ = s.cachereq_opaque,
      out = s.cachereq_opaque_M1,
    )

    s.cachereq_type_M1    = Wire(ty)
    s.cachereq_type_reg_M1 = RegEnRst(ty)(
      en  = s.reg_en_M1,
      in_ = s.cachereq_type,
      out = s.cachereq_type_M1,
    )

    s.cachereq_addr_M1    = Wire(ab)
    s.cachereq_address_reg_M1 = RegEnRst(ab)(
      en  = s.reg_en_M1,
      in_ = s.cachereq_addr,
      out = s.cachereq_addr_M1,
    )

    s.cachereq_data_M1    = Wire(db)
    s.cachereq_data_reg_M1 = RegEnRst(db)(
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
      s.tag_match_M1 = ab(s.tag_array_rdata_M1[0:tgw]) \
      == ab(s.cachereq_addr_M1)[idw+ofw:ofw+idw+tgw]


    # Duplicator
    s.rep_out_M1 = Wire(cl)
    @s.update
    def Replicator():
      for i in range(0,clw,dbw):
        s.rep_out_M1[i:i+dbw] = s.cachereq_data_M1
      # s.rep_out_M1[0:dbw] = s.cachereq_data_M1
      # s.rep_out_M1[1*dbw:2*dbw] = s.cachereq_data_M1
      # s.rep_out_M1[2*dbw:3*dbw] = s.cachereq_data_M1
      # s.rep_out_M1[3*dbw:4*dbw] = s.cachereq_data_M1

    # Data Array ( Btwn M1 and M2 )
    s.data_array_idx_M1   = Wire(ix)
    s.data_array_wdata_M1 = Wire(cl)
    s.data_array_rdata_M2 = Wire(cl)
    s.data_array_wdata_M1 //= s.rep_out_M1
    
    @s.update
    def data_array_M2_connect():
      s.data_array_idx_M1   = ab(s.cachereq_addr_M1)[ofw:idw+ofw]
    
    s.data_array_M2 = SramPRTL(clw, nbl)(
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
    s.cachereq_opaque_M2  = Wire(ob)
    s.cachereq_opaque_reg_M2 = RegEnRst(ob)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_opaque_M1,
      out = s.cacheresp_opaque,
    )
    s.cachereq_type_M2    = Wire(ty)
    s.cachereq_type_reg_M2 = RegEnRst(ty)(
      en  = s.reg_en_M2,
      in_ = s.cachereq_type_M1,
      out = s.cacheresp_type,
    )
    s.cachereq_addr_M2    = Wire(ab)
    s.cachereq_address_reg_M2 = RegEnRst(ab)(
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
    s.read_word_mux_M2 = Mux(db, 5)(
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
      s.memreq_opaque = b8(0)
      s.memreq_addr   = b32(0)
      s.memreq_data   = b128(0)
    #   s.cacheresp_data = b32(0)
    #   s.cacheresp_opaque = b8(0)
    #   s.cacheresp_type   = b4(0)
    #   s.tag_match_M1   = b1(0)
      
  def line_trace( s ):
    return ""
