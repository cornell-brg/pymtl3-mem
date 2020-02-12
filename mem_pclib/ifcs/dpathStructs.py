"""
#=========================================================================
# dpathStructs.py
#=========================================================================
bitstructs for cleaner code
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 2 February 2020
"""
from pymtl3 import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

def mk_pipeline_msg( addr, data, opaque, type_, len_ ):
  BitsAddr    = mk_bits( addr    )
  BitsData    = mk_bits( data    )
  BitsOpaque  = mk_bits( opaque  )
  BitsType    = mk_bits( type_   )
  BitsLen     = mk_bits( len_    )
  cls_name    = f"Pipeline_msg_{opaque}_{addr}_{data}"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      BitsOpaque( self.opaque ),
      BitsAddr( self.addr ),
      BitsLen( self.len ),
      BitsData( self.data ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':   BitsType,
    'opaque': BitsOpaque,
    'addr':   BitsAddr,
    'len':    BitsLen,
    'data':   BitsData,
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls


