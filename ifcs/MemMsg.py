"""
========================================================================
MemMsg.py
========================================================================
Memory message type for CIFER project

Author : Shunning Jiang, Yanghui Ou
Date   : Mar 12, 2018
"""

from pymtl3 import *

#-------------------------------------------------------------------------
# MemMsgType
#-------------------------------------------------------------------------
# Define the "type" field of memory messages

class MemMsgType:
  READ       = 0
  WRITE      = 1
  WRITE_INIT = 2  # Write no-refill
  AMO_ADD    = 3
  AMO_AND    = 4
  AMO_OR     = 5
  AMO_SWAP   = 6
  AMO_MIN    = 7
  AMO_MINU   = 8
  AMO_MAX    = 9
  AMO_MAXU   = 10
  AMO_XOR    = 11
  LR         = 12 # Load-Reserved
  SC         = 13 # Store-Conditional
  INV        = 14 # Cache invalidation
  FLUSH      = 15 # Cache flush

  str = {
    READ       : "rd",
    WRITE      : "wr",
    WRITE_INIT : "in",
    AMO_ADD    : "ad",
    AMO_AND    : "an",
    AMO_OR     : "or",
    AMO_SWAP   : "sw",
    AMO_MIN    : "mi",
    AMO_MINU   : "mu",
    AMO_MAX    : "mx",
    AMO_MAXU   : "xu",
    AMO_XOR    : "xo",
    LR         : "lr",
    SC         : "sc",
    INV        : "iv",
    FLUSH      : "fl"
  }

# Translation work-around

MemMsgType_READ       = b4(0)
MemMsgType_WRITE      = b4(1)
MemMsgType_WRITE_INIT = b4(2)
MemMsgType_AMO_ADD    = b4(3)
MemMsgType_AMO_AND    = b4(4)
MemMsgType_AMO_OR     = b4(5)
MemMsgType_AMO_SWAP   = b4(6)
MemMsgType_AMO_MIN    = b4(7)
MemMsgType_AMO_MINU   = b4(8)
MemMsgType_AMO_MAX    = b4(9)
MemMsgType_AMO_MAXU   = b4(10)
MemMsgType_AMO_XOR    = b4(11)
MemMsgType_LR         = b4(12)
MemMsgType_SC         = b4(13)
MemMsgType_INV        = b4(14)
MemMsgType_FLUSH      = b4(15)

#-------------------------------------------------------------------------
# mk_mem_req_msg
#-------------------------------------------------------------------------
# Generate bitstruct: "MemReqMsg_{}_{}_{}".format( opq, addr, data )

def mk_mem_req_msg( opq, addr, data ):
  OpqType       = mk_bits( opq            )
  AddrType      = mk_bits( addr           )
  LenType       = mk_bits( clog2(data>>3) )
  WriteMaskType = mk_bits( data >> 5      )
  DataType      = mk_bits( data           )
  cls_name      = "MemReqMsg_{}_{}_{}".format( opq, addr, data )

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      OpqType( self.opaque ),
      AddrType( self.addr ),
      LenType( self.len ),
      WriteMaskType( self.wr_mask ),
      DataType( self.data ) if self.type_ != MemMsgType.READ else
      " " * ( data//4 ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':   Bits4,
    'opaque':  OpqType,
    'addr':    AddrType,
    'len':     LenType,
    'wr_mask': WriteMaskType,
    'data':    DataType,
  },
  namespace = {
    '__str__' : req_to_str
  })

  req_cls.data_nbits = data
  return req_cls

#-------------------------------------------------------------------------
# mk_mem_resp_msg
#-------------------------------------------------------------------------
# Generate bitstruct: "MemRespMsg_{}_{}".format( opq, data )

def mk_mem_resp_msg( opq, data ):
  OpqType       = mk_bits( opq            )
  LenType       = mk_bits( clog2(data>>3) )
  WriteMaskType = mk_bits( data >> 5      )
  DataType      = mk_bits( data           )
  cls_name = "MemRespMsg_{}_{}".format( opq, data )

  def resp_to_str( self ):
    return "{}:{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      OpqType( self.opaque ),
      Bits2( self.test ),
      LenType( self.len ),
      WriteMaskType( self.wr_mask ),
      DataType( self.data ) if self.type_ != MemMsgType.WRITE else
      " " * ( data//4 ),
    )

  resp_cls = mk_bitstruct( cls_name, {
    'type_':   Bits4,
    'opaque':  OpqType,
    'test':    Bits2,
    'len':     LenType,
    'wr_mask': WriteMaskType,
    'data':    DataType,
  },
  namespace = {
    '__str__' : resp_to_str
  })

  resp_cls.data_nbits = data
  return resp_cls

#-------------------------------------------------------------------------
# mk_mem_msg
#-------------------------------------------------------------------------
# Generate a pair of bitstructs (MemReqMsg, MemRespMsg) with consistent
# bit width

def mk_mem_msg( opq, addr, data ):
  return mk_mem_req_msg( opq, addr, data ), mk_mem_resp_msg( opq, data )