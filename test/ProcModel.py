"""
=========================================================================
ProcModel.py
=========================================================================
Models the processor handshake by unifying the src and sink signals

Author : Xiaoyu Yan, Eric Tang
Date   : 9 March 2020
"""

from pymtl3 import *
from pymtl3.stdlib.mem       import MemMasterIfcRTL, MemMinionIfcRTL
from pymtl3.stdlib.basic_rtl import RegRst

class ProcModel( Component ):

  def construct( s, CacheReqType, CacheRespType ):
    # src -> |  ProcModel  |  -> cache
    # requests and responses
    s.proc  = MemMinionIfcRTL( CacheReqType, CacheRespType )
    s.cache = MemMasterIfcRTL( CacheReqType, CacheRespType )

    s.cache.req.msg  //= s.proc.req.msg
    s.cache.req.en   //= s.proc.req.en
    s.proc.req.rdy   //= s.cache.req.rdy

    s.proc.resp.msg  //= s.cache.resp.msg
    s.proc.resp.en   //= s.cache.resp.en
    # s.cache.resp.rdy //= s.proc.resp.rdy

    s.trans_in_flight = RegRst(Bits2) # keeps track of transactions in flight

    @update
    def signal_model():
      # If the cache request is not ready, then the processor's response rdy is
      # low.
      if s.trans_in_flight.out == b2(0):
        s.cache.resp.rdy @= s.proc.resp.rdy & s.cache.req.rdy
      else:
        s.cache.resp.rdy @= s.proc.resp.rdy

      # s.proc.req.rdy  = s.cache.req.rdy & s.proc.resp.rdy

    @update
    def update_trans_in_flight():
      s.trans_in_flight.in_ @= s.trans_in_flight.out
      if s.cache.req.en and ~s.cache.resp.en:
        s.trans_in_flight.in_ @= s.trans_in_flight.out + b2(1)
      elif ~s.cache.req.en and s.cache.resp.en:
        s.trans_in_flight.in_ @= s.trans_in_flight.out - b2(1)

  def line_trace( s ):
    msg = ''
    # msg = f"{s.proc.resp.en}"
    return msg
