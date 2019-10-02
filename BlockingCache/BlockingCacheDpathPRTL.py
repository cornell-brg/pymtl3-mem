#=========================================================================
# BlockingCacheDpathPRTL.py
#=========================================================================

from pymtl3      import *
# from pclib.ifcs import MemReqMsg4B, MemRespMsg4B
# from pclib.rtl import RegEnRst, Mux, RegisterFile, RegRst
from sram.SramPRTL import SramPRTL

class BlockingCacheDpathPRTL ( Component ):
  def construct( s,
                 abw  = 32,
                 dbw  = 32,
                 size = 8192, # Cache size in bytes
                 clw  = 128, # Short name for cacheline bitwidth
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
    
    # Cache <-> Proc Msg
    s.cachereq_msg  = InPort(cache_req_type)
    s.cacheresp_msg = OutPort(cache_resp_type)
    # Cache <-> Mem Msg
    s.memreq_msg    = OutPort(mem_req_type)
    s.memresp_msg   = InPort(mem_resp_type)
    # M0 Ctrl Signals
    s.tag_array_val_M0 = InPort(Bits1)
    s.tag_array_type_M0 = InPort(Bits1)
    s.tag_array_wben_M0 = InPort(Bits3)

    connect( s.cachereq_msg, s.memreq_msg)
    connect( s.cacheresp_msg, s.memresp_msg)
    #-------------
    # M0 Stage
    #-------------
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
    return s.tag_array.line_trace()
