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

                 req_type = "inv",
                 resp_type = "inv",
  ):
    nbl = size*8/clw # Short name for number of cache blocks, 8192*8/128 = 512
    idw = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw = clog2(clw/8)   # Short name for offset bit width, clog2(128/8) = 4
    tgw = abw - ofw - idw

    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1) 

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)

    connect( s.cachereq_en, s.memreq_en )
    connect( s.cachereq_rdy, s.memreq_rdy )

    connect( s.memresp_en, s.cacheresp_en )
    connect( s.memresp_rdy, s.cacheresp_rdy )
    # @s.update
    # def comb_block():
    #   s.
    
  def line_trace( s ):
    return 'hello'