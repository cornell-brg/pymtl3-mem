"""
========================================================================
Cifer MemoryCL
========================================================================
A behavioral Test Memory which is parameterized based on the number of
memory request/response ports. This version is a little different from
the one in pclib because we actually use the memory messages correctly
in the interface.

Modified for Cifer Tapeout to include write bits

Author : Shunning Jiang, edited by Xiaoyu Yan (xy97)
Date   : Mar 12, 2018
"""

from pymtl3 import *
from pymtl3.stdlib.mem.BehavioralMemory import BehavioralMemory
from pymtl3.stdlib.mem.MemoryFL import RandomStall, InelasticDelayPipe
from pymtl3.stdlib.mem import MemMsgType, mk_mem_msg
from pymtl3.stdlib.mem.ifcs import MemResponderIfc

class MemoryCL( Component ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual stuff
  def construct( s, nports, mem_ifc_dtypes=[mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)],
                 stall_prob=0, latency=1, mem_nbytes=2**20 ):

    # Local constants

    assert len(mem_ifc_dtypes) == nports
    s.nports = nports
    req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    resp_classes = [ y for (x,y) in mem_ifc_dtypes ]
    
    s.mem = BehavioralMemory( mem_nbytes )

    # Interface

    s.ifc = [ MemResponderIfc( req_classes[i], resp_classes[i] ) for i in range(nports) ]

    # stall and delays
    s.req_stalls = [ RandomStall( req_classes[i], stall_prob, i ) for i in range(nports) ]
    # s.req_qs     = [ NormalQueueRTL( req_classes[i], 2 ) for i in range(nports) ]
    s.resp_qs    = [ InelasticDelayPipe( resp_classes[i], latency+1 ) for i in range(nports) ]

    for i in range(nports):
      s.req_stalls[i].istream //= s.ifc[i].reqstream
      # s.req_stalls[i].ostream //= s.req_qs[i].istream
      s.resp_qs[i].ostream    //= s.ifc[i].respstream

      s.req_stalls[i].ostream.rdy //= s.resp_qs[i].istream.rdy
      s.req_stalls[i].ostream.val //= s.resp_qs[i].istream.val

    @update_once
    def up_mem():

      for i in range(s.nports):

        data_nbits = req_classes[i].data_nbits

        if s.req_stalls[i].ostream.val:

          # Dequeue memory request message

          req = s.req_stalls[i].ostream.msg
          len_ = int(req.len)
          if len_ == 0: len_ = data_nbits >> 3

          if   req.type_ == MemMsgType.READ:
            if hasattr( req, "wr_mask" ):
              resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                      req.wr_mask, s.mem.read( req.addr, len_ ) )
            else:
              resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                      zext( s.mem.read( req.addr, len_ ), data_nbits ) )
          elif req.type_ == MemMsgType.WRITE:

            if hasattr(req, "wr_mask"):
              # check if the request has a word-level write mask (1 word = 32 bits)
              assert req.wr_mask.nbits == req.data.nbits // 32
              for j in range(req.wr_mask.nbits):
                if req.wr_mask[j]:
                  s.mem.write( req.addr + 4 * j, 4, req.data[32*j:32*(j+1)] )
              resp = resp_classes[i]( req.type_, req.opaque, 0, 0, 0, 0 )
            else:
              # no write mask
              s.mem.write( req.addr, len_, req.data )
              # FIXME do we really set len=0 in response when doing subword wr?
              # resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0 )
              resp = resp_classes[i]( req.type_, req.opaque, 0, 0, 0 )

          else: # AMOS
            # Assume AMO operations are always a word
            amo_result = s.mem.amo( req.type_, req.addr, len_, req.data[0:32] )
            if hasattr(req, "wr_mask"):
              resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0,
                zext(amo_result, data_nbits) )
            else:
              resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                zext(amo_result, data_nbits) )

          s.resp_qs[i].istream.msg @= resp

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------
  # TODO: better line trace.

  def line_trace( s ):
    return "|".join( [ x[0].line_trace() + x[1].line_trace() for x in zip(s.req_stalls, s.resp_qs) ] )
