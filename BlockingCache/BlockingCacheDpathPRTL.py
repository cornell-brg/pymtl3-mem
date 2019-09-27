#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.ifcs import MemReqMsg4B, MemRespMsg4B
# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst
# from sram.SramRTL import * 

class BlockingCacheDpathPRTL ( Component ):
  def construct( s,
                 abw  = 32,
                 dbw  = 32,
                 size = 8192, # Cache size in bytes
                 clw  = 128, # Short name for cacheline bitwidth
                 way  = 1 # associativity
  ):
    nbl = size*8/clw, # Short name for number of cache blocks, 8192*8/128 = 512
    idw = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw = clog2(clw/8)   # Short name for offset bit width, clog2(128/8) = 4
    tgw = abw - ofw - idw
    
    # SRAM Declaration
    # Tag Array:
    # s.tag_array = SramRTL(tgw, nbl)

  def line_trace( s ):
    # return s.tag_array.line_trace()
    return 0