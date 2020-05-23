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
from pymtl3.stdlib.mem import MagicMemoryFL, MemMsgType, mk_mem_msg, MemMinionIfcCL
from pymtl3.stdlib.delays import DelayPipeDeqCL, DelayPipeSendCL, StallCL

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

    s.nports = nports
    req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    resp_classes = [ y for (x,y) in mem_ifc_dtypes ]
    
    s.mem = MagicMemoryFL( mem_nbytes )

    # Interface

    s.ifc = [ MemMinionIfcCL( req_classes[i], resp_classes[i] ) for i in range(nports) ]

    # Queues
    req_latency = min(1, latency)
    resp_latency = latency - req_latency

    s.req_stalls = [ StallCL( stall_prob, i )     for i in range(nports) ]
    s.req_qs  = [ DelayPipeDeqCL( req_latency )   for i in range(nports) ]
    s.resp_qs = [ DelayPipeSendCL( resp_latency ) for i in range(nports) ]
    
    for i in range(nports):
      s.req_stalls[i].recv //= s.ifc[i].req
      s.resp_qs[i].send    //= s.ifc[i].resp

      s.req_qs[i].enq      //= s.req_stalls[i].send

    data_nbits = req_classes[i].data_nbits

    @update_once
    def up_mem():

      for i in range(s.nports):

        if s.req_qs[i].deq.rdy() and s.resp_qs[i].enq.rdy():

          # Dequeue memory request message

          req = s.req_qs[i].deq()
          len_ = int(req.len)
          if len_ == 0: len_ = req_classes[i].data_nbits >> 3

          if   req.type_ == MemMsgType.READ:
            if hasattr( req, "wr_mask" ):
              resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                    req.wr_mask, s.mem.read( req.addr, len_ ) )
            else:
              resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                    s.mem.read( req.addr, len_ ) )
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
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0,
              zext(amo_result, data_nbits) )

          s.resp_qs[i].enq( resp )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------
  # TODO: better line trace.

  def line_trace( s ):
    return "|".join( [ x[0].line_trace() + x[1].line_trace() for x in zip(s.req_qs, s.resp_qs) ] )
