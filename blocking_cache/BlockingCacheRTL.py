"""
=========================================================================
BlockingCacheRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and
dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 February 2020
"""

from pymtl3                 import *
from pymtl3.stdlib.mem.ifcs import MemRequesterIfc, MemResponderIfc
from .BlockingCacheCtrlRTL  import BlockingCacheCtrlRTL
from .BlockingCacheDpathRTL import BlockingCacheDpathRTL
from .CacheDerivedParams    import CacheDerivedParams


class BlockingCacheRTL ( Component ):

  def construct( s, CacheReqType, CacheRespType, MemReqType, MemRespType,
                 num_bytes=4096, associativity=2 ):
    """
      Parameters
      ----------
      CacheReqType  : type
          Request type for mem_minion_ifc (e.g. between processor and cache)
      CacheRespType : type
          Response type for mem_minion_ifc
      MemReqType    : type
          Request type for mem_master_ifc (e.g. between this cache and memory)
      MemRespType   : type
          Response type for mem_master_ifc
      num_bytes     : int
          Cache size in bytes
      associativity : int
    """

    # Generate additional constants and bitstructs from the given parameters
    s.param = p = CacheDerivedParams( CacheReqType, CacheRespType, MemReqType,
                                      MemRespType, num_bytes, associativity )

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Memory-Minion Interface (e.g. proc <-> cache)
    s.mem_minion_ifc = MemResponderIfc( CacheReqType, CacheRespType )
    # Memory-Master Interface (e.g. cache <-> main memory or lower-level cache)
    s.mem_master_ifc = MemRequesterIfc( MemReqType, MemRespType )

    #---------------------------------------------------------------------
    # Structural Composition
    #---------------------------------------------------------------------

    s.cacheDpath = m = BlockingCacheDpathRTL( p )
    m.cachereq_Y   //= s.mem_minion_ifc.reqstream.msg
    m.cacheresp_M2 //= s.mem_minion_ifc.respstream.msg
    m.memresp_Y    //= s.mem_master_ifc.respstream.msg
    m.memreq_M2    //= s.mem_master_ifc.reqstream.msg

    s.cacheCtrl = m = BlockingCacheCtrlRTL( p )
    m.cachereq_val  //= s.mem_minion_ifc.reqstream.val
    m.cachereq_rdy  //= s.mem_minion_ifc.reqstream.rdy
    m.memresp_val   //= s.mem_master_ifc.respstream.val
    m.memresp_rdy   //= s.mem_master_ifc.respstream.rdy
    m.cacheresp_val //= s.mem_minion_ifc.respstream.val
    m.cacheresp_rdy //= s.mem_minion_ifc.respstream.rdy
    m.memreq_val    //= s.mem_master_ifc.reqstream.val
    m.memreq_rdy    //= s.mem_master_ifc.reqstream.rdy
    m.status        //= s.cacheDpath.status
    m.ctrl          //= s.cacheDpath.ctrl

  # Line tracing
  def line_trace( s, level=2 ):
    if level == 1:
      msg = s.cacheCtrl.line_trace()
    elif level == 2:
      memreq_msg = f"{' '*(19 + s.param.bitwidth_cacheline//4)}"
      memresp_msg = f"{' '*(12 + s.param.bitwidth_cacheline//4)}"

      if s.mem_master_ifc.respstream.val:
        memresp_msg = "{}".format(s.mem_master_ifc.respstream.msg)
      if s.mem_master_ifc.reqstream.val:
        memreq_msg  = "{}".format(s.mem_master_ifc.reqstream.msg)
      msg = "{} {}{}{}".format(
        s.cacheDpath.line_trace(), memresp_msg, s.cacheCtrl.line_trace(),
        memreq_msg
      )
    else:
      msg = ''
    return msg
