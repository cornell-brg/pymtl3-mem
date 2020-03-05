"""
=========================================================================
BlockingCacheRTL.py
=========================================================================
Top level model of Pipelined Blocking Cache with instances of ctrl and
dpath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 20 February 2020
"""
from pymtl3                               import *
from pymtl3.stdlib.connects               import connect_pairs
from pymtl3.stdlib.ifcs.MemMsg            import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.ifcs.mem_ifcs          import MemMasterIfcRTL, MemMinionIfcRTL
from pymtl3.stdlib.connects.connect_bits2bitstruct import *

from .BlockingCacheCtrlRTL                import BlockingCacheCtrlRTL
from .BlockingCacheDpathRTL               import BlockingCacheDpathRTL
from .CacheDerivedParams                  import CacheDerivedParams

class BlockingCacheRTL ( Component ):

  def construct( s, CacheReqType, CacheRespType, MemReqType, MemRespType,
    num_bytes = 4096, associativity = 1 ):
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
    p = CacheDerivedParams( CacheReqType, CacheRespType, MemReqType, MemRespType,
                            num_bytes, associativity )
    s.param = p # params for line trace

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Memory-Minion Interface (e.g. proc <-> cache)
    s.mem_minion_ifc = MemMinionIfcRTL( CacheReqType, CacheRespType )
    # Memory-Master Interface (e.g. cache <-> main memory or lower-level cache)
    s.mem_master_ifc = MemMasterIfcRTL( MemReqType, MemRespType )

    #---------------------------------------------------------------------
    # Structural Composition
    #---------------------------------------------------------------------

    s.cacheDpath = BlockingCacheDpathRTL( p )(
      cachereq_Y          = s.mem_minion_ifc.req.msg,
      memresp_Y           = s.mem_master_ifc.resp.msg
    )

    s.cacheCtrl = BlockingCacheCtrlRTL( p )(
      cachereq_en           = s.mem_minion_ifc.req.en,
      cachereq_rdy          = s.mem_minion_ifc.req.rdy,
      memresp_en            = s.mem_master_ifc.resp.en,
      memresp_rdy           = s.mem_master_ifc.resp.rdy,
      cacheresp_en          = s.mem_minion_ifc.resp.en,
      cacheresp_rdy         = s.mem_minion_ifc.resp.rdy,
      memreq_en             = s.mem_master_ifc.req.en,
      memreq_rdy            = s.mem_master_ifc.req.rdy,
    )

    connect( s.cacheDpath.dpath_out, s.cacheCtrl.dpath_in )
    connect( s.cacheDpath.ctrl_in  , s.cacheCtrl.ctrl_out )

    # Cache Response Message
    s.mem_minion_ifc.resp.msg.opaque //= s.cacheDpath.dpath_out.cacheresp_opaque_M2
    s.mem_minion_ifc.resp.msg.type_  //= s.cacheDpath.dpath_out.cacheresp_type_M2
    s.mem_minion_ifc.resp.msg.data   //= s.cacheDpath.dpath_out.cacheresp_data_M2
    s.mem_minion_ifc.resp.msg.len    //= s.cacheDpath.dpath_out.cacheresp_len_M2
    s.mem_minion_ifc.resp.msg.test   //= s.cacheCtrl.ctrl_out.hit_M2

    # Memory Request Message
    s.mem_master_ifc.req.msg.opaque  //= s.cacheDpath.dpath_out.memreq_opaque_M2
    s.mem_master_ifc.req.msg.type_   //= s.cacheCtrl.ctrl_out.memreq_type
                            # Bits32                       # StructAddr
    connect_bits2bitstruct( s.mem_master_ifc.req.msg.addr, s.cacheDpath.dpath_out.memreq_addr_M2 )
    s.mem_master_ifc.req.msg.data    //= s.cacheDpath.dpath_out.memreq_data_M2

  # Line tracing
  def line_trace( s ):
    memreq_msg = "{}".format(" "*(10 + s.param.bitwidth_cacheline//4))
    memresp_msg = "{}".format(" "*(10 + s.param.bitwidth_cacheline//4))

    if s.mem_master_ifc.resp.en:
      memresp_msg = "{}".format(s.mem_master_ifc.resp.msg)
    if s.mem_master_ifc.req.en:
      memreq_msg  = "{}".format(s.mem_master_ifc.req.msg)
    msg = "{} {}{}{}".format(
      s.cacheDpath.line_trace(), memresp_msg, s.cacheCtrl.line_trace(),
      memreq_msg
    )
    return msg
