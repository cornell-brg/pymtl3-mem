"""
=========================================================================
ProcModel.py
=========================================================================
Models the processor handshake by unifying the src and sink signals

Author : Xiaoyu Yan, Eric Tang
Date   : 9 March 2020
"""

from pymtl3 import *
from pymtl3.stdlib.mem.ifcs  import MemRequesterIfc, MemResponderIfc
from pymtl3.stdlib.primitive import RegRst

class ProcModel( Component ):

  def construct( s, CacheReqType, CacheRespType ):
    # src -> |  ProcModel  |  -> cache
    # requests and responses
    s.proc  = MemResponderIfc( CacheReqType, CacheRespType )
    s.cache = MemRequesterIfc( CacheReqType, CacheRespType )

    s.cache.reqstream.msg  //= s.proc.reqstream.msg
    s.cache.reqstream.val  //= s.proc.reqstream.val
    s.proc.reqstream.rdy   //= s.cache.reqstream.rdy

    s.proc.respstream.msg  //= s.cache.respstream.msg
    s.proc.respstream.val  //= s.cache.respstream.val
    # s.cache.resp.rdy //= s.proc.resp.rdy

    s.trans_in_flight = RegRst(Bits2) # keeps track of transactions in flight

    @update
    def signal_model():
      # If the cache request is not ready, then the processor's response rdy is
      # low.
      if s.trans_in_flight.out == b2(0):
        s.cache.respstream.rdy @= s.proc.respstream.rdy & s.cache.reqstream.rdy
      else:
        s.cache.respstream.rdy @= s.proc.respstream.rdy

      # s.proc.req.rdy  = s.cache.req.rdy & s.proc.resp.rdy

    @update
    def update_trans_in_flight():
      s.trans_in_flight.in_ @= s.trans_in_flight.out
      if s.cache.reqstream.val & s.cache.reqstream.rdy and \
        ~(s.cache.respstream.val & s.cache.respstream.rdy):
        s.trans_in_flight.in_ @= s.trans_in_flight.out + b2(1)
      elif ~(s.cache.reqstream.val & s.cache.reqstream.rdy) and \
            s.cache.respstream.val & s.cache.respstream.rdy:
        s.trans_in_flight.in_ @= s.trans_in_flight.out - b2(1)

  def line_trace( s ):
    msg = ''
    # msg = f"{s.proc.resp.en}"
    return msg
