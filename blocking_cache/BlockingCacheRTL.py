"""
=========================================================================
BlockingCacheRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and
dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 February 2020
"""

from .BlockingCacheCtrlRTL                import BlockingCacheCtrlRTL
from .BlockingCacheDpathRTL               import BlockingCacheDpathRTL
from .CacheDerivedParams                  import CacheDerivedParams
from pymtl3                               import *
from pymtl3.stdlib.connects               import connect_pairs
from pymtl3.stdlib.ifcs.MemMsg            import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.ifcs.mem_ifcs          import MemMasterIfcRTL, MemMinionIfcRTL

class BlockingCacheRTL ( Component ):

  def construct( s,
    CacheMsg      ,   # Cache req/resp msg type
    MemMsg        ,   # Memory req/resp msg type
    num_bytes     = 4096, # cache size in bytes
    associativity = 1     # Associativity
  ):

    # Generate additional constants and bitstructs from the given parameters
    p = CacheDerivedParams( CacheMsg, MemMsg, num_bytes, associativity )

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc <-> Cache
    s.cpu_port = MemMinionIfcRTL( CacheMsg.Req, CacheMsg.Resp )
    # Mem <-> Cache
    s.mem_port = MemMasterIfcRTL( MemMsg.Req, MemMsg.Resp )

    #---------------------------------------------------------------------
    # Composition
    #---------------------------------------------------------------------

    s.cacheDpath = BlockingCacheDpathRTL( p ) \
    (
      cachereq_Y          = s.cpu_port.req.msg,
      memresp_Y           = s.mem_port.resp.msg
    )

    s.cacheCtrl = BlockingCacheCtrlRTL( p ) \
    (
      cachereq_en           = s.cpu_port.req.en,
      cachereq_rdy          = s.cpu_port.req.rdy,
      memresp_en            = s.mem_port.resp.en,
      memresp_rdy           = s.mem_port.resp.rdy,
      cacheresp_en          = s.cpu_port.resp.en,
      cacheresp_rdy         = s.cpu_port.resp.rdy,
      memreq_en             = s.mem_port.req.en,
      memreq_rdy            = s.mem_port.req.rdy,
    )

    connect( s.cacheDpath.dpath_out, s.cacheCtrl.dpath_in )
    connect( s.cacheDpath.ctrl_in  , s.cacheCtrl.ctrl_out )

    # Cache Response Message
    s.cpu_port.resp.msg.opaque //= s.cacheDpath.dpath_out.cacheresp_opaque_M2
    s.cpu_port.resp.msg.type_  //= s.cacheDpath.dpath_out.cacheresp_type_M2
    s.cpu_port.resp.msg.data   //= s.cacheDpath.dpath_out.cacheresp_data_M2
    s.cpu_port.resp.msg.len    //= s.cacheDpath.dpath_out.cacheresp_len_M2
    s.cpu_port.resp.msg.test   //= s.cacheCtrl.ctrl_out.hit_M2
    
    # Memory Request Message
    s.mem_port.req.msg.opaque  //= s.cacheDpath.dpath_out.memreq_opaque_M2
    s.mem_port.req.msg.type_   //= s.cacheCtrl.ctrl_out.memreq_type
    s.mem_port.req.msg.addr    //= s.cacheDpath.dpath_out.memreq_addr_M2
    s.mem_port.req.msg.data    //= s.cacheDpath.dpath_out.memreq_data_M2

  # Line tracing
  def line_trace( s ):
    memreq_msg = "{:42}".format(" ")
    memresp_msg = "{:42}".format(" ")

    if s.mem_port.resp.en:
      memresp_msg = "{}".format(s.mem_port.resp.msg)
    if s.mem_port.req.en:
      memreq_msg  = "{}".format(s.mem_port.req.msg)
    msg = "{} {}{}{}".format(\
      s.cacheDpath.line_trace(), memresp_msg, s.cacheCtrl.line_trace(),
      memreq_msg
      )
    return msg
