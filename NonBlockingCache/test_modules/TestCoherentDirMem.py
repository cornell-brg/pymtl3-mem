#=========================================================================
# TestCoherentDirMemory
#=========================================================================

from pymtl      import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.cl   import InValRdyRandStallAdapter
from pclib.cl   import OutValRdyInelasticPipeAdapter

from ifcs.CoherentMemMsg import CoherentMemReqMsg, CoherentMemRespMsg, CoherentMemMsg16B

#-------------------------------------------------------------------------
# Directory Entry
#-------------------------------------------------------------------------

class Entry(object):

  I   = 0
  S   = 1
  M   = 2
  S_D = 3
  INV = 4

  def __init__( self, addr ):
    self.state = Entry.I
    self.S     = set()
    self.M     = None
    self.addr  = addr

  def add_S( self, src ):
    src = int( src )
    self.S.add( src )

  def remove_S( self, src ):
    src = int( src )
    if src in self.S:
      self.S.remove( src )

  def clear_S( self ):
    self.S = set([])

  def set_M( self, src ):
    src = int( src )
    self.M = src

  def clear_M( self ):
    assert self.M is not None
    self.M = None

#-------------------------------------------------------------------------
# TestCoherentDirMemory
#-------------------------------------------------------------------------

class TestCoherentDirMemory( Model ):

  #-------------------------------------------------------------------------
  # helper functions
  #-------------------------------------------------------------------------

  # get message data lenth
  def get_nbytes( s, len ):
    nbytes = len
    if nbytes == 0:
      nbytes = s.data_nbits/8
    return nbytes

  # get or create an entry for this addr
  def get_entry( s, addr ):
    for _entry in s.entries:
      if _entry.addr == addr:
        return _entry                       # we found a match
    entry = Entry( addr )                   # otherwise create a new one
    s.entries.append( entry )
    return entry

  # peak into the request queue
  def peak_req( s, req ):
    if not req.empty():
      memreq = req.first()
      return memreq
    return None                             # return memreq or None

  # test if this src is the current data onwer
  def is_owner( s, src, entry ):
    if entry.M is None:
      return False
    src = int( src )
    if entry.M == src:
      return True
    else:
      return False


  def __init__( s, mem_ifc_dtypes=CoherentMemMsg16B(), ncaches = 2, stall_prob=0, latency=0, mem_nbytes=2**20 ):

    s.dir_id  = ncaches   # this directory's ID

    # Interface

    s.reqs  = InValRdyBundle  ( mem_ifc_dtypes.req  )
    s.resps = OutValRdyBundle ( mem_ifc_dtypes.resp )
    s.fwds  = InValRdyBundle  ( mem_ifc_dtypes.req  )

    # Checks

    assert mem_ifc_dtypes.req.data.nbits  % 8 == 0
    assert mem_ifc_dtypes.resp.data.nbits % 8 == 0

    # Buffers to hold memory request/response messages

    s.reqs_q  = InValRdyRandStallAdapter     ( s.reqs,  stall_prob  )
    s.resps_q = OutValRdyInelasticPipeAdapter( s.resps, latency     )
    s.fwds_q  = OutValRdyInelasticPipeAdapter( s.fwds,  latency     )

    # Actual memory

    s.mem = bytearray( mem_nbytes )

    s.entries = []

    # Local constants

    s.mk_resp = mem_ifc_dtypes.resp.mk_msg
    s.mk_req  = mem_ifc_dtypes.req.mk_msg

    s.data_nbits   = mem_ifc_dtypes.req.data.nbits

    # test bit define
    s.No_Change = 0
    s.I_to_S    = 1
    s.I_to_M    = 2
    s.S_to_M    = 3
    s.M_to_S_D  = 4
    s.S_to_I    = 5
    s.M_to_I    = 6
    s.S_D_to_S  = 7

    # buffer for invalidations
    s.pending_inv = []

    s.INV_INPUT_REQ = Bits( 4, 15 )

    s.OUT_INV       = 0
    s.OUT_FWD_GETS  = 1
    s.OUT_FWD_GETM  = 2
    s.OUT_PUT_ACK   = 3
    s.OUT_DATA      = 4
    s.OUT_INVALID   = 5

    s.cur_state = Entry.INV
    s.nex_state = Entry.INV
    s.address   = 0
    s.reqtype   = s.INV_INPUT_REQ
    s.out_type  = s.OUT_INVALID
    s.out_dst   = 0

    #---------------------------------------------------------------------
    # Tick
    #---------------------------------------------------------------------

    @s.tick_cl
    def tick():

      # Tick adapters

      s.reqs_q.xtick()
      s.resps_q.xtick()
      s.fwds_q.xtick()

      # Reset cur_state, nex_state and address
      s.cur_state = Entry.INV
      s.nex_state = Entry.INV
      s.address   = 0
      s.reqtype   = s.INV_INPUT_REQ
      s.out_type  = s.OUT_INVALID
      s.out_dst   = 0

      # handle outgoing invalidations first
      if s.pending_inv:
        # buffer is not empty
        if not s.fwds_q.full():
          sharer, memreq = s.pending_inv.pop()
          type_ = CoherentMemReqMsg.TYPE_INV
          s.fwds_q.enq( s.mk_req( src     = memreq.src,
                                  dst     = sharer,
                                  type_   = type_,
                                  opaque  = memreq.opaque,
                                  addr    = memreq.addr,
                                  len_    = memreq.len,
                                  data    = memreq.data ) )

          s.out_type  = s.OUT_INV
          s.out_dst   = sharer

        # since we've been handling invalidations, we won't
        # process another request in this cycle
        return

      # Check the reqs_q
      memreq = s.peak_req( s.reqs_q )

      # If no memreq in this cycle, return early
      if memreq is None:
        return

      # Otherwise, process the memreq

      entry     = s.get_entry( memreq.addr )
      nbytes    = s.get_nbytes( memreq.len )
      req_type  = memreq.type_                     # mem request type

      # Constants

      y        = True
      n        = False

      TYPE_WRITE_INIT_S = CoherentMemReqMsg.TYPE_WRITE_INIT_S
      TYPE_WRITE_INIT_M = CoherentMemReqMsg.TYPE_WRITE_INIT_M
      TYPE_GET_S        = CoherentMemReqMsg.TYPE_GET_S
      TYPE_GET_M        = CoherentMemReqMsg.TYPE_GET_M
      TYPE_PUT_S        = CoherentMemReqMsg.TYPE_PUT_S
      TYPE_PUT_M        = CoherentMemReqMsg.TYPE_PUT_M

      I                 = Entry.I
      S                 = Entry.S
      M                 = Entry.M
      S_D               = Entry.S_D

      is_owner          = s.is_owner( memreq.src, entry )
      last_puts         = True if len(entry.S) == 1 else False

      #                                                                                     next   read  write  send  send  add     remove  set    clear  owner2  forward  send
      #                                                                                     state  mem   mem    ack   data  sharer  sharer  owner  owner  sharer  request  inval
      if   req_type == TYPE_WRITE_INIT_S and entry.state == I:                      cmd = ( S,     n,    y,     y,    n,    y,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_WRITE_INIT_M and entry.state == I:                      cmd = ( M,     n,    y,     y,    n,    n,      n,      y,     n,     n,      n,       n    )
      elif req_type == TYPE_GET_S        and entry.state == I:                      cmd = ( S,     y,    n,     n,    y,    y,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_GET_S        and entry.state == S:                      cmd = ( S,     y,    n,     n,    y,    y,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_GET_S        and entry.state == M:                      cmd = ( S_D,   n,    n,     n,    n,    y,      n,      n,     n,     y,      y,       n    )
      elif req_type == TYPE_GET_S        and entry.state == S_D:                    return
      elif req_type == TYPE_GET_M        and entry.state == I:                      cmd = ( M,     y,    n,     n,    y,    n,      n,      y,     n,     n,      n,       n    )
      elif req_type == TYPE_GET_M        and entry.state == S:                      cmd = ( M,     y,    n,     n,    y,    n,      y,      y,     n,     n,      n,       y    )
      elif req_type == TYPE_GET_M        and entry.state == M:                      cmd = ( M,     n,    n,     n,    n,    n,      n,      y,     n,     n,      y,       n    )
      elif req_type == TYPE_GET_M        and entry.state == S_D:                    return
      elif req_type == TYPE_PUT_S        and entry.state == I:                      cmd = ( I,     n,    n,     y,    n,    n,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_S        and entry.state == S  and last_puts:       cmd = ( I,     n,    n,     y,    n,    n,      y,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_S        and entry.state == S  and not last_puts:   cmd = ( S,     n,    n,     y,    n,    n,      y,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_S        and entry.state == M:                      cmd = ( M,     n,    n,     y,    n,    n,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_S        and entry.state == S_D:                    cmd = ( S_D,   n,    n,     y,    n,    n,      y,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_M        and entry.state == I:                      cmd = ( I,     n,    n,     y,    n,    n,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_M        and entry.state == S:                      cmd = ( S,     n,    n,     y,    n,    n,      y,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_M        and entry.state == M   and is_owner:       cmd = ( I,     n,    y,     y,    n,    n,      n,      n,     y,     n,      n,       n    )
      elif req_type == TYPE_PUT_M        and entry.state == M   and not is_owner:   cmd = ( M,     n,    n,     y,    n,    n,      n,      n,     n,     n,      n,       n    )
      elif req_type == TYPE_PUT_M        and entry.state == S_D and is_owner:       cmd = ( S,     n,    y,     y,    n,    n,      n,      n,     y,     n,      n,       n    )
      elif req_type == TYPE_PUT_M        and entry.state == S_D and not is_owner:   cmd = ( S_D,   n,    n,     y,    n,    n,      y,      n,     n,     n,      n,       n    )

      # decode command

      next_state     = cmd[0]
      read_mem       = cmd[1]
      write_mem      = cmd[2]
      send_ack       = cmd[3]
      send_data      = cmd[4]
      add_sharer     = cmd[5]
      remove_sharer  = cmd[6]
      set_owner      = cmd[7]
      clear_owner    = cmd[8]
      owner_2_sharer = cmd[9]
      fwd_request    = cmd[10]
      send_inval     = cmd[11]

      # save cur_state and nex_state for line trace
      s.cur_state = entry.state
      s.nex_state = next_state
      s.address   = entry.addr
      s.reqtype   = req_type

      # debug print
      #print idx
      #print "next   read  write  send  send  add     remove  set    clear  owner2  forward  send"
      #print "state  mem   mem    ack   data  sharer  sharer  owner  owner  sharer  request  inval"
      #print cmd

      # check if ports are ready

      if send_ack or send_data:
        # need to send an ack or data, but resp_q is full -> stall
        if s.resps_q.full():
          return

      old_owner = entry.M
      if fwd_request:
        assert old_owner is not None
        # need to send an fowarded request but fwd_q is full -> stall
        if s.fwds_q.full():
          return

      if send_inval:
        assert not s.pending_inv
        # if we need to send invalidation, assert the buffer is empty

      # get test value
      if   entry.state == next_state:
        test_value = s.No_Change
      elif entry.state == I:
        if   next_state == S:
          test_value = s.I_to_S
        elif next_state == M:
          test_value = s.I_to_M
      elif entry.state == S:
        if   next_state == I:
          test_value = s.S_to_I
        elif next_state == M:
          test_value = s.S_to_M
      elif entry.state == M:
        if   next_state == I:
          test_value = s.M_to_I
        elif next_state == S_D:
          test_value = s.M_to_S_D
      elif entry.state == S_D:
        if next_state == S:
          test_value = s.S_D_to_S

      # update state
      entry.state = next_state

      # add sharer if necessary
      if add_sharer:
        entry.add_S( memreq.src )

      # remove sharer if necessary
      if remove_sharer:
        entry.remove_S( memreq.src )

      # set owner if necessary
      if set_owner:
        entry.set_M( memreq.src )

      # clear owner if necessary
      if clear_owner:
        entry.clear_M()

      # move owner to sharer if necessary
      if owner_2_sharer:
        entry.add_S( entry.M )
        # entry.clear_M()
        # do NOT clear owner here, since S_D needs it

      # send forwarded request if necessary
      if fwd_request:
        assert old_owner is not None

        if   req_type == TYPE_GET_S:
          type_       = CoherentMemReqMsg.TYPE_FWD_GET_S
          s.out_type  = s.OUT_FWD_GETS
        elif req_type == TYPE_GET_M:
          type_       = CoherentMemReqMsg.TYPE_FWD_GET_M
          s.out_type  = s.OUT_FWD_GETM

        s.fwds_q.enq( s.mk_req( src     = memreq.src,
                                dst     = old_owner,
                                type_   = type_,
                                opaque  = memreq.opaque,
                                addr    = memreq.addr,
                                len_    = memreq.len,
                                data    = memreq.data ) )

        s.out_dst   = old_owner

      # send invaldation if necessary
      # since we set owner and remove onwer from sharer, not the sharers does not include the requester
      acks = 0
      if send_inval:
        sharers = list(entry.S)
        acks = len(sharers)
        entry.clear_S()
        for sharer in sharers:
          assert sharer != int(memreq.src)
          s.pending_inv.append( (sharer, memreq) )
          # append to the buffer. They will be sent one by one during the subsequent cycles

      # read memory if necessary
      read_data = None
      if read_mem:
        read_data = Bits( s.data_nbits )
        for j in xrange( nbytes ):
          read_data[j*8:j*8+8] = s.mem[ memreq.addr + j ]

      # write memory if necessary
      if write_mem:
        write_data = memreq.data
        for j in xrange( nbytes ):
          s.mem[ memreq.addr + j ] = write_data[j*8:j*8+8].uint()

      # send ack if necessary
      if send_ack:
        s.resps_q.enq( s.mk_resp( src     = s.dir_id,
                                  dst     = memreq.src,
                                  type_   = CoherentMemRespMsg.TYPE_PUT_ACK,
                                  acks    = 0,
                                  opaque  = memreq.opaque,
                                  test    = test_value,
                                  addr    = memreq.addr,
                                  len_    = memreq.len,
                                  data    = 0 ) )

        s.out_type  = s.OUT_PUT_ACK
        s.out_dst   = memreq.src

      # send data if necessary
      if send_data:
        assert read_data is not None
        s.resps_q.enq( s.mk_resp(  src   = s.dir_id,
                                   dst   = memreq.src,
                                   type_ = CoherentMemRespMsg.TYPE_DATA,
                                   acks  = acks,
                                   opaque = memreq.opaque,
                                   test = test_value,
                                   addr = memreq.addr,
                                   len_ = memreq.len,
                                   data = read_data ) )

        s.out_type  = s.OUT_DATA
        s.out_dst   = memreq.src

      # pop request queue
      s.reqs_q.deq()

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):

    inp_dict = {  CoherentMemReqMsg.TYPE_WRITE_INIT_S : "IS",
                  CoherentMemReqMsg.TYPE_WRITE_INIT_M : "IM",
                  CoherentMemReqMsg.TYPE_GET_S        : "GS",
                  CoherentMemReqMsg.TYPE_GET_M        : "GM",
                  CoherentMemReqMsg.TYPE_PUT_S        : "PS",
                  CoherentMemReqMsg.TYPE_PUT_M        : "PM",
                  s.INV_INPUT_REQ.uint()              : "__", }

    out_dict = {  s.OUT_INV      : "INV",
                  s.OUT_FWD_GETS : "FGS",
                  s.OUT_FWD_GETM : "FGM",
                  s.OUT_PUT_ACK  : "PAC",
                  s.OUT_DATA     : "DAT",
                  s.OUT_INVALID  : "___", }

    state_dict = {  Entry.I   : "I",
                    Entry.S   : "S",
                    Entry.M   : "M",
                    Entry.S_D : "S_D",
                    Entry.INV : "___" }

    trace = [ "[dir]" ]
    trace.append( "{}".format( inp_dict[ s.reqtype.uint() ] ) )
    trace.append( "addr {:>8x}".format( int( s.address ) ) )
    trace.append( "({:>3} -> {:>3})".format( state_dict[ s.cur_state ],
                                             state_dict[ s.nex_state ] ) )
    trace.append( "{} -> {}".format( out_dict[ s.out_type], s.out_dst ) )

    return " ".join( trace )

  #-----------------------------------------------------------------------
  # write_mem
  #-----------------------------------------------------------------------
  # Writes the list of bytes to the given memory address.

  def write_mem( s, addr, data ):
    assert len(s.mem) >= (addr + len(data))
    s.mem[ addr : addr + len(data) ] = data

  #-----------------------------------------------------------------------
  # read_mem
  #-----------------------------------------------------------------------
  # Reads size bytes from the given memory address.

  def read_mem( s, addr, size ):
    assert len(s.mem) > (addr + size)
    return s.mem[ addr : addr + size ]
