#=========================================================================
# FL model of Blocking Cache
#=========================================================================
# A function level cache model which only passes cache requests and
# responses to the memory.

from pymtl3      import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg
from pymtl3.stdlib.rtl.registers import RegRst


class BlockingCacheFL( Component ):

  cache_dict = {}

  def construct( s,
                 nbytes        = 4096, # cache size in bytes, nbytes
                 CacheMsg      = "",   # Cache req/resp msg type
                 MemMsg        = "",   # Memory req/resp msg type
                 associativity = 1     # associativity, name: associativity
  ):

    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------

    assert MemMsg.abw == CacheMsg.abw, "abw not the same"
    clw = MemMsg.dbw
    abw = MemMsg.abw
    dbw = CacheMsg.dbw
    BitsData      = mk_bits(dbw)   # data

    nbl = nbytes//clw 
    idw = clog2(nbl)         # index width; clog2(512) = 9
    ofw = clog2(clw//8)      # offset bitwidth; clog2(128/8) = 4

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( CacheMsg.Req  )
    # Cache -> Proc
    s.cacheresp = SendIfcRTL ( CacheMsg.Resp )
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemMsg.Resp   )
    # Cache -> Mem
    s.memreq    = SendIfcRTL ( MemMsg.Req    )

    #---------------------------------------------------------------------
    # Control
    #---------------------------------------------------------------------

    # pass through val/rdy signals

    connect( s.cachereq.en, s.memreq.en )
    connect( s.cachereq.rdy, s.memreq.rdy )

    connect( s.memresp.en, s.cacheresp.en )
    connect( s.memresp.rdy, s.cacheresp.rdy )

    #---------------------------------------------------------------------
    # Datapath
    #---------------------------------------------------------------------
    s.cacheresp_type_out = Wire(b4)
    s.type_reg = RegRst(b4)(
      in_ = s.cachereq.msg.type_,
      out = s.cacheresp_type_out
    )

    @s.update
    def logic():

      # Pass through requests: just copy all of the fields over, except
      # we zero extend the data field.

      if s.cachereq.msg.len == 0:
        len_ = 4
      else:
        len_ = s.cachereq.msg.len

      if s.cachereq.msg.type_ == MemMsgType.WRITE_INIT:
        s.memreq.msg.type_ = MemMsgType.WRITE
      else:
        s.memreq.msg.type_ = s.cachereq.msg.type_

      s.memreq.msg.opaque  = s.cachereq.msg.opaque
      s.memreq.msg.addr    = s.cachereq.msg.addr
      s.memreq.msg.len     = len_
      s.memreq.msg.data    = zext( BitsData(s.cachereq.msg.data), clw )

      # Pass through responses: just copy all of the fields over, except
      # we truncate the data field.

      len_ = s.memresp.msg.len
      if len_ == 4:
        len_ = 0

      s.cacheresp.msg.type_  = s.cacheresp_type_out
      s.cacheresp.msg.opaque = s.memresp.msg.opaque
      # if s.cachereq.msg.addr in cache_dict:
      #   s.cacheresp.msg.test = b1(1)
      # else:
      #   s.cacheresp.msg.test = b1(0)
      #   begin_line = s.cachereq.msg.addr//16 * 16
      #   cache_dict[begin_line] = True
      #   cache_dict[begin_line+4] = True
      #   cache_dict[begin_line+8] = True
      #   cache_dict[begin_line+12] = True
      #s.cacheresp.msg.test   = b1(0) if s.cacheresp_type_out == \
      #  MemMsgType.WRITE_INIT else b1(1)
      s.cacheresp.msg.len    = len_
      s.cacheresp.msg.data   = s.memresp.msg.data[0:abw]

    @s.update_ff
    def hit_logic():
      # print(s.cache_dict) 
      if s.cachereq.msg.type_ == MemMsgType.WRITE_INIT:
        s.cacheresp.msg.test <<= b2(0)
        begin_line = s.cachereq.msg.addr//16 * 16
        s.cache_dict[begin_line] = True
        s.cache_dict[begin_line+4] = True
        s.cache_dict[begin_line+8] = True
        s.cache_dict[begin_line+12] = True
      elif s.cachereq.msg.addr in s.cache_dict:
        s.cacheresp.msg.test <<= b2(1)
      else:
        s.cacheresp.msg.test <<= b2(0)
        begin_line = s.cachereq.msg.addr//16 * 16
        s.cache_dict[begin_line] = True
        s.cache_dict[begin_line+4] = True
        s.cache_dict[begin_line+8] = True
        s.cache_dict[begin_line+12] = True

      if s.reset:
        s.cache_dict = {}

     
  def line_trace(s):
    return "resp_rdy:{} resp_en:{}".format(s.cacheresp.rdy,s.cacheresp.en)

