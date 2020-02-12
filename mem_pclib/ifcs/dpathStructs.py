"""
#=========================================================================
# dpathStructs.py
#=========================================================================
bitstructs for cleaner code
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 2 February 2020
"""

def mk_pipeline_msg( addr, data, opaque, type_, len_ )
  BitsAddr    = mk_bits( addr    )
  BitsData    = mk_bits( data    )
  BitsOpaque  = mk_bits( opaque  )
  BitsType    = mk_bits( type_   )
  BitsLen     = mk_bits( len_    )
  cls_name    = f"Pipeline_msg_{opq}_{addr}_{data}"

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type ) ],
      OpqType( self.opaque ),
      AddrType( self.addr ),
      LenType( self.len ),
      DataType( self.data ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type':   BitsType,
    'opaque': OpqType,
    'addr':   AddrType,
    'len':    LenType,
    'data':   DataType,
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls


