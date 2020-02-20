from copy import deepcopy
from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle

class TestSinkError( Exception ):
  pass

#===============================================================================
# TestSourceSink
#===============================================================================

class TestSourceSink( Model ):

  def __init__( s, src_dtype, sink_dtype, src_msgs, sink_msgs, nports ):

    s.in_       = [ InValRdyBundle  ( sink_dtype ) for _ in range( nports ) ]
    s.out       = [ OutValRdyBundle ( src_dtype  ) for _ in range( nports ) ]

    s.done      = OutPort( 1 )

    s.src_msgs  = deepcopy( src_msgs  )
    s.sink_msgs = deepcopy( sink_msgs )

    s.cur_idx   = -1
    s.pending   = [ False for _ in range( nports ) ]

    @s.tick
    def tick_logic():

      #------------------------------------------------------------------------
      # Handle reset
      #------------------------------------------------------------------------

      if s.reset:
        for i in range( nports ):
          if s.src_msgs[i] and s.src_msgs[i][0]:
            s.out[i].msg.next = s.src_msgs[i][0]

          s.in_[i].rdy.next = False
          s.out[i].val.next = False

        s.done.next = False

        return

      # check sinks

      for i in range( nports ):

        if s.pending[i] and s.sink_msgs[i][s.cur_idx] and s.in_[i].val:

          s.pending[i] = False

          if s.in_[i].msg != s.sink_msgs[i][s.cur_idx]:
            error_msg = """
The test sink received an incorrect message!
  - sink name     : {sink_name}
  - port number   : {port_number}
  - msg number    : {msg_number}
  - expected msg  : {expected_msg}
  - actual msg    : {actual_msg}
"""
            raise TestSinkError( error_msg.format(
              sink_name     = s.name,
              port_number   = i,
              msg_number    = idx,
              expected_msg  = s.sink_msgs[i][ s.cur_idx ],
              actual_msg    = s.in_[i].msg,
            ))

        s.in_[i].rdy.next = True

      # check if we can issue new requests this cycle

      can_issue = True
      for i in range( nports ):
        if not s.out[i].rdy or s.pending[i]:
          can_issue = False
          break

      if can_issue:

        # check if we run out of tests
        if s.cur_idx == len( s.src_msgs[ 0 ] ) - 1:
          s.done.next = True
          for i in range( nports ):
            s.out[i].val.next = False
          return

        else:
          s.done.next = False
          s.cur_idx   += 1

          # issue cur_idx tests
          for i in range( nports ):
            if s.src_msgs[i][ s.cur_idx ]:
              s.out[i].val.next = True
              s.out[i].msg.next = s.src_msgs[i][ s.cur_idx ]
              s.pending[i]      = True
            else:
              s.out[i].val.next = False
              s.pending[i]      = False

      else:
        s.done.next = False
        for i in range( nports ):
          s.out[i].val.next = False

  def line_trace( s ):

    trace = []

    for i in range( len( s.in_ ) ):
      trace.append( "[src_{}] idx={} {}".format( i, s.cur_idx, s.out[i] ) )

    trace.append("-->")

    for i in range( len( s.in_ ) ):
      trace.append( "[sink_{}] {}".format( i, s.in_[i] ) )

    return " ".join( trace )
