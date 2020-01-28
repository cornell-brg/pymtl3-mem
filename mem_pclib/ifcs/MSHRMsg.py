"""
#=========================================================================
# MSHRMsg.py
#=========================================================================
Makes for MSHR alloc and dealloc msgs

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 25 January 2020
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

def mk_MSHR_msg( addr, data, opq, replacement):
  AddrType = mk_bits( addr )
  DataType = mk_bits( data )
  LenType  = mk_bits( clog2(data>>3) )
  OpqType  = mk_bits( opq            )
  RepType  = mk_bits( replacement )
  cls_name = f"MSHRMsg_{opq}_{addr}_{data}"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type ) ],
      OpqType( self.opaque ),
      AddrType( self.addr ),
      LenType( self.len ),
      DataType( self.data ) if self.type != MemMsgType.READ else
      " " * ( data//4 ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type':  Bits4,
    'opaque': OpqType,
    'addr':   AddrType,
    'len':    LenType,
    'data':   DataType,
    'rep' :   RepType,
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls