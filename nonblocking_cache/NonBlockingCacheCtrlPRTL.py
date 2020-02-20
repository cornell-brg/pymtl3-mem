
from pymtl3      import *
# from pclib.ifcs import MemReqMsg4B, MemRespMsg4B

# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst

from .ifcs.CoherentMemMsg import *

class NonBlockingCacheCtrlPRTL ( Model ):
  def construct( s,
    ncaches = 1,
    cache_id = 0,
    opw  = 8,   # Short name for opaque bitwidth
    abw  = 32,  # Short name for addr bitwidth
    dbw  = 32,  # Short name for data bitwidth
    clw  = 128, # Short name for cacheline bitwidth
    nbl  = 512, # Short name for number of cache blocks, 8192*8/128 = 512

    tgw  = 28,  # Short name for tag bit width, 32-4 = 28
    stw  = 4,   # Short name for state bit width
    ctw  = 3,   # Cache type's bit width
    mtw  = 4,   # Mem type's bit width
    ccbw = 4,   # bit width of cache commands (from S1 -> S2)
    srw  = 2   # Bit width of src and dst IDs
  ):
    idw  = clog2(nbl)   # Short name for index width, clog2(512) = 9
    ofw  = clog2(clw/8)   # Short name for offset bit width, clog2(128/8) = 4

  def line_trace( s ):
    return 'hello'