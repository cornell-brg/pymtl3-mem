#=========================================================================
# BlockingCacheCtrlPRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.ifcs import MemReqMsg4B, MemRespMsg4B
# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst

class BlockingCacheCtrlPRTL ( Component ):
  def construct( s,
                 abw  = 32,
                 dbw  = 32,
                 size = 8192, # Cache size in bytes
                 clw  = 128, # Short name for cacheline bitwidth
                 way  = 1, # associativity
  ):
    nbl = size*8//clw # Short name for number of cache blocks, 8192*8/128 = 512
    idw = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw = clog2(clw//8)   # Short name for offset bit width, clog2(128/8) = 4
    tgw = abw - ofw - idw

    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1) 

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)
    # M0 Ctrl Signals 
    s.reg_en_M0             = OutPort(Bits1)
    s.write_data_mux_sel_M0 = OutPort(mk_bits(clog2(2)))
    # tag array
    s.tag_array_val_M0      = OutPort(Bits1)
    s.tag_array_type_M0     = OutPort(Bits1)
    s.tag_array_wben_M0     = OutPort(Bits1)
    
    # M1 Ctrl Signals
    s.tag_match_M1          = InPort(Bits1)
    s.reg_en_M1             = OutPort(Bits1)
    # data array
    s.data_array_val_M1     = OutPort(Bits1)
    s.data_array_type_M1    = OutPort(Bits1)
    s.data_array_wben_M1    = OutPort(Bits1)
    # M2 Ctrl Signals
    s.reg_en_M2             = OutPort(Bits1)
    s.read_data_mux_sel_M2  = OutPort(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = OutPort(mk_bits(clog2(5)))
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    @s.update
    def comb_block():
      s.tag_array_val_M0 = 0
      s.tag_array_type_M0 = 0
      s.tag_array_wben_M0 = 0xf
    #-----------------------------------------------------
    # M1 Stage 
    #-----------------------------------------------------
    
  def line_trace( s ):
    return 'hello'