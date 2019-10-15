#=========================================================================
# BlockingCacheCtrlPRTL.py
#=========================================================================

from pymtl3      import *
from pymtl3.stdlib.rtl.registers import RegEnRst
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

class BlockingCacheCtrlPRTL ( Component ):
  def construct( s,
                 obw = 8,			      # Opaque bitwidth
                 abw  = 32,
                 dbw  = 32,
                 size = 8192, # Cache size in bytes
                 clw  = 128, # Short name for cacheline bitwidth
                 way  = 1, # associativity
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

    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)
    s.cachereq_type = InPort(Bits4)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1) 

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)
    #-----------------
    # M0 Ctrl Signals 
    #-----------------
    s.cachereq_type_M0      = InPort(ty)
    # s.reg_en_M0             = OutPort(Bits1)
    s.write_data_mux_sel_M0 = OutPort(mk_bits(clog2(2)))
    # tag array
    s.tag_array_val_M0      = OutPort(Bits1)
    s.tag_array_type_M0     = OutPort(Bits1)
    s.tag_array_wben_M0     = OutPort(Bits4)
    #-----------------
    # M1 Ctrl Signals
    #-----------------
    s.cachereq_type_M1      = InPort(ty)
    s.tag_match_M1          = InPort(Bits1)
    s.reg_en_M1             = OutPort(Bits1)
    # data array
    s.data_array_val_M1     = OutPort(Bits1)
    s.data_array_type_M1    = OutPort(Bits1)
    s.data_array_wben_M1    = OutPort(Bits16)
    #-----------------
    # M2 Ctrl Signals
    #-----------------
    s.cachereq_type_M2      = InPort(ty)
    s.reg_en_M2             = OutPort(Bits1)
    # s.read_data_mux_sel_M2  = OutPort(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = OutPort(mk_bits(clog2(5)))
    # Output Signals
    s.hit                   = OutPort(Bits2)
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    # Stall logic
    s.stall_M0 = Wire(Bits1)
    
    #Valid
    s.val_M0 = Wire(Bits1)
    s.val_M0 //= s.cachereq_en
    @s.update
    def comb_block_M0():
      s.cachereq_rdy = b1(1)
      s.memreq_en = b1(0)
      s.memresp_rdy = b1(0)
      if (s.cachereq_type == MemMsgType.WRITE_INIT):
        s.tag_array_type_M0 = b1(1)
        s.tag_array_val_M0  = b1(1)
        s.tag_array_wben_M0 = b4(1)
        s.write_data_mux_sel_M0 = b1(0) # Choose write data from cachereq
      elif (s.cachereq_type == MemMsgType.READ):
        s.tag_array_type_M0 = b1(0)
        s.tag_array_val_M0  = b1(1)
        s.tag_array_wben_M0 = b4(0) # DON'T CARE
        s.write_data_mux_sel_M0 = b1(0) # DON"T CARE


    #-----------------------------------------------------
    # M1 Stage 
    #-----------------------------------------------------
    s.val_M1 = Wire(Bits1)
    s.val_reg_M1 = RegEnRst(Bits1)(
      en  = s.reg_en_M1,
      in_ = s.val_M0,
      out = s.val_M1,
    )
    @s.update
    def comb_block_M1():
      s.reg_en_M1 = b1(1)
      if (s.cachereq_type == MemMsgType.WRITE_INIT):
        s.data_array_type_M1 = b1(1)
        s.data_array_val_M1  = b1(1)
        s.data_array_wben_M1 = b16(0xffff)
      elif (s.cachereq_type == MemMsgType.READ):
        s.data_array_type_M1 = b1(0)
        s.data_array_val_M1  = b1(1)
        s.data_array_wben_M1 = b16(0) # DON'T CARE
    s.hit[0:1] //= s.tag_match_M1

    #-----------------------------------------------------
    # M2 Stage 
    #-----------------------------------------------------
    s.val_M2 = Wire(Bits1)
    s.val_reg_M2 = RegEnRst(Bits1)(
      en  = s.reg_en_M2,
      in_ = s.val_M1,
      out = s.val_M2,
    )
    @s.update
    def comb_block_M2():
      # if s.cacheresp_rdy:
      s.cacheresp_en = b1(0)
      s.reg_en_M2 = b1(1)
      if (s.cachereq_type == MemMsgType.WRITE_INIT):
        s.read_word_mux_sel_M2 = b3(1)
      elif (s.cachereq_type == MemMsgType.READ):
        s.read_word_mux_sel_M2 = b3(1)


  def line_trace( s ):
    return "{}|{}|{}".format(s.val_M0,s.val_M1,s.val_M2)
