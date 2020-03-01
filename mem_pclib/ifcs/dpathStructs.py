"""
=========================================================================
 dpathStructs.py
=========================================================================
Bitstructs used within the datapath

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 2 February 2020
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

def mk_pipeline_msg( p ):
  cls_name    = f"Pipeline"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      BitsOpaque( self.opaque ),
      BitsAddr( self.addr ),
      BitsLen( self.len ),
      BitsData( self.data ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':  p.BitsType,
    'opaque': p.BitsOpaque,
    'addr':   p.StructAddr,
    'len':    p.BitsLen,
    'data':   p.BitsCacheline,
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls

def mk_MSHR_msg( p ):
  cls_name    = f"MSHR"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      BitsOpaque( self.opaque ),
      BitsAddr( self.addr ),
      BitsLen( self.len ),
      BitsData( self.data ),
      BitsRep(self.repl)
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':  p.BitsType,
    'opaque': p.BitsOpaque,
    'addr':   p.BitsAddr,
    'len':    p.BitsLen,
    'data':   p.BitsData,
    'repl':   p.BitsAssoclog2
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls

def mk_M0_mux_msg( p ):
  req_cls = mk_bitstruct( "M0", {
    'type_':  p.BitsType,
    'opaque': p.BitsOpaque,
    'len':    p.BitsLen,
    'data':   p.BitsData,
  })
  return req_cls

def mk_addr_struct( p ):
  # declaration alignment MATTERS here
  struct = mk_bitstruct( "addr", {
    'tag'   : p.BitsTag,
    'index' : p.BitsIdx,
    'offset': p.BitsOffset
  } )
  return struct