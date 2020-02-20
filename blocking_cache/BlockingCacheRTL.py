"""
=========================================================================
BlockingCacheRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and
dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from .BlockingCacheCtrlRTL                import BlockingCacheCtrlRTL
from .BlockingCacheDpathRTL               import BlockingCacheDpathRTL
from .CacheParams                         import CacheParams
from pymtl3                               import *
from pymtl3.stdlib.connects               import connect_pairs
from pymtl3.stdlib.ifcs.MemMsg            import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL

class BlockingCacheRTL ( Component ):

  def construct( s,
    num_bytes     = 4096, # cache size in bytes
    CacheMsg      = "",   # Cache req/resp msg type
    MemMsg        = "",   # Memory req/resp msg type
    associativity = 1     # Associativity
  ):

    p = CacheParams(num_bytes=num_bytes, CacheMsg=CacheMsg, \
                         MemMsg=MemMsg, associativity=associativity)
    #----------------------------------------------------------------------------
    # Interface
    #----------------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( CacheMsg.Req )
    # Cache -> Proc
    s.cacheresp = SendIfcRTL( CacheMsg.Resp )
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemMsg.Resp )
    # Cache -> Mem
    s.memreq    = SendIfcRTL( MemMsg.Req )

    s.cacheDpath = BlockingCacheDpathRTL( p )\
    (
      cachereq            = s.cachereq.msg,
      memresp_Y           = s.memresp.msg
    )

    s.cacheCtrl = BlockingCacheCtrlRTL( p )\
    (
      cachereq_en           = s.cachereq.en,
      cachereq_rdy          = s.cachereq.rdy,
      memresp_en            = s.memresp.en,
      memresp_rdy           = s.memresp.rdy,
      cacheresp_en          = s.cacheresp.en,
      cacheresp_rdy         = s.cacheresp.rdy,
      memreq_en             = s.memreq.en,
      memreq_rdy            = s.memreq.rdy,
    )
    connect( s.cacheDpath.dpath_out, s.cacheCtrl.dpath_in )
    connect( s.cacheDpath.ctrl_in  , s.cacheCtrl.ctrl_out )
    s.cacheresp.msg.opaque  //= s.cacheDpath.dpath_out.cacheresp_opaque_M2
    s.cacheresp.msg.type_   //= s.cacheDpath.dpath_out.cacheresp_type_M2
    s.cacheresp.msg.data    //= s.cacheDpath.dpath_out.cacheresp_data_M2
    s.cacheresp.msg.len     //= s.cacheDpath.dpath_out.cacheresp_len_M2
    s.cacheresp.msg.test    //= s.cacheCtrl.ctrl_out.hit_M2
    s.memreq.msg.opaque     //= s.cacheDpath.dpath_out.memreq_opaque_M2
    s.memreq.msg.type_      //= s.cacheCtrl.ctrl_out.memreq_type
    s.memreq.msg.addr       //= s.cacheDpath.dpath_out.memreq_addr_M2
    s.memreq.msg.data       //= s.cacheDpath.dpath_out.memreq_data_M2

    connect_pairs(
      s.cacheCtrl.reg_en_M1,                  s.cacheDpath.reg_en_M1,
    )

  # Line tracing
  def line_trace( s ):
    memreq_msg = memresp_msg = "{:42}".format(" ")

    if s.memresp.en:
      memresp_msg = "{}".format(s.memresp.msg)
    if s.memreq.en:
      memreq_msg  = "{}".format(s.memreq.msg)
    msg = "{} {} {}{}".format(\
      s.cacheCtrl.line_trace(),memreq_msg,memresp_msg,
      s.cacheDpath.line_trace())
    return msg