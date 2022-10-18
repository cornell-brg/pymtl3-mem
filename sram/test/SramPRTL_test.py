#=========================================================================
# BlockingCacheFL_test.py
#=========================================================================

import pytest
import random

from pymtl3 import *
from pymtl3.stdlib.test_utils import mk_test_case_table, run_sim
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.stream import StreamSourceFL, StreamSinkFL
from pymtl3.stdlib.primitive import RegRst
from pymtl3.stdlib.connects import connect_pairs

from pymtl3.stdlib.mem import MemMsgType, mk_mem_msg

from sram.SramPRTL import SramPRTL

MemReqMsg4B, MemRespMsg4B = mk_mem_msg(8,10,32)

class memWrapper(Component):
  def construct(s,abw,nbl):
    idw         = clog2(nbl)         # index width; clog2(512) = 9
    twb_b       = int(abw+7)//8      # Tag array write byte bitwidth

    ab          = mk_bits(abw)
    ix          = mk_bits(idw)

    s.sramreq    = IStreamIfc(MemReqMsg4B)
    s.sramresp   = OStreamIfc(MemRespMsg4B)
    s.sram_val   = Wire(b1)
    s.sram_type  = Wire(b1)
    s.sram_idx   = Wire(ix)
    s.sram_wdata = Wire(ab)
    s.sram_wben  = Wire(mk_bits(twb_b))
    s.sram_rdata = Wire(ab)

    m = s.SRAM = SramPRTL(abw, nbl)
    connect_pairs(
      m.port0_val, s.sram_val,
      m.port0_type, s.sram_type,
      m.port0_idx, s.sram_idx,
      m.port0_wdata, s.sram_wdata,
      # m.port0_wben, s.sram_wben,
      m.port0_rdata, s.sram_rdata,
    )

    for i in range(twb_b):
      s.SRAM.port0_wben[i*8:i*8+8] //= lambda: sext(s.sram_wben[i], 8)

    s.done = Wire(b1)
    m = s.reg_val = RegRst(b1)
    connect_pairs(
      m.in_, s.sramreq.val,
      m.out, s.done
    )

    m = s.reg_type_ = RegRst(b4)
    connect_pairs(
      m.in_, s.sramreq.msg.type_,
      m.out, s.sramresp.msg.type_
    )

    m = s.reg_opaque = RegRst(b8)
    connect_pairs(
      m.in_, s.sramreq.msg.opaque,
      m.out, s.sramresp.msg.opaque
    )

    @update
    def comb_logic():
      s.sramreq.rdy @= b1(1)
      if s.sramreq.msg.type_ == MemMsgType.WRITE_INIT:
        s.sram_type @= b1(1)
        s.sram_wben @= b4(0xf)
      else:
        s.sram_type @= b1(0)
        s.sram_wben @= b4(0x0)
      s.sram_val   @= s.sramreq.val
      s.sram_idx   @= ix(s.sramreq.msg.addr)
      s.sram_wdata @= ab(s.sramreq.msg.data)
      s.sramresp.msg.data @= s.sram_rdata
      s.sramresp.val @= s.done


  def line_trace(s):
    return s.SRAM.line_trace() + ""

class TestHarness(Component):
  def construct(s,src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, memModel):
    # Instantiate models
    s.src   = StreamSourceFL(MemReqMsg4B, src_msgs, src_delay)
    s.mem   = memModel(32,1024)
    s.sink  = StreamSinkFL(MemRespMsg4B, sink_msgs, sink_delay)

    connect (s.src.ostream, s.mem.sramreq)
    connect (s.mem.sramresp, s.sink.istream)

  def done(s):
    return s.src.done() and s.sink.done()

  def line_trace(s):
    return s.src.line_trace() + " " + s.mem.line_trace() \
         + " " + s.sink.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return MemReqMsg4B(type_, opaque, addr, len, data)

def resp( type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return MemRespMsg4B(type_, opaque, len, test, data)

#----------------------------------------------------------------
# Run the simulation
#----------------------------------------------------------------
# def run_sim(th, max_cycles):
#   th.elaborate()
#   # print (" -----------starting simulation----------- ")
#   th.apply( DynamicSim )
#   th.sim_reset()
#   curr_cyc = 0
#   print("")
#   while not th.done():
#     th.tick()
#     print ("{:4d}: {}".format(curr_cyc, th.line_trace()))
#     curr_cyc += 1
#     assert curr_cyc < max_cycles
#   th.tick()

#----------------------------------------------------------------------
# Test Case: read hit path
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def read_hit_1word_clean( base_addr=0 ):
  return [
    #    type  opq  addr len data                type  opq  test len data
    req( 'in', 0x0, 1,   0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x0, 1,   0, 0          ), resp( 'rd', 0x0, 0,   0,  0xdeadbeef ),
  ]

#----------------------------------------------------------------------
# Test Case: read hit/miss path,random requests
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT

def random_test( base_addr=100 ):
  array = []
  random.seed(0)
  test_amount = 100
  addr = [ i for i in range(test_amount)]
  data = [random.randint(0,0xfffff) for i in range(test_amount)]
  for i in range(test_amount):
    #                  type  opq  addr  len data
    array.append(req(  'in', i, addr[i], 0, data[i] ))
    array.append(resp( 'in', i, 0,       0, 0 ))

  for i in range(test_amount):
    array.append(req(  'rd', i, addr[i], 0, 0 ))
    array.append(resp( 'rd', i, 0,       0, data[i] ))

  return array

#-------------------------------------------------------------------------
# Test table for generic test
#-------------------------------------------------------------------------

test_case_table_generic = mk_test_case_table([
  (                         "msg_func               stall lat src sink"),
  [ "read_hit_1word_clean",  read_hit_1word_clean,  0.0,  0,  0,  0    ],
  [ "random_test",           random_test,           0.0,  0,  0,  0    ],
])

@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params ):
  msgs = test_params.msg_func(  )
  # Instantiate testharness
  th = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         memWrapper)
  # Run the test
  run_sim( th )
