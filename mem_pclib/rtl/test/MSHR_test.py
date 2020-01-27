"""
=========================================================================
MSHR_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 25 January 2020
"""

import pytest

from pymtl3 import *
from pymtl3.stdlib.test.test_srcs import TestSrcCL, TestSrcRTL
from pymtl3.stdlib.test.test_sinks import TestSinkCL, TestSinkRTL
from mem_pclib.rtl.MSHR import MSHR
from mem_pclib.ifcs.MSHRMsg import mk_MSHR_msg
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from mem_pclib.test.sim_utils import run_sim

class MSHRTestHarness(Component):
  def construct (s, alloc_src_msgs, alloc_sink_msgs, dealloc_src_msgs, 
  dealloc_sink_msgs, alloc_src_delay, alloc_sink_delay, dealloc_src_delay,
         dealloc_sink_delay, dealloc_init_delay, MSHRMsg, entries ):
     # Instantiate models
    s.alloc_src   = TestSrcRTL(MSHRMsg, alloc_src_msgs, 0, alloc_src_delay)
    s.alloc_sink  = TestSinkRTL(Bits8, alloc_sink_msgs, 0, alloc_sink_delay)
    s.dealloc_src   = TestSrcRTL(Bits8, dealloc_src_msgs, dealloc_init_delay, dealloc_src_delay)
    s.dealloc_sink  = TestSinkRTL(MSHRMsg, dealloc_sink_msgs, 0, dealloc_sink_delay)
    s.MSHR = MSHR( MSHRMsg, entries)

    connect(s.alloc_src.send, s.MSHR.alloc_req)
    connect(s.alloc_sink.recv, s.MSHR.alloc_resp)
    connect(s.dealloc_src.send, s.MSHR.dealloc_req)
    connect(s.dealloc_sink.recv, s.MSHR.dealloc_resp)

  def done( s ):
    return s.alloc_src.done() and s.alloc_sink.done() and s.dealloc_src.done()\
    and s.dealloc_sink.done()

  def line_trace( s ):
    return "A|"+s.alloc_src.line_trace() + " D|"+s.dealloc_src.line_trace()\
       +" "+ s.MSHR.line_trace() + " A|"+s.alloc_sink.line_trace() + " D|" + \
         s.dealloc_sink.line_trace()

MSHRMsg = mk_MSHR_msg(32, 32, 8, 0)
def msg( type_, opaque, addr, len, data, rep ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return MSHRMsg( type_, opaque, addr, len, data, rep )

max_cycles = 50
class MSHR_Tests:
  
  def run_test(s, alloc_msgs, dealloc_msgs, entries, alloc_src_delay, 
  alloc_sink_delay, dealloc_src_delay, dealloc_sink_delay,dealloc_init_delay ):
    harness = MSHRTestHarness(alloc_msgs[::2], alloc_msgs[1::2], 
    dealloc_msgs[::2], dealloc_msgs[1::2],
    alloc_src_delay, alloc_sink_delay, dealloc_src_delay,
    dealloc_sink_delay,dealloc_init_delay, MSHRMsg, entries)
    harness.elaborate()
    run_sim( harness, max_cycles )

  def test_simple(s):
    alloc_msgs = [
      msg( "rd", 0, 0, 0, 0, 0), Bits8(0)
    ]
    dealloc_msgs = [
      Bits8(0), msg( "rd", 0, 0, 0, 0, 0 )
    ]
    s.run_test( alloc_msgs, dealloc_msgs, 2, 0,0,0,0,1 )