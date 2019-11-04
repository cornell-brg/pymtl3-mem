
"""
#=========================================================================
# BlockingCacheFL.py
#=========================================================================
A function level cache model which only passes cache requests and
responses to the memory

Author : Xiaoyu Yan, Eric Tang
Date   : 11/04/19
"""
from pymtl3      import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg
from pymtl3.stdlib.rtl.registers import RegRst


class BlockingCacheFL( Component ):
  """
  FL Model/Golden Model used to model functionality of cache.
  A function level cache model which only passes cache requests and
  responses to the memory
  - Can only model DMAP cache
  - 1 cycle latency
  - CANNOT handle random stalls/latencies (Not neccessary)
  """
  def construct( s,
                 nbytes        = 4096, # cache size in bytes, nbytes
                 CacheMsg      = "",   # Cache req/resp msg type
                 MemMsg        = "",   # Memory req/resp msg type
                 associativity = 1     # associativity, name: associativity
  ):

    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------

    assert MemMsg.abw == CacheMsg.abw, "abw not the same"

    obw       = MemMsg.obw
    clw       = MemMsg.dbw
    abw       = MemMsg.abw
    dbw       = CacheMsg.dbw
    nbl       = nbytes//clw 
    idw       = clog2(nbl)     # index width; clog2(512) = 9
    ofw       = clog2(clw//8)  # offset bitwidth; clog2(128/8) = 4
    tgw       = abw - ofw - idw    # tag bitwidth; 32 - 4 - 9 = 19
    
    BitsOpaque= mk_bits(obw)   # opaque
    BitsType  = mk_bits(4)     # type, always 4 bits
    BitsData  = mk_bits(dbw)   # data
    BitsAddr  = mk_bits(abw)   # address 
    BitsIdx   = mk_bits(idw)   # index 
    BitsTag   = mk_bits(tgw)   # tag 
    BitsLen   = mk_bits( clog2(dbw>>3) )
    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc -> Cache
    s.cachereq  = RecvIfcRTL ( CacheMsg.Req  )
    # Cache -> Proc
    s.cacheresp = SendIfcRTL ( CacheMsg.Resp )
    # Mem -> Cache
    s.memresp   = RecvIfcRTL ( MemMsg.Resp   )
    # Cache -> Mem
    s.memreq    = SendIfcRTL ( MemMsg.Req    )

    #---------------------------------------------------------------------
    # Control
    #---------------------------------------------------------------------

    # pass through val/rdy signals

    connect( s.cachereq.en, s.memreq.en )
    connect( s.cachereq.rdy, s.memreq.rdy )

    connect( s.memresp.en, s.cacheresp.en )
    connect( s.memresp.rdy, s.cacheresp.rdy )
    
    s.tag_array         = [Wire(BitsAddr) for i in range(nbl)]
    s.ctrl              = [Wire(b1) for i in range(nbl)]
    
    s.cachereq_len      = Wire(BitsLen)
    s.cachereq_opaque   = Wire(BitsOpaque)
    s.cachereq_type     = Wire(BitsType)
    s.cachereq_addr     = Wire(BitsAddr)
    s.cachereq_data     = Wire(BitsData)
    @s.update
    def input_cast(): 
      s.cachereq_len    = BitsLen(s.cachereq.msg.len)
      s.cachereq_type   = BitsType(s.cachereq.msg.type_)
      s.cachereq_opaque = BitsOpaque(s.cachereq.msg.opaque)
      s.cachereq_addr   = BitsAddr(s.cachereq.msg.addr)
      s.cachereq_data   = BitsData(s.cachereq.msg.data)

    #---------------------------------------------------------------------
    # Datapath
    #---------------------------------------------------------------------

    #REGISTERED INPUTS
    s.cacheresp_type_out = Wire(b4)
    s.type_reg = RegRst(b4)(
      in_ = s.cachereq.msg.type_,
      out = s.cacheresp_type_out

    ) # ASSUMING SINGLE CYCLE LATENCY 
    
    s.cacheresp_addr_out = Wire(BitsAddr)
    s.idx = Wire(BitsIdx)
    s.tag = Wire(BitsTag)
    s.addr_reg = RegRst(BitsAddr)(
      in_ = s.cachereq.msg.addr,
      out = s.cacheresp_addr_out
    ) # ASSUMING SINGLE CYCLE LATENCY
    
    s.val = Wire(b1)
    s.val_reg = RegRst(b1)(
      in_ = s.cachereq.en,
      out = s.val
    ) # ASSUMING SINGLE CYCLE LATENCY
    s.idx //= s.cacheresp_addr_out[ofw:ofw+idw]
    s.tag //= s.cacheresp_addr_out[ofw+idw:abw]

    @s.update
    def tag_check_logic():
      if s.reset:
        for i in range(nbl):
          s.tag_array[i] = BitsAddr(0)
          s.ctrl[i]      = b1(0)
      elif s.val:
        if s.tag_array[s.idx] == s.tag and s.ctrl[s.idx]:
          s.cacheresp.msg.test = b2(1) # Hit, GREAT
        else: 
          s.cacheresp.msg.test = b2(0)
          s.tag_array[s.idx]   = s.tag # Miss, replace old tag with new tag
          s.ctrl[s.idx]        = b1(1) # ctrl always becomes valid when we access it
        
        if s.cacheresp_type_out == MemMsgType.WRITE_INIT or \
          s.cacheresp_type_out == MemMsgType.WRITE: 
          s.tag_array[s.idx] = s.tag # Update tag array if we are writing
        
        if s.cacheresp_type_out == MemMsgType.WRITE_INIT: # INIT always miss
          s.cacheresp.msg.test = b2(0) 
        

    @s.update
    def test_mem_logic():
      # Pass through requests: just copy all of the fields over, except
      # we zero extend the data field.
      if  s.cachereq_len == 0:
        len_ = 4
      else:
        len_ =  s.cachereq_len

      if s.cachereq.msg.type_ == MemMsgType.WRITE_INIT:
        s.memreq.msg.type_ = MemMsgType.WRITE
      else:
        s.memreq.msg.type_ = s.cachereq.msg.type_

      s.memreq.msg.opaque  = s.cachereq.msg.opaque
      s.memreq.msg.addr    = s.cachereq.msg.addr
      s.memreq.msg.len     = len_
      s.memreq.msg.data    = zext( BitsData(s.cachereq.msg.data), clw )

      # Pass through responses: just copy all of the fields over, except
      # we truncate the data field.

      len_ = s.memresp.msg.len
      if len_ == 4:
        len_ = 0

      s.cacheresp.msg.type_  = s.cacheresp_type_out
      s.cacheresp.msg.opaque = s.memresp.msg.opaque
      s.cacheresp.msg.len    = len_
      s.cacheresp.msg.data   = s.memresp.msg.data[0:abw]


     
  def line_trace(s):
    return "tag:{} crl:{}".format(s.tag_array[s.idx], s.ctrl[s.idx] )


