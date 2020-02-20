#=========================================================================
# CoherentMemMsg
#=========================================================================
# Contains coherent memory request and response messages

from pymtl import *

import math

#-------------------------------------------------------------------------
# CoherentMemReqMsg
#-------------------------------------------------------------------------
#     2b     2b       4b      8b     32b    4b    128b
# +-------+--------+------+--------+------+-----+------+
# + SrcID | DestID | type | opaque | addr | len | data |
# +-------+--------+------+--------+------+-----+------+

class CoherentMemReqMsg( BitStructDefinition ):

  nbits         = 180
  src_nbits     = 2
  dst_nbits     = 2
  type_nbits    = 4
  opaque_nbits  = 8
  addr_nbits    = 32
  len_nbits     = 4
  data_nbits    = 128

  # Coherent msg types

  TYPE_GET_S        = 0
  TYPE_GET_M        = 1
  TYPE_PUT_S        = 2
  TYPE_PUT_M        = 3
  TYPE_FWD_GET_S    = 4
  TYPE_FWD_GET_M    = 5
  TYPE_INV          = 6
  TYPE_WRITE_INIT_S = 7
  TYPE_WRITE_INIT_M = 8

  # Init

  def __init__( s ):

    s.src     = BitField( CoherentMemReqMsg.src_nbits     )
    s.dst     = BitField( CoherentMemReqMsg.dst_nbits     )
    s.type_   = BitField( CoherentMemReqMsg.type_nbits    )
    s.opaque  = BitField( CoherentMemReqMsg.opaque_nbits  )
    s.addr    = BitField( CoherentMemReqMsg.addr_nbits    )
    s.len     = BitField( CoherentMemReqMsg.len_nbits     )
    s.data    = BitField( CoherentMemReqMsg.data_nbits    )

  # Make a generic request message

  def mk_msg( s, src, dst, type_, opaque, addr, len_, data ):

    msg         = s()
    msg.src     = src
    msg.dst     = dst
    msg.type_   = type_
    msg.opaque  = opaque
    msg.addr    = addr
    msg.len     = len_
    msg.data    = data

    return msg

  def mk_rd( s, opaque, len_, data ):

    msg         = s()
    msg.src     = 0
    msg.dst     = 0
    msg.type_   = CoherentMemReqMsg.TYPE_GET_S
    msg.opaque  = opaque
    msg.len     = len_
    msg.data    = data

    return msg

  def mk_wr( s, opaque, len_, data ):

    msg         = s()
    msg.src     = 0
    msg.dst     = 0
    msg.type_   = CoherentMemReqMsg.TYPE_GET_M
    msg.opaque  = opaque
    msg.test    = 0
    msg.len     = len_
    msg.data    = data

    return msg

  # Return string format of a message

  def __str__( s ):

    if s.type_ == CoherentMemReqMsg.TYPE_GET_S:
      return "gets :{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_GET_M:
      return "getm :{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_PUT_S:
      return "puts :{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_PUT_M:
      return "putm :{}:{}:{}:{}".format( s.src, s.opaque, s.addr, s.data               )

    if s.type_ == CoherentMemReqMsg.TYPE_FWD_GET_S:
      return "fgets:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_FWD_GET_S:
      return "fgetm:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_INV:
      return "inv:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_WRITE_INIT_S:
      return "inits:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemReqMsg.TYPE_WRITE_INIT_M:
      return "initm:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    return "???:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

#-------------------------------------------------------------------------
# CoherentMemRespMsg
#-------------------------------------------------------------------------
#      2b    2b      4b     4b      8b      4b     32b    4b    128b
# +-------+-------+------+------+--------+------+------+-----+------+
# + SrcID | DstID | type | acks | opaque | test | addr | len | data |
# +-------+-------+------+------+--------+------+------+-----+------+

class CoherentMemRespMsg( BitStructDefinition ):

  nbits         = 188
  src_nbits     = 2
  dst_nbits     = 2
  type_nbits    = 4
  acks_nbits    = 4
  opaque_nbits  = 8
  test_nbits    = 4
  addr_nbits    = 32
  len_nbits     = 4
  data_nbits    = 128

  # Coherent msg types

  TYPE_DATA     = 0
  TYPE_PUT_ACK  = 1
  TYPE_INV_ACK  = 2

  # Init

  def __init__( s ):

    s.src     = BitField( CoherentMemRespMsg.src_nbits    )
    s.dst     = BitField( CoherentMemRespMsg.dst_nbits    )
    s.type_   = BitField( CoherentMemRespMsg.type_nbits   )
    s.acks    = BitField( CoherentMemRespMsg.acks_nbits   )
    s.opaque  = BitField( CoherentMemRespMsg.opaque_nbits )
    s.test    = BitField( CoherentMemRespMsg.test_nbits   )
    s.addr    = BitField( CoherentMemRespMsg.addr_nbits   )
    s.len     = BitField( CoherentMemRespMsg.len_nbits    )
    s.data    = BitField( CoherentMemRespMsg.data_nbits   )

  # Make a generic request message

  def mk_msg( s, src, dst, type_, acks, opaque, test, addr, len_, data ):

    msg         = s()
    msg.src     = src
    msg.dst     = dst
    msg.type_   = type_
    msg.acks    = acks
    msg.opaque  = opaque
    msg.test    = test
    msg.addr    = addr
    msg.len     = len_
    msg.data    = data

    return msg

  def mk_rd( s, addr, opaque, len_, data, test=0, acks=0 ):

    msg         = s()
    msg.src     = 0
    msg.dst     = 0
    msg.acks    = acks
    msg.type_   = CoherentMemRespMsg.TYPE_DATA
    msg.opaque  = opaque
    msg.test    = test
    msg.addr    = addr
    msg.len     = len_
    msg.data    = data

    return msg

  def mk_wr( s, addr, opaque, len_, test=0 ):

    msg         = s()
    msg.src     = 0
    msg.dst     = 0
    msg.acks    = 0
    msg.type_   = CoherentMemRespMsg.TYPE_PUT_ACK
    msg.opaque  = opaque
    msg.test    = test
    msg.addr    = addr
    msg.len     = len_
    msg.data    = 0

    return msg

  # Return string format of a message

  def __str__( s ):

    if s.type_ == CoherentMemRespMsg.TYPE_DATA:
      return "dat:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, s.data               )

    if s.type_ == CoherentMemRespMsg.TYPE_PUT_ACK:
      return "pak:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    if s.type_ == CoherentMemRespMsg.TYPE_INV_ACK:
      return "iak:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

    return "???:{}:{}:{}:{}".format( s.src, s.opaque, s.addr, ' '*(s.data.nbits/4) )

CoherentMemReqMsg16B   = CoherentMemReqMsg()
CoherentMemRespMsg16B  = CoherentMemRespMsg()

class CoherentMemMsg16B( object ):
  def __init__( s ):
    s.req  = CoherentMemReqMsg()
    s.resp = CoherentMemRespMsg()
