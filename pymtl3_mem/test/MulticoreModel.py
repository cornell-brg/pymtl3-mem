"""
=========================================================================
MulticoreModel.py
=========================================================================
Models the multicore processor for testing multicache

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 13 April 2020
"""
from pymtl3 import *
from pymtl3.stdlib.mem.ifcs import MemRequesterIfc, MemResponderIfc
from pymtl3.stdlib.stream import StreamSourceFL, StreamSinkFL
from pymtl3_mem.constants import *
from pymtl3_mem.blocking_cache.units.counters import CounterUpDown, CounterEnRst

from .ProcModel import ProcModel

def mk_multicache_test_struct( p ):
  cls_name    = f"MulticacheTestingSrc"
  req_cls = mk_bitstruct( cls_name, {
    "order" : Bits32,
    "req"   : p.CacheReqType
  })
  return req_cls

class MulticoreModel( Component ):
  
  def construct( s, p ):
    s.p = p
    srcMsg = mk_multicache_test_struct( p )

    s.mem_master_ifc = [MemRequesterIfc( p.CacheReqType, p.CacheRespType ) 
    for _ in range(p.ncaches)]

    src_transactions = [ [] for _ in range( p.ncaches ) ]
    sink_transactions = [ [] for _ in range( p.ncaches ) ]
    srcs  = p.msgs[::2]
    sinks = p.msgs[1::2]
    orders = [y for x,y,z in srcs]

    for i in range(len(srcs)):
      cache_number, order, msg = srcs[i]
      src_transactions[cache_number].append( srcMsg(order, msg) )
      # src_transactions[cache_number].append( msg )
      sink_transactions[cache_number].append( sinks[i] )

    s.src  = [ StreamSourceFL( srcMsg, src_transactions[i], p.src_init_delay,
     p.src_delay ) for i in range( p.ncaches ) ]
    s.sink = [ StreamSinkFL( p.CacheRespType, sink_transactions[i], p.sink_init_delay,
     p.sink_delay ) for i in range( p.ncaches ) ]
    s.proc_model = [ ProcModel( p.CacheReqType, p.CacheRespType ) for _ in range( p.ncaches ) ]
    
    for i in range( p.ncaches ):
      s.proc_model[i].cache //= s.mem_master_ifc[i]
      s.sink[i].istream     //= s.proc_model[i].proc.respstream
      s.proc_model[i].proc.reqstream.msg //= s.src[i].ostream.msg.req
      # s.proc_model[i].proc.reqstream.val //= s.src[i].ostream.val
      # s.proc_model[i].proc.reqstream.rdy //= s.src[i].ostream.rdy

    s.curr_order          = CounterUpDown( Bits32 )
    s.curr_order.up_amt //= b32(1)
    s.curr_order.dw_amt //= b32(1)
    s.curr_order.ld_amt //= b32(0)
    s.curr_order.ld_en  //= b1(0)
    s.curr_order.up_en  //= lambda : s.curr_order_in_flight.out == 0
    s.curr_order.dw_en  //= b1(0)

    s.curr_order_in_flight = CounterUpDown( Bits32, orders.count( 0 ) ) # inflight instead of waiting
    s.curr_order_in_flight.ld_amt //= lambda : Bits32( orders.count(s.curr_order.out + 1) )
    s.curr_order_in_flight.ld_en  //= lambda : s.curr_order_in_flight.out == 0
    s.curr_order_in_flight.up_amt //= b32(0)
    s.curr_order_in_flight.up_en  //= b1(0)

    @update
    def src_send_recv():
      # for i in range( p.ncaches ):
      #   s.src[i].ostream.rdy @= n
      #   if s.proc_model[i].proc.reqstream.rdy:      
      #     if s.src[i].ostream.msg.order <= s.curr_order.out:
      #       s.src[i].ostream.rdy @= y
      for i in range( p.ncaches ):
        s.proc_model[i].proc.reqstream.val @= 0
        s.src[i].ostream.rdy @= 0
        if s.src[i].ostream.msg.order <= s.curr_order.out:
          s.proc_model[i].proc.reqstream.val @= s.src[i].ostream.val
          s.src[i].ostream.rdy @= s.proc_model[i].proc.reqstream.rdy
        
    @update
    def curr_order_in_flight_logic():
      s.curr_order_in_flight.dw_en @= n
      trans_done = 0
      for i in range( p.ncaches ):
        if s.proc_model[i].proc.respstream.val & s.proc_model[i].proc.respstream.rdy:
          s.curr_order_in_flight.dw_en @= y
          trans_done += 1

      s.curr_order_in_flight.dw_amt @= b32(trans_done)     
      

  def done( s ):
    src_done = True
    sink_done = True
    for m in s.src:
      src_done &= m.done()
    for m in s.sink:
      sink_done &= m.done()
    return src_done and sink_done

  def line_trace( s ):
    msg = ''

    # for i in range( s.p.ncaches ):
    #   if s.src[i].ostream.val & s.src[i].ostream.rdy:
    #     msg += f'{i}>{s.src[i].ostream.msg} '  
    #   elif ~s.src[i].ostream.val & s.src[i].ostream.rdy:
    #     msg += ' '*(39)
    #   else:
    #     msg += '#'+' '*(38)
    # for i in range( s.p.ncaches ):
    #   if s.sink[i].istream.val & s.sink[i].istream.rdy:
    #     msg += f'{i}<{s.sink[i].istream.msg} '  
    #   elif ~s.sink[i].istream.val & s.sink[i].istream.rdy:
    #     msg += ' '*(23)
    #   else:
    #     msg += ' #'+' '*(21)

    # msg += s.curr_order_in_flight.line_trace()
    # msg += s.curr_order.line_trace()
    # msg += f' lden:{s.curr_order_in_flight.ld_en} lda:{s.curr_order_in_flight.ld_amt} '
    # msg += s.proc_model[0].line_trace()

    for i in range( s.p.ncaches ):
      msg += f"{s.proc_model[i].proc}(P{i}){s.proc_model[i].cache} || "

    return msg
