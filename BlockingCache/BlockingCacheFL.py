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

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( CacheMsg.Req )
    # Cache -> Proc
    s.cacheresp = SendIfcRTL( CacheMsg.Resp )
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemMsg.Resp )
    # Cache -> Mem
    s.memreq    = SendIfcRTL( MemMsg.Req )

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
      s.cacheresp.msg.test   = b1(0) if s.cacheresp_type_out == \
        MemMsgType.WRITE_INIT else b1(1)
      s.cacheresp.msg.len    = len_
      s.cacheresp.msg.data   = s.memresp.msg.data[0:abw]

  def line_trace(s):
    return "(forw)"
